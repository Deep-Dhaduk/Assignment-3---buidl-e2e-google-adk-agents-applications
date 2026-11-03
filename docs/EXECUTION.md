# Execution walkthrough

## Setup

Run all commands from the repository root. On Windows use `scripts/setup.ps1` as described in README. On Linux/macOS:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
npm ci
cp .env.example .env
python -m assignment init
python -m assignment doctor
```

Edit `.env` locally with your Gemini key. A free-tier key may have low quotas or unavailable search/model combinations. If a call fails, inspect the error and choose an available `ADK_MODEL`; never substitute fabricated live output.

## Live validation status

All five applications completed live checks. Lead research/export completed after a guided rerun and manual citation review on November 1. See [live validation results](LIVE_VALIDATION.md) for tested models, evidence, and known output limitations.

## Local verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m assignment mcp-smoke
$env:REVIEW_EXECUTION = "trusted"
.\.venv\Scripts\python.exe -m assignment demo
```

The demo writes `artifacts/local/local-demo.json`. Open it and show MCP tool discovery, the priced quote, the order and duplicate retry, failed buggy tests and passing fixed tests. These are local tool results, not live Gemini results.

## A: Lead generation

```powershell
.\.venv\Scripts\python.exe -m assignment run lead_generation
```

First prompt: `I sell automated QA software. Help me define a customer profile for small US B2B SaaS companies. I want three leads with public evidence, not personal emails.`

Review the proposed profile, then reply: `Confirmed. Research three companies matching that profile and export the evidence-backed report.`

Inspect search calls in the saved trace. Open the generated JSON and CSV. Verify every cited URL and explain unknowns. A smaller list is acceptable when evidence is insufficient.

## B: Gemini CLI

```powershell
.\.venv\Scripts\python.exe -m assignment run gemini_cli_agent --prompt "Analyze the buggy checkout sample. Explain the defects and propose regression tests."
```

Show planner output, the `gemini_cli` tool call and response, exit code, and the explanation. The CLI does not run tests here; application D does. Try project `fixed` for a comparison. Missing CLI/key and timeout states are explicit errors.

## C: Bug assistance

```powershell
.\.venv\Scripts\python.exe -m assignment run bug_assistant --prompt "Checkout charges for one item when I order three. Find the relevant ticket and source, explain the cause, and suggest regression tests."
```

Expected evidence: BUG-101, the `calculate_total` implementation in `pricing.py`, and the quantity test. Follow up about an empty cart to investigate BUG-102. Ask for an unrelated problem to show uncertainty instead of a fabricated ticket.

## D: Code review

```powershell
$env:REVIEW_EXECUTION = "trusted"
.\.venv\Scripts\python.exe -m assignment run code_review --project buggy --prompt "Review this checkout module. Prioritize reproducible correctness failures."
.\.venv\Scripts\python.exe -m assignment run code_review --project fixed --prompt "Review the corrected module and report the actual test outcome."
```

The buggy sample produces two failures, one error, and one passing test. Ruff flags an unused import. The fixed sample passes all four tests. Compare evidence and structured reports. The project is chosen by `--project` or the API's validated `project` field, not by arbitrary file paths in chat. Start a new session when switching projects.

## E: Shopping

```powershell
.\.venv\Scripts\python.exe -m assignment run ecommerce
```

1. `Find running shoes under 100 dollars.`
2. `I want one pair of SHOE-001 with standard delivery. Prepare the order.`
3. Ask to place the displayed quote if the agent has not requested confirmation yet.
4. Review the quote/action, then type `/approve`. Use `/reject` to demonstrate denial.
5. `Check the status of that order.`
6. `Change delivery to pickup.` Review and approve the new action.
7. `Can I buy a tournament racket?` The database reports zero stock.

The returned order ID corresponds to a persisted row. Do not show any output as a real payment receipt.

## Authenticated browser/API demonstration

Set `APP_API_KEY` locally to a random secret with at least 24 characters, then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn assignment.api:app --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/docs`. Supply `Bearer YOUR_APP_API_KEY` in the authorization header field. Example request to `POST /agents/assignment_c_mcp_bug_assistant/run`:

```json
{"prompt":"Investigate BUG-101","project":"buggy"}
```

Use the returned `session_id` for follow-ups. For an action awaiting approval, send its returned confirmation key to `POST /agents/assignment_e_ecommerce/confirm`:

```json
{"session_id":"RETURNED_SESSION","confirmation_id":"RETURNED_CONFIRMATION_ID","confirmed":true}
```

The API rejects invented, already-consumed, and wrong-session confirmation IDs. Direct `/shop` endpoints demonstrate database behavior without model calls. The API is intentionally single-operator and one worker.

## Optional ADK development UI

The agent folders are named `assignment_a_lead_generation`, `assignment_b_gemini_cli`, `assignment_c_mcp_bug_assistant`, `assignment_d_code_review`, and `assignment_e_ecommerce`. These names appear in the ADK web app selector; CLI and API names remain unchanged. The folders follow ADK discovery conventions. You can try:

```powershell
.\.venv\Scripts\adk.exe web agents --host 127.0.0.1 --port 8000
```

The pinned ADK UI starts successfully and discovers all five applications. It has its own session service; the review sample defaults to `buggy` there. The custom runtime supplies persistent SQLite sessions without SQLAlchemy's optional async dependencies. Keep this development server local. Restart the server after editing `.env`.

## Troubleshooting

### Temporary model failure while recording

Lead generation retries each model request up to four total attempts for HTTP
500/502/503/504, with exponential backoff starting at two seconds. It does not
automatically restart the entire workflow or retry a daily quota error. The
existing overall agent-turn time limit still applies. Retries cannot guarantee
that an overloaded provider recovers.

If a model error persists, the CLI prints a concise error and exits with status 1.
When a session ID is known, it prints a resume command. Interactive `--session`
restores the previous conversation and any pending confirmations:

```powershell
.\.venv\Scripts\python.exe -m assignment run lead_generation --session YOUR_SESSION_ID
```

Wait for the `You>` prompt before entering your research request. Video-script
instructions such as "While it processes, say" are spoken narration, not terminal
commands. Check whether earlier tool actions or exports completed before repeating
an action after a failed response. A previous successful recording or saved report
must be labeled as such if the new live run fails.

| Symptom | Action |
|---|---|
| Missing Gemini key | Edit `.env`, restart the process, run `doctor`; never print the key |
| Model not found / quota exceeded | Select an available model or wait for quota reset; save the actual failure |
| CLI unavailable | Install Node 22 and run `npm ci` |
| MCP database missing | Run `python -m assignment init` using the same environment |
| Tests disabled | Explicitly select trusted sample execution or configure Docker |
| Order expired | Ask for a new quote; quotes last 15 minutes |
| API startup rejects key | Set a separate, random `APP_API_KEY` of at least 24 characters |
| API returns 429 | Wait for the current run; this demo serializes agent runs |
| Fixed review still shows buggy project | Start a fresh session with `--project fixed` |
