import os

from google.cloud import firestore

from app.utils import get_logger

logger = get_logger(__name__)

logger.info("Initializing Firestore client...")

# For local dev only — on Cloud Run, auth uses the attached service account automatically
if os.path.exists("service_account.json"):
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
db = firestore.Client(database="bank-exams-questions")

logger.info("Firestore client initialized. Project: %s", db.project)

