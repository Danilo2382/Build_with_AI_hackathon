import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL
from google.adk.agents import LlmAgent

from memory import get_contacts, update_contact, update_reminder, get_reminders

_SYSTEM_PROMPT = """You are a warm companion helping elderly users stay connected.
1. Use get_my_contacts to answer questions about family and friends.
2. If the user says they spoke to someone (e.g., 'I just called Ana'):
   - Find the contact_id for Ana using get_my_contacts.
   - Call record_contact_made(contact_id).
   - Congratulate them warmly.
3. Be encouraging and warm, never guilt-tripping."""


async def get_my_contacts() -> list[dict]:
    """Get the user's contact list including family and friends with last contact dates."""
    return await get_contacts("nikola")


async def record_contact_made(contact_id: str) -> str:
    """Record that the user successfully reached out to a contact today.
    
    Args:
        contact_id: The ID of the contact the user spoke to.
    """
    from datetime import date
    today = date.today().isoformat()
    await update_contact("nikola", contact_id, {"last_contact": today})
    
    # Mark relevant reminder as confirmed if it exists
    reminders = await get_reminders("nikola")
    for r in reminders:
        if r.get("type") == "people" and r.get("linked_id") == contact_id:
            await update_reminder("nikola", r["id"], {"status": "confirmed"})
            break
            
    return "That's wonderful! I've recorded that you've been in touch."


root_agent = LlmAgent(
    name="people",
    model=FAST_MODEL,
    description="Helps the user stay in touch with family and friends.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_my_contacts, record_contact_made],
)
