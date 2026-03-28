import importlib

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini):
    with patch("adk.exercise.agent.get_exercise", new_callable=AsyncMock, return_value={}):
        with patch("adk.exercise.agent.update_exercise", new_callable=AsyncMock):
            from adk.exercise.agent import run
            result = await run("demo_user", "Let's stretch")
    assert isinstance(result, AgentResponse)
    assert result.agent == "exercise"
    assert result.media is None


@pytest.mark.asyncio
async def test_run_injects_history_into_prompt():
    state = {
        "last_session": "2026-03-27",
        "streak_days": 3,
        "limitations": "bad knees",
    }
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Great job!"
        return m

    with patch("memory.get_exercise", new_callable=AsyncMock, return_value=state):
        with patch("memory.update_exercise", new_callable=AsyncMock):
            with patch(
                "vertexai.generative_models.GenerativeModel.generate_content_async",
                side_effect=fake_generate,
            ):
                import adk.exercise.agent as ex
                importlib.reload(ex)
                await ex.run("demo_user", "I did stretching today")

    assert "streak" in captured[0] or "2026-03-27" in captured[0]


@pytest.mark.asyncio
async def test_run_updates_streak(mock_gemini):
    with patch("adk.exercise.agent.get_exercise", new_callable=AsyncMock, return_value={}):
        with patch("adk.exercise.agent.update_exercise", new_callable=AsyncMock) as mock_update:
            from adk.exercise.agent import run
            await run("demo_user", "I finished my exercises")
    mock_update.assert_called_once()
    saved = mock_update.call_args[0][1]
    assert "last_session" in saved
