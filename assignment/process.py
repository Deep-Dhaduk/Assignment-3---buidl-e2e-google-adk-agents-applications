"""Bounded child processes with argument arrays (never a shell command)."""

import os
import signal
import subprocess
import tempfile
import time


def execute(
    argv: list[str], *, cwd: str, timeout: int, env: dict | None = None, stdin: str = ""
) -> dict:
    started = time.monotonic()
    options = {"start_new_session": True} if os.name != "nt" else {}
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            child = subprocess.Popen(
                argv,
                cwd=cwd,
                env=env,
                stdin=subprocess.PIPE,
                stdout=output,
                stderr=errors,
                shell=False,
                **options,
            )
        except OSError as exc:
            return {"status": "unavailable", "message": str(exc), "exit_code": None}
        status = "ok"
        try:
            child.communicate(input=stdin.encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            status = "timeout"
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                )
            else:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            child.kill()
            child.communicate()
        output.seek(0)
        errors.seek(0)
        stdout = output.read(65537)
        stderr = errors.read(65537)
        return {
            "status": status if status != "ok" else ("ok" if child.returncode == 0 else "failed"),
            "exit_code": child.returncode,
            "stdout": stdout[:65536].decode("utf-8", errors="replace"),
            "stderr": stderr[:65536].decode("utf-8", errors="replace"),
            "truncated": len(stdout) > 65536 or len(stderr) > 65536,
            "duration_seconds": round(time.monotonic() - started, 3),
        }
