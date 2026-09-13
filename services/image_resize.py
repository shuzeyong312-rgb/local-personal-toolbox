from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageOps

MODES = {"fixed", "width", "height", "max"}
FIT_MODES = {"contain", "cover", "stretch"}


@dataclass(frozen=True)
class ResizeOptions:
    mode: str = "fixed"
    width: int | None = 800
    height: int | None = 800
    fit_mode: str = "contain"
    prevent_upscale: bool = True
    background_color: str = "#ffffff"

    def __post_init__(self) -> None:
        if self.mode not in MODES or self.fit_mode not in FIT_MODES:
            raise ValueError("不支持的尺寸调整方式")
        required = ("width", "height") if self.mode in {"fixed", "max"} else (self.mode,)
        for name in required:
            value = getattr(self, name)
            if value is None or not 1 <= value <= 20000:
                raise ValueError("尺寸必须在 1 到 20000 px 之间")
        try:
            ImageColor.getrgb(self.background_color)
        except ValueError as exc:
            raise ValueError("背景颜色无效") from exc


def calculate_output_size(source_size: tuple[int, int], options: ResizeOptions) -> tuple[int, int]:
    source_width, source_height = source_size
    if source_width <= 0 or source_height <= 0:
        raise ValueError("原图尺寸无效")
    if options.mode == "fixed":
        return options.width, options.height  # type: ignore[return-value]
    if options.mode == "width":
        scale = options.width / source_width  # type: ignore[operator]
    elif options.mode == "height":
        scale = options.height / source_height  # type: ignore[operator]
    else:
        scale = min(options.width / source_width, options.height / source_height)  # type: ignore[operator]
    if options.prevent_upscale:
        scale = min(scale, 1)
    return max(1, round(source_width * scale)), max(1, round(source_height * scale))


def resize_image(image: Image.Image, options: ResizeOptions) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if options.mode != "fixed":
        return image.resize(calculate_output_size(image.size, options), Image.Resampling.LANCZOS)

    target = (options.width, options.height)
    if options.fit_mode == "stretch":
        return image.resize(target, Image.Resampling.LANCZOS)
    scale = (min if options.fit_mode == "contain" else max)(target[0] / image.width, target[1] / image.height)
    if options.prevent_upscale:
        scale = min(scale, 1)
    scaled = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
    if options.fit_mode == "cover":
        left = max(0, (scaled.width - target[0]) // 2)
        top = max(0, (scaled.height - target[1]) // 2)
        cropped = scaled.crop((left, top, min(scaled.width, left + target[0]), min(scaled.height, top + target[1])))
        if cropped.size == target:
            return cropped
        scaled = cropped
    mode = "RGBA" if image.mode in {"RGBA", "LA"} else "RGB"
    background = Image.new(mode, target, ImageColor.getrgb(options.background_color) + ((255,) if mode == "RGBA" else ()))
    background.paste(scaled, ((target[0] - scaled.width) // 2, (target[1] - scaled.height) // 2), scaled if scaled.mode in {"RGBA", "LA"} else None)
    return background


def resize_output_path(source: Path, output_dir: Path) -> Path:
    candidate = output_dir / f"{source.stem}_resized{source.suffix.lower()}"
    index = 2
    while candidate.exists() or candidate.resolve() == source.resolve():
        candidate = output_dir / f"{source.stem}_resized_{index}{source.suffix.lower()}"
        index += 1
    return candidate


def process_resize(source: Path, destination: Path, options: ResizeOptions) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        if getattr(original, "is_animated", False):
            raise ValueError("不支持动态图片")
        original.load()
        image_format = original.format
        if image_format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("不支持的图片格式")
        result = resize_image(original, options)
        save_options = {}
        exif = original.getexif()
        for tag in (256, 257, 274):
            if tag in exif:
                del exif[tag]
        if exif:
            save_options["exif"] = exif.tobytes()
        if original.info.get("icc_profile"):
            save_options["icc_profile"] = original.info["icc_profile"]
        if image_format == "JPEG":
            if result.mode != "RGB":
                flattened = Image.new("RGB", result.size, options.background_color)
                flattened.paste(result, mask=result.getchannel("A") if "A" in result.getbands() else None)
                result = flattened
            save_options.update(quality=95, subsampling=0)
        elif image_format == "WEBP":
            save_options.update(quality=95, method=6)
        result.save(destination, format=image_format, **save_options)
