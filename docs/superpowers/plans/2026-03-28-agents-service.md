# Agents Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Python FastAPI agents service that handles all AI logic for Oonook using Vertex AI Gemini, with Firestore long-term memory for medication, exercise, and people agents.

**Architecture:** ADK `LlmAgent` defines each agent (name, model, instruction, description). `vertexai.GenerativeModel` executes the actual Gemini calls. A router classifies intent with one Gemini call, then dispatches in Python code. Memory agents manually read Firestore before and write after each call.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, `google-adk`, `vertexai` (via `google-cloud-aiplatform`), `google-cloud-firestore`, `google-cloud-storage`, pytest, pytest-asyncio

---

## File Map

```
agents/
├── main.py              # FastAPI app, endpoints, global error handler
├── router.py            # Gemini intent classification + Python dispatch
├── memory.py            # Firestore get/update helpers (async)
├── gcs.py               # GCS upload, returns public HTTPS URL
├── config.py            # env var loading + vertexai.init()
├── models.py            # Pydantic request/response schemas
├── agents/
│   ├── __init__.py
│   ├── medication.py    # LlmAgent def + run(user_id, message)
│   ├── exercise.py      # LlmAgent def + run(user_id, message)
│   ├── checkup.py       # LlmAgent def + run(user_id, message)
│   ├── people.py        # LlmAgent def + run(user_id, message)
│   └── vision.py        # LlmAgent def + run_image() + run_video()
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_memory.py
│   ├── test_gcs.py
│   ├── test_medication.py
│   ├── test_exercise.py
│   ├── test_checkup.py
│   ├── test_people.py
│   ├── test_vision.py
│   ├── test_router.py
│   └── test_main.py
└── requirements.txt
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `agents/requirements.txt`
- Create: `agents/config.py`
- Create: `agents/models.py`
- Create: `agents/pytest.ini`
- Create: `agents/tests/__init__.py`
- Create: `agents/tests/conftest.py`
- Create: `agents/tests/test_models.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
google-adk>=0.2.0
google-cloud-aiplatform>=1.57.0
google-cloud-firestore>=2.16.0
google-cloud-storage>=2.17.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

- [ ] **Step 2: Create config.py**

```python
# agents/config.py
import os
import vertexai

GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west3")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "YOUR_GCS_BUCKET")

# Initialise Vertex AI once at import time — no network call, just sets config
vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
```

- [ ] **Step 3: Create models.py**

```python
# agents/models.py
from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    user_id: str
    message: str


class VisionRequest(BaseModel):
    user_id: str
    image_base64: str


class VideoRequest(BaseModel):
    user_id: str
    video_base64: str


class MediaItem(BaseModel):
    type: str  # "image" | "video"
    url: str


class AgentResponse(BaseModel):
    response: str
    agent: str
    media: Optional[MediaItem] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    fallback_response: str
```

- [ ] **Step 4: Create pytest.ini**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 5: Create tests/conftest.py**

```python
# agents/tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def gemini_text():
    """Raw text returned by a mocked Gemini response."""
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
def firestore_empty():
    return _make_firestore_mock(data=None)


@pytest.fixture
def firestore_medication():
    return _make_firestore_mock(data={
        "medications": [{"name": "Aspirin", "dose": "100mg", "schedule": ["08:00", "20:00"]}],
        "last_confirmed": {},
        "notes": "Take with food",
    })
```

- [ ] **Step 6: Create tests/test_models.py**

```python
# agents/tests/test_models.py
from models import AgentResponse, MediaItem, ChatRequest, ErrorResponse


def test_agent_response_defaults_media_to_none():
    r = AgentResponse(response="Hello", agent="medication")
    assert r.media is None


def test_agent_response_with_media():
    r = AgentResponse(
        response="Here is your image",
        agent="vision",
        media=MediaItem(type="image", url="https://storage.googleapis.com/YOUR_GCS_BUCKET/x.jpg"),
    )
    assert r.media.type == "image"
    assert "YOUR_GCS_BUCKET" in r.media.url


def test_chat_request_fields():
    req = ChatRequest(user_id="demo_user", message="When do I take aspirin?")
    assert req.user_id == "demo_user"
    assert "aspirin" in req.message


def test_error_response_has_fallback():
    err = ErrorResponse(
        error="agent_error",
        message="Something went wrong",
        fallback_response="Sorry, I am having trouble. Please try again.",
    )
    assert err.fallback_response.startswith("Sorry")
```

