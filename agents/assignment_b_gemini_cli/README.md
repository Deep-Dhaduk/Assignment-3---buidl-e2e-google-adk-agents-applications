# B — Gemini CLI as an ADK tool

Planner → CLI executor → result explainer.

## Code walkthrough

Start with [assignment_b_gemini_cli.py](assignment_b_gemini_cli.py), then [assignment/gemini_cli.py](../../assignment/gemini_cli.py). The executor calls gemini_cli in assignment/gemini_cli.py. It launches the pinned npm package with Node, sends an allowlisted source bundle over stdin, captures JSON, enforces a timeout and denies CLI tool execution.

## Run

From the repository root after setup and database initialization:

```powershell
.\.venv\Scripts\python.exe -m assignment run gemini_cli_agent
```

Try: `Analyze the buggy checkout project and propose regression tests.`

Inspect the returned trace to see actual tool calls and responses.

## Evidence and boundaries

Requires Node, npm ci and Gemini API access. The wrapper analyzes code but does not execute tests or modify files. Only buggy and fixed projects are registered.

Generated traces/reports are in `artifacts/local/`. Watch the [assignment walkthrough videos on Google Drive](https://drive.google.com/drive/folders/1PsvdSfge91KUjwOJbUK7G3BqPK1wT3FH?usp=sharing). Follow [the execution guide](../../docs/EXECUTION.md). Reference projects and explicit adaptations are listed in [REFERENCES.md](../../docs/REFERENCES.md).
