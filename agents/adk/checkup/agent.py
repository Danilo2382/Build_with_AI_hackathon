import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_checkups
from models import AgentResponse

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

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=FAST_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


async def run(user_id: str, message: str) -> AgentResponse:
    checkups = await get_checkups(user_id)

    context = f"User upcoming checkups:\n{json.dumps(checkups, indent=2)}\n\n" if checkups else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    return AgentResponse(response=response.text, agent="checkup", media=None)