- [ ] **Step 7: Run tests**

```bash
cd agents
pip install -r requirements.txt
pytest tests/test_models.py -v
```

Expected:
```
test_models.py::test_agent_response_defaults_media_to_none PASSED
test_models.py::test_agent_response_with_media PASSED
test_models.py::test_chat_request_fields PASSED
test_models.py::test_error_response_has_fallback PASSED
4 passed
```

- [ ] **Step 8: Commit**

```bash
git add agents/
git commit -m "feat(agents): project scaffold — models, config, pytest setup"
```

---

## Task 2: Firestore Memory Module

**Files:**
- Create: `agents/memory.py`
- Create: `agents/tests/test_memory.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_memory.py
import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_get_memory_returns_empty_dict_when_no_doc(firestore_empty):
    db, _ = firestore_empty
    with patch("memory.db", db):
        import memory
        result = await memory.get_memory("demo_user", "medication")
    assert result == {}


@pytest.mark.asyncio
async def test_get_memory_returns_stored_data(firestore_medication):
    db, _ = firestore_medication
    with patch("memory.db", db):
        import memory
        result = await memory.get_memory("demo_user", "medication")
    assert result["medications"][0]["name"] == "Aspirin"


@pytest.mark.asyncio
async def test_update_memory_calls_set_with_merge(firestore_empty):
    db, doc_ref = firestore_empty
    updates = {"medications": [{"name": "Aspirin"}]}
    with patch("memory.db", db):
        import memory
        await memory.update_memory("demo_user", "medication", updates)
    doc_ref.set.assert_called_once_with(updates, merge=True)


@pytest.mark.asyncio
async def test_get_memory_uses_correct_firestore_path(firestore_empty):
    db, _ = firestore_empty
    with patch("memory.db", db):
        import memory
        await memory.get_memory("user_123", "exercise")
    db.collection.assert_called_with("agent_memory")
    db.collection().document.assert_called_with("user_123")
    db.collection().document().collection.assert_called_with("exercise")
    db.collection().document().collection().document.assert_called_with("data")
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_memory.py -v
```

Expected: `ModuleNotFoundError: No module named 'memory'`

- [ ] **Step 3: Implement memory.py**

```python
# agents/memory.py
from google.cloud import firestore

db: firestore.AsyncClient = firestore.AsyncClient()


async def get_memory(user_id: str, domain: str) -> dict:
    """Read memory for user+domain. Returns {} if document does not exist."""
    doc = (
        db.collection("agent_memory")
        .document(user_id)
        .collection(domain)
        .document("data")
    )
    snap = await doc.get()
    return snap.to_dict() or {}


async def update_memory(user_id: str, domain: str, updates: dict) -> None:
    """Merge updates into memory document for user+domain."""
    doc = (
        db.collection("agent_memory")
        .document(user_id)
        .collection(domain)
        .document("data")
    )
    await doc.set(updates, merge=True)
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_memory.py -v
```

Expected:
```
test_memory.py::test_get_memory_returns_empty_dict_when_no_doc PASSED
test_memory.py::test_get_memory_returns_stored_data PASSED
test_memory.py::test_update_memory_calls_set_with_merge PASSED
test_memory.py::test_get_memory_uses_correct_firestore_path PASSED
4 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/memory.py agents/tests/test_memory.py
git commit -m "feat(agents): Firestore memory module with get/update helpers"
```

---

## Task 3: GCS Upload Module

