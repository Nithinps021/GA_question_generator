from fastapi import APIRouter, Request

from app.db import db
from app.types import EnglishQuestionItem, QuestionItem
from app.utils import get_logger
from telegram.api import TelegramBot, ga_bot, en_bot
from telegram.formatting import (
    build_options_keyboard,
    format_correct_response,
    format_question,
    format_quiz_complete,
    format_wrong_response,
)

QUIZ_CONFIG = {
    "ga": {"collection": "questions", "model": QuestionItem, "num_options": 4, "subscribers": "ga_subscribers"},
    "en": {"collection": "en_questions", "model": EnglishQuestionItem, "num_options": 5, "subscribers": "en_subscribers"},
}

logger = get_logger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _parse_callback_data(data: str) -> tuple[str, str, int, str, str, int] | None:
    """Parse callback_data: quiz_type:date:index:correct:selected:score"""
    parts = data.split(":")
    if len(parts) != 6:
        return None
    try:
        quiz_type = parts[0]
        quiz_date = parts[1]
        question_index = int(parts[2])
        correct_answer = parts[3]
        selected_option = parts[4]
        score = int(parts[5])
        if quiz_type not in QUIZ_CONFIG:
            return None
        return quiz_type, quiz_date, question_index, correct_answer, selected_option, score
    except (ValueError, IndexError):
        return None


def _get_quiz_questions(quiz_type: str, quiz_date: str) -> list[QuestionItem | EnglishQuestionItem] | None:
    """Fetch quiz questions from Firestore by type and date."""
    config = QUIZ_CONFIG[quiz_type]
    doc = db.collection(config["collection"]).document(quiz_date).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if not data or "quiz" not in data:
        return None
    return [config["model"](**q) for q in data["quiz"]]


async def _handle_callback_query(bot: TelegramBot, callback_query: dict):
    cb_id = callback_query["id"]
    data = callback_query.get("data", "")
    chat_id = str(callback_query["message"]["chat"]["id"])
    message_id = callback_query["message"]["message_id"]

    parsed = _parse_callback_data(data)
    if not parsed:
        await bot.answer_callback_query(cb_id, "Invalid action")
        return

    quiz_type, quiz_date, question_index, correct_answer, selected_option, score = parsed
    config = QUIZ_CONFIG[quiz_type]

    await bot.answer_callback_query(cb_id)

    questions = _get_quiz_questions(quiz_type, quiz_date)
    if not questions:
        await bot.edit_message_text(chat_id, message_id, "Quiz data not found.")
        return

    total = len(questions)
    if question_index >= total:
        return

    question = questions[question_index]
    is_correct = correct_answer == selected_option
    new_score = score + 1 if is_correct else score

    if is_correct:
        response_text = format_correct_response(question, question_index, total, selected_option)
    else:
        response_text = format_wrong_response(question, question_index, total, selected_option)

    await bot.edit_message_text(chat_id, message_id, response_text)

    next_index = question_index + 1
    if next_index < total:
        next_question = questions[next_index]
        next_text = format_question(next_question, next_index, total)
        next_keyboard = build_options_keyboard(
            quiz_type=quiz_type,
            quiz_date=quiz_date,
            question_index=next_index,
            correct_answer=next_question.answer,
            score=new_score,
            num_options=config["num_options"],
        )
        await bot.send_message(chat_id, next_text, reply_markup=next_keyboard)
    else:
        await bot.send_message(chat_id, format_quiz_complete(new_score, total))


async def _handle_message(bot: TelegramBot, quiz_type: str, message: dict):
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()
    collection = QUIZ_CONFIG[quiz_type]["subscribers"]

    if text == "/start":
        db.collection(collection).document(chat_id).set(
            {"chat_id": chat_id, "active": True}, merge=True
        )
        if quiz_type == "ga":
            welcome = (
                "<b>Welcome to Bank Exam GA Bot!</b>\n\n"
                "You'll receive daily current affairs quiz questions for SBI PO, IBPS PO, and RBI Grade B preparation.\n\n"
                "Use /stop to unsubscribe."
            )
        else:
            welcome = (
                "<b>Welcome to Bank Exam English Bot!</b>\n\n"
                "You'll receive daily English language quiz questions for SBI PO, IBPS PO, and SBI Clerk preparation.\n\n"
                "Use /stop to unsubscribe."
            )
        await bot.send_message(chat_id, welcome)
    elif text == "/stop":
        db.collection(collection).document(chat_id).update({"active": False})
        await bot.send_message(
            chat_id,
            "You've been unsubscribed. Use /start to subscribe again.",
        )


async def _process_update(bot: TelegramBot, quiz_type: str, update: dict):
    if "callback_query" in update:
        await _handle_callback_query(bot, update["callback_query"])
    elif "message" in update:
        await _handle_message(bot, quiz_type, update["message"])


@router.post("/ga/webhook")
async def ga_webhook(request: Request):
    update = await request.json()
    await _process_update(ga_bot, "ga", update)
    return {"ok": True}


@router.post("/en/webhook")
async def en_webhook(request: Request):
    update = await request.json()
    await _process_update(en_bot, "en", update)
    return {"ok": True}
