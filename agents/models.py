from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str


class VisionRequest(BaseModel):
    user_id: str
    image_base64: str


class VideoRequest(BaseModel):
    user_id: str
    video_base64: str


class MediaItem(BaseModel):
    type: str  # "image" | "video"
    url: str


class AgentResponse(BaseModel):
    response: str
    agent: str
    media: Optional[MediaItem] = None


class GenerateRemindersRequest(BaseModel):
    user_id: str


class VoiceReminderRequest(BaseModel):
    user_id: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    fallback_response: str
