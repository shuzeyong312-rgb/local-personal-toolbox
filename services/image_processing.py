from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

JPEG_QUALITY = 95
WEBP_QUALITY = 95
OUTPUT_FORMATS = {"png": ("PNG", ".png"), "jpg": ("JPEG", ".jpg"), "webp": ("WEBP", ".webp")}


@dataclass(frozen=True)
class WatermarkOptions:
    text: str
    font_size: int = 36
    opacity: int = 128
    color: str = "#ffffff"
    position: str = "右下"
    margin: int = 24
    tiled: bool = False
    angle: int = 30
    spacing: int = 80


def _font(size: int):
    for path in (
        Path("C:/Windows/Fonts/msyh.ttc"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ):
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _text_layer(text: str, font, color: str, opacity: int) -> Image.Image:
    box = font.getbbox(text)
    width, height = box[2] - box[0], box[3] - box[1]
    layer = Image.new("RGBA", (max(1, width + 8), max(1, height + 8)), (0, 0, 0, 0))
    rgb = ImageColor.getrgb(color)
    ImageDraw.Draw(layer).text((4 - box[0], 4 - box[1]), text, font=font, fill=(*rgb, opacity))
    return layer


def render_watermark(image: Image.Image, options: WatermarkOptions) -> Image.Image:
    base = image.convert("RGBA")
    if not options.text.strip():
        return base

    mark = _text_layer(options.text, _font(options.font_size), options.color, options.opacity)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    if options.tiled:
        mark = mark.rotate(options.angle, expand=True, resample=Image.Resampling.BICUBIC)
        step_x = max(1, mark.width + options.spacing)
        step_y = max(1, mark.height + options.spacing)
        for y in range(-mark.height, base.height + mark.height, step_y):
            for x in range(-mark.width, base.width + mark.width, step_x):
                overlay.alpha_composite(mark, (x, y))
    else:
        w, h = base.size
        mw, mh = mark.size
        positions = {
            "左上": (options.margin, options.margin),
            "右上": (w - mw - options.margin, options.margin),
            "左下": (options.margin, h - mh - options.margin),
            "右下": (w - mw - options.margin, h - mh - options.margin),
            "居中": ((w - mw) // 2, (h - mh) // 2),
        }
        x, y = positions.get(options.position, positions["右下"])
        overlay.alpha_composite(mark, (max(0, x), max(0, y)))
    return Image.alpha_composite(base, overlay)


def ensure_static(image: Image.Image) -> None:
    if getattr(image, "is_animated", False):
        raise ValueError("暂不支持动态图片水印。")


def output_path(
    source: Path, output_dir: Path, output_format: str = "original", order_prefix: str = ""
) -> Path:
    with Image.open(source) as image:
        ensure_static(image)
        actual_format = image.format
    if output_format == "original":
        suffix = source.suffix.lower()
        if actual_format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("不支持的图片格式")
        if suffix not in ({".jpg", ".jpeg"} if actual_format == "JPEG" else {f".{actual_format.lower()}"}):
            suffix = OUTPUT_FORMATS["jpg" if actual_format == "JPEG" else actual_format.lower()][1]
    else:
        try:
            _, suffix = OUTPUT_FORMATS[output_format]
        except KeyError as exc:
            raise ValueError("不支持的输出格式") from exc

    name = source.name
    while Path(name).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        name = Path(name).stem
    output_name = f"{order_prefix}_{name}" if order_prefix else name
    candidate = output_dir / f"{output_name}_水印版{suffix}"
    index = 2
    while candidate.exists():
        candidate = output_dir / f"{output_name}_水印版_{index}{suffix}"
        index += 1
    return candidate


def process_image(
    source: Path,
    destination: Path,
    options: WatermarkOptions,
    output_format: str = "original",
    quality: int = 95,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        ensure_static(original)
        original.load()
        size = original.size
        exif = original.info.get("exif")
        icc = original.info.get("icc_profile")
        result = render_watermark(original, options)
        selected_format = original.format if output_format == "original" else OUTPUT_FORMATS.get(output_format, (None,))[0]
        if selected_format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("不支持的输出格式")
        save_options = {}
        if exif:
            save_options["exif"] = exif
        if icc:
            save_options["icc_profile"] = icc
        if selected_format == "JPEG":
            background = Image.new("RGB", result.size, "white")
            background.paste(result, mask=result.getchannel("A"))
            result = background
            save_options.update(quality=quality, subsampling=0)
        elif selected_format == "WEBP":
            save_options.update(quality=quality, method=6)
        result.save(destination, format=selected_format, **save_options)
        if result.size != size:
            raise RuntimeError("输出图片尺寸发生变化")
