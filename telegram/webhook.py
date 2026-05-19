from fastapi import APIRouter, Request

from app.db import db
from app.types import QuestionItem
from app.utils import get_logger
from telegram.api import answer_callback_query, edit_message_text, send_message
from telegram.formatting import (
    build_options_keyboard,
    format_correct_response,
    format_question,
    format_quiz_complete,
    format_wrong_response,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _parse_callback_data(data: str) -> tuple[str, int, str, str, int] | None:
    """Parse callback_data: date:index:correct:selected:score"""
    parts = data.split(":")
    if len(parts) != 5:
        return None
    try:
        quiz_date = parts[0]
        question_index = int(parts[1])
        correct_answer = parts[2]
        selected_option = parts[3]
        score = int(parts[4])
        return quiz_date, question_index, correct_answer, selected_option, score
    except (ValueError, IndexError):
        return None


def _get_quiz_questions(quiz_date: str) -> list[QuestionItem] | None:
    """Fetch quiz questions from Firestore by date."""
    doc = db.collection("questions").document(quiz_date).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if not data or "quiz" not in data:
        return None
    return [QuestionItem(**q) for q in data["quiz"]]


async def _handle_callback_query(callback_query: dict):
    cb_id = callback_query["id"]
    data = callback_query.get("data", "")
    chat_id = str(callback_query["message"]["chat"]["id"])
    message_id = callback_query["message"]["message_id"]

    parsed = _parse_callback_data(data)
    if not parsed:
        await answer_callback_query(cb_id, "Invalid action")
        return

    quiz_date, question_index, correct_answer, selected_option, score = parsed

    await answer_callback_query(cb_id)

    questions = _get_quiz_questions(quiz_date)
    if not questions:
        await edit_message_text(chat_id, message_id, "Quiz data not found.")
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

    await edit_message_text(chat_id, message_id, response_text)

    next_index = question_index + 1
    if next_index < total:
        next_question = questions[next_index]
        next_text = format_question(next_question, next_index, total)
        next_keyboard = build_options_keyboard(
            quiz_date=quiz_date,
            question_index=next_index,
            correct_answer=next_question.answer,
            score=new_score,
        )
        await send_message(chat_id, next_text, reply_markup=next_keyboard)
    else:
        await send_message(chat_id, format_quiz_complete(new_score, total))


async def _handle_message(message: dict):
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()

    if text == "/start":
        db.collection("subscribers").document(chat_id).set(
            {"chat_id": chat_id, "active": True}, merge=True
        )
        await send_message(
            chat_id,
            "<b>Welcome to Bank Exam GA Bot!</b>\n\n"
            "You'll receive daily current affairs quiz questions for SBI PO, IBPS PO, and RBI Grade B preparation.\n\n"
            "Use /stop to unsubscribe.",
        )
    elif text == "/stop":
        db.collection("subscribers").document(chat_id).update({"active": False})
        await send_message(
            chat_id,
            "You've been unsubscribed. Use /start to subscribe again.",
        )


@router.post("/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()

    if "callback_query" in update:
        await _handle_callback_query(update["callback_query"])
    elif "message" in update:
        await _handle_message(update["message"])

    return {"ok": True}
