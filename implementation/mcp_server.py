from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from db import SQLiteAdapter, ValidationError
from init_db import DB_PATH, create_database


if not Path(DB_PATH).exists():
    create_database(DB_PATH)

adapter = SQLiteAdapter(DB_PATH)
mcp = FastMCP("SQLite Lab MCP Server")


def _run_safely(callback):
    try:
        return callback()
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool(name="search")
def search(
    table: str,
    filters: dict[str, Any] | list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str | None = None,
    descending: bool = False,
) -> dict[str, Any]:
    """Search rows with validated filters, ordering, and pagination."""

    return _run_safely(lambda: adapter.search(table, columns, filters, limit, offset, order_by, descending))


@mcp.tool(name="insert")
def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Insert one row into a validated table and return the inserted payload."""

    return _run_safely(lambda: adapter.insert(table, values))


@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: str | None = None,
    filters: dict[str, Any] | list[dict[str, Any]] | None = None,
    group_by: str | list[str] | None = None,
) -> dict[str, Any]:
    """Run count, avg, sum, min, or max with optional filters and grouping."""

    return _run_safely(lambda: adapter.aggregate(table, metric, column, filters, group_by))


@mcp.resource("schema://database")
def database_schema() -> str:
    """Return the full SQLite database schema as JSON text."""

    return json.dumps(adapter.get_database_schema(), indent=2)


@mcp.resource("schema://table/{table_name}")
def table_schema(table_name: str) -> str:
    """Return one table schema as JSON text."""

    return _run_safely(lambda: json.dumps({table_name: adapter.get_table_schema(table_name)}, indent=2))


if __name__ == "__main__":
    mcp.run(show_banner=False)
