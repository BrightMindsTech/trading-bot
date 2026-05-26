
# ============================================================
# 🤖 Trading Bot Framework - الإصدار الكامل
# ============================================================
# مؤلف: Trading Bot Builder
# الوصف: إطار عمل متكامل لبناء بوتات التداول
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ============================================================
# أنواع الأوامر والهياكل
# ============================================================

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"
    NONE = "none"

@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

# ============================================================
# المؤشرات الفنية
# ============================================================

class TechnicalIndicators:
    """مجموعة شاملة من المؤشرات الفنية"""

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2):
        middle = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

# ============================================================
# الاستراتيجيات
# ============================================================

class TradingStrategy:
    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

class RSIStrategy(TradingStrategy):
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Strategy", {'rsi_period': rsi_period, 'oversold': oversold, 'overbought': overbought})

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['RSI'] = TechnicalIndicators.rsi(df['close'], self.params['rsi_period'])
        df['signal'] = 0
        df.loc[df['RSI'] < self.params['oversold'], 'signal'] = 1
        df.loc[df['RSI'] > self.params['overbought'], 'signal'] = -1
        return df

class MACDStrategy(TradingStrategy):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("MACD Strategy", {'fast': fast, 'slow': slow, 'signal': signal})

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        macd, signal_line, histogram = TechnicalIndicators.macd(
            df['close'], self.params['fast'], self.params['slow'], self.params['signal'])
        df['MACD'] = macd
        df['Signal_Line'] = signal_line
        df['signal'] = 0
        df.loc[(macd > signal_line) & (macd.shift(1) <= signal_line.shift(1)), 'signal'] = 1
        df.loc[(macd < signal_line) & (macd.shift(1) >= signal_line.shift(1)), 'signal'] = -1
        return df

class BollingerBandsStrategy(TradingStrategy):
    def __init__(self, period: int = 20, std_dev: int = 2):
        super().__init__("Bollinger Bands Strategy", {'period': period, 'std_dev': std_dev})

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            df['close'], self.params['period'], self.params['std_dev'])
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower
        df['signal'] = 0
        df.loc[df['close'] < lower, 'signal'] = 1
        df.loc[df['close'] > upper, 'signal'] = -1
        return df

class GoldenCrossStrategy(TradingStrategy):
    def __init__(self, fast_period: int = 50, slow_period: int = 200):
        super().__init__("Golden Cross Strategy", {'fast_period': fast_period, 'slow_period': slow_period})

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['SMA_Fast'] = TechnicalIndicators.sma(df['close'], self.params['fast_period'])
        df['SMA_Slow'] = TechnicalIndicators.sma(df['close'], self.params['slow_period'])
        df['signal'] = 0
        df.loc[(df['SMA_Fast'] > df['SMA_Slow']) & 
               (df['SMA_Fast'].shift(1) <= df['SMA_Slow'].shift(1)), 'signal'] = 1
        df.loc[(df['SMA_Fast'] < df['SMA_Slow']) & 
               (df['SMA_Fast'].shift(1) >= df['SMA_Slow'].shift(1)), 'signal'] = -1
        return df

class MultiIndicatorStrategy(TradingStrategy):
    def __init__(self, rsi_period: int = 14, rsi_oversold: int = 35, rsi_overbought: int = 65,
                 bb_period: int = 20, bb_std: int = 2):
        super().__init__("Multi-Indicator Strategy", {
            'rsi_period': rsi_period, 'rsi_oversold': rsi_oversold,
            'rsi_overbought': rsi_overbought, 'bb_period': bb_period, 'bb_std': bb_std})

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['RSI'] = TechnicalIndicators.rsi(df['close'], self.params['rsi_period'])
        macd, signal_line, histogram = TechnicalIndicators.macd(df['close'])
        df['MACD'] = macd
        df['MACD_Signal'] = signal_line
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            df['close'], self.params['bb_period'], self.params['bb_std'])
        df['BB_Upper'] = upper
        df['BB_Lower'] = lower

        rsi_buy = df['RSI'] < self.params['rsi_oversold']
        rsi_sell = df['RSI'] > self.params['rsi_overbought']
        macd_buy = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        macd_sell = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        bb_buy = df['close'] < lower
        bb_sell = df['close'] > upper

        df['signal'] = 0
        df.loc[(rsi_buy.astype(int) + macd_buy.astype(int) + bb_buy.astype(int)) >= 2, 'signal'] = 1
        df.loc[(rsi_sell.astype(int) + macd_sell.astype(int) + bb_sell.astype(int)) >= 2, 'signal'] = -1
        return df

# ============================================================
# إدارة المخاطر
# ============================================================

