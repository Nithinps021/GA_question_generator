import json
import os
import uuid

from google import genai
from google.genai import types

from app.types import DailyEnglishQuiz
from app.utils import get_logger

logger = get_logger(__name__)


def generate_english_questions() -> dict:
    client = genai.Client()

    golden_english_prompt = (
        """
       You are an elite English Language faculty and exam setter for India's toughest banking exams (SBI PO, IBPS PO, RBI Grade B). Your task is to generate exactly 20 highly standard, Medium to Hard difficulty English questions matching the latest exam patterns.
       CRITICAL EXAM PATTERN & VARIETY INSTRUCTIONS:
       1. Diverse Contexts (The Hindu/The Economist Style): Base your sentences on diverse, serious themes including economics, global geopolitics, climate science, public policy, advanced technology, history, and social issues. Avoid casual or trivial sentences. Do not restrict the context solely to banking; mirror the wide-ranging, dense prose of actual exam papers.
       2. Strict Pattern Rotation (Day-to-Day Variety): To ensure the user faces a completely unpredictable mock test each time, you must deliberately rotate and mix the question formats. If a previous batch leaned heavily on standard Error Spotting, this batch must emphasize different structures (e.g., Sentence Divider Errors, Cloze-style fillers, or Column Matching). Do not let the quiz feel like a template.
       3. Complete Freshness (No Batch Duplication): Every single question, vocabulary word, idiom, and grammatical trap must be created from scratch. Avoid repeating sentence structures, specific error types (like the exact same subject-verb inversion rule), or core vocabulary words used in previous batches.
       4. Options: Every question MUST have exactly 5 options (A, B, C, D, E).
       5. Comprehensive Topic Mix (Select a dynamic mix for this batch):
           - Advanced Error Spotting: (e.g., split sentences, parallel structures, subjunctive mood, advanced prepositions).
           - Phrase Replacement / Sentence Improvement: Bold a complex grammatical phrase; Option E must be 'No correction required'.
           - Contextual Word Swap: Bold 3 to 4 words that need rearrangement for coherence.
           - Double/Triple Fillers: Advanced vocabulary where blanks rely heavily on contextual tone and secondary meanings of words.
           - Idioms & Phrasal Verbs: Test the precise application of standard/business idioms in context.

        6. Explanations: Provide a crystal-clear, deep-dive grammatical or vocabulary explanation so a student learns the exact rule or nuance they missed.

        RESPONSE FORMAT:
        Return ONLY valid JSON (no markdown, no code fences) matching this exact schema:
        {"date": "YYYY-MM-DD", "quiz": [{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."], "answer": "A", "explanation": "..."}]}
        
        The quiz array must contain exactly 20 items.
        """
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
    user_request = f"Generate a fresh, highly randomized set of 20 medium-to-hard banking English questions. Execution ID: {run_id}"

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