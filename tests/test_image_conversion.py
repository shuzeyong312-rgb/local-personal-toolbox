import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.image_conversion import ConversionOptions, convert_image, output_path


class ImageConversionTests(unittest.TestCase):
    def test_transparent_png_to_jpg_uses_selected_background_and_keeps_size(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, destination = root / "透明.png", root / "透明.jpg"
            Image.new("RGBA", (31, 27), (255, 0, 0, 0)).save(source)
            convert_image(source, destination, ConversionOptions(target_format="jpg", background_color="#ffffff"))
            with Image.open(destination) as image:
                self.assertEqual((31, 27), image.size)
                self.assertEqual("JPEG", image.format)
                self.assertGreater(min(image.convert("RGB").getpixel((0, 0))), 240)

    def test_supported_modes_and_formats_convert_without_changing_size(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            cases = (("P", "png", "png"), ("L", "bmp", "webp"), ("CMYK", "jpg", "bmp"), ("RGB", "bmp", "png"))
            for index, (mode, source_format, target) in enumerate(cases):
                source = root / f"source-{index}.{source_format}"
                Image.new(mode, (13, 17)).save(source)
                destination = root / f"result-{index}.{target}"
                convert_image(source, destination, ConversionOptions(target_format=target, webp_lossless=True))
                with Image.open(destination) as image:
                    self.assertEqual((13, 17), image.size)

    def test_collision_modes_never_overwrite_source_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "main.png"
            source.write_bytes(b"original")
            self.assertEqual(root / "main_1.png", output_path(source, root, ConversionOptions()))
            self.assertIsNone(output_path(source, root, ConversionOptions(collision="skip")))
