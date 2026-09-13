from __future__ import annotations

import asyncio

from mcp import Client

from reliability_lab.server import mcp


def test_mcp_server_exposes_real_tools() -> None:
    async def scenario() -> None:
        async with Client(mcp) as client:
            result = await client.list_tools()
            names = {tool.name for tool in result.tools}
            assert {
                "route_technical_request",
                "inspect_prompt",
                "score_ai_output",
                "reliability_metrics",
            } <= names

            result = await client.call_tool(
                "inspect_prompt",
                {"prompt_id": "technical_review"},
            )
            assert result.structured_content["version"] == "1.1.0"

    asyncio.run(scenario())
