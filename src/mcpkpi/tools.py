"""Tool logic, independent of the MCP transport so it can be unit tested."""

from __future__ import annotations

import re
from typing import Any

import duckdb

MAX_ROWS = 200
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|copy|pragma|call|install|load|export|set)\b",
    re.IGNORECASE,
)

KPIS = {
    "completion_rate": (
        "Share of visits completed",
        "SELECT ROUND(AVG((status = 'completed')::INT), 3) AS completion_rate FROM visits",
    ),
    "avg_duration_min": (
        "Mean duration of completed visits (minutes)",
        "SELECT ROUND(AVG(duration_min), 1) AS avg_duration_min FROM visits "
        "WHERE status = 'completed'",
    ),
    "visits_by_district": (
        "Visit counts and completion rate per district",
        "SELECT w.district, COUNT(*) AS visits, "
        "ROUND(AVG((v.status = 'completed')::INT), 3) AS completion_rate "
        "FROM visits v JOIN workers w USING (worker_id) GROUP BY 1 ORDER BY 1",
    ),
}


class QueryRejected(ValueError):
    """Raised when SQL is not a single read-only SELECT."""


def validate_select(sql: str) -> str:
    """Return cleaned SQL if it is a single read-only SELECT/WITH, else raise."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise QueryRejected("empty query")
    if ";" in cleaned:
        raise QueryRejected("multiple statements are not allowed")
    if not re.match(r"^(select|with)\b", cleaned, re.IGNORECASE):
        raise QueryRejected("only SELECT queries are allowed")
    if _FORBIDDEN.search(cleaned):
        raise QueryRejected("query contains a forbidden keyword")
    return cleaned


def _rows(cur: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    cols = [d[0] for d in cur.description]
    data = cur.fetchmany(MAX_ROWS + 1)
    truncated = len(data) > MAX_ROWS
    data = data[:MAX_ROWS]
    return {
        "columns": cols,
        "rows": [[str(v) if hasattr(v, "isoformat") else v for v in r] for r in data],
        "truncated": truncated,
    }


def list_tables(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [r[0] for r in con.execute("SHOW TABLES").fetchall()]


def describe_table(con: duckdb.DuckDBPyConnection, table: str) -> list[dict[str, str]]:
    if table not in list_tables(con):
        raise QueryRejected(f"unknown table: {table}")
    info = con.execute(f"DESCRIBE {table}").fetchall()
    return [{"column": r[0], "type": r[1]} for r in info]


def run_select(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, Any]:
    return _rows(con.execute(validate_select(sql)))


def kpi(con: duckdb.DuckDBPyConnection, name: str) -> dict[str, Any]:
    if name not in KPIS:
        raise QueryRejected(f"unknown KPI '{name}'. Available: {sorted(KPIS)}")
    description, sql = KPIS[name]
    return {"kpi": name, "description": description, **_rows(con.execute(sql))}
