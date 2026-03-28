import pytest
from unittest.mock import AsyncMock, patch

from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini):
    with patch("adk.checkup.agent.get_checkups", new_callable=AsyncMock, return_value=[]):
        from adk.checkup.agent import run
        result = await run("demo_user", "When is my next checkup?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "checkup"
    assert result.media is None
    assert result.response == "Test response from Gemini"


@pytest.mark.asyncio
async def test_run_injects_checkups_into_prompt():
    checkups = [{"id": "chk_001", "doctor": "Dr. Petrović", "date": "2026-04-05", "time": "10:30"}]
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        from unittest.mock import MagicMock
        m = MagicMock()
        m.text = "You have a checkup on April 5th."
        return m

    with patch("adk.checkup.agent.get_checkups", new_callable=AsyncMock, return_value=checkups):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            from adk.checkup.agent import run
            await run("demo_user", "Do I have any appointments?")

    assert "Petrović" in captured[0] or "2026-04-05" in captured[0]
