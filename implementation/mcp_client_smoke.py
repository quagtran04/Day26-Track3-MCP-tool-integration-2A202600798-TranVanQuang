from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastmcp import Client


SERVER_PATH = Path(__file__).resolve().parent / "mcp_server.py"


def printable(value):
    if hasattr(value, "model_dump"):
        return printable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {key: printable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [printable(item) for item in value]
    if hasattr(value, "__dict__"):
        return printable(vars(value))
    return value


async def main() -> None:
    client = Client(str(SERVER_PATH))
    async with client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": {"cohort": "A1"},
                "order_by": "score",
                "descending": True,
                "limit": 2,
            },
        )
        schema_result = await client.read_resource("schema://table/students")

    print(json.dumps({"tools": [tool.name for tool in tools]}, indent=2))
    print(json.dumps({"resources": [str(resource.uri) for resource in resources]}, indent=2))
    print(json.dumps({"resource_templates": [str(template.uriTemplate) for template in templates]}, indent=2))
    print(json.dumps({"search_result": printable(search_result)}, indent=2))
    print(json.dumps({"schema_result": printable(schema_result)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
