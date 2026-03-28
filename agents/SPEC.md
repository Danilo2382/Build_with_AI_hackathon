# Agents Spec — Dev 3

## Overview
Python FastAPI service at port 8000. Handles all AI logic using **Google ADK** (Agent Development Kit) with **Vertex AI Gemini** models. Implements a multi-agent architecture: a router agent dispatches to specialized domain agents. Some agents have **long-term memory backed by Firestore**.

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- `google-adk` — Google Agent Development Kit
- `google-cloud-aiplatform` — Vertex AI SDK
- `google-cloud-firestore` — long-term agent memory + session storage
- `google-cloud-storage` — media upload for vision/video responses
- `vertexai` — Gemini model access

## Environment Variables
```
GOOGLE_CLOUD_PROJECT=oonook-demo
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET=oonook-media
FIRESTORE_EMULATOR_HOST=firestore:9090    # local only; unset in prod
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json
```

## Models
| Use case | Model |
|---|---|
| Chat / text agents | `gemini-1.5-flash` |
| Vision / video | `gemini-1.5-pro` |

## Endpoints

### POST /chat
```json
// Request
{ "user_id": "demo_user", "message": "When do I take my aspirin?" }

// Response
{ "response": "You take Aspirin at 8am and 8pm.", "agent": "medication", "media": null }
```

### POST /vision
```json
// Request
{ "user_id": "demo_user", "image_base64": "data:image/jpeg;base64,..." }

// Response
{ "response": "This is Aspirin 100mg.", "agent": "vision", "media": { "type": "image", "url": "https://storage.googleapis.com/..." } }
```

### POST /video
```json
// Request
{ "user_id": "demo_user", "video_base64": "data:video/mp4;base64,..." }

// Response
{ "response": "I can see you doing the exercise correctly.", "agent": "vision", "media": { "type": "video", "url": "https://storage.googleapis.com/..." } }
```

### GET /health
```json
{ "status": "ok" }
```

## Multi-Agent Architecture (Google ADK)

```
POST /chat
    │
    ▼
RouterAgent  (gemini-1.5-flash, stateless)
    │  classifies intent from message
    ├──► MedicationAgent   → "medication"  [has memory]
    ├──► ExerciseAgent     → "exercise" | "stretching"  [has memory]
    ├──► CheckupAgent      → "checkup"  [stateless]
    └──► PeopleAgent       → "people"   [has memory]

POST /vision / POST /video
    │
    ▼
VisionAgent  (gemini-1.5-pro, stateless)
    └──► uploads media to GCS, returns URL
```

## Agent Definitions

### RouterAgent (stateless)
- Model: `gemini-1.5-flash`
- Classifies user message into: `medication`, `exercise`, `stretching`, `checkup`, `people`, `general`
- Dispatches to matching sub-agent and returns its response with `agent` field set
- `general` intent → handled by a built-in fallback response: a warm, friendly reply that invites the user to ask about medications, exercise, checkups, or people. No sub-agent invoked.

### MedicationAgent (long-term memory)
- Model: `gemini-1.5-flash`
- System prompt: helpful medication assistant for elderly users; answers questions about schedules, dosage, and reminders
- Tone: warm, simple language, short sentences
- **Memory:** reads/writes `agent_memory/{user_id}/medication` in Firestore
  - Stores: medication list, schedule, last confirmation timestamps
  - Injects relevant memory into context on each call
- Returns `media: null`

### ExerciseAgent (long-term memory)
- Model: `gemini-1.5-flash`
- System prompt: friendly exercise and stretching coach; encourages gentle movement appropriate for elderly users
- Handles both `exercise` and `stretching` intents
- **Memory:** reads/writes `agent_memory/{user_id}/exercise` in Firestore
  - Stores: exercise history, last session date, streak count
  - Injects history summary into context on each call
- Returns `media: null`

### CheckupAgent (stateless)
- Model: `gemini-1.5-flash`
- System prompt: reminds user about upcoming medical checkups and appointments
- Returns `media: null`

