# Agents Spec — Dev 3

## Overview
Python FastAPI service at port 8000. Handles all AI logic using **Google ADK** (Agent Development Kit) with **Vertex AI Gemini** models. Implements a multi-agent architecture: a root orchestrator delegates to specialised domain agents. All agents read from **Firestore** (flat collections). Emergency alerts are sent via **Telegram Bot API**.

## Stack
- Python 3.11+
- FastAPI + Uvicorn
- `google-adk` — Google Agent Development Kit
- `google-cloud-aiplatform` — Vertex AI SDK
- `google-cloud-firestore` — agent memory + session storage
- `google-cloud-storage` — media upload for vision/video responses
- `vertexai` — Gemini model access
- `httpx` — async HTTP (Telegram, weather, news RSS)

## Environment Variables
```
GOOGLE_CLOUD_PROJECT=woven-bonbon-485514-h5
GOOGLE_CLOUD_LOCATION=europe-west1
GCS_BUCKET=oonook-media
GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json
```

## Models
| Use case | Model |
|---|---|
| Router + text agents | `gemini-1.5-flash` |
| Root orchestrator | `gemini-1.5-pro` |
| Vision / video | `gemini-1.5-pro` |

## Endpoints

### POST /chat
```json
// Request
{ "user_id": "nikola", "message": "When do I take my aspirin?" }

// Response
{ "response": "You take Aspirin at 8am and 8pm.", "agent": "medication", "media": null }
```

### POST /vision
```json
// Request
{ "user_id": "nikola", "image_base64": "data:image/jpeg;base64,..." }

// Response
{ "response": "This is Aspirin 100mg.", "agent": "vision", "media": { "type": "image", "url": "https://storage.googleapis.com/..." } }
```

### POST /video
```json
// Request
{ "user_id": "nikola", "video_base64": "data:video/mp4;base64,..." }

// Response
{ "response": "I can see you doing the exercise correctly.", "agent": "vision", "media": { "type": "video", "url": "https://storage.googleapis.com/..." } }
```

### POST /reminders/generate
Triggered by the backend scheduler every 6 hours to regenerate AI-based reminders for a user.
```json
// Request
{ "user_id": "nikola" }

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
{ "user_id": "nikola", "message": "Remind me to drink water every morning" }

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
adk/root/agent.py  ← root_agent (ADK orchestrator, gemini-1.5-pro)
    │  5 own tools + delegates to sub-agents
    ├── tools: get_user_profile, get_todays_reminders, get_current_datetime,
    │          get_health_summary, call_for_help (→ Telegram)
    │
    ├──► MedicationAgent   → get_my_medications()
    ├──► ExerciseAgent     → get_my_exercise_profile(), record_exercise_session()
    ├──► CheckupAgent      → get_my_checkups()
    ├──► PeopleAgent       → get_my_contacts()
    ├──► VisionAgent       → gemini-1.5-pro, image/video analysis
    └──► NewsAgent         → get_weather(), get_news_headlines(),
                             get_news_preferences(), update_news_preference()

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

### RootAgent (orchestrator)
- Model: `gemini-1.5-pro`
- Delegates to all sub-agents; handles general questions directly with own tools
- **Tools:**
  - `get_user_profile()` — user name, age, language from `users` collection
  - `get_todays_reminders()` — all reminders from `reminders` collection
  - `get_current_datetime()` — current date, time, day of week
  - `get_health_summary()` — combined medications + checkups + reminder count
  - `call_for_help(trigger_message)` — sends emergency Telegram alert immediately
- **Emergency detection:** voice-aware; triggers on any distress signal — "help", "fell", "can't breathe", "chest pain", "scared", etc. False positives are preferred over misses.

### MedicationAgent
- Model: `gemini-1.5-flash`
- Answers questions about medication schedules, dosage, reminders
- **Tool:** `get_my_medications()` — reads `medications` collection for `nikola`

### ExerciseAgent
- Model: `gemini-1.5-flash`
- Friendly exercise and stretching coach; tracks streak
- **Tools:**
  - `get_my_exercise_profile()` — reads `exercise` collection
  - `record_exercise_session()` — increments streak, writes `last_session`

### CheckupAgent
- Model: `gemini-1.5-flash`
- Manages medical appointment reminders
- **Tool:** `get_my_checkups()` — reads `checkups` collection

### PeopleAgent
- Model: `gemini-1.5-flash`
- Helps user stay connected with family and friends
- **Tool:** `get_my_contacts()` — reads `contacts` collection

### VisionAgent
- Model: `gemini-1.5-pro`
- Accepts base64-encoded image or video
- Uploads media to GCS bucket (`oonook-media`), returns public HTTPS URL
- Returns `media: { type: "image"|"video", url: "https://storage.googleapis.com/oonook-media/..." }`

### NewsAgent
- Model: `gemini-1.5-flash`
- Provides weather and personalised news headlines
- **Tools:**
  - `get_weather()` — Open-Meteo API, Belgrade, no API key required
  - `get_news_headlines()` — BBC News RSS, top 8 stories
  - `get_news_preferences()` — reads `news_preferences` collection
  - `update_news_preference(topic, liked)` — writes liked/disliked topics to Firestore
- **Long-term memory:** reads preferences before showing news, prioritises liked topics, skips disliked ones, updates preferences based on user reactions

## Emergency Tool — Telegram

When `call_for_help` is triggered:
1. Fetches user profile (name) from `users/nikola`
2. Fetches all contacts with `emergency_contact: true`
3. Calls Gemini to generate one-sentence assessment of the distress
4. Sends to each contact's `telegram_chat_id` via Telegram Bot API:
```
🚨 Nikola Nikolic might need help, reach out immediately.

