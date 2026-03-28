import importlib

import pytest
from unittest.mock import MagicMock, patch

from models import AgentResponse
from tests.conftest import _make_firestore_mock


@pytest.fixture
def firestore_exercise():
    return _make_firestore_mock(data={
        "last_session": "2026-03-27",
        "streak_days": 3,
        "history": [{"date": "2026-03-27", "type": "stretching", "duration_min": 10}],
    })


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini, firestore_empty):
    db, _ = firestore_empty
    with patch("memory._get_db", return_value=db):
        from agents.exercise import run
        result = await run("demo_user", "Let's stretch")
    assert isinstance(result, AgentResponse)
    assert result.agent == "exercise"
    assert result.media is None


@pytest.mark.asyncio
async def test_run_injects_history_into_prompt(firestore_exercise):
    db, _ = firestore_exercise
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Great job!"
        return m

    with patch("memory._get_db", return_value=db):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            import agents.exercise as ex
            importlib.reload(ex)
            await ex.run("demo_user", "I did stretching today")

    assert "streak" in captured[0] or "2026-03-27" in captured[0]


@pytest.mark.asyncio
async def test_run_updates_streak(mock_gemini, firestore_empty):
    db, doc_ref = firestore_empty
    with patch("memory._get_db", return_value=db):
        from agents.exercise import run
        await run("demo_user", "I finished my exercises")
    doc_ref.set.assert_called_once()
    saved = doc_ref.set.call_args[0][0]
    assert "last_session" in saved
