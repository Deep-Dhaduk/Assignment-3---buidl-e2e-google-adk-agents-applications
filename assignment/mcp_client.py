import os
import sys

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from assignment.config import ROOT, database_url


def server_parameters(domain: str) -> StdioServerParameters:
    env = {
        name: os.environ[name]
        for name in ("PATH", "SystemRoot", "SYSTEMROOT", "TEMP", "TMP")
        if name in os.environ
    }
    env["DATABASE_URL"] = database_url()
    return StdioServerParameters(
        command=sys.executable, args=["-m", "assignment.mcp_server", domain], cwd=str(ROOT), env=env
    )


def toolset(domain: str) -> McpToolset:
    names = (
        ["search_bugs", "get_bug", "read_source"]
        if domain == "bugs"
        else ["search_products", "get_product"]
    )
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=server_parameters(domain), timeout=30
        ),
        tool_filter=names,
    )
