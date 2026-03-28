import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_firestore_mock(data: dict | None = None):
    """Returns (db_mock, doc_ref_mock). data is what snap.to_dict() returns."""
    snap = MagicMock()
    snap.to_dict.return_value = data
    doc_ref = MagicMock()
    doc_ref.get = AsyncMock(return_value=snap)
    doc_ref.set = AsyncMock()
    db = MagicMock()
    db.collection.return_value.document.return_value.collection.return_value.document.return_value = doc_ref
    return db, doc_ref


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


@pytest.fixture
def firestore_empty():
    return _make_firestore_mock(data=None)


@pytest.fixture
def firestore_medication():
    return _make_firestore_mock(data={
        "medications": [{"name": "Aspirin", "dose": "100mg", "schedule": ["08:00", "20:00"]}],
        "last_confirmed": {},
        "notes": "Take with food",
    })
