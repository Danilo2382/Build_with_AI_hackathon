import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def gemini_text():
    return "Test response from Gemini"


@pytest.fixture
def mock_gemini(gemini_text):
    """Patches GenerativeModel.generate_content_async for all tests that use it."""
    mock_resp = MagicMock()
    mock_resp.text = gemini_text
    with patch(
        "vertexai.generative_models.GenerativeModel.generate_content_async",
        new_callable=AsyncMock,
        return_value=mock_resp,
    ) as m:
        yield m
