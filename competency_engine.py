from __future__ import annotations

from copy import deepcopy
from typing import Any


COMPETENCY_STAGES: list[dict[str, Any]] = [
    {
        "title": "شناسایی مدل های زبانی و مهندسی پرامپت",
        "max_score": 15,
        "criteria": [
            "درک تفاوت مدل های زبانی و کاربرد هرکدام",
            "تشخیص مسئله مناسب برای مهندسی پرامپت",
            "تعریف هدف آموزشی روشن برای خروجی",
            "انتخاب رویکرد مناسب برای محدودیت های واقعی",
        ],
        "weights": [30, 25, 25, 20],
    },
    {
        "title": "ساختار و اجزای پرامپت",
        "max_score": 15,
        "criteria": [
            "تعیین نقش و مسئولیت مدل",
            "تعریف هدف، زمینه و مخاطب",
            "مشخص کردن قالب خروجی قابل ارزیابی",
            "اعمال محدودیت ها و مرزبندی پاسخ",
        ],
        "weights": [25, 30, 25, 20],
    },
    {
        "title": "تکنیک های پیشرفته",
        "max_score": 15,
        "criteria": [
            "انتخاب تکنیک متناسب با نوع مسئله",
            "ترکیب صحیح چند تکنیک در یک سناریو",
            "کاهش خطا و ابهام در پاسخ مدل",
            "توانایی توضیح دلیل انتخاب تکنیک ها",
        ],
        "weights": [30, 25, 25, 20],
    },
    {
        "title": "ارزیابی و بهبود پرامپت",
        "max_score": 15,
        "criteria": [
            "تعریف معیار کمی و کیفی برای ارزیابی",
            "تحلیل پاسخ و استخراج نقاط ضعف",
            "بازنویسی مرحله ای و مستند پرامپت",
            "تصمیم گیری بر پایه داده و شواهد",
        ],
        "weights": [25, 30, 25, 20],
    },
    {
        "title": "تولید محتوای متنی",
        "max_score": 10,
        "criteria": [
            "ساختار منطقی و انسجام متن",
            "تناسب لحن با مخاطب هدف",
            "دقت و شفافیت محتوا",
            "قابلیت انتشار یا استفاده عملی",
        ],
        "weights": [25, 25, 30, 20],
    },
    {
        "title": "تولید تصویر",
        "max_score": 10,
        "criteria": [
            "تعریف دقیق سوژه و سبک بصری",
            "کنترل نور، ترکیب بندی و جزئیات",
            "استفاده موثر از نگتیو پرامپت",
            "تناسب خروجی با کاربرد نهایی",
        ],
        "weights": [25, 30, 25, 20],
    },
    {
        "title": "تولید ویدیو و انیمیشن",
        "max_score": 10,
        "criteria": [
            "طراحی مفهوم و سناریوی ویدیو",
            "گام بندی صحنه به صحنه",
            "کنترل سبک بصری و حرکت دوربین",
            "هم راستایی خروجی با هدف آموزشی/تجاری",
        ],
        "weights": [25, 30, 25, 20],
    },
    {
        "title": "تولید محتوای صوتی",
        "max_score": 10,
        "criteria": [
            "طراحی متن مناسب گفتار",
            "تناسب لحن و ریتم با مخاطب",
            "وضوح پیام و پیامد عملی",
            "آمادگی برای بازتولید و بهینه سازی",
        ],
        "weights": [30, 25, 25, 20],
    },
]


def get_competency_stages() -> list[dict[str, Any]]:
    stages = deepcopy(COMPETENCY_STAGES)
    for stage in stages:
        stage["trainee_score"] = 0.0
    return stages


def get_rubric_levels() -> list[dict[str, Any]]:
    return [
        {"امتیاز": 0, "سطح": "نیاز به شروع", "توضیح": "شاخص مرتبط در خروجی دیده نمی شود."},
        {"امتیاز": 1, "سطح": "مقدماتی", "توضیح": "شاخص به شکل محدود و ناپایدار دیده می شود."},
        {"امتیاز": 2, "سطح": "در حال رشد", "توضیح": "شاخص قابل مشاهده است اما هنوز خطا دارد."},
        {"امتیاز": 3, "سطح": "قابل قبول", "توضیح": "شاخص عمدتا درست اجرا شده و قابل استفاده است."},
        {"امتیاز": 4, "سطح": "خوب", "توضیح": "شاخص دقیق و پایدار اجرا شده و کیفیت مناسب دارد."},
        {"امتیاز": 5, "سطح": "حرفه ای", "توضیح": "شاخص عالی، قابل دفاع و قابل تعمیم اجرا شده است."},
    ]


