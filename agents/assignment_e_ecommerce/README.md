# E — E-commerce assistant

MCP catalog → quote → explicit runtime confirmation → order → status/delivery.

## Code walkthrough

Start with [assignment_e_ecommerce.py](assignment_e_ecommerce.py), then [assignment/commerce.py](../../assignment/commerce.py). Catalog tools use MCP. Mutating Python tools receive identity through ADK ToolContext. Quotes expire, prices use integer cents, stock updates are atomic, and unique quote IDs make checkout retries idempotent.

## Run

From the repository root after setup and database initialization:

```powershell
.\.venv\Scripts\python.exe -m assignment run ecommerce
```

Try: `Find running shoes under 100 dollars, then prepare one SHOE-001 for standard delivery.`

Review the displayed quote, then use `/approve` or `/reject` for a pending action. Show order status after approval and the out-of-stock racket case.

## Evidence and boundaries

Demo orders only, no payments. SQLite is the tested backend; PostgreSQL/AlloyDB support is configurable but unverified here. Runtime approval is required for orders and delivery changes.

Generated traces/reports are in `artifacts/local/`. Watch the [assignment walkthrough videos on Google Drive](https://drive.google.com/drive/folders/1PsvdSfge91KUjwOJbUK7G3BqPK1wT3FH?usp=sharing). Follow [the execution guide](../../docs/EXECUTION.md). Reference projects and explicit adaptations are listed in [REFERENCES.md](../../docs/REFERENCES.md).
