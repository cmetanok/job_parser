"""Парсер вакансий с портала «Работа России» (Trudvsem)"""

import requests

API_URL = "https://opendata.trudvsem.ru/api/v1/vacancies"


def fetch_trudvsem(query: str, limit: int = 100) -> list[dict]:
    """Сбор вакансий с Trudvsem."""
    vacancies = []
    try:
        resp = requests.get(
            API_URL,
            params={"text": query, "limit": limit, "offset": 0},
            timeout=30,
        )
        if resp.status_code != 200:
            return vacancies

        data = resp.json()
        raw = data.get("results", {}).get("vacancies", [])

        for item in raw:
            vac = item.get("vacancy", {})
            vacancies.append(_parse_trudvsem(vac))
    except Exception:
        pass
    return vacancies


def _parse_trudvsem(v: dict) -> dict:
    # Собираем все текстовые поля для анализа
    schedule = str(v.get("schedule") or "").lower()
    employment_type = str(v.get("employment_type") or "").lower()
    requirements = str(v.get("requirements") or "").lower()
    title = str(v.get("job-name") or "").lower()

    company_name = ""
    if v.get("company") and isinstance(v.get("company"), dict):
        company_name = str(v["company"].get("name") or "").lower()

    haystack = f"{schedule} {employment_type} {requirements} {title} {company_name}"

    remote_markers = [
        "удален", "удалён", "remote", "дистанцион",
        "из любой точки", "home office", "work from home",
    ]

    remote = any(marker in haystack for marker in remote_markers)
    if not remote and "удален" in employment_type:
        remote = True

    return {
        "source": "Trudvsem",
        "id": str(v.get("id")),
        "name": v.get("job-name"),
        "company": (v.get("company") or {}).get("name"),
        "city": (v.get("region") or {}).get("name"),
        "salary_from": v.get("salary_min") or None,
        "salary_to": v.get("salary_max") or None,
        "currency": "RUR",
        "url": v.get("vac_url"),
        "published_at": v.get("creation-date"),
        "experience": v.get("experience"),
        "skills": (v.get("requirements") or "")[:200] if v.get("requirements") else "",
        "remote": remote,
    }