from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def is_supported_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def images_in_folder(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if is_supported_image(p))
