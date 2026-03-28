from config import FAST_MODEL
from vertexai.generative_models import GenerativeModel

from adk.checkup.agent import run as run_checkup
from adk.exercise.agent import run as run_exercise
from adk.medication.agent import run as run_medication
from adk.people.agent import run as run_people
from adk.vision.agent import run_image, run_video
from models import AgentResponse

_ROUTER_PROMPT = """You are a routing assistant. Classify the user message into exactly one of these intents:
- medication  (questions about pills, doses, schedules, taking medications)
- exercise    (physical activity, stretching, walking, workouts)
- checkup     (doctor appointments, medical checkups, health exams)
- people      (family, friends, staying in touch, contacts)
- general     (anything else)

Reply with only the intent word, nothing else."""

_router_model: GenerativeModel | None = None


def _get_router_model() -> GenerativeModel:
    global _router_model
    if _router_model is None:
        _router_model = GenerativeModel(model_name=FAST_MODEL)
    return _router_model


async def route(user_id: str, message: str) -> AgentResponse:
    response = await _get_router_model().generate_content_async(
        f"{_ROUTER_PROMPT}\n\nUser message: {message}"
    )
    intent = response.text.strip().lower()

    if intent == "medication":
        return await run_medication(user_id, message)
    if intent == "exercise":
        return await run_exercise(user_id, message)
    if intent == "checkup":
        return await run_checkup(user_id, message)
    if intent == "people":
        return await run_people(user_id, message)

    # general or unrecognised — default to checkup as a safe fallback
    return await run_checkup(user_id, message)
