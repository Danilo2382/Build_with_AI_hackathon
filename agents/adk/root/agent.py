import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import SMART_MODEL  # noqa: F401 — ensures vertexai.init() is called
from google.adk.agents import LlmAgent

from adk.checkup.agent import root_agent as checkup_agent
from adk.exercise.agent import root_agent as exercise_agent
from adk.medication.agent import root_agent as medication_agent
from adk.people.agent import root_agent as people_agent
from adk.vision.agent import root_agent as vision_agent

root_agent = LlmAgent(
    name="oonook",
    model=SMART_MODEL,
    description="Main coordinator for Oonook, a voice-first elderly care companion.",
    instruction="""You are Oonook, a caring assistant for elderly users.
Delegate every request to the appropriate specialist agent:
- medication: pills, doses, schedules, reminders
- exercise: physical activity, stretching, movement
- checkup: doctor appointments, medical exams, health checks
- people: staying in touch with family and friends
- vision: describing images or videos""",
    sub_agents=[medication_agent, exercise_agent, checkup_agent, people_agent, vision_agent],
)
