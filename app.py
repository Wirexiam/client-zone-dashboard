# app.py

import streamlit as st
import time
from data_preparation import prepare_dataset

st.set_page_config(page_title="Импорт данных", layout="wide")
st.title("📥 Загрузка и обработка Excel-файла")

# --- Redirect-флаг в сессии
if "redirect" not in st.session_state:
    st.session_state["redirect"] = False

# --- Если redirect активен — уходим в Dashboard
if st.session_state["redirect"]:
    st.session_state["redirect"] = False
    st.switch_page("pages/1_dashboard.py")

# --- Загрузка файла
uploaded_file = st.file_uploader("Выберите Excel-файл (.xlsx)", type=["xlsx"])

if uploaded_file:
    with st.spinner("⏳ Обработка файла..."):
        df_result = prepare_dataset(uploaded_file)
        st.success("✅ Данные успешно обработаны!")

        st.dataframe(df_result.head(10))

        st.download_button(
            label="📥 Скачать CSV",
            data=df_result.to_csv(index=False).encode("utf-8"),
            file_name="processed_transitions_dataset.csv",
            mime="text/csv"
        )

        # ⚡ Пауза 3 секунды перед переходом
        time.sleep(3)
        st.session_state["redirect"] = True
        st.experimental_rerun()
