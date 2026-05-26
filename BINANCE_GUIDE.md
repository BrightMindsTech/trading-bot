# دليل الربط مع Binance API

## تحذير امني مهم
مفاتيح API المكشوفة هي السبب الرئيسي لسرقة العملات الرقمية!
• احفظ المفاتيح في متغيرات بيئة (Environment Variables)
• لا تضع المفاتيح مباشرة في الكود ابدا
• امنع صلاحيات السحب (Withdrawals) في اعدادات API
• قصر الوصول على IP محدد (IP Whitelist)

---

## الخطوة 1: انشاء حساب Binance والحصول على API Keys

1. سجل في Binance: https://www.binance.com
2. اكمل التحقق KYC
3. اذهب الى: الحساب → ادارة API → انشاء API
4. امنح الصلاحيات:
   - تداول السبوت (Spot Trading)
   - تداول الهامش (Margin Trading) - اختياري
   - السحب (Withdrawals) - امنعها دائما!
5. قصر الوصول على IP محدد (IP Whitelist) - موصى به بشدة
6. احفظ الـ API Key و API Secret في مكان امن

---

## الخطوة 2: تثبيت المكتبات المطلوبة

```bash
pip install python-binance pandas numpy
```

المكتبات الرئيسية:
• python-binance - الربط الرسمي مع Binance API
• pandas - معالجة البيانات
• numpy - العمليات الحسابية

---

## الخطوة 3: اعداد متغيرات البيئة (الطريقة الامنة)

Linux/Mac (Terminal):
```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

Windows (PowerShell):
```powershell
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

او استخدم ملف .env (مع مكتبة python-dotenv):
```bash
pip install python-dotenv
```

ملف .env:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

---

## الخطوة 4: اختبار على Testnet (التداول الورقي)

Binance توفر بيئة اختبار مجانية:
• Spot Testnet: https://testnet.binance.vision
• Futures Testnet: https://testnet.binancefuture.com

الخطوات:
1. انشئ حساب Testnet (منفصل عن الحساب الحقيقي)
2. احصل على مفاتيح API خاصة بالـ Testnet
3. ابدأ بالتداول الورقي لاختبار البوت

```python
from binance.client import Client
client = Client(api_key, api_secret, testnet=True)
```

---

## الخطوة 5: الكود الاساسي للربط

```python
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import os

# 1. قراءة المفاتيح من متغيرات البيئة
api_key = os.environ.get('BINANCE_API_KEY')
api_secret = os.environ.get('BINANCE_API_SECRET')

# 2. انشاء العميل (Testnet للتجربة)
client = Client(api_key, api_secret, testnet=True)

# 3. جلب بيانات الشموع التاريخية
def get_klines(symbol="BTCUSDT", interval="1h", lookback="24 hours ago UTC"):
    klines = client.get_historical_klines(symbol, interval, lookback)

    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])

    # تحويل الاعمدة الرقمية
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])

    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)

    return df[['open', 'high', 'low', 'close', 'volume']]

# 4. الحصول على السعر الحالي
def get_price(symbol="BTCUSDT"):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker['price'])

# 5. الحصول على الرصيد
def get_balance(asset="USDT"):
    balance = client.get_asset_balance(asset=asset)
    return float(balance['free'])

# 6. تنفيذ امر سوقي
def market_order(symbol, side, quantity):
    try:
        if side == "BUY":
            order = client.order_market_buy(symbol=symbol, quantity=quantity)
        else:
            order = client.order_market_sell(symbol=symbol, quantity=quantity)
        return order
    except BinanceAPIException as e:
        print(f"Error: {e}")
        return None

# 7. تنفيذ امر محدد السعر
def limit_order(symbol, side, quantity, price):
    try:
        if side == "BUY":
            order = client.order_limit_buy(symbol=symbol, quantity=quantity, price=price)
        else:
            order = client.order_limit_sell(symbol=symbol, quantity=quantity, price=price)
        return order
    except BinanceAPIException as e:
        print(f"Error: {e}")
        return None
```

---

## الخطوة 6: ربط البوت مع Binance

