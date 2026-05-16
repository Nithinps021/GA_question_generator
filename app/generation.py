import json

from google import genai
from google.genai import types

from app.types import DailyQuizPayload


def fetch_ai_quiz() -> dict:
    """Calls Gemini with Google Search grounding and extracts the verified structured schema."""
    # The client automatically picks up GEMINI_API_KEY from the environment
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
        "4. Strictly verify information across multiple search fragments to avoid hallucinations. Do not invent fake financial announcements."
    )

    config = types.GenerateContentConfig(
        system_instruction=golden_prompt,
        tools=[types.Tool(google_search=types.GoogleSearch())],  # Turn on Google Search Grounding
        temperature=0.2,  # Low temperature enforces high factual accuracy
        response_mime_type="application/json",
        response_schema=DailyQuizPayload,
    )

    user_intent = "Fetch the latest relevant current affairs and compile today's comprehensive 20-question banking exam GA quiz."

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_intent,
        config=config
    )

    return json.loads(response.text)