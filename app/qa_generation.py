import json
import os

from google import genai
from google.genai import types

from app.utils import get_logger

logger = get_logger(__name__)


def generate_questions() -> dict:
    """
    Generates a 20-question GA quiz using Gemini
    with Google Search Grounding and broadcasts it to all active Firestore subscribers.
    """
    client = genai.Client()

    golden_prompt = (
        "You are an elite exam curator specializing in General Awareness (GA) and Banking/Financial Awareness "
        "for competitive Indian banking exams (such as SBI PO, IBPS PO, and RBI Grade B).\n\n"
        "Your objective is to generate exactly 20 distinct, high-quality multiple-choice questions based strictly "
        "on real world factual developments from the last 24–48 hours.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Proactively use the Google Search tool to fetch live financial news, latest RBI notifications, monetary policy adjustments, "
        "corporate banking shifts, banking tech innovations, national schemes, and critical regulatory changes.\n"
        "2. Ensure highly specific data metrics (e.g., specific pool sizes, names of appointed officials, exact policy names, base years). "
        "Avoid generic or outdated current affairs.\n"
        "3. Balance the 20 questions across: 60% Current Financial/Banking/Economic Affairs, 20% Latest National/International General Current Affairs, "
        "and 20% Static Banking Concepts (grounded or triggered by recent news trends).\n"
        "4. Strictly verify information across multiple search fragments to avoid hallucinations. Do not invent fake financial announcements.\n\n"
        "RESPONSE FORMAT:\n"
        "Return ONLY valid JSON (no markdown, no code fences) matching this exact schema:\n"
        '{"date": "YYYY-MM-DD", "quiz": [{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A", "explanation": "..."}]}\n'
        "The quiz array must contain exactly 20 items."
    )

    config = types.GenerateContentConfig(
        system_instruction=golden_prompt,
        tools=[types.Tool(google_search=types.GoogleSearch())],  # Turn on Google Search Grounding
        temperature=0.2,  # Low temperature enforces high factual accuracy
    )

    user_intent = "Fetch the latest relevant current affairs and compile today's comprehensive 20-question banking exam GA quiz."

    logger.info("Sending request to Gemini (model: gemini-2.5-flash)")
    response = client.models.generate_content(
        model=os.environ.get("GEMINI_MODEL"),
        contents=user_intent,
        config=config
    )

    logger.info("Received response from Gemini, parsing quiz data")
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]  # remove opening ```json
        text = text.rsplit("```", 1)[0]  # remove closing ```
    return json.loads(text)