**Files:**
- Create: `agents/gcs.py`
- Create: `agents/tests/test_gcs.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_gcs.py
import pytest
from unittest.mock import patch, MagicMock


def _gcs_mock():
    blob = MagicMock()
    blob.upload_from_string = MagicMock()
    bucket = MagicMock()
    bucket.blob.return_value = blob
    client = MagicMock()
    client.bucket.return_value = bucket
    return client, blob


def test_upload_image_returns_public_https_url():
    client, _ = _gcs_mock()
    with patch("gcs.storage.Client", return_value=client):
        with patch("gcs.GCS_BUCKET", "YOUR_GCS_BUCKET"):
            import gcs
            url = gcs.upload_media("data:image/jpeg;base64,/9j/4AAQ==", "image/jpeg")
    assert url.startswith("https://storage.googleapis.com/YOUR_GCS_BUCKET/")
    assert url.endswith(".jpg")


def test_upload_video_returns_mp4_url():
    client, _ = _gcs_mock()
    with patch("gcs.storage.Client", return_value=client):
        with patch("gcs.GCS_BUCKET", "YOUR_GCS_BUCKET"):
            import gcs
            url = gcs.upload_media("data:video/mp4;base64,AAAAI=", "video/mp4")
    assert url.endswith(".mp4")


def test_upload_passes_correct_content_type():
    client, blob = _gcs_mock()
    with patch("gcs.storage.Client", return_value=client):
        with patch("gcs.GCS_BUCKET", "YOUR_GCS_BUCKET"):
            import gcs
            gcs.upload_media("data:image/jpeg;base64,/9j/4AAQ==", "image/jpeg")
    _, kwargs = blob.upload_from_string.call_args
    assert kwargs["content_type"] == "image/jpeg"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_gcs.py -v
```

- [ ] **Step 3: Implement gcs.py**

```python
# agents/gcs.py
import base64
import uuid
from google.cloud import storage
from config import GCS_BUCKET


def upload_media(data_uri: str, content_type: str) -> str:
    """Upload base64 data URI to GCS. Returns public HTTPS URL."""
    _, encoded = data_uri.split(",", 1)
    data = base64.b64decode(encoded)

    ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
    blob_name = f"{uuid.uuid4()}.{ext}"

    client = storage.Client()
    blob = client.bucket(GCS_BUCKET).blob(blob_name)
    blob.upload_from_string(data, content_type=content_type)

    return f"https://storage.googleapis.com/{GCS_BUCKET}/{blob_name}"
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_gcs.py -v
```

Expected:
```
test_gcs.py::test_upload_image_returns_public_https_url PASSED
test_gcs.py::test_upload_video_returns_mp4_url PASSED
test_gcs.py::test_upload_passes_correct_content_type PASSED
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/gcs.py agents/tests/test_gcs.py
git commit -m "feat(agents): GCS upload helper returning public URL"
```

---

## Task 4: MedicationAgent

**Files:**
- Create: `agents/agents/__init__.py`
- Create: `agents/agents/medication.py`
- Create: `agents/tests/test_medication.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_medication.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini, firestore_empty):
    db, _ = firestore_empty
    with patch("memory.db", db):
        from agents.medication import run
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

    with patch("memory.db", db):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            from agents import medication
            import importlib; importlib.reload(medication)
            await medication.run("demo_user", "When do I take aspirin?")

    assert "Aspirin" in captured[0]


@pytest.mark.asyncio
async def test_run_writes_memory_after_response(mock_gemini, firestore_empty):
    db, doc_ref = firestore_empty
    with patch("memory.db", db):
        from agents.medication import run
        await run("demo_user", "I just took my aspirin")
    doc_ref.set.assert_called_once()
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_medication.py -v
```

- [ ] **Step 3: Create agents/__init__.py**

```python
# agents/agents/__init__.py
```

- [ ] **Step 4: Implement agents/medication.py**

```python
# agents/agents/medication.py
import json
from datetime import datetime, timezone

from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_memory, update_memory
from models import AgentResponse

_SYSTEM_PROMPT = """You are a warm, helpful medication assistant for elderly users.
Answer questions about medication schedules, dosage, and reminders.
Use simple language and short sentences. Be caring and patient.
If the user says they took a medication, acknowledge it warmly."""

_agent = LlmAgent(
    name="medication",
    model="gemini-2.0-flash",
    description="Handles questions about medications, dosage schedules, and reminders.",
    instruction=_SYSTEM_PROMPT,
)

_model = GenerativeModel(model_name=_agent.model, system_instruction=_SYSTEM_PROMPT)


async def run(user_id: str, message: str) -> AgentResponse:
    mem = await get_memory(user_id, "medication")

    context = f"User medication history:\n{json.dumps(mem, indent=2)}\n\n" if mem else ""
    response = await _model.generate_content_async(f"{context}User: {message}")

    await update_memory(user_id, "medication", {
        **mem,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="medication", media=None)
```

- [ ] **Step 5: Run — expect PASS**

```bash
pytest tests/test_medication.py -v
```

Expected:
```
test_medication.py::test_run_returns_agent_response PASSED
test_medication.py::test_run_injects_memory_into_prompt PASSED
test_medication.py::test_run_writes_memory_after_response PASSED
3 passed
```

