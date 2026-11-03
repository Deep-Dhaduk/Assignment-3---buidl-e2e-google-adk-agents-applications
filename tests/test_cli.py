import httpx
import pytest
from google import genai
from google.adk.events import Event
from google.genai import types
from google.genai.errors import APIError, ServerError

from assignment import cli
from assignment.config import data_dir, model_with_retries
from assignment.sessions import SQLiteSessionService


@pytest.mark.parametrize("status,recovers,expected_calls", [(503, True, 2), (503, False, 4), (429, False, 1)])
def test_model_http_retries_are_bounded(status, recovers, expected_calls):
    calls = []

    def handle(request):
        calls.append(request)
        if recovers and len(calls) > 1:
            return httpx.Response(
                200, json={"candidates": [{"content": {"parts": [{"text": "Recovered"}]}}]}
            )
        return httpx.Response(status, json={"error": {"code": status, "message": "Temporary"}})

    retry = model_with_retries().retry_options.model_copy(
        update={"initial_delay": 0, "max_delay": 0, "jitter": 0}
    )
    with genai.Client(
        api_key="synthetic-test-key",
        vertexai=False,
        http_options=types.HttpOptions(
            retry_options=retry, client_args={"transport": httpx.MockTransport(handle)}
        ),
    ) as client:
        if recovers:
            assert client.models.generate_content(model="test", contents="test").text == "Recovered"
        else:
            with pytest.raises(APIError):
                client.models.generate_content(model="test", contents="test")
    assert len(calls) == expected_calls


async def test_cli_error_is_concise_and_does_not_replay_workflow(monkeypatch, capsys):
    calls = []

    async def unavailable(*args, **kwargs):
        calls.append(kwargs)
        raise ServerError(503, {"error": {"message": "private-diagnostic-value"}})

    monkeypatch.setattr(cli, "run_turn", unavailable)
    with pytest.raises(SystemExit) as exc:
        await cli.run_turn_cli(
            "lead_generation", "local-user", session_id="saved-session", prompt="Confirmed"
        )
    assert exc.value.code == 1
    output = capsys.readouterr().err
    assert "HTTP 503" in output and "--session saved-session" in output
    assert "private-diagnostic-value" not in output and "Traceback" not in output
    assert len(calls) == 1


async def test_chat_resume_restores_pending_confirmation(monkeypatch):
    service = SQLiteSessionService(data_dir() / "sessions.db")
    session = await service.create_session(app_name="ecommerce", user_id="local-user")
    await service.append_event(
        session,
        Event(
            author="ecommerce",
            content=types.Content(
                role="model",
                parts=[types.Part(function_call=types.FunctionCall(
                    id="pending-action", name="adk_request_confirmation", args={}
                ))],
            ),
        ),
    )
    await service.close()
    entered = iter(["/approve", "/quit"])
    calls = []

    async def complete(*args, **kwargs):
        calls.append(kwargs)
        return {"session_id": session.id, "confirmations": {}, "messages": [], "trace": "test"}

    monkeypatch.setattr("builtins.input", lambda _: next(entered))
    monkeypatch.setattr(cli, "run_turn", complete)
    await cli.chat("ecommerce", "buggy", session.id)
    assert len(calls) == 1
    assert calls[0]["session_id"] == session.id
    assert calls[0]["confirmation_id"] == "pending-action"
    assert calls[0]["confirmed"] is True
