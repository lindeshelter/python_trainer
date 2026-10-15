from __future__ import annotations

import os
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_DIR / ".env"


def _load_env_file() -> None:
    """Загружает простые KEY=VALUE-настройки из .env без перезаписи окружения."""
    if not ENV_FILE.is_file():
        return

    try:
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", maxsplit=1)
        name = name.strip()
        value = value.strip()
        if not name:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(name, value)


def _get_setting(*names: str) -> str | None:
    """Возвращает первое непустое значение из перечисленных переменных."""
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


STUDY_PLAN = (
    "Python — ввод и вывод, работа с файлами",
    "Типы данных",
    "Операторы в Python",
    "Условные конструкции и циклы: if, while, for",
    "Функции",
    "Область видимости и пространства имён",
    "Классы",
    "Класс Object и его методы",
    "Импортирование объектов и работа с модулями",
    "Генераторы коллекций",
    "Менеджер контекста: with / as",
)


TEACHER_PROMPT = """
Ты — опытный преподаватель и наставник по Python, специализирующийся на обучении начинающих.

Твоя цель — помогать ученику понимать синтаксис, логику Python и самостоятельно решать задачи.
Давай только одну задачу или одну рекомендацию за раз. Не показывай готовое решение заранее.
Если решение неверное, сначала укажи место ошибки и объясни причину простыми словами.
Полное решение показывай только по прямой просьбе или когда без него невозможно объяснить ошибку.
Не критикуй ученика и не навязывай единственный стиль, если есть несколько правильных решений.

ПЛАН ИЗУЧЕНИЯ ОСНОВ PYTHON

Обучай ученика последовательно, не перескакивая через темы:

1. Python — ввод и вывод, работа с файлами
2. Типы данных
3. Операторы в Python
4. Условные конструкции и циклы: if, while, for
5. Функции
6. Область видимости и пространства имён
7. Классы
8. Класс Object и его методы
9. Импортирование объектов и работа с модулями
10. Генераторы коллекций
11. Менеджер контекста: with / as

Для каждой темы подготовь в среднем 5–6 практических задач.
Задачи внутри темы должны идти от простых к более сложным и постепенно закреплять
материал предыдущих задач.

Правила прохождения учебного плана:
- сначала определи текущую тему по истории задач и уровню ученика;
- не переходи к следующей теме после одной успешной задачи;
- ориентируйся примерно на 5–6 задач по текущей теме;
- переходи дальше только после уверенного освоения текущей темы;
- если ученик часто ошибается, предложи дополнительную задачу по этой же теме;
- иногда используй задачи на повторение ранее изученных тем;
- новая задача должна соответствовать текущей теме и уровню ученика;
- не включай сложные темы раньше времени без необходимости;
- каждая задача должна проверять конкретный навык, а не сразу весь Python.

При генерации задачи указывай только одну тему и не смешивай много новых концепций.
При проверке решения учитывай не только правильность результата, но и то,
какие темы из учебного плана ученик уже изучает.
"""


def _request_ai(prompt: str) -> str:
    """Отправляет запрос провайдеру с OpenAI-совместимым API."""
    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError(
            "Библиотека openai не установлена. Установите зависимости из requirements.txt."
        ) from error

    _load_env_file()
    api_key = _get_setting("AI_API_KEY", "API_KEY", "OPENAI_API_KEY")
    model = _get_setting("AI_MODEL", "API_MODEL", "MODEL", "OPENAI_MODEL")
    base_url = _get_setting("AI_BASE_URL", "API_URL", "OPENAI_BASE_URL")

    if not api_key:
        raise RuntimeError(
            "Не задан ключ AI_API_KEY. Укажите ключ выбранного AI-провайдера "
            "в .env или в переменных окружения."
        )

    if not model:
        raise RuntimeError(
            "Не задана модель. Укажите AI_MODEL в .env или в переменных окружения."
        )

    client_options: dict[str, str] = {"api_key": api_key}
    if base_url:
        client_options["base_url"] = base_url

    client = OpenAI(**client_options)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as error:
        raise RuntimeError(f"Не удалось получить ответ AI-провайдера: {error}") from error

    try:
        text = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise RuntimeError("AI-провайдер вернул ответ в неожиданном формате.") from error

    if not text:
        raise RuntimeError("AI-провайдер вернул пустой ответ.")

    return text.strip()


def generate_task(
    topic: str,
    history: Any = None,
    current_task: Any = None,
) -> str:
    """Генерирует задачу и просит не повторять текущую."""
    history_text = ""
    if history:
        history_text = f"""
История предыдущих задач ученика:
{history}
"""

    current_task_text = current_task or "Текущая задача отсутствует."
    prompt = f"""
{TEACHER_PROMPT}

Текущая тема должна быть одной из тем учебного плана:
{chr(10).join(f"- {item}" for item in STUDY_PLAN)}

Текущая выбранная тема:
{topic}

ТЕКУЩАЯ ЗАДАЧА, КОТОРУЮ НЕЛЬЗЯ ПОВТОРЯТЬ:
{current_task_text}

{history_text}

Сгенерируй одну новую небольшую практическую задачу.
Она должна отличаться от текущей задачи по условию и названию.
Не копируй текущую задачу и не возвращай её перефразированный вариант.
Верни результат строго в формате:

Название: ...
Тема: ...
Условие: ...

Условие должно быть понятным начинающему программисту.
"""

    return _request_ai(prompt)


def check_solution(task: Any, code: str, input_data: str = "") -> str:
    """Проверяет код ученика относительно условия задачи."""
    prompt = f"""
{TEACHER_PROMPT}

Проверь решение ученика относительно условия задачи.

УСЛОВИЕ ЗАДАЧИ:
{task}

КОД УЧЕНИКА:
```python
{code}
```

ВХОДНЫЕ ДАННЫЕ:
{input_data or "(не указаны)"}

Проанализируй соответствие условию, синтаксис, логику, типы данных и результат.
Не переписывай программу целиком без необходимости.
Верни ответ в формате:

### 1. Соответствие условию
### 2. Разбор решения
### 3. Найденные ошибки
### 4. Что сделано правильно
### 5. Рекомендации
### 6. Итог

В разделе «Итог» используй один вариант:
✅ задача решена полностью
🟡 задача почти решена, требуется исправить несколько моментов
❌ задача пока не решена
"""

    return _request_ai(prompt)


def ask_teacher(question: str, task: Any = None) -> str:
    """Отвечает на вопрос ученика с учётом текущей задачи."""
    if not question.strip():
        raise ValueError("Введите вопрос преподавателю.")

    task_context = task if task else "Текущая задача не выбрана."
    prompt = f"""
{TEACHER_PROMPT}

Ученик задаёт вопрос по обучению Python.

ТЕКУЩАЯ ЗАДАЧА:
{task_context}

ВОПРОС УЧЕНИКА:
{question}

Ответь понятно и кратко, как начинающему программисту.
Не показывай полное решение текущей задачи, если ученик прямо его не просит.
Если вопрос не связан с Python или обучением, вежливо верни разговор к теме.
"""

    return _request_ai(prompt)
