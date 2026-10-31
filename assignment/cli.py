import argparse
import asyncio
import importlib.metadata
import json
import os
import shutil
import sys

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from assignment import commerce
from assignment.config import ROOT, artifact_dir
from assignment.db import initialize
from assignment.mcp_client import server_parameters
from assignment.review import collect_review
from assignment.runtime import AGENTS, run_turn


def doctor() -> dict:
    return {
        "python": sys.version.split()[0],
        "google_adk": importlib.metadata.version("google-adk"),
        "mcp": importlib.metadata.version("mcp"),
        "gemini_key_configured": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
        "node_installed": bool(shutil.which("node")),
        "gemini_cli_installed": (ROOT / "node_modules/@google/gemini-cli/package.json").exists(),
        "docker_installed": bool(shutil.which("docker")),
        "review_execution": os.getenv("REVIEW_EXECUTION", "disabled"),
    }


async def mcp_smoke() -> dict:
    results = {}
    for domain, name, args in [
        ("bugs", "search_bugs", {"query": "quantity"}),
        ("catalog", "search_products", {"query": "running"}),
    ]:
        async with stdio_client(server_parameters(domain)) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                discovered = await session.list_tools()
                result = await session.call_tool(name, args)
                if result.isError:
                    raise RuntimeError(f"MCP {domain} tool call failed")
                results[domain] = {
                    "tools": [tool.name for tool in discovered.tools],
                    "result": result.model_dump(mode="json"),
                }
    return results


async def offline_demo() -> dict:
    initialize()
    quote = commerce.create_quote("demo-customer", "BALL-001", 1, "pickup")
    if quote["status"] != "confirmation_required":
        raise RuntimeError("Demo stock exhausted; use a fresh ADK_DATA_DIR")
    quote_id = quote["quote"]["id"]
    order = commerce.place_order("demo-customer", quote_id, confirmed=True)
    return {
        "mode": "LOCAL TOOL VERIFICATION — no model calls or web research",
        "mcp": await mcp_smoke(),
        "quote": quote,
        "unconfirmed": commerce.place_order("demo-customer", quote_id, confirmed=False),
        "order": order,
        "retry": commerce.place_order("demo-customer", quote_id, confirmed=True),
        "buggy_review": collect_review("buggy"),
        "fixed_review": collect_review("fixed"),
    }


async def chat(name: str, project: str):
    session_id = None
    pending = {}
    print("Enter a message; /quit exits. Pending actions require /approve or /reject.")
    while True:
        prompt = input("You> ").strip()
        if prompt == "/quit":
            return
        if not prompt:
            continue
        if pending:
            if prompt not in {"/approve", "/reject"}:
                print("Use /approve or /reject for the displayed action.")
                continue
            result = await run_turn(
                name,
                "local-user",
                session_id=session_id,
                confirmation_id=next(iter(pending)),
                confirmed=prompt == "/approve",
            )
        else:
            result = await run_turn(
                name, "local-user", prompt=prompt, session_id=session_id, project=project
            )
        session_id = result["session_id"]
        pending = result["confirmations"]
        for text in result["messages"]:
            print(text)
        if pending:
            print("Action awaiting your approval:", json.dumps(pending, indent=2))
        print("Saved trace:", result["trace"])


def main():
    parser = argparse.ArgumentParser(description="Five Google ADK applications")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "doctor", "mcp-smoke", "demo"):
        commands.add_parser(command)
    review = commands.add_parser("review")
    review.add_argument("project", choices=["buggy", "fixed"])
    run = commands.add_parser("run")
    run.add_argument("agent", choices=AGENTS)
    run.add_argument("--prompt")
    run.add_argument("--session")
    run.add_argument("--project", choices=["buggy", "fixed"], default="buggy")
    args = parser.parse_args()
    if args.command == "init":
        result = initialize()
    elif args.command == "doctor":
        result = doctor()
    elif args.command == "mcp-smoke":
        result = asyncio.run(mcp_smoke())
    elif args.command == "demo":
        result = asyncio.run(offline_demo())
        path = artifact_dir() / "local-demo.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        result = {"mode": result["mode"], "artifact": str(path)}
    elif args.command == "review":
        result = collect_review(args.project)
    elif args.prompt:
        result = asyncio.run(
            run_turn(
                args.agent,
                "local-user",
                prompt=args.prompt,
                session_id=args.session,
                project=args.project,
            )
        )
    else:
        asyncio.run(chat(args.agent, args.project))
        return
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
