from __future__ import annotations

from typing import Any


def _extract_response_text(response: Any) -> str:
    if isinstance(response, dict):
        return str(response.get("response", "")).strip()

    text = str(getattr(response, "response", "")).strip()
    if text:
        return text

    dump_method = getattr(response, "model_dump", None)
    if callable(dump_method):
        try:
            data = dump_method()
            if isinstance(data, dict):
                return str(data.get("response", "")).strip()
        except Exception:
            return ""

    return ""


def generate_with_ollama(
    prompt: str, model: str = "qwen2.5:3b"
) -> dict[str, str | bool]:
    cleaned_prompt = (prompt or "").strip()
    if not cleaned_prompt:
        return {
            "ok": False,
            "text": "",
            "error": "متن ورودی برای مدل خالی است. خروجی قالب داخلی نمایش داده شد.",
        }

    try:
        import ollama
    except Exception:
        return {
            "ok": False,
            "text": "",
            "error": (
                "کتابخانه Ollama در پایتون نصب نیست. "
                "برای ادامه از «pip install -r requirements.txt» استفاده کنید."
            ),
        }

    try:
        response = ollama.generate(model=model, prompt=cleaned_prompt)
        text = _extract_response_text(response)
        if not text:
            return {
                "ok": False,
                "text": "",
                "error": "از Ollama پاسخی دریافت نشد. خروجی قالب داخلی نمایش داده شد.",
            }
        return {"ok": True, "text": text, "error": ""}
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        raw_error = str(getattr(exc, "error", exc)).lower()

        if status_code == 404 or "not found" in raw_error:
            return {
                "ok": False,
                "text": "",
                "error": (
                    f"مدل «{model}» روی Ollama پیدا نشد. "
                    f"ابتدا این دستور را اجرا کنید: ollama pull {model}"
                ),
            }

        if any(
            token in raw_error
            for token in [
                "connection refused",
                "failed to connect",
                "timed out",
                "localhost",
                "11434",
            ]
        ):
            return {
                "ok": False,
                "text": "",
                "error": (
                    "اتصال به Ollama برقرار نشد. "
                    "ابتدا برنامه Ollama را اجرا کنید و دوباره تلاش کنید."
                ),
            }

        return {
            "ok": False,
            "text": "",
            "error": f"خطا در تولید پاسخ با Ollama: {exc}",
        }


def list_installed_ollama_models() -> dict[str, Any]:
    try:
        import ollama
    except Exception:
        return {
            "ok": False,
            "models": [],
            "error": (
                "کتابخانه Ollama در پایتون نصب نیست. "
                "برای ادامه از «pip install -r requirements.txt» استفاده کنید."
            ),
        }

    try:
        response = ollama.list()
    except Exception as exc:
        raw_error = str(getattr(exc, "error", exc)).lower()
        if any(
            token in raw_error
            for token in [
                "connection refused",
                "failed to connect",
                "timed out",
                "localhost",
                "11434",
            ]
        ):
            return {
                "ok": False,
                "models": [],
                "error": (
                    "اتصال به Ollama برقرار نشد. "
                    "ابتدا برنامه Ollama را اجرا کنید."
                ),
            }
        return {
            "ok": False,
            "models": [],
            "error": f"خطا در خواندن لیست مدل‌های Ollama: {exc}",
        }

    items: list[Any] = []
    if isinstance(response, dict):
        items = list(response.get("models", []))
    else:
        items = list(getattr(response, "models", []) or [])
        if not items:
            dump_method = getattr(response, "model_dump", None)
            if callable(dump_method):
                try:
                    data = dump_method()
                    if isinstance(data, dict):
                        items = list(data.get("models", []))
                except Exception:
                    items = []

    names: list[str] = []
    for item in items:
        if isinstance(item, dict):
            name = str(item.get("model") or item.get("name") or "").strip()
        else:
            name = str(getattr(item, "model", "") or getattr(item, "name", "")).strip()
        if name:
            names.append(name)

    unique_sorted = sorted(set(names))
    return {"ok": True, "models": unique_sorted, "error": ""}
