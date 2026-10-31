"""Generate submission evidence from actual checks, without making model calls."""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run(args, env=None):
    result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout.replace(str(ROOT), "{REPOSITORY}"),
        "stderr": result.stderr.replace(str(ROOT), "{REPOSITORY}"),
    }


def main():
    destination = ROOT / "artifacts"
    destination.mkdir(exist_ok=True)
    checks = {}
    checks["lint"] = run(
        [sys.executable, "-m", "ruff", "check", "assignment", "agents", "tests", "scripts"]
    )
    checks["tests"] = run(
        [sys.executable, "-m", "pytest", "-q", "--junitxml=artifacts/test-results.xml"]
    )
    xml_path = destination / "test-results.xml"
    if xml_path.exists():
        document = ElementTree.parse(xml_path)
        for suite in document.iter("testsuite"):
            suite.set("hostname", "local-verification")
        document.write(xml_path, encoding="utf-8", xml_declaration=True)
    with tempfile.TemporaryDirectory(prefix="adk-verification-") as directory:
        env = dict(os.environ)
        env.update(
            {
                "ADK_DATA_DIR": directory,
                "ADK_ARTIFACT_DIR": str(Path(directory) / "artifacts"),
                "DATABASE_URL": f"sqlite:///{(Path(directory) / 'demo.db').as_posix()}",
                "REVIEW_EXECUTION": "trusted",
            }
        )
        checks["local_tool_demo"] = run([sys.executable, "-m", "assignment", "demo"], env)
        for field in ("stdout", "stderr"):
            checks["local_tool_demo"][field] = (
                checks["local_tool_demo"][field]
                .replace(directory, "{TEMPORARY_DEMO_DIRECTORY}")
                .replace(directory.replace("\\", "\\\\"), "{TEMPORARY_DEMO_DIRECTORY}")
            )
        if checks["local_tool_demo"]["exit_code"] == 0:
            raw = (Path(directory) / "artifacts/local-demo.json").read_text(encoding="utf-8")
            raw = raw.replace(str(ROOT).replace("\\", "\\\\"), "{REPOSITORY}")
            raw = raw.replace(directory.replace("\\", "\\\\"), "{TEMPORARY_DEMO_DIRECTORY}")
            (destination / "local-demo.json").write_text(raw, encoding="utf-8")
    evidence = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "google_adk": version("google-adk"),
        "mcp": version("mcp"),
        "checks": checks,
        "live_gemini_verified": False,
        "cloud_deployment_verified": False,
        "docker_verified": False,
        "youtube_uploaded": False,
        "note": "Local tools and ADK orchestration tested. Scripted models in tests are test doubles, not live Gemini calls.",
    }
    (destination / "verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({name: check["exit_code"] for name, check in checks.items()}, indent=2))
    return 0 if all(check["exit_code"] == 0 for check in checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
