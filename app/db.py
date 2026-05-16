import os

from google.cloud import firestore

from app.utils import get_logger

logger = get_logger(__name__)

logger.info("Initializing Firestore client...")

os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
db = firestore.Client()

logger.info("Firestore client initialized. Project: %s", db.project)

