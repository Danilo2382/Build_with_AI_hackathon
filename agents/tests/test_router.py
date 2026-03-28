import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import AgentResponse


def _gemini_mock(text: str):
    m = MagicMock()
    m.text = text
    return m


def _agent_response(agent: str) -> AgentResponse:
    return AgentResponse(response=f"Response from {agent}", agent=agent, media=None)


@pytest.mark.asyncio
async def test_routes_to_medication(mock_gemini):
    mock_gemini.return_value = _gemini_mock("medication")
    with patch("router.run_medication", new_callable=AsyncMock,
               return_value=_agent_response("medication")) as med:
        from router import route
        result = await route("demo_user", "When do I take my aspirin?")
    assert result.agent == "medication"
    med.assert_called_once()


@pytest.mark.asyncio
async def test_routes_to_exercise(mock_gemini):
    mock_gemini.return_value = _gemini_mock("exercise")
    with patch("router.run_exercise", new_callable=AsyncMock,
               return_value=_agent_response("exercise")) as ex:
        from router import route
        result = await route("demo_user", "I want to do some stretching")
    assert result.agent == "exercise"
    ex.assert_called_once()


@pytest.mark.asyncio
async def test_routes_to_checkup(mock_gemini):
    mock_gemini.return_value = _gemini_mock("checkup")
    with patch("router.run_checkup", new_callable=AsyncMock,
               return_value=_agent_response("checkup")) as chk:
        from router import route
        result = await route("demo_user", "When is my doctor appointment?")
    assert result.agent == "checkup"
    chk.assert_called_once()


@pytest.mark.asyncio
async def test_routes_to_people(mock_gemini):
    mock_gemini.return_value = _gemini_mock("people")
    with patch("router.run_people", new_callable=AsyncMock,
               return_value=_agent_response("people")) as ppl:
        from router import route
        result = await route("demo_user", "Should I call my daughter?")
    assert result.agent == "people"
    ppl.assert_called_once()


@pytest.mark.asyncio
async def test_general_intent_falls_back_to_checkup(mock_gemini):
    mock_gemini.return_value = _gemini_mock("general")
    with patch("router.run_checkup", new_callable=AsyncMock,
               return_value=_agent_response("checkup")) as chk:
        from router import route
        result = await route("demo_user", "What is the weather today?")
    assert result.agent == "checkup"
    chk.assert_called_once()


@pytest.mark.asyncio
async def test_unknown_intent_falls_back_to_checkup(mock_gemini):
    mock_gemini.return_value = _gemini_mock("something_random")
    with patch("router.run_checkup", new_callable=AsyncMock,
               return_value=_agent_response("checkup")) as chk:
        from router import route
        await route("demo_user", "blah blah")
    chk.assert_called_once()
