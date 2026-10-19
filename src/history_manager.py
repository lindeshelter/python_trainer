from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HISTORY_FILE = DATA_DIR / "progress.json"


def _ensure_history_file() -> None:
    """Создаёт папку и пустую историю при первом запуске."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


def load_history() -> list[dict[str, Any]]:
    """Загружает историю задач и восстанавливает пустую историю при ошибке JSON."""
    _ensure_history_file()
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def save_task(task: dict[str, Any]) -> bool:
    """Сохраняет задачу, если задача с таким названием ещё не сохранена."""
    title = task.get("title")
    if not title:
        raise ValueError("У задачи должно быть непустое поле title.")

    history = load_history()
    if any(saved_task.get("title") == title for saved_task in history):
        return False

    history.append(task)
    _ensure_history_file()
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True