- [ ] **Step 6: Commit**

```bash
git add agents/agents/ agents/tests/test_medication.py
git commit -m "feat(agents): MedicationAgent with Firestore memory"
```

---

## Task 5: ExerciseAgent

**Files:**
- Create: `agents/agents/exercise.py`
- Create: `agents/tests/test_exercise.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_exercise.py
import pytest
from unittest.mock import patch, MagicMock
from models import AgentResponse


@pytest.fixture
def firestore_exercise():
    from tests.conftest import _make_firestore_mock
    return _make_firestore_mock(data={
        "last_session": "2026-03-27",
        "streak_days": 3,
        "history": [{"date": "2026-03-27", "type": "stretching", "duration_min": 10}],
    })


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini, firestore_empty):
    db, _ = firestore_empty
    with patch("memory.db", db):
        from agents.exercise import run
        result = await run("demo_user", "Let's stretch")
    assert isinstance(result, AgentResponse)
    assert result.agent == "exercise"
    assert result.media is None


@pytest.mark.asyncio
async def test_run_injects_history_into_prompt(firestore_exercise):
    db, _ = firestore_exercise
    captured = []

    async def fake_generate(prompt, **_):
        captured.append(str(prompt))
        m = MagicMock()
        m.text = "Great job!"
        return m

    with patch("memory.db", db):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            from agents import exercise
            import importlib; importlib.reload(exercise)
            await exercise.run("demo_user", "I did stretching today")

    assert "streak" in captured[0] or "2026-03-27" in captured[0]


@pytest.mark.asyncio
async def test_run_updates_streak(mock_gemini, firestore_empty):
    db, doc_ref = firestore_empty
    with patch("memory.db", db):
        from agents.exercise import run
        await run("demo_user", "I finished my exercises")
    doc_ref.set.assert_called_once()
    saved = doc_ref.set.call_args[0][0]
    assert "last_session" in saved
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_exercise.py -v
```

- [ ] **Step 3: Implement agents/exercise.py**

```python
# agents/agents/exercise.py
import json
from datetime import date, datetime, timezone

from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_memory, update_memory
from models import AgentResponse

_SYSTEM_PROMPT = """You are a friendly exercise and stretching coach for elderly users.
Encourage gentle movement. Celebrate small wins warmly.
Keep sentences short. Safety first — never push too hard.
Handle both exercise and stretching topics."""

_agent = LlmAgent(
    name="exercise",
    model="gemini-2.0-flash",
    description="Handles exercise, stretching, and physical activity questions.",
    instruction=_SYSTEM_PROMPT,
)

_model = GenerativeModel(model_name=_agent.model, system_instruction=_SYSTEM_PROMPT)


async def run(user_id: str, message: str) -> AgentResponse:
    mem = await get_memory(user_id, "exercise")

    context = f"User exercise history:\n{json.dumps(mem, indent=2)}\n\n" if mem else ""
    response = await _model.generate_content_async(f"{context}User: {message}")

    today = date.today().isoformat()
    streak = mem.get("streak_days", 0)
    if mem.get("last_session") != today:
        streak += 1

    await update_memory(user_id, "exercise", {
        **mem,
        "last_session": today,
        "streak_days": streak,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="exercise", media=None)
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_exercise.py -v
```

Expected:
```
test_exercise.py::test_run_returns_agent_response PASSED
test_exercise.py::test_run_injects_history_into_prompt PASSED
test_exercise.py::test_run_updates_streak PASSED
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/agents/exercise.py agents/tests/test_exercise.py
git commit -m "feat(agents): ExerciseAgent with streak tracking memory"
```

---

## Task 6: CheckupAgent

**Files:**
- Create: `agents/agents/checkup.py`
- Create: `agents/tests/test_checkup.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_checkup.py
import pytest
from unittest.mock import patch
from models import AgentResponse


@pytest.mark.asyncio
async def test_run_returns_agent_response(mock_gemini):
    from agents.checkup import run
    result = await run("demo_user", "When is my next checkup?")
    assert isinstance(result, AgentResponse)
    assert result.agent == "checkup"
    assert result.media is None
    assert result.response == "Test response from Gemini"


@pytest.mark.asyncio
async def test_run_never_touches_firestore(mock_gemini):
    with patch("memory.db") as mock_db:
        from agents.checkup import run
        await run("demo_user", "Do I have a checkup soon?")
    mock_db.collection.assert_not_called()
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_checkup.py -v
```

