from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from models import AgentResponse, MediaItem


def _make_event(text: str):
    """Build a mock ADK final response event."""
    part = MagicMock()
    part.text = text
    content = MagicMock()
    content.parts = [part]
    event = MagicMock()
    event.is_final_response.return_value = True
    event.content = content
    return event


async def _aiter(*items):
    for item in items:
        yield item


def _agent_resp(agent: str = "oonook", media=None) -> AgentResponse:
    return AgentResponse(response="Test response", agent=agent, media=media)


@pytest.fixture
def app():
    from main import app
    return app


@pytest.mark.asyncio
async def test_health(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_returns_agent_response(app):
    event = _make_event("You take Aspirin at 8am.")
    with patch("main._runner.run_async", return_value=_aiter(event)):
        with patch("main._get_or_create_session", new_callable=AsyncMock, return_value="session-u1"):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/chat", json={"user_id": "u1", "message": "When do I take aspirin?"})
    assert resp.status_code == 200
    assert resp.json()["response"] == "You take Aspirin at 8am."
    assert resp.json()["agent"] == "oonook"


@pytest.mark.asyncio
async def test_chat_error_returns_fallback(app):
    async def _boom(*args, **kwargs):
        raise RuntimeError("boom")
        yield  # make it an async generator

    with patch("main._runner.run_async", side_effect=RuntimeError("boom")):
        with patch("main._get_or_create_session", new_callable=AsyncMock, return_value="session-u1"):
            async with AsyncClient(
                transport=ASGITransport(app=app, raise_app_exceptions=False),
                base_url="http://test",
            ) as client:
                resp = await client.post("/chat", json={"user_id": "u1", "message": "hello"})
    assert resp.status_code == 200
    assert "fallback_response" in resp.json()


@pytest.mark.asyncio
async def test_vision_image_endpoint(app):
    media = MediaItem(type="image", url="https://storage.googleapis.com/bucket/x.jpg")
    with patch("main.run_image", new_callable=AsyncMock,
               return_value=_agent_resp("vision", media=media)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/vision/image",
                json={"user_id": "u1", "image_base64": "data:image/jpeg;base64,/9j/4AAQ=="},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "vision"
    assert data["media"]["type"] == "image"


@pytest.mark.asyncio
async def test_vision_video_endpoint(app):
    media = MediaItem(type="video", url="https://storage.googleapis.com/bucket/x.mp4")
    with patch("main.run_video", new_callable=AsyncMock,
               return_value=_agent_resp("vision", media=media)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/vision/video",
                json={"user_id": "u1", "video_base64": "data:video/mp4;base64,AAAAAAAA"},
            )
    assert resp.status_code == 200
    assert resp.json()["media"]["type"] == "video"
