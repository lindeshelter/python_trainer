import io
import contextlib
import sys


def run_code(code, input_data):
    output = io.StringIO()

    try:
        sys.stdin = io.StringIO(input_data)

        with contextlib.redirect_stdout(output):
            exec(code)

        return output.getvalue()

    except Exception as error:
        return f"Ошибка: {error}"
