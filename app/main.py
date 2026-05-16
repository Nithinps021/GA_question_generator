from fastapi import FastAPI

from app.utils import setup_logging
from app.routes import router

setup_logging()

app = FastAPI(title="Bank Exam GA Bot Backend")

app.include_router(router)
