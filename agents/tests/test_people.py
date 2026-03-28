import importlib

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini):
    with patch("adk.people.agent.get_contacts", new_callable=AsyncMock, return_value=[]):
        from adk.people.agent import run
        result = await run("demo_user", "Should I call Ana?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "people"
    assert result.media is None


@pytest.mark.asyncio
async def test_run_injects_contacts_into_prompt():
    contacts = [{"id": "con_001", "name": "Ana", "relationship": "daughter", "days_since": 14}]
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Yes, call Ana!"
        return m

    with patch("memory.get_contacts", new_callable=AsyncMock, return_value=contacts):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            import adk.people.agent as ppl
            importlib.reload(ppl)
            await ppl.run("demo_user", "Who should I call?")

    assert "Ana" in captured[0]


@pytest.mark.asyncio
async def test_run_with_empty_contacts(mock_gemini):
    with patch("adk.people.agent.get_contacts", new_callable=AsyncMock, return_value=[]):
        from adk.people.agent import run
        result = await run("demo_user", "Who should I contact?")
    assert isinstance(result, AgentResponse)
