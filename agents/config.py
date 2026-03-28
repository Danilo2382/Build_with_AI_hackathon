import json
import os
from pathlib import Path

from dotenv import load_dotenv
import vertexai

_REPO_ROOT = Path(__file__).parent.parent

# Load config/.env when running locally (no-op if the file doesn't exist)
load_dotenv(_REPO_ROOT / "config" / ".env")

# Resolve GOOGLE_APPLICATION_CREDENTIALS to absolute — dotenv sets it as a
# relative path (relative to repo root) but Google SDKs resolve from CWD.
_sa_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
if _sa_env and not Path(_sa_env).is_absolute():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(_REPO_ROOT / _sa_env)

GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")

# Model selection — change here to swap across all agents at once
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-1.5-flash-002")  # router + text agents
SMART_MODEL = os.getenv("SMART_MODEL", "gemini-1.5-pro-002")  # vision


def _resolve_project() -> str:
    """Read project ID from the service account file."""
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS",
                             str(_REPO_ROOT / "config" / "sa.json"))
    with open(sa_path) as f:
        return json.load(f)["project_id"]


GOOGLE_CLOUD_PROJECT = _resolve_project()

# Initialise Vertex AI once at import time — no network call, just sets config
vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
