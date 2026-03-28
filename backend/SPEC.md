# Backend Spec — Dev 2

## Overview
Thin Spring Boot proxy. Receives requests from the frontend, forwards AI calls to the Python agents service, and handles reminders CRUD against Firestore. No AI logic lives here.

## Stack
- Spring Boot 3
- Java 21
- Maven
- Google Cloud Firestore SDK
- No Spring Security

## Environment Variables
```
AGENTS_URL=http://agents:8000
FIRESTORE_EMULATOR_HOST=firestore:9090
GOOGLE_CLOUD_PROJECT=pratilac-demo
```

## Base URLs
- Local: `http://localhost:8080`
- Prod: Cloud Run (set by infra dev)

## Endpoints

### POST /chat
Forwards to agents service, returns response as-is.
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

### GET /reminders?user_id=demo_user
Reads from Firestore collection `reminders`, filters by `user_id`.
```json
{
  "reminders": [
    { "id": "rem_001", "type": "medication", "icon": "💊", "label": "Aspirin", "time": "14:00", "status": "pending" },
    { "id": "rem_002", "type": "stretching", "icon": "🧘", "label": "Stretching", "time": "16:00", "status": "pending" },
    { "id": "rem_003", "type": "people", "icon": "👥", "label": "Call Ana", "time": null, "days_since_contact": 14, "status": "overdue" }
  ]
}
```

### POST /reminders/confirm
Updates reminder status to `confirmed` in Firestore.
```json
// Request
{ "user_id": "demo_user", "reminder_id": "rem_001" }

// Response
{ "confirmed": true, "response": "Great, I marked your Aspirin as taken!" }
```

### GET /health
```json
{ "status": "ok", "agents_reachable": true }
```
Calls `GET ${AGENTS_URL}/health`. If agents returns HTTP 200 (any body), set `agents_reachable: true`. If connection fails or non-200, set `agents_reachable: false`. Never return 5xx — always return 200 with the boolean flag.

## Internal Forwarding Rules
Spring never processes AI. Forward bodies unchanged:
```
POST /chat   → POST ${AGENTS_URL}/chat
POST /vision → POST ${AGENTS_URL}/vision
POST /video  → POST ${AGENTS_URL}/video
```
Pass through response body and status code as-is.

## Error Response Shape
All errors (including forwarding failures) return this shape so the frontend can always speak a fallback:
```json
{
  "error": "agents_unavailable",
  "message": "Could not reach AI service.",
  "fallback_response": "Sorry, I am having trouble. Please try again."
}
```

## File Structure
```
backend/src/main/java/com/pratilac/
├── controllers/
│   ├── ChatController.java
│   ├── VisionController.java
│   ├── RemindersController.java
│   └── HealthController.java
├── services/
│   ├── AgentsService.java         # HTTP forwarding to agents
│   └── RemindersService.java      # Firestore CRUD
├── models/
│   ├── ChatRequest.java
│   ├── ChatResponse.java
│   ├── VisionRequest.java
│   ├── VideoRequest.java
│   ├── Reminder.java
│   └── ErrorResponse.java
├── config/
│   └── RestClientConfig.java      # WebClient or RestClient bean
└── PratilacApplication.java
```

## Firestore Data Model
Collection: `reminders`
Document fields: `id`, `user_id`, `type`, `icon`, `label`, `time` (nullable), `status`, `days_since_contact` (nullable)

## Seed Data
On startup, if collection is empty, seed with the 3 demo reminders shown above.

## Out of Scope
Auth, JWT, user management, multiple real users.
