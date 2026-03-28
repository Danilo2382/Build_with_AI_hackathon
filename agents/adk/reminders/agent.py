import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import SMART_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import create_reminder, get_checkups, get_contacts, get_medications, write_reminders

_SYSTEM_PROMPT = """You generate daily reminders for elderly users based on their medications, contacts, and checkups.

Output ONLY a valid JSON array of reminder objects. No explanation, no markdown, just the JSON array.

Each reminder must have these fields:
- type: "medication" | "exercise" | "people" | "checkup"
- icon: appropriate emoji
- label: short, friendly label (max 40 chars)
- time: "HH:MM" or null
- status: "pending" | "overdue" | "upcoming"
- days_since_contact: integer or null (only for people type)
- linked_id: the id of the source document or null

Rules:
- Create one reminder per medication schedule time
- Create people reminders for contacts with days_since > 7, mark overdue if > 14
- Create checkup reminders for upcoming appointments, always "upcoming" status
- Always include one exercise reminder at a sensible morning time"""

root_agent = LlmAgent(
    name="reminders",
    model=SMART_MODEL,
    description="Generates daily reminders from the user's medications, contacts, and checkups.",
    instruction=_SYSTEM_PROMPT,
)

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=SMART_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


async def run(user_id: str) -> dict:
    meds = await get_medications(user_id)
    contacts = await get_contacts(user_id)
    checkups = await get_checkups(user_id)

    prompt = f"""Generate reminders for this user.

Medications:
{json.dumps(meds, indent=2)}

Contacts:
{json.dumps(contacts, indent=2)}

Upcoming checkups:
{json.dumps(checkups, indent=2)}

Output only the JSON array of reminders."""

    response = await _get_model().generate_content_async(prompt)

    raw = response.text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    reminders = json.loads(raw)
    await write_reminders(user_id, reminders)

    return {"generated": len(reminders), "reminders": reminders}


_VOICE_PROMPT = """Extract a single reminder from a voice message. Today is {today}.

Output ONLY a valid JSON object with these fields:
- type: "medication" | "exercise" | "people" | "checkup" | "general"
- icon: appropriate emoji
- label: short, friendly label (max 40 chars)
- time: "HH:MM" or null
- status: "pending"
- days_since_contact: null

Examples:
"remind me to take my vitamin at noon" → {{"type": "medication", "icon": "💊", "label": "Take vitamin", "time": "12:00", "status": "pending", "days_since_contact": null}}
"remind me to call my son tomorrow evening" → {{"type": "people", "icon": "📞", "label": "Call son", "time": "19:00", "status": "pending", "days_since_contact": null}}
"remind me to do my stretches" → {{"type": "exercise", "icon": "🧘", "label": "Do stretches", "time": null, "status": "pending", "days_since_contact": null}}"""


async def run_voice(user_id: str, message: str) -> dict:
    from datetime import date
    prompt = _VOICE_PROMPT.format(today=date.today().isoformat()) + f'\n\nVoice message: "{message}"'

    response = await _get_model().generate_content_async(prompt)

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    reminder = json.loads(raw)
    await create_reminder(user_id, reminder)

    return {"created": True, "reminder": reminder}
