import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_get_memory_returns_empty_dict_when_no_doc(firestore_empty):
    db, _ = firestore_empty
    with patch("memory._get_db", return_value=db):
        import memory
        result = await memory.get_memory("demo_user", "medication")
    assert result == {}


@pytest.mark.asyncio
async def test_get_memory_returns_stored_data(firestore_medication):
    db, _ = firestore_medication
    with patch("memory._get_db", return_value=db):
        import memory
        result = await memory.get_memory("demo_user", "medication")
    assert result["medications"][0]["name"] == "Aspirin"


@pytest.mark.asyncio
async def test_update_memory_calls_set_with_merge(firestore_empty):
    db, doc_ref = firestore_empty
    updates = {"medications": [{"name": "Aspirin"}]}
    with patch("memory._get_db", return_value=db):
        import memory
        await memory.update_memory("demo_user", "medication", updates)
    doc_ref.set.assert_called_once_with(updates, merge=True)


@pytest.mark.asyncio
async def test_get_memory_uses_correct_firestore_path(firestore_empty):
    db, _ = firestore_empty
    with patch("memory._get_db", return_value=db):
        import memory
        await memory.get_memory("user_123", "exercise")
    db.collection.assert_called_with("agent_memory")
    db.collection().document.assert_called_with("user_123")
    db.collection().document().collection.assert_called_with("exercise")
    db.collection().document().collection().document.assert_called_with("data")
