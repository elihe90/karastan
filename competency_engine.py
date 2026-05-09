from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


COMPETENCY_STAGES: list[dict[str, Any]] = [
    {
        "title": "شناسایی و تحلیل",
        "max_score": 9.5,
        "criteria": [
            "شناسایی معماری مدلهای زبانی بزرگ، توانمندیها و محدودیتهای Claude, GPT-4, BERT, T5",
            "شناسایی ملاحظات اخلاقی، تعریف پرامپت و مهندسی پرامپت",
            "شناسایی کاربردهای مهندسی پرامپت",
        ],
        "weights": [2.0, 2.0, 5.5],
    },
    {
        "title": "ساختار و اجزای پرامپت",
        "max_score": 9.5,
        "criteria": [
            "بررسی عناصر کلیدی یک پرامپت مؤثر",
            "توانایی طراحی و استفاده از انواع پرامپت ها",
            "بهینه سازی و اصلاح پرامپت های ناموفق",
            "نوشتن پرامپت برای سناریوهای مختلف و دریافت بازخورد",
        ],
        "weights": [2.0, 2.0, 2.0, 3.5],
    },
    {
        "title": "تکنیک های پیشرفته مهندسی پرامپت",
        "max_score": 12.0,
        "criteria": [
            "استفاده از تکنیک های چند مرحله ای",
            "استفاده از مثال ها، داده های آموزشی، پرامپت های با محدودیت، پرامپت های هدایت شده و کنترل خروجی",
        ],
        "weights": [6.0, 6.0],
    },
    {
        "title": "ارزیابی و بهبود پرامپت",
        "max_score": 8.0,
        "criteria": [
            "شناسایی متریک های ارزیابی پرامپت و استفاده از روشهای جمع آوری بازخورد",
            "استفاده از فرآیند تکرار و بهبود پرامپت بر اساس داده ها",
        ],
        "weights": [4.0, 4.0],
    },
    {
        "title": "تولید محتوای متنی",
        "max_score": 11.0,
        "criteria": [
            "انتخاب و استفاده از مدل مناسب محتوای متنی و تولید متن متنوع مثل مقاله، داستان، شعر، کد و سناریوی بازاریابی",
            "بهینه سازی پرامپت برای خروجی های با کیفیت، سبک های نگارشی مختلف، ترجمه و ویرایش",
        ],
        "weights": [4.0, 7.0],
    },
    {
        "title": "تولید تصویر",
        "max_score": 21.5,
        "criteria": [
            "انتخاب مدل مناسب تصویری و طراحی پرامپت های دقیق و توصیفی برای تصویر با کیفیت بالا",
            "کنترل سبک، جزئیات و سایر ابعاد تصویر با استفاده از پرامپت",
            "بهینه سازی پرامپت برای بهبود خروجی تصویر",
        ],
        "weights": [7.25, 7.0, 7.25],
    },
    {
        "title": "تولید ویدیو و انیمیشن",
        "max_score": 12.0,
        "criteria": [
            "استفاده از ابزارها و مدلهای تولید ویدیو و انیمیشن بر پایه متن و طراحی پرامپت پیچیده برای صحنه، شخصیت، حرکت و نورپردازی",
            "کیفیت خروجی یا سناریوی تولید ویدیو/انیمیشن",
        ],
        "weights": [6.0, 6.0],
    },
    {
        "title": "تولید محتوای صوتی",
        "max_score": 12.0,
        "criteria": [
            "استفاده از مدلهای تبدیل متن به گفتار و طراحی پرامپت برای کنترل لحن، سرعت، احساسات، پادکست و محتوای صوتی",
            "بهینه سازی پرامپت برای بهبود خروجی صوتی",
        ],
        "weights": [6.0, 6.0],
    },
    {
        "title": "معیار نگرشی",
        "max_score": 5.0,
        "criteria": [
            "مسئولیت پذیری",
            "رعایت اخلاق حرفه ای",
            "مدیریت زمان",
            "رعایت ایمنی داده",
            "مستندسازی فرآیند",
        ],
        "weights": [1.0, 1.0, 1.0, 1.0, 1.0],
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

    raw_max_total = float(sum(float(stage["max_score"]) for stage in stages))
    normalization_factor = (100.0 / raw_max_total) if raw_max_total > 0 else 1.0
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

    normalized_total = round(total_score * normalization_factor, 2)
    final_percentage = round((normalized_total / 100.0) * 100.0, 2)
    pass_status = "قبول" if final_percentage >= float(pass_threshold) else "نیاز به تمرین بیشتر"

    return {
        "stages": stage_results,
        "total_score": normalized_total,
        "max_score": 100.0,
        "raw_total_score": round(total_score, 2),
        "raw_max_score": round(raw_max_total, 2),
        "percentage": final_percentage,
        "pass_status": pass_status,
        "pass_threshold": float(pass_threshold),
    }


def build_template_feedback(result: dict[str, Any], evidence_text: str = "") -> str:
    stage_results = result.get("stages", [])
    if not stage_results:
        return "ارزیابی انجام شد، اما داده کافی برای بازخورد مرحله ای موجود نیست."

    sorted_stages = sorted(stage_results, key=lambda item: float(item.get("stage_percentage", 0.0)))
    strengths = [str(item.get("title", "-")) for item in sorted_stages[-3:]][::-1]
    weaknesses = [str(item.get("title", "-")) for item in sorted_stages[:3]]
    missing = [title for title in weaknesses if title not in strengths]
    evidence = (evidence_text or "").strip()[:350]

    lines = [f"نتیجه نهایی: {result.get('pass_status', '-')} | امتیاز: {result.get('total_score', 0)} از {result.get('max_score', 100)}"]
    lines.append("نقاط قوت:")
    lines.extend([f"- {item}" for item in strengths])
    lines.append("نقاط ضعف:")
    lines.extend([f"- {item}" for item in weaknesses])
    lines.append("عناصر جاافتاده:")
    lines.extend([f"- {item}" for item in missing] if missing else ["- مورد بحرانی مشاهده نشد."])
    lines.append("پیشنهادهای بهبود:")
    lines.append("- برای هر مرحله ضعیف، یک نسخه بازنویسی‌شده از پرامپت با نقش/هدف/قیود روشن ثبت کنید.")
    lines.append("- برای خروجی‌های تصویر/ویدیو/صوت، نگتیو پرامپت و کنترل سبک/لحن/سرعت را صریح کنید.")
    lines.append("- خروجی جدید را دوباره با همین روبریک امتیازدهی و مستندسازی کنید.")
    if evidence:
        lines.append("خلاصه شواهد:")
        lines.append(evidence)
    return "\n".join(lines)


def _contains_any(text: str, tokens: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(token.lower() in lowered for token in tokens)


def analyze_prompt_offline(prompt_text: str) -> dict[str, Any]:
    text = (prompt_text or "").strip()
    normalized = re.sub(r"\s+", " ", text).strip()
    words = [item for item in normalized.split(" ") if item]
    word_count = len(words)

    signals = {
        "role": _contains_any(normalized, ["نقش", "به عنوان", "you are", "role"]),
        "goal": _contains_any(normalized, ["هدف", "می خواهم", "درخواست", "goal", "task"]),
        "context": _contains_any(normalized, ["زمینه", "شرایط", "context", "پیش زمینه"]),
        "output_format": _contains_any(normalized, ["قالب", "خروجی", "json", "table", "bullet"]),
        "constraints": _contains_any(normalized, ["محدودیت", "حداکثر", "حداقل", "فقط", "only"]),
        "audience": _contains_any(normalized, ["مخاطب", "دانشجو", "کارآموز", "audience"]),
        "tone": _contains_any(normalized, ["لحن", "رسمی", "دوستانه", "tone"]),
        "cta": _contains_any(normalized, ["cta", "دعوت به اقدام", "اقدام بعدی", "ثبت نام", "شروع کنید"]),
        "examples": _contains_any(normalized, ["مثال", "نمونه", "for example", "sample"]),
        "step_by_step_logic": _contains_any(
            normalized,
            ["گام به گام", "مرحله به مرحله", "step by step", "chain of thought", "reasoning"],
        ),
        "negative_prompt": _contains_any(normalized, ["negative prompt", "نگتیو", "عدم نمایش", "حذف"]),
        "visual_style": _contains_any(normalized, ["style", "سبک", "استایل", "cinematic", "realistic"]),
        "camera": _contains_any(normalized, ["camera", "دوربین", "angle", "lens"]),
        "lighting": _contains_any(normalized, ["lighting", "نور", "نورپردازی", "shadow"]),
        "voice_tone": _contains_any(normalized, ["voice", "tone of voice", "صدای", "لحن گفتار"]),
        "pace": _contains_any(normalized, ["pace", "speed", "tempo", "سرعت", "ریتم"]),
        "emotion": _contains_any(normalized, ["emotion", "feeling", "احساس", "هیجان", "حس"]),
        "ethical_awareness": _contains_any(
            normalized,
            ["اخلاق", "سوگیری", "حریم خصوصی", "bias", "privacy", "ethical"],
        ),
    }

    richness_bonus = 1 if word_count >= 60 else 0
    field_scores: dict[str, int] = {}
    for key, active in signals.items():
        if not active:
            field_scores[key] = 0
            continue
        base = 3
        if key in {"constraints", "context", "output_format", "goal", "step_by_step_logic"}:
            base = 4
        field_scores[key] = min(5, base + richness_bonus)

    completeness = sum(1 for item in signals.values() if item)
    completeness_ratio = round((completeness / len(signals)) * 100.0, 2)

    return {
        "signals": signals,
        "field_scores": field_scores,
        "word_count": word_count,
        "completeness_ratio": completeness_ratio,
        "normalized_prompt": normalized,
    }


def _signal_score(analysis: dict[str, Any], key: str, fallback: float = 0.0) -> float:
    value = analysis.get("field_scores", {}).get(key)
    if value is None:
        return float(fallback)
    return max(0.0, min(5.0, float(value)))


def build_stage_ratings_from_analysis(
    analysis: dict[str, Any],
    prompt_text: str = "",
    generated_output: str = "",
) -> list[list[float]]:
    text = (prompt_text or "").strip().lower()
    output_text = (generated_output or "").strip().lower()
    model_signal = 5.0 if _contains_any(text, ["llm", "gpt", "qwen", "مدل"]) else 2.5
    advanced_signal = 5.0 if _contains_any(text, ["few-shot", "chain of thought", "react", "step-back", "مرحله"]) else 2.0
    multimedia_signal = 5.0 if _contains_any(text, ["تصویر", "image", "ویدیو", "video", "animation", "انیمیشن"]) else 2.0
    audio_signal = 5.0 if _contains_any(text, ["صوت", "voice", "podcast", "audio"]) else 2.0
    output_quality = 4.5 if len(output_text.split()) >= 40 else (3.0 if output_text else 2.0)

    stage_ratings = [
        [
            model_signal,
            _signal_score(analysis, "ethical_awareness", 2.0),
            _signal_score(analysis, "goal", 2.5),
        ],
        [
            _signal_score(analysis, "role", 1.5),
            _signal_score(analysis, "goal", 1.5),
            _signal_score(analysis, "constraints", 1.5),
            _signal_score(analysis, "output_format", 1.5),
        ],
        [
            advanced_signal,
            _signal_score(analysis, "step_by_step_logic", 2.0),
        ],
        [
            _signal_score(analysis, "examples", 2.0),
            _signal_score(analysis, "step_by_step_logic", 2.0),
        ],
        [
            output_quality,
            _signal_score(analysis, "tone", 2.5),
        ],
        [
            multimedia_signal,
            _signal_score(analysis, "visual_style", 2.0),
            _signal_score(analysis, "negative_prompt", 2.0),
        ],
        [
            multimedia_signal,
            _signal_score(analysis, "camera", 2.0),
        ],
        [
            audio_signal,
            _signal_score(analysis, "voice_tone", 2.0),
        ],
        [
            _signal_score(analysis, "ethical_awareness", 2.0),
            _signal_score(analysis, "ethical_awareness", 2.0),
            _signal_score(analysis, "constraints", 2.0),
            _signal_score(analysis, "ethical_awareness", 2.0),
            _signal_score(analysis, "ethical_awareness", 2.0),
        ],
    ]
    return [[max(0.0, min(5.0, float(x))) for x in row] for row in stage_ratings]


def classify_skill_level(percentage: float) -> str:
    value = float(percentage)
    if value >= 85:
        return "حرفه ای"
    if value >= 70:
        return "مسلط"
    if value >= 55:
        return "در حال رشد"
    return "نیازمند تقویت پایه"


def build_improvement_suggestions(result: dict[str, Any], limit: int = 3) -> list[str]:
    stages = list(result.get("stages", []) or [])
    if not stages:
        return ["ارزیابی مرحله ای برای تولید پیشنهاد کافی نیست."]
    weak = sorted(stages, key=lambda item: float(item.get("stage_percentage", 0.0)))
    selected = weak[: max(1, int(limit))]
    suggestions = []
    for stage in selected:
        title = str(stage.get("title", "مرحله"))
        suggestions.append(
            f"برای «{title}» یک تمرین هدفمند طراحی کنید و با Rubric همان مرحله دوباره امتیازدهی کنید."
        )
    return suggestions
