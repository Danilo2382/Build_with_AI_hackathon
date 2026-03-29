import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent

from memory import get_medications

_SYSTEM_PROMPT = """You are a warm, helpful medication assistant for elderly users.
You already know who the user is. Never ask for their name, date of birth, or any identity information.
When asked about medications, always call get_my_medications immediately and answer based on the results.
Use simple language and short sentences. Be caring and patient.
If the user says they took a medication, acknowledge it warmly."""


async def get_my_medications() -> list[dict]:
    """Get the user's medication list including names, doses, and schedules."""
    return await get_medications("nikola")


root_agent = LlmAgent(
    name="medication",
    model=FAST_MODEL,
    description="Handles questions about medications, dosage schedules, and reminders.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_my_medications],
)
