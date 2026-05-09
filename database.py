from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
ENV_DB_PATH = os.getenv("KARISTAN_DB_PATH", "").strip()
DB_PATH = Path(ENV_DB_PATH) if ENV_DB_PATH else BASE_DIR / "karistan_results.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    # برخی محیط‌های آفلاین/شبکه‌ای با فایل journal پیش‌فرض SQLite ناسازگارند.
    conn.execute("PRAGMA journal_mode=MEMORY;")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA synchronous=OFF;")
    return conn


def init_db() -> tuple[bool, str]:
    """ایجاد جدول نتایج آزمون در صورت نبود آن."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trainee_name TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    percentage REAL NOT NULL,
                    exam_type TEXT NOT NULL DEFAULT 'comprehensive',
                    chapter_reference TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                str(row[1]).strip()
                for row in conn.execute("PRAGMA table_info(quiz_results)").fetchall()
            }
            if "exam_type" not in columns:
                conn.execute(
                    "ALTER TABLE quiz_results ADD COLUMN exam_type TEXT NOT NULL DEFAULT 'comprehensive'"
                )
            if "chapter_reference" not in columns:
                conn.execute(
                    "ALTER TABLE quiz_results ADD COLUMN chapter_reference TEXT NOT NULL DEFAULT ''"
                )
        return True, ""
    except sqlite3.Error as exc:
        return False, str(exc)


def save_quiz_result(
    trainee_name: str,
    score: int,
    total: int,
    percentage: float,
    exam_type: str = "comprehensive",
    chapter_reference: str = "",
) -> tuple[bool, str]:
    try:
        exam_type = (exam_type or "comprehensive").strip().lower()
        if exam_type not in {"comprehensive", "chapter"}:
            exam_type = "comprehensive"
        chapter_reference = (chapter_reference or "").strip()
        if exam_type != "chapter":
            chapter_reference = ""

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO quiz_results (
                    trainee_name, score, total, percentage, exam_type, chapter_reference, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trainee_name,
                    score,
                    total,
                    percentage,
                    exam_type,
                    chapter_reference,
                    created_at,
                ),
            )
        return True, ""
    except sqlite3.Error as exc:
        return False, str(exc)


def fetch_results() -> tuple[list[dict[str, Any]], str]:
    try:
        with _get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT
                    id,
                    trainee_name,
                    score,
                    total,
                    percentage,
                    exam_type,
                    chapter_reference,
                    created_at
                FROM quiz_results
                ORDER BY id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows], ""
    except sqlite3.Error as exc:
        return [], str(exc)
