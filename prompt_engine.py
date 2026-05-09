from __future__ import annotations

from typing import Any

from utils import clean_text, contains_persian

ELEMENT_LABELS = {
    "role": "نقش",
    "goal": "هدف",
    "context": "زمینه",
    "output_format": "قالب خروجی",
    "constraints": "محدودیت‌ها",
}


def detect_prompt_elements(prompt_text: str) -> dict[str, bool]:
    text = clean_text(prompt_text).lower()

    role = any(token in text for token in ["به عنوان", "نقش", "تو یک", "you are"])
    goal = len(text) >= 20 and any(
        token in text for token in ["می خواهم", "می‌خواهم", "هدف", "درخواست", "لطفا", "please"]
    )
    context = any(
        token in text
        for token in ["زمینه", "شرایط", "برای", "مخاطب", "context", "audience"]
    )
    output_format = any(
        token in text
        for token in ["قالب", "جدول", "فهرست", "bullet", "json", "خروجی", "format"]
    )
    constraints = any(
        token in text
        for token in ["محدودیت", "حداکثر", "حداقل", "بدون", "constraint", "only"]
    )

    return {
        "role": role,
        "goal": goal,
        "context": context,
        "output_format": output_format,
        "constraints": constraints,
    }


def _build_final_prompt(
    role: str, task: str, context: str, output_format: str, constraints: list[str]
) -> str:
    constraints_text = "\n".join([f"- {item}" for item in constraints])
    return (
        f"نقش: {role}\n"
        f"وظیفه: {task}\n"
        f"زمینه: {context}\n"
        f"قالب خروجی: {output_format}\n"
        f"محدودیت‌ها:\n{constraints_text}"
    )


def generate_structured_prompt(
    category: str, topic: str, templates_data: dict[str, Any]
) -> dict[str, Any]:
    topic = clean_text(topic) or "موضوع موردنظر"
    categories = templates_data.get("categories", {})

    if not categories:
        categories = {
            "عمومی": {
                "role": "شما یک دستیار آموزشی دقیق هستید.",
                "task_template": "در مورد «{topic}» یک خروجی کاربردی تولید کن.",
                "context_template": "کاربر فارسی‌زبان است و دنبال نتیجه عملی است.",
                "output_format": "فهرست مرحله‌ای",
                "constraints": [
                    "پاسخ روشن و کوتاه باشد.",
                    "از مثال عملی استفاده شود.",
                    "زبان خروجی فارسی باشد.",
                ],
            }
        }

    selected = categories.get(category) or next(iter(categories.values()))

    role = selected.get("role", "شما یک دستیار حرفه‌ای هستید.")
    task = selected.get("task_template", "برای «{topic}» خروجی تولید کن.").format(
        topic=topic
    )
    context = selected.get(
        "context_template", "مخاطب کارآموز فنی فارسی‌زبان با دسترسی محدود به اینترنت است."
    ).format(topic=topic)
    output_format = selected.get("output_format", "فهرست شماره‌دار")
    constraints = selected.get(
        "constraints",
        ["پاسخ شفاف باشد.", "از کلی‌گویی پرهیز شود.", "خروجی قابل اجرا باشد."],
    )

    final_prompt = _build_final_prompt(role, task, context, output_format, constraints)
    return {
        "role": role,
        "task": task,
        "context": context,
        "output_format": output_format,
        "constraints": constraints,
        "final_prompt": final_prompt,
    }


def improve_prompt(raw_prompt: str) -> dict[str, Any]:
    cleaned = clean_text(raw_prompt)
    checks = detect_prompt_elements(cleaned)
    score_total = sum(1 for value in checks.values() if value)

    missing = [ELEMENT_LABELS[key] for key, value in checks.items() if not value]
    explanations = []
    if missing:
        explanations.append(
            "برای کامل‌تر شدن پرامپت، این بخش‌ها اضافه شدند: " + "، ".join(missing)
        )
    else:
        explanations.append("پرامپت شما ساختار خوبی داشت و فقط دقیق‌تر و اجرایی‌تر شد.")

    goal_text = cleaned or "یک پاسخ کاربردی و آموزشی درباره موضوع موردنظر تولید کن."
    improved = _build_final_prompt(
        role="شما یک مربی حرفه‌ای هوش مصنوعی برای کارآموزان فنی هستید.",
        task=goal_text,
        context=(
            "مخاطب کارآموز ایرانی است، زمان محدود دارد و ممکن است اینترنت پایدار نداشته باشد."
        ),
        output_format="پاسخ را در 4 بخش ارائه کن: توضیح کوتاه، مراحل عملی، مثال، تمرین.",
        constraints=[
            "پاسخ فقط به زبان فارسی باشد.",
            "خروجی حداکثر 250 کلمه باشد.",
            "از مثال واقعی و قابل اجرا استفاده شود.",
        ],
    )

    checklist = {ELEMENT_LABELS[key]: int(value) for key, value in checks.items()}
    return {
        "improved_prompt": improved,
        "explanations": explanations,
        "checklist": checklist,
        "score_total": score_total,
    }


