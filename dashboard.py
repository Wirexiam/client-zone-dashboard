# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from itertools import product

# Загрузка данных
df = pd.read_csv("processed_transitions_dataset.csv", parse_dates=["Дата_утверждения", "next_date"])

st.set_page_config(page_title="Анализ переходов зон", layout="wide")
st.title("📊 Аналитика переходов между зонами клиентов")

# --- Сайдбар фильтры ---
st.sidebar.header("🔍 Фильтры")
zones = df["Зона"].unique().tolist()
selected_zones = st.sidebar.multiselect("Текущая зона", zones, default=zones)

start_date = df["Дата_утверждения"].min().date()
end_date = df["Дата_утверждения"].max().date()
date_range = st.sidebar.date_input("Диапазон дат утверждения", [start_date, end_date])

# --- Генерация сценариев ---
scenarios = set()
for a, b in product(zones, repeat=2):
    if a != b:
        scenarios.add((a, b))
for a, b, c in product(zones, repeat=3):
    if len(set([a, b, c])) == 3:
        scenarios.add((a, b, c))

scenario_strings = sorted([' → '.join(s) for s in scenarios])
scenario_options = ["— Отобразить все —"] + scenario_strings
selected_scenario = st.sidebar.selectbox("🎯 Выбрать сценарий перехода (по зонам)", scenario_options)

# Определяем, включён ли фильтр по сценарию
apply_scenario = selected_scenario != "— Отобразить все —"
selected_steps = selected_scenario.split(" → ") if apply_scenario else []

# --- Фильтрация по дате и зонам ---
filtered_df = df[
    (df["Зона"].isin(selected_zones)) &
    (df["Дата_утверждения"] >= pd.to_datetime(date_range[0])) &
    (df["Дата_утверждения"] <= pd.to_datetime(date_range[1]))
]

# --- Поиск ИНН по сценарию ---
if apply_scenario:
    matching_inns = []
    for inn, group in df.groupby("ИНН"):
        path = group.sort_values("Дата_утверждения")["Зона"].tolist()
        for i in range(len(path) - len(selected_steps) + 1):
            if path[i:i + len(selected_steps)] == selected_steps:
                matching_inns.append(inn)
                break
    scenario_df = df[df["ИНН"].isin(matching_inns)]
else:
    scenario_df = filtered_df.copy()

# --- KPI ---
col1, col2, col3 = st.columns(3)
col1.metric("👤 Уникальных клиентов", scenario_df["ИНН"].nunique())
col2.metric("🔁 Всего переходов", len(scenario_df))
col3.metric("📅 Период", f"{date_range[0]} — {date_range[1]}")

st.markdown("---")

# --- График: Частота переходов ---
transition_counts = (
    scenario_df
    .groupby(["Зона", "next_zone"])
    .size()
    .reset_index(name="Количество")
)
fig1 = px.sunburst(
    transition_counts,
    path=["Зона", "next_zone"],
    values="Количество",
    title="🔄 Частота переходов из зоны в зону"
)
st.plotly_chart(fig1, use_container_width=True)

# --- График: Динамика --- обновлён для всех шагов сценария
graph_df = scenario_df.copy()

# Если сценарий выбран — работаем по шагам
if apply_scenario:
    steps_for_graph = selected_steps
else:
    steps_for_graph = zones  # Все зоны, если выбран "Отобразить все"

# Собираем график по выбранным шагам
parts = []
for step in steps_for_graph:
    from_part = graph_df[graph_df["Зона"] == step][["Дата_утверждения"]].copy()
    from_part["zone"] = step
    from_part["date"] = from_part["Дата_утверждения"]

    to_part = graph_df[graph_df["next_zone"] == step][["next_date"]].copy()
    to_part["zone"] = step
    to_part["date"] = to_part["next_date"]

    parts.append(pd.concat([from_part[["zone", "date"]], to_part[["zone", "date"]]]))

if parts:
    df_combined = pd.concat(parts)
    df_combined["month"] = df_combined["date"].dt.to_period("M").astype(str)

    monthly_trend = df_combined.groupby(["month", "zone"]).size().reset_index(name="Количество")

    title = f"📈 Динамика переходов по сценариям ({selected_scenario})" if apply_scenario else "📈 Общая динамика переходов по зонам"
    fig2 = px.line(
        monthly_trend,
        x="month", y="Количество", color="zone",
        markers=True,
        title=title
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("⚠️ Нет данных для построения графика.")

# --- Таблица примеров ---
scenario_label = selected_scenario
selected_steps = selected_scenario.split(" → ")

st.markdown(f"### 🔎 Примеры клиентов со сценарием {scenario_label}")

show_only_transitions = st.sidebar.checkbox("🔎 Показать только строки переходов (без истории)", value=False)

if apply_scenario:
    # Шаг 1. Найдём ИНН, у которых есть последовательность всех шагов
    matching_inns = []
    for inn, group in df.groupby("ИНН"):
        path = group.sort_values("Дата_утверждения")["Зона"].tolist()
        for i in range(len(path) - len(selected_steps) + 1):
            if path[i:i + len(selected_steps)] == selected_steps:
                matching_inns.append(inn)
                break
    example_df = filtered_df[filtered_df["ИНН"].isin(matching_inns)]

    if show_only_transitions:
        filters = []
        for i in range(len(selected_steps) - 1):
            a = selected_steps[i]
            b = selected_steps[i + 1]
            pair_filter = (example_df["Зона"] == a) & (example_df["next_zone"] == b)
            filters.append(pair_filter)
        final_filter = filters[0]
        for f in filters[1:]:
            final_filter |= f
        example_df = example_df[final_filter]

else:
    example_df = filtered_df.copy()  # Показать всё

st.dataframe(
    example_df[["ИНН", "Зона", "Дата_утверждения", "next_zone", "next_date"]]
    .sort_values(by=["ИНН", "Дата_утверждения"])
    .reset_index(drop=True)
)

# --- Загрузка CSV ---
st.download_button(
    label="📥 Скачать данные по сценарию",
    data=scenario_df.to_csv(index=False).encode("utf-8"),
    file_name="scenario_filtered_data.csv",
    mime="text/csv"
)
