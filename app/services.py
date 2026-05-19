from fastapi import HTTPException

from google.cloud.firestore_v1.base_query import FieldFilter

from app.db import db
from app.generation import generate_questions
from app.types import DailyQuiz
from app.utils import get_logger

logger = get_logger(__name__)

def get_subscribed_users()-> list[str]:
    try:
        docs = db.collection("subscribers").where(filter=FieldFilter("active", "==", True)).stream()
        return [doc.to_dict()["chat_id"] for doc in docs]
    except Exception as e:
        logger.exception("Failed to fetch users from Firestore")
        raise HTTPException(status_code=500, detail=f"Database Fetch Error: {str(e)}")

def get_questions() -> DailyQuiz:
    try:
        quiz_data = generate_questions()
        return DailyQuiz.model_validate(quiz_data)
    except Exception as e:
        logger.exception("Gemini quiz generation failed")
        raise HTTPException(status_code=500, detail=f"Gemini Generation Error: {str(e)}")

def save_quiz(quiz: DailyQuiz):
    try:
        doc_ref = db.collection("questions").document(quiz.date)
        doc_ref.set({"quiz": [q.model_dump() for q in quiz.quiz]})
        logger.info("Saved quiz to Firestore for date: %s", quiz.date)
    except Exception as e:
        logger.exception("Failed to save quiz to Firestore")
        raise HTTPException(status_code=500, detail=f"Database Write Error: {str(e)}")


async def broadcast_quiz(question: DailyQuiz, users: list[str]):
    from telegram.broadcaster import broadcast_first_question
    await broadcast_first_question(question, users)

