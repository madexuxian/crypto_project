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
from itertools import combinations

logger = logging.getLogger(__name__)

latest_prices = {pair: {} for pair in settings.TRACKED_PAIRS}


def normalize_pair(pair, exchange):
    return pair.replace('-', '').replace('_', '').lower()


async def broadcast_price_spread():
    """
    Calculates and broadcasts spreads between all pairs of exchanges.
    """
    channel_layer = get_channel_layer()
    while True:
        await asyncio.sleep(settings.BROADCAST_INTERVAL)
        pairs_to_broadcast = ['btcusdt', 'ethusdt', 'solusdt']

        for pair in pairs_to_broadcast:
            prices = latest_prices.get(pair, {})
            # We need at least two prices to calculate a spread
            if len(prices) < 2:
                continue

            # Dynamically create all combinations of 2 from the available exchanges
            exchange_pairs = list(combinations(prices.keys(), 2))

            spreads_data = {}
            for ex1, ex2 in exchange_pairs:
                price1 = prices[ex1]
                price2 = prices[ex2]

                spread = price1 - price2
                avg_price = (price1 + price2) / 2
                spread_percentage = (abs(spread) / avg_price) * 100 if avg_price > 0 else 0

                # Create a consistent key, e.g., 'binance_okx'
                key = "_vs_".join(sorted((ex1, ex2)))
                spreads_data[key] = {
                    'spread': f"{spread:.4f}",
                    'spread_percentage': f"{spread_percentage:.4f}"
                }

            if spreads_data:
                message = {
                    'type': 'price_update',
                    'pair': pair.upper(),
                    'spreads': spreads_data,  # Send all calculated spreads
                    'prices': prices,  # Also send raw prices
                    'timestamp': time.time(),
                }
                logger.debug(f"Broadcasting spread message: {message}")
                await channel_layer.group_send(
                    'price_spread',
                    {'type': 'price_update', 'message': message}
                )


async def broadcast_triangular_arbitrage():
    """
    Calculates and broadcasts triangular arbitrage opportunities.
    """
    channel_layer = get_channel_layer()
    FEE_PER_TRANSACTION = 0.00075
    TOTAL_FEE_RATE = 1 - (FEE_PER_TRANSACTION * 3)

    paths = {
        'USDT-BTC-ETH-USDT': ('btcusdt', 'ethbtc', 'ethusdt'),
        'USDT-SOL-BTC-USDT': ('solusdt', 'solbtc', 'btcusdt'),
        'USDT-SOL-ETH-USDT': ('solusdt', 'soleth', 'ethusdt'),
    }

    while True:
        await asyncio.sleep(settings.BROADCAST_INTERVAL)

        for name, pairs in paths.items():
            try:
                price1 = latest_prices[pairs[0]]['binance']
                price2 = latest_prices[pairs[1]]['binance']
                price3 = latest_prices[pairs[2]]['binance']

                start_usdt = 1.0

                if name == 'USDT-BTC-ETH-USDT':
                    coin1_amount = start_usdt / price1
                    coin2_amount = coin1_amount / price2
                    end_usdt = coin2_amount * price3
                else:
                    coin1_amount = start_usdt / price1
                    coin2_amount = coin1_amount * price2
                    end_usdt = coin2_amount * price3

                profit = (end_usdt * TOTAL_FEE_RATE) - start_usdt
                profit_percentage = (profit / start_usdt) * 100

                message = {
                    'type': 'arbitrage_update',
                    'path': name,
                    'profit_percentage': f"{profit_percentage:.6f}",
                    'timestamp': time.time(),
                }

                await channel_layer.group_send(
                    'triangular_arbitrage',
                    {'type': 'arbitrage_update', 'message': message}
                )

            except (KeyError, TypeError, ZeroDivisionError) as e:
                logger.warning(
                    f"Could not calculate triangular arbitrage for {name}: Missing data or calculation error - {e}")
                continue


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

                    if isinstance(message, bytes):
                        try:
                            message = gzip.decompress(message).decode('utf-8')
                        except (gzip.BadGzipFile, UnicodeDecodeError):
                            message = message.decode('utf-8')

                    data = json.loads(message)

                    if data.get('event') == 'ping':
                        await websocket.send(json.dumps({'event': 'pong'}))
                        continue
                    if 'ping' in data:
                        await websocket.send(json.dumps({'pong': data['ping']}))
                        continue
                    if data.get('op') == 'ping':
                        await websocket.send(json.dumps({'op': 'pong'}))
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
    htx_pairs = ['btcusdt', 'ethusdt', 'solusdt']
    return [{"sub": f"market.{pair}.trade.detail", "id": f"id{i}"} for i, pair in enumerate(htx_pairs)]


def parse_okx(data, exchange):
    if data.get('arg', {}).get('channel') == 'trades' and 'data' in data:
        for trade in data['data']:
            if 'px' in trade and 'instId' in trade:
                pair = normalize_pair(trade['instId'], exchange)
                if pair in latest_prices:
                    latest_prices[pair][exchange] = float(trade['px'])


def sub_okx():
    okx_pairs = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT']
    return {"op": "subscribe", "args": [{"channel": "trades", "instId": pair} for pair in okx_pairs]}


class Command(BaseCommand):
    help = 'Starts the real-time trade data streaming client'

    def handle(self, *args, **options):
        logger.info("Starting trade data streamer...")
        loop = asyncio.get_event_loop()

        binance_streams = '/'.join([f"{pair.lower()}@trade" for pair in settings.TRACKED_PAIRS])
        binance_uri = f"wss://stream.binance.com:9443/ws/{binance_streams}"
        htx_uri = "wss://api.huobi.pro/ws"
        okx_uri = "wss://ws.okx.com:8443/ws/v5/public"

        tasks = [
            handle_exchange_stream(binance_uri, sub_binance, 'binance', parse_binance),
            handle_exchange_stream(htx_uri, sub_htx, 'htx', parse_htx),
            handle_exchange_stream(okx_uri, sub_okx, 'okx', parse_okx),
            broadcast_price_spread(),
            broadcast_triangular_arbitrage()
        ]

        loop.run_until_complete(asyncio.gather(*tasks))