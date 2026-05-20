import os

import httpx

from app.utils import get_logger

logger = get_logger(__name__)


class TelegramBot:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def send_message(
        self,
        chat_id: str,
        text: str,
        reply_markup: dict | None = None,
        parse_mode: str = "HTML",
    ) -> dict:
        client = self._get_client()
        payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = await client.post(f"{self.base_url}/sendMessage", json=payload)
        data = resp.json()
        if not data.get("ok"):
            logger.error("sendMessage failed for chat %s: %s", chat_id, data)
        return data

    async def edit_message_text(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        reply_markup: dict | None = None,
        parse_mode: str = "HTML",
    ) -> dict:
        client = self._get_client()
        payload: dict = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = await client.post(f"{self.base_url}/editMessageText", json=payload)
        data = resp.json()
        if not data.get("ok"):
            logger.error("editMessageText failed for chat %s: %s", chat_id, data)
        return data

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str | None = None,
    ) -> dict:
        client = self._get_client()
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        resp = await client.post(f"{self.base_url}/answerCallbackQuery", json=payload)
        data = resp.json()
        if not data.get("ok"):
            logger.error("answerCallbackQuery failed: %s", data)
        return data

    async def set_webhook(self, webhook_url: str) -> dict:
        client = self._get_client()
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
        }
        resp = await client.post(f"{self.base_url}/setWebhook", json=payload)
        data = resp.json()
        logger.info("setWebhook: %s", data)
        return data


ga_bot = TelegramBot(os.environ.get("GA_BOT_TOKEN", ""))
en_bot = TelegramBot(os.environ.get("EN_BOT_TOKEN", ""))

BOTS = {"ga": ga_bot, "en": en_bot}
