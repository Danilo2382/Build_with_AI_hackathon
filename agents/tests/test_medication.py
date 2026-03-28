import importlib

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini):
    with patch("adk.medication.agent.get_medications", new_callable=AsyncMock, return_value=[]):
        from adk.medication.agent import run
        result = await run("demo_user", "When do I take aspirin?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "medication"
    assert result.media is None
    assert result.response == "Test response from Gemini"


@pytest.mark.asyncio
async def test_run_injects_memory_into_prompt():
    meds = [{"id": "med_001", "name": "Aspirin", "dose": "100mg", "schedule": ["08:00", "20:00"]}]
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Take Aspirin at 8am."
        return m

    with patch("memory.get_medications", new_callable=AsyncMock, return_value=meds):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            import adk.medication.agent as med
            importlib.reload(med)
            await med.run("demo_user", "When do I take aspirin?")

    assert "Aspirin" in captured[0]


@pytest.mark.asyncio
async def test_run_with_empty_medications(mock_gemini):
    with patch("adk.medication.agent.get_medications", new_callable=AsyncMock, return_value=[]):
        from adk.medication.agent import run
        result = await run("demo_user", "Do I have any medications?")
    assert isinstance(result, AgentResponse)
