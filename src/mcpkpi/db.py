"""Database setup: a deterministic synthetic health-worker visits dataset."""

from __future__ import annotations

import random
from datetime import date, timedelta

import duckdb

DISTRICTS = ["North", "South", "East", "West"]
STATUSES = ["completed", "completed", "completed", "missed", "rescheduled"]


def build_demo_db(n_visits: int = 500, seed: int = 11) -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB with `workers` and `visits` tables."""
    rng = random.Random(seed)
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE workers (worker_id INTEGER, name VARCHAR, district VARCHAR)")
    con.execute(
        "CREATE TABLE visits (visit_id INTEGER, worker_id INTEGER, visit_date DATE,"
        " status VARCHAR, duration_min INTEGER)"
    )
    workers = [(i, f"Worker {i}", DISTRICTS[i % len(DISTRICTS)]) for i in range(1, 21)]
    con.executemany("INSERT INTO workers VALUES (?, ?, ?)", workers)
    start = date(2026, 1, 1)
    rows = []
    for vid in range(1, n_visits + 1):
        status = rng.choice(STATUSES)
        dur = rng.randint(10, 60) if status == "completed" else 0
        rows.append(
            (vid, rng.randint(1, 20), start + timedelta(days=rng.randint(0, 89)), status, dur)
        )
    con.executemany("INSERT INTO visits VALUES (?, ?, ?, ?, ?)", rows)
    return con
