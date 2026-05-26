import os
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def main() -> int:
    """
    Runs the BinanceTradingBot and mirrors stdout/stderr into logs/bot.log.

    Configure via environment variables:
      - SYMBOL (default: BTCUSDT)
      - INTERVAL (default: 1h)
      - LOOKBACK (default: 7 days ago UTC)
      - SLEEP_SECONDS (default: 300)
      - PAPER_TRADING (default: true)
      - TESTNET (default: true)
      - FUTURES (default: false)
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "bot.log"

    # Ensure we start a fresh file each run for readability.
    # Use line buffering so logs appear immediately in the UI.
    f = open(log_path, "w", encoding="utf-8", buffering=1)

    with redirect_stdout(f), redirect_stderr(f):
        try:
            # Import inside redirected context so any import-time prints are captured.
            from binance_connector import BinanceAPI, BinanceTradingBot  # noqa
            from trading_bot_framework import MultiIndicatorStrategy, RiskManager  # noqa

            symbol = os.environ.get("SYMBOL", "BTCUSDT")
            interval = os.environ.get("INTERVAL", "1h")
            lookback = os.environ.get("LOOKBACK", "7 days ago UTC")
            sleep_seconds = int(os.environ.get("SLEEP_SECONDS", "300"))
            paper_trading = os.environ.get("PAPER_TRADING", "true").lower() in {"1", "true", "yes", "y"}
            testnet = os.environ.get("TESTNET", "true").lower() in {"1", "true", "yes", "y"}
            futures = os.environ.get("FUTURES", "false").lower() in {"1", "true", "yes", "y"}

            print("========================================", flush=True)
            print("Trading Bot Runner (logs/bot.log)", flush=True)
            print(f"SYMBOL={symbol} INTERVAL={interval} LOOKBACK={lookback}", flush=True)
            print(f"TESTNET={testnet} FUTURES={futures} PAPER_TRADING={paper_trading}", flush=True)
            print("========================================", flush=True)

            api = BinanceAPI(testnet=testnet, futures=futures)
            strategy = MultiIndicatorStrategy()
            risk = RiskManager(max_position_size=0.05, stop_loss_pct=0.02, take_profit_pct=0.04)

            bot = BinanceTradingBot(
                strategy=strategy,
                risk_manager=risk,
                api=api,
                symbol=symbol,
                interval=interval,
                paper_trading=paper_trading,
            )

            # Prime with a single data fetch summary.
            df = bot.fetch_data(lookback=lookback)
            latest_close = df["close"].iloc[-1] if not df.empty else "N/A"
            print(f"Fetched {len(df)} candles. Latest close: {latest_close}", flush=True)

            bot.run(interval_seconds=sleep_seconds)
        except Exception:
            print("\nRunner crashed with exception:\n", flush=True)
            traceback.print_exc()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

