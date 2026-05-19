import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.utils import setup_logging
from app.routes import router
from telegram.webhook import router as telegram_router
from telegram.api import close_client
from telegram.polling import start_polling


@asynccontextmanager
async def lifespan(_app: FastAPI):
    polling_task = asyncio.create_task(start_polling())
    yield
    polling_task.cancel()
    await close_client()


setup_logging()

app = FastAPI(title="Bank Exam GA Bot Backend", lifespan=lifespan)

app.include_router(router)
app.include_router(telegram_router)
