import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


LOG_PATH = Path("logs/bot.log")
PID_PATH = Path("logs/bot.pid")


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _read_pid() -> int | None:
    if not PID_PATH.exists():
        return None
    try:
        return int(PID_PATH.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def _write_pid(pid: int) -> None:
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(pid), encoding="utf-8")


def _clear_pid() -> None:
    try:
        PID_PATH.unlink(missing_ok=True)
    except Exception:
        pass


def _start_bot() -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)
    # Start in a separate process so Streamlit stays responsive.
    proc = subprocess.Popen(
        [sys.executable, "run_bot_to_log.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
    )
    _write_pid(proc.pid)


def _stop_bot(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)  # since start_new_session=True
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    _clear_pid()


st.set_page_config(page_title="Trading Bot Interface", layout="wide")
st.title("Trading Bot Interface")

pid = _read_pid()
running = bool(pid) and _is_running(pid)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.metric("Status", "RUNNING" if running else "STOPPED")
with col2:
    if running:
        if st.button("Stop bot", type="primary"):
            _stop_bot(pid)  # type: ignore[arg-type]
            st.rerun()
    else:
        if st.button("Start bot", type="primary"):
            _start_bot()
            st.rerun()
with col3:
    st.caption("Logs are written to `logs/bot.log` by `run_bot_to_log.py`.")

with st.expander("Settings (env vars)", expanded=False):
    st.code(
        "\n".join(
            [
                "SYMBOL=BTCUSDT",
                "INTERVAL=1h",
                "LOOKBACK=7 days ago UTC",
                "SLEEP_SECONDS=300",
                "PAPER_TRADING=true",
                "TESTNET=true",
                "FUTURES=false",
            ]
        )
    )
    st.caption("Set these in your shell (or `.env`) before clicking Start.")

st.divider()

left, right = st.columns([2, 1])
with left:
    st.subheader("Live log")
with right:
    auto_refresh = st.toggle("Auto refresh", value=True)
    refresh_seconds = st.number_input("Refresh seconds", min_value=1, max_value=60, value=2)

filter_text = st.text_input("Filter (contains)", value="")
max_lines = st.number_input("Max lines", min_value=100, max_value=50000, value=4000, step=100)

meta_left, meta_right = st.columns([2, 1])
with meta_left:
    st.caption(f"Log file: `{LOG_PATH}`")
with meta_right:
    if LOG_PATH.exists():
        st.caption(f"Size: {LOG_PATH.stat().st_size} bytes")

show_full_file = st.toggle("Show full raw file", value=False, help="If off, shows only the last N lines.")

if LOG_PATH.exists():
    raw = LOG_PATH.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    if filter_text.strip():
        ft = filter_text.strip().lower()
        lines = [ln for ln in lines if ft in ln.lower()]
    if not show_full_file:
        lines = lines[-int(max_lines) :]
    st.code("\n".join(lines) if lines else "(no matching log lines yet)")

    st.download_button(
        label="Download bot.log",
        data=raw,
        file_name="bot.log",
        mime="text/plain",
        use_container_width=True,
    )
else:
    st.info("No log yet. Click Start bot to begin logging.")

if auto_refresh:
    st.caption("Auto refresh enabled.")
    time.sleep(int(refresh_seconds))
    st.rerun()

