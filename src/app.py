import streamlit as st

from runner import run_code
from history_manager import load_history, save_task


st.title("🐍 Python Trainer")

current_task = {
    "title": "Площадь прямоугольника",
    "topic": "Ввод и вывод",
    "description": """
Напишите программу, которая получает длину
и ширину прямоугольника и выводит его площадь.
"""
}


st.header(current_task["title"])

st.write(
    current_task["description"]
)


code = st.text_area(
    "Ваш код",
    height=250
)

input_data = st.text_area(
    "Входные данные"
)



col1, col2, col3 = st.columns(3)


with col1:
    run_button = st.button("▶ Запустить")


with col2:
    check_button = st.button("🤖 Проверить")


with col3:
    save_button = st.button("⭐ Сохранить")


if run_button:

    result = run_code(
        code,
        input_data
    )

    st.subheader("Результат")

    st.code(result)


if check_button:

    st.info(
        "Здесь будет проверка преподавателем."
    )


if save_button:

    result = save_task(current_task)

    if result:
        st.success(
            "Задача добавлена в повторение ⭐"
        )
    else:
        st.warning(
            "Эта задача уже сохранена"
        )


st.sidebar.title("📚 Мои задачи")


history = load_history()

selected_task = None

if history:

    titles = [
        task["title"]
        for task in history
    ]

    selected_title = st.sidebar.selectbox(
        "📚 Мои задачи",
        titles
    )

    selected_task = next(
        task for task in history
        if task["title"] == selected_title
    )

