
# 🤖 Trading Bot Framework - دليل الاستخدام

## نظرة عامة
إطار عمل متكامل لبناء واختبار بوتات التداول الآلي باستخدام Python.

## المكونات الرئيسية

### 1. المؤشرات الفنية (TechnicalIndicators)
- SMA, EMA
- RSI, MACD
- Bollinger Bands
- ATR, Stochastic
- Ichimoku Cloud, VWAP
- Fibonacci Retracement

### 2. الاستراتيجيات (TradingStrategy)
- **RSI Strategy**: التشبع البيعي/الشرائي
- **MACD Strategy**: تقاطعات MACD
- **Bollinger Bands Strategy**: الانعكاسات عند النطاقات
- **Golden Cross Strategy**: التقاطع الذهبي
- **Mean Reversion Strategy**: العودة للمتوسط
- **Breakout Strategy**: اختراق المستويات
- **Multi-Indicator Strategy**: تأكيد متعدد المؤشرات (الأقوى)

### 3. إدارة المخاطر (RiskManager)
- حد أقصى لحجم الصفقة
- وقف خسارة وجني أرباح
- وقف خسارة متحرك
- حد يومي للخسارة
- حد أقصى للتراجع
- تعديل حجم الصفقة حسب التقلب

### 4. محرك الباكتست (BacktestEngine)
- محاكاة كاملة للتداول
- حساب العمولات والانزلاق السعري
- مقاييس الأداء الشاملة

## كيفية الاستخدام

```python
from trading_bot_framework import *

# تحميل البيانات
data = pd.read_csv('your_data.csv', index_col=0, parse_dates=True)

# اختيار الاستراتيجية
strategy = MultiIndicatorStrategy()

# إعداد إدارة المخاطر
risk = RiskManager(
    max_position_size=0.05,    # 5% من رأس المال
    stop_loss_pct=0.02,        # وقف خسارة 2%
    take_profit_pct=0.04,      # جني أرباح 4%
    trailing_stop=True
)

# إنشاء البوت
bot = TradingBot(
    strategy=strategy,
    risk_manager=risk,
    initial_capital=10000,
    symbol="BTCUSDT"
)

# تحليل السوق
analysis = bot.analyze_market(data)
print(analysis)

# تشغيل المحاكاة
metrics = bot.run_simulation(data)
```

## مقاييس الأداء
- العائد الإجمالي
- نسبة النجاح
- الحد الأقصى للتراجع
- نسبة شارب
- معامل الربحية

## تحذيرات مهمة
⚠️ هذا الإطار للأغراض التعليمية والبحثية فقط.
⚠️ التداول يحمل مخاطر كبيرة وقد تخسر رأس مالك بالكامل.
⚠️ اختبر الاستراتيجيات جيداً قبل استخدامها في السوق الحقيقي.
⚠️ لا تضع أموالاً لا تستطيع تحمل خسارتها.
