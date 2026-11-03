"""Configuration is read at runtime so tests can isolate databases and artifacts."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)


def model_name() -> str:
    return os.getenv("ADK_MODEL", "gemini-2.5-flash")


def model_with_retries():
    """Retry transient model HTTP failures, without replaying an agent workflow."""
    from google.adk.models.google_llm import Gemini
    from google.genai import types

    return Gemini(
        model=model_name(),
        retry_options=types.HttpRetryOptions(
            attempts=4,
            initial_delay=2,
            max_delay=10,
            exp_base=2,
            http_status_codes=[500, 502, 503, 504],
        ),
    )


def data_dir() -> Path:
    path = Path(os.getenv("ADK_DATA_DIR", str(ROOT / "data"))).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_dir() -> Path:
    path = Path(os.getenv("ADK_ARTIFACT_DIR", str(ROOT / "artifacts" / "local"))).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_url() -> str:
    return os.getenv("DATABASE_URL") or f"sqlite:///{(data_dir() / 'assignment.db').as_posix()}"


def sample_project(name: str) -> Path:
    # An explicit registry prevents an LLM from reading arbitrary paths or secrets.
    projects = {key: ROOT / "examples" / "review_targets" / key for key in ("buggy", "fixed")}
    if name not in projects:
        raise ValueError("project must be 'buggy' or 'fixed'")
    return projects[name].resolve()
