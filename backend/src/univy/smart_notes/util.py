from pathlib import Path

from univy.constants import OUTPUT_DIR


def read_json_content(file_name: str) -> str:
    with open(Path(OUTPUT_DIR) / file_name, "r") as file:
        return file.read()
