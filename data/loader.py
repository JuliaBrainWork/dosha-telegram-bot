import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("questions.json")


def load_questions() -> list[dict[str, Any]]:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, list):
        raise ValueError("questions.json must contain a list")

    for item in raw:
        if item.get("mode") not in {"prakriti", "vikriti"}:
            raise ValueError(f"Invalid mode in question: {item.get('id')}")
    return raw


def questions_by_mode(mode: str) -> list[dict[str, Any]]:
    return [q for q in load_questions() if q["mode"] == mode]


def question_map() -> dict[str, dict[str, Any]]:
    return {q["id"]: q for q in load_questions()}
