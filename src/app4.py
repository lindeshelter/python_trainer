from __future__ import annotations

import streamlit as st

from ai_teacher3 import ask_teacher, check_solution, generate_task
from history_manager2 import load_history, save_task
from runner2 import run_code
from task2 import CURRENT_TASK


st.set_page_config(page_title="Python Trainer", page_icon="🐍")
st.title("🐍 Python Trainer")


if "current_task" not in st.session_state:
    st.session_state.current_task = dict(CURRENT_TASK)
if "teacher_answer" not in st.session_state:
    st.session_state.teacher_answer = ""
if "check_result" not in st.session_state:
    st.session_state.check_result = ""
if "run_result" not in st.session_state:
    st.session_state.run_result = ""
if "notice" not in st.session_state:
    st.session_state.notice = ""


def parse_generated_task(response: str, fallback_topic: str) -> dict[str, str]:
    """Преобразует структурированный ответ преподавателя в задачу."""
    task = {
        "title": "Новая задача",
        "topic": fallback_topic,
        "description": response.strip(),
    }
    description_lines: list[str] = []
    in_description = False

    for raw_line in response.splitlines():
        line = raw_line.strip()
        lower_line = line.lower()

        if lower_line.startswith("название:"):
            value = line.split(":", 1)[1].strip()
            if value:
                task["title"] = value
            in_description = False
        elif lower_line.startswith("тема:"):
            value = line.split(":", 1)[1].strip()
            if value:
                task["topic"] = value
            in_description = False
        elif lower_line.startswith("условие:"):
            value = line.split(":", 1)[1].strip()
            if value:
                description_lines.append(value)
            in_description = True
        elif in_description:
            description_lines.append(raw_line.rstrip())

    description = "\n".join(description_lines).strip()
    if description:
        task["description"] = description
    return task


def reset_task_state() -> None:
    """Удаляет результаты и ввод, относящиеся к предыдущей задаче."""
    for key in (
        "solution_code",
        "input_data",
        "teacher_question",
        "teacher_answer",
        "check_result",
        "run_result",
    ):
        st.session_state.pop(key, None)


# Эта кнопка обрабатывается до создания полей кода. После успешной генерации
# выполняется новый запуск приложения уже с новой задачей.
if st.button("➡️ Следующая задача", use_container_width=True):
    old_task = st.session_state.current_task
    with st.spinner("Преподаватель подбирает новую задачу..."):
        try:
            generated = generate_task(old_task["topic"], load_history())
            new_task = parse_generated_task(generated, old_task["topic"])
        except (RuntimeError, ValueError) as error:
            st.error(str(error))
        else:
            st.session_state.current_task = new_task
            reset_task_state()
            st.session_state.notice = "Новая задача загружена."
            st.rerun()


current_task = st.session_state.current_task
st.header(current_task["title"])
st.caption(f"Тема: {current_task['topic']}")
st.write(current_task["description"])

if st.session_state.notice:
    st.success(st.session_state.notice)
    st.session_state.notice = ""

st.subheader("Вопрос преподавателю")
question = st.text_area(
    "Ваш вопрос",
    key="teacher_question",
    placeholder="Например: чем input() отличается от int(input())?",
)
if st.button("💬 Задать вопрос", use_container_width=True):
    if not question.strip():
        st.warning("Сначала введите вопрос.")
    else:
        with st.spinner("Преподаватель готовит ответ..."):
            try:
                st.session_state.teacher_answer = ask_teacher(question, current_task)
            except (RuntimeError, ValueError) as error:
                st.error(str(error))
            else:
                st.rerun()

if st.session_state.teacher_answer:
    st.subheader("Ответ преподавателя")
    st.markdown(st.session_state.teacher_answer)

st.subheader("Решение задачи")
code = st.text_area(
    "Ваш код",
    height=250,
    key="solution_code",
    placeholder="Например:\nlength = int(input())\n...",
)
input_data = st.text_area(
    "Входные данные",
    key="input_data",
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
        st.session_state.run_result = run_code(code, input_data)
        st.session_state.check_result = ""

if st.session_state.run_result:
    st.subheader("Результат запуска")
    st.code(st.session_state.run_result, language="text")

if check_button:
    if not code.strip():
        st.warning("Сначала введите код для проверки.")
    else:
        with st.spinner("Преподаватель проверяет решение..."):
            try:
                # Берём задачу непосредственно из session_state, чтобы проверка
                # всегда относилась к задаче, которая сейчас показана.
                st.session_state.check_result = check_solution(
                    st.session_state.current_task,
                    code,
                    input_data,
                )
            except RuntimeError as error:
                st.error(str(error))
            else:
                st.session_state.run_result = ""

if st.session_state.check_result:
    st.subheader("Проверка решения")
    st.markdown(st.session_state.check_result)

if save_button:
    try:
        saved = save_task(st.session_state.current_task)
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
