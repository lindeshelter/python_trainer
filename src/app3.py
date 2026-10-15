from __future__ import annotations

import streamlit as st

from ai_teacher3 import ask_teacher, check_solution, generate_task
from history_manager2 import load_history, save_task
from runner2 import run_code
from task2 import CURRENT_TASK


st.set_page_config(page_title="Python Trainer", page_icon="🐍")
st.title("🐍 Python Trainer")

if "current_task" not in st.session_state:
    st.session_state.current_task = CURRENT_TASK
if "task_number" not in st.session_state:
    st.session_state.task_number = 1


def parse_generated_task(response: str, fallback_topic: str) -> dict[str, str]:
    """Преобразует ответ преподавателя в структуру задачи."""
    fields = {"title": "Новая задача", "topic": fallback_topic, "description": response.strip()}
    current_field = None
    description_lines: list[str] = []

    for raw_line in response.splitlines():
        line = raw_line.strip()
        lower_line = line.lower()
        if lower_line.startswith("название:"):
            fields["title"] = line.split(":", 1)[1].strip() or fields["title"]
            current_field = "title"
        elif lower_line.startswith("тема:"):
            fields["topic"] = line.split(":", 1)[1].strip() or fields["topic"]
            current_field = "topic"
        elif lower_line.startswith("условие:"):
            first_line = line.split(":", 1)[1].strip()
            if first_line:
                description_lines.append(first_line)
            current_field = "description"
        elif current_field == "description":
            description_lines.append(raw_line.rstrip())

    description = "\n".join(description_lines).strip()
    if description:
        fields["description"] = description
    return fields


current_task = st.session_state.current_task
st.header(current_task["title"])
st.caption(f"Тема: {current_task['topic']}")
st.write(current_task["description"])

next_task_col, question_col = st.columns(2)
with next_task_col:
    next_task_button = st.button("➡️ Следующая задача", use_container_width=True)
with question_col:
    ask_button = st.button("💬 Задать вопрос", use_container_width=True)

if next_task_button:
    with st.spinner("Преподаватель подбирает новую задачу..."):
        try:
            generated = generate_task(current_task["topic"], load_history())
            st.session_state.current_task = parse_generated_task(
                generated,
                current_task["topic"],
            )
            st.session_state.task_number += 1
            st.success("Новая задача готова.")
            st.rerun()
        except (RuntimeError, ValueError) as error:
            st.error(str(error))

question = st.text_area(
    "Ваш вопрос преподавателю",
    key="teacher_question",
    placeholder="Например: чем input() отличается от int(input())?",
)
if ask_button:
    if not question.strip():
        st.warning("Сначала введите вопрос.")
    else:
        with st.spinner("Преподаватель готовит ответ..."):
            try:
                answer = ask_teacher(question, current_task)
            except (RuntimeError, ValueError) as error:
                st.error(str(error))
            else:
                st.subheader("Ответ преподавателя")
                st.markdown(answer)

code = st.text_area(
    "Ваш код",
    height=250,
    key=f"code_{st.session_state.task_number}",
    placeholder="Например:\nlength = int(input())\n...",
)
input_data = st.text_area(
    "Входные данные",
    key=f"input_{st.session_state.task_number}",
    placeholder="Каждое значение — на новой строке",
)

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
