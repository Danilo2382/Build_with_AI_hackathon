# Frontend Spec — Dev 1

## Overview
Single-screen, voice-first Expo React Native app for elderly users. No navigation, no text input, no loading spinners. All feedback is via voice (TTS). Minimum font size 32px everywhere.

## Stack
- Expo SDK 51
- React Native + TypeScript
- Expo Router (single screen only)
- expo-av (audio recording + TTS playback)
- expo-camera (photo + video capture)
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

| State | Visual | Audio |
|---|---|---|
| idle | gray | — |
| listening | red, pulsing | — |
| thinking | animated spinner | plays "Let me check that..." via TTS |
| responding | blue, sound wave | speaks full response via TTS |

Flow: hold → record audio → release → POST /chat → TTS response.

## Camera Button
- **Tap** → capture photo → POST /vision
- **Hold** → record video → POST /video
- Result appears in media zone
- Never auto-opens

## Reminders Strip
- Horizontal scroll, always visible when idle
- Fetch on mount from `GET /reminders?user_id=demo_user`
- Five types: 💊 medication | 🧘 stretching | 💪 exercise | 🏥 checkup | 👥 people
- Each card: icon + label + time
- Tap any card → trigger voice interaction: sends a predefined message to `POST /chat` based on reminder type (e.g. tapping 💊 Aspirin sends `"Tell me about my Aspirin reminder"`, tapping 👥 Call Ana sends `"Should I call Ana?"`). No mic recording needed — message is synthetic.

## Media Zone
- Hidden by default
- Image: full width, caption below
- Video: inline, autoplay muted
- Tap → fullscreen; tap X → close

## API Contract

All calls to `${EXPO_PUBLIC_BACKEND_URL}` — hardcode `user_id = "demo_user"`.

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

GET /reminders?user_id=demo_user
  response: { reminders[] }

POST /reminders/confirm
  body: { user_id, reminder_id }
  response: { confirmed, response }
```

On any error:
- If response is valid JSON with `fallback_response` field → speak it via TTS
- If response cannot be parsed as JSON (e.g. network timeout, 502 HTML page) → speak hardcoded fallback: `"Sorry, I cannot connect. Please try again."`

## Constraints
- Font minimum 32px everywhere
- High contrast (no grays for text)
- No loading spinners — always voice feedback
- No auth, no login screen
- No navigation — single screen forever
