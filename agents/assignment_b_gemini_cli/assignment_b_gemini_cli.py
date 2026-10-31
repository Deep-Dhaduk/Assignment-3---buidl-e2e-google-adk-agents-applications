"""Assignment B: Gemini CLI as an ADK tool."""

from google.adk.agents import LlmAgent, SequentialAgent

from assignment.config import model_name
from assignment.gemini_cli import gemini_cli

root_agent = SequentialAgent(
    name="gemini_cli_agent",
    sub_agents=[
        LlmAgent(
            name="task_planner",
            model=model_name(),
            output_key="cli_plan",
            instruction="Turn the user's request into one concise plain-language analysis task for the gemini_cli tool. The available projects are buggy and fixed; use buggy unless specified. These projects contain only pricing.py and test_pricing.py. Scope the task to that source bundle, including the evidence and proposed tests needed. Do not invent UI, payment, or shipping code. Do not output shell commands, CLI subcommands, or flags: the tool wrapper supplies the actual invocation. Do not claim you have executed anything.",
        ),
        LlmAgent(
            name="cli_executor",
            model=model_name(),
            tools=[gemini_cli],
            output_key="cli_result",
            instruction="Execute this plan by calling gemini_cli exactly once: {cli_plan}. Pass the selected registered project and task. Preserve the tool's response, exit_code, status and duration. Do not substitute your own answer for a failed CLI invocation.",
        ),
        LlmAgent(
            name="result_explainer",
            model=model_name(),
            instruction="Explain this actual CLI result: {cli_result}. State whether the CLI succeeded and its reported exit code. If it failed, give the reported error and setup step; never present a simulated result. On success summarize evidenced findings and label any proposed tests as 'Suggested tests (not executed)'. Explicitly state that the CLI analyzed source only and did not execute tests. Never label a test plan or predicted outcomes as verified test execution. Actual test execution belongs to the separate code_review application. Keep the explanation concise and do not invent CLI commands or file paths.",
        ),
    ],
)