💬 They said: "help I fell"

🤖 Nikola may have fallen and be unable to get up; call them immediately.

🕐 28 March 2026, 14:32
```
- Bot: @Oonookbot — token stored in Firestore `app_config/telegram`
- Contacts without a `telegram_chat_id` are skipped

## Firestore Schema

Flat root-level collections. All user-scoped documents include a `userId` field and are filtered with `.where("userId", "==", user_id)`.

```
users/              {user_id}          — profile (name, age, language)
medications/        {med_id}           userId, name, dose, schedule, notes
contacts/           {con_id}           userId, name, relationship, phone, last_contact,
                                       emergency_contact (bool), telegram_chat_id
exercise/           {user_id}          — state doc (streak_days, last_session, limitations)
checkups/           {chk_id}           userId, doctor, specialty, date, location
reminders/          {rem_id}           userId, title, description, time, auto_generated (bool)
news_preferences/   {user_id}          — liked_topics[], disliked_topics[]
app_config/         telegram           — bot_token (Telegram Bot API token)
```

### reminders collection
```json
{
  "userId": "nikola",
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
1. **Read** relevant collection(s) from Firestore via tool call
2. **Inject** facts as context into the Gemini prompt
3. Call Gemini, get response
4. **Write** any updates back (e.g. exercise streak, news preferences)

## File Structure
```
agents/
├── main.py                  # FastAPI app + endpoint definitions
├── router.py                # Intent classification + dispatch to domain agents
├── memory.py                # Firestore helpers (get/write per collection)
├── telegram.py              # Telegram Bot API helper (loads token from Firestore)
├── models.py                # Pydantic request/response schemas
├── config.py                # env var loading + vertexai.init()
├── seed.py                  # One-time Firestore seeding script (demo data for nikola)
├── adk/
│   ├── root/agent.py        # ADK root orchestrator + 5 tools incl. call_for_help
│   ├── medication/agent.py  # MedicationAgent — get_my_medications tool
│   ├── exercise/agent.py    # ExerciseAgent — exercise profile + streak tools
│   ├── checkup/agent.py     # CheckupAgent — get_my_checkups tool
│   ├── people/agent.py      # PeopleAgent — get_my_contacts tool
│   ├── vision/agent.py      # VisionAgent — image + video via Gemini Pro
│   ├── news/agent.py        # NewsAgent — weather + news + preferences tools
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

# ADK web UI (test agents directly)
adk web adk/
```
Requires `GOOGLE_APPLICATION_CREDENTIALS` pointing to a service account with:
- `roles/aiplatform.user` (Vertex AI)
- `roles/datastore.user` (Firestore)
- `roles/storage.objectAdmin` (GCS media bucket)
