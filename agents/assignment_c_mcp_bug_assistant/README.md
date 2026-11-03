# C — MCP bug assistance

User symptoms → MCP ticket search → ticket/source evidence → diagnosis.

## Code walkthrough

Start with [assignment_c_mcp_bug_assistant.py](assignment_c_mcp_bug_assistant.py), then [assignment/mcp_server.py](../../assignment/mcp_server.py). McpToolset launches the Python MCP stdio server with the bugs domain. The server exposes search_bugs, get_bug and read_source. Queries are parameterized and source files are allowlisted.

## Run

From the repository root after setup and database initialization:

```powershell
.\.venv\Scripts\python.exe -m assignment run bug_assistant
```

Try: `Why does checkout charge for one item when the quantity is three?`

Inspect the returned trace to see actual tool calls and responses.

## Evidence and boundaries

Seeded local tickets are used instead of live GitHub issues. Tools are read-only. The assistant proposes fixes and tests but cannot claim to have applied them.

Generated traces/reports are in `artifacts/local/`. Watch the [assignment walkthrough videos on Google Drive](https://drive.google.com/drive/folders/1PsvdSfge91KUjwOJbUK7G3BqPK1wT3FH?usp=sharing). Follow [the execution guide](../../docs/EXECUTION.md) and [recording script](../../docs/VIDEO_SCRIPT.md). Reference projects and explicit adaptations are listed in [REFERENCES.md](../../docs/REFERENCES.md).
