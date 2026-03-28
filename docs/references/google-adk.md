# Google ADK (Agent Development Kit) — Python Reference

Source: https://google.github.io/adk-docs/

---

## Installation

```bash
pip install google-adk
```

---

## Vertex AI Configuration

Set these env vars — ADK will use Vertex AI instead of API key:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
```

Or in `.env`:
```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Agent Definition — LlmAgent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-2.0-flash",          # required
    name="my_agent",                    # required, unique identifier
    description="What this agent does", # used by parent for routing
    instruction="Behavioral guidance",  # system prompt
    tools=[my_tool_fn],                 # Python functions auto-wrapped as FunctionTool
    sub_agents=[child_agent],           # child agents for delegation
    output_key="result_key",            # store response in session state
)
```

### Constructor parameters

| Parameter | Type | Description |
|---|---|---|
| `model` | `str` | Required. LLM model ID e.g. `"gemini-2.0-flash"`, `"gemini-1.5-pro"` |
| `name` | `str` | Required. Unique agent identifier |
| `description` | `str` | Agent capabilities summary — used by parent LLM to decide routing |
| `instruction` | `str` | System prompt / behavioral guidance. Supports `{var}` template syntax to inject session state |
| `tools` | `list` | Python functions (auto-wrapped) or `FunctionTool` instances |
| `sub_agents` | `list` | Child agents. Parent LLM calls `transfer_to_agent(agent_name=...)` to delegate |
| `output_key` | `str` | Key in session state where final response is stored |
| `include_contents` | `str` | `'default'` or `'none'` — controls whether chat history is sent |
| `generate_content_config` | `GenerateContentConfig` | Temperature, max tokens, etc. |

---

## Tools — Python Functions

ADK auto-wraps Python functions as tools. The docstring becomes the tool description.

```python
def get_medication_schedule(user_id: str) -> dict:
    """Returns the medication schedule for the given user."""
    # fetch from Firestore etc.
    return {"medications": [...]}

agent = LlmAgent(
    model="gemini-2.0-flash",
    name="medication_agent",
    tools=[get_medication_schedule],
)
```

---

## Running an Agent Programmatically (Runner)

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME = "oonook"
USER_ID = "demo_user"
SESSION_ID = "session_001"

# Setup
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID,
)
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

# Run async, collect final response
async def call_agent(message: str) -> str:
    content = types.Content(role="user", parts=[types.Part.from_text(message)])
    response_text = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text
    return response_text
```

---

## Multi-Agent Routing — Coordinator / Sub-Agents

The coordinator LLM reads sub-agent `description` fields to decide delegation.
It generates `transfer_to_agent(agent_name=...)` internally.

```python
from google.adk.agents import LlmAgent

medication_agent = LlmAgent(
    name="medication",
    model="gemini-2.0-flash",
    description="Handles questions about medications, dosage, and schedules.",
    instruction="You are a warm medication assistant for elderly users...",
)

exercise_agent = LlmAgent(
    name="exercise",
    model="gemini-2.0-flash",
    description="Handles exercise, stretching, and physical activity questions.",
    instruction="You are a friendly exercise coach for elderly users...",
)

router_agent = LlmAgent(
    name="router",
    model="gemini-2.0-flash",
    description="Routes user requests to the correct specialist agent.",
    instruction="Route every user message to the most appropriate sub-agent based on their description.",
    sub_agents=[medication_agent, exercise_agent],
)
```

---

## Sequential Pipeline

```python
from google.adk.agents import SequentialAgent, LlmAgent

step1 = LlmAgent(name="Step1", output_key="intermediate_data")
step2 = LlmAgent(name="Step2", instruction="Process: {intermediate_data}")

pipeline = SequentialAgent(name="Pipeline", sub_agents=[step1, step2])
```

---

## Parallel Execution

```python
from google.adk.agents import ParallelAgent, LlmAgent

fetch_a = LlmAgent(name="FetchA", output_key="result_a")
fetch_b = LlmAgent(name="FetchB", output_key="result_b")

parallel = ParallelAgent(name="Parallel", sub_agents=[fetch_a, fetch_b])
```

---

## State — Passing Data Between Agents

- `output_key="key"` on `LlmAgent` saves the final response to `session.state["key"]`
- `{key}` in `instruction` injects `session.state["key"]` at runtime
- Tools can read/write `session.state` via `tool_context.state`

---

## Imports Quick Reference

```python
from google.adk.agents import LlmAgent, BaseAgent, SequentialAgent, ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import agent_tool
from google.adk.events import Event, EventActions
from google.genai import types
from google.genai.types import GenerateContentConfig
```

---

## Models (Vertex AI)

| Use case | Model ID |
|---|---|
| Fast text | `gemini-2.0-flash` |
| Thinking/complex | `gemini-2.5-pro` |
| Multimodal (vision) | `gemini-1.5-pro` or `gemini-2.0-flash` |

Use `gemini-2.0-flash` unless you specifically need multimodal or deep reasoning.
