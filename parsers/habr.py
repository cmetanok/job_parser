"""Парсер вакансий Habr Career"""

import requests
from bs4 import BeautifulSoup

API_URL = "https://career.habr.com/api/frontend/vacancies"
VACANCY_URL = "https://career.habr.com/vacancies/{id}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_habr(query: str, pages: int = 2) -> list[dict]:
    vacancies = []
    for page in range(1, pages + 1):
        try:
            resp = requests.get(
                API_URL,
                params={"q": query, "page": page},
                headers=HEADERS,
                timeout=15,
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            items = data.get("list", [])
            if not items:
                break
            for v in items:
                vacancies.append(_parse_habr(v))
        except Exception:
            break
    return vacancies


def _parse_habr(v: dict) -> dict:
    salary = v.get("salary") or {}
    skills = v.get("skills", []) or []
    location = v.get("location", {})
    city = location.get("title") if isinstance(location, dict) else str(location) if location else ""

    # Проверяем remote из API (структурированное поле)
    remote = bool(v.get("remote", False))
    if not remote and v.get("work_format"):
        remote = str(v.get("work_format")).lower() == "remote"

    # Если API не дал ответа — проверяем HTML-страницу
    if not remote:
        remote = _check_remote_from_html(v.get("id"))

    return {
        "source": "Habr Career",
        "id": str(v.get("id")),
        "name": v.get("title"),
        "company": (v.get("company") or {}).get("title"),
        "city": city,
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "currency": salary.get("currency", "RUR"),
        "url": f"https://career.habr.com/vacancies/{v.get('id')}",
        "published_at": v.get("publishedAt"),
        "experience": v.get("qualification"),
        "skills": ", ".join(s.get("title", "") for s in skills if isinstance(s, dict)),
        "remote": remote,
    }


def _check_remote_from_html(vacancy_id) -> bool:
    """Проверrf страницs вакансии на наличие метки «Можно удалённо»."""
    if not vacancy_id:
        return False
    try:
        resp = requests.get(
            VACANCY_URL.format(id=vacancy_id),
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return False

        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = soup.get_text().lower()
        return "можно удалённо" in page_text or "удалённо" in page_text
    except Exception:
        return False