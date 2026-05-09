from __future__ import annotations

from typing import Any

from utils import load_json


def load_quiz_questions(file_path: str = "data/quiz_questions.json") -> list[dict[str, Any]]:
    raw_data = load_json(file_path, default={"questions": []})
    questions = raw_data.get("questions", [])

    valid_questions: list[dict[str, Any]] = []
    for item in questions:
        if not isinstance(item, dict):
            continue
        if (
            "question" in item
            and "options" in item
            and "correct_answer_index" in item
            and "explanation" in item
            and isinstance(item["options"], list)
            and len(item["options"]) == 4
        ):
            valid_questions.append(item)

    return valid_questions


def get_available_chapters(questions: list[dict[str, Any]]) -> list[str]:
    """لیست فصل‌های موجود در بانک سوالات را برمی‌گرداند."""
    ordered: list[str] = []
    seen: set[str] = set()
    for item in questions:
        chapter = str(item.get("chapter_reference", "")).strip()
        if not chapter:
            continue
        if chapter not in seen:
            seen.add(chapter)
            ordered.append(chapter)
    return ordered


def filter_questions_by_chapter(
    questions: list[dict[str, Any]], chapter_reference: str
) -> list[dict[str, Any]]:
    chapter_reference = (chapter_reference or "").strip()
    if not chapter_reference:
        return questions
    return [
        item
        for item in questions
        if str(item.get("chapter_reference", "")).strip() == chapter_reference
    ]


def evaluate_answers(
    questions: list[dict[str, Any]], answers_map: dict[int, int]
) -> tuple[int, list[dict[str, Any]]]:
    score = 0
    details: list[dict[str, Any]] = []

    for idx, question in enumerate(questions):
        correct_index = int(question["correct_answer_index"])
        user_index = answers_map.get(idx, -1)
        is_correct = user_index == correct_index

        if is_correct:
            score += 1

        details.append(
            {
                "question": question["question"],
                "options": question["options"],
                "user_answer_index": user_index,
                "correct_answer_index": correct_index,
                "explanation": question["explanation"],
                "is_correct": is_correct,
            }
        )

    return score, details
