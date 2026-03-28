import importlib

import pytest
from unittest.mock import MagicMock, patch

from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini, firestore_empty):
    db, _ = firestore_empty
    with patch("memory._get_db", return_value=db):
        from adk.medication.agent import run
        result = await run("demo_user", "When do I take aspirin?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "medication"
    assert result.media is None
    assert result.response == "Test response from Gemini"


@pytest.mark.asyncio
async def test_run_injects_memory_into_prompt(firestore_medication):
    db, _ = firestore_medication
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Take Aspirin at 8am."
        return m

    with patch("memory._get_db", return_value=db):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            import adk.medication.agent as med
            importlib.reload(med)
            await med.run("demo_user", "When do I take aspirin?")

    assert "Aspirin" in captured[0]


@pytest.mark.asyncio
async def test_run_writes_memory_after_response(mock_gemini, firestore_empty):
    db, doc_ref = firestore_empty
    with patch("memory._get_db", return_value=db):
        from adk.medication.agent import run
        await run("demo_user", "I just took my aspirin")
    doc_ref.set.assert_called_once()
