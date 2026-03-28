from google.cloud import firestore

_db: firestore.AsyncClient | None = None


def _get_db() -> firestore.AsyncClient:
    """Lazy Firestore client — created on first use, not at import time."""
    global _db
    if _db is None:
        _db = firestore.AsyncClient()
    return _db


async def get_memory(user_id: str, domain: str) -> dict:
    """Read memory for user+domain. Returns {} if document does not exist."""
    doc = (
        _get_db()
        .collection("agent_memory")
        .document(user_id)
        .collection(domain)
        .document("data")
    )
    snap = await doc.get()
    return snap.to_dict() or {}


async def update_memory(user_id: str, domain: str, updates: dict) -> None:
    """Merge updates into memory document for user+domain."""
    doc = (
        _get_db()
        .collection("agent_memory")
        .document(user_id)
        .collection(domain)
        .document("data")
    )
    await doc.set(updates, merge=True)
