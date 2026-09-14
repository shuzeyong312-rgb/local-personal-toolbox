import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.image_compression import compress_image, compression_output_path


class ImageCompressionTests(unittest.TestCase):
    def test_supported_formats_preserve_format_dimensions_and_alpha(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for suffix, mode in (("jpg", "RGB"), ("png", "RGBA"), ("webp", "RGB")):
                source = root / f"source.{suffix}"
                destination = root / f"result.{suffix}"
                Image.effect_noise((500, 500), 80).convert(mode).save(source, quality=100)
                result = compress_image(source, destination, 65)
                if result.status == "压缩成功":
                    with Image.open(destination) as compressed:
                        self.assertEqual((500, 500), compressed.size)
                        self.assertEqual({"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}[suffix], compressed.format)
                        if suffix == "png":
                            self.assertIn("A", compressed.getbands())
                    self.assertLess(result.compressed_size, result.original_size)
                else:
                    self.assertEqual("无需压缩", result.status)
                    self.assertFalse(destination.exists())

    def test_output_name_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "商品.jpg"
            Image.new("RGB", (10, 10)).save(source)
            first = compression_output_path(source)
            self.assertEqual(root / "压缩结果" / "商品.jpg", first)
            first.parent.mkdir()
            first.touch()
            self.assertEqual("商品_1.jpg", compression_output_path(source).name)

    def test_invalid_quality_and_damaged_image_fail(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            damaged = root / "bad.jpg"
            damaged.write_text("bad", encoding="utf-8")
            with self.assertRaises(ValueError):
                compress_image(damaged, root / "out.jpg", 0)
            with self.assertRaises(Exception):
                compress_image(damaged, root / "out.jpg")


if __name__ == "__main__":
    unittest.main()
