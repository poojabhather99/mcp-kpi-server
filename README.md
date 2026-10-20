# mcp-kpi-server

[![CI](https://github.com/poojabhather99/mcp-kpi-server/actions/workflows/ci.yml/badge.svg)](https://github.com/poojabhather99/mcp-kpi-server/actions/workflows/ci.yml)

**Live demo (runs in your browser):** https://poojabhather99.github.io/mcp-kpi-server/

A [Model Context Protocol](https://modelcontextprotocol.io) server that lets an LLM client (Claude Desktop, Claude Code, or any MCP client) query an analytical database through a small set of safe, read-only tools.

The demo database is **synthetic** (health-worker visits across four districts, generated deterministically with a seed). No real data is included.

## Tools

| Tool | Purpose |
|---|---|
| `list_tables` | Tables available to query |
| `describe_table(table)` | Column names and types |
| `run_select(sql)` | Run one read-only SELECT (max 200 rows, flagged if truncated) |
| `get_kpi(name)` | Named KPIs: `completion_rate`, `avg_duration_min`, `visits_by_district` |

## Safety model

`run_select` accepts a single statement that starts with `SELECT` or `WITH` and contains none of the write/DDL/IO keywords (`insert`, `update`, `delete`, `drop`, `alter`, `create`, `attach`, `copy`, `pragma`, `call`, `install`, `load`, `export`, `set`). Multiple statements and unknown table names are rejected, and results are capped at 200 rows.

This is a keyword guard, not a sandbox. It will also reject a harmless query whose text contains one of those words, for example a column called `set`. For anything beyond a demo, run the server against a read-only database user or a read-only DuckDB file, and treat the guard as a second layer.

## Run

```bash
pip install -e ".[dev]"
mcp-kpi-server          # stdio transport
pytest -q               # 19 tests
```

Claude Desktop config:

```json
{
  "mcpServers": {
    "kpi": { "command": "mcp-kpi-server" }
  }
}
```

## Layout

- `src/mcpkpi/tools.py`: tool logic and the SQL guard, independent of MCP so it is unit tested directly
- `src/mcpkpi/server.py`: thin FastMCP wrapper registering the four tools
- `src/mcpkpi/db.py`: seeded demo dataset
- `tests/`: guard cases, row cap, JSON-safe dates, KPI checks, tool registration

## Limitations

- Pinned to `mcp<2` (the v1 `FastMCP` API); v2 renamed it.
- Demo data only; swapping in a real database means replacing `db.py` and the `KPIS` queries.
- Tested through the tool layer and tool registration, not against a live MCP client session.
