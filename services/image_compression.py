from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps


@dataclass(frozen=True)
class CompressionResult:
    source: Path
    destination: Path | None
    original_size: int
    compressed_size: int
    status: str


def compression_output_path(source: Path, output_dir: Path | None = None) -> Path:
    folder = output_dir or source.parent / "压缩结果"
    candidate = folder / source.name
    index = 1
    while candidate.exists() or candidate.resolve() == source.resolve():
        candidate = folder / f"{source.stem}_{index}{source.suffix.lower()}"
        index += 1
    return candidate


def compress_image(source: Path, destination: Path, quality: int = 80) -> CompressionResult:
    if not 1 <= quality <= 100:
        raise ValueError("图片质量必须在 1 到 100 之间")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        if getattr(original, "is_animated", False):
            raise ValueError("不支持动态图片")
        original.load()
        image_format = original.format
        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("不支持的图片格式")

        image = ImageOps.exif_transpose(original)
        save_options: dict[str, object] = {"optimize": True}
        if original.info.get("icc_profile"):
            save_options["icc_profile"] = original.info["icc_profile"]
        if image_format == "JPEG":
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            save_options.update(quality=quality)
        elif image_format == "PNG":
            save_options.update(compress_level=9)
        else:
            save_options.update(quality=quality, method=6)
        image.save(destination, format=image_format, **save_options)

    original_size = source.stat().st_size
    compressed_size = destination.stat().st_size
    if compressed_size >= original_size:
        destination.unlink()
        return CompressionResult(source, None, original_size, original_size, "无需压缩")
    return CompressionResult(source, destination, original_size, compressed_size, "压缩成功")
