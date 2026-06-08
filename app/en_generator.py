import json
import os
import random
import uuid

from fastapi import HTTPException
from google import genai
from google.genai import types

from app.blueprint import TOTAL_QUESTIONS, build_daily_blueprint
from app.db import db
from app.types import DailyEnglishQuiz
from app.utils import get_logger

logger = get_logger(__name__)

VALID_ANSWERS = {"A", "B", "C", "D", "E"}


def build_prompt(file_name: str, reference_questions: list[dict], blueprint: str) -> str:
    with open(f"prompt/{file_name}") as f:
        prompt_template = f.read()

    return prompt_template.replace(
        "[INSERT_YOUR_JSON_DATA_HERE]",
        json.dumps(reference_questions, indent=2),
    ).replace(
        "[INSERT_DAILY_BLUEPRINT_HERE]",
        blueprint,
    )


def validate_quiz(quiz: dict) -> list[str]:
    """Return a list of constraint violations; empty list means the quiz passed.

    These are the failures the prompt alone can't reliably prevent: wrong total
    count, invalid/missing answer letters, and a skewed answer-letter spread.
    """
    errors: list[str] = []
    questions = quiz.get("quiz", []) if isinstance(quiz, dict) else []

    if len(questions) != TOTAL_QUESTIONS:
        errors.append(
            f"Expected exactly {TOTAL_QUESTIONS} questions, got {len(questions)}."
        )

    histogram = {letter: 0 for letter in VALID_ANSWERS}
    for idx, q in enumerate(questions, 1):
        answer = str(q.get("answer", "")).strip().upper()
        if answer not in VALID_ANSWERS:
            errors.append(
                f"Question {idx}: answer '{q.get('answer')}' is not one of A-E "
                f"(it must be the OPTION LETTER, e.g. 'C', never a sentence label)."
            )
            continue
        histogram[answer] += 1

    # Only judge spread when the count is right, otherwise the numbers are noise.
    if len(questions) == TOTAL_QUESTIONS:
        for letter in sorted(VALID_ANSWERS):
            if histogram[letter] > 9:
                errors.append(
                    f"Answer '{letter}' is used {histogram[letter]} times "
                    f"(max 9). Spread answers more evenly across A-E."
                )
            if histogram[letter] < 2:
                errors.append(
                    f"Answer '{letter}' is used only {histogram[letter]} times "
                    f"(min 2). Spread answers more evenly across A-E."
                )

    return errors

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


def _parse_response_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # remove opening ```json
        text = text.rsplit("```", 1)[0]  # remove closing ```
    return json.loads(text)


def generate_english_questions(max_attempts: int = 3) -> dict:
    client = genai.Client(vertexai=True, api_key=os.environ.get("GEMINI_API_KEY"))

    # A fresh randomized blueprint per run is what actually varies the question
    # *patterns* day to day — temperature only varies wording. The blueprint also
    # fixes the block counts in code so they always sum to exactly 30.
    blueprint = build_daily_blueprint()
    logger.info("Today's quiz blueprint:\n%s", blueprint)

    golden_english_prompt = build_prompt(
        file_name="prelims_question_generator.md",
        reference_questions=get_random_questions_from_collection(collection="prelims_questions"),
        blueprint=blueprint,
    )

    config = types.GenerateContentConfig(
        system_instruction=golden_english_prompt,
        # 0.5 keeps wording fresh while improving format/constraint adherence;
        # day-to-day variety comes from the randomized blueprint, not temperature.
        temperature=0.5,
        response_mime_type="application/json",
        response_schema=DailyEnglishQuiz,
    )

    # Injecting a random UUID into the user prompt acts as a "salt".
    # It mathematically forces the LLM to see this as a brand-new request every single day.
    run_id = str(uuid.uuid4())
    base_request = (
        f"Generate the {TOTAL_QUESTIONS}-question paper strictly following TODAY'S "
        f"BLUEPRINT and the instructions. Execution ID: {run_id}"
    )

    quiz: dict = {}
    errors: list[str] = []
    for attempt in range(1, max_attempts + 1):
        user_request = base_request
        if errors:
            user_request += (
                "\n\nYour previous attempt was REJECTED for these reasons. Fix every "
                "one of them and regenerate the full paper:\n- " + "\n- ".join(errors)
            )

        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL"),
            contents=user_request,
            config=config,
        )
        logger.info("Received response from Gemini (attempt %d), parsing", attempt)
        quiz = _parse_response_text(response.text)

        errors = validate_quiz(quiz)
        if not errors:
            return quiz
        logger.warning(
            "Quiz failed validation on attempt %d/%d: %s",
            attempt, max_attempts, "; ".join(errors),
        )

    logger.error(
        "Quiz still invalid after %d attempts; returning best effort. Issues: %s",
        max_attempts, "; ".join(errors),
    )
    return quiz