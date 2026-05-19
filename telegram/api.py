import os

import httpx

from app.utils import get_logger

logger = get_logger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def send_message(
    chat_id: str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML",
) -> dict:
    client = _get_client()
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    resp = await client.post(f"{BASE_URL}/sendMessage", json=payload)
    data = resp.json()
    if not data.get("ok"):
        logger.error("sendMessage failed for chat %s: %s", chat_id, data)
    return data


async def edit_message_text(
    chat_id: str,
    message_id: int,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str = "HTML",
) -> dict:
    client = _get_client()
    payload: dict = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    resp = await client.post(f"{BASE_URL}/editMessageText", json=payload)
    data = resp.json()
    if not data.get("ok"):
        logger.error("editMessageText failed for chat %s: %s", chat_id, data)
    return data


async def answer_callback_query(
    callback_query_id: str,
    text: str | None = None,
) -> dict:
    client = _get_client()
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    resp = await client.post(f"{BASE_URL}/answerCallbackQuery", json=payload)
    data = resp.json()
    if not data.get("ok"):
        logger.error("answerCallbackQuery failed: %s", data)
    return data


async def get_updates(offset: int | None = None, timeout: int = 30) -> list[dict]:
    client = _get_client()
    payload: dict = {
        "timeout": timeout,
        "allowed_updates": ["message", "callback_query"],
    }
    if offset is not None:
        payload["offset"] = offset
    resp = await client.post(f"{BASE_URL}/getUpdates", json=payload, timeout=timeout + 10)
    data = resp.json()
    if not data.get("ok"):
        logger.error("getUpdates failed: %s", data)
        return []
    return data.get("result", [])


async def delete_webhook() -> dict:
    client = _get_client()
    resp = await client.post(f"{BASE_URL}/deleteWebhook")
    data = resp.json()
    logger.info("deleteWebhook: %s", data)
    return data
