import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.genai import types

from memory import get_contacts
from models import AgentResponse

_SYSTEM_PROMPT = """You are a warm companion helping elderly users stay connected with family and friends.
You already know who the user is. Never ask for their name or any identity information.
When asked about contacts or family, always call get_my_contacts immediately and answer based on the results.
Gently remind them who they haven't spoken to recently.
Be encouraging and warm, never guilt-tripping."""

async def get_my_contacts() -> list[dict]:
    """Get the user's contact list including family and friends with last contact dates."""
    return await get_contacts("nikola")


root_agent = LlmAgent(
    name="people",
    model=FAST_MODEL,
    description="Helps the user stay in touch with family and friends.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_my_contacts],
)

_session_service = InMemorySessionService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(app_name="people", agent=root_agent, session_service=_session_service)
    return _runner


async def run(user_id: str, message: str) -> AgentResponse:
    runner = _get_runner()
    session = await _session_service.create_session(app_name="people", user_id=user_id)
    user_msg = types.Content(parts=[types.Part(text=message)])

    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=user_msg):
        if event.is_final_response() and event.content:
            final_text = "\n".join(part.text for part in event.content.parts if part.text)

    return AgentResponse(
        response=final_text or "I couldn't get that information right now. Please try again.",
        agent="people",
        media=None,
    )
