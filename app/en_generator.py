import json
import os
import random
import uuid

from fastapi import HTTPException
from google import genai
from google.genai import types

from app.db import db
from app.types import DailyEnglishQuiz
from app.utils import get_logger

logger = get_logger(__name__)


def build_prompt(file_name:str, reference_questions: list[dict]) -> str:
    with open(f"prompt/{file_name}") as f:
        prompt_template = f.read()

    return prompt_template.replace(
        "[INSERT_YOUR_JSON_DATA_HERE]",
        json.dumps(reference_questions, indent=2)
    )

def get_random_questions_from_collection(collection: str) -> list[dict]:
    """Get one random question from each document in a collection.

    Each document is expected to have a 'questions' key containing an array.
    Returns a list of dicts with 'section' (doc ID) and the random question fields.
    """
    try:
        docs = db.collection(collection).stream()
        random_questions = []
        for doc in docs:
            data = doc.to_dict()
            questions = data.get("questions", [])
            if questions:
                question = random.choice(questions)
                question["section"] = doc.id
                random_questions.append(question)
        return random_questions
    except Exception as e:
        logger.exception("Failed to fetch random questions from collection %s", collection)
        raise HTTPException(status_code=500, detail=f"Database Fetch Error: {str(e)}")


def generate_english_questions() -> dict:
    client = genai.Client(vertexai=True, api_key=os.environ.get("GEMINI_API_KEY"))

    golden_english_prompt = build_prompt(
        file_name="prelims_question_generator.md",
        reference_questions=get_random_questions_from_collection(collection="prelims_questions"),
    )

    config = types.GenerateContentConfig(
        system_instruction=golden_english_prompt,
        # A temperature of 0.7 ensures the model takes creative liberties with vocabulary
        # and sentence structures, preventing the "repetitive daily quiz" feel.
        temperature=0.7,
        response_mime_type="application/json",
        response_schema=DailyEnglishQuiz,
    )

    # Injecting a random UUID into the user prompt acts as a "salt".
    # It mathematically forces the LLM to see this as a brand-new request every single day.
    run_id = str(uuid.uuid4())
    user_request = f"Generate the 30-question as per the blueprint and instructions. Execution ID: {run_id}"

    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL"),
        contents=user_request,
        config=config
    )

    logger.info("Received response from Gemini, parsing quiz data")
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # remove opening ```json
        text = text.rsplit("```", 1)[0]  # remove closing ```
    return json.loads(text)