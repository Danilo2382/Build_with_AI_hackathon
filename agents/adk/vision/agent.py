import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import SMART_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel, Image, Part

from models import AgentResponse

_SYSTEM_PROMPT = """Describe images and videos clearly for elderly users.
Use simple, calm language. Focus on health-relevant details."""

root_agent = LlmAgent(
    name="vision",
    model=SMART_MODEL,
    description="Analyses images and videos for elderly users.",
    instruction=_SYSTEM_PROMPT,
)

_model: GenerativeModel | None = None


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        _model = GenerativeModel(model_name=SMART_MODEL, system_instruction=_SYSTEM_PROMPT)
    return _model


def _decode(data_uri: str) -> tuple[bytes, str]:
    header, encoded = data_uri.split(",", 1)
    mime = header.split(":")[1].split(";")[0]
    return base64.b64decode(encoded), mime


async def run_image(user_id: str, image_base64: str) -> AgentResponse:
    raw, mime = _decode(image_base64)

    response = await _get_model().generate_content_async([
        Part.from_image(Image.from_bytes(raw)),
        "Describe this image for an elderly user in simple terms.",
    ])

    return AgentResponse(response=response.text, agent="vision", media=None)


async def run_video(user_id: str, video_base64: str) -> AgentResponse:
    raw, mime = _decode(video_base64)

    response = await _get_model().generate_content_async([
        Part.from_data(data=raw, mime_type=mime),
        "Describe what is happening in this video for an elderly user.",
    ])

    return AgentResponse(response=response.text, agent="vision", media=None)
