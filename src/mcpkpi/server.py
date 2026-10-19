"""MCP server entry point (stdio transport)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools
from .db import build_demo_db

mcp = FastMCP("kpi-server")
_con = build_demo_db()


@mcp.tool()
def list_tables() -> list[str]:
    """List the tables available to query."""
    return tools.list_tables(_con)


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """Return column names and types for a table."""
    return tools.describe_table(_con, table)


@mcp.tool()
def run_select(sql: str) -> dict:
    """Run a single read-only SELECT query (max 200 rows returned)."""
    return tools.run_select(_con, sql)


@mcp.tool()
def get_kpi(name: str) -> dict:
    """Compute a named KPI: completion_rate, avg_duration_min or visits_by_district."""
    return tools.kpi(_con, name)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
