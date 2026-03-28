from google.cloud import firestore

_db: firestore.AsyncClient | None = None


def _get_db() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient()
    return _db


# ── Profile ────────────────────────────────────────────────────────────────

async def get_profile(user_id: str) -> dict:
    snap = await _get_db().collection("users").document(user_id).get()
    return snap.to_dict() or {}


# ── Medications ────────────────────────────────────────────────────────────

async def get_medications(user_id: str) -> list[dict]:
    docs = await _get_db().collection("medications").where("userId", "==", user_id).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


async def update_medication(user_id: str, med_id: str, updates: dict) -> None:
    await _get_db().collection("medications").document(med_id).set(updates, merge=True)


# ── Contacts ───────────────────────────────────────────────────────────────

async def get_contacts(user_id: str) -> list[dict]:
    docs = await _get_db().collection("contacts").where("userId", "==", user_id).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


async def get_emergency_contacts(user_id: str) -> list[dict]:
    docs = await _get_db().collection("contacts").where("userId", "==", user_id).where("emergency_contact", "==", True).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


async def update_contact(user_id: str, contact_id: str, updates: dict) -> None:
    await _get_db().collection("contacts").document(contact_id).set(updates, merge=True)


# ── Exercise ───────────────────────────────────────────────────────────────

async def get_exercise(user_id: str) -> dict:
    snap = await _get_db().collection("exercise").document(user_id).get()
    return snap.to_dict() or {}


async def update_exercise(user_id: str, updates: dict) -> None:
    await _get_db().collection("exercise").document(user_id).set(updates, merge=True)


# ── Checkups ───────────────────────────────────────────────────────────────

async def get_checkups(user_id: str) -> list[dict]:
    docs = await _get_db().collection("checkups").where("userId", "==", user_id).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


# ── Reminders ──────────────────────────────────────────────────────────────

async def write_reminders(user_id: str, reminders: list[dict]) -> None:
    """Replace all reminders for a user with AI-generated ones."""
    db = _get_db()
    col = db.collection("reminders")

    # Delete only previously auto-generated reminders
    existing = await col.where("userId", "==", user_id).where("auto_generated", "==", True).get()
    for doc in existing:
        await doc.reference.delete()

    # Write new reminders, flagged as auto-generated
    for reminder in reminders:
        await col.document().set({"userId": user_id, "auto_generated": True, **reminder})


async def create_reminder(user_id: str, reminder: dict) -> None:
    """Write a single manually-created reminder — never deleted by auto-generation."""
    await _get_db().collection("reminders").document().set({
        "userId": user_id,
        "auto_generated": False,
        **reminder,
    })


async def get_reminders(user_id: str) -> list[dict]:
    """Return all reminders for the user."""
    docs = await _get_db().collection("reminders").where("userId", "==", user_id).get()
    return [{"id": d.id, **d.to_dict()} for d in docs]


# ── News Preferences ────────────────────────────────────────────────────────

async def get_news_preferences(user_id: str) -> dict:
    """Return the user's news topic preferences."""
    snap = await _get_db().collection("news_preferences").document(user_id).get()
    return snap.to_dict() or {"liked_topics": [], "disliked_topics": []}


async def update_news_preferences(user_id: str, updates: dict) -> None:
    """Update the user's news topic preferences."""
    await _get_db().collection("news_preferences").document(user_id).set(updates, merge=True)
