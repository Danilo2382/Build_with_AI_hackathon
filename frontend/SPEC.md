# Frontend Spec — Dev 1

## Overview

Single-screen, voice-first Expo React Native app for elderly users. No navigation, no text input, no loading spinners. All feedback is via voice (TTS). Minimum font size 32px everywhere.

## Stack

- Expo SDK 51
- React Native + TypeScript
- Expo Router (single screen only)
- expo-audio (audio recording + TTS playback) ← replaces expo-av
- expo-video (video playback in media zone) ← replaces expo-av for video
- expo-camera (photo + video capture)
- expo-speech (TTS — speaks responses and thinking prompt aloud)
- No external HTTP libraries — use `fetch` only

## Environment

```
EXPO_PUBLIC_BACKEND_URL=http://localhost:8080
```

## Screen Layout (top to bottom)

```
┌─────────────────────────────┐
│  Greeting: name + date       │  always visible
├─────────────────────────────┤
│  Media zone (max 40% height) │  hidden when empty
│  image / video + caption     │
├─────────────────────────────┤
│  Response text area          │  hidden when empty
├─────────────────────────────┤
│  Reminders strip (scroll →)  │  always visible
├─────────────────────────────┤
│        [MIC BUTTON]          │  large, centered
│       [camera button]        │  smaller, below mic
└─────────────────────────────┘
```

## Mic Button — Push to Talk

Four states:

| State      | Visual           | Audio                                        |
| ---------- | ---------------- | -------------------------------------------- |
| idle       | gray             | —                                            |
| listening  | red, pulsing     | —                                            |
| thinking   | animated spinner | plays "Let me check that..." via expo-speech |
| responding | blue, sound wave | speaks full response via expo-speech         |

Flow: hold → record audio via **expo-audio** → release → POST /chat → speak response via **expo-speech**.

## Camera Button

- **Tap** → capture photo → POST /vision
- **Hold** → record video → POST /video
- Result appears in media zone
- Never auto-opens

## Reminders Strip

- Horizontal scroll, always visible when idle
- Fetch on mount from `GET /reminders?user_id=nikola`
- Five types: 💊 medication | 🧘 stretching | 💪 exercise | 🏥 checkup | 👥 people
- Each card: icon + label + time
- Tap any card → trigger voice interaction: sends a predefined message to `POST /chat` based on reminder type (e.g. tapping 💊 Aspirin sends `"Tell me about my Aspirin reminder"`, tapping 👥 Call Ana sends `"Should I call Ana?"`). No mic recording needed — message is synthetic.

## Setup Modal

- Accessed via long-press on share button (5+ seconds)
- Dark theme, green accent
- Fields: Patient Name, Medications (name/dose/time), Contacts (name/relationship/telegram_chat_id), Appointments (doctor/date)
- TODO: wire up Save to write to Firestore via backend

## Media Zone

- Hidden by default
- Image: full width, caption below — rendered via React Native `<Image>`
- Video: inline, autoplay muted — rendered via **expo-video** `<VideoView>`
- Tap → fullscreen; tap X → close

## API Contract

All calls to `${EXPO_PUBLIC_BACKEND_URL}` — hardcode `user_id = "nikola"`.

```
POST /chat
  body: { user_id, message }
  response: { response, agent, media: { type, url } | null }

POST /vision
  body: { user_id, image_base64 }
  response: same shape

POST /video
  body: { user_id, video_base64 }
  response: same shape

GET /reminders?user_id=nikola
  response: { reminders[] }

POST /reminders/confirm
  body: { user_id, reminder_id }
  response: { confirmed, response }
```

On any error:

- If response is valid JSON with `fallback_response` field → speak it via expo-speech
- If response cannot be parsed as JSON (e.g. network timeout, 502 HTML page) → speak hardcoded fallback: `"Sorry, I cannot connect. Please try again."`

## Constraints

- Font minimum 32px everywhere
- High contrast (no grays for text)
- No loading spinners — always voice feedback
- No auth, no login screen
- No navigation — single screen forever
