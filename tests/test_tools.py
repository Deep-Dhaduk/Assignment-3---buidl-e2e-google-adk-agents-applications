import asyncio
import json
import sys

import pytest

from assignment.bugs import get_bug, read_source, search_bugs
from assignment.gemini_cli import gemini_cli
from assignment.process import execute
from assignment.reports import export_leads
from assignment.review import collect_review


def test_bug_evidence_and_traversal():
    assert "BUG-101" in [b["id"] for b in search_bugs("quantity")["bugs"]]
    assert get_bug("missing")["status"] == "not_found"
    assert "return price_cents" in read_source("buggy", "pricing.py")["source"]
    assert read_source("buggy", "../../.env")["status"] == "error"
    assert read_source("../../", "pricing.py")["status"] == "error"


def test_review_actual_failures_and_fix(monkeypatch):
    monkeypatch.setenv("REVIEW_EXECUTION", "trusted")
    buggy = collect_review("buggy")
    fixed = collect_review("fixed")
    assert buggy["tests"]["status"] == "failed"
    assert "ZeroDivisionError" in buggy["tests"]["stderr"]
    assert buggy["analysis"]["lint_findings"][0]["code"] == "F401"
    assert fixed["tests"]["status"] == "ok"
    assert fixed["analysis"]["lint_findings"] == []


def test_review_execution_defaults_off():
    assert collect_review("buggy")["tests"]["status"] == "disabled"
    assert collect_review("../../")["status"] == "error"


def test_subprocess_timeout(tmp_path):
    result = execute(
        [sys.executable, "-c", "import time; time.sleep(10)"], cwd=str(tmp_path), timeout=1
    )
    assert result["status"] == "timeout"


def test_cli_missing_key_is_not_fake_success(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert asyncio.run(gemini_cli("Analyze code", "buggy"))["status"] == "unavailable"
    assert asyncio.run(gemini_cli("Analyze code", "../"))["status"] == "error"


def test_lead_export_validation_dedup_and_csv_injection(tmp_path):
    lead = {
        "company": "=SUM(1,2)",
        "website": "https://example.com",
        "fit_score": 40,
        "rationale": "Industry match only",
        "sources": ["https://example.com/about"],
        "unknowns": ["Buying intent"],
    }
    report = {
        "target_profile": "Synthetic test",
        "methodology": "Unit test; not live research",
        "leads": [lead, lead],
        "limitations": ["Synthetic"],
    }
    result = export_leads(report)
    assert result["count"] == 1
    from pathlib import Path

    assert "'=SUM" in Path(result["csv"]).read_text(encoding="utf-8")
    assert len(json.loads(Path(result["json"]).read_text())["leads"]) == 1
    lead["sources"] = ["javascript:alert(1)"]
    with pytest.raises(ValueError):
        export_leads(report)
