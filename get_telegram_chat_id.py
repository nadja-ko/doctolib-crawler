import os

import requests
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")

if not token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")


url = f"https://api.telegram.org/bot{token}/getUpdates"

print("Waiting for a Telegram message...")
print("Now send /start or hello to @nadja_ko_bot in Telegram.")

response = requests.get(
    url,
    params={"timeout": 30},
    timeout=35,
)

response.raise_for_status()

data = response.json()

print("\nTelegram response:")
print(data)

for update in data["result"]:
    message = update.get("message")

    if message:
        print("\nFOUND MESSAGE")
        print("Chat ID:", message["chat"]["id"])
        print("Message:", message.get("text"))