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
GOOGLE_CLOUD_PROJECT=woven-bonbon-485514-h5
```

## Base URLs
- Local: `http://localhost:8080`
- Prod: Cloud Run (set by infra dev)

## Endpoints

### POST /chat
Forwards to agents service, returns response as-is.
```json
// Request
{ "user_id": "nikola", "audio_base64": "<base64 encoded m4a audio>" }

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

### GET /reminders?user_id=nikola
Reads from Firestore `reminders` collection, filters by `userId`.
```json
{
  "reminders": [
    { "id": "rem_001", "type": "medication", "icon": "💊", "label": "Take Aspirin", "time": "08:00", "status": "pending" },
    { "id": "rem_002", "type": "exercise",   "icon": "🏃", "label": "Morning stretches", "time": "09:00", "status": "pending" },
    { "id": "rem_003", "type": "people",     "icon": "📞", "label": "Call Ana", "time": null, "days_since_contact": 14, "status": "overdue" }
  ]
}
```

### POST /reminders/confirm
Updates reminder status to `confirmed` in Firestore.
```json
// Request
{ "user_id": "nikola", "reminder_id": "rem_001" }

// Response
{ "confirmed": true, "response": "Great, I marked your Aspirin as taken!" }
```

### GET /health
```json
{ "status": "ok", "agents_reachable": true }
```
Calls `GET ${AGENTS_URL}/health`. If agents returns HTTP 200, set `agents_reachable: true`. Never return 5xx — always return 200 with the boolean flag.

## Scheduled Jobs

### Reminder Generation — every 6 hours
`RemindersScheduler.java` calls `POST ${AGENTS_URL}/reminders/generate` with `user_id: "nikola"`.
- Agents service reads medications, contacts, checkups from Firestore
- Generates up to 12 AI reminders, replaces all `auto_generated: true` reminders
- Manual reminders (`auto_generated: false`) are never touched

```java
@Scheduled(cron = "0 0 */6 * * *")
public void generateReminders() { ... }
```
Requires `@EnableScheduling` on `OonookApplication`.

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
backend/src/main/java/com/pmfns/oonook/
├── controllers/
│   ├── ChatController.java
│   ├── VisionController.java
│   ├── RemindersController.java
│   └── HealthController.java
├── services/
│   ├── AgentsService.java         # HTTP forwarding to agents + generateReminders()
│   ├── RemindersService.java      # Firestore CRUD
│   └── RemindersScheduler.java    # @Scheduled every 6 hours
├── models/
│   ├── ChatRequest.java
│   ├── ChatResponse.java
│   ├── VisionRequest.java
│   ├── VideoRequest.java
│   ├── Reminder.java
│   └── ErrorResponse.java
├── config/
│   └── RestClientConfig.java
└── OonookApplication.java         # @EnableScheduling
```

## Firestore Data Model
Uses flat root-level collections (shared with agents service):
```
reminders/    userId, title, description, time, auto_generated, type, icon, label, status
```
All other collections (medications, contacts, exercise, checkups, users, news_preferences, app_config) are managed exclusively by the agents service.

## Out of Scope
Auth, JWT, user management, multiple real users.