def teach_prompt(raw_prompt: str) -> dict[str, Any]:
    cleaned = clean_text(raw_prompt)
    checks = detect_prompt_elements(cleaned)
    strengths = [ELEMENT_LABELS[key] for key, value in checks.items() if value]
    missing = [ELEMENT_LABELS[key] for key, value in checks.items() if not value]
    improved = improve_prompt(cleaned)

    weaknesses = (
        [f"بخش «{item}» در پرامپت اولیه واضح نبود یا وجود نداشت." for item in missing]
        if missing
        else ["ضعف مهمی دیده نشد، اما می‌توان دقت واژه‌ها را بیشتر کرد."]
    )
    trainee_explanation = (
        "پرامپت خوب مثل یک دستور کار دقیق است: بگو چه کسی پاسخ دهد، چه کاری انجام شود، "
        "در چه شرایطی، با چه قالبی و با چه محدودیت‌هایی."
    )

    return {
        "strengths": strengths or ["ایده اصلی مشخص بود."],
        "weaknesses": weaknesses,
        "missing_elements": missing,
        "rewritten_prompt": improved["improved_prompt"],
        "simple_explanation": trainee_explanation,
    }


def _to_english_subject(text: str) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return "an educational concept"
    if contains_persian(cleaned):
        return f"the concept '{cleaned}' in an Iranian educational context"
    return cleaned


def generate_image_prompt(idea: str, fields: dict[str, str]) -> dict[str, str]:
    subject = fields.get("subject") or idea
    subject_en = _to_english_subject(subject)

    image_type = clean_text(str(fields.get("image_type", ""))) or "آموزشی"
    style = fields.get("style", "cinematic digital illustration")
    lighting = fields.get("lighting", "soft natural lighting")
    camera_angle = fields.get("camera_angle", "eye-level angle")
    colors = fields.get("colors", "warm neutral palette")
    details = fields.get("details", "high detail textures and realistic depth")
    quality = fields.get("quality", "8k, ultra-detailed, professional composition")
    platform = clean_text(str(fields.get("platform", ""))) or "Instagram"
    aspect_ratio = clean_text(str(fields.get("aspect_ratio", ""))) or "1:1"
    composition = clean_text(str(fields.get("composition", ""))) or "balanced composition"
    negative_prompt = fields.get(
        "negative_prompt",
        "blurry, low resolution, distorted anatomy, extra limbs, noisy background, watermark, text artifacts",
    )

    type_directions = {
        "آموزشی": "clear instructional composition, readable focal points",
        "تبلیغاتی": "high-impact commercial composition, strong focal contrast",
        "پوستر": "poster-ready layout, bold hierarchy, clean negative space",
        "محصولی": "product-centered composition, studio lighting, crisp detail",
        "مفهومی": "symbolic conceptual visual storytelling",
    }
    type_direction = type_directions.get(image_type, type_directions["آموزشی"])

    english_prompt = (
        f"{subject_en}, image type: {image_type}, style: {style}, lighting: {lighting}, "
        f"camera angle: {camera_angle}, colors: {colors}, composition: {composition}, "
        f"direction: {type_direction}, details: {details}, quality: {quality}, "
        f"target platform: {platform}, aspect ratio: {aspect_ratio}"
    )

    persian_explanation = (
        "این پرامپت علاوه بر موضوع و سبک، نوع تصویر، پلتفرم هدف، نسبت تصویر "
        "و ترکیب‌بندی را مشخص می‌کند تا خروجی قابل کنترل‌تر و متناسب با کاربرد نهایی باشد."
    )
    settings_summary = (
        f"نوع: {image_type} | پلتفرم: {platform} | نسبت تصویر: {aspect_ratio} | سبک: {style}"
    )
    copy_block = f"PROMPT:\\n{english_prompt}\\n\\nNEGATIVE PROMPT:\\n{negative_prompt}"

    return {
        "persian_explanation": persian_explanation,
        "english_prompt": english_prompt,
        "negative_prompt": negative_prompt,
        "copy_block": copy_block,
        "settings_summary": settings_summary,
    }


