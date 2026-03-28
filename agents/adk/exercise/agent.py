import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_exercise, update_exercise
from models import AgentResponse

_SYSTEM_PROMPT = """You are a friendly exercise and stretching coach for elderly users.
Encourage gentle movement. Celebrate small wins warmly.
Keep sentences short. Safety first — never push too hard.
Respect any physical limitations the user has.
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
    state = await get_exercise(user_id)

    context = f"User exercise profile:\n{json.dumps(state, indent=2)}\n\n" if state else ""
    response = await _get_model().generate_content_async(f"{context}User: {message}")

    today = date.today().isoformat()
    streak = state.get("streak_days", 0)
    if state.get("last_session") != today:
        streak += 1

    await update_exercise(user_id, {
        **state,
        "last_session": today,
        "streak_days": streak,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="exercise", media=None)
