import ast
import json
import os
import shutil
import sys
import uuid

from assignment.config import artifact_dir, sample_project
from assignment.process import execute


def inspect_project(project: str) -> dict:
    """Parse registered Python samples and run Ruff; never execute submitted code."""
    try:
        root = sample_project(project)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    files = []
    findings = []
    for path in sorted(root.glob("*.py")):
        if path.is_symlink() or path.resolve().parent != root:
            return {"status": "error", "message": "Symlinks are not accepted"}
        source = path.read_text(encoding="utf-8")
        if len(source) > 100000:
            return {"status": "error", "message": "File exceeds review limit"}
        files.append({"file": path.name, "source": source})
        try:
            tree = ast.parse(source, filename=path.name)
        except SyntaxError as exc:
            findings.append(
                {"file": path.name, "line": exc.lineno, "rule": "syntax", "message": exc.msg}
            )
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"eval", "exec"}
            ):
                findings.append(
                    {
                        "file": path.name,
                        "line": node.lineno,
                        "rule": "dynamic-execution",
                        "message": "Review dynamic execution of untrusted input",
                    }
                )
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append(
                    {
                        "file": path.name,
                        "line": node.lineno,
                        "rule": "bare-except",
                        "message": "Bare except can hide unexpected failures",
                    }
                )
    lint = execute(
        [sys.executable, "-m", "ruff", "check", "--isolated", "--output-format", "json", "."],
        cwd=str(root),
        timeout=30,
    )
    try:
        lint_findings = json.loads(lint.get("stdout", ""))
    except json.JSONDecodeError:
        lint_findings = []
    return {
        "status": "ok",
        "project": project,
        "files": files,
        "ast_findings": findings,
        "lint": lint,
        "lint_findings": lint_findings,
    }


def run_project_tests(project: str) -> dict:
    """Run real unittest tests under the configured execution policy."""
    try:
        root = sample_project(project)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    mode = os.getenv("REVIEW_EXECUTION", "disabled")
    if mode == "trusted":
        # Only repository-owned fixtures are registered. This is not a sandbox.
        result = execute(
            [
                sys.executable,
                "-I",
                "-c",
                "import sys,unittest; sys.path.insert(0,'.'); unittest.main(module=None,argv=['unittest','discover','-v'])",
            ],
            cwd=str(root),
            timeout=30,
        )
    elif mode == "docker":
        if not shutil.which("docker"):
            return {"status": "unavailable", "message": "Docker is not installed"}
        container = "adk-review-" + uuid.uuid4().hex
        result = execute(
            [
                "docker",
                "run",
                "--rm",
                "--name",
                container,
                "--network=none",
                "--read-only",
                "--memory=128m",
                "--cpus=1",
                "--pids-limit=64",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--user=65534:65534",
                "--mount",
                f"type=bind,source={root},target=/workspace,readonly",
                "--workdir=/workspace",
                "assignment-review-runner:local",
                "python",
                "-B",
                "-m",
                "unittest",
                "discover",
                "-v",
            ],
            cwd=str(root),
            timeout=45,
        )
        if result["status"] == "timeout":
            execute(["docker", "rm", "-f", container], cwd=str(root), timeout=10)
    else:
        return {
            "status": "disabled",
            "message": "Tests were NOT executed. Set REVIEW_EXECUTION=trusted for repository fixtures, or docker for isolation.",
        }
    result["execution_mode"] = mode
    return result


def collect_review(project: str) -> dict:
    """Collect evidence deterministically before asking an LLM to interpret it."""
    analysis = inspect_project(project)
    if analysis["status"] != "ok":
        return analysis
    result = {"project": project, "analysis": analysis, "tests": run_project_tests(project)}
    report_path = artifact_dir() / f"review-evidence-{uuid.uuid4().hex}.json"
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["artifact"] = str(report_path)
    return result
