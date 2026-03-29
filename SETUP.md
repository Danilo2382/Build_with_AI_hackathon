# Oonook — Local Setup Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Java (JDK) | 21 | https://adoptium.net |
| Maven | 3.9+ | bundled as `mvnw`, or install separately |
| Python | 3.11+ | https://www.python.org |
| Node.js | 18+ | https://nodejs.org |
| Android SDK / ADB | any | via Android Studio |

---

## 1. Clone & configure secrets

```bash
git clone https://github.com/Danilo2382/Build_with_AI_hackathon.git
cd Build_with_AI_hackathon
```

### Service account key (required for everything)

1. Go to [GCP Console](https://console.cloud.google.com) → Project `woven-bonbon-485514-h5`
2. IAM & Admin → Service Accounts → find the Oonook service account
3. Keys → Add Key → JSON → download
4. Copy the downloaded file to `config/sa.json`

> `config/sa.json` is gitignored — never commit it.

### Environment file

```bash
cp config/.env config/.env  # already exists, verify values
```

The file should look like this:

```env
FAST_MODEL=gemini-2.5-flash-lite
SMART_MODEL=gemini-2.5-flash
GOOGLE_CLOUD_LOCATION=europe-west1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_APPLICATION_CREDENTIALS=./config/sa.json
AGENTS_URL=http://agents:8000
EXPO_PUBLIC_BACKEND_URL=http://localhost:8080
```

---

## 2. Seed demo data (first time only)

```bash
cd agents
pip install -r requirements.txt
python seed.py
cd ..
```

This creates the demo user `nikola` in Firestore with medications, contacts, checkups, and exercise data.

---

## 3. Start the agents (Python / FastAPI)

```bash
cd agents
pip install -r requirements.txt       # skip if already done
uvicorn main:app --reload --port 8000
```

Runs on **http://localhost:8000**

### Known issues

**`ImportError: cannot import name 'texttospeech_v1'`**
```bash
pip install google-cloud-texttospeech
```

**`ModuleNotFoundError: No module named 'google.adk'` or dependency conflicts**
```bash
pip install --upgrade "google-adk[vertexai]>=0.2.0"
```

If pip gives resolver errors on older pip:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Start the backend (Java / Spring Boot)

```bash
cd backend/oonook
mvn spring-boot:run
```

Runs on **http://localhost:8080**

### Known issues

**`FileNotFoundException: config\sa.json`**

The credentials path is resolved relative to where you run `mvn`.
Run the command from `backend/oonook/` (not `backend/`), or set the env variable explicitly:

```powershell
# PowerShell
$env:GCP_CREDENTIALS_PATH="file:D:/GDGHakaton/Build_with_AI_hackathon/config/sa.json"; mvn spring-boot:run
```

```bash
# bash / Git Bash
GCP_CREDENTIALS_PATH="file:$(pwd)/../../config/sa.json" mvn spring-boot:run
```

**`No plugin found for prefix 'spring-boot'`**

You are in the wrong folder. Run from `backend/oonook/`, not `backend/`.

---

## 5. Start the frontend (Expo / React Native)

```bash
cd frontend
npm install
npx expo start
```

Then press `a` to open on Android device/emulator.

### Connect to backend from a physical Android device

The device can't reach `localhost` on your PC. You need to use your PC's local IP:

1. Find your IP: `ipconfig` (Windows) → look for your WiFi adapter IPv4
2. Create or edit `frontend/.env`:
   ```env
   EXPO_PUBLIC_BACKEND_URL=http://YOUR_PC_IP:8080
   ```
3. Make sure both the phone and PC are on the same WiFi network.

Alternatively, use ADB reverse (USB cable required):
```bash
adb reverse tcp:8080 tcp:8080
adb reverse tcp:8000 tcp:8000
```
This tunnels the phone's `localhost:8080` to your PC, so you can keep `EXPO_PUBLIC_BACKEND_URL=http://localhost:8080`.

### Known issues

**`"react-dom" is added as a dependency but doesn't seem to be installed`**
```bash
npm install
```

**`npm install` fails with peer dependency errors**

The project uses `.npmrc` with `legacy-peer-deps=true`. If it's missing:
```bash
echo "legacy-peer-deps=true" > frontend/.npmrc
npm install
```

---

## 6. Generate reminders (optional, after seeding)

```bash
curl -X POST http://localhost:8000/reminders/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"nikola"}'
```

---

## Architecture overview

```
[Phone / Expo app]
        │  HTTP (port 8080)
        ▼
[Spring Boot backend]  ──── Firestore (reminders, scheduling)
        │  HTTP (port 8000)
        ▼
[Python FastAPI agents]
        │
        ├── Google Vertex AI (Gemini models via google-adk)
        ├── Google Cloud TTS (text-to-speech)
        └── Firestore (user data, medications, contacts, etc.)
```

**Ports:**
- `8080` — Spring Boot backend
- `8000` — Python agents

**GCP project:** `woven-bonbon-485514-h5` | **Region:** `europe-west1`

**Demo user:** `nikola` (all agents are hardcoded to this user ID)

---

## Common gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| Backend 500 on `/chat` | DevTools restarting mid-request | `spring.devtools.restart.enabled=false` in application.properties (already set) |
| Agent returns transcription prompt verbatim | STT ran on `gemini-2.5-flash-lite` which doesn't support audio | Use `SMART_MODEL=gemini-2.5-flash` for STT (already set) |
| 429 Too Many Requests | Free tier RPM limit on Gemini | Wait ~60s between test requests |
| `finish_reason: 15` from agent | Model tried to call a tool not registered | Agents must use ADK `Runner`, not raw `generate_content_async` |
| Spring Boot 422 from uvicorn | HTTP/2 upgrade header rejected | `RestClientConfig` forces HTTP/1.1 (already fixed) |
| Backend NPE on `Map.of()` | `null` values not allowed in `Map.of()` | Use typed payload records with `@JsonProperty` (already fixed) |
