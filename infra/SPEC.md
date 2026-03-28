# Infra Spec — Dev 4

## Overview
Local development environment using Docker Compose. All services run locally. Firestore uses real GCP — no emulator. Cloud deployment is out of scope for now.

## GCP Project
```
Project ID: woven-bonbon-485514-h5
Region:     europe-west1
```
Vertex AI (Gemini), GCS, and Firestore all connect to real GCP — even in local dev.

## Local Stack

```
docker-compose.yml
├── backend      (Spring Boot :8080)
└── agents       (Python FastAPI :8000)

frontend          (Expo — runs on host machine, not in Docker)
```

## docker-compose.yml
```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    environment:
      AGENTS_URL: http://agents:8000
      GOOGLE_CLOUD_PROJECT: woven-bonbon-485514-h5
    depends_on:
      - agents

  agents:
    build: ./agents
    ports:
      - "8000:8000"
    environment:
      GOOGLE_CLOUD_PROJECT: woven-bonbon-485514-h5
      GOOGLE_CLOUD_LOCATION: europe-west1
      GCS_BUCKET: oonook-media
      GOOGLE_APPLICATION_CREDENTIALS: /secrets/sa.json
    volumes:
      - ./config/sa.json:/secrets/sa.json:ro
```

## Dockerfiles

**backend/Dockerfile**
```dockerfile
FROM eclipse-temurin:21-jdk-alpine
WORKDIR /app
COPY target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
```
> Build the jar first: `cd backend && mvn package -DskipTests`

**agents/Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## GCP Resources

### Service Account
- Roles:
  - `roles/aiplatform.user` — Vertex AI / Gemini (agents)
  - `roles/storage.objectAdmin` — GCS media bucket (agents)
  - `roles/datastore.user` — Firestore read/write (agents + backend)
- Key file: download as JSON → place at `./config/sa.json` (gitignored)

### Cloud Storage Bucket
- Name: `oonook-media`
- Location: `europe-west1`
- Access: uniform, public read

```bash
gsutil mb -l europe-west1 gs://oonook-media
gsutil iam ch allUsers:objectViewer gs://oonook-media
```

### Firestore (real GCP)
Collections managed by the agents service:
```
users/              — user profile (nikola / Nikola Nikolic)
medications/        — medication list with schedules
contacts/           — family/friends; emergency_contact (bool) + telegram_chat_id
exercise/           — exercise streak and session history
checkups/           — upcoming medical appointments
reminders/          — AI-generated and manual reminders
news_preferences/   — liked/disliked news topics per user
app_config/         — telegram bot token (app_config/telegram → bot_token)
```

### Telegram Bot
- Bot: @Oonookbot
- Token stored in Firestore: `app_config/telegram` → `bot_token`
- Emergency contacts must message @Oonookbot first to activate their chat
- `telegram_chat_id` stored on the contact's Firestore document

## Config & Secrets
```
config/
├── .env          ← gitignored, copy from .env.example and fill in
├── .env.example  ← committed template
├── sa.json       ← gitignored, download from GCP Console
└── sa.json.example ← committed shape reference
```

## Local Dev Quickstart
```bash
# 1. Place GCP service account key at ./config/sa.json

# 2. Build Spring Boot jar
cd backend && mvn package -DskipTests && cd ..

# 3. Start backend + agents
docker compose up

# 4. Start frontend (separate terminal, on host)
cd frontend && npx expo start

# 5. (Optional) ADK web UI for testing agents
cd agents && adk web adk/
```

Services:
- Frontend (Expo): `exp://localhost:8081`
- Backend: `http://localhost:8080`
- Agents: `http://localhost:8000`

## Demo Data
Seed Firestore with data for user `nikola` (Nikola Nikolic):
```bash
cd agents && python3.11 seed.py
```
Generate AI reminders after seeding:
```bash
curl -X POST http://localhost:8000/reminders/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"nikola"}'
```

## Out of Scope (for now)
Cloud Run deployment, Artifact Registry, CI/CD, custom domain, staging environment.
