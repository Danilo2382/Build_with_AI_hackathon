import json
from datetime import datetime, timezone

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_memory, update_memory
from models import AgentResponse

_SYSTEM_PROMPT = """You are a warm, helpful medication assistant for elderly users.
Answer questions about medication schedules, dosage, and reminders.
Use simple language and short sentences. Be caring and patient.
If the user says they took a medication, acknowledge it warmly."""

_agent = LlmAgent(
    name="medication",
    model=FAST_MODEL,
    description="Handles questions about medications, dosage schedules, and reminders.",
    instruction=_SYSTEM_PROMPT,
)

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=FAST_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


async def run(user_id: str, message: str) -> AgentResponse:
    mem = await get_memory(user_id, "medication")

    context = f"User medication history:\n{json.dumps(mem, indent=2)}\n\n" if mem else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    await update_memory(user_id, "medication", {
        **mem,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="medication", media=None)
