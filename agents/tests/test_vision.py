import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import AgentResponse


def _gemini_mock(text: str):
    m = MagicMock()
    m.text = text
    return m


@pytest.mark.asyncio
async def test_run_image_returns_agent_response():
    with patch(
        "vertexai.generative_models.GenerativeModel.generate_content_async",
        new_callable=AsyncMock,
        return_value=_gemini_mock("This is Aspirin 100mg."),
    ):
        from adk.vision.agent import run_image
        result = await run_image("demo_user", "data:image/jpeg;base64,/9j/4AAQ==")

    assert isinstance(result, AgentResponse)
    assert result.agent == "vision"
    assert result.media is None


@pytest.mark.asyncio
async def test_run_video_returns_agent_response():
    with patch(
        "vertexai.generative_models.GenerativeModel.generate_content_async",
        new_callable=AsyncMock,
        return_value=_gemini_mock("You are exercising correctly."),
    ):
        from adk.vision.agent import run_video
        result = await run_video("demo_user", "data:video/mp4;base64,AAAAAAAA")

    assert isinstance(result, AgentResponse)
    assert result.agent == "vision"
    assert result.media is None
