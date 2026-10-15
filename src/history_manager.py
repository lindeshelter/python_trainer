import json


def load_history():
    with open("../data/history.json", "r", encoding="utf-8") as file:
        return json.load(file)


def save_task(task):
    history = load_history()

    # проверяем, нет ли такой задачи
    for saved_task in history:
        if saved_task["title"] == task["title"]:
            return False

    history.append(task)

    with open("../data/history.json", "w", encoding="utf-8") as file:
        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=4
        )

    return True