- [ ] **Step 3: Implement agents/checkup.py**

```python
# agents/agents/checkup.py
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from models import AgentResponse

_SYSTEM_PROMPT = """You are a caring assistant helping elderly users remember medical checkups.
Remind them gently about upcoming appointments.
Keep language simple, warm, and reassuring."""

_agent = LlmAgent(
    name="checkup",
    model="gemini-2.0-flash",
    description="Handles medical checkup reminders and appointment questions.",
    instruction=_SYSTEM_PROMPT,
)

_model = GenerativeModel(model_name=_agent.model, system_instruction=_SYSTEM_PROMPT)


async def run(user_id: str, message: str) -> AgentResponse:
    response = await _model.generate_content_async(f"User: {message}")
    return AgentResponse(response=response.text, agent="checkup", media=None)
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_checkup.py -v
```

Expected:
```
test_checkup.py::test_run_returns_agent_response PASSED
test_checkup.py::test_run_never_touches_firestore PASSED
2 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/agents/checkup.py agents/tests/test_checkup.py
git commit -m "feat(agents): stateless CheckupAgent"
```

---

## Task 7: PeopleAgent

**Files:**
- Create: `agents/agents/people.py`
- Create: `agents/tests/test_people.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_people.py
import pytest
from unittest.mock import patch, MagicMock
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
    with patch("memory.db", db):
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

    with patch("memory.db", db):
        with patch(
            "vertexai.generative_models.GenerativeModel.generate_content_async",
            side_effect=fake_generate,
        ):
            from agents import people
            import importlib; importlib.reload(people)
            await people.run("demo_user", "Who should I call?")

    assert "Ana" in captured[0]


@pytest.mark.asyncio
async def test_run_writes_memory(mock_gemini, firestore_empty):
    db, doc_ref = firestore_empty
    with patch("memory.db", db):
        from agents.people import run
        await run("demo_user", "I called my daughter")
    doc_ref.set.assert_called_once()
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_people.py -v
```

- [ ] **Step 3: Implement agents/people.py**

```python
# agents/agents/people.py
import json
from datetime import datetime, timezone

from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from memory import get_memory, update_memory
from models import AgentResponse

_SYSTEM_PROMPT = """You are a warm companion helping elderly users stay connected with family and friends.
Gently remind them who they haven't spoken to recently.
Be encouraging and warm, never guilt-tripping.
Use the contact history to give personalised nudges."""

_agent = LlmAgent(
    name="people",
    model="gemini-2.0-flash",
    description="Helps the user stay in touch with family and friends.",
    instruction=_SYSTEM_PROMPT,
)

_model = GenerativeModel(model_name=_agent.model, system_instruction=_SYSTEM_PROMPT)


async def run(user_id: str, message: str) -> AgentResponse:
    mem = await get_memory(user_id, "people")

    context = f"User contact history:\n{json.dumps(mem, indent=2)}\n\n" if mem else ""
    response = await _model.generate_content_async(f"{context}User: {message}")

    await update_memory(user_id, "people", {
        **mem,
        "last_interaction": datetime.now(timezone.utc).isoformat(),
    })

    return AgentResponse(response=response.text, agent="people", media=None)
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_people.py -v
```

Expected:
```
test_people.py::test_run_returns_agent_response PASSED
test_people.py::test_run_injects_contacts_into_prompt PASSED
test_people.py::test_run_writes_memory PASSED
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/agents/people.py agents/tests/test_people.py
git commit -m "feat(agents): PeopleAgent with contact history memory"
```

---

## Task 8: VisionAgent

