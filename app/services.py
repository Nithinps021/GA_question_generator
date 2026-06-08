
from fastapi import HTTPException

from google.cloud.firestore_v1.base_query import FieldFilter

from app.db import db
from app.en_generator import generate_english_questions
from app.qa_generation import generate_questions
from app.types import DailyQuiz, DailyEnglishQuiz, ReferenceSection
from app.utils import get_logger

logger = get_logger(__name__)

def get_subscribed_users(collection: str = "ga_subscribers") -> list[str]:
    try:
        docs = db.collection(collection).where(filter=FieldFilter("active", "==", True)).stream()
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

def get_english_questions() -> DailyEnglishQuiz:
    try:
        quiz_data = generate_english_questions()
        return DailyEnglishQuiz.model_validate(quiz_data)
    except Exception as e:
        logger.exception("Gemini quiz generation failed")
        raise HTTPException(status_code=500, detail=f"Gemini Generation Error: {str(e)}")

def save_quiz(quiz: DailyQuiz | DailyEnglishQuiz, path: str = "questions") -> DailyQuiz:
    try:
        doc_ref = db.collection(path).document(quiz.date)
        doc_ref.set({"quiz": [q.model_dump() for q in quiz.quiz]})
        logger.info("Saved quiz to Firestore for date: %s", quiz.date)
    except Exception as e:
        logger.exception("Failed to save quiz to Firestore")
        raise HTTPException(status_code=500, detail=f"Database Write Error: {str(e)}")


async def broadcast_quiz(question: DailyQuiz | DailyEnglishQuiz, users: list[str], quiz_type: str = "ga"):
    from telegram.api import BOTS
    from telegram.broadcaster import broadcast_first_question
    await broadcast_first_question(BOTS[quiz_type], question, users, quiz_type=quiz_type)


def get_todays_questions(collection: str = "questions", output_file: str = "todays_questions.json") -> str:
    import json
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    try:
        doc = db.collection(collection).document(today).get()
        questions = doc.to_dict().get("quiz", []) if doc.exists else []
        with open(output_file, "w") as f:
            json.dump({"date": today, "quiz": questions}, f, indent=2)
        logger.info("Wrote %d questions to %s", len(questions), output_file)
        return output_file
    except Exception as e:
        logger.exception("Failed to fetch today's questions from Firestore")
        raise HTTPException(status_code=500, detail=f"Database Fetch Error: {str(e)}")


def inject_reference_questions(data: ReferenceSection):
    try:
        doc_ref = db.collection(data.collection).document(data.section_name)
        doc_ref.set({"questions": [q.model_dump() for q in data.questions]})
        logger.info("Injected data into firestore collection %s", data.collection)
    except Exception as e:
        logger.exception("Failed to save quiz to Firestore")
        raise HTTPException(status_code=500, detail=f"Database Write Error: {str(e)}")