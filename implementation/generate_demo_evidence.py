from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastmcp import Client
from fastmcp.exceptions import ToolError


BASE_DIR = Path(__file__).resolve().parent
SERVER_PATH = BASE_DIR / "mcp_server.py"
OUTPUT_PATH = BASE_DIR.parent / "demo" / "mcp-client-evidence.md"


def as_jsonable(value):
    if hasattr(value, "model_dump"):
        return as_jsonable(value.model_dump(mode="json"))
    if isinstance(value, dict):
        return {key: as_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return as_jsonable(vars(value))
    return value


def block(title: str, payload) -> str:
    return f"## {title}\n\n```json\n{json.dumps(as_jsonable(payload), indent=2)}\n```\n"


async def main() -> None:
    client = Client(str(SERVER_PATH))
    async with client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()
        database_schema = await client.read_resource("schema://database")
        table_schema = await client.read_resource("schema://table/students")
        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": {"cohort": "A1"},
                "order_by": "score",
                "descending": True,
            },
        )
        aggregate_result = await client.call_tool(
            "aggregate",
            {
                "table": "students",
                "metric": "avg",
                "column": "score",
                "group_by": "cohort",
            },
        )
        try:
            invalid_result = await client.call_tool("search", {"table": "missing_table"})
        except ToolError as exc:
            invalid_result = {"is_error": True, "message": str(exc)}

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            "# MCP Client Evidence",
            "",
            block("Discovered Tools", [tool.name for tool in tools]),
            block("Discovered Resources", [str(resource.uri) for resource in resources]),
            block("Discovered Resource Templates", [str(template.uriTemplate) for template in templates]),
            block("Read schema://database", database_schema),
            block("Read schema://table/students", table_schema),
            block("Call search", search_result),
            block("Call aggregate", aggregate_result),
            block("Call invalid table", invalid_result),
        ]
    )
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote evidence to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
