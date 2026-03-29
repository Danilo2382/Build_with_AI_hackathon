import base64
import logging

import config  # noqa: F401 — ensures vertexai.init() is called
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from vertexai.generative_models import GenerativeModel, Part

from adk.root.agent import root_agent
from adk.vision.agent import run_image, run_video
from config import FAST_MODEL
from models import AgentResponse, ChatRequest, GenerateRemindersRequest, VideoRequest, VisionRequest, VoiceChatRequest, VoiceReminderRequest
from reminders import run as run_reminders, run_voice as run_voice_reminder
from tts import synthesize

logger = logging.getLogger(__name__)

app = FastAPI(title="Oonook Agents", version="1.0.0")

_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, app_name="oonook", session_service=_session_service)


async def _get_or_create_session(user_id: str) -> str:
    session_id = f"session-{user_id}"
    existing = await _session_service.get_session(app_name="oonook", user_id=user_id, session_id=session_id)
    if existing is None:
        await _session_service.create_session(app_name="oonook", user_id=user_id, session_id=session_id)
    return session_id


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=200,
        content={"fallback_response": "Sorry, I had trouble understanding that. Please try again."},
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=AgentResponse)
async def chat(body: ChatRequest) -> AgentResponse:
    session_id = await _get_or_create_session(body.user_id)
    content = types.Content(role="user", parts=[types.Part.from_text(text=body.message)])

    response_text = ""
    async for event in _runner.run_async(
        user_id=body.user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text

    return AgentResponse(response=response_text, agent="oonook", media=None)


async def _transcribe(audio_base64: str, mime_type: str = "audio/mp4") -> str:
    """Transcribe audio to text using Gemini."""
    audio_bytes = base64.b64decode(audio_base64)
    model = GenerativeModel(model_name=FAST_MODEL)
    response = await model.generate_content_async([
        Part.from_data(data=audio_bytes, mime_type=mime_type),
        "Transcribe this audio exactly as spoken. Return only the transcribed text, nothing else.",
    ])
    return response.text.strip()


@app.post("/chat/voice", response_model=AgentResponse)
async def chat_voice(body: VoiceChatRequest) -> AgentResponse:
    message = await _transcribe(body.audio_base64, body.mime_type or "audio/mp4")
    logger.info("Transcribed voice: %s", message)
    session_id = await _get_or_create_session(body.user_id)
    content = types.Content(role="user", parts=[types.Part.from_text(text=message)])

    response_text = ""
    async for event in _runner.run_async(
        user_id=body.user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text

    audio_base64 = await synthesize(response_text)
    return AgentResponse(response=response_text, agent="oonook", media=None, audio_base64=audio_base64)


@app.post("/reminders/generate")
async def generate_reminders(body: GenerateRemindersRequest) -> dict:
    return await run_reminders(body.user_id)


@app.post("/reminders/voice")
async def voice_reminder(body: VoiceReminderRequest) -> dict:
    return await run_voice_reminder(body.user_id, body.message)


@app.post("/vision/image", response_model=AgentResponse)
async def vision_image(body: VisionRequest) -> AgentResponse:
    return await run_image(body.user_id, body.image_base64)


@app.post("/vision/video", response_model=AgentResponse)
async def vision_video(body: VideoRequest) -> AgentResponse:
    return await run_video(body.user_id, body.video_base64)
