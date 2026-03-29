import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import FAST_MODEL, SMART_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent
from vertexai.generative_models import GenerativeModel

from adk.checkup.agent import root_agent as checkup_agent
from adk.exercise.agent import root_agent as exercise_agent
from adk.medication.agent import root_agent as medication_agent
from adk.news.agent import root_agent as news_agent
from adk.people.agent import root_agent as people_agent
from adk.vision.agent import root_agent as vision_agent
from memory import get_checkups, get_emergency_contacts, get_medications, get_profile, get_reminders
from telegram import send_message


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


async def _ai_reasoning(user_message: str) -> str:
    """Generate a one-sentence emergency assessment using Gemini."""
    model = GenerativeModel(model_name=FAST_MODEL)
    prompt = (
        f"An elderly person said: \"{user_message}\"\n"
        "In one short sentence, describe what kind of emergency this might be "
        "and what their contact should do. Be direct and calm."
    )
    response = await model.generate_content_async(prompt)
    return response.text.strip()


async def call_for_help(trigger_message: str) -> str:
    """Send an emergency alert to all emergency contacts via Telegram.
    Call this IMMEDIATELY if the user screams for help, says they fell, are hurt,
    can't breathe, feel chest pain, or expresses any distress or danger signal.
    Do not ask for confirmation — act immediately.

    Args:
        trigger_message: The exact message the user said that triggered the emergency.
    """
    profile = await get_profile("nikola")
    name = profile.get("name", "The user")
    contacts = await get_emergency_contacts("nikola")

    if not contacts:
        return "No emergency contacts configured."

    reasoning = await _ai_reasoning(trigger_message)
    timestamp = datetime.now().strftime("%d %B %Y, %H:%M")

    message = (
        f"🚨 {name} might need help, reach out immediately.\n\n"
        f"💬 They said: \"{trigger_message}\"\n\n"
        f"🤖 {reasoning}\n\n"
        f"🕐 {timestamp}"
    )

    sent = 0
    for contact in contacts:
        chat_id = contact.get("telegram_chat_id")
        if chat_id:
            await send_message(chat_id, message)
            sent += 1

    if sent == 0:
        return "Emergency contacts found but no Telegram chat IDs configured yet."
    return f"Emergency alert sent to {sent} contact(s)."


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


async def confirm_my_reminder(reminder_id: str) -> str:
    """Mark a specific reminder as 'confirmed' (completed) by its ID.
    
    Args:
        reminder_id: The unique ID of the reminder to confirm.
    """
    from memory import update_reminder
    await update_reminder("nikola", reminder_id, {"status": "confirmed"})
    return "Reminder confirmed successfully."


root_agent = LlmAgent(
    name="oonook",
    model=SMART_MODEL,
    description="Main coordinator for Oonook, a voice-first elderly care companion.",
    instruction="""You are Oonook, a caring assistant for elderly users.
You already know who the user is — never ask for their name or any identity information.
Use get_user_profile to personalise your greeting. Use get_current_datetime to be time-aware.
Use get_todays_reminders or get_health_summary to answer overview questions.

PROACTIVE SCHEDULE: If the user asks "What should I do?", "What's my schedule?", or anything about their day:
1. Call get_todays_reminders immediately.
2. Summarize the items they haven't confirmed yet (pending medications, exercise, or calls).
3. Do not ask what they want to be reminded of—just tell them their schedule.

ACTIONS & CONFIRMATION:
1. If the user mentions completing a task that matches a reminder (e.g., "I took my pill", "I did my stretches"):
   - First, call get_todays_reminders to find the matching reminder's unique ID.
   - Then, call confirm_my_reminder(reminder_id) immediately.
2. You can also delegate to specialized agents:
   - medication: take detailed history, confirm specific pill intake
   - exercise: record full sessions or update streaks
   - people: log family calls

EMERGENCY: This is a voice interface — transcription may be imperfect.
Call call_for_help IMMEDIATELY, without asking for confirmation, if they fell, can't breathe, or screams help.

Delegate specialist requests as needed:
- medication: pills, history, confirm intake
- exercise: activity, streaks, sessions
- checkup: appointments
- people: family and friends contact logs
- vision: describing images or videos
- news: latest news headlines""",
    tools=[get_user_profile, get_todays_reminders, get_current_datetime, get_health_summary, call_for_help, confirm_my_reminder],
    sub_agents=[medication_agent, exercise_agent, checkup_agent, people_agent, vision_agent, news_agent],
)
