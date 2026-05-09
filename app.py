from __future__ import annotations

import base64
from datetime import datetime
import html
import json
import os
from pathlib import Path
import random
from typing import Any
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as components_html

from api_provider import (
    generate_image_with_openai_compatible_api,
    generate_with_openai_compatible_api,
)
from competency_engine import (
    analyze_prompt_offline,
    build_template_feedback,
    classify_skill_level,
    evaluate_competency_assessment,
    get_competency_stages,
    get_rubric_levels,
)
from database import (
    fetch_competency_results,
    fetch_results,
    init_db,
    save_competency_result,
    save_quiz_result,
)
from llm_provider import generate_with_ollama, list_installed_ollama_models
from prompt_engine import (
    generate_image_prompt,
    generate_structured_prompt,
    generate_video_prompt,
    improve_prompt,
    teach_prompt,
)
from quiz import (
    evaluate_answers,
    filter_questions_by_chapter,
    get_available_chapters,
    load_quiz_questions,
)
from utils import DATA_DIR, calculate_percentage, get_status, load_json


st.set_page_config(
    page_title="Karistan - Offline Prompt Engineering Learning Lab",
    layout="wide",
    initial_sidebar_state="expanded",
)


RTL_STYLE = """
<style>
:root {
    --font-fa: "Vazirmatn", "Vazir", "IRANSansX", "IRANSans", "B Yekan", "Tahoma", sans-serif;
    --bg-app: #18305c;
    --bg-surface: #27457a;
    --bg-surface-soft: #32558f;
    --bg-elevated: #3b66a7;
    --text-primary: #edf3ff;
    --text-secondary: #d2def2;
    --text-muted: #a6b8d9;
    --accent: #4ea3ff;
    --accent-strong: #2f7cff;
    --accent-soft: rgba(78, 163, 255, 0.14);
    --border-soft: rgba(144, 180, 233, 0.24);
    --border-strong: rgba(104, 158, 235, 0.5);
    --shadow-card: 0 14px 35px rgba(3, 8, 20, 0.45);
    --radius-lg: 18px;
    --radius-md: 14px;
}

@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    direction: rtl;
    text-align: right;
    font-family: var(--font-fa);
}

/* Force Persian font across Streamlit/BaseWeb widgets */
[data-testid="stAppViewContainer"] *:not(code):not(pre) {
    font-family: var(--font-fa) !important;
}

body {
    font-size: 17px;
    color: var(--text-primary);
}

h1, h2, h3, h4, p, label, li, span {
    text-align: right !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1000px 520px at 10% -10%, rgba(125, 175, 255, 0.33), transparent 55%),
        radial-gradient(760px 420px at 88% -8%, rgba(96, 201, 255, 0.2), transparent 54%),
        linear-gradient(180deg, #23437a 0%, var(--bg-app) 62%, #1d3a6a 100%);
}

.main .block-container {
    max-width: 1200px;
    padding-top: 1.3rem;
    padding-bottom: 2.4rem;
}

[data-testid="stSidebar"] * {
    direction: rtl;
    text-align: right !important;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(40, 66, 112, 0.98) 0%, rgba(27, 49, 88, 0.98) 100%);
    border-left: 1px solid var(--border-soft);
}

[data-testid="stSidebar"] .block-container {
    padding-top: 0.85rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--text-secondary);
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(244, 248, 255, 0.08) !important;
    border: 1px solid rgba(188, 214, 247, 0.3) !important;
    border-radius: 12px !important;
    color: #f4f8ff !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: #f4f8ff !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"] {
    margin-bottom: 0.1rem;
}

[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 1px solid rgba(144, 180, 233, 0.22);
    border-radius: 14px;
    background: rgba(31, 52, 90, 0.48);
    margin-top: 0.45rem;
}

h1, h2, h3, h4 {
    color: var(--text-primary) !important;
    letter-spacing: -0.01em;
}

p, li, label, [data-testid="stCaptionContainer"] {
    color: var(--text-secondary);
}

[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid var(--border-soft);
}

[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
[data-baseweb="textarea"] > div {
    border-radius: 12px !important;
    background: #f4f8ff !important;
    border: 1px solid #d2deef !important;
    color: #122340 !important;
}

[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    color: #10233f !important;
    caret-color: #1f5fd8 !important;
}

[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {
    color: #6b7ea3 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div {
    color: #10233f !important;
}

[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stFormSubmitButton"] button {
    border-radius: 12px !important;
    border: 1px solid var(--border-strong) !important;
    background: linear-gradient(140deg, #1f5fd8, #2d7eff) !important;
    color: #f4f8ff !important;
    font-weight: 700 !important;
    box-shadow: 0 10px 24px rgba(29, 87, 197, 0.35);
}

[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    border-color: #8ac8ff !important;
    filter: brightness(1.07);
}

button[data-baseweb="tab"] {
    background: rgba(32, 54, 94, 0.9) !important;
    border: 1px solid var(--border-soft) !important;
    border-radius: 12px !important;
    margin-left: 0.35rem !important;
    color: var(--text-secondary) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(34, 97, 214, 0.66), rgba(27, 74, 170, 0.66)) !important;
    color: #f0f6ff !important;
    border-color: rgba(145, 195, 255, 0.62) !important;
}

[data-testid="stExpander"] {
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    background: rgba(31, 52, 90, 0.72);
}

[data-testid="stMetric"] {
    background: linear-gradient(165deg, rgba(39, 66, 112, 0.9), rgba(27, 48, 86, 0.9));
    border-radius: 14px;
    border: 1px solid var(--border-soft);
    padding: 0.8rem 1rem;
}

[data-testid="stCodeBlock"] {
    border-radius: 14px;
    border: 1px solid rgba(121, 178, 255, 0.35);
    box-shadow: 0 8px 22px rgba(2, 7, 19, 0.45);
    overflow: hidden;
}

[data-testid="stCodeBlock"] pre {
    background: linear-gradient(180deg, #081325 0%, #0a1730 100%) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    overflow: hidden;
}

.hero-panel {
    background:
        radial-gradient(520px 260px at 90% 8%, rgba(100, 181, 255, 0.23), transparent 58%),
        linear-gradient(145deg, rgba(16, 34, 67, 0.96), rgba(8, 18, 36, 0.96));
    border: 1px solid rgba(125, 176, 248, 0.42);
    border-radius: 24px;
    padding: 1.15rem 1.25rem 1.2rem 1.25rem;
    margin-bottom: 0.72rem;
    box-shadow: var(--shadow-card);
    overflow: hidden;
}

.hero-content {
    max-width: 980px;
    margin-right: auto;
    display: grid;
    gap: 0.22rem;
}

.hero-title {
    margin: 0;
    font-size: 2.05rem;
    font-weight: 800;
    color: #f3f8ff;
}

.hero-subtitle {
    margin: 0.1rem 0 0.45rem 0;
    color: #bdd1f1;
    font-size: 1.08rem;
    font-weight: 700;
    line-height: 1.72;
    max-width: 54ch;
}

.hero-description {
    margin: 0 0 0.7rem 0;
    color: #d9e7fb;
    font-size: 0.97rem;
    line-height: 1.82;
    max-width: 88ch;
}

.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
    justify-content: flex-start;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid rgba(145, 197, 255, 0.32);
    padding: 0.35rem 0.8rem;
    background: rgba(27, 53, 96, 0.52);
    color: #d8e8ff;
    font-size: 0.82rem;
}

.hero-ctas {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 0.45rem;
    align-items: center;
    justify-content: flex-start;
}

.hero-cta {
    border-radius: 11px;
    border: 1px solid rgba(159, 206, 255, 0.46);
    background: linear-gradient(145deg, rgba(35, 99, 214, 0.9), rgba(47, 126, 255, 0.9));
    color: #f4f8ff;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 0.4rem 0.78rem;
}

.home-footer {
    text-align: center;
    color: #d9e8ff;
    margin-top: 1.1rem;
    font-size: 0.95rem;
    line-height: 1.9;
}

.surface-card {
    background: linear-gradient(165deg, rgba(33, 55, 97, 0.88), rgba(24, 42, 78, 0.88));
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-lg);
    padding: 0.85rem 0.95rem;
    box-shadow: var(--shadow-card);
    margin-bottom: 0.65rem;
}

.surface-title {
    color: #edf4ff;
    font-weight: 700;
    margin-bottom: 0.45rem;
    font-size: 1rem;
}

.surface-body {
    color: var(--text-secondary);
    line-height: 1.95;
    font-size: 0.96rem;
}

.surface-body ul,
.surface-body ol {
    margin: 0.3rem 0 0 0;
    padding-right: 1.1rem;
}

.module-chip-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.module-chip {
    border: 1px solid rgba(122, 177, 252, 0.42);
    border-radius: 10px;
    padding: 0.44rem 0.72rem;
    background: rgba(23, 44, 80, 0.72);
    color: #d7e8ff;
    font-size: 0.88rem;
}

.prompt-shell-title {
    margin-top: 0.55rem;
    margin-bottom: 0.35rem;
    color: #d5e8ff;
    font-weight: 700;
    font-size: 0.92rem;
}

.lesson-pill {
    display: inline-flex;
    border-radius: 999px;
    background: var(--accent-soft);
    border: 1px solid rgba(108, 171, 255, 0.43);
    color: #d6e8ff;
    padding: 0.22rem 0.74rem;
    font-size: 0.82rem;
    margin-left: 0.3rem;
    margin-bottom: 0.2rem;
}

.step-card {
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-md);
    background: rgba(28, 47, 84, 0.84);
    padding: 0.8rem 0.95rem;
    margin-bottom: 0.6rem;
}

.step-title {
    color: #ebf4ff;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.step-body {
    color: var(--text-secondary);
    line-height: 1.85;
}

.sidebar-brand {
    border: 1px solid rgba(113, 172, 255, 0.4);
    border-radius: 18px;
    padding: 0.72rem 0.8rem;
    margin-bottom: 0.65rem;
    background: linear-gradient(150deg, rgba(23, 45, 86, 0.9), rgba(12, 22, 44, 0.9));
}

.sidebar-brand-title {
    color: #f4f8ff;
    font-weight: 800;
    font-size: 1.22rem;
}

.sidebar-brand-sub {
    color: #bfd5f7;
    font-size: 0.81rem;
    margin-top: 0.2rem;
}

.sidebar-section-title {
    color: #d8e9ff;
    font-size: 0.8rem;
    font-weight: 700;
    margin-top: 0.45rem;
    margin-bottom: 0.25rem;
    letter-spacing: 0.03em;
}

.status-chip {
    border-radius: 10px;
    border: 1px solid var(--border-soft);
    background: rgba(20, 36, 67, 0.82);
    color: #d7e8ff;
    padding: 0.38rem 0.55rem;
    font-size: 0.82rem;
    margin-bottom: 0.5rem;
}

.status-chip.success {
    border-color: rgba(45, 211, 152, 0.5);
    background: rgba(10, 76, 54, 0.3);
}

.status-chip.warning {
    border-color: rgba(250, 204, 21, 0.52);
    background: rgba(116, 88, 12, 0.3);
}

.status-chip.error {
    border-color: rgba(239, 68, 68, 0.55);
    background: rgba(120, 29, 29, 0.35);
}

.status-chip.info {
    border-color: rgba(96, 165, 250, 0.5);
    background: rgba(30, 58, 138, 0.28);
}

.workspace-shell {
    border: 1px solid rgba(164, 203, 255, 0.45);
    border-radius: 18px;
    background: linear-gradient(160deg, rgba(38, 63, 108, 0.85), rgba(30, 52, 92, 0.85));
    box-shadow: var(--shadow-card);
    padding: 0.95rem 1rem;
    margin-bottom: 0.9rem;
}

.workspace-form-shell {
    border: 1px solid rgba(170, 208, 255, 0.42);
    border-radius: 16px;
    background: linear-gradient(160deg, rgba(36, 60, 104, 0.78), rgba(30, 52, 92, 0.78));
    padding: 0.9rem 0.95rem 0.8rem 0.95rem;
    margin-bottom: 0.8rem;
}

.workspace-kicker {
    color: #d7e8ff;
    font-size: 0.82rem;
    letter-spacing: 0.03em;
    margin-bottom: 0.35rem;
}

.workspace-title {
    color: #f6faff;
    font-size: 1.18rem;
    font-weight: 800;
    margin-bottom: 0.42rem;
}

.workspace-desc {
    color: #d6e3f9;
    font-size: 0.92rem;
    line-height: 1.8;
}

.output-shell {
    border: 1px solid rgba(175, 211, 255, 0.48);
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(20, 38, 72, 0.92), rgba(24, 44, 81, 0.92));
    overflow: hidden;
    margin-top: 0.55rem;
}

.output-head {
    border-bottom: 1px solid rgba(168, 203, 251, 0.32);
    padding: 0.55rem 0.85rem;
    color: #d7e9ff;
    font-size: 0.83rem;
    font-weight: 700;
    background: rgba(17, 32, 62, 0.62);
}

.output-body {
    padding: 0.85rem 0.9rem;
    color: #f2f7ff;
    font-size: 0.96rem;
    line-height: 2.15;
    white-space: pre-wrap;
    text-align: right;
    max-width: 860px;
    margin: 0 auto;
}

.output-meta {
    color: #bdd6fb;
    font-size: 0.78rem;
    padding: 0.35rem 0.88rem 0.65rem 0.88rem;
    text-align: left;
}

.divider-soft {
    border-top: 1px solid var(--border-soft);
    margin-top: 0.55rem;
    margin-bottom: 0.55rem;
}

.assessment-status-wrap {
    border: 1px solid rgba(152, 204, 255, 0.5);
    border-radius: 16px;
    background: linear-gradient(160deg, rgba(34, 57, 99, 0.9), rgba(22, 40, 74, 0.92));
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.8rem;
}

.assessment-status-head {
    color: #dcecff;
    font-size: 0.82rem;
    letter-spacing: 0.03em;
    margin-bottom: 0.35rem;
}

.assessment-status-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 0.45rem;
}

.assessment-status-item {
    border: 1px solid rgba(165, 206, 255, 0.38);
    border-radius: 12px;
    background: rgba(16, 30, 58, 0.62);
    padding: 0.42rem 0.55rem;
}

.assessment-status-label {
    color: #a9c4ea;
    font-size: 0.74rem;
}

.assessment-status-value {
    color: #f2f7ff;
    font-size: 0.9rem;
    font-weight: 700;
    margin-top: 0.08rem;
}

.assessment-panel {
    border: 1px solid rgba(160, 201, 255, 0.44);
    border-radius: 16px;
    background: linear-gradient(165deg, rgba(35, 58, 101, 0.86), rgba(24, 42, 76, 0.9));
    padding: 0.78rem 0.85rem;
    margin-bottom: 0.75rem;
    min-height: 120px;
}

.assessment-panel-title {
    color: #f1f7ff;
    font-weight: 800;
    font-size: 0.96rem;
    margin-bottom: 0.34rem;
}

.assessment-panel-desc {
    color: #d2e2f8;
    font-size: 0.87rem;
    line-height: 1.9;
}

.assessment-final-card {
    border: 1px solid rgba(129, 198, 255, 0.5);
    border-radius: 18px;
    background:
        radial-gradient(460px 220px at 88% 18%, rgba(110, 187, 255, 0.18), transparent 58%),
        linear-gradient(150deg, rgba(19, 37, 70, 0.95), rgba(14, 27, 50, 0.96));
    padding: 0.92rem 1rem;
    margin-top: 0.65rem;
}

.assessment-final-title {
    color: #f4f8ff;
    font-size: 1.02rem;
    font-weight: 800;
    margin-bottom: 0.42rem;
}

.assessment-final-body {
    color: #d6e5fa;
    font-size: 0.9rem;
    line-height: 1.95;
}

[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label p {
    color: var(--text-secondary) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label p,
[data-testid="stSidebar"] [data-testid="stCheckbox"] label p {
    color: #c6d9f7 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 0.18rem !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0.16rem 0.2rem !important;
    margin: 0 !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(244, 248, 255, 0.08) !important;
}

@media (max-width: 900px) {
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1.4rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }

    .hero-panel {
        padding: 1rem 1rem 1.15rem 1rem;
    }

    .hero-content {
        max-width: 100%;
    }

    .hero-title {
        font-size: 1.7rem;
    }

    .hero-subtitle {
        font-size: 0.93rem;
        line-height: 1.75;
    }

    .assessment-status-grid {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
"""

