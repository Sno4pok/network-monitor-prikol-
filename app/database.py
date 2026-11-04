import sqlite3
from datetime import datetime, timedelta

from app.checker import CheckResult

DB_PATH = "monitor.db"


def get_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # рядки як словники: row["name"]
    return conn


def init_db() -> None:
    """Create tables if they do not exist yet."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hosts (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL UNIQUE,
                target  TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checks (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id           INTEGER NOT NULL,
                checked_at        TEXT NOT NULL,
                is_up             INTEGER NOT NULL,
                response_time_ms  REAL,
                status_code       INTEGER,
                error             TEXT,
                FOREIGN KEY (host_id) REFERENCES hosts (id)
            )
            """
        )


def get_or_create_host(conn: sqlite3.Connection, name: str, target: str) -> int:
    """Return the id of a host, creating it if it does not exist."""
    row = conn.execute("SELECT id FROM hosts WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute(
        "INSERT INTO hosts (name, target) VALUES (?, ?)", (name, target)
    )
    return cursor.lastrowid


def save_results(results: list[CheckResult]) -> None:
    """Save a list of check results to the database."""
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        for r in results:
            host_id = get_or_create_host(conn, r.name, r.target)
            conn.execute(
                """
                INSERT INTO checks
                    (host_id, checked_at, is_up, response_time_ms, status_code, error)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (host_id, now, int(r.is_up), r.response_time_ms, r.status_code, r.error),
            )


def get_stats(hours: int = 24) -> list[dict]:
    """Uptime % and response times per host for the last N hours."""
    since = (datetime.now() - timedelta(hours=hours)).isoformat(timespec="seconds")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                h.name                                   AS name,
                COUNT(*)                                 AS total_checks,
                ROUND(100.0 * SUM(c.is_up) / COUNT(*), 1) AS uptime_percent,
                ROUND(AVG(c.response_time_ms), 1)        AS avg_response_ms,
                ROUND(MAX(c.response_time_ms), 1)        AS max_response_ms
            FROM checks c
            JOIN hosts h ON h.id = c.host_id
            WHERE c.checked_at >= ?
            GROUP BY h.id
            ORDER BY h.name
            """,
            (since,),
        ).fetchall()
    return [dict(row) for row in rows]