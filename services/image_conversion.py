from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor

FORMATS = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP", "bmp": "BMP"}
INPUT_FORMATS = set(FORMATS.values())
COLLISION_MODES = {"rename", "overwrite", "skip"}


@dataclass(frozen=True)
class ConversionOptions:
    target_format: str = "png"
    jpg_quality: int = 90
    webp_quality: int = 90
    webp_lossless: bool = False
    background_color: str = "#ffffff"
    prefix: str = ""
    suffix: str = ""
    collision: str = "rename"

    def __post_init__(self) -> None:
        if self.target_format not in FORMATS:
            raise ValueError("不支持的目标格式")
        if not 1 <= self.jpg_quality <= 100 or not 1 <= self.webp_quality <= 100:
            raise ValueError("图片质量必须在 1 到 100 之间")
        if self.collision not in COLLISION_MODES:
            raise ValueError("不支持的同名文件处理方式")
        if any(char in self.prefix + self.suffix for char in '<>:"/\\|?*'):
            raise ValueError("文件名前后缀不能包含路径或非法字符")
        try:
            ImageColor.getrgb(self.background_color)
        except ValueError as exc:
            raise ValueError("透明区域背景颜色无效") from exc


def output_path(source: Path, output_dir: Path, options: ConversionOptions) -> Path | None:
    candidate = output_dir / f"{options.prefix}{source.stem}{options.suffix}.{options.target_format}"
    if not candidate.exists() and candidate.resolve() != source.resolve():
        return candidate
    if options.collision == "skip":
        return None
    if options.collision == "overwrite" and candidate.resolve() != source.resolve():
        return candidate
    index = 1
    while candidate.exists() or candidate.resolve() == source.resolve():
        candidate = output_dir / f"{options.prefix}{source.stem}{options.suffix}_{index}.{options.target_format}"
        index += 1
    return candidate


def _flatten_alpha(image: Image.Image, color: str) -> Image.Image:
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, ImageColor.getrgb(color) + (255,))
    return Image.alpha_composite(background, rgba).convert("RGB")


def convert_image(source: Path, destination: Path, options: ConversionOptions) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        if getattr(original, "is_animated", False):
            raise ValueError("不支持动态图片")
        original.load()
        if original.format not in INPUT_FORMATS:
            raise ValueError("不支持的图片格式")
        source_size = original.size
        image = original.copy()
        save_options: dict[str, object] = {}
        if options.target_format == "jpg":
            image = _flatten_alpha(image, options.background_color) if image.mode in {"RGBA", "LA"} or "transparency" in image.info else image.convert("RGB")
            save_options.update(quality=options.jpg_quality, subsampling=0)
        elif options.target_format == "webp":
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            save_options.update(lossless=options.webp_lossless, quality=options.webp_quality, method=6)
        elif options.target_format == "png":
            if image.mode == "CMYK":
                image = image.convert("RGB")
        elif image.mode not in {"RGB", "RGBA", "L", "P"}:
            image = image.convert("RGB")
        image.save(destination, format=FORMATS[options.target_format], **save_options)
    try:
        with Image.open(destination) as result:
            result.load()
            if result.size != source_size or result.format != FORMATS[options.target_format]:
                raise RuntimeError("输出文件验证失败")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
