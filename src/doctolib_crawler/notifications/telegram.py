import os

import requests
from dotenv import load_dotenv


load_dotenv()


def send_telegram_message(message: str) -> None:
    """Send a message to the configured Telegram chat."""

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID is not set.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=10,
    )

    response.raise_for_status()
    