import asyncio

from fastapi import APIRouter

from app.services import get_subscribed_users, get_questions, broadcast_quiz, save_quiz
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/broadcast-quiz")
async def generate_and_broadcast_quiz():
    chat_ids = get_subscribed_users()
    if not chat_ids:
        logger.warning("No active subscribers found, halting execution")
        return {"message": "Execution halted: No active subscribers found in Firestore."}

    questions = get_questions()

    await asyncio.gather(
        asyncio.to_thread(save_quiz, questions),
        asyncio.to_thread(broadcast_quiz, question=questions, users=chat_ids)
    )
    return {"quiz_data": questions}
    return {"message": f"Successfully processed and broadcasted quiz to {len(chat_ids)} users."}

