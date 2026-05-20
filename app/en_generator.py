import json
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
        You are an elite English Language faculty and exam setter for India's toughest banking exams (SBI PO, IBPS PO, SBI Clerk).
        Your task is to generate exactly 20 highly standard, Medium to Hard difficulty English questions matching the latest previous year question patterns.
        CRITICAL EXAM PATTERN INSTRUCTIONS:
        1. Context: Base your sentences on banking, economy, geopolitics, environment, or 'The Hindu' editorial-style themes. No casual or trivial sentences.
        2. Options: Every question MUST have exactly 5 options (A, B, C, D, E). 
        3. Topics to cover (Ensure a balanced, unpredictable mix across these areas):
           - Error Spotting: Test advanced grammar (Subject-Verb Inversion, Parallelism, Conditional Clauses, Phrasal prepositions).
           - Phrase Replacement / Sentence Improvement: Bold a grammatical phrase; options must offer structurally close alternatives. Option E is 'No correction required'.
           - Word Swap: Bold 3 to 4 words in a sentence. Options must suggest which pair to swap for contextual coherence.
           - Fillers (Double or Single): Require advanced vocabulary where blanks are contextually linked.
           - Idioms & Phrases / Spelling Context: Test contextual application of banking/standard idioms.
        4. Explanations: Provide a crystal-clear, deep-dive grammatical or vocabulary explanation so a student learns the exact rule they missed.
        5. Randomization & Freshness: You MUST highly randomize the vocabulary, sentence contexts, and grammatical rules tested. Never repeat exact contexts, 
        sentence structures, or specific idioms across different generations. Treat this as a completely fresh, unpredictable mock test so the user does not 
        experience repetitive patterns.
        "RESPONSE FORMAT:\n"
        "Return ONLY valid JSON (no markdown, no code fences) matching this exact schema:\n"
        '{"date": "YYYY-MM-DD", "quiz": [{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A", "explanation": "..."}]}\n'
        "The quiz array must contain exactly 20 items."
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
        model='gemini-2.5-flash',
        contents=user_request,
        config=config
    )

    logger.info("Received response from Gemini, parsing quiz data")
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # remove opening ```json
        text = text.rsplit("```", 1)[0]  # remove closing ```
    return json.loads(text)