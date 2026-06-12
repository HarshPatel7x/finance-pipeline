"""Real stdio round-trip against the MCP server — exercised, not theatre.

Spawns mcp_server.server as a subprocess and speaks actual JSON-RPC over stdio
via the SDK's own client: initialize -> tools/list -> tools/call. Asserts the
keyword path only, so the test needs no API key and no AWS credentials.
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parent.parent


async def _roundtrip() -> tuple:
    params = StdioServerParameters(
        command=sys.executable,  # the python running pytest — has mcp installed
        args=["-m", "mcp_server.server"],
        cwd=str(REPO_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            call = await session.call_tool(
                "categorize", {"name": "STARBUCKS #123", "merchant": "Starbucks"}
            )
    return tools, call


def test_mcp_stdio_roundtrip():
    tools, call = asyncio.run(asyncio.wait_for(_roundtrip(), timeout=30))

    # tools/list: exactly one tool, with a generated JSON Schema definition
    names = [t.name for t in tools.tools]
    assert names == ["categorize"]
    schema = tools.tools[0].inputSchema
    assert schema["type"] == "object"
    assert "name" in schema["properties"]
    assert schema["required"] == ["name"]

    # tools/call: the keyword rule fires — no API key involved
    assert not call.isError
    result = call.structuredContent
    assert result["category"] == "Food & Drink"
    assert result["source"] == "keyword"
    assert result["input_tokens"] == 0 and result["output_tokens"] == 0
