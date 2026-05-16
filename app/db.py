from google.cloud import firestore

from app.utils import get_logger

logger = get_logger(__name__)

logger.info("Initializing Firestore client...")
db = firestore.Client()
logger.info("Firestore client initialized. Project: %s", db.project)