**Files:**
- Create: `agents/agents/vision.py`
- Create: `agents/tests/test_vision.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_vision.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from models import AgentResponse


def _gemini_mock(text: str):
    m = MagicMock()
    m.text = text
    return m


@pytest.mark.asyncio
async def test_run_image_returns_response_and_media():
    gcs_url = "https://storage.googleapis.com/YOUR_GCS_BUCKET/x.jpg"
    with patch(
        "vertexai.generative_models.GenerativeModel.generate_content_async",
        new_callable=AsyncMock,
        return_value=_gemini_mock("This is Aspirin 100mg."),
    ):
        with patch("agents.vision.upload_media", return_value=gcs_url):
            from agents.vision import run_image
            result = await run_image("demo_user", "data:image/jpeg;base64,/9j/4AAQ==")

    assert isinstance(result, AgentResponse)
    assert result.agent == "vision"
    assert result.media is not None
    assert result.media.type == "image"
    assert result.media.url == gcs_url


@pytest.mark.asyncio
async def test_run_video_returns_response_and_media():
    gcs_url = "https://storage.googleapis.com/YOUR_GCS_BUCKET/x.mp4"
    with patch(
        "vertexai.generative_models.GenerativeModel.generate_content_async",
        new_callable=AsyncMock,
        return_value=_gemini_mock("You are exercising correctly."),
    ):
        with patch("agents.vision.upload_media", return_value=gcs_url):
            from agents.vision import run_video
            result = await run_video("demo_user", "data:video/mp4;base64,AAAAI=")

    assert result.media.type == "video"
    assert result.media.url == gcs_url


@pytest.mark.asyncio
async def test_run_image_uploads_to_gcs_before_returning():
    upload_calls = []

    def fake_upload(data_uri, content_type):
        upload_calls.append(content_type)
        return "https://storage.googleapis.com/YOUR_GCS_BUCKET/x.jpg"

    with patch(
        "vertexai.generative_models.GenerativeModel.generate_content_async",
        new_callable=AsyncMock,
        return_value=_gemini_mock("An image."),
    ):
        with patch("agents.vision.upload_media", side_effect=fake_upload):
            from agents import vision
            import importlib; importlib.reload(vision)
            await vision.run_image("demo_user", "data:image/jpeg;base64,/9j/4AAQ==")

    assert len(upload_calls) == 1
    assert "jpeg" in upload_calls[0]
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_vision.py -v
```

- [ ] **Step 3: Implement agents/vision.py**

```python
# agents/agents/vision.py
import base64

from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel, Part, Image

from gcs import upload_media
from models import AgentResponse, MediaItem

_SYSTEM_PROMPT = """Describe images and videos clearly for elderly users.
Use simple, calm language. Focus on health-relevant details."""

_agent = LlmAgent(
    name="vision",
    model="gemini-1.5-pro",
    description="Analyses images and videos for elderly users.",
    instruction=_SYSTEM_PROMPT,
)

_model = GenerativeModel(model_name=_agent.model, system_instruction=_SYSTEM_PROMPT)


def _decode(data_uri: str) -> tuple[bytes, str]:
    header, encoded = data_uri.split(",", 1)
    mime = header.split(":")[1].split(";")[0]
    return base64.b64decode(encoded), mime


async def run_image(user_id: str, image_base64: str) -> AgentResponse:
    raw, mime = _decode(image_base64)
    gcs_url = upload_media(image_base64, mime)

    response = await _model.generate_content_async([
        Part.from_image(Image.from_bytes(raw)),
        "Describe this image for an elderly user in simple terms.",
    ])

    return AgentResponse(
        response=response.text,
        agent="vision",
        media=MediaItem(type="image", url=gcs_url),
    )


async def run_video(user_id: str, video_base64: str) -> AgentResponse:
    raw, mime = _decode(video_base64)
    gcs_url = upload_media(video_base64, mime)

    response = await _model.generate_content_async([
        Part.from_data(data=raw, mime_type=mime),
        "Describe what is happening in this video for an elderly user.",
    ])

    return AgentResponse(
        response=response.text,
        agent="vision",
        media=MediaItem(type="video", url=gcs_url),
    )
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_vision.py -v
```

Expected:
```
test_vision.py::test_run_image_returns_response_and_media PASSED
test_vision.py::test_run_video_returns_response_and_media PASSED
test_vision.py::test_run_image_uploads_to_gcs_before_returning PASSED
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/agents/vision.py agents/tests/test_vision.py
git commit -m "feat(agents): VisionAgent for image/video with GCS upload"
```

---

## Task 9: Router

