import pytest
from unittest.mock import patch

from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini):
    from adk.checkup.agent import run
    result = await run("demo_user", "When is my next checkup?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "checkup"
    assert result.media is None
    assert result.response == "Test response from Gemini"


@pytest.mark.asyncio
async def test_run_never_touches_firestore(mock_gemini):
    with patch("memory._get_db") as mock_get_db:
        from adk.checkup.agent import run
        await run("demo_user", "Do I have a checkup soon?")
    mock_get_db.assert_not_called()