### PeopleAgent (long-term memory)
- Model: `gemini-1.5-flash`
- System prompt: helps elderly user stay connected with family and friends; gentle, warm social nudges
- **Memory:** reads/writes `agent_memory/{user_id}/people` in Firestore
  - Stores: contact list, last_contact dates, relationship notes
  - Injects contact history into context on each call
- Returns `media: null`

### VisionAgent (stateless)
- Model: `gemini-1.5-pro`
- Accepts base64-encoded image or video
- Describes what it sees in simple language for an elderly user
- Uploads media to GCS bucket (`oonook-media`), returns public HTTPS URL
- Bucket is configured for public read — no signed URLs needed
- Returns `media: { type: "image"|"video", url: "https://storage.googleapis.com/oonook-media/..." }`

## Long-Term Memory — Firestore Schema

Each memory document lives at the full Firestore path:
```
agent_memory (collection)
  └── {user_id} (document)
        └── {domain} (subcollection: "medication" | "exercise" | "people")
              └── data (document)  ← actual memory fields stored here
```
Shorthand used elsewhere in this spec: `agent_memory/{user_id}/{domain}/data`

### medication document
```json
{
  "medications": [
    { "name": "Aspirin", "dose": "100mg", "schedule": ["08:00", "20:00"] }
  ],
  "last_confirmed": { "Aspirin": "2026-03-28T08:05:00Z" },
  "notes": "Take with food"
}
```

### exercise document
```json
{
  "last_session": "2026-03-27",
  "streak_days": 3,
  "history": [
    { "date": "2026-03-27", "type": "stretching", "duration_min": 10 }
  ]
}
```

### people document
```json
{
  "contacts": [
    { "name": "Ana", "relationship": "daughter", "last_contact": "2026-03-14", "days_since": 14 }
  ]
}
```

## Memory Read/Write Pattern
On each agent call:
1. **Read** memory doc from Firestore for `user_id`
2. **Inject** relevant facts as additional context into the Gemini prompt
3. Call Gemini, get response
4. **Write** any updates back to the memory doc (e.g. new exercise session, confirmed medication)

```python
async def get_memory(user_id: str, domain: str) -> dict:
    doc = db.collection("agent_memory").document(user_id).collection(domain).document("data")
    snap = await doc.get()
    return snap.to_dict() or {}

async def update_memory(user_id: str, domain: str, updates: dict):
    doc = db.collection("agent_memory").document(user_id).collection(domain).document("data")
    await doc.set(updates, merge=True)
```

## File Structure
```
agents/
├── main.py                  # FastAPI app + endpoint definitions
├── router.py                # RouterAgent — intent classification + dispatch
├── agents/
│   ├── medication.py        # MedicationAgent + memory
│   ├── exercise.py          # ExerciseAgent + memory
│   ├── checkup.py           # CheckupAgent (stateless)
│   ├── people.py            # PeopleAgent + memory
│   └── vision.py            # VisionAgent (image + video)
├── memory.py                # Firestore memory helpers (get/update)
├── gcs.py                   # GCS upload helper
├── models.py                # Pydantic request/response schemas
├── config.py                # env var loading
└── requirements.txt
```

## Response Schema (Pydantic)
```python
class MediaItem(BaseModel):
    type: str  # "image" | "video"
    url: str

class AgentResponse(BaseModel):
    response: str
    agent: str
    media: Optional[MediaItem] = None
```

## Error Handling
All unhandled exceptions return HTTP 200 with:
```json
{
  "error": "agent_error",
  "message": "<exception message>",
  "fallback_response": "Sorry, I am having trouble. Please try again."
}
```
Frontend always speaks `fallback_response` on error shape.

## Local Dev
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Requires `GOOGLE_APPLICATION_CREDENTIALS` pointing to a service account with:
- `roles/aiplatform.user` (Vertex AI)
- `roles/datastore.user` (Firestore — or use emulator locally)
- `roles/storage.objectAdmin` (GCS media bucket)
