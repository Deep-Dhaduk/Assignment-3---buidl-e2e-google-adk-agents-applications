# D — Code review assistant

Deterministic evidence → schema-constrained synthesis → validated report.

## Code walkthrough

Start with [assignment_d_code_review.py](assignment_d_code_review.py), then [assignment/review.py](../../assignment/review.py). ReviewEvidenceAgent always collects AST, Ruff and execution-policy-dependent unittest evidence. The LLM then interprets it, and ExportAgent validates ReviewReport before writing JSON.

## Run

From the repository root after setup and database initialization:

```powershell
.\.venv\Scripts\python.exe -m assignment run code_review
```

Try: `Review this checkout module and prioritize reproducible correctness failures.`

For real fixture execution set `$env:REVIEW_EXECUTION = "trusted"`. Run again with `--project fixed` in a new session and compare the evidence.

## Evidence and boundaries

Select the project with --project buggy or --project fixed. Execution defaults to disabled; trusted mode is only for repository fixtures. Docker mode requires a separately built runner image.

Generated traces/reports are in `artifacts/local/`. Follow [the execution guide](../../docs/EXECUTION.md) and [recording script](../../docs/VIDEO_SCRIPT.md). Reference projects and explicit adaptations are listed in [REFERENCES.md](../../docs/REFERENCES.md).
