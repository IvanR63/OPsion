import asyncio
import requests
from datetime import datetime
from telegram import Bot
import os

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

TICKERS = ["TSLA", "SPY", "QQQ"]
CHECK_INTERVAL = 60

bot = Bot(token=TELEGRAM_TOKEN)

def fetch_options_flow(symbol):
    url = f"https://finnhub.io/api/v1/stock/option-chain?symbol={symbol}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    alerts = []
    for d in data.get("data", []):
        for option in d.get("options", []):
            volume = option.get("volume", 0)
            oi = option.get("openInterest", 1)
            premium = option.get("lastPrice", 0) * volume
            if oi == 0: oi = 1
            if volume > oi * 5 and premium > 1_000_000:
                alert = {
                    "type": option.get("type"),
                    "strike": option.get("strike"),
                    "expiration": option.get("expirationDate"),
                    "volume": volume,
                    "oi": oi,
                }
                alerts.append(alert)
    return alerts

async def main():
    while True:
        for symbol in TICKERS:
            alerts = fetch_options_flow(symbol)
            if alerts:
                for alert in alerts:
                    message = (
                        f"{symbol} {alert['type'].upper()} ALERT\n"
                        f"Strike: {alert['strike']}\n"
                        f"Expiration: {alert['expiration']}\n"
                        f"Volume: {alert['volume']} | OI: {alert['oi']}"
                    )
                    bot.send_message(chat_id=CHAT_ID, text=message)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
