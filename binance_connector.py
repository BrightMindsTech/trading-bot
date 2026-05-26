
# ============================================================
# 🔗 Binance Connector Module - وحدة الربط مع Binance
# ============================================================
# يدعم: Spot, Futures, Testnet, WebSockets
# ============================================================

"""
⚠️ تحذير أمني مهم:
• احفظ مفاتيح API في متغيرات بيئة (Environment Variables)
• لا تضع المفاتيح مباشرة في الكود أبداً
• امنع صلاحيات السحب (Withdrawals) في إعدادات API
• قصر الوصول على IP محدد (IP Whitelist)
"""

import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Load .env (if present) so keys don't need exporting
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # Optional dependency; code will still work with exported env vars
    pass

# ============================================================
# التثبيت المطلوب:
# pip install python-binance
# ============================================================

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    from binance import ThreadedWebsocketManager
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("⚠️ مكتبة python-binance غير مثبتة. قم بتثبيتها عبر: pip install python-binance")


class BinanceAPI:
    """
    🔗 واجهة الربط مع Binance API
    تدعم Spot, Futures, و Testnet
    """

    def __init__(self, 
                 api_key: str = None,
                 api_secret: str = None,
                 testnet: bool = True,
                 futures: bool = False):
        """
        تهيئة الاتصال مع Binance

        Args:
            api_key: مفتاح API (يفضل من متغير بيئة)
            api_secret: سر API (يفضل من متغير بيئة)
            testnet: True للتداول الورقي، False للتداول الحقيقي
            futures: True للعقود الآجلة، False للسبوت
        """

        # قراءة المفاتيح من متغيرات البيئة إذا لم تُمرر
        self.api_key = api_key or os.environ.get('BINANCE_API_KEY')
        self.api_secret = api_secret or os.environ.get('BINANCE_API_SECRET')

        if not self.api_key or not self.api_secret:
            raise ValueError("❌ مفاتيح API غير موجودة! قم بتعيينها في متغيرات البيئة أو تمريرها مباشرة")

        self.testnet = testnet
        self.futures = futures

        # إنشاء العميل
        if BINANCE_AVAILABLE:
            # Some environments inject HTTP(S)_PROXY which can break Binance connectivity.
            # Force-disable proxy usage unless the user explicitly edits this.
            self.client = Client(
                self.api_key,
                self.api_secret,
                testnet=testnet,
                requests_params={
                    "timeout": 20,
                    "proxies": {"http": None, "https": None},
                },
            )
        else:
            raise ImportError("❌ مكتبة python-binance غير مثبتة")

        print(f"✅ تم الاتصال بـ Binance {'Testnet' if testnet else 'Live'} {'Futures' if futures else 'Spot'}")

    # ============================================================
    # 📊 الحصول على بيانات السوق
    # ============================================================

    def get_historical_klines(self, 
                             symbol: str = "BTCUSDT",
                             interval: str = "1h",
                             start_time: datetime = None,
                             end_time: datetime = None,
                             limit: int = 500) -> pd.DataFrame:
        """
        الحصول على بيانات الشموع التاريخية (OHLCV)

        Args:
            symbol: زوج التداول (مثال: BTCUSDT)
            interval: الفاصل الزمني (1m, 5m, 15m, 1h, 4h, 1d)
            start_time: وقت البدء
            end_time: وقت الانتهاء
            limit: عدد الشموع (الحد الأقصى 1000)

        Returns:
            DataFrame يحتوي على open, high, low, close, volume
        """

        # تحويل الأوقات إلى timestamp
        start_ts = int(start_time.timestamp() * 1000) if start_time else None
        end_ts = int(end_time.timestamp() * 1000) if end_time else None

        try:
            if self.futures:
                klines = self.client.futures_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=start_ts,
                    end_str=end_ts,
                    limit=limit
                )
            else:
                klines = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=start_ts,
                    end_str=end_ts,
                    limit=limit
                )

            # تحويل إلى DataFrame
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])

            # تحويل الأعمدة الرقمية
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # تحويل الأوقات
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            df.set_index('open_time', inplace=True)

            return df[numeric_cols]

        except BinanceAPIException as e:
            print(f"❌ خطأ في Binance API: {e}")
            return pd.DataFrame()

    def get_recent_klines(self, 
                         symbol: str = "BTCUSDT",
                         interval: str = "1h",
                         lookback: str = "24 hours ago UTC") -> pd.DataFrame:
        """
        الحصول على بيانات الشموع الأخيرة بسهولة

        Args:
            symbol: زوج التداول
            interval: الفاصل الزمني
            lookback: فترة النظر للخلف (مثال: "24 hours ago UTC", "7 days ago UTC")
        """
        try:
            if self.futures:
                klines = self.client.futures_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=lookback
                )
            else:
                klines = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=lookback
                )

            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])

            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df.set_index('open_time', inplace=True)

            return df[numeric_cols]

        except BinanceAPIException as e:
            print(f"❌ خطأ: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        """الحصول على السعر الحالي"""
        try:
            if self.futures:
                ticker = self.client.futures_symbol_ticker(symbol=symbol)
            else:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"❌ خطأ في الحصول على السعر: {e}")
            return 0.0

    def get_account_balance(self, asset: str = "USDT") -> Dict:
        """الحصول على رصيد حساب محدد"""
        try:
            if self.futures:
                account = self.client.futures_account()
                for asset_info in account['assets']:
                    if asset_info['asset'] == asset:
                        return {
                            'asset': asset,
                            'wallet_balance': float(asset_info['walletBalance']),
                            'available_balance': float(asset_info['availableBalance']),
                            'unrealized_pnl': float(asset_info['unrealizedProfit'])
                        }
            else:
                balance = self.client.get_asset_balance(asset=asset)
                return {
                    'asset': asset,
                    'free': float(balance['free']),
                    'locked': float(balance['locked']),
                    'total': float(balance['free']) + float(balance['locked'])
                }
        except Exception as e:
            print(f"❌ خطأ في الحصول على الرصيد: {e}")
            return {}

    # ============================================================
    # 🎯 تنفيذ الأوامر
    # ============================================================

    def place_market_order(self, 
                          symbol: str,
                          side: str,  # "BUY" أو "SELL"
                          quantity: float,
                          test: bool = False) -> Dict:
        """
        تنفيذ أمر سوقي

        Args:
            symbol: زوج التداول
            side: جهة الأمر (BUY/SELL)
            quantity: الكمية
            test: True لاختبار الأمر (لا يُنفذ فعلياً)
        """
        try:
            if self.futures:
                if test:
                    order = self.client.futures_create_test_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity
                    )
                else:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity
                    )
            else:
                if test:
                    order = self.client.create_test_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity
                    )
                else:
                    order = self.client.order_market_buy(
                        symbol=symbol,
                        quantity=quantity
                    ) if side == "BUY" else self.client.order_market_sell(
                        symbol=symbol,
                        quantity=quantity
                    )

            print(f"✅ تم تنفيذ أمر {side} {quantity} {symbol}")
            return order

        except BinanceAPIException as e:
            print(f"❌ فشل في تنفيذ الأمر: {e}")
            return {}

    def place_limit_order(self,
                         symbol: str,
                         side: str,
                         quantity: float,
                         price: float,
                         test: bool = False) -> Dict:
        """تنفيذ أمر محدد السعر"""
        try:
            if self.futures:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    quantity=quantity,
                    price=price,
                    timeInForce='GTC'
                )
            else:
                order = self.client.order_limit_buy(
                    symbol=symbol,
                    quantity=quantity,
                    price=price
                ) if side == "BUY" else self.client.order_limit_sell(
                    symbol=symbol,
                    quantity=quantity,
                    price=price
                )

            print(f"✅ تم إنشاء أمر محدد {side} {quantity} {symbol} @ {price}")
            return order

        except BinanceAPIException as e:
            print(f"❌ فشل في إنشاء الأمر: {e}")
            return {}

    def place_stop_loss_order(self,
                             symbol: str,
                             side: str,
                             quantity: float,
                             stop_price: float,
                             test: bool = False) -> Dict:
        """تنفيذ أمر وقف الخسارة"""
        try:
            if self.futures:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type='STOP_MARKET',
                    quantity=quantity,
                    stopPrice=stop_price
                )
            else:
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type='STOP_LOSS',
                    quantity=quantity,
                    stopPrice=stop_price
                )
            return order
        except BinanceAPIException as e:
            print(f"❌ فشل: {e}")
            return {}

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """الحصول على الأوامر المفتوحة"""
        try:
            if self.futures:
                return self.client.futures_get_open_orders(symbol=symbol)
            return self.client.get_open_orders(symbol=symbol)
        except Exception as e:
            print(f"❌ خطأ: {e}")
            return []

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """إلغاء أمر محدد"""
        try:
            if self.futures:
                return self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
            return self.client.cancel_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            print(f"❌ خطأ: {e}")
            return {}

    def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """إلغاء جميع الأوامر المفتوحة"""
        try:
            if self.futures:
                return self.client.futures_cancel_all_open_orders(symbol=symbol)
            open_orders = self.get_open_orders(symbol)
            cancelled = []
            for order in open_orders:
                cancelled.append(self.cancel_order(symbol, order['orderId']))
            return cancelled
        except Exception as e:
            print(f"❌ خطأ: {e}")
            return []

    # ============================================================
    # 📡 WebSocket للبيانات المباشرة
    # ============================================================

    def start_websocket(self, 
                       symbol: str = "BTCUSDT",
                       callback: callable = None,
                       stream_type: str = "kline_1m"):
        """
        بدء WebSocket للبيانات المباشرة

        Args:
            symbol: زوج التداول
            callback: دالة معالجة البيانات
            stream_type: نوع البث (kline_1m, ticker, depth)
        """
        self.twm = ThreadedWebsocketManager(api_key=self.api_key, api_secret=self.api_secret)
        self.twm.start()

        if callback is None:
            callback = self._default_callback

        if stream_type.startswith("kline"):
            interval = stream_type.split("_")[1]
            self.twm.start_kline_socket(symbol=symbol, interval=interval, callback=callback)
        elif stream_type == "ticker":
            self.twm.start_symbol_ticker_socket(symbol=symbol, callback=callback)
        elif stream_type == "depth":
            self.twm.start_depth_socket(symbol=symbol, callback=callback)

        print(f"📡 WebSocket بدأ للـ {symbol} ({stream_type})")

    def _default_callback(self, msg):
        """دالة معالجة افتراضية"""
        print(f"📊 بيانات واردة: {msg.get('e', 'unknown')} - {msg.get('c', 'N/A')}")

    def stop_websocket(self):
        """إيقاف WebSocket"""
        if hasattr(self, 'twm'):
            self.twm.stop()
            print("📡 WebSocket detenido")


# ============================================================
# 🤖 البوت المتكامل مع Binance
# ============================================================

class BinanceTradingBot:
    """
    🤖 بوت التداول المتكامل مع Binance
    يجمع بين الاستراتيجيات وإدارة المخاطر وAPI
    """

    def __init__(self,
                 strategy,
                 risk_manager,
                 api: BinanceAPI,
                 symbol: str = "BTCUSDT",
                 interval: str = "1h",
                 paper_trading: bool = True):
        """
        تهيئة البوت

        Args:
            strategy: كائن الاستراتيجية
            risk_manager: كائن إدارة المخاطر
            api: كائن BinanceAPI
            symbol: زوج التداول
            interval: الفاصل الزمني
            paper_trading: True للتداول الورقي (تسجيل فقط)
        """
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.api = api
        self.symbol = symbol
        self.interval = interval
        self.paper_trading = paper_trading

        self.position = None
        self.entry_price = 0
        self.quantity = 0
        self.trades_log = []
        self.running = False

        print(f"🤖 البوت جاهز: {symbol} | {interval} | {'Paper' if paper_trading else 'LIVE'}")

    def fetch_data(self, lookback: str = "7 days ago UTC") -> pd.DataFrame:
        """جلب بيانات السوق"""
        return self.api.get_recent_klines(
            symbol=self.symbol,
            interval=self.interval,
            lookback=lookback
        )

    def analyze_and_trade(self):
        """تحليل السوق وتنفيذ التداول"""
        # جلب البيانات
        data = self.fetch_data()
        if data.empty:
            print("❌ لا توجد بيانات")
            return

        # تحليل الاستراتيجية
        signal_data = self.strategy.generate_signals(data)
        current_price = data['close'].iloc[-1]
        signal = signal_data['signal'].iloc[-1]

        # حساب ATR
        from trading_bot_framework import TechnicalIndicators
        atr = TechnicalIndicators.atr(data['high'], data['low'], data['close'], 14).iloc[-1]

        print(f"📊 {self.symbol} @ {current_price:.2f} | Signal: {signal} | ATR: {atr:.4f}")

        # منطق التداول
        if self.position is None and signal == 1:
            # فتح صفقة شراء
            self._open_long(current_price, atr)

        elif self.position == 'long' and signal == -1:
            # إغلاق صفقة
            self._close_long(current_price)

        elif self.position == 'long':
            # التحقق من وقف الخسارة وجني الأرباح
            self._check_exit_conditions(current_price)

    def _open_long(self, price: float, atr: float):
        """فتح صفقة شراء"""
        if not self.risk_manager.can_open_position():
            print("⚠️ الحد الأقصى للصفقات المفتوحة")
            return

        # الحصول على الرصيد
        balance = self.api.get_account_balance("USDT")
        available = balance.get('available_balance', balance.get('free', 0))

        # حساب حجم الصفقة
        quantity = self.risk_manager.calculate_position_size(available, price, atr)

        # حساب مستويات وقف الخسارة وجني الأرباح
        stop_loss = self.risk_manager.calculate_stop_loss(price, 'buy')
        take_profit = self.risk_manager.calculate_take_profit(price, 'buy')

        print(f"🟢 إشارة شراء: {quantity} {self.symbol} @ {price:.2f}")
        print(f"   🛑 Stop Loss: {stop_loss:.2f} | 🎯 Take Profit: {take_profit:.2f}")

        if not self.paper_trading:
            # تنفيذ فعلي
            order = self.api.place_market_order(
                symbol=self.symbol,
                side="BUY",
                quantity=quantity
            )
            if order:
                self.position = 'long'
                self.entry_price = price
                self.quantity = quantity
                self.risk_manager.open_positions += 1
        else:
            # تداول ورقي
            self.position = 'long'
            self.entry_price = price
            self.quantity = quantity
            self.risk_manager.open_positions += 1
            print("   📝 (Paper Trading - لم يُنفذ فعلياً)")

        # تسجيل الصفقة
        self.trades_log.append({
            'time': datetime.now(),
            'action': 'BUY',
            'price': price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        })

    def _close_long(self, price: float):
        """إغلاق صفقة شراء"""
        pnl = (price - self.entry_price) * self.quantity
        pnl_pct = (price - self.entry_price) / self.entry_price * 100

        print(f"🔴 إغلاق صفقة: {self.quantity} {self.symbol} @ {price:.2f}")
        print(f"   💰 P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")

        if not self.paper_trading:
            order = self.api.place_market_order(
                symbol=self.symbol,
                side="SELL",
                quantity=self.quantity
            )
        else:
            print("   📝 (Paper Trading)")

        self.position = None
        self.risk_manager.open_positions -= 1

        self.trades_log.append({
            'time': datetime.now(),
            'action': 'SELL',
            'price': price,
            'quantity': self.quantity,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })

    def _check_exit_conditions(self, current_price: float):
        """التحقق من شروط الخروج"""
        stop_loss = self.risk_manager.calculate_stop_loss(self.entry_price, 'buy')
        take_profit = self.risk_manager.calculate_take_profit(self.entry_price, 'buy')

        if current_price <= stop_loss:
            print(f"🛑 وقف الخسارة مُفعل @ {current_price:.2f}")
            self._close_long(current_price)
        elif current_price >= take_profit:
            print(f"🎯 جني الأرباح مُفعل @ {current_price:.2f}")
            self._close_long(current_price)

    def run(self, interval_seconds: int = 60):
        """
        تشغيل البوت بشكل مستمر

        Args:
            interval_seconds: الفاصل الزمني بين كل تحليل (بالثواني)
        """
        self.running = True
        print(f"🚀 البوت يعمل... (تحديث كل {interval_seconds} ثانية)")

        try:
            while self.running:
                self.analyze_and_trade()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n⏹️ إيقاف البوت...")
            self.running = False

    def stop(self):
        """إيقاف البوت"""
        self.running = False
        print("⏹️ البوت متوقف")

    def get_trades_summary(self) -> pd.DataFrame:
        """ملخص الصفقات"""
        return pd.DataFrame(self.trades_log)


# ============================================================
# 🧪 مثال الاستخدام
# ============================================================

if __name__ == "__main__":

    # 1. إعداد المفاتيح (من متغيرات البيئة)
    # export BINANCE_API_KEY="your_key"
    # export BINANCE_API_SECRET="your_secret"

    # 2. إنشاء الاتصال (Testnet للتجربة)
    api = BinanceAPI(testnet=True, futures=False)

    # 3. جلب البيانات
    data = api.get_recent_klines(symbol="BTCUSDT", interval="1h", lookback="24 hours ago UTC")
    print(data.tail())

    # 4. الحصول على السعر الحالي
    price = api.get_current_price("BTCUSDT")
    print(f"السعر الحالي: ${price}")

    # 5. الحصول على الرصيد
    balance = api.get_account_balance("USDT")
    print(f"الرصيد: {balance}")

    # 6. إنشاء البوت (Paper Trading)
    from trading_bot_framework import MultiIndicatorStrategy, RiskManager

    strategy = MultiIndicatorStrategy()
    risk = RiskManager(max_position_size=0.05, stop_loss_pct=0.02, take_profit_pct=0.04)

    bot = BinanceTradingBot(
        strategy=strategy,
        risk_manager=risk,
        api=api,
        symbol="BTCUSDT",
        interval="1h",
        paper_trading=True  # ⚠️ ابدأ بالتداول الورقي دائماً
    )

    # 7. تشغيل البوت
    # bot.run(interval_seconds=300)  # تحديث كل 5 دقائق
