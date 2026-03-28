import json
from datetime import date, datetime, timezone

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_memory, update_memory
from models import AgentResponse

_SYSTEM_PROMPT = """You are a friendly exercise and stretching coach for elderly users.
Encourage gentle movement. Celebrate small wins warmly.
Keep sentences short. Safety first — never push too hard.
Handle both exercise and stretching topics."""

root_agent = LlmAgent(
    name="exercise",
    model=FAST_MODEL,
    description="Handles exercise, stretching, and physical activity questions.",
    instruction=_SYSTEM_PROMPT,
)

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=FAST_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


async def run(user_id: str, message: str) -> AgentResponse:
    mem = await get_memory(user_id, "exercise")

    context = f"User exercise history:\n{json.dumps(mem, indent=2)}\n\n" if mem else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    today = date.today().isoformat()
    streak = mem.get("streak_days", 0)
    if mem.get("last_session") != today:
        streak += 1

    await update_memory(user_id, "exercise", {
        **mem,
        "last_session": today,
        "streak_days": streak,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="exercise", media=None)
