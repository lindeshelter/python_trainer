from __future__ import annotations

import streamlit as st

from ai_teacher2 import check_solution
from history_manager2 import load_history, save_task
from runner2 import run_code
from task2 import CURRENT_TASK


st.set_page_config(page_title="Python Trainer", page_icon="🐍")
st.title("🐍 Python Trainer")

current_task = CURRENT_TASK
st.header(current_task["title"])
st.caption(f"Тема: {current_task['topic']}")
st.write(current_task["description"])

code = st.text_area("Ваш код", height=250, placeholder="Например:\nlength = int(input())\n...")
input_data = st.text_area("Входные данные", placeholder="Каждое значение — на новой строке")

col1, col2, col3 = st.columns(3)
with col1:
    run_button = st.button("▶ Запустить", use_container_width=True)
with col2:
    check_button = st.button("🤖 Проверить", use_container_width=True)
with col3:
    save_button = st.button("⭐ Сохранить", use_container_width=True)

if run_button:
    if not code.strip():
        st.warning("Сначала введите код.")
    else:
        st.subheader("Результат запуска")
        st.code(run_code(code, input_data), language="text")

if check_button:
    if not code.strip():
        st.warning("Сначала введите код для проверки.")
    else:
        with st.spinner("Преподаватель проверяет решение..."):
            try:
                result = check_solution(current_task, code, input_data)
            except RuntimeError as error:
                st.error(str(error))
            else:
                st.markdown(result)

if save_button:
    try:
        saved = save_task(current_task)
    except (OSError, ValueError) as error:
        st.error(f"Не удалось сохранить задачу: {error}")
    else:
        if saved:
            st.success("Задача добавлена в повторение ⭐")
        else:
            st.warning("Эта задача уже сохранена")

st.sidebar.title("📚 Мои задачи")
history = load_history()
if history:
    titles = [task.get("title", "Без названия") for task in history]
    selected_title = st.sidebar.selectbox("Выберите задачу", titles)
    selected_task = next(
        task for task in history if task.get("title") == selected_title
    )
    st.sidebar.write(selected_task.get("description", ""))
else:
    st.sidebar.info("Сохранённых задач пока нет.")
