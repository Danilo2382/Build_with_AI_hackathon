import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent

from memory import get_checkups

_SYSTEM_PROMPT = """You are a caring assistant helping elderly users manage their medical appointments.
You already know who the user is. Never ask for their name or any identity information.
When asked about appointments or checkups, always call get_my_checkups immediately and answer based on the results.
Keep language simple, warm, and reassuring."""


async def get_my_checkups() -> list[dict]:
    """Get the user's upcoming medical checkups and appointments."""
    return await get_checkups("nikola")


root_agent = LlmAgent(
    name="checkup",
    model=FAST_MODEL,
    description="Handles medical checkup reminders and appointment questions.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_my_checkups],
)
