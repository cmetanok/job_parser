"""Streamlit-дашборд для анализа вакансий с Habr Career и Trudvsem."""

import streamlit as st
import pandas as pd
import plotly.express as px

from parsers import fetch_habr, fetch_trudvsem

# --- Настройка страницы ---
st.set_page_config(
    page_title="Аналитика вакансий",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Вспомогательные функции ---
def normalize_grade(experience_str):
    if not experience_str:
        return "Не указан"
    s = str(experience_str).lower()
    if "junior" in s or "стажер" in s or "intern" in s or "без опыта" in s:
        return "Junior"
    if "middle" in s:
        return "Middle"
    if "senior" in s or "lead" in s or "ведущий" in s:
        return "Senior"
    if "1" in s and "3" in s:
        return "1-3 года"
    if "3" in s and "6" in s:
        return "3-6 лет"
    if "6" in s or "более" in s:
        return "Более 6 лет"
    return "Не указан"


def source_badge_class(source):
    if "Habr" in source:
        return "badge-habr"
    if "Trud" in source:
        return "badge-trud"
    return "badge-exp"


def grade_badge_class(grade):
    if grade == "Junior":
        return "badge-junior"
    if grade == "Middle":
        return "badge-middle"
    if grade == "Senior":
        return "badge-senior"
    return "badge-exp"


def format_salary(value):
    if value is None or pd.isna(value):
        return None
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return None


def build_vacancy_card(row):
    source_cls = source_badge_class(row["source"])
    grade_cls = grade_badge_class(row["grade_normalized"])

    salary_parts = []
    sf = format_salary(row.get("salary_from"))
    st_ = format_salary(row.get("salary_to"))
    if sf:
        salary_parts.append(f"от {sf}")
    if st_:
        salary_parts.append(f"до {st_}")
    salary_text = " ".join(salary_parts) + " ₽" if salary_parts else "зарплата не указана"

    remote_badge = ""
    if row.get("remote"):
        remote_badge = '<span class="badge badge-remote">Удалёнка</span>'

    skills_html = ""
    if row.get("skills"):
        skills_html = f'<div class="vacancy-skills">{row["skills"][:200]}</div>'

    return (
        f'<div class="vacancy-card">'
        f'<div class="vacancy-title">{row["name"]}</div>'
        f'<div class="vacancy-meta">'
        f'<span class="badge {source_cls}">{row["source"]}</span>'
        f'<span class="badge {grade_cls}">{row["grade_normalized"]}</span>'
        f'{remote_badge}'
        f'</div>'
        f'<div class="vacancy-meta">Компания: {row["company"] or "—"} &nbsp;·&nbsp; '
        f'Город: {row["city"] or "—"} &nbsp;·&nbsp; {salary_text}</div>'
        f'{skills_html}'
        f'<a class="vacancy-link" href="{row["url"]}" target="_blank">Открыть вакансию →</a>'
        f'</div>'
    )


# --- Кэширование парсинга ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all(query: str, sources: tuple, pages: int) -> pd.DataFrame:
    """Собирает вакансии из выбранных источников. Кэшируется на 1 час."""
    all_vacancies = []
    if "Habr Career" in sources:
        all_vacancies.extend(fetch_habr(query, pages=pages))
    if "Trudvsem" in sources:
        all_vacancies.extend(fetch_trudvsem(query, limit=pages * 50))

    if not all_vacancies:
        return pd.DataFrame()

    df = pd.DataFrame(all_vacancies)
    df["grade_normalized"] = df["experience"].apply(normalize_grade)
    return df


# --- CSS: шрифты, шапка, карточки ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f7f8fa; }

    /* Шапка */
    .hero-wrap {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        border-radius: 16px;
        padding: 48px 40px;
        margin-bottom: 32px;
        box-shadow: 0 10px 30px rgba(247, 151, 30, 0.3);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.25);
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 16px;
        text-transform: uppercase;
    }
    .hero-title {
        color: #ffffff;
        font-size: 2.6rem;
        font-weight: 700;
        margin: 0 0 12px 0;
        line-height: 1.15;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.92);
        font-size: 1.1rem;
        margin: 0;
        font-weight: 400;
    }

    /* Метрики */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e8eaed;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] { color: #6b7280; font-size: 0.85rem; }
    div[data-testid="stMetricValue"] { color: #111827; font-weight: 700; }

    /* Карточка вакансии */
    .vacancy-card {
        background: #ffffff;
        border: 1px solid #e8eaed;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .vacancy-card:hover {
        box-shadow: 0 6px 20px rgba(30, 60, 114, 0.12);
        transform: translateY(-2px);
    }
    .vacancy-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #111827;
        margin: 0 0 10px 0;
        line-height: 1.35;
    }
    .vacancy-meta {
        color: #4b5563;
        font-size: 0.9rem;
        margin: 6px 0;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        color: #ffffff;
        margin-right: 6px;
        letter-spacing: 0.2px;
        text-transform: uppercase;
    }
    .badge-habr { background-color: #4a90d9; }
    .badge-trud { background-color: #2e7d32; }
    .badge-junior { background-color: #16a34a; }
    .badge-middle { background-color: #ea580c; }
    .badge-senior { background-color: #be123c; }
    .badge-remote { background-color: #7c3aed; }
    .badge-exp { background-color: #6b7280; }
    .vacancy-skills {
        color: #6b7280;
        font-size: 0.85rem;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #f0f0f0;
    }
    .vacancy-link {
        display: inline-block;
        margin-top: 10px;
        color: #2a5298;
        font-weight: 600;
        text-decoration: none;
        font-size: 0.9rem;
    }
    .vacancy-link:hover { text-decoration: underline; }
    .footnote {
        color: #6b7280;
        font-size: 0.78rem;
        font-style: italic;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# --- Шапка сайта ---
st.markdown(
    '<div class="hero-wrap">'
    '<div class="hero-badge">Live Data</div>'
    '<div class="hero-title">Аналитика вакансий</div>'
    '<div class="hero-subtitle">Агрегатор данных с Habr Career и портала «Работа России»</div>'
    '</div>',
    unsafe_allow_html=True,
)


# --- Сайдбар: параметры поиска и фильтры ---
with st.sidebar:
    st.header("Параметры поиска")

    query = st.text_input("Ключевое слово", value="Python")
    sources = st.multiselect(
        "Источники",
        ["Habr Career", "Trudvsem"],
        default=["Habr Career", "Trudvsem"],
    )
    pages = st.slider("Страниц для парсинга", 1, 5, 2)

    st.divider()
    st.header("Фильтры")

    filter_city = st.text_input("Город", placeholder="Например: Москва")
    filter_grade = st.selectbox(
        "Уровень / Опыт",
        ["Все", "Junior", "Middle", "Senior", "1-3 года", "3-6 лет", "Более 6 лет", "Не указан"],
    )
    filter_remote = st.checkbox("Только удалённая работа")
    filter_min_salary = st.number_input("Мин. зарплата, ₽", min_value=0, value=0, step=10000)

    st.divider()
    sort_by = st.selectbox(
        "Сортировать",
        [
            "По дате (свежие)",
            "По зарплате (убывание)",
            "По зарплате (возрастание)",
            "По названию (А-Я)",
        ],
    )

    st.divider()
    search_button = st.button("Собрать вакансии", type="primary", use_container_width=True)


# --- Сбор данных с кэшированием ---
if search_button:
    with st.spinner("Собираем вакансии..."):
        df = fetch_all(query, tuple(sources), pages)

    if df.empty:
        st.warning("Ничего не найдено. Попробуйте другое ключевое слово или источники.")
        st.session_state.pop("df", None)
    else:
        st.session_state["df"] = df
        st.session_state["query"] = query
        st.session_state["page"] = 1


# --- Отображение результатов ---
if "df" in st.session_state:
    df = st.session_state["df"]
    filtered = df.copy()

    # Фильтры
    if filter_city:
        filtered = filtered[
            filtered["city"].str.contains(filter_city, case=False, na=False)
        ]
    if filter_grade != "Все":
        filtered = filtered[filtered["grade_normalized"] == filter_grade]
    if filter_remote and "remote" in filtered.columns:
        remote_series = filtered["remote"].fillna(False).apply(
            lambda x: bool(x) if not isinstance(x, str) else x.lower() in ("true", "1", "yes", "да")
        )
        filtered = filtered[remote_series]
    if filter_min_salary > 0:
        filtered["salary_max"] = filtered[["salary_from", "salary_to"]].max(axis=1)
        filtered = filtered[filtered["salary_max"] >= filter_min_salary]

    # Сортировка
    if sort_by == "По дате (свежие)":
        filtered = filtered.sort_values("published_at", ascending=False, na_position="last")
    elif sort_by == "По зарплате (убывание)":
        filtered["_sort_salary"] = filtered[["salary_from", "salary_to"]].max(axis=1)
        filtered = filtered.sort_values("_sort_salary", ascending=False, na_position="last")
    elif sort_by == "По зарплате (возрастание)":
        filtered["_sort_salary"] = filtered[["salary_from", "salary_to"]].max(axis=1)
        filtered = filtered.sort_values("_sort_salary", ascending=True, na_position="last")
    elif sort_by == "По названию (А-Я)":
        filtered = filtered.sort_values("name", ascending=True, na_position="last")

    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего вакансий", len(filtered))
    col2.metric("Компаний", filtered["company"].nunique())
    col3.metric("Городов", filtered["city"].nunique())

    salaries = filtered["salary_from"].dropna()
    salary_count = len(salaries)
    avg_salary = int(salaries.mean()) if not salaries.empty else 0
    col4.metric(
        "Средняя зарплата (от)",
        f"{avg_salary:,} ₽".replace(",", " "),
        help=f"Рассчитано по {salary_count} из {len(filtered)} вакансий, где указана зарплата",
    )
    st.markdown(
        f'<div class="footnote">* Средняя зарплата рассчитана только по {salary_count} '
        f'из {len(filtered)} вакансий, в которых указан уровень дохода.</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Вкладки
    tab1, tab2, tab3, tab4 = st.tabs(["Вакансии", "Навыки", "Города", "Зарплаты"])

    with tab1:
        st.subheader(f"Найдено {len(filtered)} вакансий")

        if filtered.empty:
            st.info("Нет вакансий, соответствующих фильтрам.")
        else:
            # Пагинация
            per_page = st.selectbox(
                "Вакансий на странице", [10, 20, 50], index=1, key="per_page"
            )
            total_pages = max(1, (len(filtered) + per_page - 1) // per_page)

            if "page" not in st.session_state:
                st.session_state["page"] = 1
            if st.session_state["page"] > total_pages:
                st.session_state["page"] = 1

            current_page = st.session_state["page"]
            start = (current_page - 1) * per_page
            end = start + per_page
            page_items = filtered.iloc[start:end]

            # Карточки вакансий
            for _, row in page_items.iterrows():
                st.markdown(build_vacancy_card(row), unsafe_allow_html=True)

            # Кнопки навигации
            st.write("")
            nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
            with nav_col1:
                if st.button("← Назад", disabled=(current_page <= 1), use_container_width=True):
                    st.session_state["page"] = current_page - 1
                    st.rerun()
            with nav_col2:
                st.markdown(
                    f'<div style="text-align:center; padding-top:8px; color:#6b7280;">'
                    f'Страница {current_page} из {total_pages}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with nav_col3:
                if st.button("Вперёд →", disabled=(current_page >= total_pages), use_container_width=True):
                    st.session_state["page"] = current_page + 1
                    st.rerun()

    with tab2:
        st.subheader("ТОП-15 навыков")
        skills_series = filtered["skills"].dropna().str.split(", ").explode()
        skills_series = skills_series[skills_series != ""]
        top_skills = skills_series.value_counts().head(15)

        if not top_skills.empty:
            fig = px.bar(
                x=top_skills.values,
                y=top_skills.index,
                orientation="h",
                labels={"x": "Количество", "y": "Навык"},
                color_discrete_sequence=["#2a5298"],
            )
            fig.update_layout(height=500, showlegend=False, font=dict(family="Inter"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных о навыках")

    with tab3:
        st.subheader("ТОП-15 городов")
        top_cities = filtered["city"].value_counts().head(15)
        if not top_cities.empty:
            fig = px.bar(
                x=top_cities.index,
                y=top_cities.values,
                labels={"x": "Город", "y": "Количество"},
                color_discrete_sequence=["#ea580c"],
            )
            fig.update_layout(height=500, font=dict(family="Inter"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Нет данных о городах")

    with tab4:
        st.subheader("Распределение зарплат")
        salary_data = filtered["salary_from"].dropna()
        if not salary_data.empty:
            fig = px.histogram(
                salary_data,
                nbins=20,
                labels={"value": "Зарплата, ₽", "count": "Количество"},
                color_discrete_sequence=["#16a34a"],
            )
            fig.update_layout(height=500, font=dict(family="Inter"))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(
                f'<div class="footnote">* Гистограмма построена по {len(salary_data)} вакансиям '
                f'с указанной зарплатой.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Нет данных о зарплатах")

else:
    st.info("Настройте параметры в сайдбаре и нажмите «Собрать вакансии»")