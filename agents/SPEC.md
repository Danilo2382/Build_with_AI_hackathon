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

### POST /reminders/generate
Triggered by the backend scheduler every 6 hours to regenerate AI-based reminders for a user.
```json
// Request
{ "user_id": "demo_user" }

// Response
{ "status": "ok", "count": 12 }
```
- Reads `medications`, `contacts`, and `checkups` collections from Firestore
- Calls Gemini to generate up to 12 actionable reminders
- Deletes all previous `auto_generated: true` reminders for the user, then writes new ones
- Manual reminders (`auto_generated: false`) are never touched

### POST /reminders/voice
Creates a single custom reminder from a voice/text message. Permanent — never overwritten by scheduled generation.
```json
// Request
{ "user_id": "demo_user", "message": "Remind me to drink water every morning" }

// Response
{ "status": "ok" }
```
- Parses the message into a structured reminder with `title`, `description`, and `time`
- Writes to `reminders` collection with `auto_generated: false`

### GET /health
```json
{ "status": "ok" }
```

## Multi-Agent Architecture (Google ADK)

```
POST /chat
    │
    ▼
router.py  (intent classification)
    │
    ▼
adk/root/agent.py  ← root_agent (ADK orchestrator, gemini-2.5-pro)
    │  delegates to sub-agents based on descriptions
    ├──► MedicationAgent   → reads medications collection
    ├──► ExerciseAgent     → reads/writes exercise collection
    ├──► CheckupAgent      → reads checkups collection
    ├──► PeopleAgent       → reads contacts collection
    └──► VisionAgent       → gemini-1.5-pro, image/video analysis

POST /reminders/generate
    │
    ▼
adk/reminders/agent.py  run()
    └──► reads medications + contacts + checkups → Gemini → writes reminders

POST /reminders/voice
    │
    ▼
adk/reminders/agent.py  run_voice()
    └──► parses voice message → writes single permanent reminder

adk web (dev UI)
    └──► scans adk/ subdirectories, picks up root_agent from each agent.py
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

## Firestore Schema

Flat root-level collections. All user-scoped documents include a `userId` field and are filtered with `.where("userId", "==", user_id)`.

```
users/           {user_id}                    — profile (name, age, language)
medications/     {med_id}    userId, name, dose, schedule, notes
contacts/        {con_id}    userId, name, relationship, phone, last_contact
exercise/        {user_id}                    — state doc (streak_days, limitations)
checkups/        {chk_id}    userId, doctor, specialty, date, location
reminders/       {rem_id}    userId, title, description, time, auto_generated (bool)
```

### reminders collection
```json
{
  "userId": "demo_user",
  "title": "Take Aspirin",
  "description": "100mg — take with water",
  "time": "08:00",
  "auto_generated": true
}
```
- `auto_generated: true` — created by `/reminders/generate`; deleted and regenerated each run
- `auto_generated: false` — created by `/reminders/voice`; permanent, never overwritten

## Memory Read/Write Pattern
On each agent call:
1. **Read** relevant collection(s) from Firestore for `user_id`
2. **Inject** relevant facts as additional context into the Gemini prompt
3. Call Gemini, get response
4. **Write** any updates back (e.g. exercise streak increment)

## File Structure
```
agents/
├── main.py                  # FastAPI app + endpoint definitions
├── router.py                # Intent classification + dispatch to domain agents
├── memory.py                # Firestore helpers (get/write per collection)
├── models.py                # Pydantic request/response schemas
├── config.py                # env var loading + vertexai.init()
├── seed.py                  # One-time Firestore seeding script (demo data)
├── adk/
│   ├── root/agent.py        # ADK root orchestrator (adk web entry point)
│   ├── medication/agent.py  # MedicationAgent — reads medications collection
│   ├── exercise/agent.py    # ExerciseAgent — reads/writes exercise collection
│   ├── checkup/agent.py     # CheckupAgent — reads checkups collection
│   ├── people/agent.py      # PeopleAgent — reads contacts collection
│   ├── vision/agent.py      # VisionAgent — image + video via Gemini Pro
│   └── reminders/agent.py   # run() for AI generation, run_voice() for custom
├── gcs.py                   # GCS upload helper
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
- `roles/datastore.user` (Firestore)
- `roles/storage.objectAdmin` (GCS media bucket)
