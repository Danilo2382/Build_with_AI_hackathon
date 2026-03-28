import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_db(snap_data=None, docs=None):
    """Build a Firestore mock supporting single-doc gets, .where() queries, and sets."""
    snap = MagicMock()
    snap.exists = snap_data is not None
    snap.to_dict.return_value = snap_data

    doc_snaps = []
    for doc_id, data in (docs or {}).items():
        d = MagicMock()
        d.id = doc_id
        d.to_dict.return_value = data
        doc_snaps.append(d)

    doc_ref = MagicMock()
    doc_ref.get = AsyncMock(return_value=snap)
    doc_ref.set = AsyncMock()

    query_ref = MagicMock()
    query_ref.get = AsyncMock(return_value=doc_snaps)

    col_ref = MagicMock()
    col_ref.get = AsyncMock(return_value=doc_snaps)
    col_ref.where.return_value = query_ref
    col_ref.document.return_value = doc_ref

    db = MagicMock()
    db.collection.return_value = col_ref
    return db, doc_ref


@pytest.mark.asyncio
async def test_get_profile_returns_dict():
    db, _ = _make_db(snap_data={"name": "Mirko", "age": 72})
    with patch("memory._get_db", return_value=db):
        from memory import get_profile
        result = await get_profile("demo_user")
    assert result["name"] == "Mirko"


@pytest.mark.asyncio
async def test_get_profile_returns_empty_when_missing():
    db, _ = _make_db(snap_data=None)
    with patch("memory._get_db", return_value=db):
        from memory import get_profile
        result = await get_profile("demo_user")
    assert result == {}


@pytest.mark.asyncio
async def test_get_medications_returns_list():
    docs = {"med_001": {"name": "Aspirin", "dose": "100mg"}}
    db, _ = _make_db(docs=docs)
    with patch("memory._get_db", return_value=db):
        from memory import get_medications
        result = await get_medications("demo_user")
    assert len(result) == 1
    assert result[0]["id"] == "med_001"
    assert result[0]["name"] == "Aspirin"


@pytest.mark.asyncio
async def test_get_contacts_returns_list():
    docs = {"con_001": {"name": "Ana", "relationship": "daughter"}}
    db, _ = _make_db(docs=docs)
    with patch("memory._get_db", return_value=db):
        from memory import get_contacts
        result = await get_contacts("demo_user")
    assert result[0]["name"] == "Ana"


@pytest.mark.asyncio
async def test_get_exercise_returns_dict():
    db, _ = _make_db(snap_data={"streak_days": 3, "last_session": "2026-03-27"})
    with patch("memory._get_db", return_value=db):
        from memory import get_exercise
        result = await get_exercise("demo_user")
    assert result["streak_days"] == 3


@pytest.mark.asyncio
async def test_update_exercise_calls_set_with_merge():
    db, doc_ref = _make_db()
    with patch("memory._get_db", return_value=db):
        from memory import update_exercise
        await update_exercise("demo_user", {"streak_days": 4})
    doc_ref.set.assert_called_once_with({"streak_days": 4}, merge=True)


@pytest.mark.asyncio
async def test_get_checkups_returns_list():
    docs = {"chk_001": {"doctor": "Dr. Petrović", "date": "2026-04-05"}}
    db, _ = _make_db(docs=docs)
    with patch("memory._get_db", return_value=db):
        from memory import get_checkups
        result = await get_checkups("demo_user")
    assert result[0]["doctor"] == "Dr. Petrović"


@pytest.mark.asyncio
async def test_uses_flat_collection_paths():
    db, _ = _make_db(snap_data={})
    with patch("memory._get_db", return_value=db):
        from memory import get_profile, get_exercise
        await get_profile("user_123")
        await get_exercise("user_123")
    calls = [c.args[0] for c in db.collection.call_args_list]
    assert "users" in calls
    assert "exercise" in calls
