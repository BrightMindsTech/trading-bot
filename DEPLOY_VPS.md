# Deploy on VPS (EU region) — real Binance, no demo

Streamlit Community Cloud is blocked by Binance geo-restrictions.  
Run the app on a **VPS in Europe** (same code, real Testnet API).

## 1) Create a VPS

Pick a provider and an **EU location** (examples):

| Provider | Region examples |
|----------|-----------------|
| [Hetzner](https://www.hetzner.com/cloud) | Helsinki, Nuremberg, Falkenstein |
| [DigitalOcean](https://www.digitalocean.com) | Frankfurt, Amsterdam |
| [AWS Lightsail](https://lightsail.aws.amazon.com) | eu-central-1 (Frankfurt) |

**OS:** Ubuntu 22.04 or 24.04  
**Size:** 1 vCPU / 1–2 GB RAM is enough to start  
**Auth:** SSH key (recommended)

## 2) SSH into the server

```bash
ssh root@YOUR_SERVER_IP
# or: ssh ubuntu@YOUR_SERVER_IP
```

## 3) Clone the repo

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/BrightMindsTech/trading-bot.git
cd trading-bot
```

## 4) Add your Binance Testnet keys

```bash
cp .env.example .env
nano .env
```

Example `.env`:

```env
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
SYMBOL=BTCUSDT
INTERVAL=1h
LOOKBACK=7 days ago UTC
SLEEP_SECONDS=300
PAPER_TRADING=true
TESTNET=true
FUTURES=false
```

## 5) Run the installer

```bash
chmod +x deploy/setup_vps.sh
bash deploy/setup_vps.sh
```

## 6) Start the app

```bash
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

Open in your browser:

```text
http://YOUR_SERVER_IP:8501
```

Click **Start bot** in the UI.

## Useful commands

```bash
# Live service logs
sudo journalctl -u trading-bot -f

# Restart after code or .env changes
cd ~/trading-bot && git pull
bash deploy/setup_vps.sh   # if dependencies changed
sudo systemctl restart trading-bot

# Bot file log (from UI runner)
tail -f ~/trading-bot/logs/bot.log
```

## Optional: HTTPS with a domain

1. Point DNS `A` record → VPS IP  
2. Install Caddy or Nginx reverse proxy to port `8501`  
3. Restrict port `8501` in firewall to localhost only after proxy is working

## Security checklist

- Keep `PAPER_TRADING=true` and `TESTNET=true` until you are confident
- Never commit `.env`
- Use Binance API keys **without withdrawal** permission
- Prefer SSH keys; disable password SSH if possible
- Consider IP whitelist on Binance API (your VPS public IP)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Binance geo error | VPS must be in EU; not US Streamlit Cloud |
| Empty `bot.log` | `sudo systemctl restart trading-bot`, click Start again |
| API key invalid | Regenerate Testnet keys; no extra spaces in `.env` |
| Cannot open :8501 | `sudo ufw allow 8501` and check cloud provider firewall |
