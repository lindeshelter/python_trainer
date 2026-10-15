from __future__ import annotations

import streamlit as st

from ai_teacher6 import STUDY_PLAN, ask_teacher, check_solution, generate_task
from history_manager2 import load_history, save_task
from runner2 import run_code
from task2 import CURRENT_TASK


st.set_page_config(page_title="Python Trainer", page_icon="🐍")
st.title("🐍 Python Trainer")


if "topic_index" not in st.session_state:
    st.session_state.topic_index = 0
if "current_task" not in st.session_state:
    st.session_state.current_task = {
        **CURRENT_TASK,
        "topic": STUDY_PLAN[st.session_state.topic_index],
    }
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
        lower_line = line.casefold()

        if lower_line.startswith("название:"):
            value = line.split(":", 1)[1].strip()
            if value:
                task["title"] = value
            in_description = False
        elif lower_line.startswith("тема:"):
            # Тема берётся из навигации, чтобы AI не смог случайно переключить раздел.
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
    """Очищает данные, относящиеся к предыдущей задаче."""
    for key in (
        "solution_code",
        "input_data",
        "teacher_question",
        "teacher_answer",
        "check_result",
        "run_result",
    ):
        st.session_state.pop(key, None)


def task_is_same(first: dict[str, str], second: dict[str, str]) -> bool:
    """Проверяет, не вернул ли провайдер ту же задачу."""
    return (
        first.get("title", "").strip().casefold()
        == second.get("title", "").strip().casefold()
        and first.get("description", "").strip().casefold()
        == second.get("description", "").strip().casefold()
    )


def get_new_task(topic: str, old_task: dict[str, str]) -> dict[str, str]:
    """Генерирует новую задачу строго в выбранной теме."""
    response = generate_task(
        topic,
        load_history(),
        current_task=old_task,
    )
    new_task = parse_generated_task(response, topic)
    new_task["topic"] = topic
    if task_is_same(old_task, new_task):
        raise RuntimeError(
            "Провайдер вернул ту же задачу. Нажмите кнопку перехода ещё раз."
        )
    return new_task


def change_topic(new_index: int) -> None:
    """Переключает тему и очищает состояние старой задачи."""
    st.session_state.topic_index = new_index
    reset_task_state()
    st.session_state.current_task = {
        "title": "Новая задача",
        "topic": STUDY_PLAN[new_index],
        "description": "Нажмите «Следующая задача», чтобы получить задачу по этой теме.",
    }
    st.session_state.notice = f"Выбрана тема {new_index + 1}: {STUDY_PLAN[new_index]}"


# Навигация меняет только индекс темы. Генерация задачи запускается отдельной кнопкой.
previous_col, next_col = st.columns(2)
with previous_col:
    previous_disabled = st.session_state.topic_index == 0
    if st.button(
        "⬅️ Предыдущая тема",
        disabled=previous_disabled,
        use_container_width=True,
    ):
        change_topic(st.session_state.topic_index - 1)
        st.rerun()
with next_col:
    next_disabled = st.session_state.topic_index == len(STUDY_PLAN) - 1
    if st.button(
        "Следующая тема ➡️",
        disabled=next_disabled,
        use_container_width=True,
    ):
        change_topic(st.session_state.topic_index + 1)
        st.rerun()


current_topic = STUDY_PLAN[st.session_state.topic_index]
current_task = st.session_state.current_task

st.progress(
    (st.session_state.topic_index + 1) / len(STUDY_PLAN),
    text=f"Тема {st.session_state.topic_index + 1} из {len(STUDY_PLAN)}",
)
st.subheader(current_topic)
st.caption(f"Текущая задача: {current_task['title']}")
st.write(current_task["description"])

if st.session_state.notice:
    st.success(st.session_state.notice)
    st.session_state.notice = ""

if st.button("➡️ Следующая задача", use_container_width=True):
    with st.spinner("Преподаватель подбирает задачу..."):
        try:
            new_task = get_new_task(current_topic, current_task)
        except (RuntimeError, ValueError) as error:
            st.error(str(error))
        else:
            st.session_state.current_task = new_task
            reset_task_state()
            st.session_state.notice = "Новая задача загружена."
            st.rerun()

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
    placeholder="Введите решение задачи",
)
input_data = st.text_area(
    "Входные данные",
    key="input_data",
    placeholder="Каждое значение — на новой строке",
)

run_col, check_col, save_col = st.columns(3)
with run_col:
    run_button = st.button("▶ Запустить", use_container_width=True)
with check_col:
    check_button = st.button("🤖 Проверить", use_container_width=True)
with save_col:
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

st.sidebar.title("📚 Учебный план")
selected_topic = st.sidebar.selectbox(
    "Перейти к теме",
    STUDY_PLAN,
    index=st.session_state.topic_index,
)
selected_index = STUDY_PLAN.index(selected_topic)
if selected_index != st.session_state.topic_index:
    change_topic(selected_index)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("📚 Мои задачи")
history = load_history()
if history:
    titles = [task.get("title", "Без названия") for task in history]
    selected_title = st.sidebar.selectbox("Выберите сохранённую задачу", titles)
    selected_task = next(
        task for task in history if task.get("title") == selected_title
    )
    st.sidebar.write(selected_task.get("description", ""))
else:
    st.sidebar.info("Сохранённых задач пока нет.")