st.markdown(RTL_STYLE, unsafe_allow_html=True)


OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_MODEL_OPTIONS = [
    "qwen2.5:3b",
    "qwen2.5:7b",
]
AVALAI_BASE_URL_DEFAULT = "https://api.avalai.ir/v1"
AVALAI_BASE_URL_IR_DEFAULT = "https://api.avalapis.ir/v1"
AVALAI_MODEL_DEFAULT = "gpt-4o-mini"


def get_lessons() -> list[dict]:
    data = load_json(DATA_DIR / "sample_lessons.json", default={"lessons": []})
    return data.get("lessons", [])


def get_prompt_templates() -> dict:
    return load_json(DATA_DIR / "prompt_templates.json", default={"categories": {}})


def get_quiz_questions() -> list[dict]:
    return load_quiz_questions(str(DATA_DIR / "quiz_questions.json"))


def get_book_outline() -> dict:
    return load_json(DATA_DIR / "book_outline.json", default={"chapters": []})


def maybe_generate_with_local_ollama(
    prompt: str, fallback_text: str, model: str = OLLAMA_MODEL
) -> tuple[str, str, str]:
    if not st.session_state.get("use_ollama_local", False):
        return fallback_text, "", "template"

    result = generate_with_ollama(prompt=prompt, model=model)
    if result.get("ok"):
        text = str(result.get("text", "")).strip()
        if text:
            return text, "", "ollama"
        return fallback_text, "پاسخ Ollama خالی بود. خروجی قالب داخلی نمایش داده شد.", "template"

    error_text = str(result.get("error", "خطا در ارتباط با Ollama")).strip()
    lowered = error_text.lower()
    model_not_found = ("پیدا نشد" in error_text) or ("not found" in lowered)

    if model_not_found and model != OLLAMA_MODEL:
        fallback_result = generate_with_ollama(prompt=prompt, model=OLLAMA_MODEL)
        if fallback_result.get("ok"):
            fallback_generated = str(fallback_result.get("text", "")).strip()
            if fallback_generated:
                return (
                    fallback_generated,
                    (
                        f"مدل انتخابی «{model}» موجود نبود؛ "
                        f"به‌صورت خودکار از مدل پیشنهادی MVP یعنی «{OLLAMA_MODEL}» استفاده شد."
                    ),
                    "ollama",
                )

        fallback_error = str(fallback_result.get("error", "")).strip()
        combined = error_text
        if fallback_error:
            combined += f" | خطای fallback به «{OLLAMA_MODEL}»: {fallback_error}"
        return fallback_text, combined, "template"

    return fallback_text, error_text, "template"


def get_selected_ollama_model() -> str:
    selected = str(st.session_state.get("ollama_model_name", OLLAMA_MODEL)).strip()
    return selected or OLLAMA_MODEL


def get_selected_avalai_base_url() -> str:
    from_env = (
        os.getenv("KARISTAN_API_BASE_URL", "").strip()
        or os.getenv("AVALAI_BASE_URL", "").strip()
    )
    selected = str(st.session_state.get("avalai_base_url", from_env)).strip()
    if selected:
        return selected
    return AVALAI_BASE_URL_DEFAULT


def get_selected_avalai_model() -> str:
    from_env = os.getenv("KARISTAN_API_MODEL", "").strip() or os.getenv("AVALAI_MODEL", "").strip()
    selected = str(st.session_state.get("avalai_model_name", from_env)).strip()
    if selected:
        return selected
    return AVALAI_MODEL_DEFAULT


def get_selected_avalai_api_key() -> str:
    from_env = (
        os.getenv("KARISTAN_API_KEY", "").strip()
        or os.getenv("AVALAI_API_KEY", "").strip()
    )
    selected = str(st.session_state.get("avalai_api_key", "")).strip()
    return selected or from_env


def get_api_status_badge() -> tuple[str, str]:
    if not st.session_state.get("use_avalai_api", False):
        return "ℹ️ API غیرفعال است.", "info"

    api_key = get_selected_avalai_api_key()
    base_url = get_selected_avalai_base_url()
    model = get_selected_avalai_model()

    if not api_key:
        return "⚠️ API روشن است اما API Key وارد نشده.", "warning"
    if not base_url:
        return "⚠️ API روشن است اما Base URL خالی است.", "warning"
    if not model:
        return "⚠️ API روشن است اما مدل API مشخص نشده.", "warning"

    # This is a config-level readiness check (not a live request check).
    return "✅ API فعال است (تنظیمات کامل است).", "success"


