import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.genai import types
from datetime import date, datetime, timezone

from memory import get_exercise, update_exercise
from models import AgentResponse

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

_session_service = InMemorySessionService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(app_name="exercise", agent=root_agent, session_service=_session_service)
    return _runner


async def run(user_id: str, message: str) -> AgentResponse:
    runner = _get_runner()
    session = await _session_service.create_session(app_name="exercise", user_id=user_id)
    user_msg = types.Content(parts=[types.Part(text=message)])

    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=user_msg):
        if event.is_final_response() and event.content:
            final_text = "\n".join(part.text for part in event.content.parts if part.text)

    return AgentResponse(
        response=final_text or "I couldn't get that information right now. Please try again.",
        agent="exercise",
        media=None,
    )
