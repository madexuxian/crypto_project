# core/management/commands/trading_bot.py
import asyncio
import time
import logging
from decimal import Decimal

from django.core.management.base import BaseCommand
from core.models import APIKey

# 【最终修复】使用最明确的、IDE友好的导入路径
# 即使IDE可能仍然显示警告，但这是各库官方推荐的或实际有效的导入方式
# --------------------------------------------------------------------------
try:
    # 币安 Binance
    from binance.client import Client as BinanceClient
    from binance.exceptions import BinanceAPIException
except ImportError:
    print("错误：无法导入'binance'库。请确保已通过 'pip install python-binance' 安装。")
    exit()

try:
    # 欧易 OKX
    from okx.api.trade import TradeAPI as OkxTradeAPI
except ImportError:
    print("错误：无法导入'okx'库。请确保已通过 'pip install okx' 安装。")
    exit()

try:
    # 火币 HTX (导入名为 huobi)
    from huobi.client.trade import TradeClient
    from huobi.client.account import AccountClient
    from huobi.constant import AccountType, OrderType, OrderSource
    from huobi.exception import HuobiApiException
except ImportError:
    print("错误：无法导入'huobi'库。请确保已通过 'pip install huobipro' 安装。")
    exit()
# --------------------------------------------------------------------------


logger = logging.getLogger(__name__)


# 伪函数：用于从数据流获取价差。在生产中应替换为Redis等中间件。
def get_latest_spread_data(pair, ex1, ex2):
    from random import uniform
    key = "_vs_".join(sorted((ex1, ex2)))
    mock_spreads = {
        'binance_vs_okx': {'spread_percentage': uniform(0.0001, 0.005)},
        'binance_vs_htx': {'spread_percentage': uniform(0.0001, 0.005)},
        'htx_vs_okx': {'spread_percentage': uniform(0.0001, 0.005)},
    }
    spread_percentage_str = f"{mock_spreads.get(key, {}).get('spread_percentage', 0.0):.6f}"
    return {'spread_percentage': Decimal(spread_percentage_str)}


class Command(BaseCommand):
    help = 'Runs the automated trading bot'

    def handle(self, *args, **options):
        logger.info("Starting trading bot...")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main_loop())

    async def main_loop(self):
        while True:
            try:
                active_keys = APIKey.objects.filter(is_active=True)
                for key_config in active_keys:
                    self.process_trade_logic(key_config)
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Trading bot main loop error: {e}", exc_info=True)
                await asyncio.sleep(15)

    def process_trade_logic(self, config: APIKey):
        spread_data = get_latest_spread_data('btcusdt', 'binance', 'okx')
        if not spread_data:
            return

        current_spread = spread_data['spread_percentage']
        if not config.has_open_position and current_spread >= config.buy_spread_percentage:
            logger.info(
                f"BUY SIGNAL for {config.user_profile.user.username} on {config.exchange}. Spread: {current_spread:.4%}")
            self.execute_order(config, 'BUY')
        elif config.has_open_position and abs(current_spread) <= config.sell_spread_percentage:
            logger.info(
                f"SELL SIGNAL for {config.user_profile.user.username} on {config.exchange}. Spread: {current_spread:.4%}")
            self.execute_order(config, 'SELL')

    def execute_order(self, config: APIKey, side: str):
        api_key = config.get_api_key()
        secret_key = config.get_secret_key()

        logger.info(f"Executing {side} order on {config.exchange} for user {config.user_profile.user.username}")

        # --- 币安 (Binance) ---
        if config.exchange == 'binance':
            try:
                client = BinanceClient(api_key, secret_key)
                if side == 'BUY':
                    order = client.create_order(symbol='BTCUSDT', side=BinanceClient.SIDE_BUY,
                                                type=BinanceClient.ORDER_TYPE_MARKET,
                                                quoteOrderQty=config.trade_amount_usdt)
                    logger.info(f"Order executed on Binance: {order}")
                    config.has_open_position = True
                    config.save()
                else:  # SELL
                    logger.warning("Binance SELL logic needs implementation.")
            except BinanceAPIException as e:
                logger.error(f"Binance API Error for {config.user_profile.user.username}: {e}")

        # --- 欧易 (OKX) ---
        elif config.exchange == 'okx':
            passphrase = "your-api-passphrase"  # 必须从用户处获取
            try:
                tradeAPI = OkxTradeAPI(api_key, secret_key, passphrase, False, '1')
                if side == 'BUY':
                    result = tradeAPI.place_order(instId='BTC-USDT', tdMode='cash', side='buy', ordType='market',
                                                  sz=str(config.trade_amount_usdt), tgtCcy='quote_ccy')
                    if result['code'] == '0':
                        logger.info(f"Order executed on OKX: {result['data']}")
                        config.has_open_position = True
                        config.save()
                    else:
                        logger.error(f"OKX order failed: {result['msg']}")
                else:  # SELL
                    logger.warning("OKX SELL logic needs implementation.")
            except Exception as e:
                logger.error(f"OKX order execution failed: {e}", exc_info=True)

        # --- 火币 (HTX) ---
        elif config.exchange == 'htx':
            try:
                account_client = AccountClient(api_key=api_key, secret_key=secret_key)
                accounts = account_client.get_accounts(account_type=AccountType.SPOT)
                spot_account_id = accounts[0].id

                trade_client = TradeClient(api_key=api_key, secret_key=secret_key)
                if side == 'BUY':
                    order_id = trade_client.create_order(symbol='btcusdt', account_id=spot_account_id,
                                                         order_type=OrderType.BUY_MARKET, source=OrderSource.API,
                                                         quote_amount=str(config.trade_amount_usdt))
                    logger.info(f"Order sent to HTX, order ID: {order_id}")
                    config.has_open_position = True
                    config.save()
                else:  # SELL
                    logger.warning("HTX SELL logic needs implementation.")
            except HuobiApiException as e:
                logger.error(f"HTX API Error: {e.error_code} - {e.error_message}")
            except Exception as e:
                logger.error(f"HTX order execution failed: {e}", exc_info=True)