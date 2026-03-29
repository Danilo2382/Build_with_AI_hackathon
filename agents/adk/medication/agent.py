import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.genai import types

from memory import get_medications
from models import AgentResponse

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

_session_service = InMemorySessionService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(app_name="medication", agent=root_agent, session_service=_session_service)
    return _runner


async def run(user_id: str, message: str) -> AgentResponse:
    runner = _get_runner()
    session = await _session_service.create_session(app_name="medication", user_id=user_id)
    user_msg = types.Content(parts=[types.Part(text=message)])

    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=user_msg):
        if event.is_final_response() and event.content:
            final_text = "\n".join(part.text for part in event.content.parts if part.text)

    return AgentResponse(
        response=final_text or "I couldn't get that information right now. Please try again.",
        agent="medication",
        media=None,
    )
