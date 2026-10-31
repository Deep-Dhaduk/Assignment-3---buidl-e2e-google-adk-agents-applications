from sqlalchemy import or_, select

from assignment.config import sample_project
from assignment.db import bugs, engine


def search_bugs(query: str) -> dict:
    """Find seeded internal bug tickets by words in title or description."""
    words = query.split()[:8]
    if not words or len(query) > 300:
        return {"status": "error", "message": "Supply a short search query"}
    clauses = []
    for word in words:
        pattern = "%" + word.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
        clauses.extend(
            [bugs.c.title.ilike(pattern, escape="!"), bugs.c.description.ilike(pattern, escape="!")]
        )
    with engine().connect() as conn:
        rows = conn.execute(select(bugs).where(or_(*clauses)).limit(10)).mappings()
        return {"status": "ok", "bugs": [dict(row) for row in rows]}


def get_bug(bug_id: str) -> dict:
    """Read one bug ticket, preserving its ID as an evidence citation."""
    with engine().connect() as conn:
        row = conn.execute(select(bugs).where(bugs.c.id == bug_id)).mappings().first()
        return {"status": "ok", "bug": dict(row)} if row else {"status": "not_found"}


def read_source(project: str, filename: str) -> dict:
    """Read an allowlisted sample file, with line numbers, without executing it."""
    if filename not in {"pricing.py", "test_pricing.py"}:
        return {"status": "error", "message": "Only pricing.py and test_pricing.py are available"}
    try:
        root = sample_project(project)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    path = root / filename
    if path.is_symlink() or path.resolve().parent != root:
        return {"status": "error", "message": "Source path is outside the sample project"}
    lines = path.read_text(encoding="utf-8").splitlines()
    return {
        "status": "ok",
        "file": filename,
        "project": project,
        "source": "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1)),
    }