**Files:**
- Create: `agents/router.py`
- Create: `agents/tests/test_router.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_router.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from models import AgentResponse


def _intent(text: str):
    m = MagicMock()
    m.text = text
    return m


@pytest.mark.asyncio
async def test_routes_medication(firestore_empty, mock_gemini):
    db, _ = firestore_empty
    intent_mock = AsyncMock(return_value=_intent("medication"))
    agent_mock = AsyncMock(return_value=AgentResponse(response="Take aspirin at 8am", agent="medication"))

    with patch("vertexai.generative_models.GenerativeModel.generate_content_async", intent_mock):
        with patch("router.medication.run", agent_mock):
            with patch("memory.db", db):
                from router import route
                result = await route("demo_user", "When do I take aspirin?")

    assert result.agent == "medication"
    agent_mock.assert_called_once_with("demo_user", "When do I take aspirin?")


@pytest.mark.asyncio
async def test_routes_stretching_to_exercise(firestore_empty):
    db, _ = firestore_empty
    intent_mock = AsyncMock(return_value=_intent("stretching"))
    agent_mock = AsyncMock(return_value=AgentResponse(response="Great stretch!", agent="exercise"))

    with patch("vertexai.generative_models.GenerativeModel.generate_content_async", intent_mock):
        with patch("router.exercise.run", agent_mock):
            from router import route
            result = await route("demo_user", "Time to stretch")

    assert result.agent == "exercise"


@pytest.mark.asyncio
async def test_routes_exercise(firestore_empty):
    db, _ = firestore_empty
    intent_mock = AsyncMock(return_value=_intent("exercise"))
    agent_mock = AsyncMock(return_value=AgentResponse(response="Let's go!", agent="exercise"))

    with patch("vertexai.generative_models.GenerativeModel.generate_content_async", intent_mock):
        with patch("router.exercise.run", agent_mock):
            from router import route
            await route("demo_user", "I want to exercise")

    agent_mock.assert_called_once()


@pytest.mark.asyncio
async def test_general_intent_returns_fallback():
    intent_mock = AsyncMock(return_value=_intent("general"))

    with patch("vertexai.generative_models.GenerativeModel.generate_content_async", intent_mock):
        from router import route
        result = await route("demo_user", "What is the weather?")

    assert result.agent == "general"
    assert "medication" in result.response.lower() or "exercise" in result.response.lower()


@pytest.mark.asyncio
async def test_unknown_intent_falls_back_to_general():
    intent_mock = AsyncMock(return_value=_intent("GARBAGE_XYZ"))

    with patch("vertexai.generative_models.GenerativeModel.generate_content_async", intent_mock):
        from router import route
        result = await route("demo_user", "blah blah")

    assert result.agent == "general"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_router.py -v
```

- [ ] **Step 3: Implement router.py**

```python
# agents/router.py
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from agents import checkup, exercise, medication, people
from models import AgentResponse

_SYSTEM_PROMPT = """Classify the user message into exactly one intent.
Reply with ONLY one word — no punctuation, no explanation.

Intents:
medication  → pills, doses, schedules, medicine, pharmacy
exercise    → physical activity, working out, gym, walking
stretching  → stretching, flexibility, yoga, physiotherapy
checkup     → doctor, appointment, medical test, health visit
people      → family, friends, calling someone, social contact
general     → anything else"""

_agent = LlmAgent(
    name="router",
    model="gemini-2.0-flash",
    description="Classifies user intent and routes to the correct specialist agent.",
    instruction=_SYSTEM_PROMPT,
)

_model = GenerativeModel(model_name=_agent.model, system_instruction=_SYSTEM_PROMPT)

_GENERAL_RESPONSE = (
    "I can help with your medications, exercise, checkups, "
    "or staying in touch with family. What would you like?"
)


async def route(user_id: str, message: str) -> AgentResponse:
    intent_resp = await _model.generate_content_async(f"Message: {message}")
    intent = intent_resp.text.strip().lower()

    if intent == "medication":
        return await medication.run(user_id, message)
    elif intent in ("exercise", "stretching"):
        return await exercise.run(user_id, message)
    elif intent == "checkup":
        return await checkup.run(user_id, message)
    elif intent == "people":
        return await people.run(user_id, message)
    else:
        return AgentResponse(response=_GENERAL_RESPONSE, agent="general", media=None)
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_router.py -v
```

Expected:
```
test_router.py::test_routes_medication PASSED
test_router.py::test_routes_stretching_to_exercise PASSED
test_router.py::test_routes_exercise PASSED
test_router.py::test_general_intent_returns_fallback PASSED
test_router.py::test_unknown_intent_falls_back_to_general PASSED
5 passed
```

- [ ] **Step 5: Commit**

```bash
git add agents/router.py agents/tests/test_router.py
git commit -m "feat(agents): router with Gemini intent classification and Python dispatch"
```

