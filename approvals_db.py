import sqlite3
from datetime import datetime, timezone

APPROVALS_DB = "pending_approvals.sqlite"


def _connect():
    return sqlite3.connect(APPROVALS_DB)


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL UNIQUE,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                user_message TEXT,
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        conn.commit()


def save_pending(
    thread_id: str,
    recipient: str,
    subject: str,
    body: str,
    user_message: str = "",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO pending_approvals
                (thread_id, recipient, subject, body, user_message, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
            ON CONFLICT(thread_id) DO UPDATE SET
                recipient = excluded.recipient,
                subject = excluded.subject,
                body = excluded.body,
                user_message = excluded.user_message,
                status = 'PENDING',
                updated_at = ?
            """,
            (thread_id, recipient, subject, body, user_message, now, now),
        )
        conn.commit()


def get_pending_rows():
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, thread_id, recipient, subject, body, user_message, status, created_at
            FROM pending_approvals
            WHERE status = 'PENDING'
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def update_status(thread_id: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE pending_approvals
            SET status = ?, updated_at = ?
            WHERE thread_id = ? AND status = 'PENDING'
            """,
            (status, now, thread_id),
        )
        conn.commit()