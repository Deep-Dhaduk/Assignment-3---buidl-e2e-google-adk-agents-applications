import json

import pytest
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.events import Event, EventActions
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import FunctionTool
from google.genai import types

from agents.assignment_e_ecommerce.agent import confirm_order
from assignment import commerce, runtime
from assignment.catalog import get_product
from assignment.mcp_client import toolset
from assignment.sessions import SQLiteSessionService
from assignment.workflows import ExportAgent, ReviewEvidenceAgent


class ScriptedModel(BaseLlm):
    """Deterministic test double; never presented as a live Gemini execution."""

    replies: list[types.Content]

    async def generate_content_async(self, llm_request, stream=False):
        assert self.replies, "Unexpected extra model call"
        yield LlmResponse(content=self.replies.pop(0))


def text_reply(text):
    return types.Content(role="model", parts=[types.Part(text=text)])


async def test_session_persists_identity_state_and_temp_scope(tmp_path):
    service = SQLiteSessionService(tmp_path / "sessions.db")
    session = await service.create_session(app_name="test", user_id="alice")
    await service.append_event(
        session,
        Event(
            author="test",
            actions=EventActions(state_delta={"result": 42, "temp:secret": "ephemeral"}),
        ),
    )
    reopened = SQLiteSessionService(tmp_path / "sessions.db")
    restored = await reopened.get_session(app_name="test", user_id="alice", session_id=session.id)
    assert restored.state == {"result": 42}
    assert len(restored.events) == 1
    assert await reopened.get_session(app_name="test", user_id="bob", session_id=session.id) is None
    stale = restored.model_copy(deep=True)
    await reopened.append_event(restored, Event(author="test"))
    with pytest.raises(ValueError, match="Session changed"):
        await reopened.append_event(stale, Event(author="test"))


@pytest.mark.parametrize("approved", [False, True])
async def test_real_adk_confirmation_roundtrip(monkeypatch, approved):
    quote = commerce.create_quote("alice", "BALL-001", 1, "pickup")["quote"]
    call = types.Content(
        role="model",
        parts=[
            types.Part(
                function_call=types.FunctionCall(
                    name="confirm_order", args={"quote_id": quote["id"]}
                )
            )
        ],
    )
    model = ScriptedModel(model="test-only", replies=[call, text_reply("Action processed.")])
    agent = LlmAgent(
        name="ecommerce",
        model=model,
        tools=[FunctionTool(confirm_order, require_confirmation=True)],
    )
    monkeypatch.setattr(runtime, "load_agent", lambda _: agent)
    first = await runtime.run_turn("ecommerce", "alice", prompt="Place this order")
    assert len(first["confirmations"]) == 1
    assert get_product("BALL-001")["product"]["stock"] == 20
    confirmation_id = next(iter(first["confirmations"]))
    with pytest.raises(ValueError, match="Session not found"):
        await runtime.run_turn(
            "ecommerce",
            "bob",
            session_id=first["session_id"],
            confirmation_id=confirmation_id,
            confirmed=True,
        )
    second = await runtime.run_turn(
        "ecommerce",
        "alice",
        session_id=first["session_id"],
        confirmation_id=confirmation_id,
        confirmed=approved,
    )
    assert not second["confirmations"]
    assert get_product("BALL-001")["product"]["stock"] == (19 if approved else 20)
    with pytest.raises(ValueError, match="No pending confirmation"):
        await runtime.run_turn(
            "ecommerce",
            "alice",
            session_id=first["session_id"],
            confirmation_id=confirmation_id,
            confirmed=True,
        )


async def test_review_pipeline_exports_structured_output(monkeypatch):
    report = {
        "project": "fixed",
        "summary": "Scripted test response",
        "findings": [],
        "test_status": "disabled",
        "limitations": ["Tests disabled", "Model is a test double"],
    }
    model = ScriptedModel(model="test-only", replies=[text_reply(json.dumps(report))])
    agent = SequentialAgent(
        name="code_review",
        sub_agents=[
            ReviewEvidenceAgent(name="evidence"),
            LlmAgent(name="summarizer", model=model, output_key="review_report"),
            ExportAgent(name="export", report_kind="review", state_key="review_report"),
        ],
    )
    monkeypatch.setattr(runtime, "load_agent", lambda _: agent)
    result = await runtime.run_turn("code_review", "alice", prompt="Review", project="fixed")
    from pathlib import Path

    trace = json.loads(Path(result["trace"]).read_text())
    assert any(event["author"] == "evidence" for event in trace)
    exported = json.loads(result["messages"][-1])
    assert exported["status"] == "ok"
    assert Path(exported["json"]).exists()


async def test_adk_invokes_mcp_and_reopens_after_cleanup(monkeypatch):
    call = types.Content(
        role="model",
        parts=[
            types.Part(function_call=types.FunctionCall(name="get_bug", args={"bug_id": "BUG-101"}))
        ],
    )
    model = ScriptedModel(
        model="test-only",
        replies=[call, text_reply("First diagnosis"), call, text_reply("Second diagnosis")],
    )
    agent = LlmAgent(name="bug_assistant", model=model, tools=[toolset("bugs")])
    monkeypatch.setattr(runtime, "load_agent", lambda _: agent)
    from pathlib import Path

    for _ in range(2):
        result = await runtime.run_turn("bug_assistant", "alice", prompt="Investigate quantity")
        trace = Path(result["trace"]).read_text()
        assert "Checkout total ignores quantity" in trace
