import os
from pathlib import Path


def open_folder(path: Path) -> None:
    os.startfile(path)  # type: ignore[attr-defined]
