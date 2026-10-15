from __future__ import annotations

import contextlib
import io
import sys
from typing import Any


def run_code(code: str, input_data: str = "") -> str:
    """Запускает учебный код и возвращает stdout или понятное сообщение об ошибке.

    Это простой локальный запуск для учебного прототипа, а не безопасный sandbox.
    Не запускайте в нём неизвестный или недоверенный код.
    """
    output = io.StringIO()
    previous_stdin = sys.stdin

    try:
        sys.stdin = io.StringIO(input_data)
        with contextlib.redirect_stdout(output):
            exec(code, {"__name__": "__main__"})
        return output.getvalue()
    except Exception as error:
        return f"Ошибка: {type(error).__name__}: {error}"
    finally:
        sys.stdin = previous_stdin