def evaluate_stage_score(
    ratings: list[float], weights: list[float], max_score: float
) -> tuple[float, float]:
    if not ratings or not weights or len(ratings) != len(weights):
        return 0.0, 0.0
    safe_weights = [max(0.0, float(item)) for item in weights]
    total_weight = sum(safe_weights)
    if total_weight <= 0:
        return 0.0, 0.0

    weighted_ratio = 0.0
    for rating, weight in zip(ratings, safe_weights):
        normalized_rating = max(0.0, min(5.0, float(rating))) / 5.0
        weighted_ratio += normalized_rating * weight
    weighted_ratio = weighted_ratio / total_weight

    score = round(weighted_ratio * float(max_score), 2)
    percentage = round(weighted_ratio * 100.0, 2)
    return score, percentage


def evaluate_competency_assessment(
    stage_ratings: list[list[float]],
    pass_threshold: float = 70.0,
) -> dict[str, Any]:
    stages = get_competency_stages()
    if len(stage_ratings) != len(stages):
        raise ValueError("Stage ratings count mismatch.")

    max_total = float(sum(float(stage["max_score"]) for stage in stages))
    total_score = 0.0
    stage_results: list[dict[str, Any]] = []

    for stage, ratings in zip(stages, stage_ratings):
        stage_score, stage_percentage = evaluate_stage_score(
            ratings=ratings,
            weights=[float(item) for item in stage["weights"]],
            max_score=float(stage["max_score"]),
        )
        stage["trainee_score"] = stage_score
        total_score += stage_score
        stage_results.append(
            {
                "title": stage["title"],
                "max_score": float(stage["max_score"]),
                "criteria": stage["criteria"],
                "weights": stage["weights"],
                "ratings": [round(float(item), 2) for item in ratings],
                "trainee_score": stage_score,
                "stage_percentage": stage_percentage,
            }
        )

    final_percentage = round((total_score / max_total) * 100.0, 2) if max_total else 0.0
    pass_status = "قبول" if final_percentage >= float(pass_threshold) else "نیاز به تقویت"

    return {
        "stages": stage_results,
        "total_score": round(total_score, 2),
        "max_score": round(max_total, 2),
        "percentage": final_percentage,
        "pass_status": pass_status,
        "pass_threshold": float(pass_threshold),
    }


def build_template_feedback(result: dict[str, Any], evidence_text: str = "") -> str:
    stage_results = result.get("stages", [])
    if not stage_results:
        return "ارزیابی انجام شد، اما داده کافی برای بازخورد مرحله ای موجود نیست."

    sorted_stages = sorted(
        stage_results,
        key=lambda item: float(item.get("stage_percentage", 0.0)),
        reverse=True,
    )
    strengths = [item["title"] for item in sorted_stages[:2]]
    growth = [item["title"] for item in sorted_stages[-2:]]
    evidence = (evidence_text or "").strip()

    lines = [
        f"نتیجه نهایی: {result.get('pass_status', '-')} با امتیاز {result.get('percentage', 0)} درصد.",
        "نقاط قوت کلیدی:",
    ]
    lines.extend([f"- {item}" for item in strengths])
    lines.append("حوزه های نیازمند تمرین بیشتر:")
    lines.extend([f"- {item}" for item in growth])
    lines.append("پیشنهاد آموزشی:")
    lines.append("- برای هر حوزه ضعیف، یک تمرین عملی کوتاه با معیار ارزیابی مشخص تعریف کنید.")
    lines.append("- پس از بازنویسی، خروجی جدید را با معیارهای همان مرحله مجدد امتیازدهی کنید.")
    if evidence:
        lines.append("جمع بندی شواهد کارآموز:")
        lines.append(evidence[:350])
    return "\n".join(lines)
