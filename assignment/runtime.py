import asyncio
import importlib
import json
import uuid

from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.genai import types

from assignment.config import artifact_dir, data_dir
from assignment.sessions import SQLiteSessionService

AGENT_PACKAGES = {
    "lead_generation": "assignment_a_lead_generation",
    "gemini_cli_agent": "assignment_b_gemini_cli",
    "bug_assistant": "assignment_c_mcp_bug_assistant",
    "code_review": "assignment_d_code_review",
    "ecommerce": "assignment_e_ecommerce",
}
AGENTS = tuple(AGENT_PACKAGES)


def load_agent(name: str):
    if name not in AGENTS:
        raise ValueError("Unknown agent")
    return importlib.import_module(f"agents.{AGENT_PACKAGES[name]}.agent").root_agent


def pending_confirmations(events) -> dict:
    pending = {}
    for event in events:
        for call in event.get_function_calls():
            if call.name == "adk_request_confirmation":
                pending[call.id] = call.args
        for response in event.get_function_responses():
            if response.name == "adk_request_confirmation":
                pending.pop(response.id, None)
    return pending


async def run_turn(
    name: str,
    user_id: str,
    *,
    prompt: str = "",
    session_id: str | None = None,
    project: str = "buggy",
    confirmation_id: str | None = None,
    confirmed: bool = False,
) -> dict:
    agent = load_agent(name)
    sessions = SQLiteSessionService(data_dir() / "sessions.db")
    runner = Runner(agent=agent, app_name=name, session_service=sessions)
    try:
        if session_id:
            session = await sessions.get_session(
                app_name=name, user_id=user_id, session_id=session_id
            )
            if not session:
                raise ValueError("Session not found for this user and agent")
        else:
            if confirmation_id:
                raise ValueError("A confirmation requires an existing session")
            session = await sessions.create_session(
                app_name=name, user_id=user_id, state={"review_project": project}
            )
        if confirmation_id:
            pending = pending_confirmations(session.events)
            if confirmation_id not in pending:
                raise ValueError("No pending confirmation with this ID")
            payload = dict(pending[confirmation_id].get("toolConfirmation", {}))
            payload["confirmed"] = confirmed
            message = types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(
                            id=confirmation_id, name="adk_request_confirmation", response=payload
                        )
                    )
                ],
            )
        else:
            if not prompt.strip() or len(prompt) > 8000:
                raise ValueError("Prompt must contain 1–8000 characters")
            if pending_confirmations(session.events):
                raise ValueError(
                    "Approve or reject the pending action before sending another prompt"
                )
            message = types.Content(role="user", parts=[types.Part(text=prompt)])
        events = []
        texts = []
        async with asyncio.timeout(240):
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=message,
                run_config=RunConfig(max_llm_calls=18),
            ):
                events.append(event)
                if event.content:
                    texts.extend(part.text for part in event.content.parts or [] if part.text)
                if len(events) > 200:
                    raise RuntimeError("Event limit exceeded")
        trace = artifact_dir() / f"{name}-{uuid.uuid4().hex}.json"
        trace.write_text(
            json.dumps(
                [event.model_dump(mode="json", exclude_none=True) for event in events], indent=2
            ),
            encoding="utf-8",
        )
        session = await sessions.get_session(app_name=name, user_id=user_id, session_id=session.id)
        return {
            "agent": name,
            "session_id": session.id,
            "messages": texts,
            "confirmations": pending_confirmations(session.events),
            "trace": str(trace),
        }
    finally:
        await runner.close()
        await sessions.close()