class RiskManager:
    def __init__(self, max_position_size: float = 0.1, stop_loss_pct: float = 0.02,
                 take_profit_pct: float = 0.04, max_daily_loss: float = 0.05,
                 max_drawdown: float = 0.15, risk_reward_ratio: float = 2.0,
                 trailing_stop: bool = True, trailing_stop_pct: float = 0.015,
                 max_open_positions: int = 3, volatility_adjustment: bool = True):
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.risk_reward_ratio = risk_reward_ratio
        self.trailing_stop = trailing_stop
        self.trailing_stop_pct = trailing_stop_pct
        self.max_open_positions = max_open_positions
        self.volatility_adjustment = volatility_adjustment
        self.peak_equity = 0.0
        self.current_drawdown = 0.0
        self.open_positions = 0

    def calculate_position_size(self, capital: float, current_price: float, atr: Optional[float] = None):
        base_size = capital * self.max_position_size
        if self.volatility_adjustment and atr is not None and atr > 0 and current_price > 0:
            volatility_factor = min(1.0, 0.02 / (atr / current_price))
            base_size *= volatility_factor
        return round(base_size / current_price, 4)

    def calculate_stop_loss(self, entry_price: float, side: str):
        if side == 'buy':
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    def calculate_take_profit(self, entry_price: float, side: str):
        if side == 'buy':
            return entry_price * (1 + self.take_profit_pct)
        return entry_price * (1 - self.take_profit_pct)

    def can_open_position(self) -> bool:
        """Return True when we are below the configured open-position limit."""
        return self.open_positions < self.max_open_positions

    def update_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        highest_price: float,
        side: str
    ) -> Optional[float]:
        """
        Compute trailing-stop price for an open trade.
        Returns None when trailing stop is disabled.
        """
        if not self.trailing_stop:
            return None

        if side == 'buy':
            base_stop = entry_price * (1 - self.stop_loss_pct)
            trailing_level = highest_price * (1 - self.trailing_stop_pct)
            return max(base_stop, trailing_level)

        base_stop = entry_price * (1 + self.stop_loss_pct)
        trailing_level = highest_price * (1 + self.trailing_stop_pct)
        return min(base_stop, trailing_level)

# ============================================================
# محرك الباكتست
# ============================================================

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.capital = initial_capital
        self.equity_curve = []
        self.trades = []

    def run_backtest(self, data: pd.DataFrame, strategy: TradingStrategy, risk_manager: RiskManager = None):
        if risk_manager is None:
            risk_manager = RiskManager()

        df = strategy.generate_signals(data.copy())
        position = None
        entry_price = 0
        entry_time = None
        highest_price = 0
        position_size = 0

        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            current_time = df.index[i]
            signal = df['signal'].iloc[i]
            atr = TechnicalIndicators.atr(df['high'], df['low'], df['close'], 14).iloc[i] if i > 14 else None

            if position is None and signal == 1 and risk_manager.can_open_position():
                position_size = risk_manager.calculate_position_size(self.capital, current_price, atr)
                cost = position_size * current_price * (1 + self.commission + self.slippage)
                if cost <= self.capital:
                    position = 'long'
                    entry_price = current_price
                    entry_time = current_time
                    highest_price = current_price
                    risk_manager.open_positions += 1
                    self.trades.append({'entry_time': entry_time, 'entry_price': entry_price, 
                                       'quantity': position_size, 'side': 'buy'})

            if position == 'long':
                highest_price = max(highest_price, current_price)
                stop_loss = risk_manager.calculate_stop_loss(entry_price, 'buy')
                take_profit = risk_manager.calculate_take_profit(entry_price, 'buy')
                trailing_stop = risk_manager.update_trailing_stop(entry_price, current_price, highest_price, 'buy')

                close_trade = False
                close_reason = ''
                if current_price <= stop_loss:
                    close_trade, close_reason = True, 'stop_loss'
                elif current_price >= take_profit:
                    close_trade, close_reason = True, 'take_profit'
                elif trailing_stop and current_price <= trailing_stop:
                    close_trade, close_reason = True, 'trailing_stop'
                elif signal == -1:
                    close_trade, close_reason = True, 'signal'

                if close_trade:
                    exit_price = current_price * (1 - self.slippage)
                    pnl = (exit_price - entry_price) * position_size
                    self.capital += pnl - (position_size * exit_price * self.commission)
                    self.trades[-1].update({'exit_time': current_time, 'exit_price': exit_price,
                                           'pnl': pnl, 'reason': close_reason})
                    position = None
                    risk_manager.open_positions -= 1

            equity = self.capital
            if position == 'long':
                equity += (current_price - entry_price) * position_size
            self.equity_curve.append(equity)

        return self._calculate_metrics()

    def _calculate_metrics(self):
        equity_series = pd.Series(self.equity_curve)
        returns = equity_series.pct_change().dropna()
        closed_trades = [t for t in self.trades if 'pnl' in t]
        pnl_list = [t['pnl'] for t in closed_trades]
        winning_trades = [p for p in pnl_list if p > 0]
        losing_trades = [p for p in pnl_list if p <= 0]

        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100
        peak = equity_series.expanding(min_periods=1).max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min() * 100
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 and returns.std() != 0 else 0

        return {
            'total_return_pct': round(total_return, 2),
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate_pct': round(len(winning_trades) / len(closed_trades) * 100, 2) if closed_trades else 0,
            'avg_win': round(np.mean(winning_trades), 2) if winning_trades else 0,
            'avg_loss': round(np.mean(losing_trades), 2) if losing_trades else 0,
            'profit_factor': round(abs(sum(winning_trades) / sum(losing_trades)), 2) if losing_trades and sum(losing_trades) != 0 else float('inf'),
            'max_drawdown_pct': round(abs(max_drawdown), 2),
            'sharpe_ratio': round(sharpe, 2),
            'final_capital': round(self.capital, 2),
            'equity_curve': self.equity_curve,
            'trades': closed_trades
        }

