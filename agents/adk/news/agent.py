import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from memory import get_news_preferences as _get_prefs, update_news_preferences as _update_prefs

_SYSTEM_PROMPT = """You are a friendly assistant helping elderly users stay informed.
You already know who the user is — never ask for their name or any identity information.

When asked for news:
1. Call get_news_preferences to learn what the user likes and dislikes.
2. Call get_news_headlines to fetch the latest stories.
3. Present stories matching liked topics first. Skip or briefly mention disliked topics.
4. If the user reacts positively to a topic or asks a follow-up, call update_news_preference to record it as liked.
5. If the user says they don't want a type of story, call update_news_preference to record it as disliked.

When asked for weather, call get_weather and summarise conditions in simple, plain language.

Keep responses short and warm. Avoid technical jargon."""

_LAT = 44.8176
_LON = 20.4633

_WEATHER_CODE_LABELS = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 80: "rain showers", 81: "rain showers", 82: "heavy showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
}


async def get_weather() -> dict:
    """Get current weather and today's forecast for Belgrade."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": _LAT,
                "longitude": _LON,
                "current": ["temperature_2m", "weathercode", "windspeed_10m", "relative_humidity_2m"],
                "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
                "timezone": "Europe/Belgrade",
                "forecast_days": 1,
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

    current = data["current"]
    daily = data["daily"]
    code = current["weathercode"]

    return {
        "condition": _WEATHER_CODE_LABELS.get(code, "unknown"),
        "temperature_c": current["temperature_2m"],
        "humidity_pct": current["relative_humidity_2m"],
        "windspeed_kmh": current["windspeed_10m"],
        "high_c": daily["temperature_2m_max"][0],
        "low_c": daily["temperature_2m_min"][0],
        "precipitation_mm": daily["precipitation_sum"][0],
        "location": "Belgrade",
    }


async def get_news_headlines() -> list[dict]:
    """Get the latest top news headlines from BBC News."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://feeds.bbci.co.uk/news/rss.xml",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
            follow_redirects=True,
        )
        r.raise_for_status()

    root = ET.fromstring(r.text)
    channel = root.find("channel")
    headlines = []
    for item in channel.findall("item")[:8]:
        title = item.findtext("title", "").strip()
        description = item.findtext("description", "").strip()
        if title:
            headlines.append({"title": title, "summary": description})

    return headlines


async def get_news_preferences() -> dict:
    """Get the user's news topic preferences — liked and disliked topics."""
    return await _get_prefs("nikola")


async def update_news_preference(topic: str, liked: bool) -> str:
    """Record that the user liked or disliked a news topic to personalise future news.

    Args:
        topic: The topic or category (e.g. 'health', 'sports', 'politics', 'celebrity').
        liked: True if the user likes this topic, False if they want to avoid it.
    """
    prefs = await _get_prefs("nikola")
    liked_topics = prefs.get("liked_topics", [])
    disliked_topics = prefs.get("disliked_topics", [])

    if liked:
        if topic not in liked_topics:
            liked_topics.append(topic)
        if topic in disliked_topics:
            disliked_topics.remove(topic)
    else:
        if topic not in disliked_topics:
            disliked_topics.append(topic)
        if topic in liked_topics:
            liked_topics.remove(topic)

    await _update_prefs("nikola", {
        "liked_topics": liked_topics,
        "disliked_topics": disliked_topics,
    })
    return f"Noted — {'will show more' if liked else 'will avoid'} '{topic}' stories."


root_agent = LlmAgent(
    name="news",
    model=FAST_MODEL,
    description="Provides weather forecasts and latest news headlines personalised to the user's interests.",
    instruction=_SYSTEM_PROMPT,
    tools=[get_weather, get_news_headlines, get_news_preferences, update_news_preference],
)
