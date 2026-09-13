from __future__ import annotations

import sqlite3
from pathlib import Path


class RunStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    prompt_id TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    used_fallback INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    estimated_cost_usd REAL NOT NULL,
                    evaluation_score REAL NOT NULL
                )
                """
            )

    def record(self, **values: object) -> int:
        columns = (
            "prompt_id",
            "prompt_version",
            "provider",
            "used_fallback",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "estimated_cost_usd",
            "evaluation_score",
        )
        with self._connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO runs ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                tuple(values[column] for column in columns),
            )
            return int(cursor.lastrowid)

    def metrics(self) -> dict[str, object]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS run_count,
                    ROUND(AVG(latency_ms), 2) AS average_latency_ms,
                    ROUND(SUM(estimated_cost_usd), 6) AS estimated_cost_usd,
                    ROUND(AVG(evaluation_score), 3) AS average_evaluation_score,
                    SUM(used_fallback) AS fallback_count
                FROM runs
                """
            ).fetchone()
        return dict(row) if row else {}

