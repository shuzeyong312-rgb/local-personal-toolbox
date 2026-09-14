from dataclasses import dataclass
from pathlib import Path
from statistics import median

from PIL import Image, ImageChops, ImageDraw, ImageOps


MODE_THRESHOLDS = {
    "conservative": (14, 42),
    "standard": (25, 62),
    "strong": (42, 88),
}


@dataclass(frozen=True)
class BackgroundRemoveOptions:
    mode: str = "standard"
    soften_edges: bool = True

    def __post_init__(self) -> None:
        if self.mode not in MODE_THRESHOLDS:
            raise ValueError("不支持的背景移除模式")


def detect_background_color(image: Image.Image) -> tuple[tuple[int, int, int], bool]:
    rgb = image.convert("RGB")
    step_x = max(1, rgb.width // 24)
    step_y = max(1, rgb.height // 24)
    points = (
        [(x, 0) for x in range(0, rgb.width, step_x)]
        + [(x, rgb.height - 1) for x in range(0, rgb.width, step_x)]
        + [(0, y) for y in range(0, rgb.height, step_y)]
        + [(rgb.width - 1, y) for y in range(0, rgb.height, step_y)]
    )
    colors = [rgb.getpixel(point) for point in points]
    background = tuple(round(median(channel)) for channel in zip(*colors))
    spread = median(max(abs(value[i] - background[i]) for i in range(3)) for value in colors)
    return background, spread > 24


def remove_background(
    image: Image.Image, options: BackgroundRemoveOptions = BackgroundRemoveOptions()
) -> tuple[Image.Image, bool]:
    image = ImageOps.exif_transpose(image).convert("RGBA")
    background, is_complex = detect_background_color(image)
    rgb = image.convert("RGB")
    reference = Image.new("RGB", rgb.size, background)
    difference = ImageChops.difference(rgb, reference)
    distance = ImageChops.lighter(ImageChops.lighter(*difference.split()[:2]), difference.getchannel("B"))
    clear_at, keep_at = MODE_THRESHOLDS[options.mode]

    candidate = distance.point(lambda value: 255 if value < keep_at else 0)
    connected = Image.new("L", (image.width + 2, image.height + 2), 255)
    connected.paste(candidate, (1, 1))
    ImageDraw.floodfill(connected, (0, 0), 128)
    connected = connected.crop((1, 1, image.width + 1, image.height + 1)).point(lambda value: 255 if value == 128 else 0)

    if options.soften_edges:
        alpha = distance.point(
            lambda value: 0 if value <= clear_at else 255 if value >= keep_at else round(255 * (value - clear_at) / (keep_at - clear_at))
        )
    else:
        alpha = distance.point(lambda value: 0 if value < keep_at else 255)
    alpha = ImageChops.lighter(alpha, ImageChops.invert(connected))
    image.putalpha(ImageChops.darker(image.getchannel("A"), alpha))
    return image, is_complex


def background_remove_output_path(source: Path, output_dir: Path) -> Path:
    candidate = output_dir / f"{source.stem}_透明.png"
    index = 2
    while candidate.exists() or candidate.resolve() == source.resolve():
        candidate = output_dir / f"{source.stem}_透明_{index}.png"
        index += 1
    return candidate


def process_background_remove(source: Path, destination: Path, options: BackgroundRemoveOptions) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        if getattr(original, "is_animated", False):
            raise ValueError("不支持动态图片")
        original.load()
        if original.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("不支持的图片格式")
        result, is_complex = remove_background(original, options)
        save_options = {"icc_profile": original.info["icc_profile"]} if original.info.get("icc_profile") else {}
        result.save(destination, format="PNG", **save_options)
        return is_complex
