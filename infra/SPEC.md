# Infra Spec — Dev 4

## Overview
Local development environment using Docker Compose + Firestore emulator. All services run locally. Cloud deployment is out of scope for now.

## GCP Project (for Vertex AI + GCS — used even locally)
```
Project ID: pratilac-demo
Region:     us-central1
```
Even in local dev, Vertex AI (Gemini) and GCS calls go to real GCP. Only Firestore is emulated locally.

## Local Stack

```
docker-compose.yml
├── backend      (Spring Boot :8080)
├── agents       (Python FastAPI :8000)
└── firestore    (Firestore emulator :9090 + UI :4000)

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
      FIRESTORE_EMULATOR_HOST: firestore:9090
      GOOGLE_CLOUD_PROJECT: pratilac-demo
    depends_on:
      - agents
      - firestore

  agents:
    build: ./agents
    ports:
      - "8000:8000"
    environment:
      GOOGLE_CLOUD_PROJECT: pratilac-demo
      GOOGLE_CLOUD_LOCATION: us-central1
      GCS_BUCKET: pratilac-media
      FIRESTORE_EMULATOR_HOST: firestore:9090
      GOOGLE_APPLICATION_CREDENTIALS: /secrets/sa.json
    volumes:
      - ./secrets/sa.json:/secrets/sa.json:ro
    depends_on:
      - firestore

  firestore:
    image: gcr.io/google.com/cloudsdktool/google-cloud-cli:emulators
    command: >
      gcloud emulators firestore start
      --host-port=0.0.0.0:9090
      --project=pratilac-demo
    ports:
      - "9090:9090"
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

## GCP Resources Needed (even for local dev)

### Service Account
- Name: `pratilac-sa@pratilac-demo.iam.gserviceaccount.com`
- Roles:
  - `roles/aiplatform.user` — Vertex AI / Gemini calls (agents)
  - `roles/storage.objectAdmin` — GCS media bucket (agents)
  - `roles/datastore.user` — Firestore read/write (agents: agent_memory; backend: reminders)
- Key file: download as JSON → place at `./secrets/sa.json` (gitignored)

### Cloud Storage Bucket
- Name: `pratilac-media`
- Location: `us-central1`
- Access: uniform, public read (for media URLs served to frontend)

Create once:
```bash
gsutil mb -l us-central1 gs://pratilac-media
gsutil iam ch allUsers:objectViewer gs://pratilac-media
```

### Firestore
- Emulated locally via Docker (no real Firestore needed for dev)
- Collections used:
  - `reminders` — managed by backend (CRUD, seeded on startup)
  - `agent_memory` — managed by agents service (long-term memory per user/domain)
    - Path pattern: `agent_memory/{user_id}/{domain}/data`
    - Domains: `medication`, `exercise`, `people`
    - Created automatically by agents on first write; no manual seeding needed

## Secrets
```
secrets/
└── sa.json    ← GCP service account key (gitignored, never commit)
```

Add to `.gitignore`:
```
secrets/
*.json
```

## Local Dev Quickstart
```bash
# 1. Place GCP service account key at ./secrets/sa.json

# 2. Build Spring Boot jar
cd backend && mvn package -DskipTests && cd ..

# 3. Start backend + agents + firestore emulator
docker compose up

# 4. Start frontend (separate terminal, on host)
cd frontend && npx expo start
```

Services will be available at:
- Frontend (Expo): `exp://localhost:8081` (or scan QR)
- Backend: `http://localhost:8080`
- Agents: `http://localhost:8000`
- Firestore emulator: `localhost:9090` (gRPC — no web UI with this image)

## Firestore Seed Data
The backend seeds demo reminders on first startup (see backend SPEC). No manual seeding needed.

## Out of Scope (for now)
Cloud Run deployment, Artifact Registry, CI/CD, custom domain, staging environment — these come after the demo is working locally.
