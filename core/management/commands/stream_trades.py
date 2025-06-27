# core/management/commands/stream_trades.py
import asyncio
import json
import time
import logging
import gzip
from django.core.management.base import BaseCommand
from django.conf import settings
from channels.layers import get_channel_layer
import websockets

logger = logging.getLogger(__name__)

latest_prices = {pair: {} for pair in settings.TRACKED_PAIRS}


def normalize_pair(pair, exchange):
    return pair.replace('-', '').replace('_', '').lower()


async def broadcast_price_spread():
    channel_layer = get_channel_layer()
    while True:
        await asyncio.sleep(settings.BROADCAST_INTERVAL)
        for pair in settings.TRACKED_PAIRS:
            prices = latest_prices.get(pair, {})
            valid_prices = {k: v for k, v in prices.items() if v is not None}

            if len(valid_prices) > 1:
                max_price = max(valid_prices.values())
                min_price = min(valid_prices.values())
                spread = max_price - min_price
                avg_price = sum(valid_prices.values()) / len(valid_prices)
                spread_percentage = (spread / avg_price) * 100 if avg_price > 0 else 0

                message = {
                    'type': 'spread_update',
                    'pair': pair.upper(),
                    'spread': f"{spread:.4f}",
                    'spread_percentage': f"{spread_percentage:.4f}",
                    'timestamp': time.time(),
                    'prices': valid_prices
                }

                logger.debug(f"Broadcasting message: {message}")
                await channel_layer.group_send(
                    'price_spread',
                    {'type': 'price_update', 'message': message}
                )


async def handle_exchange_stream(uri, subscription_payload_generator, exchange_name, parse_function):
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                subscription_payload = subscription_payload_generator()
                if subscription_payload:
                    if isinstance(subscription_payload, list):
                        for payload in subscription_payload:
                            await websocket.send(json.dumps(payload))
                    else:
                        await websocket.send(json.dumps(subscription_payload))
                logger.info(f"Connected to {exchange_name} and sent subscription.")

                while True:
                    message = await websocket.recv()

                    # HTX and some other exchanges send gzipped data
                    if isinstance(message, bytes):
                        try:
                            message = gzip.decompress(message).decode('utf-8')
                        except (gzip.BadGzipFile, UnicodeDecodeError):
                            message = message.decode('utf-8')

                    data = json.loads(message)
                    logger.debug(f"Received from {exchange_name}: {data}")

                    # Handle heartbeats (ping/pong)
                    if 'ping' in data:
                        await websocket.send(json.dumps({'pong': data['ping']}))
                        logger.info(f"Sent pong to {exchange_name}")
                        continue
                    if 'op' in data and data.get('op') == 'ping':
                        await websocket.send(json.dumps({'op': 'pong'}))
                        logger.info(f"Sent pong to {exchange_name}")
                        continue

                    parse_function(data, exchange_name)

        except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
            logger.error(f"Connection to {exchange_name} closed: {e}. Reconnecting in 5s...")
        except Exception as e:
            logger.error(f"An error occurred with {exchange_name}: {e}. Reconnecting in 5s...")
        await asyncio.sleep(5)


def parse_binance(data, exchange):
    if 's' in data and 'p' in data:
        pair = normalize_pair(data['s'], exchange)
        if pair in latest_prices:
            latest_prices[pair][exchange] = float(data['p'])


def sub_binance():
    return None


def parse_htx(data, exchange):
    if 'ch' in data and 'tick' in data:
        pair = normalize_pair(data['ch'].split('.')[1], exchange)
        if pair in latest_prices:
            latest_prices[pair][exchange] = float(data['tick']['data'][0]['price'])


def sub_htx():
    return [{"sub": f"market.{pair}.trade.detail", "id": f"id{i}"} for i, pair in enumerate(settings.TRACKED_PAIRS)]


def parse_okx(data, exchange):
    if data.get('arg', {}).get('channel') == 'trades' and 'data' in data:
        pair = normalize_pair(data['arg']['instId'], exchange)
        if pair in latest_prices:
            latest_prices[pair][exchange] = float(data['data'][0][0])


def sub_okx():
    return {"op": "subscribe",
            "args": [{"channel": "trades", "instId": pair.upper().replace('USDT', '-USDT')} for pair in
                     settings.TRACKED_PAIRS]}


class Command(BaseCommand):
    help = 'Starts the real-time trade data streaming client'

    def handle(self, *args, **options):
        logger.info("Starting trade data streamer...")
        loop = asyncio.get_event_loop()

        binance_streams = '/'.join([f"{pair}@trade" for pair in settings.TRACKED_PAIRS])
        binance_uri = f"wss://stream.binance.com:9443/ws/{binance_streams}"
        htx_uri = "wss://api.huobi.pro/ws"
        okx_uri = "wss://ws.okx.com:8443/ws/v5/public"

        tasks = [
            handle_exchange_stream(binance_uri, sub_binance, 'binance', parse_binance),
            handle_exchange_stream(htx_uri, sub_htx, 'htx', parse_htx),
            handle_exchange_stream(okx_uri, sub_okx, 'okx', parse_okx),
            broadcast_price_spread()
        ]

        loop.run_until_complete(asyncio.gather(*tasks))
