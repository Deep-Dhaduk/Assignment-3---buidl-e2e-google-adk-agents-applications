# A — Deep research for lead generation

Profile discovery → confirmation → research → verification → report export.

## Code walkthrough

Start with [assignment_a_lead_generation.py](assignment_a_lead_generation.py), then [assignment/reports.py](../../assignment/reports.py). The coordinator uses AgentTool to call pattern discovery and a SequentialAgent research workflow. The search stages use Google Search; synthesis uses LeadReport; ExportAgent writes validated JSON and CSV.

## Run

From the repository root after setup and database initialization:

```powershell
.\.venv\Scripts\python.exe -m assignment run lead_generation
```

Try: `Find three US B2B SaaS leads for automated QA software. Ask me to confirm the profile first.`

Confirm the proposed profile in a second turn. Inspect the exported CSV/JSON and actual source URLs.

## Evidence and boundaries

Live search and Gemini access are required. No synthetic lead list is substituted on failure. Scores are model assessments, not verified purchase intent.

Generated traces/reports are in `artifacts/local/`. Watch the [assignment walkthrough videos on Google Drive](https://drive.google.com/drive/folders/1PsvdSfge91KUjwOJbUK7G3BqPK1wT3FH?usp=sharing). Follow [the execution guide](../../docs/EXECUTION.md) and [recording script](../../docs/VIDEO_SCRIPT.md). Reference projects and explicit adaptations are listed in [REFERENCES.md](../../docs/REFERENCES.md).

## Live validation

The November 1 live run exported one tentative lead. Exact headcount and QA buying intent remain unknown; the score gives no buying-signal points without evidence. Search callbacks preserve provider grounding metadata in session state and the parent trace. See the [report](../../artifacts/lead-report.json), [citation review](../../artifacts/lead-citation-review.json), and [search evidence](../../artifacts/lead-search-evidence.json). The final report followed a guided rerun after source and scoring issues were identified; future outputs still need review.
