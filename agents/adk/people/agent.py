import json
from datetime import datetime, timezone

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_memory, update_memory
from models import AgentResponse

_SYSTEM_PROMPT = """You are a warm companion helping elderly users stay connected with family and friends.
Gently remind them who they haven't spoken to recently.
Be encouraging and warm, never guilt-tripping.
Use the contact history to give personalised nudges."""

root_agent = LlmAgent(
    name="people",
    model=FAST_MODEL,
    description="Helps the user stay in touch with family and friends.",
    instruction=_SYSTEM_PROMPT,
)

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=FAST_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


async def run(user_id: str, message: str) -> AgentResponse:
    mem = await get_memory(user_id, "people")

    context = f"User contact history:\n{json.dumps(mem, indent=2)}\n\n" if mem else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    await update_memory(user_id, "people", {
        **mem,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="people", media=None)
