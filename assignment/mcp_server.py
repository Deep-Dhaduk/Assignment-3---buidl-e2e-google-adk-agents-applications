"""Real MCP stdio service; stdout is reserved for the protocol."""

import argparse

from mcp.server.fastmcp import FastMCP

from assignment.bugs import get_bug, read_source, search_bugs
from assignment.catalog import get_product, search_products


def create_server(domain: str) -> FastMCP:
    server = FastMCP(f"assignment-{domain}")
    functions = (
        [search_bugs, get_bug, read_source] if domain == "bugs" else [search_products, get_product]
    )
    for function in functions:
        server.tool()(function)
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", choices=["bugs", "catalog"])
    create_server(parser.parse_args().domain).run(transport="stdio")
