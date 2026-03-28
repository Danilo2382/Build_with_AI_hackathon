import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import SMART_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent

from adk.checkup.agent import root_agent as checkup_agent
from adk.exercise.agent import root_agent as exercise_agent
from adk.medication.agent import root_agent as medication_agent
from adk.news.agent import root_agent as news_agent
from adk.people.agent import root_agent as people_agent
from adk.vision.agent import root_agent as vision_agent
from memory import get_checkups, get_medications, get_profile, get_reminders


async def get_user_profile() -> dict:
    """Get the user's profile including their name, age, language, and emergency contact."""
    return await get_profile("nikola")


async def get_todays_reminders() -> list[dict]:
    """Get all of today's reminders for the user — medications, checkups, exercise, and people."""
    return await get_reminders("nikola")


async def get_current_datetime() -> dict:
    """Get the current date, time, and day of the week."""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "day_of_week": now.strftime("%A"),
    }


async def get_health_summary() -> dict:
    """Get a combined health overview: medications, upcoming checkups, and exercise streak."""
    meds = await get_medications("nikola")
    checkups = await get_checkups("nikola")
    reminders = await get_reminders("nikola")
    return {
        "medications": meds,
        "upcoming_checkups": checkups,
        "reminders_count": len(reminders),
    }


root_agent = LlmAgent(
    name="oonook",
    model=SMART_MODEL,
    description="Main coordinator for Oonook, a voice-first elderly care companion.",
    instruction="""You are Oonook, a caring assistant for elderly users.
You already know who the user is — never ask for their name or any identity information.
Use get_user_profile to personalise your greeting. Use get_current_datetime to be time-aware.
Use get_todays_reminders or get_health_summary to answer overview questions.
Delegate specialist requests immediately to the appropriate sub-agent:
- medication: pills, doses, schedules, reminders
- exercise: physical activity, stretching, movement
- checkup: doctor appointments, medical exams, health checks
- people: staying in touch with family and friends
- vision: describing images or videos
- news: current weather forecast and latest news headlines""",
    tools=[get_user_profile, get_todays_reminders, get_current_datetime, get_health_summary],
    sub_agents=[medication_agent, exercise_agent, checkup_agent, people_agent, vision_agent, news_agent],
)
