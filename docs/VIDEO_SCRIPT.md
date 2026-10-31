# YouTube code and execution walkthrough

**Recording status: not recorded or uploaded.** This is a script for a real recording, not a transcript of completed live Gemini runs.

Suggested length: 25–35 minutes. Adjust to your course requirements. Record your IDE and terminal/browser. Hide `.env`, API authorization fields and account details. Use an unlisted video only if the instructor accepts it, and verify the link in a signed-out browser.

## 00:00 — Assignment and architecture

Explain: “This repository contains five Google ADK applications. They share configuration, database utilities, session persistence and trace recording. I will show the code and execute each application.”

Open README and `docs/ARCHITECTURE.md`. State which components run locally and which cloud components have not been deployed. Show `python -m assignment doctor`, which reports key presence without exposing it.

## 03:00 — Deep research lead generation

Open `agents/assignment_a_lead_generation/assignment_a_lead_generation.py`. Explain the root coordinator, AgentTool wrappers, SequentialAgent and state keys. Open `assignment/reports.py` and explain evidence URLs, scoring, validation, domain deduplication and JSON/CSV export.

Run the two-turn scenario from EXECUTION.md. Show the proposed profile, your confirmation, search/verification calls, and the final report. Inspect two source URLs. Explain unknowns instead of presenting guesses as facts. If the model/search quota fails, record the failure honestly and rerun after access is available.

## 09:00 — Gemini CLI inside ADK

Open `agents/assignment_b_gemini_cli/assignment_b_gemini_cli.py` and `assignment/gemini_cli.py`. Explain plan → execute → explain, actual subprocess invocation, explicit source bundle, argument-array execution, timeout, JSON parsing and tool policy.

Run analysis of the buggy sample. Show the CLI tool response and exit code. Explain that analysis and proposed tests are different from running tests. Show a missing-key or invalid-project error using test output rather than exposing credentials.

## 14:00 — Bug assistant through MCP

Open `assignment/mcp_server.py`, `assignment/mcp_client.py` and the bug agent. Explain the MCP protocol boundary and the tool allowlist.

Run `mcp-smoke`, then investigate BUG-101 through the live agent. Show ticket retrieval, line-numbered source evidence and suggested regression tests. Explain that this demonstration uses seeded tickets and does not mutate GitHub issues.

## 19:00 — Code review

Open `assignment/review.py` and `assignment/workflows.py`. Explain why evidence collection runs deterministically before model synthesis. Describe disabled, trusted-fixture and Docker execution modes.

Run the buggy review and show actual failures, the empty-cart exception and Ruff's unused-import finding. Run the fixed review and show four passing tests. Compare the structured reports and cite file/line evidence. State which execution mode was used.

## 25:00 — E-commerce

Open `agents/assignment_e_ecommerce/assignment_e_ecommerce.py`, `assignment/commerce.py` and `assignment/db.py`. Explain MCP reads, quote calculation, runtime confirmation, customer ownership, atomic stock update and unique quote-based retry handling.

Search for shoes, prepare a quote, approve the pending purchase, check the order and change delivery. Show an unavailable racket. Show the duplicate-order test and explain why retries do not decrement stock twice. State explicitly that no payment is processed.

## 31:00 — Tests and submission

Run the test suite. Show the recorded verification artifact, CI workflow, setup instructions and deployment limitations. Point to the GitHub URL and video link location. Summarize actual limitations, including any live run or cloud deployment you did not perform.

After recording, add the real YouTube URL and chapter timestamps to README and SUBMISSION.md. Do not use placeholder links or claim the recording is complete before uploading it.
