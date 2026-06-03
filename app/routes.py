import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.services import get_english_questions, get_questions, get_subscribed_users, broadcast_quiz, save_quiz, \
    inject_reference_questions
from app.types import ReferenceSection
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/")
async def welcome_message():
    return {"status":"hellow world"}

@router.get("/health-check")
async def health_check():
    return {"status":True}

@router.get("/broadcast-quiz", dependencies=[Depends(verify_api_key)])
async def generate_and_broadcast_quiz():
    chat_ids = get_subscribed_users("ga_subscribers")
    if not chat_ids:
        logger.warning("No active GA subscribers found")
        return {"message": "No active GA subscribers found."}

    questions = get_questions()

    await asyncio.gather(
        asyncio.to_thread(save_quiz, questions, "questions"),
        broadcast_quiz(question=questions, users=chat_ids, quiz_type="ga"),
    )
    return {"message": f"GA quiz broadcasted to {len(chat_ids)} users."}


@router.get("/broadcast-english-quiz", dependencies=[Depends(verify_api_key)])
async def generate_and_broadcast_english_quiz():
    chat_ids = get_subscribed_users("en_subscribers")
    if not chat_ids:
        logger.warning("No active English subscribers found")
        return {"message": "No active English subscribers found."}

    questions = get_english_questions()
    questions.date = datetime.now().strftime("%Y-%m-%d")

    await asyncio.gather(
        asyncio.to_thread(save_quiz, questions, "en_questions"),
        broadcast_quiz(question=questions, users=chat_ids, quiz_type="en"),
    )
    return {"message": f"English quiz broadcasted to {len(chat_ids)} users."}


@router.post("/inject-questions", dependencies=[Depends(verify_api_key)])
async def handle_inject_questions(data: ReferenceSection):
    inject_reference_questions(data)
    return {"message": f"Inject questions into {data.section_name} sections."}