import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL
from google.adk.agents import LlmAgent

from memory import get_medications, update_medication, update_reminder, get_reminders

_SYSTEM_PROMPT = """You are a warm medication assistant. 
1. Use get_my_medications to answer questions.
2. If the user says they took a pill (e.g. 'I took my Aspirin'):
   - First, call get_my_reminders to find the reminder ID matching that medication.
   - Also find the med_id from get_my_medications.
   - Call confirm_medication_taken(reminder_id, med_id).
   - Acknowledge warmly.
3. If they ask if they took it, use the data to tell them."""


async def get_my_medications() -> list[dict]:
    """Get the user's medication list including names, doses, and schedules."""
    return await get_medications("nikola")


async def get_my_reminders() -> list[dict]:
    """Get today's reminders to find which one to mark as completed."""
    return await get_reminders("nikola")


async def confirm_medication_taken(reminder_id: str, med_id: str) -> str:
    """Record that the user took their medication today.
    
    Args:
        reminder_id: The ID of the reminder to mark as confirmed.
        med_id: The ID of the medication document.
    """
    from datetime import datetime
    now = datetime.now().isoformat()
    await update_reminder("nikola", reminder_id, {"status": "confirmed"})
    await update_medication("nikola", med_id, {"last_taken_at": now})
    return "Medication successfully recorded as taken."


root_agent = LlmAgent(
    name="medication",
    model=FAST_MODEL,
    description="Handles questions about medications, dosage schedules, and reminders.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_my_medications, get_my_reminders, confirm_medication_taken],
)
