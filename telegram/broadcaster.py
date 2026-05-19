import asyncio

from app.types import DailyQuiz
from app.utils import get_logger
from telegram.api import send_message
from telegram.formatting import build_options_keyboard, format_question

logger = get_logger(__name__)

RATE_LIMIT = asyncio.Semaphore(25)


async def broadcast_first_question(quiz: DailyQuiz, chat_ids: list[str]):
    total = len(quiz.quiz)
    if total == 0:
        logger.warning("Quiz has no questions, skipping broadcast")
        return

    first_question = quiz.quiz[0]
    text = format_question(first_question, index=0, total=total)
    keyboard = build_options_keyboard(
        quiz_date=quiz.date,
        question_index=0,
        correct_answer=first_question.answer,
        score=0,
    )

    async def send_to_user(chat_id: str):
        async with RATE_LIMIT:
            try:
                await send_message(chat_id, text, reply_markup=keyboard)
                logger.info("Sent first question to chat %s", chat_id)
            except Exception:
                logger.exception("Failed to send question to chat %s", chat_id)

    await asyncio.gather(*(send_to_user(cid) for cid in chat_ids))
    logger.info("Broadcast complete: sent to %d users", len(chat_ids))
