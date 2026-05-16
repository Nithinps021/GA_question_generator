import hashlib

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.db import db

api_key_header = APIKeyHeader(name="X-API-Key")


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def store_api_key(key: str) -> str:
    """Hash the key and store it in Firestore. Returns the hash."""
    key_hash = hash_api_key(key)
    db.collection("api_keys").document(key_hash).set({"active": True})
    return key_hash


async def verify_api_key(key: str = Security(api_key_header)):
    key_hash = hash_api_key(key)
    doc = db.collection("api_keys").document(key_hash).get()
    if doc.exists and doc.to_dict().get("active"):  # type: ignore[union-attr]
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API key",
    )
