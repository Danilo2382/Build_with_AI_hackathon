"""
Telegram Bot helper.
Bot token is loaded from Firestore (app_config/telegram) on first use.
"""
import logging

import httpx
from google.cloud import firestore

logger = logging.getLogger(__name__)

_bot_token: str | None = None


async def _get_bot_token() -> str:
    global _bot_token
    if _bot_token is None:
        db = firestore.AsyncClient()
        snap = await db.collection("app_config").document("telegram").get()
        data = snap.to_dict() or {}
        _bot_token = data.get("bot_token", "")
    return _bot_token


async def send_message(chat_id: str, text: str) -> bool:
    """Send a Telegram message to the given chat_id. Returns True on success."""
    token = await _get_bot_token()
    if not token:
        logger.error("Telegram bot token not configured in app_config/telegram")
        return False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            r.raise_for_status()
            return True
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False
