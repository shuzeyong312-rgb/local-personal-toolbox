from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

JPEG_QUALITY = 95
WEBP_QUALITY = 95


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


def output_path(source: Path, output_dir: Path) -> Path:
    candidate = output_dir / f"{source.stem}_watermarked{source.suffix.lower()}"
    index = 2
    while candidate.exists():
        candidate = output_dir / f"{source.stem}_watermarked_{index}{source.suffix.lower()}"
        index += 1
    return candidate


def process_image(source: Path, destination: Path, options: WatermarkOptions) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        original.load()
        size = original.size
        exif = original.info.get("exif")
        icc = original.info.get("icc_profile")
        result = render_watermark(original, options)
        suffix = source.suffix.lower()
        save_options = {}
        if exif:
            save_options["exif"] = exif
        if icc:
            save_options["icc_profile"] = icc
        if suffix in {".jpg", ".jpeg"}:
            result = result.convert("RGB")
            save_options.update(quality=JPEG_QUALITY, subsampling=0)
            image_format = "JPEG"
        elif suffix == ".webp":
            save_options.update(quality=WEBP_QUALITY, method=6)
            image_format = "WEBP"
        else:
            image_format = "PNG"
        result.save(destination, format=image_format, **save_options)
        if result.size != size:
            raise RuntimeError("输出图片尺寸发生变化")
