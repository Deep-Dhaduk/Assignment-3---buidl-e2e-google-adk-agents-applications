import csv
import json
import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from assignment.config import artifact_dir


class Lead(BaseModel):
    company: str
    website: str
    fit_score: int = Field(ge=0, le=100)
    rationale: str
    sources: list[str] = Field(min_length=1)
    unknowns: list[str]

    @field_validator("website")
    @classmethod
    def website_is_http(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError("Website must be an HTTP(S) URL")
        return value

    @field_validator("sources")
    @classmethod
    def sources_are_http(cls, values: list[str]) -> list[str]:
        if any(not value.startswith(("https://", "http://")) for value in values):
            raise ValueError("Sources must be HTTP(S) URLs")
        return list(dict.fromkeys(values))


class LeadReport(BaseModel):
    target_profile: str
    methodology: str
    leads: list[Lead] = Field(max_length=20)
    limitations: list[str]


class ReviewFinding(BaseModel):
    severity: Literal["critical", "high", "medium", "low", "info"]
    file: str
    line: int = Field(ge=1)
    issue: str
    evidence: str
    suggested_fix: str


class ReviewReport(BaseModel):
    project: str
    summary: str
    findings: list[ReviewFinding]
    test_status: Literal["passed", "failed", "disabled", "unavailable", "timeout"]
    limitations: list[str]


def export_leads(raw: str | dict) -> dict:
    report = (
        LeadReport.model_validate_json(raw)
        if isinstance(raw, str)
        else LeadReport.model_validate(raw)
    )
    # Deduplicate domains; do not fabricate extra leads to fill the requested count.
    from urllib.parse import urlparse

    seen = set()
    unique = []
    for lead in report.leads:
        domain = urlparse(lead.website).netloc.lower().removeprefix("www.")
        if domain not in seen:
            unique.append(lead)
            seen.add(domain)
    report.leads = unique
    stem = artifact_dir() / f"leads-{uuid.uuid4().hex}"
    stem.with_suffix(".json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    with stem.with_suffix(".csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["company", "website", "fit_score", "rationale", "sources", "unknowns"])
        for lead in report.leads:
            cells = [
                lead.company,
                lead.website,
                str(lead.fit_score),
                lead.rationale,
                " | ".join(lead.sources),
                " | ".join(lead.unknowns),
            ]
            writer.writerow(
                [
                    "'" + cell if cell.lstrip().startswith(("=", "+", "-", "@")) else cell
                    for cell in cells
                ]
            )
    return {
        "status": "ok",
        "count": len(unique),
        "json": str(stem.with_suffix(".json")),
        "csv": str(stem.with_suffix(".csv")),
    }


def export_review(raw: str | dict) -> dict:
    report = (
        ReviewReport.model_validate_json(raw)
        if isinstance(raw, str)
        else ReviewReport.model_validate(raw)
    )
    path = artifact_dir() / f"review-report-{uuid.uuid4().hex}.json"
    path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
    return {"status": "ok", "json": str(path)}
