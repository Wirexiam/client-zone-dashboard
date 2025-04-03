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

# --- Анализ длительности перед переходом в Ч ---
st.markdown("## ⏱️ Длительность пребывания в зонах перед переходом в Ч")
min_days = st.slider("📉 Порог дней до перехода в Ч", min_value=0, max_value=180, value=10, step=1)
black_inns = df[df["next_zone"] == "Ч"]["ИНН"].unique()
durations = []
for inn in black_inns:
    group = df[df["ИНН"] == inn].sort_values("Дата_утверждения")
    for i in range(len(group) - 1):
        current = group.iloc[i]
        next_ = group.iloc[i + 1]
        if next_["Зона"] == "Ч":
            days = (next_["Дата_утверждения"] - current["Дата_утверждения"]).days
            if days >= min_days:
                durations.append({
                    "ИНН": inn,
                    "Зона перед Ч": current["Зона"],
                    "Дата входа": current["Дата_утверждения"],
                    "Дата в Ч": next_["Дата_утверждения"],
                    "Дней в зоне": days
                })
            break
duration_df = pd.DataFrame(durations)
if not duration_df.empty:
    fig_duration = px.box(
        duration_df,
        x="Зона перед Ч", y="Дней в зоне",
        points="all",
        title=f"⏱️ Время в зонах перед Чёрной (от {min_days} дней)",
        labels={"Зона перед Ч": "Зона", "Дней в зоне": "Дней до Ч"}
    )
    st.plotly_chart(fig_duration, use_container_width=True)

    stats = duration_df.groupby("Зона перед Ч")["Дней в зоне"].agg(["mean", "median", "count"]).round(1)
    st.markdown("### 📊 Статистика по зонам перед Ч")
    st.dataframe(stats)

    st.download_button(
        label="📥 Скачать длительности перед Ч",
        data=duration_df.to_csv(index=False).encode("utf-8"),
        file_name="durations_to_black.csv",
        mime="text/csv"
    )
else:
    st.warning("⚠️ Нет клиентов, удовлетворяющих выбранному порогу.")