# ============================================================
# البوت التداولي
# ============================================================

class TradingBot:
    def __init__(self, strategy: TradingStrategy, risk_manager: RiskManager,
                 initial_capital: float = 10000.0, symbol: str = "BTCUSDT", timeframe: str = "1h"):
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.symbol = symbol
        self.timeframe = timeframe
        self.trades_history = []
        self.equity_curve = [initial_capital]

    def analyze_market(self, data: pd.DataFrame) -> Dict:
        signal_data = self.strategy.generate_signals(data)
        last_signal = signal_data['signal'].iloc[-1]
        current_price = data['close'].iloc[-1]
        atr = TechnicalIndicators.atr(data['high'], data['low'], data['close'], 14).iloc[-1]

        analysis = {
            'symbol': self.symbol,
            'current_price': round(current_price, 2),
            'signal': 'BUY' if last_signal == 1 else 'SELL' if last_signal == -1 else 'HOLD',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'strategy': self.strategy.name
        }

        if last_signal == 1 and self.risk_manager.can_open_position():
            position_size = self.risk_manager.calculate_position_size(self.capital, current_price, atr)
            analysis['recommendation'] = {
                'action': 'BUY',
                'quantity': position_size,
                'entry_price': round(current_price, 2),
                'stop_loss': round(self.risk_manager.calculate_stop_loss(current_price, 'buy'), 2),
                'take_profit': round(self.risk_manager.calculate_take_profit(current_price, 'buy'), 2)
            }
        else:
            analysis['recommendation'] = {'action': 'HOLD', 'reason': 'No clear signal'}

        return analysis

    def run_simulation(self, data: pd.DataFrame, verbose: bool = True):
        engine = BacktestEngine(initial_capital=self.initial_capital)
        metrics = engine.run_backtest(data, self.strategy, self.risk_manager)
        self.capital = metrics['final_capital']
        self.equity_curve = metrics['equity_curve']
        if verbose:
            print(f"Strategy: {self.strategy.name}")
            print(f"Total Return: {metrics['total_return_pct']}%")
            print(f"Win Rate: {metrics['win_rate_pct']}%")
            print(f"Max Drawdown: {metrics['max_drawdown_pct']}%")
            print(f"Sharpe Ratio: {metrics['sharpe_ratio']}")
        return metrics

# ============================================================
# مثال الاستخدام
# ============================================================

if __name__ == "__main__":
    # إنشاء بيانات تجريبية
    np.random.seed(42)
    n_days = 500
    returns = np.random.normal(0.0005, 0.02, n_days)
    price = 100 * np.cumprod(1 + returns)
    dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')

    df = pd.DataFrame({
        'open': price * (1 + np.random.normal(0, 0.005, n_days)),
        'high': price * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        'low': price * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        'close': price,
        'volume': np.random.randint(1000000, 10000000, n_days)
    }, index=dates)

    df['high'] = np.maximum(df['high'], df[['open', 'close']].max(axis=1))
    df['low'] = np.minimum(df['low'], df[['open', 'close']].min(axis=1))

    # إنشاء البوت
    strategy = MultiIndicatorStrategy()
    risk = RiskManager(max_position_size=0.05, stop_loss_pct=0.02, take_profit_pct=0.04)
    bot = TradingBot(strategy=strategy, risk_manager=risk, initial_capital=10000)

    # تحليل السوق
    analysis = bot.analyze_market(df)
    print("Market Analysis:", analysis)

    # تشغيل المحاكاة
    metrics = bot.run_simulation(df)
