"""Рекомендации по доработке темы: шаблон или LLM (OpenAI-совместимый API, если настроен)."""
import httpx

from . import config

TIPS = [
    "Покажите другой кейс или отрасль, чем в архивном докладе.",
    "Смените глубину: от обзора к разбору конкретных артефактов и цифр.",
    "Опишите, что слушатель сможет применить завтра и чем это отличается от уже звучавшего.",
]


def template(top: dict) -> str:
    asp = ", ".join(top["aspects"]) or "общая тематика"
    return (
        f"Близкий доклад: «{top['title']}» (Analyst Days {top['conference_number']}, {top['year']}). "
        f"Совпадают элементы: {asp}. {' '.join(TIPS)} "
        "Укажите в аннотации, что нового вы добавляете по сравнению с этим докладом."
    )


def _llm(annotation: str, top: dict) -> str | None:
    if not (config.LLM_BASE_URL and config.LLM_API_KEY and config.LLM_MODEL):
        return None
    prompt = (
        "Ты помогаешь автору доклада на конференции Analyst Days. Аннотация автора:\n"
        f"{annotation}\n\nПохожий ранее принятый доклад: «{top['title']}» "
        f"(Analyst Days {top['conference_number']}, {top['year']}).\n"
        "Кратко (3-4 предложения, по-русски) объясни, что совпадает, и предложи, как изменить ракурс темы."
    )
    try:
        r = httpx.post(
            f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
            json={"model": config.LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 300},
            timeout=config.LLM_TIMEOUT,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        return text or None
    except Exception:
        return None


def build(annotation: str, top: dict) -> tuple[str, str]:
    text = _llm(annotation, top)
    if text:
        return text, "LLM"
    return template(top), "шаблон"