---

## Task 10: FastAPI App

**Files:**
- Create: `agents/main.py`
- Create: `agents/tests/test_main.py`

- [ ] **Step 1: Write failing tests**

```python
# agents/tests/test_main.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from models import AgentResponse, MediaItem


@pytest.fixture
async def client():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_calls_router_and_returns_response(client):
    mock_result = AgentResponse(response="Take aspirin at 8am.", agent="medication")
    with patch("main.route", AsyncMock(return_value=mock_result)):
        resp = await client.post("/chat", json={"user_id": "demo_user", "message": "When do I take aspirin?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "Take aspirin at 8am."
    assert data["agent"] == "medication"
    assert data["media"] is None


@pytest.mark.asyncio
async def test_vision_calls_run_image(client):
    mock_result = AgentResponse(
        response="This is Aspirin.",
        agent="vision",
        media=MediaItem(type="image", url="https://storage.googleapis.com/YOUR_GCS_BUCKET/x.jpg"),
    )
    with patch("main.vision.run_image", AsyncMock(return_value=mock_result)):
        resp = await client.post("/vision", json={"user_id": "demo_user", "image_base64": "data:image/jpeg;base64,abc"})
    assert resp.status_code == 200
    assert resp.json()["media"]["type"] == "image"


@pytest.mark.asyncio
async def test_video_calls_run_video(client):
    mock_result = AgentResponse(
        response="You are exercising correctly.",
        agent="vision",
        media=MediaItem(type="video", url="https://storage.googleapis.com/YOUR_GCS_BUCKET/x.mp4"),
    )
    with patch("main.vision.run_video", AsyncMock(return_value=mock_result)):
        resp = await client.post("/video", json={"user_id": "demo_user", "video_base64": "data:video/mp4;base64,abc"})
    assert resp.status_code == 200
    assert resp.json()["media"]["type"] == "video"


@pytest.mark.asyncio
async def test_unhandled_exception_returns_error_shape(client):
    with patch("main.route", AsyncMock(side_effect=Exception("Vertex AI unavailable"))):
        resp = await client.post("/chat", json={"user_id": "demo_user", "message": "Hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert "fallback_response" in data
    assert data["fallback_response"].startswith("Sorry")
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_main.py -v
```

- [ ] **Step 3: Implement main.py**

```python
# agents/main.py
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agents import vision
from models import AgentResponse, ChatRequest, ErrorResponse, VideoRequest, VisionRequest
from router import route

app = FastAPI(title="Oonook Agents")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=200,
        content=ErrorResponse(
            error="agent_error",
            message=str(exc),
            fallback_response="Sorry, I am having trouble. Please try again.",
        ).model_dump(),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=AgentResponse)
async def chat(req: ChatRequest):
    return await route(req.user_id, req.message)


@app.post("/vision", response_model=AgentResponse)
async def handle_vision(req: VisionRequest):
    return await vision.run_image(req.user_id, req.image_base64)


@app.post("/video", response_model=AgentResponse)
async def handle_video(req: VideoRequest):
    return await vision.run_video(req.user_id, req.video_base64)
```

- [ ] **Step 4: Run full test suite**

```bash
pytest -v
```

Expected: all 25 tests pass.

- [ ] **Step 5: Commit**

```bash
git add agents/main.py agents/tests/test_main.py
git commit -m "feat(agents): FastAPI app — /chat /vision /video /health with error handler"
```

---

## Task 11: Smoke Test Against Real GCP

- [ ] **Step 1: Set environment and start service**

```bash
cd agents
cp ../config/.env.example .env
# edit .env — fill in GOOGLE_CLOUD_PROJECT and GCS_BUCKET

export $(grep -v '^#' .env | xargs)
export GOOGLE_APPLICATION_CREDENTIALS=../config/sa.json
uvicorn main:app --reload --port 8000
```

Expected: `Application startup complete.`

- [ ] **Step 2: Health check**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 3: Chat — medication intent**

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo_user","message":"When do I take my aspirin?"}' | python3 -m json.tool
```

Expected shape: `{"response": "...", "agent": "medication", "media": null}`

- [ ] **Step 4: Chat — general fallback**

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo_user","message":"What is 2 plus 2?"}' | python3 -m json.tool
```

Expected: `"agent": "general"`

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat(agents): agents service complete — smoke tested against Vertex AI"
```