def generate_video_prompt(
    idea: str, duration_seconds: int = 30, settings: dict[str, Any] | None = None
) -> dict[str, Any]:
    cleaned_idea = clean_text(idea) or "یک سناریوی آموزشی کوتاه"
    opts = settings or {}

    style = clean_text(str(opts.get("style", ""))) or "cinematic educational realism"
    platform = clean_text(str(opts.get("platform", ""))) or "social media"
    aspect_ratio = clean_text(str(opts.get("aspect_ratio", ""))) or "16:9"
    tone = clean_text(str(opts.get("tone", ""))) or "الهام‌بخش و عملی"
    audience = clean_text(str(opts.get("audience", ""))) or "کارآموزان فنی"
    camera_intensity = clean_text(str(opts.get("camera_intensity", ""))) or "متوسط"
    video_type = clean_text(str(opts.get("video_type", ""))) or "آموزشی"

    try:
        scene_count = int(opts.get("scene_count", 4))
    except Exception:
        scene_count = 4

    scene_count = min(6, max(3, scene_count))
    duration_seconds = min(180, max(15, int(duration_seconds)))
    segment = max(3, duration_seconds // scene_count)

    if camera_intensity == "آرام":
        camera_profile = "حرکت نرم، پن آهسته و کات‌های طولانی"
    elif camera_intensity == "پویا":
        camera_profile = "حرکت پویا، تراکینگ سریع و کات‌های ریتمیک"
    else:
        camera_profile = "حرکت متعادل با پن و تراکینگ کنترل‌شده"

    type_opening = {
        "آموزشی": "معرفی درس و هدف یادگیری",
        "تبلیغاتی": "معرفی سریع ارزش پیشنهادی و جلب توجه",
        "داستانی": "شروع با یک صحنه روایی کوتاه",
        "گزارشی": "بیان داده‌های کلیدی و زمینه موضوع",
    }

    intro = type_opening.get(video_type, type_opening["آموزشی"])

    scene_descriptions = [
        f"{intro} درباره «{cleaned_idea}» برای {audience}.",
        "نمایش مثال واقعی یا شبه‌واقعی برای روشن‌شدن کاربرد.",
        "شرح گام‌های کلیدی و نکات اجرایی با تاکید تصویری.",
        "نمایش خطاهای رایج و مسیر اصلاح آن‌ها.",
        "جمع‌بندی، یادآوری نکات کلیدی و دعوت به تمرین.",
        "پایان‌بندی با CTA متناسب با نوع ویدیو.",
    ]

    storyboard: list[dict[str, str]] = []
    for idx in range(scene_count):
        start_t = idx * segment
        end_t = duration_seconds if idx == scene_count - 1 else min(duration_seconds, (idx + 1) * segment)
        storyboard.append(
            {
                "scene": f"صحنه {idx + 1}",
                "time": f"{start_t} تا {end_t} ثانیه",
                "description": scene_descriptions[min(idx, len(scene_descriptions) - 1)],
                "camera": camera_profile,
            }
        )

    narration = (
        f"این ویدیوی {video_type} با لحن {tone}، موضوع «{cleaned_idea}» را برای {audience} ارائه می‌کند. "
        "ابتدا مسئله تعریف می‌شود، سپس مثال عملی نمایش داده می‌شود و در پایان اقدام بعدی مشخص می‌گردد."
    )

    video_prompt = (
        "Create a Persian video with the following settings:\n"
        f"- Video type: {video_type}\n"
        f"- Core concept: {_to_english_subject(cleaned_idea)}\n"
        f"- Duration: {duration_seconds} seconds\n"
        f"- Number of scenes: {scene_count}\n"
        f"- Visual style: {style}\n"
        f"- Tone: {tone}\n"
        f"- Audience: {audience}\n"
        f"- Platform target: {platform}\n"
        f"- Aspect ratio: {aspect_ratio}\n"
        f"- Camera direction: {camera_profile}\n"
        "Generate coherent scene-by-scene progression, Persian captions, and a CTA aligned with video type."
    )

    return {
        "video_concept": f"ویدیوی {video_type} درباره «{cleaned_idea}»",
        "storyboard": storyboard,
        "camera_movement": camera_profile,
        "visual_style": f"{style} | نسبت تصویر {aspect_ratio}",
        "narration_text": narration,
        "video_generation_prompt": video_prompt,
        "settings_summary": (
            f"نوع: {video_type} | مدت: {duration_seconds} ثانیه | صحنه: {scene_count} | "
            f"سبک: {style} | پلتفرم: {platform}"
        ),
    }
