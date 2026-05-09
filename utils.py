from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_json(file_path: Path | str, default: Any) -> Any:
    """بارگذاری امن JSON با مقدار پیش‌فرض در صورت خطا."""
    path = Path(file_path)
    if not path.is_absolute():
        path = BASE_DIR / path

    try:
        # utf-8-sig برای پشتیبانی از فایل‌هایی است که BOM دارند.
        with path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def calculate_percentage(score: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((score / total) * 100, 2)


def get_status(percentage: float) -> str:
    return "قبول" if percentage >= 60 else "نیاز به تمرین بیشتر"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def contains_persian(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))