```python
from trading_bot_framework import MultiIndicatorStrategy, RiskManager, TechnicalIndicators
from binance.client import Client
import pandas as pd
import time

# اعدادات API
api_key = os.environ.get('BINANCE_API_KEY')
api_secret = os.environ.get('BINANCE_API_SECRET')
client = Client(api_key, api_secret, testnet=True)

# اعدادات البوت
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
PAPER_TRADING = True  # ابدأ بالتداول الورقي دائما

# انشاء الاستراتيجية وادارة المخاطر
strategy = MultiIndicatorStrategy()
risk = RiskManager(
    max_position_size=0.05,    # 5% من راس المال
    stop_loss_pct=0.02,        # وقف خسارة 2%
    take_profit_pct=0.04,      # جني ارباح 4%
    trailing_stop=True
)

# دالة جلب البيانات من Binance
def fetch_binance_data(symbol, interval, lookback="7 days ago UTC"):
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    return df[['open', 'high', 'low', 'close', 'volume']]

# حلقة التداول الرئيسية
def trading_loop():
    position = None
    entry_price = 0
    quantity = 0

    while True:
        try:
            # جلب البيانات
            data = fetch_binance_data(SYMBOL, INTERVAL)
            current_price = data['close'].iloc[-1]

            # تحليل الاستراتيجية
            signals = strategy.generate_signals(data)
            signal = signals['signal'].iloc[-1]

            # حساب ATR
            atr = TechnicalIndicators.atr(data['high'], data['low'], data['close'], 14).iloc[-1]

            print(f"[{pd.Timestamp.now()}] {SYMBOL} @ ${current_price:.2f} | Signal: {signal}")

            # منطق التداول
            if position is None and signal == 1:
                # فتح صفقة شراء
                balance = float(client.get_asset_balance('USDT')['free'])
                qty = risk.calculate_position_size(balance, current_price, atr)

                if PAPER_TRADING:
                    print(f"[PAPER] شراء {qty} {SYMBOL} @ {current_price}")
                else:
                    order = client.order_market_buy(symbol=SYMBOL, quantity=qty)
                    print(f"شراء {qty} {SYMBOL} @ {current_price}")

                position = 'long'
                entry_price = current_price
                quantity = qty

            elif position == 'long' and signal == -1:
                # اغلاق صفقة
                pnl = (current_price - entry_price) * quantity
                pnl_pct = (current_price - entry_price) / entry_price * 100

                if PAPER_TRADING:
                    print(f"[PAPER] بيع {quantity} {SYMBOL} @ {current_price} | P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
                else:
                    order = client.order_market_sell(symbol=SYMBOL, quantity=quantity)
                    print(f"بيع {quantity} {SYMBOL} @ {current_price} | P&L: ${pnl:.2f}")

                position = None
                entry_price = 0
                quantity = 0

            # انتظر 5 دقائق
            time.sleep(300)

        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(60)

# تشغيل البوت
if __name__ == "__main__":
    print("بدء البوت...")
    print("تأكد من انك على Testnet!")
    trading_loop()
```

---

## الخطوة 7: WebSocket للبيانات المباشرة (اسرع)

```python
from binance import ThreadedWebsocketManager
import pandas as pd

api_key = os.environ.get('BINANCE_API_KEY')
api_secret = os.environ.get('BINANCE_API_SECRET')

# انشاء مدير WebSocket
twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
twm.start()

def handle_socket_message(msg):
    if msg['e'] == 'kline':
        kline = msg['k']
        print(f"شمعة جديدة: {kline['s']} | O: {kline['o']} | C: {kline['c']}")
    elif msg['e'] == 'trade':
        print(f"تداول: {msg['s']} | السعر: {msg['p']} | الكمية: {msg['q']}")
    elif msg['e'] == '24hrTicker':
        print(f"{msg['s']}: ${msg['c']} | تغير 24h: {msg['P']}%")

# بدء الاستماع
# 1. بث الشموع (Klines)
twm.start_kline_socket(symbol='BTCUSDT', interval='1m', callback=handle_socket_message)

# 2. بث السعر المباشر
# twm.start_symbol_ticker_socket(symbol='BTCUSDT', callback=handle_socket_message)

# 3. بث دفتر الطلبات (Order Book)
# twm.start_depth_socket(symbol='BTCUSDT', callback=handle_socket_message)

print("WebSocket يعمل... اضغط Ctrl+C للايقاف")

try:
    twm.join()
except KeyboardInterrupt:
    twm.stop()
    print("WebSocket detenido")
```

---

## ملخص API Calls المهمة

| العملية | Spot | Futures |
|---------|------|---------|
| السعر الحالي | get_symbol_ticker() | futures_symbol_ticker() |
| بيانات الشموع | get_historical_klines() | futures_historical_klines() |
| الرصيد | get_asset_balance() | futures_account() |
| امر سوقي | order_market_buy/sell() | futures_create_order() |
| امر محدد | order_limit_buy/sell() | futures_create_order() |
| وقف خسارة | create_order() | futures_create_order() |
| الاوامر المفتوحة | get_open_orders() | futures_get_open_orders() |
| الغاء امر | cancel_order() | futures_cancel_order() |

---

## نصائح امنية مهمة

1. لا تضع مفاتيح API في الكود ابدا
2. استخدم متغيرات البيئة او ملف .env
3. امنع صلاحيات السحب (Withdrawals)
4. قصر الوصول على IP محدد
5. استخدم Testnet قبل التداول الحقيقي
6. ابدأ براس مال صغير جدا (10-20%)
7. راقب البوت باستمرار في الايام الاولى
8. استخدم VPS/Cloud Server للتشغيل 24/7

---

## خطوات التنفيذ الموصى بها

1. اختبار الباكتست على بيانات تاريخية (2-3 سنوات)
2. التحقق من صحة النتائج على بيانات خارج العينة (Out-of-Sample)
3. تشغيل التداول الورقي (Paper Trading) لمدة 2-4 اسابيع على Testnet
4. البدء براس مال صغير (10-20% من راس المال المخطط)
5. مراقبة الاداء المستمر ومقارنته مع الباكتست
6. زيادة راس المال تدريجيا بعد تأكيد الاداء
7. ايقاف البوت اذا انحرف الاداء بشكل كبير عن التوقعات

---

تحذير: هذا الدليل للاغراض التعليمية والبحثية فقط. التداول يحمل مخاطر كبيرة وقد تخسر راس مالك بالكامل. اختبر الاستراتيجيات جيدا قبل استخدامها في السوق الحقيقي.