def run_api_connection_test() -> tuple[str, str]:
    api_key = get_selected_avalai_api_key()
    base_url = get_selected_avalai_base_url()
    model = get_selected_avalai_model()

    if not api_key:
        return "warning", "⚠️ برای تست اتصال، ابتدا API Key را وارد کنید."
    if not base_url:
        return "warning", "⚠️ برای تست اتصال، Base URL را وارد کنید."
    if not model:
        return "warning", "⚠️ برای تست اتصال، نام مدل API را وارد کنید."

    test_result = generate_with_openai_compatible_api(
        prompt="فقط عبارت OK را برگردان.",
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
    if test_result.get("ok"):
        return "success", f"✅ تست اتصال موفق بود. مدل «{model}» پاسخ داد."

    error_text = str(test_result.get("error", "خطای نامشخص در تست اتصال API")).strip()
    return "error", f"❌ تست اتصال ناموفق بود: {error_text}"


def maybe_generate_with_configured_ai(
    prompt: str, fallback_text: str, ollama_model: str = OLLAMA_MODEL
) -> tuple[str, str, str]:
    errors: list[str] = []

    if st.session_state.get("use_avalai_api", False):
        api_result = generate_with_openai_compatible_api(
            prompt=prompt,
            model=get_selected_avalai_model(),
            api_key=get_selected_avalai_api_key(),
            base_url=get_selected_avalai_base_url(),
        )
        if api_result.get("ok"):
            text = str(api_result.get("text", "")).strip()
            if text:
                return text, "", "api"
        errors.append(str(api_result.get("error", "خطا در ارتباط با API")))

    if st.session_state.get("use_ollama_local", False):
        local_text, local_error, local_source = maybe_generate_with_local_ollama(
            prompt=prompt,
            fallback_text=fallback_text,
            model=ollama_model,
        )

        # If local generation produced a non-fallback result, keep it.
        if local_source == "ollama":
            if errors:
                return local_text, "API در دسترس نبود؛ خروجی با Ollama تولید شد.", "ollama"
            return local_text, local_error, "ollama"

        if local_error:
            errors.append(local_error)

    if errors:
        return fallback_text, " | ".join(errors), "template"
    return fallback_text, "", "template"


def format_ai_source(source: str) -> str:
    normalized = str(source or "").strip().lower()
    if normalized == "api":
        return "API"
    if normalized == "ollama":
        return "Ollama"
    return "Template داخلی"


def get_ollama_model_options() -> tuple[list[str], str]:
    result = list_installed_ollama_models()
    if result.get("ok"):
        models = [str(item).strip() for item in result.get("models", []) if str(item).strip()]
        if models:
            return models, ""
        return OLLAMA_MODEL_OPTIONS[:], (
            "هنوز مدلی روی Ollama نصب نشده است. "
            "ابتدا با دستور `ollama pull qwen2.5:3b` یک مدل نصب کنید."
        )

    return OLLAMA_MODEL_OPTIONS[:], str(result.get("error", "خطا در خواندن مدل‌های Ollama"))


def format_ollama_model_label(model_name: str) -> str:
    if str(model_name).strip() == OLLAMA_MODEL:
        return f"{model_name} (پیشنهادی برای MVP)"
    return str(model_name)


def _escape(text: str) -> str:
    return html.escape(str(text or ""))


def _to_ul(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return ""
    return "<ul>" + "".join(f"<li>{_escape(item)}</li>" for item in cleaned) + "</ul>"


def _to_ol(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return ""
    return "<ol>" + "".join(f"<li>{_escape(item)}</li>" for item in cleaned) + "</ol>"


def render_surface_card(title: str, body_html: str) -> None:
    st.markdown(
        f"""
        <div class="surface-card">
            <div class="surface-title">{_escape(title)}</div>
            <div class="surface-body">{body_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prompt_shell(title: str, content: str) -> None:
    st.markdown(f'<div class="prompt-shell-title">{_escape(title)}</div>', unsafe_allow_html=True)
    st.code(content, language="text")


def render_copy_button(copy_text: str, key: str) -> None:
    button_id = f"copy-btn-{key}"
    message_id = f"copy-msg-{key}"
    payload = json.dumps(str(copy_text or ""), ensure_ascii=False)
    components_html(
        f"""
        <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px;">
            <span id="{message_id}" style="color:#d7e8ff;font-size:12px;"></span>
            <button id="{button_id}" style="
                border:1px solid rgba(161,205,255,.58);
                background:linear-gradient(145deg,#1e5fd2,#2d7eff);
                color:#f4f8ff;
                border-radius:10px;
                font-weight:700;
                padding:6px 12px;
                cursor:pointer;
            ">کپی متن</button>
        </div>
        <script>
            const text = {payload};
            const btn = document.getElementById("{button_id}");
            const msg = document.getElementById("{message_id}");
            if (btn) {{
                btn.onclick = async () => {{
                    try {{
                        await navigator.clipboard.writeText(text);
                        msg.textContent = "کپی شد";
                    }} catch (err) {{
                        msg.textContent = "کپی ناموفق";
                    }}
                }};
            }}
        </script>
        """,
        height=44,
    )


def _decode_image_b64_to_bytes(image_b64: str) -> bytes:
    raw = str(image_b64 or "").strip()
    if not raw:
        return b""
    # Support both plain base64 and data URL formats.
    if raw.startswith("data:image") and "," in raw:
        raw = raw.split(",", 1)[1].strip()
    try:
        return base64.b64decode(raw)
    except Exception:
        return b""


def _download_image_url_to_bytes(image_url: str, api_key: str = "") -> bytes:
    url = str(image_url or "").strip()
    if not url:
        return b""

    def _fetch(req: Request) -> bytes:
        with urlopen(req, timeout=25) as resp:
            return resp.read()

    # First try without headers (for public/signed URLs).
    try:
        return _fetch(Request(url, method="GET"))
    except Exception:
        pass

    # Then try with Authorization for providers that protect image URLs.
    token = str(api_key or "").strip()
    if token:
        try:
            req = Request(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "image/*",
                },
                method="GET",
            )
            return _fetch(req)
        except Exception:
            return b""

    return b""


def render_home() -> None:
    book_pdf = Path("promt engineer _virast (100).pdf")
    book_is_ready = book_pdf.exists()
    status_kind = "success" if book_is_ready else "warning"
    status_text = (
        "کتاب مرجع شناسایی شد و نسخه کتاب‌محور فعال است."
        if book_is_ready
        else "فایل کتاب در پروژه یافت نشد؛ برنامه با داده‌های نمونه اجرا می‌شود."
    )

    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-content">
                <h1 class="hero-title">کارستان</h1>
                <p class="hero-subtitle">
                    یادگیری مبتنی بر شبیه‌سازی با هوش مصنوعی
                </p>
                <p class="hero-description">
                    یادگیری، تمرین و ارزیابی مهارت‌های هوش مصنوعی
                    در یک محیط فارسی، تعاملی و کاربردی.
                    <br><br>
                    کارستان برای آموزش واقعی طراحی شده است؛
                    جایی برای ساختن مهارت، تمرین عملی و تجربه کار با ابزارهای هوش مصنوعی.
                </p>
                <div class="hero-badges">
                    <span class="hero-badge">آموزش آفلاین</span>
                    <span class="hero-badge">طراحی پرامپت ساختاریافته</span>
                    <span class="hero-badge">آزمون و گزارش پیشرفت</span>
                    <span class="hero-badge">RTL فارسی حرفه‌ای</span>
                </div>
                <div class="hero-ctas">
                    <span class="hero-cta">شروع یادگیری</span>
                    <span class="hero-cta">ورود به کارگاه عملی</span>
                    <span class="hero-cta">تولید محتوای هوش مصنوعی</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="status-chip {status_kind}">{_escape(status_text)}</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        render_surface_card(
            "ماموریت کارستان",
            (
                "کارستان آموزش هوش مصنوعی را ساده‌تر، کاربردی‌تر و در دسترس‌تر می‌کند."
                "<br>"
                "یک محیط یکپارچه برای یادگیری، تمرین، آزمون و تولید واقعی محتوا."
            ),
        )
    with col2:
        featured_workspaces = [
            "تولید متن با AI",
            "ارزیابی مهارتی شایستگی محور",
            "تولیدگر پرامپت",
            "بهبوددهنده پرامپت",
            "درس‌ها",
            "آزمون آفلاین",
            "نتایج",
        ]
        featured_chips = "".join(
            f'<span class="module-chip">{_escape(item)}</span>' for item in featured_workspaces
        )
        render_surface_card(
            "فضاهای کاری",
            (
                "برای شروع سریع، از گزینه‌های زیر استفاده کنید:"
                f'<div class="module-chip-wrap" style="margin-top:0.55rem;">{featured_chips}</div>'
                "<div style='margin-top:0.45rem;font-size:0.86rem;color:#cfe0f9;'>"
                "همه بخش‌ها از سایدبار در دسترس هستند."
                "</div>"
            ),
        )

    if book_pdf.exists():
        st.success("نسخه کتاب‌محور فعال است: فایل مرجع کتاب در پروژه شناسایی شد.")
    else:
        st.info("فایل PDF کتاب در پوشه پروژه یافت نشد. داده‌های نمونه استفاده می‌شود.")

    st.markdown(
        """
        <div class="home-footer">
            <strong>کارستان</strong><br>
            آموزش متوقف نمی‌شود.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_book_map() -> None:
    st.title("نقشه کتاب مرجع")
    outline = get_book_outline()

    render_surface_card(
        "مرجع محتوا",
        (
            f"عنوان کتاب: <b>{_escape(outline.get('book_title', '-'))}</b><br>"
            f"فایل مرجع: <code>{_escape(outline.get('source_file', '-'))}</code>"
        ),
    )

    chapters = outline.get("chapters", [])
    if not chapters:
        st.warning("نقشه فصل‌ها موجود نیست.")
        return

    for chapter in chapters:
        with st.expander(f"{chapter.get('chapter', '')} - {chapter.get('title', '')}"):
            topics = [str(topic).strip() for topic in chapter.get("topics", []) if str(topic).strip()]
            render_surface_card("سرفصل‌ها", _to_ul(topics) if topics else "سرفصلی ثبت نشده است.")


def render_lessons() -> None:
    st.title("ماژول درس")
    lessons = get_lessons()

    if not lessons:
        st.error("فایل درس‌ها بارگذاری نشد یا خالی است.")
        return

    def _chapter_sort_key(item: dict) -> tuple[int, str]:
        try:
            number = int(item.get("chapter_number", 999))
        except Exception:
            number = 999
        title = str(item.get("chapter_title", "")).strip()
        return number, title

    chapter_map: dict[str, list[dict]] = {}
    for lesson_item in sorted(lessons, key=_chapter_sort_key):
        chapter_number = lesson_item.get("chapter_number", "")
        chapter_title = str(lesson_item.get("chapter_title", "")).strip() or "فصل بدون عنوان"
        chapter_key = f"فصل {chapter_number}: {chapter_title}" if chapter_number else chapter_title
        chapter_map.setdefault(chapter_key, []).append(lesson_item)

    chapter_options = list(chapter_map.keys())
    selected_chapter = st.selectbox("انتخاب فصل", chapter_options)
    chapter_lessons = chapter_map.get(selected_chapter, [])
    if not chapter_lessons:
        st.warning("برای فصل انتخاب‌شده درسی ثبت نشده است.")
        return

    lesson_titles = [
        str(item.get("lesson_title", "")).strip() or f"درس {idx + 1}"
        for idx, item in enumerate(chapter_lessons)
    ]
    selected_lesson_title = st.selectbox("انتخاب درس", lesson_titles)

    lesson = next(
        (
            item
            for item in chapter_lessons
            if (str(item.get("lesson_title", "")).strip() or "") == selected_lesson_title
        ),
        chapter_lessons[0],
    )

    chapter_number = lesson.get("chapter_number", "")
    chapter_title = str(lesson.get("chapter_title", "")).strip()

    pills: list[str] = []
    if chapter_number:
        pills.append(f'<span class="lesson-pill">فصل {chapter_number}</span>')
    if chapter_title:
        pills.append(f'<span class="lesson-pill">{_escape(chapter_title)}</span>')
    if pills:
        st.markdown("".join(pills), unsafe_allow_html=True)

    render_surface_card(
        str(lesson.get("lesson_title", "درس")),
        _escape(str(lesson.get("learning_goal", "-"))),
    )

    tab_explanation, tab_example, tab_practice, tab_assessment = st.tabs(
        [
            "توضیح آموزشی",
            "مثال کتاب‌محور",
            "تمرین و پروژه",
            "ارزیابی",
        ]
    )

    with tab_explanation:
        full_explanation = str(lesson.get("full_explanation", "")).strip() or "-"
        render_surface_card("توضیح کامل", _escape(full_explanation))

        key_concepts = lesson.get("key_concepts", [])
        if isinstance(key_concepts, list) and key_concepts:
            render_surface_card("مفاهیم کلیدی", _to_ul([str(item) for item in key_concepts]))
        else:
            st.info("مفهوم کلیدی برای این درس ثبت نشده است.")

    with tab_example:
        render_surface_card(
            "نمونه مبتنی بر کتاب",
            _escape(str(lesson.get("book_based_example", "-"))),
        )
        render_prompt_shell(
            "نمونه پرامپت ضعیف",
            str(lesson.get("weak_prompt", "-")),
        )
        render_prompt_shell(
            "نسخه بهبودیافته پرامپت",
            str(lesson.get("improved_prompt", "-")),
        )

    with tab_practice:
        render_surface_card(
            "تمرین مهارتی",
            _escape(str(lesson.get("practice_exercise", "-"))),
        )
        render_surface_card(
            "مینی‌پروژه کارگاهی",
            _escape(str(lesson.get("mini_project", "-"))),
        )

    with tab_assessment:
        render_surface_card(
            "پرسش ارزیابی عملی",
            _escape(str(lesson.get("assessment_question", "-"))),
        )
        render_surface_card(
            "پاسخ / معیار مورد انتظار",
            _escape(str(lesson.get("expected_answer", "-"))),
        )


def render_prompt_generator() -> None:
    st.title("تولیدگر پرامپت")
    render_surface_card(
        "طراحی سریع پرامپت",
        "دسته‌بندی و موضوع را انتخاب کنید تا نسخه ساختاریافته نقش، وظیفه، زمینه، خروجی و محدودیت‌ها تولید شود.",
    )
    templates = get_prompt_templates()
    categories = list(templates.get("categories", {}).keys())

    if not categories:
        st.error("قالب‌های پرامپت در دسترس نیست.")
        return

    category = st.selectbox("دسته‌بندی", categories)
    topic = st.text_input("موضوع", placeholder="مثال: آموزش ایمنی کارگاه")

    if st.button("تولید پرامپت ساختاریافته", use_container_width=True):
        result = generate_structured_prompt(category=category, topic=topic, templates_data=templates)
        final_prompt_text = result["final_prompt"]
        ai_source = "template"
        ollama_error = ""

        if st.session_state.get("use_avalai_api", False) or st.session_state.get("use_ollama_local", False):
            ollama_model = get_selected_ollama_model()
            ollama_prompt = (
                "بر اساس اطلاعات زیر، یک پرامپت نهایی حرفه‌ای، روشن و اجرایی به زبان فارسی بنویس.\n"
                "فقط متن نهایی پرامپت را برگردان.\n\n"
                f"نقش: {result['role']}\n"
                f"وظیفه: {result['task']}\n"
                f"زمینه: {result['context']}\n"
                f"قالب خروجی: {result['output_format']}\n"
                "محدودیت‌ها:\n"
                + "\n".join(f"- {item}" for item in result["constraints"])
            )
            final_prompt_text, ollama_error, ai_source = maybe_generate_with_configured_ai(
                prompt=ollama_prompt,
                fallback_text=result["final_prompt"],
                ollama_model=ollama_model,
            )

        if ollama_error:
            st.info(f"{ollama_error} (Fallback: سیستم قالب داخلی)")

        st.markdown("### خروجی ساختاریافته")
        c1, c2 = st.columns(2)
        with c1:
            render_surface_card("نقش", _escape(result["role"]))
            render_surface_card("زمینه", _escape(result["context"]))
        with c2:
            render_surface_card("وظیفه", _escape(result["task"]))
            render_surface_card("قالب خروجی", _escape(result["output_format"]))
        render_surface_card("محدودیت‌ها", _to_ul(result["constraints"]))

        render_prompt_shell("متن نهایی پرامپت", final_prompt_text)
        st.caption(f"منبع تولید: {format_ai_source(ai_source)}")
        st.caption("برای کپی، از آیکون کپی در گوشه کادر استفاده کنید.")

        st.download_button(
            "دانلود پرامپت",
            data=final_prompt_text.encode("utf-8"),
            file_name="karistan_prompt.txt",
            mime="text/plain",
            use_container_width=True,
        )


def render_prompt_improver() -> None:
    st.title("بهبوددهنده پرامپت")
    render_surface_card(
        "بازنویسی هوشمند",
        "پرامپت خام را وارد کنید تا با حفظ هدف، نسخه دقیق‌تر و اجرایی‌تر همراه با تحلیل آموزشی دریافت کنید.",
    )
    raw_prompt = st.text_area(
        "پرامپت خام یا ضعیف خود را وارد کنید",
        height=160,
        placeholder="مثال: درباره مدیریت زمان توضیح بده",
    )

    if st.button("بهبود پرامپت", use_container_width=True):
        if not raw_prompt.strip():
            st.warning("ابتدا یک پرامپت وارد کنید.")
            return

        result = improve_prompt(raw_prompt)
        improved_prompt_text = result["improved_prompt"]
        ai_source = "template"
        ollama_error = ""
        if st.session_state.get("use_avalai_api", False) or st.session_state.get("use_ollama_local", False):
            ollama_model = get_selected_ollama_model()
            ollama_prompt = (
                "پرامپت زیر را با کیفیت بهتر بازنویسی کن.\n"
                "خروجی باید فارسی، کوتاه، شفاف و اجرایی باشد.\n"
                "فقط متن پرامپت بهبودیافته را برگردان.\n\n"
                f"پرامپت اولیه:\n{raw_prompt.strip()}"
            )
            improved_prompt_text, ollama_error, ai_source = maybe_generate_with_configured_ai(
                prompt=ollama_prompt,
                fallback_text=result["improved_prompt"],
                ollama_model=ollama_model,
            )

        if ollama_error:
            st.info(f"{ollama_error} (Fallback: سیستم قالب داخلی)")

        score_col, source_col = st.columns([1, 1.3])
        with score_col:
            st.metric("امتیاز چک‌لیست", f"{result['score_total']} / 5")
        with source_col:
            render_surface_card("منبع تولید", _escape(format_ai_source(ai_source)))

        checklist_df = pd.DataFrame(
            [{"مولفه": key, "امتیاز": value} for key, value in result["checklist"].items()]
        )
        st.dataframe(checklist_df, use_container_width=True, hide_index=True)

        render_surface_card("توضیح بهبودها", _to_ul(result["explanations"]))

        render_prompt_shell("پرامپت بهبودیافته", improved_prompt_text)
        st.caption("برای کپی، از آیکون کپی در گوشه کادر استفاده کنید.")


def render_prompt_teacher() -> None:
    st.title("معلم پرامپت")
    render_surface_card(
        "تحلیل آموزشی پرامپت",
        "پرامپت شما مانند یک سناریوی کلاس بررسی می‌شود: نقاط قوت، نقاط ضعف، عناصر جاافتاده و نسخه بازنویسی‌شده.",
    )
    user_prompt = st.text_area(
        "پرامپت خود را وارد کنید تا به‌صورت آموزشی تحلیل شود",
        height=160,
        placeholder="مثال: یک متن تبلیغاتی برای کلاس آشپزی بنویس",
    )

    if st.button("تحلیل آموزشی پرامپت", use_container_width=True):
        if not user_prompt.strip():
            st.warning("ابتدا پرامپت را وارد کنید.")
            return

        result = teach_prompt(user_prompt)
        rewritten_prompt_text = result["rewritten_prompt"]
        ai_source = "template"
        ollama_error = ""
        if st.session_state.get("use_avalai_api", False) or st.session_state.get("use_ollama_local", False):
            ollama_model = get_selected_ollama_model()
            ollama_prompt = (
                "پرامپت زیر را برای کارآموز فنی به شکل دقیق‌تر بازنویسی کن.\n"
                "نسخه جدید باید نقش، هدف، زمینه، قالب خروجی و محدودیت را روشن کند.\n"
                "فقط متن نسخه بازنویسی‌شده را برگردان.\n\n"
                f"پرامپت اولیه:\n{user_prompt.strip()}"
            )
            rewritten_prompt_text, ollama_error, ai_source = maybe_generate_with_configured_ai(
                prompt=ollama_prompt,
                fallback_text=result["rewritten_prompt"],
                ollama_model=ollama_model,
            )

        if ollama_error:
            st.info(f"{ollama_error} (Fallback: سیستم قالب داخلی)")

        strengths_col, weaknesses_col = st.columns(2)
        with strengths_col:
            render_surface_card("نقاط قوت", _to_ul(result["strengths"]))
        with weaknesses_col:
            render_surface_card("نقاط ضعف", _to_ul(result["weaknesses"]))

        if result["missing_elements"]:
            missing_text = "، ".join(str(item) for item in result["missing_elements"])
        else:
            missing_text = "بخش جاافتاده مهمی دیده نشد."
        render_surface_card("بخش‌های جاافتاده", _escape(missing_text))

        render_prompt_shell("نسخه بازنویسی‌شده بهتر", rewritten_prompt_text)
        st.caption(f"منبع تولید: {format_ai_source(ai_source)}")

        render_surface_card("توضیح ساده برای کارآموز", _escape(result["simple_explanation"]))


def render_text_prompt_studio() -> None:
    st.title("استدیو پرامپت متنی")
    st.markdown(
        """
        <div class="workspace-shell">
            <div class="workspace-kicker">KARISTAN PROMPT STUDIO</div>
            <div class="workspace-title">تولید پرامپت متنی بر اساس قالب‌های داخلی</div>
            <div class="workspace-desc">
                این بخش کاملاً آفلاین کار می‌کند و بدون نیاز به API، یک پرامپت ساختاریافته را از روی قالب
                و موضوعی که وارد می‌کنید می‌سازد.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    templates = get_prompt_templates()
    categories = list(templates.get("categories", {}).keys())
    if not categories:
        st.error("قالب‌های پرامپت در دسترس نیست.")
        return

    with st.form("text_prompt_studio_form"):
        st.markdown('<div class="workspace-form-shell">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.2])
        with c1:
            category = st.selectbox("دسته‌بندی قالب", categories)
        with c2:
            topic = st.text_input(
                "موضوع پرامپت",
                placeholder="مثال: آموزش ایمنی کارگاه",
            )

        topic_hint = st.text_area(
            "توضیح کوتاه یا جزئیات اضافی",
            placeholder="مثال: مخاطب کارآموز فنی است، خروجی باید کوتاه و اجرایی باشد.",
            height=96,
        )
        submitted = st.form_submit_button("تولید پرامپت بر اساس قالب", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        st.caption("یکی از قالب‌ها را انتخاب کنید و سپس موضوع را وارد کنید تا پرامپت نهایی ساخته شود.")
        return

    if not topic.strip():
        st.warning("ابتدا موضوع پرامپت را وارد کنید.")
        return

    effective_topic = topic.strip()
    if topic_hint.strip():
        effective_topic = f"{effective_topic} - {topic_hint.strip()}"

    result = generate_structured_prompt(category=category, topic=effective_topic, templates_data=templates)
    final_prompt_text = result["final_prompt"]
    selected_template = templates.get("categories", {}).get(category, {})

    st.markdown("### خروجی قالب")
    c1, c2 = st.columns(2)
    with c1:
        render_surface_card("نقش", _escape(result["role"]))
        render_surface_card("زمینه", _escape(result["context"]))
    with c2:
        render_surface_card("وظیفه", _escape(result["task"]))
        render_surface_card("قالب خروجی", _escape(result["output_format"]))

    render_surface_card("محدودیت‌ها", _to_ul(result["constraints"]))

    if topic_hint.strip():
        render_surface_card("توضیح اضافه", _escape(topic_hint))

    render_surface_card("قالب انتخابی", _escape(category))
    render_surface_card("الگوی خروجی", _escape(str(selected_template.get("output_format", "-"))))
    render_prompt_shell("پرامپت نهایی", final_prompt_text)
    st.caption("این خروجی از قالب داخلی ساخته شده و برای استفاده در هر مدل زبانی قابل کپی است.")

    render_copy_button(final_prompt_text, "text_prompt_studio")
    st.download_button(
        "دانلود پرامپت",
        data=final_prompt_text.encode("utf-8"),
        file_name="karistan_text_prompt.txt",
        mime="text/plain",
        use_container_width=True,
    )


def render_ai_text_generator_workspace(force_api: bool = False) -> None:
    if not force_api:
        render_text_prompt_studio()
        return

    st.title("تولید متن با AI" if force_api else "استدیو پرامپت متنی")
    st.markdown(
        """
        <div class="workspace-shell">
            <div class="workspace-kicker">KARISTAN AI WRITER</div>
            <div class="workspace-title">تولید متن حرفه‌ای با تکنیک‌های مهندسی پرامپت</div>
            <div class="workspace-desc">
                نوع محتوا، لحن، مخاطب، ساختار و تکنیک‌های پرامپت‌نویسی را انتخاب کنید
                تا متن نهایی با کیفیت انتشاری و قابل اجرا دریافت کنید.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if force_api:
        render_surface_card(
            "حالت اجرا",
            "این مسیر مستقیماً از API استفاده می‌کند و برای تولید متن به مدل OpenAI-Compatible وصل می‌شود.",
        )

    content_type_labels = {
        "article": "مقاله",
        "caption": "کپشن",
        "educational_text": "متن آموزشی",
        "ad_copy": "متن تبلیغاتی",
        "video_script": "اسکریپت ویدیو",
        "report": "گزارش کوتاه",
        "story": "متن داستانی",
    }

    technique_options = [
        "Zero-shot Prompting",
        "Few-shot Prompting",
        "Role Prompting",
        "Contextual Prompting",
        "Step-back Prompting",
        "Chain of Thought",
        "ReAct",
    ]

    tone_options = [
        "رسمی",
        "صمیمی",
        "الهام‌بخش",
        "آموزشی",
        "تحلیلی",
        "مینیمال و مستقیم",
    ]

    audience_options = [
        "عموم کاربران",
        "دانش‌آموز / دانشجو",
        "کارآموز فنی",
        "مدیران کسب‌وکار",
        "مشتری بالقوه",
        "مخاطب شبکه اجتماعی",
    ]

    structure_options = {
        "paragraph": "پاراگرافی",
        "bullet": "لیست گام‌به‌گام",
        "sectioned": "بخش‌بندی شده",
        "script": "اسکریپت صحنه‌ای",
    }

    with st.form("ai_text_generator_form"):
        st.markdown('<div class="workspace-form-shell">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            content_type = st.selectbox(
                "نوع محتوا",
                list(content_type_labels.keys()),
                format_func=lambda item: content_type_labels.get(item, item),
            )
        with c2:
            tone = st.selectbox("لحن", tone_options)
        with c3:
            audience = st.selectbox("مخاطب هدف", audience_options)

        d1, d2 = st.columns([1, 1])
        with d1:
            output_structure = st.selectbox(
                "ساختار خروجی",
                list(structure_options.keys()),
                format_func=lambda item: structure_options.get(item, item),
            )
        with d2:
            max_words_input = st.text_input("سقف کلمات", value="220", placeholder="مثال: 220")

        techniques = st.multiselect(
            "تکنیک‌های پرامپت‌نویسی",
            technique_options,
            default=["Role Prompting", "Contextual Prompting"],
        )

        topic = st.text_input("موضوع اصلی", placeholder="مثال: اهمیت یادگیری مهارت در بازار کار")
        goal = st.text_input("هدف متن", placeholder="مثال: ترغیب به ثبت‌نام")
        include_cta = st.checkbox("در پایان متن CTA داشته باشد", value=True)

        constraints = st.text_area(
            "جزئیات / محدودیت‌ها",
            placeholder="مثال: حداکثر 3 پاراگراف، یک مثال عملی، بدون اغراق",
            height=108,
        )

        submitted = st.form_submit_button("تولید متن", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not topic.strip():
            st.warning("ابتدا موضوع اصلی را وارد کنید.")
            return

        api_mode_enabled = force_api or st.session_state.get("use_avalai_api", False)
        if not api_mode_enabled:
            st.warning("برای این Workspace ابتدا API را فعال کنید.")
            return

        api_key = get_selected_avalai_api_key()
        base_url = get_selected_avalai_base_url()
        model = get_selected_avalai_model()
        if not api_key or not base_url or not model:
            st.warning("تنظیمات API کامل نیست.")
            return

        content_type_label = content_type_labels.get(content_type, content_type)
        structure_label = structure_options.get(output_structure, output_structure)
        techniques_text = "، ".join(techniques) if techniques else "Zero-shot Prompting"
        cta_line = "در پایان متن یک CTA شفاف اضافه کن." if include_cta else "CTA اضافه نشود."
        try:
            max_words = int((max_words_input or "").strip())
        except ValueError:
            st.warning("سقف کلمات باید عدد باشد.")
            return
        if max_words < 50 or max_words > 5000:
            st.warning("سقف کلمات باید بین 50 تا 5000 باشد.")
            return

        generation_prompt_lines = [
            "شما یک نویسنده حرفه‌ای فارسی هستید.",
            "متن نهایی را فقط به زبان فارسی برگردان.",
            "بر اساس تکنیک‌های زیر بنویس:",
            f"تکنیک‌ها: {techniques_text}",
            "",
            f"نوع محتوا: {content_type_label}",
            f"لحن: {tone}",
            f"مخاطب: {audience}",
            f"ساختار خروجی: {structure_label}",
            f"حداکثر کلمات: {max_words}",
            f"موضوع: {topic.strip()}",
            f"هدف: {(goal or '-').strip()}",
            f"محدودیت‌ها: {(constraints or '-').strip()}",
            f"دستور پایانی: {cta_line}",
        ]
        generation_prompt = "\n".join(generation_prompt_lines)

        with st.spinner("در حال تولید متن..."):
            result = generate_with_openai_compatible_api(
                prompt=generation_prompt,
                model=model,
                api_key=api_key,
                base_url=base_url,
            )

        if not result.get("ok"):
            st.error(str(result.get("error", "خطا در تولید متن")))
            return

        st.session_state["ai_text_workspace_output"] = str(result.get("text", "")).strip()
        st.session_state["ai_text_workspace_meta"] = {
            "content_type": content_type_label,
            "tone": tone,
            "audience": audience,
            "structure": structure_label,
            "techniques": techniques_text,
            "max_words": max_words,
            "model": model,
        }

    output_text = str(st.session_state.get("ai_text_workspace_output", "")).strip()
    if output_text:
        meta = st.session_state.get("ai_text_workspace_meta", {})
        render_surface_card(
            "تنظیمات خروجی",
            (
                f"نوع محتوا: <b>{_escape(meta.get('content_type', '-'))}</b> | "
                f"لحن: <b>{_escape(meta.get('tone', '-'))}</b> | "
                f"مخاطب: <b>{_escape(meta.get('audience', '-'))}</b><br>"
                f"ساختار: <b>{_escape(meta.get('structure', '-'))}</b> | "
                f"تکنیک‌ها: <b>{_escape(meta.get('techniques', '-'))}</b> | "
                f"سقف کلمات: <b>{_escape(meta.get('max_words', '-'))}</b><br>"
                f"Model: <code>{_escape(meta.get('model', '-'))}</code>"
            ),
        )

        output_html = _escape(output_text).replace("\n", "<br>")
        text_word_count = len([token for token in output_text.split() if token.strip()])
        st.markdown(
            f"""
            <div class="output-shell">
                <div class="output-head">Generated Text</div>
                <div class="output-body">{output_html}</div>
                <div class="output-meta">Words: {text_word_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_copy_button(output_text, "ai_text_workspace")


def render_image_prompt_studio() -> None:
    st.title("استودیو پرامپت تصویر")
    render_surface_card(
        "Image Prompt Studio",
        "نسخه MVP فقط پرامپت تصویر تولید می‌کند و تصویر واقعی نمی‌سازد. می‌توانید علاوه بر جزئیات هنری، نوع تصویر و تنظیمات انتشار را هم کنترل کنید.",
    )

    with st.expander("ایده و موضوع", expanded=True):
        idea = st.text_input(
            "ایده تصویر",
            placeholder="مثال: کارآموز در حال یادگیری الکترونیک در کارگاه",
        )
        subject = st.text_input("موضوع (Subject)", value="")

    with st.expander("تنظیمات تولید", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            image_type = st.selectbox(
                "نوع تصویر",
                ["آموزشی", "تبلیغاتی", "پوستر", "محصولی", "مفهومی"],
                index=0,
            )
            style = st.text_input("سبک (Style)", value="cinematic educational illustration")
            lighting = st.text_input("نورپردازی (Lighting)", value="soft natural light")
            camera_angle = st.text_input("زاویه دوربین (Camera Angle)", value="eye-level medium shot")

        with col2:
            platform = st.selectbox(
                "پلتفرم هدف",
                ["Instagram", "YouTube Thumbnail", "Website Banner", "Classroom Slide"],
                index=0,
            )
            aspect_ratio = st.selectbox(
                "نسبت تصویر",
                ["1:1", "9:16", "16:9", "4:5"],
                index=0,
            )
            composition = st.text_input("ترکیب‌بندی (Composition)", value="balanced composition with clear focal point")
            colors = st.text_input("رنگ‌ها (Colors)", value="warm educational palette")

    with st.expander("جزئیات خروجی", expanded=False):
        details = st.text_input(
            "جزئیات (Details)",
            value="clear facial expressions, realistic classroom environment",
        )
        quality = st.text_input("کیفیت (Quality)", value="8k, ultra-detailed, sharp focus")
        negative_prompt = st.text_area(
            "نگتیو پرامپت (Negative Prompt)",
            value="blurry, low resolution, noisy background, watermark, text artifacts, distorted anatomy",
            height=100,
        )

    if st.button("تولید پرامپت تصویر", use_container_width=True):
        if not idea.strip() and not subject.strip():
            st.warning("حداقل ایده تصویر یا موضوع را وارد کنید.")
            return

        result = generate_image_prompt(
            idea=idea,
            fields={
                "subject": subject,
                "image_type": image_type,
                "style": style,
                "lighting": lighting,
                "camera_angle": camera_angle,
                "colors": colors,
                "composition": composition,
                "platform": platform,
                "aspect_ratio": aspect_ratio,
                "details": details,
                "quality": quality,
                "negative_prompt": negative_prompt,
            },
        )

        render_surface_card("توضیح فارسی", _escape(result["persian_explanation"]))
        if result.get("settings_summary"):
            render_surface_card("خلاصه تنظیمات", _escape(str(result["settings_summary"])))
        render_prompt_shell("پرامپت تصویر (English)", result["english_prompt"])
        render_prompt_shell("نگتیو پرامپت", result["negative_prompt"])
        render_prompt_shell("بلوک آماده کپی", result["copy_block"])
        st.caption("برای کپی، از آیکون کپی در گوشه کادر استفاده کنید.")


def render_api_image_generation() -> None:
    st.title("تولید تصویر با API")
    render_surface_card(
        "API Image Generator",
        "این بخش فقط برای تولید تصویر واقعی با API است. پرامپت تصویر را وارد کنید و خروجی نهایی را ببینید.",
    )

    image_prompt_input = st.text_area(
        "پرامپت تصویر",
        placeholder="مثال: A vocational classroom in Iran, cinematic style, soft natural light...",
        height=140,
        key="api_image_prompt_input",
    )
    negative_prompt_input = st.text_input(
        "Negative Prompt (اختیاری)",
        value="",
        key="api_image_negative_prompt_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        api_image_model = st.text_input(
            "مدل تصویر API",
            value="gpt-image-1",
            key="api_image_model_name_nav",
            placeholder="مثال: gpt-image-1",
        )
    with col2:
        api_image_size = st.selectbox(
            "سایز تصویر",
            options=["1024x1024", "1536x1024", "1024x1536"],
            index=0,
            key="api_image_size_nav",
        )

    if st.button("تولید تصویر با API", use_container_width=True, key="generate_image_api_nav_btn"):
        if not image_prompt_input.strip():
            st.warning("ابتدا پرامپت تصویر را وارد کنید.")
            return

        if not st.session_state.get("use_avalai_api", False):
            st.warning("برای تولید تصویر، ابتدا API را در سایدبار فعال کنید.")
            return

        api_key = get_selected_avalai_api_key()
        base_url = get_selected_avalai_base_url()
        if not api_key or not base_url:
            st.warning("تنظیمات API کامل نیست. API Key و Base URL را بررسی کنید.")
            return

        full_prompt = image_prompt_input.strip()
        if negative_prompt_input.strip():
            full_prompt += f"\n\nNegative prompt: {negative_prompt_input.strip()}"

        with st.spinner("در حال تولید تصویر با API..."):
            image_result = generate_image_with_openai_compatible_api(
                prompt=full_prompt,
                model=api_image_model,
                api_key=api_key,
                base_url=base_url,
                size=api_image_size,
            )

        if not image_result.get("ok"):
            st.error(str(image_result.get("error", "خطا در تولید تصویر با API")))
            return

        st.success("تولید تصویر با API انجام شد.")
        image_url = str(image_result.get("image_url", "")).strip()
        image_b64 = str(image_result.get("image_b64", "")).strip()
        image_bytes = b""

        if image_b64:
            image_bytes = _decode_image_b64_to_bytes(image_b64)

        if not image_bytes and image_url:
            image_bytes = _download_image_url_to_bytes(
                image_url=image_url,
                api_key=get_selected_avalai_api_key(),
            )

        if image_bytes:
            st.image(
                image_bytes,
                caption=f"خروجی API - مدل {api_image_model}",
                use_container_width=True,
            )
        elif image_url:
            st.warning("تصویر تولید شد، اما لینک مستقیم در مرورگر قابل نمایش نبود.")
            st.markdown(f"[مشاهده لینک تصویر]({image_url})")
        else:
            st.warning("API تصویر ساخت، اما داده قابل نمایش برنگرداند.")


def render_video_prompt_studio() -> None:
    st.title("استودیو پرامپت ویدیو")
    render_surface_card(
        "Video Prompt Studio",
        "نسخه MVP فقط پرامپت و استوری‌بورد ویدیو تولید می‌کند و ویدیوی واقعی نمی‌سازد. می‌توانید علاوه بر مدت، نوع ویدیو و تنظیمات سناریو را هم کنترل کنید.",
    )

    with st.expander("ایده و سناریو", expanded=True):
        idea = st.text_input(
            "ایده ویدیو",
            placeholder="مثال: آموزش گام‌به‌گام رزومه‌نویسی برای کارآموزان",
        )

    with st.expander("تنظیمات تولید", expanded=False):
        duration = st.slider("مدت تقریبی ویدیو (ثانیه)", min_value=20, max_value=180, value=40, step=10)
        scene_count = st.slider("تعداد صحنه‌ها", min_value=3, max_value=6, value=4, step=1)

        col1, col2 = st.columns(2)
        with col1:
            video_type = st.selectbox(
                "نوع ویدیو",
                ["آموزشی", "تبلیغاتی", "داستانی", "گزارشی"],
                index=0,
            )
            style = st.selectbox(
                "سبک بصری",
                [
                    "cinematic educational realism",
                    "documentary classroom",
                    "minimal motion-graphics",
                    "dynamic workshop style",
                ],
                index=0,
            )
            tone = st.selectbox(
                "لحن روایت",
                ["الهام‌بخش و عملی", "رسمی و آموزشی", "دوستانه و ساده", "تحلیلی و دقیق"],
                index=0,
            )

        with col2:
            camera_intensity = st.selectbox(
                "شدت حرکت دوربین",
                ["آرام", "متوسط", "پویا"],
                index=1,
            )
            platform = st.selectbox(
                "پلتفرم هدف",
                ["Instagram Reels", "YouTube", "Aparat", "Classroom Display"],
                index=0,
            )
            aspect_ratio = st.selectbox(
                "نسبت تصویر",
                ["9:16", "16:9", "1:1"],
                index=0,
            )
            audience = st.text_input("مخاطب هدف", value="کارآموزان فنی")

    if st.button("تولید پرامپت ویدیو و استوری‌بورد", use_container_width=True):
        if not idea.strip():
            st.warning("ایده ویدیو را وارد کنید.")
            return

        result = generate_video_prompt(
            idea=idea,
            duration_seconds=duration,
            settings={
                "video_type": video_type,
                "scene_count": scene_count,
                "style": style,
                "platform": platform,
                "aspect_ratio": aspect_ratio,
                "tone": tone,
                "audience": audience,
                "camera_intensity": camera_intensity,
            },
        )

        render_surface_card("مفهوم ویدیو", _escape(result["video_concept"]))
        if result.get("settings_summary"):
            render_surface_card("خلاصه تنظیمات", _escape(str(result["settings_summary"])))

        st.markdown("### استوری‌بورد صحنه‌به‌صحنه")
        storyboard_df = pd.DataFrame(result["storyboard"])
        st.dataframe(storyboard_df, use_container_width=True, hide_index=True)

        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            render_surface_card("حرکت دوربین", _escape(result["camera_movement"]))
            render_surface_card("سبک بصری", _escape(result["visual_style"]))
        with detail_col2:
            render_surface_card("متن نریشن", _escape(result["narration_text"]))

        render_prompt_shell(
            "پرامپت تولید ویدیو (Video Generation Prompt)",
            result["video_generation_prompt"],
        )
        st.caption("برای کپی، از آیکون کپی در گوشه کادر استفاده کنید.")


def _get_stage_feedback(stage_percentage: float) -> str:
    value = float(stage_percentage)
    if value >= 85:
        return "عملکرد پایدار و حرفه‌ای"
    if value >= 70:
        return "قابل قبول، با ظرفیت بهبود"
    if value >= 55:
        return "در حال رشد، نیازمند تمرین هدفمند"
    return "نیازمند بازطراحی و تمرین مجدد"


def _save_assessment_workspace(payload: dict[str, Any]) -> tuple[bool, str]:
    save_path = DATA_DIR / "assessment_workspace_saves.jsonl"
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _contains_any_local(text: str, tokens: list[str]) -> bool:
    lowered = str(text or "").lower()
    return any(token.lower() in lowered for token in tokens)


def _signal_score_local(analysis: dict[str, Any], key: str, fallback: float = 2.0) -> float:
    value = analysis.get("field_scores", {}).get(key)
    if value is None:
        return float(fallback)
    return max(0.0, min(5.0, float(value)))


def _build_official_stage_ratings(stage_payloads: list[dict[str, str]]) -> tuple[list[list[float]], dict[str, Any]]:
    all_text = "\n".join(
        (
            f"{item.get('scenario', '')}\n{item.get('prompt', '')}\n{item.get('evidence', '')}"
            for item in stage_payloads
        )
    )
    global_analysis = analyze_prompt_offline(all_text)
    ratings: list[list[float]] = []

    for idx, payload in enumerate(stage_payloads, start=1):
        stage_text = f"{payload.get('scenario', '')}\n{payload.get('prompt', '')}\n{payload.get('evidence', '')}"
        stage_analysis = analyze_prompt_offline(stage_text)
        low = stage_text.lower()
        model_signal = 5.0 if _contains_any_local(low, ["claude", "gpt-4", "bert", "t5", "llm", "transformer"]) else 2.0
        image_signal = 5.0 if _contains_any_local(low, ["image", "تصویر", "diffusion", "midjourney", "sdxl"]) else 2.0
        video_signal = 5.0 if _contains_any_local(low, ["video", "ویدیو", "انیمیشن", "runway", "sora", "kling"]) else 2.0
        audio_signal = 5.0 if _contains_any_local(low, ["audio", "voice", "tts", "speech", "صوت", "پادکست"]) else 2.0

        if idx == 1:
            row = [
                model_signal,
                _signal_score_local(stage_analysis, "ethical_awareness", 2.0),
                max(_signal_score_local(stage_analysis, "goal", 2.0), _signal_score_local(stage_analysis, "context", 2.0)),
            ]
        elif idx == 2:
            row = [
                (_signal_score_local(stage_analysis, "role", 2.0) + _signal_score_local(stage_analysis, "goal", 2.0)) / 2.0,
                max(_signal_score_local(stage_analysis, "examples", 2.0), _signal_score_local(stage_analysis, "output_format", 2.0)),
                max(_signal_score_local(stage_analysis, "constraints", 2.0), _signal_score_local(stage_analysis, "step_by_step_logic", 2.0)),
                max(_signal_score_local(stage_analysis, "audience", 2.0), _signal_score_local(stage_analysis, "tone", 2.0)),
            ]
        elif idx == 3:
            row = [
                _signal_score_local(stage_analysis, "step_by_step_logic", 2.0),
                max(_signal_score_local(stage_analysis, "examples", 2.0), _signal_score_local(stage_analysis, "constraints", 2.0)),
            ]
        elif idx == 4:
            metric_signal = 5.0 if _contains_any_local(low, ["metric", "kpi", "a/b", "precision", "recall", "feedback"]) else 2.0
            iter_signal = 5.0 if _contains_any_local(low, ["iterate", "iteration", "revise", "بهبود", "بازنگری"]) else 2.0
            row = [metric_signal, iter_signal]
        elif idx == 5:
            content_signal = 5.0 if _contains_any_local(low, ["مقاله", "داستان", "شعر", "کد", "بازاریابی", "article", "story", "poem", "marketing"]) else 2.0
            optimize_signal = max(_signal_score_local(stage_analysis, "tone", 2.0), _signal_score_local(stage_analysis, "output_format", 2.0))
            row = [max(model_signal, content_signal), optimize_signal]
        elif idx == 6:
            row = [
                image_signal,
                max(_signal_score_local(stage_analysis, "visual_style", 2.0), _signal_score_local(stage_analysis, "lighting", 2.0)),
                max(_signal_score_local(stage_analysis, "negative_prompt", 2.0), _signal_score_local(stage_analysis, "constraints", 2.0)),
            ]
        elif idx == 7:
            row = [
                max(video_signal, _signal_score_local(stage_analysis, "camera", 2.0)),
                max(_signal_score_local(stage_analysis, "step_by_step_logic", 2.0), _signal_score_local(stage_analysis, "lighting", 2.0)),
            ]
        elif idx == 8:
            row = [
                max(audio_signal, _signal_score_local(stage_analysis, "voice_tone", 2.0)),
                max(_signal_score_local(stage_analysis, "pace", 2.0), _signal_score_local(stage_analysis, "emotion", 2.0)),
            ]
        else:
            row = [
                5.0 if _contains_any_local(low, ["مسئولیت", "مسئولیت پذیری", "responsibility"]) else 4.0,
                max(_signal_score_local(stage_analysis, "ethical_awareness", 2.0), 4.0),
                5.0 if _contains_any_local(low, ["زمان", "deadline", "time"]) else 4.0,
                5.0 if _contains_any_local(low, ["ایمنی داده", "privacy", "امنیت", "safety"]) else 4.0,
                5.0 if _contains_any_local(low, ["مستند", "documentation", "log", "گزارش"]) else 4.0,
            ]
        ratings.append([max(0.0, min(5.0, float(v))) for v in row])

    return ratings, global_analysis


def render_competency_assessment_engine() -> None:
    st.title("لابراتوار ارزیابی عملی مهارت AI")
    render_surface_card(
        "Karistan Assessment Lab",
        "محیط ارزیابی آفلاین برای تحلیل ساختاری پرامپت، امتیازدهی شایستگی و ثبت نتایج."
    )

    if "assessment_lab_save_status" not in st.session_state:
        st.session_state["assessment_lab_save_status"] = "ثبت نشده"
    if "assessment_lab_ai_source" not in st.session_state:
        st.session_state["assessment_lab_ai_source"] = "template"
    if "assessment_lab_ai_error" not in st.session_state:
        st.session_state["assessment_lab_ai_error"] = ""
    if "assessment_lab_generated_output" not in st.session_state:
        st.session_state["assessment_lab_generated_output"] = ""
    if "assessment_lab_rewrite" not in st.session_state:
        st.session_state["assessment_lab_rewrite"] = ""
    if "assessment_lab_analysis" not in st.session_state:
        st.session_state["assessment_lab_analysis"] = {}
    if "assessment_lab_result" not in st.session_state:
        st.session_state["assessment_lab_result"] = {}
    if "assessment_lab_feedback" not in st.session_state:
        st.session_state["assessment_lab_feedback"] = ""

    lab_tab, dashboard_tab = st.tabs(["محیط ارزیابی عملی", "داشبورد پیشرفت کارآموز"])

    with lab_tab:
        trainee_name = st.text_input("نام کارآموز", key="assessment_lab_trainee_name")
        pass_threshold = st.slider(
            "حد نصاب قبولی (درصد)",
            min_value=50,
            max_value=90,
            value=70,
            step=5,
            key="assessment_lab_pass_threshold",
        )

        st.markdown("### مرحله ۱: پرامپت متنی")
        text_scenario = st.text_area("سناریو متنی", key="assessment_text_scenario", height=90)
        text_prompt = st.text_area("پرامپت متنی", key="assessment_text_prompt", height=180)
        text_evidence = st.text_area("شواهد مرحله متنی (اختیاری)", key="assessment_text_evidence", height=90)

        st.markdown("### مرحله ۲: پرامپت تصویر")
        image_scenario = st.text_area("سناریو تصویر", key="assessment_image_scenario", height=90)
        image_prompt = st.text_area("پرامپت تصویر", key="assessment_image_prompt", height=180)
        image_evidence = st.text_area("شواهد مرحله تصویر (اختیاری)", key="assessment_image_evidence", height=90)

        st.markdown("### مرحله ۳: پرامپت ویدئو")
        video_scenario = st.text_area("سناریو ویدئو", key="assessment_video_scenario", height=90)
        video_prompt = st.text_area("پرامپت ویدئو", key="assessment_video_prompt", height=180)
        video_evidence = st.text_area("شواهد مرحله ویدئو (اختیاری)", key="assessment_video_evidence", height=90)

        c1, c2, c3 = st.columns(3)
        run_assessment = c1.button("ارزیابی آفلاین سه‌مرحله‌ای", use_container_width=True)
        run_api_feedback = c2.button("بازخورد API (اختیاری و بدون امتیاز)", use_container_width=True)
        run_save = c3.button("ذخیره نتیجه", use_container_width=True)
        st.caption("API فقط برای تولید بازخورد متنی است و هیچ امتیاز مستقیمی به نمره آزمون اضافه نمی‌کند.")
        st.caption("فیلدهای شواهد برای مستندسازی و کیفیت بازخورد هستند و بارم مستقیم ندارند.")

        if run_assessment:
            if not text_prompt.strip() or not image_prompt.strip() or not video_prompt.strip():
                st.warning("برای هر سه مرحله، پرامپت را وارد کنید.")
            else:
                text_payload = {"scenario": text_scenario, "prompt": text_prompt, "evidence": text_evidence}
                image_payload = {"scenario": image_scenario, "prompt": image_prompt, "evidence": image_evidence}
                video_payload = {"scenario": video_scenario, "prompt": video_prompt, "evidence": video_evidence}
                attitude_payload = {
                    "scenario": "\n".join([text_scenario, image_scenario, video_scenario]),
                    "prompt": "\n".join([text_prompt, image_prompt, video_prompt]),
                    "evidence": "\n".join([text_evidence, image_evidence, video_evidence]),
                }

                # Map official rubric to 3 practical phases:
                # text -> stages 1..5, image -> stage 6, video -> stages 7..8, attitude -> stage 9
                stage_payloads = [
                    text_payload,
                    text_payload,
                    text_payload,
                    text_payload,
                    text_payload,
                    image_payload,
                    video_payload,
                    video_payload,
                    attitude_payload,
                ]
                ratings, global_analysis = _build_official_stage_ratings(stage_payloads)
                result = evaluate_competency_assessment(
                    stage_ratings=ratings,
                    pass_threshold=float(pass_threshold),
                )
                feedback_text = build_template_feedback(result=result, evidence_text=attitude_payload["evidence"])
                st.session_state["assessment_lab_analysis"] = global_analysis
                st.session_state["assessment_lab_result"] = result
                st.session_state["assessment_lab_feedback"] = feedback_text
                st.session_state["assessment_lab_ai_source"] = "template"
                st.session_state["assessment_lab_ai_error"] = ""

        if run_api_feedback:
            result = st.session_state.get("assessment_lab_result", {})
            fallback_feedback = str(st.session_state.get("assessment_lab_feedback", "")).strip()
            if not result:
                st.warning("ابتدا ارزیابی آفلاین را اجرا کنید.")
            else:
                stage_lines = [
                    f"- {item.get('title', '-')}: {item.get('trainee_score', 0)} از {item.get('max_score', 0)}"
                    for item in list(result.get("stages", []))
                ]
                prompt = (
                    "بازخورد فارسی کوتاه در چهار بخش بده: نقاط قوت، نقاط ضعف، عناصر جاافتاده، پیشنهادهای بهبود.\n\n"
                    + "\n".join(stage_lines)
                )
                enriched_feedback, ai_error, ai_source = maybe_generate_with_configured_ai(
                    prompt=prompt,
                    fallback_text=fallback_feedback or "بازخورد داخلی در دسترس نیست.",
                    ollama_model=get_selected_ollama_model(),
                )
                st.session_state["assessment_lab_feedback"] = enriched_feedback
                st.session_state["assessment_lab_ai_source"] = ai_source
                st.session_state["assessment_lab_ai_error"] = ai_error

        if run_save:
            result = st.session_state.get("assessment_lab_result", {})
            if not trainee_name.strip():
                st.warning("نام کارآموز را وارد کنید.")
            elif not result:
                st.warning("ابتدا ارزیابی آفلاین را اجرا کنید.")
            else:
                stage_rows = result.get("stages", [])
                saved_db, db_error = save_competency_result(
                    trainee_name=trainee_name.strip(),
                    total_score=float(result.get("total_score", 0.0)),
                    max_score=float(result.get("max_score", 100.0)),
                    percentage=float(result.get("percentage", 0.0)),
                    pass_status=str(result.get("pass_status", "نیاز به تمرین بیشتر")),
                    stage_scores_json=json.dumps(stage_rows, ensure_ascii=False),
                    ai_feedback=str(st.session_state.get("assessment_lab_feedback", "")),
                    ai_source=str(st.session_state.get("assessment_lab_ai_source", "template")),
                )
                if not saved_db:
                    st.error(f"خطا در ذخیره SQLite: {db_error}")
                else:
                    st.success("نتیجه ارزشیابی در SQLite ذخیره شد.")
                    st.session_state["assessment_lab_save_status"] = (
                        f"ذخیره شد ({datetime.now().strftime('%H:%M:%S')})"
                    )
                    _save_assessment_workspace(
                        {
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "trainee_name": trainee_name.strip(),
                            "standard_code": "3512100023",
                            "text": {
                                "scenario": text_scenario,
                                "prompt": text_prompt,
                                "evidence": text_evidence,
                            },
                            "image": {
                                "scenario": image_scenario,
                                "prompt": image_prompt,
                                "evidence": image_evidence,
                            },
                            "video": {
                                "scenario": video_scenario,
                                "prompt": video_prompt,
                                "evidence": video_evidence,
                            },
                            "result": result,
                            "feedback": st.session_state.get("assessment_lab_feedback", ""),
                        }
                    )

        result = st.session_state.get("assessment_lab_result", {})
        analysis = st.session_state.get("assessment_lab_analysis", {})
        if analysis:
            detect_fields = [
                ("role", "نقش"),
                ("goal", "هدف"),
                ("context", "زمینه"),
                ("output_format", "قالب خروجی"),
                ("constraints", "محدودیت‌ها"),
                ("audience", "مخاطب"),
                ("tone", "لحن"),
                ("examples", "مثال‌ها"),
                ("step_by_step_logic", "منطق مرحله‌به‌مرحله"),
                ("negative_prompt", "نگتیو پرامپت"),
                ("visual_style", "سبک بصری"),
                ("camera", "دوربین"),
                ("lighting", "نورپردازی"),
                ("voice_tone", "لحن صدا"),
                ("pace", "سرعت/ریتم"),
                ("emotion", "احساس"),
                ("ethical_awareness", "آگاهی اخلاقی"),
            ]
            signal_map = dict(analysis.get("signals", {}))
            score_map = dict(analysis.get("field_scores", {}))
            detect_rows = []
            for key, label in detect_fields:
                detect_rows.append(
                    {
                        "مولفه": label,
                        "وضعیت": "شناسایی شد" if bool(signal_map.get(key, False)) else "جاافتاده",
                        "امتیاز": int(score_map.get(key, 0)),
                    }
                )
            st.markdown("### تشخیص عناصر پرامپت")
            st.dataframe(pd.DataFrame(detect_rows), use_container_width=True, hide_index=True)

        if result:
            stage_rows = list(result.get("stages", []))
            stage_map = {str(item.get("title", "")): float(item.get("trainee_score", 0.0)) for item in stage_rows}
            max_map = {str(item.get("title", "")): float(item.get("max_score", 0.0)) for item in stage_rows}

            text_titles = [
                "شناسایی و تحلیل",
                "ساختار و اجزای پرامپت",
                "تکنیک های پیشرفته مهندسی پرامپت",
                "ارزیابی و بهبود پرامپت",
                "تولید محتوای متنی",
                "معیار نگرشی",
            ]
            image_titles = ["تولید تصویر"]
            video_titles = ["تولید ویدیو و انیمیشن", "تولید محتوای صوتی"]

            text_score = sum(stage_map.get(title, 0.0) for title in text_titles)
            text_max = sum(max_map.get(title, 0.0) for title in text_titles)
            image_score = sum(stage_map.get(title, 0.0) for title in image_titles)
            image_max = sum(max_map.get(title, 0.0) for title in image_titles)
            video_score = sum(stage_map.get(title, 0.0) for title in video_titles)
            video_max = sum(max_map.get(title, 0.0) for title in video_titles)

            st.markdown("### نتیجه سه مرحله آزمون")
            section_df = pd.DataFrame(
                [
                    {"بخش": "متنی", "امتیاز": round(text_score, 2), "از": round(text_max, 2)},
                    {"بخش": "تصویر", "امتیاز": round(image_score, 2), "از": round(image_max, 2)},
                    {"بخش": "ویدئو", "امتیاز": round(video_score, 2), "از": round(video_max, 2)},
                ]
            )
            st.dataframe(section_df, use_container_width=True, hide_index=True)

            total_score = float(result.get("total_score", 0.0))
            status_text = "قبول" if total_score >= float(pass_threshold) else "نیاز به تمرین بیشتر"
            ai_source = str(st.session_state.get("assessment_lab_ai_source", "template")).strip()
            st.markdown(
                f"""
                <div class="assessment-final-card">
                    <div class="assessment-final-title">نتیجه نهایی</div>
                    <div class="assessment-final-body">
                        امتیاز کل: <b>{total_score}</b> از <b>100</b><br/>
                        وضعیت: <b>{_escape(status_text)}</b><br/>
                        سطح مهارتی: <b>{_escape(classify_skill_level(float(result.get("percentage", 0.0))))}</b><br/>
                        امتیاز API: <b>0</b> (فقط بازخورد متنی)<br/>
                        منبع بازخورد: <b>{_escape(format_ai_source(ai_source))}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            feedback_text = str(st.session_state.get("assessment_lab_feedback", "")).strip()
            if feedback_text:
                render_prompt_shell("بازخورد فارسی", feedback_text)

    with dashboard_tab:
        rows, error = fetch_competency_results()
        if error:
            st.error(f"خطا در خواندن نتایج شایستگی: {error}")
            return
        if not rows:
            st.info("هنوز هیچ ارزیابی مهارتی ثبت نشده است.")
            return

        df = pd.DataFrame(rows)
        df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce").fillna(0.0)
        df["total_score"] = pd.to_numeric(df["total_score"], errors="coerce").fillna(0.0)
        df["max_score"] = pd.to_numeric(df["max_score"], errors="coerce").fillna(0.0)

        trainee_names = sorted(
            [str(item).strip() for item in df["trainee_name"].dropna().unique() if str(item).strip()]
        )
        selected_trainee = st.selectbox("فیلتر کارآموز", ["همه کارآموزان"] + trainee_names)
        filtered_df = (
            df
            if selected_trainee == "همه کارآموزان"
            else df[df["trainee_name"].astype(str) == selected_trainee]
        )

        pass_rate = (
            round((filtered_df["pass_status"].astype(str) == "قبول").mean() * 100.0, 2)
            if len(filtered_df) > 0
            else 0.0
        )
        avg_score = round(float(filtered_df["percentage"].mean()), 2) if len(filtered_df) > 0 else 0.0

        d1, d2, d3 = st.columns(3)
        d1.metric("تعداد ارزیابی", int(len(filtered_df)))
        d2.metric("میانگین شایستگی", f"{avg_score}%")
        d3.metric("نرخ قبولی", f"{pass_rate}%")

        st.markdown("### روند پیشرفت")
        trend_df = (
            filtered_df[["created_at", "percentage"]]
            .copy()
            .sort_values("created_at")
            .rename(columns={"created_at": "زمان", "percentage": "شایستگی"})
        )
        if len(trend_df) > 0:
            st.line_chart(trend_df.set_index("زمان"))

        stage_records: list[dict[str, Any]] = []
        for _, row in filtered_df.iterrows():
            raw_json = str(row.get("stage_scores_json", "")).strip()
            if not raw_json:
                continue
            try:
                stage_items = json.loads(raw_json)
            except Exception:
                continue
            if not isinstance(stage_items, list):
                continue
            for stage in stage_items:
                stage_records.append(
                    {
                        "مرحله": str(stage.get("title", "-")),
                        "درصد مرحله": float(stage.get("stage_percentage", 0.0)),
                    }
                )

        if stage_records:
            stage_avg_df = (
                pd.DataFrame(stage_records)
                .groupby("مرحله", as_index=False)["درصد مرحله"]
                .mean()
                .sort_values("درصد مرحله", ascending=False)
            )
            st.markdown("### میانگین شایستگی هر مرحله")
            st.dataframe(stage_avg_df, use_container_width=True, hide_index=True)

        view_df = filtered_df[
            [
                "id",
                "trainee_name",
                "total_score",
                "max_score",
                "percentage",
                "pass_status",
                "ai_source",
                "created_at",
            ]
        ].rename(
            columns={
                "id": "شناسه",
                "trainee_name": "نام کارآموز",
                "total_score": "امتیاز کل",
                "max_score": "حداکثر امتیاز",
                "percentage": "درصد",
                "pass_status": "وضعیت",
                "ai_source": "منبع تحلیل",
                "created_at": "تاریخ/ساعت",
            }
        )
        st.markdown("### ثبت های ارزیابی مهارتی")
        st.dataframe(view_df, use_container_width=True, hide_index=True)

        csv_data = view_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "خروجی CSV ارزیابی مهارتی",
            data=csv_data,
            file_name="karistan_competency_results.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_quiz() -> None:
    st.title("آزمون آفلاین")
    render_surface_card(
        "ارزیابی کارآموز",
        "آزمون را تکمیل کنید تا نمره، درصد و تحلیل پاسخ‌ها ثبت شود. نتایج به‌صورت محلی در SQLite ذخیره خواهند شد.",
    )
    all_questions = get_quiz_questions()

    if len(all_questions) < 1:
        st.error("سوالات آزمون بارگذاری نشد.")
        return

    exam_type_map = {
        "آزمون جامع": "comprehensive",
        "آزمون هر فصل": "chapter",
    }
    selected_mode_label = st.radio(
        "نوع آزمون", list(exam_type_map.keys()), horizontal=True
    )
    exam_type = exam_type_map[selected_mode_label]

    selected_chapter = ""
    questions = all_questions
    selection_mode_key = "all"
    if exam_type == "chapter":
        chapters = get_available_chapters(all_questions)
        if not chapters:
            st.warning(
                "برای فعال شدن آزمون فصل‌به‌فصل، باید فیلد `chapter_reference` در بانک سوالات تکمیل شود."
            )
            st.info("در حال حاضر فقط آزمون جامع قابل استفاده است.")
            return

        selected_chapter = st.selectbox("انتخاب فصل", chapters)
        chapter_questions = filter_questions_by_chapter(all_questions, selected_chapter)
        if not chapter_questions:
            st.warning("برای فصل انتخاب‌شده سوالی یافت نشد.")
            return

        max_questions = len(chapter_questions)
        st.caption(f"تعداد کل سوالات موجود در این فصل: {max_questions}")
        selection_mode = st.radio(
            "روش انتخاب سوال",
            ["بدون تکرار", "با تکرار (برای تعداد بیشتر از بانک فصل)"],
            horizontal=True,
        )

        if selection_mode == "با تکرار (برای تعداد بیشتر از بانک فصل)":
            selection_mode_key = "repeat"
            selected_count = int(
                st.number_input(
                    "تعداد سوال این فصل",
                    min_value=1,
                    max_value=50,
                    value=min(10, 50),
                    step=1,
                )
            )
            questions = [random.choice(chapter_questions) for _ in range(selected_count)]
            if selected_count > max_questions:
                st.info("به دلیل محدودیت بانک این فصل، بعضی سوال‌ها تکراری نمایش داده می‌شوند.")
        else:
            selection_mode_key = "unique"
            selected_count = int(
                st.number_input(
                    "تعداد سوال این فصل",
                    min_value=1,
                    max_value=max_questions,
                    value=min(5, max_questions),
                    step=1,
                )
            )
            shuffled_questions = chapter_questions[:]
            random.shuffle(shuffled_questions)
            questions = shuffled_questions[:selected_count]

    render_surface_card("مشخصات آزمون", f"تعداد سوالات این آزمون: <b>{len(questions)}</b>")

    chapter_key = selected_chapter.replace(" ", "_") if selected_chapter else "all"
    question_key_prefix = f"{exam_type}_{chapter_key}_{selection_mode_key}_{len(questions)}"
    with st.form(f"quiz_form_{question_key_prefix}"):
        trainee_name = st.text_input("نام کارآموز")
        answers_map: dict[int, int] = {}
        compact_mode = st.checkbox("نمایش فشرده سوالات (آکاردئونی)", value=True)

        for idx, question in enumerate(questions):
            question_title = f"سوال {idx + 1}"
            if compact_mode:
                with st.expander(question_title, expanded=(idx == 0)):
                    st.markdown(f"**{question['question']}**")
                    choice = st.radio(
                        "گزینه درست را انتخاب کنید",
                        options=question["options"],
                        index=None,
                        key=f"quiz_{question_key_prefix}_q_{idx}",
                        label_visibility="collapsed",
                    )
            else:
                st.markdown(f"**{idx + 1}. {question['question']}**")
                choice = st.radio(
                    "گزینه درست را انتخاب کنید",
                    options=question["options"],
                    index=None,
                    key=f"quiz_{question_key_prefix}_q_{idx}",
                    label_visibility="collapsed",
                )
            if choice is not None:
                answers_map[idx] = question["options"].index(choice)

        submit = st.form_submit_button("ارسال آزمون و محاسبه نمره")

    if submit:
        if not trainee_name.strip():
            st.warning("نام کارآموز را وارد کنید.")
            return

        if len(answers_map) != len(questions):
            st.warning("لطفاً به همه سوالات پاسخ دهید.")
            return

        score, details = evaluate_answers(questions, answers_map)
        total = len(questions)
        percentage = calculate_percentage(score, total)
        status = get_status(percentage)

        saved, error = save_quiz_result(
            trainee_name=trainee_name.strip(),
            score=score,
            total=total,
            percentage=percentage,
            exam_type=exam_type,
            chapter_reference=selected_chapter,
        )
        if not saved:
            st.error(f"خطا در ذخیره نتیجه آزمون: {error}")
            return

        st.session_state["last_quiz_result"] = {
            "trainee_name": trainee_name.strip(),
            "score": score,
            "total": total,
            "percentage": percentage,
            "status": status,
            "details": details,
            "exam_type": exam_type,
            "chapter_reference": selected_chapter,
        }

    result = st.session_state.get("last_quiz_result")
    if result:
        result_exam_type = str(result.get("exam_type", "comprehensive")).strip().lower()
        result_chapter = str(result.get("chapter_reference", "")).strip()
        result_exam_label = (
            "آزمون هر فصل" if result_exam_type == "chapter" else "آزمون جامع"
        )

        render_surface_card(
            f"نتیجه: {result['trainee_name']}",
            f"نوع آزمون: <b>{_escape(result_exam_label)}</b>",
        )
        if result_chapter:
            st.markdown(f'<span class="lesson-pill">فصل: {_escape(result_chapter)}</span>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("نمره", f"{result['score']} از {result['total']}")
        c2.metric("درصد", f"{result['percentage']}%")
        c3.metric("وضعیت", result["status"])

        st.markdown("### پاسخ‌نامه و توضیحات")
        for idx, item in enumerate(result["details"], start=1):
            state = "درست" if item["is_correct"] else "نادرست"
            with st.expander(f"سوال {idx} - {state}"):
                st.write(item["question"])
                user_idx = item["user_answer_index"]
                if user_idx >= 0:
                    st.write(f"پاسخ شما: {item['options'][user_idx]}")
                else:
                    st.write("پاسخ شما: ثبت نشده")
                st.write(f"پاسخ صحیح: {item['options'][item['correct_answer_index']]}")
                st.write(f"توضیح: {item['explanation']}")


def render_results() -> None:
    st.title("نتایج آزمون")
    render_surface_card(
        "داشبورد نتایج",
        "تمام خروجی‌های آزمون در این صفحه قابل مشاهده و دانلود هستند.",
    )
    rows, error = fetch_results()

    if error:
        st.error(f"خطا در خواندن نتایج: {error}")
        return

    if not rows:
        st.info("هنوز نتیجه‌ای ثبت نشده است.")
        return

    df = pd.DataFrame(rows)
    if "exam_type" not in df.columns:
        df["exam_type"] = "comprehensive"
    if "chapter_reference" not in df.columns:
        df["chapter_reference"] = ""

    df["exam_type"] = df["exam_type"].fillna("comprehensive").astype(str).str.strip().str.lower()
    df["exam_type"] = df["exam_type"].replace("", "comprehensive")
    df["exam_label"] = df["exam_type"].apply(
        lambda value: "آزمون هر فصل" if value == "chapter" else "آزمون جامع"
    )
    df["chapter_reference"] = df["chapter_reference"].fillna("").astype(str).str.strip()
    df.loc[df["chapter_reference"] == "", "chapter_reference"] = "-"
    df["status"] = df["percentage"].apply(get_status)
    view_df = df[
        [
            "id",
            "trainee_name",
            "exam_label",
            "chapter_reference",
            "score",
            "total",
            "percentage",
            "status",
            "created_at",
        ]
    ].rename(
        columns={
            "id": "شناسه",
            "trainee_name": "نام کارآموز",
            "exam_label": "نوع آزمون",
            "chapter_reference": "فصل",
            "score": "نمره",
            "total": "از",
            "percentage": "درصد",
            "status": "وضعیت",
            "created_at": "تاریخ/ساعت",
        }
    )

    st.dataframe(view_df, use_container_width=True, hide_index=True)

    csv_data = view_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "خروجی CSV نتایج",
        data=csv_data,
        file_name="karistan_quiz_results.csv",
        mime="text/csv",
        use_container_width=True,
    )


def main() -> None:
    ok, db_error = init_db()
    if not ok:
        st.error(f"خطا در آماده‌سازی پایگاه‌داده: {db_error}")
        st.stop()

    pages = {
        "خانه": render_home,
        "نقشه کتاب مرجع": render_book_map,
        "درس‌ها": render_lessons,
        "ارزشیابی عملی": render_competency_assessment_engine,
        "بهبوددهنده پرامپت": render_prompt_improver,
        "تولید متن با AI": lambda: render_ai_text_generator_workspace(force_api=True),
        "استدیو پرامپت متنی": render_text_prompt_studio,
        "استدیو پرامپت تصویر": render_image_prompt_studio,
        "استدیو پرامپت ویدئو": render_video_prompt_studio,
        "تولید تصویر با API": render_api_image_generation,
        "تولیدگر پرامپت": render_prompt_generator,
        "معلم پرامپت": render_prompt_teacher,
        "آزمون آفلاین": render_quiz,
        "نتایج": render_results,
    }

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Karistan</div>
            <div class="sidebar-brand-sub">Premium Prompt Learning Platform</div>
            <div class="sidebar-brand-sub">آموزش متوقف نمی‌شود</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="sidebar-section-title">ناوبری</div>', unsafe_allow_html=True)
    selected_page = st.sidebar.radio("ناوبری", list(pages.keys()), label_visibility="collapsed")
    st.sidebar.caption("انتخاب صفحه")

    if selected_page == "استدیو پرامپت متنی":
        st.sidebar.markdown(
            '<div class="status-chip info">ℹ️ این صفحه بدون API کار می‌کند و فقط از قالب‌های داخلی استفاده می‌کند.</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.sidebar.expander("اتصال API", expanded=(selected_page == "تولید متن با AI")):
            st.caption("این بخش برای صفحاتی است که خروجی را از API می‌گیرند.")
            st.checkbox("استفاده از API (AvalAI / OpenAI-Compatible)", key="use_avalai_api")
            if selected_page == "تولید متن با AI" or st.session_state.get("use_avalai_api", False):
                default_base_url = (
                    os.getenv("KARISTAN_API_BASE_URL", "").strip()
                    or os.getenv("AVALAI_BASE_URL", "").strip()
                    or AVALAI_BASE_URL_DEFAULT
                )
                default_model = (
                    os.getenv("KARISTAN_API_MODEL", "").strip()
                    or os.getenv("AVALAI_MODEL", "").strip()
                    or AVALAI_MODEL_DEFAULT
                )
                st.text_input(
                    "Base URL (AvalAI)",
                    key="avalai_base_url",
                    value=default_base_url,
                    placeholder="https://api.avalai.ir/v1",
                )
                st.text_input(
                    "مدل API",
                    key="avalai_model_name",
                    value=default_model,
                    placeholder="gpt-4o-mini",
                )
                st.text_input(
                    "API Key",
                    key="avalai_api_key",
                    type="password",
                    placeholder="ak-...",
                )
                st.caption(
                    "اگر در پنل AvalAI مسیر `/openai` دارید، همان مسیر را در Base URL وارد کنید."
                )
                if st.button("تست اتصال API", use_container_width=True, key="avalai_test_connection_btn"):
                    with st.spinner("در حال تست اتصال API..."):
                        kind, text = run_api_connection_test()
                    st.session_state["avalai_live_status_kind"] = kind
                    st.session_state["avalai_live_status_text"] = text

        status_text, status_kind = get_api_status_badge()
        if selected_page == "تولید متن با AI" and not st.session_state.get("use_avalai_api", False):
            status_text = "ℹ️ صفحه تولید متن با AI از API استفاده می‌کند."
            status_kind = "info"
        st.sidebar.markdown(
            f'<div class="status-chip {status_kind}">{_escape(status_text)}</div>',
            unsafe_allow_html=True,
        )

        live_kind = str(st.session_state.get("avalai_live_status_kind", "")).strip().lower()
        live_text = str(st.session_state.get("avalai_live_status_text", "")).strip()
        if live_text:
            live_class = "success" if live_kind == "success" else "warning" if live_kind == "warning" else "error"
            st.sidebar.markdown(
                f'<div class="status-chip {live_class}">{_escape(live_text)}</div>',
                unsafe_allow_html=True,
            )

        with st.sidebar.expander("مدل لوکال Ollama", expanded=False):
            st.checkbox("استفاده از مدل لوکال Ollama", key="use_ollama_local")
            if st.session_state.get("use_ollama_local", False):
                model_options, model_info = get_ollama_model_options()
                current_model = str(st.session_state.get("ollama_model_name", OLLAMA_MODEL)).strip()
                preferred_model = (
                    OLLAMA_MODEL
                    if OLLAMA_MODEL in model_options
                    else (model_options[0] if model_options else OLLAMA_MODEL)
                )
                if current_model not in model_options:
                    current_model = preferred_model
                    st.session_state["ollama_model_name"] = current_model

                current_index = model_options.index(current_model) if model_options else 0
                st.selectbox(
                    "مدل Ollama",
                    options=model_options,
                    index=current_index,
                    key="ollama_model_name",
                    format_func=format_ollama_model_label,
                )
                if model_info:
                    st.markdown(
                        f'<div class="status-chip info">{_escape(model_info)}</div>',
                        unsafe_allow_html=True,
                    )
                st.caption("برای افزودن مدل جدید، ابتدا در ترمینال: `ollama pull <model>`")

    try:
        pages[selected_page]()
    except Exception as exc:
        st.error(f"خطای غیرمنتظره در ماژول «{selected_page}»: {exc}")


if __name__ == "__main__":
    main()

