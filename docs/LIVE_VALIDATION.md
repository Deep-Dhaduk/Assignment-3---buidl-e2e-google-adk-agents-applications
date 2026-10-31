# Live validation ? October 31, 2026

Four of the five applications completed live workflows. Lead-profile confirmation passed, but research and export remain incomplete. These checks used real Gemini calls and actual local tools.

| Application | Result | Observed evidence |
|---|---|---|
| A ? Lead generation | Partial | Proposed a customer profile and requested confirmation. Research encountered a 503, then quota errors; no live lead report or citations were produced. |
| B ? Gemini CLI | Passed | ADK invoked the actual Node/Gemini CLI subprocess; exit code 0, source analysis returned, no CLI tools executed. The final explanation labels proposed tests as not executed. |
| C ? Bug assistant | Passed previously | Retrieved BUG-101 and source evidence through MCP and identified the ignored quantity argument. |
| D ? Code review | Passed | Executed the registered sample tests: buggy had two failures, one error and one pass; fixed passed all four. Both structured reports were exported. |
| E ? E-commerce | Passed | MCP catalog lookup, $89.99 quote, runtime-approved demo order, status lookup, runtime-approved pickup change, and zero-stock racket response. Database inspection found one order and stock decremented once. |

## Models and limitations

The bug and code-review checks used `gemini-2.5-flash`. Shopping started on that model and finished on `gemini-3.5-flash-lite`. The final full Gemini CLI run used `gemini-3.5-flash-lite`.

Google returned a daily free-tier limit of 20 requests for this project's `gemini-2.5-flash`, plus a per-minute limit of 5 during one attempt. These are observed limits for this account, not guarantees for other accounts. `gemini-2.5-flash-lite` returned 404 for this new account and recommended `gemini-3.5-flash-lite`.

The newer model completed non-search tasks, but the research workflow returned 429. Google's [pricing documentation](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite) lists Google Search grounding as unavailable on that model's free API tier. Lead research still needs available quota on a Search-capable model. Billing settings and `.env` were not changed.

An order was saved before a model error interrupted the approval response. A subsequent real `order_status` call confirmed it. The demo did not retry the purchase or create a duplicate. No real payment occurred.

The CLI's suggestions still require human review: its suggested zero-quantity test expects zero, while the fixed sample deliberately rejects zero quantity. The CLI does not execute tests; the separate code-review agent does.

## Fixes verified

- The Gemini CLI wrapper now trusts its freshly generated temporary workspace for that subprocess only. Its existing deny-all tool policy and disabled extensions remain in place. This follows the documented [headless workspace trust option](https://geminicli.com/docs/cli/trusted-folders/#headless-and-automated-environments).
- Planner instructions now request source-scoped plain-language tasks, and the final explanation explicitly distinguishes analysis and proposed tests from actual test execution.
- Lint passed and all 22 automated tests passed after the changes (13 dependency/experimental-feature warnings).

## Evidence

[Sanitized live evidence](../artifacts/live-verification.json) records the outcomes and relative trace paths. Detailed live results and reports are under `artifacts/local/live-validation/`; isolated demo databases are under `data/live-validation/`. These directories are ignored by Git. The earlier offline evidence remains a historical record in `artifacts/verification.json`.

## Remaining live check

After the `gemini-2.5-flash` quota resets, rerun the two-turn lead-generation scenario in [EXECUTION.md](EXECUTION.md). Confirm the profile, research up to two companies, verify the cited pages, and inspect the exported JSON and CSV. Do not mark this check complete until those artifacts actually exist.

For further non-search demonstrations, select the successfully tested model for the current PowerShell session:

```powershell
$env:ADK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_CLI_MODEL = "gemini-3.5-flash-lite"
.\.venv\Scripts\python.exe -m assignment run gemini_cli_agent
```

For lead research, select the original Search-capable model after its quota resets:

```powershell
$env:ADK_MODEL = "gemini-2.5-flash"
.\.venv\Scripts\python.exe -m assignment run lead_generation
```

Video recording/upload, managed cloud verification if required, and final submission remain outstanding.
