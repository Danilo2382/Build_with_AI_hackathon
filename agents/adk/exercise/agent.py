import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent

from memory import get_exercise, update_exercise

_SYSTEM_PROMPT = """You are a friendly exercise and stretching coach for elderly users.
You already know who the user is. Never ask for their name or any identity information.
When asked about their exercise history or profile, call get_my_exercise_profile immediately.
When the user completes a session, call record_exercise_session.
Encourage gentle movement. Celebrate small wins warmly.
Keep sentences short. Safety first — never push too hard.
Respect any physical limitations the user has."""


async def get_my_exercise_profile() -> dict:
    """Get the user's exercise profile including streak, last session, and physical limitations."""
    return await get_exercise("nikola")


async def record_exercise_session() -> str:
    """Record that the user completed an exercise session today, updating their streak."""
    state = await get_exercise("nikola")
    today = date.today().isoformat()
    streak = state.get("streak_days", 0)
    if state.get("last_session") != today:
        streak += 1
    await update_exercise("nikola", {
        **state,
        "last_session": today,
        "streak_days": streak,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })
    return f"Session recorded. Streak is now {streak} days."


root_agent = LlmAgent(
    name="exercise",
    model=FAST_MODEL,
    description="Handles exercise, stretching, and physical activity questions.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_my_exercise_profile, record_exercise_session],
)
