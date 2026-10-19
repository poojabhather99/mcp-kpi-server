import pytest

from mcpkpi import tools
from mcpkpi.db import build_demo_db


@pytest.fixture(scope="module")
def con():
    return build_demo_db()


def test_demo_db_is_deterministic():
    a = build_demo_db().execute("SELECT SUM(duration_min) FROM visits").fetchone()
    b = build_demo_db().execute("SELECT SUM(duration_min) FROM visits").fetchone()
    assert a == b


def test_list_tables(con):
    assert sorted(tools.list_tables(con)) == ["visits", "workers"]


def test_describe_table(con):
    cols = {c["column"] for c in tools.describe_table(con, "visits")}
    assert {"visit_id", "status", "duration_min"} <= cols


def test_describe_unknown_table(con):
    with pytest.raises(tools.QueryRejected):
        tools.describe_table(con, "nope; DROP TABLE visits")


def test_select_ok(con):
    out = tools.run_select(con, "SELECT COUNT(*) AS n FROM visits;")
    assert out["columns"] == ["n"] and out["rows"] == [[500]]


def test_with_cte_ok(con):
    out = tools.run_select(con, "WITH x AS (SELECT 1 AS a) SELECT a FROM x")
    assert out["rows"] == [[1]]


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE visits",
        "DELETE FROM visits",
        "SELECT 1; DROP TABLE visits",
        "INSERT INTO visits VALUES (1,1,'2026-01-01','x',1)",
        "COPY visits TO '/tmp/x.csv'",
        "",
        "PRAGMA database_list",
        "SELECT * FROM visits; SELECT 1",
    ],
)
def test_rejects_unsafe(con, sql):
    with pytest.raises(tools.QueryRejected):
        tools.run_select(con, sql)


def test_row_cap_and_truncation(con):
    out = tools.run_select(con, "SELECT * FROM visits")
    assert len(out["rows"]) == tools.MAX_ROWS and out["truncated"] is True


def test_dates_are_json_safe(con):
    out = tools.run_select(con, "SELECT visit_date FROM visits LIMIT 1")
    assert isinstance(out["rows"][0][0], str)


def test_kpis_run(con):
    for name in tools.KPIS:
        out = tools.kpi(con, name)
        assert out["rows"]
    rate = tools.kpi(con, "completion_rate")["rows"][0][0]
    assert 0 < rate < 1


def test_unknown_kpi(con):
    with pytest.raises(tools.QueryRejected):
        tools.kpi(con, "revenue")


def test_server_registers_tools():
    import asyncio

    from mcpkpi.server import mcp

    names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert names == {"list_tables", "describe_table", "run_select", "get_kpi"}
