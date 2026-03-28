import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

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

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=FAST_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


async def run(user_id: str, message: str) -> AgentResponse:
    contacts = await get_contacts(user_id)

    context = f"User contacts:\n{json.dumps(contacts, indent=2)}\n\n" if contacts else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    return AgentResponse(response=response.text, agent="people", media=None)
