import base64
import logging

import config  # noqa: F401 — ensures vertexai.init() is called
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from vertexai.generative_models import GenerativeModel, Part

from adk.reminders.agent import run as run_reminders, run_voice as run_voice_reminder
from adk.vision.agent import run_image, run_video
from models import AgentResponse, ChatRequest, GenerateRemindersRequest, VideoRequest, VisionRequest, VoiceReminderRequest
from router import route

logger = logging.getLogger(__name__)

app = FastAPI(title="Oonook Agents", version="1.0.0")


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
    audio_bytes = base64.b64decode(body.audio_base64)
    audio_part = Part.from_data(data=audio_bytes, mime_type="audio/mp4")
    # Use SMART_MODEL for STT — gemini-2.5-flash-lite does not support audio input
    stt_model = GenerativeModel(model_name=config.SMART_MODEL)
    stt_response = await stt_model.generate_content_async(
        [audio_part, "Transcribe exactly what the user said. Output only the transcription, nothing else."]
    )
    message = stt_response.text.strip()
    logger.info("[chat] transcribed: %s", message)
    print(f"[chat] transcribed: {message!r}", flush=True)
    return await route(body.user_id, message)


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
