from nightwise.paths import DATA_DIR
"""Persistent community reports for the local NightWise prototype."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


DB_PATH = DATA_DIR / "community_reports.sqlite3"
REPORT_TYPES = {"sighting", "feedback"}


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS community_reports (
            report_id TEXT PRIMARY KEY,
            report_type TEXT NOT NULL,
            reported_at TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
    """)
    return connection


def save_report(report_type, payload):
    if report_type not in REPORT_TYPES:
        raise ValueError(f"Unsupported report type: {report_type}")

    report = dict(payload)
    report.update({
        "report_id": str(uuid4()),
        "reported_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ),
        "status": "Pending review",
    })

    connection = _connect()
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO community_reports
                    (report_id, report_type, reported_at, status, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report["report_id"],
                    report_type,
                    report["reported_at"],
                    report["status"],
                    json.dumps(report),
                ),
            )
    finally:
        connection.close()

    return report


def load_reports(report_type):
    if report_type not in REPORT_TYPES:
        raise ValueError(f"Unsupported report type: {report_type}")

    connection = _connect()
    try:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM community_reports
            WHERE report_type = ?
            ORDER BY reported_at, rowid
            """,
            (report_type,),
        ).fetchall()
    finally:
        connection.close()

    return [json.loads(row[0]) for row in rows]

def clear_reports():
    """Delete all saved wildlife sightings and lighting feedback."""
    connection = _connect()
    try:
        with connection:
            connection.execute("DELETE FROM community_reports")
    finally:
        connection.close()