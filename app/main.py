import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.utils import setup_logging
from app.routes import router
from telegram.webhook import router as telegram_router
from telegram.api import ga_bot, en_bot


@asynccontextmanager
async def lifespan(_app: FastAPI):
    webhook_url = os.environ["WEBHOOK_URL"]
    await ga_bot.set_webhook(f"{webhook_url}/telegram/ga/webhook")
    await en_bot.set_webhook(f"{webhook_url}/telegram/en/webhook")
    yield
    await ga_bot.close()
    await en_bot.close()


setup_logging()

app = FastAPI(title="Bank Exam GA Bot Backend", lifespan=lifespan)

app.include_router(router)
app.include_router(telegram_router)
