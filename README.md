# Assignment 3 — End-to-end Google ADK applications

Five runnable Python applications with real ADK orchestration, a Gemini CLI subprocess, MCP services, code-review evidence, and transactional demo orders.

**Submission status:** implementation and local verification are included. Live Gemini runs passed for the bug assistant, Gemini CLI, code review, and e-commerce. Lead-profile confirmation passed, but live research/export remains blocked by model quota and Search availability. See [live validation results](docs/LIVE_VALIDATION.md). A YouTube recording has **not** been created or uploaded. Google Cloud/AlloyDB deployment has **not** been executed. See [the submission checklist](docs/SUBMISSION.md) before submitting.

| Requirement | Application | Implementation |
|---|---|---|
| a. Deep research for lead generation | [assignment_a_lead_generation](agents/assignment_a_lead_generation/README.md) | Profile discovery → user confirmation → web research → verification → scored JSON/CSV reports |
| b. Gemini CLI as an ADK tool | [assignment_b_gemini_cli](agents/assignment_b_gemini_cli/README.md) | Planner → actual headless Gemini CLI subprocess → result explanation |
| c. MCP bug assistant | [assignment_c_mcp_bug_assistant](agents/assignment_c_mcp_bug_assistant/README.md) | ADK → MCP stdio → bug database and source evidence |
| d. Code review assistant | [assignment_d_code_review](agents/assignment_d_code_review/README.md) | Deterministic AST/lint/test evidence → structured review → report artifact |
| e. E-commerce assistant | [assignment_e_ecommerce](agents/assignment_e_ecommerce/README.md) | MCP product search → priced quote → runtime approval → transactional order |

## Assignment source files

Open these files to review the five assignment implementations:

- [assignment_a_lead_generation.py](agents/assignment_a_lead_generation/assignment_a_lead_generation.py)
- [assignment_b_gemini_cli.py](agents/assignment_b_gemini_cli/assignment_b_gemini_cli.py)
- [assignment_c_mcp_bug_assistant.py](agents/assignment_c_mcp_bug_assistant/assignment_c_mcp_bug_assistant.py)
- [assignment_d_code_review.py](agents/assignment_d_code_review/assignment_d_code_review.py)
- [assignment_e_ecommerce.py](agents/assignment_e_ecommerce/assignment_e_ecommerce.py)

Each folder also includes a small `agent.py` entry point for ADK discovery. Existing run commands still work.

## Quick start on Windows

Prerequisites: Python 3.11–3.13 (tested with 3.13), Node.js 22, Git, and Gemini API access for live agents. Google Cloud and Docker are optional for the local path.

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Open `.env` locally and set `GOOGLE_API_KEY`. Do not commit or record the key. `ADK_MODEL` is configurable; choose a model available to your account. Search/model availability and free-tier quotas depend on your Gemini account.

```powershell
.\.venv\Scripts\python.exe -m assignment doctor
.\.venv\Scripts\python.exe -m assignment run bug_assistant
```

Enter: `Why does checkout charge for only one item when I buy three?`

Chat exits with `/quit`. E-commerce actions pause until `/approve` or `/reject`. The local CLI uses a fixed development identity; it is not a public multi-user service.

## Run all five applications

```powershell
.\.venv\Scripts\python.exe -m assignment run lead_generation
.\.venv\Scripts\python.exe -m assignment run gemini_cli_agent
.\.venv\Scripts\python.exe -m assignment run bug_assistant
.\.venv\Scripts\python.exe -m assignment run code_review --project buggy
.\.venv\Scripts\python.exe -m assignment run ecommerce
```

Run one prompt non-interactively:

```powershell
.\.venv\Scripts\python.exe -m assignment run bug_assistant --prompt "Investigate BUG-101 and cite the source lines."
```

The returned session ID can be supplied with `--session` for another turn. Interactive chat is the easiest way to handle checkout confirmation.

## Verify without an API key

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
.\.venv\Scripts\python.exe -m assignment mcp-smoke
$env:REVIEW_EXECUTION = "trusted"
.\.venv\Scripts\python.exe -m assignment demo
```

`trusted` executes only the two registered repository sample projects on your machine. It is **not** a sandbox for arbitrary code. `disabled` is the default. [Docker isolation](docs/DEPLOYMENT.md) is available when Docker is installed.

The demo uses real database transactions, MCP connections, Ruff, and unittest. It does **not** call Gemini, perform live lead research, or pretend to invoke a model. Repeated demos consume seeded stock; use a fresh `ADK_DATA_DIR` when needed.

## Browser access and API

Set a random `APP_API_KEY` of at least 24 characters in `.env`, then:

```powershell
.\.venv\Scripts\python.exe -m uvicorn assignment.api:app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/docs` for the interactive API. Each protected request requires the header `Authorization: Bearer YOUR_APP_API_KEY`. This is a single-operator API; the server assigns identity rather than accepting a customer ID from the model.

For the ADK development web UI:

```powershell
.\.venv\Scripts\adk.exe web agents --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and select an assignment folder (`assignment_a_lead_generation` through `assignment_e_ecommerce`). The UI and discovery of all five applications were checked locally; live model calls still require your key. See [the execution guide](docs/EXECUTION.md). Keep development interfaces on localhost.

## Artifacts and walkthrough

- [Architecture and code walkthrough](docs/ARCHITECTURE.md)
- [Execution guide and demo prompts](docs/EXECUTION.md)
- [YouTube recording script](docs/VIDEO_SCRIPT.md)
- [Deployment and operational boundaries](docs/DEPLOYMENT.md)
- [References and adaptations](docs/REFERENCES.md)
- [Submission checklist](docs/SUBMISSION.md)
- [Recorded local verification](artifacts/verification.json)
- [Live validation results and remaining blocker](docs/LIVE_VALIDATION.md)
- [Sanitized live verification evidence](artifacts/live-verification.json)

Agent traces and generated reports go to `artifacts/local/`; databases and sessions go to `data/`. Both are ignored by Git. Only sanitized, intentional evidence belongs in the submission.

## Design boundaries

The code includes confirmation enforcement, parameterized queries, ownership checks, expiring quotes, integer-cent prices, atomic stock updates, idempotent checkout, bounded subprocesses, and tests. These are production-oriented controls, **not a claim that this student project is certified for production**.

The implementation uses a custom MCP server with SQLite locally and SQLAlchemy/psycopg support for PostgreSQL-compatible databases. It does not reproduce the reference's managed AlloyDB + MCP Toolbox deployment. The bug assistant uses seeded local tickets and sample source, not a live GitHub issue integration. Code review is restricted to allowlisted sample projects. See the adaptation table in the references document.

No real payments, customer emails, or outreach are sent.
