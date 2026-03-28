"""
Seed script — populates Firestore with demo data for nikola.
Run from agents/ directory: python3.11 seed.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

import config  # noqa — ensures env vars are loaded
from google.cloud import firestore

USER_ID = "nikola"


async def seed():
    db = firestore.AsyncClient()

    # ── User profile ───────────────────────────────────────────
    await db.collection("users").document(USER_ID).set({
        "name": "Nikola Nikolic",
        "age": 72,
        "language": "sr",
        "voice_speed": "slow",
        "emergency_contact": "Ana",
        "created_at": "2026-03-28",
    })
    print("✓ users")

    # ── Medications ────────────────────────────────────────────
    meds = [
        {
            "id": "med_001",
            "userId": USER_ID,
            "name": "Aspirin",
            "dose": "100mg",
            "schedule": ["08:00", "20:00"],
            "with_food": True,
            "last_confirmed": None,
            "notes": "Blood thinner, do not skip",
        },
        {
            "id": "med_002",
            "userId": USER_ID,
            "name": "Metformin",
            "dose": "500mg",
            "schedule": ["07:00", "13:00", "19:00"],
            "with_food": True,
            "last_confirmed": None,
            "notes": "For diabetes, take with meals",
        },
        {
            "id": "med_003",
            "userId": USER_ID,
            "name": "Lisinopril",
            "dose": "10mg",
            "schedule": ["08:00"],
            "with_food": False,
            "last_confirmed": None,
            "notes": "Blood pressure, take in the morning",
        },
    ]
    for med in meds:
        med_id = med.pop("id")
        await db.collection("medications").document(med_id).set(med)
    print("✓ medications")

    # ── Contacts ───────────────────────────────────────────────
    contacts = [
        {
            "id": "con_001",
            "userId": USER_ID,
            "name": "Ana",
            "relationship": "daughter",
            "phone": "+381641234567",
            "last_contact": "2026-03-14",
            "days_since": 14,
            "notes": "Calls every Sunday, lives in Novi Sad",
            "emergency_contact": True,
            "telegram_chat_id": "",  # fill in after /start with the bot
        },
        {
            "id": "con_002",
            "userId": USER_ID,
            "name": "Marko",
            "relationship": "son",
            "phone": "+381691234567",
            "last_contact": "2026-03-20",
            "days_since": 8,
            "notes": "Busy with work, best to call evenings",
        },
        {
            "id": "con_003",
            "userId": USER_ID,
            "name": "Milica",
            "relationship": "friend",
            "phone": "+381621234567",
            "last_contact": "2026-02-28",
            "days_since": 28,
            "notes": "Old neighbour, loves to chat",
        },
    ]
    for contact in contacts:
        con_id = contact.pop("id")
        await db.collection("contacts").document(con_id).set(contact)
    print("✓ contacts")

    # ── Exercise ───────────────────────────────────────────────
    await db.collection("exercise").document(USER_ID).set({
        "userId": USER_ID,
        "last_session": "2026-03-27",
        "streak_days": 3,
        "preferred_time": "morning",
        "limitations": "bad knees, avoid jumping and high-impact exercises",
        "history": [
            {"date": "2026-03-27", "type": "stretching", "duration_min": 10},
            {"date": "2026-03-26", "type": "walking", "duration_min": 20},
            {"date": "2026-03-25", "type": "stretching", "duration_min": 15},
        ],
    })
    print("✓ exercise")

    # ── Checkups ───────────────────────────────────────────────
    checkups = [
        {
            "id": "chk_001",
            "userId": USER_ID,
            "doctor": "Dr. Petrović",
            "specialty": "cardiologist",
            "date": "2026-04-05",
            "time": "10:30",
            "location": "Dom zdravlja Zemun",
            "notes": "Bring ECG results from last visit",
            "status": "upcoming",
        },
        {
            "id": "chk_002",
            "userId": USER_ID,
            "doctor": "Dr. Nikolić",
            "specialty": "general practitioner",
            "date": "2026-04-15",
            "time": "09:00",
            "location": "Dom zdravlja Zemun",
            "notes": "Regular quarterly checkup",
            "status": "upcoming",
        },
    ]
    for checkup in checkups:
        chk_id = checkup.pop("id")
        await db.collection("checkups").document(chk_id).set(checkup)
    print("✓ checkups")

    # ── App config ─────────────────────────────────────────────
    await db.collection("app_config").document("telegram").set({
        "bot_token": "",  # fill in with BotFather token
    }, merge=True)
    print("✓ app_config/telegram")

    print("\nDone. Firestore seeded for nikola.")


asyncio.run(seed())
