# Bank Exam GA Bot

A daily General Awareness quiz generator for Indian banking exam preparation (SBI PO, IBPS PO, RBI Grade B). Uses Google Gemini with Search Grounding to produce 20 MCQs from the latest 24-48 hours of current affairs, then broadcasts them to subscribers via Telegram.

## How It Works

1. **Generate** -- Gemini (with live Google Search) creates 20 questions covering banking/financial affairs, national/international news, and static banking concepts.
2. **Store** -- Quiz data is saved to Google Cloud Firestore, keyed by date.
3. **Broadcast** -- Questions are sent to all active Telegram subscribers (WIP).

## Project Structure

```
app/
  main.py          # FastAPI application entry point
  routes.py        # API endpoints
  services.py      # Business logic (fetch subscribers, generate & save quiz)
  generation.py    # Gemini prompt and response parsing
  db.py            # Firestore client initialization
  types.py         # Pydantic models (DailyQuiz, QuestionItem)
  utils.py         # Logging setup
telegram/
  broadcaster.py   # Telegram message broadcasting (WIP)
  webhook.py       # Telegram webhook handler (WIP)
```

## Prerequisites

- Python 3.13+
- A Google Cloud project with Firestore enabled
- Gemini API access (via `google-genai`)
- A Telegram bot token (for broadcasting)

## Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
GOOGLE_APPLICATION_CREDENTIALS=service_account.json
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
```

## Running

```bash
# Load env vars and start the dev server
source .env && uvicorn app.main:app --reload --port 8080
```

Or use the helper script:

```bash
./dev-run.sh
```

## API

| Method | Endpoint           | Description                                      |
|--------|--------------------|--------------------------------------------------|
| GET    | `/broadcast-quiz`  | Generate today's quiz, save it, and broadcast it  |
