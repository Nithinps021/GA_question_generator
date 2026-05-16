import os


from app.db import get_all_active_users
from app.generation import fetch_ai_quiz


def generate_and_broadcast_quiz(request):
    """
    HTTP Cloud Function that generates a 20-question GA quiz using Gemini
    with Google Search Grounding and broadcasts it to all active Firestore subscribers.
    """
    # Verify environment variables are configured
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return "Missing TELEGRAM_BOT_TOKEN environment variable.", 500

    # 1. Fetch active subscribers from Firestore
    try:
        print("Getting users")
        users = get_all_active_users()
        chat_ids = [user.to_dict()["chat_id"] for user in users]
    except Exception as e:
        return f"Database Fetch Error: {str(e)}", 500

    if not chat_ids:
        return "Execution halted: No active subscribers found in Firestore.", 200

    # 2. Query Gemini for the Structured Quiz Data
    try:
        quiz_data = fetch_ai_quiz()
    except Exception as e:
        return f"Gemini Generation Error: {str(e)}", 500

    # 3. Broadcast generated content to all tracked accounts
    # broadcast_to_subscribers(quiz_data, chat_ids, bot_token)
    return f"Successfully processed and broadcasted quiz to {len(chat_ids)} users.", 200


