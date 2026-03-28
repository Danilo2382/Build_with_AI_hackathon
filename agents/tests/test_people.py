import importlib

import pytest
from unittest.mock import MagicMock, patch

from models import AgentResponse
from tests.conftest import _make_firestore_mock


@pytest.fixture
def firestore_people():
    return _make_firestore_mock(data={
        "contacts": [
            {"name": "Ana", "relationship": "daughter", "last_contact": "2026-03-14", "days_since": 14}
        ]
    })


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini, firestore_empty):
    db, _ = firestore_empty
    with patch("memory._get_db", return_value=db):
        from agents.people import run
        result = await run("demo_user", "Should I call Ana?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "people"
    assert result.media is None


@pytest.mark.asyncio
async def test_run_injects_contacts_into_prompt(firestore_people):
    db, _ = firestore_people
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Yes, call Ana!"
        return m

    with patch("memory._get_db", return_value=db):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            import agents.people as ppl
            importlib.reload(ppl)
            await ppl.run("demo_user", "Who should I call?")

    assert "Ana" in captured[0]


@pytest.mark.asyncio
async def test_run_writes_memory(mock_gemini, firestore_empty):
    db, doc_ref = firestore_empty
    with patch("memory._get_db", return_value=db):
        from agents.people import run
        await run("demo_user", "I called my daughter")
    doc_ref.set.assert_called_once()
