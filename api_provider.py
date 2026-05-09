from __future__ import annotations

from typing import Any


def _extract_chat_text(response: Any) -> str:
    if isinstance(response, dict):
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            return str(message.get("content", "")).strip()
        return ""

    choices = getattr(response, "choices", None) or []
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if message is not None:
            text = str(getattr(message, "content", "")).strip()
            if text:
                return text

    dump_method = getattr(response, "model_dump", None)
    if callable(dump_method):
        try:
            data = dump_method()
            if isinstance(data, dict):
                choices = data.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    return str(message.get("content", "")).strip()
        except Exception:
            return ""

    return ""


def generate_with_openai_compatible_api(
    prompt: str,
    model: str,
    api_key: str,
    base_url: str,
) -> dict[str, str | bool]:
    cleaned_prompt = (prompt or "").strip()
    if not cleaned_prompt:
        return {
            "ok": False,
            "text": "",
            "error": "متن ورودی خالی است. خروجی قالب داخلی نمایش داده شد.",
        }

    cleaned_model = (model or "").strip()
    if not cleaned_model:
        return {
            "ok": False,
            "text": "",
            "error": "نام مدل API مشخص نیست. خروجی قالب داخلی نمایش داده شد.",
        }

    cleaned_api_key = (api_key or "").strip()
    if not cleaned_api_key:
        return {
            "ok": False,
            "text": "",
            "error": "کلید API وارد نشده است. خروجی قالب داخلی نمایش داده شد.",
        }

    cleaned_base_url = (base_url or "").strip()
    if not cleaned_base_url:
        return {
            "ok": False,
            "text": "",
            "error": "آدرس Base URL تنظیم نشده است. خروجی قالب داخلی نمایش داده شد.",
        }

    try:
        from openai import OpenAI
    except Exception:
        return {
            "ok": False,
            "text": "",
            "error": (
                "کتابخانه openai نصب نیست. "
                "برای ادامه از «pip install -r requirements.txt» استفاده کنید."
            ),
        }

    try:
        client = OpenAI(api_key=cleaned_api_key, base_url=cleaned_base_url)
        response = client.chat.completions.create(
            model=cleaned_model,
            messages=[
                {"role": "system", "content": "You are a precise Persian assistant."},
                {"role": "user", "content": cleaned_prompt},
            ],
            temperature=0.2,
        )
        text = _extract_chat_text(response)
        if not text:
            return {
                "ok": False,
                "text": "",
                "error": "از API پاسخی دریافت نشد. خروجی قالب داخلی نمایش داده شد.",
            }
        return {"ok": True, "text": text, "error": ""}
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        raw_error = str(getattr(exc, "message", exc)).lower()

        if status_code == 401 or "unauthorized" in raw_error or "invalid api key" in raw_error:
            return {
                "ok": False,
                "text": "",
                "error": "کلید API معتبر نیست یا دسترسی ندارد. خروجی قالب داخلی نمایش داده شد.",
            }

        if status_code == 404 or "not found" in raw_error:
            return {
                "ok": False,
                "text": "",
                "error": (
                    f"مدل «{cleaned_model}» روی API پیدا نشد. "
                    "مدل دیگری انتخاب کنید."
                ),
            }

        if any(
            token in raw_error
            for token in [
                "connection",
                "timeout",
                "timed out",
                "dns",
                "network",
            ]
        ):
            return {
                "ok": False,
                "text": "",
                "error": "اتصال به API برقرار نشد. اینترنت یا Base URL را بررسی کنید.",
            }

        return {
            "ok": False,
            "text": "",
            "error": f"خطا در فراخوانی API: {exc}",
        }


def generate_image_with_openai_compatible_api(
    prompt: str,
    model: str,
    api_key: str,
    base_url: str,
    size: str = "1024x1024",
) -> dict[str, str | bool]:
    cleaned_prompt = (prompt or "").strip()
    if not cleaned_prompt:
        return {"ok": False, "image_url": "", "image_b64": "", "error": "پرامپت تصویر خالی است."}

    cleaned_model = (model or "").strip()
    if not cleaned_model:
        return {"ok": False, "image_url": "", "image_b64": "", "error": "مدل تصویر API مشخص نیست."}

    cleaned_api_key = (api_key or "").strip()
    if not cleaned_api_key:
        return {"ok": False, "image_url": "", "image_b64": "", "error": "کلید API وارد نشده است."}

    cleaned_base_url = (base_url or "").strip()
    if not cleaned_base_url:
        return {"ok": False, "image_url": "", "image_b64": "", "error": "Base URL تنظیم نشده است."}

    cleaned_size = (size or "1024x1024").strip()

    try:
        from openai import OpenAI
    except Exception:
        return {
            "ok": False,
            "image_url": "",
            "image_b64": "",
            "error": (
                "کتابخانه openai نصب نیست. "
                "برای ادامه از «pip install -r requirements.txt» استفاده کنید."
            ),
        }

    try:
        client = OpenAI(api_key=cleaned_api_key, base_url=cleaned_base_url)
        response = client.images.generate(
            model=cleaned_model,
            prompt=cleaned_prompt,
            size=cleaned_size,
        )

        image_url = ""
        image_b64 = ""

        data_items = getattr(response, "data", None)
        if data_items:
            first = data_items[0]
            image_url = str(getattr(first, "url", "") or "").strip()
            image_b64 = str(getattr(first, "b64_json", "") or "").strip()
        else:
            dump_method = getattr(response, "model_dump", None)
            if callable(dump_method):
                data = dump_method()
                if isinstance(data, dict):
                    items = data.get("data", []) or []
                    if items:
                        first = items[0] or {}
                        image_url = str(first.get("url", "")).strip()
                        image_b64 = str(first.get("b64_json", "")).strip()

        if image_url or image_b64:
            return {"ok": True, "image_url": image_url, "image_b64": image_b64, "error": ""}

        return {
            "ok": False,
            "image_url": "",
            "image_b64": "",
            "error": "از API تصویر قابل نمایش دریافت نشد.",
        }
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        raw_error = str(getattr(exc, "message", exc)).lower()

        if status_code == 401 or "unauthorized" in raw_error or "invalid api key" in raw_error:
            return {
                "ok": False,
                "image_url": "",
                "image_b64": "",
                "error": "کلید API معتبر نیست یا دسترسی لازم برای تصویر ندارد.",
            }

        if status_code == 404 or "not found" in raw_error:
            return {
                "ok": False,
                "image_url": "",
                "image_b64": "",
                "error": f"مدل تصویر «{cleaned_model}» روی API پیدا نشد.",
            }

        if any(
            token in raw_error
            for token in [
                "connection",
                "timeout",
                "timed out",
                "dns",
                "network",
            ]
        ):
            return {
                "ok": False,
                "image_url": "",
                "image_b64": "",
                "error": "اتصال به API برقرار نشد. اینترنت یا Base URL را بررسی کنید.",
            }

        return {
            "ok": False,
            "image_url": "",
            "image_b64": "",
            "error": f"خطا در تولید تصویر با API: {exc}",
        }
