import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from models import AgentResponse, MediaItem


def _agent_resp(agent: str = "checkup", media=None) -> AgentResponse:
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
    with patch("main.route", new_callable=AsyncMock, return_value=_agent_resp("medication")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/chat", json={"user_id": "u1", "message": "When do I take aspirin?"})
    assert resp.status_code == 200
    assert resp.json()["agent"] == "medication"


@pytest.mark.asyncio
async def test_chat_error_returns_fallback(app):
    with patch("main.route", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
        # raise_app_exceptions=False: Starlette sends the fallback response then re-raises;
        # httpx must not propagate the re-raise so we can inspect the response.
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
