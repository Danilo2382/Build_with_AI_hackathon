import base64

from google.cloud import texttospeech


_client: texttospeech.TextToSpeechAsyncClient | None = None


def _get_client() -> texttospeech.TextToSpeechAsyncClient:
    global _client
    if _client is None:
        _client = texttospeech.TextToSpeechAsyncClient()
    return _client


async def synthesize(text: str) -> str:
    """Convert text to speech and return base64-encoded MP3 audio."""
    client = _get_client()
    response = await client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Journey-F",
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95,
        ),
    )
    return base64.b64encode(response.audio_content).decode("utf-8")
