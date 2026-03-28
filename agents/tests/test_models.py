from models import AgentResponse, ChatRequest, ErrorResponse, MediaItem


def test_agent_response_defaults_media_to_none():
    r = AgentResponse(response="Hello", agent="medication")
    assert r.media is None


def test_agent_response_with_media():
    r = AgentResponse(
        response="Here is your image",
        agent="vision",
        media=MediaItem(type="image", url="https://storage.googleapis.com/YOUR_GCS_BUCKET/x.jpg"),
    )
    assert r.media.type == "image"
    assert "YOUR_GCS_BUCKET" in r.media.url


def test_chat_request_fields():
    req = ChatRequest(user_id="demo_user", message="When do I take aspirin?")
    assert req.user_id == "demo_user"
    assert "aspirin" in req.message


def test_error_response_has_fallback():
    err = ErrorResponse(
        error="agent_error",
        message="Something went wrong",
        fallback_response="Sorry, I am having trouble. Please try again.",
    )
    assert err.fallback_response.startswith("Sorry")
