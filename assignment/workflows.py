"""Deterministic workflow stages surrounding the model's interpretation."""

import asyncio
import json
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from assignment.reports import export_leads, export_review
from assignment.review import collect_review


def record_search_grounding(callback_context: CallbackContext, llm_response: LlmResponse) -> None:
    """Keep provider search evidence when AgentTool hides its nested agent events."""
    if llm_response.grounding_metadata:
        records = list(callback_context.state.get("lead_search_evidence", []))
        records.append(
            {
                "agent": callback_context.agent_name,
                "grounding": llm_response.grounding_metadata.model_dump(
                    mode="json", exclude_none=True
                ),
            }
        )
        callback_context.state["lead_search_evidence"] = records


class ReviewEvidenceAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        project = ctx.session.state.get("review_project", "buggy")
        result = await asyncio.to_thread(collect_review, project)
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(result))]),
            actions=EventActions(state_delta={"review_evidence": json.dumps(result)}),
        )


class ExportAgent(BaseAgent):
    report_kind: str
    state_key: str

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        raw = ctx.session.state.get(self.state_key)
        try:
            result = export_leads(raw) if self.report_kind == "leads" else export_review(raw)
        except (ValueError, TypeError) as exc:
            result = {"status": "invalid_report", "message": str(exc)[:1000]}
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=json.dumps(result))]),
            actions=EventActions(state_delta={f"{self.report_kind}_artifacts": result}),
        )
