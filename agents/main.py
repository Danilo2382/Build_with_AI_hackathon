import asyncio
import base64
import logging

import config  # noqa: F401 — ensures vertexai.init() is called
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from google.adk.runners import Runner, LiveRequestQueue
from google.adk.sessions import InMemorySessionService
from google.genai import types
from vertexai.generative_models import GenerativeModel, Part

from adk.root.agent import root_agent
from adk.vision.agent import run_image, run_video
from config import FAST_MODEL
from models import AgentResponse, ChatRequest, GenerateRemindersRequest, VideoRequest, VisionRequest, VoiceChatRequest, VoiceReminderRequest
from reminders import run as run_reminders, run_voice as run_voice_reminder

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


@app.websocket("/chat/voice/stream")
async def voice_stream(ws: WebSocket, user_id: str):
    await ws.accept()
    session_id = await _get_or_create_session(user_id)
    queue = LiveRequestQueue()

    async def stream_responses():
        try:
            async for event in _runner.run_live(
                user_id=user_id, session_id=session_id,
                live_request_queue=queue,
            ):
                if event.audio_data:
                    await ws.send_bytes(event.audio_data)
        except Exception as e:
            logger.error(f"Live stream error: {e}")

    asyncio.create_task(stream_responses())
    try:
        async for chunk in ws.iter_bytes():
            queue.send_audio(chunk)  # PCM in from mic
    except Exception as e:
        logger.error(f"WebSocket client disconnected or error: {e}")


@app.post("/reminders/generate")
async def generate_reminders(body: GenerateRemindersRequest) -> dict:
    return await run_reminders(body.user_id)


@app.post("/reminders/voice")
async def voice_reminder(body: VoiceReminderRequest) -> dict:
    return await run_voice_reminder(body.user_id, body.message)


@app.get("/contacts/{contact_id}/describe")
async def describe_contact(contact_id: str) -> dict:
    from memory import get_contacts
    from vertexai.generative_models import GenerativeModel
    db = __import__("memory")._get_db()
    snap = await db.collection("contacts").document(contact_id).get()
    contact = snap.to_dict()
    if not contact:
        return {"description": ""}
    name         = contact.get("name", "this person")
    relationship = contact.get("relationship", "someone important")
    notes        = contact.get("notes", "")
    last_contact = contact.get("last_contact", "")
    days_since   = contact.get("days_since", "")
    prompt = (
        f"Write 2-3 warm, personal sentences reminding an elderly person about {name}, their {relationship}. "
        f"Use these notes: {notes}. "
        + (f"They last spoke {days_since} days ago (on {last_contact}). " if days_since else "")
        + "Be affectionate and specific. No greetings, just the description."
    )
    model = GenerativeModel(model_name=FAST_MODEL)
    response = await model.generate_content_async(prompt)
    return {"description": response.text.strip()}


@app.post("/vision/image", response_model=AgentResponse)
async def vision_image(body: VisionRequest) -> AgentResponse:
    return await run_image(body.user_id, body.image_base64)


@app.post("/vision/video", response_model=AgentResponse)
async def vision_video(body: VideoRequest) -> AgentResponse:
    return await run_video(body.user_id, body.video_base64)
