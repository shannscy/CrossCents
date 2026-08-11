"""Lightweight persistence for the prototype's mock ledger.

Plain sqlite3 (stdlib, no new dependency) — enough to make transactions and
audit events survive a restart and be queried simply. Not a real accounting
system: no double-entry, no concurrency tuning, no migrations framework.
Swap for a real database when this stops being a demo.
"""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "crosscents.db"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                owner_user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                memo TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                event TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bank_accounts (
                user_id TEXT PRIMARY KEY,
                account_holder TEXT NOT NULL,
                account_number_masked TEXT NOT NULL,
                linked_at TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_transaction(
    owner_user_id: str,
    type_: str,
    sender: str,
    recipient: str,
    amount: float,
    currency: str,
    status: str,
    memo: str | None = None,
) -> dict:
    tx_id = str(uuid.uuid4())
    created_at = _now()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO transactions (id, owner_user_id, type, sender, recipient, amount, currency, status, memo, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tx_id, owner_user_id, type_, sender, recipient, amount, currency, status, memo, created_at),
        )
    return {
        "id": tx_id,
        "type": type_,
        "sender": sender,
        "recipient": recipient,
        "amount": amount,
        "currency": currency,
        "status": status,
        "memo": memo,
        "created_at": created_at,
    }


def list_transactions(owner_user_id: str, type_: str | None = None) -> list[dict]:
    with _connect() as conn:
        if type_:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE owner_user_id = ? AND type = ? ORDER BY created_at DESC",
                (owner_user_id, type_),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE owner_user_id = ? ORDER BY created_at DESC",
                (owner_user_id,),
            ).fetchall()
    return [dict(row) for row in rows]


def sum_completed_amount(owner_user_id: str, type_: str) -> float:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions"
            " WHERE owner_user_id = ? AND type = ? AND status = 'completed'",
            (owner_user_id, type_),
        ).fetchone()
    return float(row["total"])


def write_audit(user_id: str, event: str, detail: str | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO audit_log (id, user_id, event, detail, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, event, detail, _now()),
        )


def list_audit(user_id: str, limit: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT event, detail, created_at FROM audit_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_bank_account(user_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM bank_accounts WHERE user_id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def upsert_bank_account(user_id: str, account_holder: str, account_number_masked: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO bank_accounts (user_id, account_holder, account_number_masked, linked_at)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET account_holder = excluded.account_holder,"
            " account_number_masked = excluded.account_number_masked, linked_at = excluded.linked_at",
            (user_id, account_holder, account_number_masked, _now()),
        )
