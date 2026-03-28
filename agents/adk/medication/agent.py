import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_medications
from models import AgentResponse

_SYSTEM_PROMPT = """You are a warm, helpful medication assistant for elderly users.
Answer questions about medication schedules, dosage, and reminders.
Use simple language and short sentences. Be caring and patient.
If the user says they took a medication, acknowledge it warmly."""

root_agent = LlmAgent(
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
    meds = await get_medications(user_id)

    context = f"User medications:\n{json.dumps(meds, indent=2)}\n\n" if meds else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    return AgentResponse(response=response.text, agent="medication", media=None)
