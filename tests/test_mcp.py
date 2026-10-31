from mcp import ClientSession
from mcp.client.stdio import stdio_client

from assignment.mcp_client import server_parameters, toolset


async def test_real_mcp_bug_server():
    async with stdio_client(server_parameters("bugs")) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {"search_bugs", "get_bug", "read_source"}
            result = await session.call_tool("get_bug", {"bug_id": "BUG-101"})
            assert not result.isError
            assert "Checkout total ignores quantity" in result.content[0].text
            invalid = await session.call_tool(
                "read_source", {"project": "buggy", "filename": "../.env"}
            )
            assert "Only pricing.py" in invalid.content[0].text


async def test_adk_discovers_real_mcp_catalog_tools():
    tools = toolset("catalog")
    try:
        discovered = await tools.get_tools()
        assert {tool.name for tool in discovered} == {"search_products", "get_product"}
    finally:
        await tools.close()
