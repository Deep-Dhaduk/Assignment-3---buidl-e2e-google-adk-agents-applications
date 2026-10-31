"""Snapshot the tested environment without credentials or editable machine paths."""

from importlib.metadata import distributions
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lines = [
    "# Tested dependency snapshot. Regenerate with python scripts/lock_dependencies.py.",
    "# Python 3.13; pywin32 is only required on Windows.",
]
packages = {}
for package in distributions():
    name = package.metadata["Name"]
    if name.lower() in {"adk-assignment-suite", "pip", "setuptools"}:
        continue
    marker = '; sys_platform == "win32"' if name.lower() == "pywin32" else ""
    packages[name.lower()] = f"{name}=={package.version}{marker}"
lines.extend(packages[name] for name in sorted(packages))
(root / "requirements.lock").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Locked {len(packages)} distributions")
