import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_json(relative_path: str):
    path = ROOT / relative_path

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_policies():
    return load_json("corpus/policies.json")


def load_recordings():
    return load_json("recordings/observations.json")


def load_expected_results():
    return load_json("expected/expected_results.json")