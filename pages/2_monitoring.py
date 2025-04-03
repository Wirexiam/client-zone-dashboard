# 2_monitoring.py
import streamlit as st
import pandas as pd
import plotly.express as px

# Загрузка данных
st.set_page_config(page_title="Мониторинг зон", layout="wide")
st.title("📡 Мониторинг движения клиентов по зонам")

df = pd.read_csv("processed_transitions_dataset.csv", parse_dates=["Дата_утверждения", "next_date"])

# --- Блок 1. Длительность перед переходом в Ч ---
st.header("⏱️ Длительность пребывания перед переходом в Ч")

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
    fig = px.box(
        duration_df,
        x="Зона перед Ч", y="Дней в зоне",
        points="all",
        title=f"⏱️ Время в зонах перед Ч (>{min_days} дн)",
        labels={"Зона перед Ч": "Зона", "Дней в зоне": "Дней до Ч"}
    )
    st.plotly_chart(fig, use_container_width=True)

    stats = duration_df.groupby("Зона перед Ч")["Дней в зоне"].agg(["mean", "median", "count"]).round(1)
    st.markdown("### 📊 Статистика по зонам перед Ч")
    st.dataframe(stats)

    st.markdown("### 🔍 Примеры клиентов")
    st.dataframe(duration_df.sort_values("Дней в зоне", ascending=False))

    st.download_button(
        label="📅 Скачать длительности перед Ч",
        data=duration_df.to_csv(index=False).encode("utf-8"),
        file_name="durations_to_black.csv",
        mime="text/csv"
    )
else:
    st.warning("Нет данных по заданному порогу")

# --- Блок 2. Остановленные траектории ---
st.header("🛑 Остановленные траектории (не дошли до Ч)")

# Найдём тех, кто не дошёл до Ч
last_steps = df.sort_values("Дата_утверждения").groupby("ИНН").last().reset_index()
not_black = last_steps[last_steps["Зона"] != "Ч"]

if not not_black.empty:
    st.markdown("### 📍 Зоны, в которых остановились клиенты")
    zone_counts = not_black["Зона"].value_counts().reset_index()
    zone_counts.columns = ["Зона", "Кол-во"]
    fig2 = px.bar(zone_counts, x="Зона", y="Кол-во", title="🧭 Клиенты по последней зоне")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🔍 Примеры остановленных клиентов")
    st.dataframe(not_black[["ИНН", "Зона", "Дата_утверждения"]].sort_values("Дата_утверждения", ascending=False))
else:
    st.info("Все клиенты дошли до Ч. Остановленных нет.")
