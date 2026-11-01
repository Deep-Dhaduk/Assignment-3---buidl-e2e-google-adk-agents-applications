# Live validation - updated November 1, 2026

All five applications have completed live workflows using real Gemini calls and actual tools. Lead generation completed on November 1 after prompt corrections, a guided rerun, and manual review of all final citations. This verifies the workflow and exports, not guaranteed accuracy for unattended future research.

| Application | Result | Observed evidence |
|---|---|---|
| A - Lead generation | Passed with review | Profile confirmation, real research and verification searches, and JSON/CSV export. Final output is one tentative Baremetrics lead scored 70/100; current headcount and QA buying intent remain unknown. |
| B - Gemini CLI | Passed | ADK invoked the actual Node/Gemini CLI subprocess; exit code 0, source analysis returned, no CLI tools executed. The final explanation labels proposed tests as not executed. |
| C - Bug assistant | Passed previously | Retrieved BUG-101 and source evidence through MCP and identified the ignored quantity argument. |
| D - Code review | Passed | Executed the registered sample tests: buggy had two failures, one error and one pass; fixed passed all four. Both structured reports were exported. |
| E - E-commerce | Passed | MCP catalog lookup, $89.99 quote, runtime-approved demo order, status lookup, runtime-approved pickup change, and zero-stock racket response. Database inspection found one order and stock decremented once. |

## Models and limitations

The successful lead, bug and code-review checks used `gemini-2.5-flash`. Shopping started on that model and finished on `gemini-3.5-flash-lite`. The final full Gemini CLI run used `gemini-3.5-flash-lite`.

Google returned a daily free-tier limit of 20 requests for this project's `gemini-2.5-flash`, plus a per-minute limit of 5 during one attempt. These are observed limits for this account, not guarantees for other accounts. `gemini-2.5-flash-lite` returned 404 for this new account and recommended `gemini-3.5-flash-lite`.

The newer model completed non-search tasks, but the research workflow returned 429. Google's [pricing documentation](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite) lists Google Search grounding as unavailable on that model's free API tier. On November 1, `gemini-2.5-flash` responded again and completed the Search workflow. Future research still requires available quota on a Search-capable model. Billing settings and `.env` were not changed.

An order was saved before a model error interrupted the approval response. A subsequent real `order_status` call confirmed it. The demo did not retry the purchase or create a duplicate. No real payment occurred.

The CLI's suggestions still require human review: its suggested zero-quantity test expects zero, while the fixed sample deliberately rejects zero quantity. The CLI does not execute tests; the separate code-review agent does.

## Lead report and source review

The first live report treated a web application as QA buying intent and scored it 100/100. It was rejected. Instructions now separate the three score components, require zero buying-signal points when intent is unverified, and preserve headcount uncertainty. Another draft contained inaccessible links and conflicting headcount claims; it was also rejected during citation review.

The final guided rerun re-verified Baremetrics, a company discovered in the initial live research, against three reviewer-checked pages. The [JSON report](../artifacts/lead-report.json) and [CSV](../artifacts/lead-report.csv) contain the same one lead, score, citations and unknowns. A smaller list was accepted instead of inventing a second lead.

- The [official product page](https://baremetrics.com/) supports subscription analytics and web-product fit.
- The [official team page](https://baremetrics.com/about) describes a globally remote team and displays 10+ people; it does not establish an exact current headcount or a maximum of 50.
- [Growjo](https://growjo.com/company/Baremetrics) lists San Francisco and 17 employees. These are third-party directory claims, not independently confirmed current staffing data.

The result is a tentative research candidate, not a verified buyer. [Citation review](../artifacts/lead-citation-review.json) records the limitations. [Provider search evidence](../artifacts/lead-search-evidence.json) records both stages' queries and indexed sources. The verifier returned an unrelated indexed source, so directly opening the three final citations was essential. The model also retained verbose scoring instructions in its methodology field; the original export is preserved without silently rewriting it.

## Fixes verified

- The Gemini CLI wrapper now trusts its freshly generated temporary workspace for that subprocess only. Its existing deny-all tool policy and disabled extensions remain in place. This follows the documented [headless workspace trust option](https://geminicli.com/docs/cli/trusted-folders/#headless-and-automated-environments).
- Planner instructions now request source-scoped plain-language tasks, and the final explanation explicitly distinguishes analysis and proposed tests from actual test execution.
- Lead research instructions now distinguish product fit from buying intent and require explicit uncertainty. Search callbacks preserve provider grounding metadata from nested research agents in the parent trace.
- Lint passed and all 22 automated tests passed after the code changes (13 dependency/experimental-feature warnings).

## Evidence

[Sanitized live evidence](../artifacts/live-verification.json) records the outcomes and relative trace paths. Detailed live results and reports are under `artifacts/local/live-validation/`; isolated demo databases are under `data/live-validation/`. These directories are ignored by Git. The earlier offline evidence remains a historical record in `artifacts/verification.json`.

## Repeating the demonstration

All five live checks are complete with the limitations above. For a new recording, follow [EXECUTION.md](EXECUTION.md), inspect each new output, and preserve evidence from the actual recorded run. Model outputs and quotas can vary.

For further non-search demonstrations, select the successfully tested model for the current PowerShell session:

```powershell
$env:ADK_MODEL = "gemini-3.5-flash-lite"
$env:GEMINI_CLI_MODEL = "gemini-3.5-flash-lite"
.\.venv\Scripts\python.exe -m assignment run gemini_cli_agent
```

For lead research, select the successfully tested Search-capable model when quota is available:

```powershell
$env:ADK_MODEL = "gemini-2.5-flash"
.\.venv\Scripts\python.exe -m assignment run lead_generation
```

Video recording/upload, managed cloud verification if required, and final submission remain outstanding.
