"""Configuration is read at runtime so tests can isolate databases and artifacts."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)


def model_name() -> str:
    return os.getenv("ADK_MODEL", "gemini-2.5-flash")


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
