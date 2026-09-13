import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.image_processing import JPEG_QUALITY, WatermarkOptions, output_path, process_image, render_watermark


class ImageProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.options = WatermarkOptions(text="测试水印", font_size=18, opacity=120, margin=5)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_all_formats_keep_original_dimensions(self) -> None:
        for suffix, mode in ((".jpg", "RGB"), (".png", "RGBA"), (".webp", "RGB")):
            with self.subTest(suffix=suffix):
                source = self.root / f"source{suffix}"
                destination = self.root / f"result{suffix}"
                Image.new(mode, (137, 83), (40, 80, 120, 210) if mode == "RGBA" else (40, 80, 120)).save(source)
                process_image(source, destination, self.options)
                with Image.open(destination) as result:
                    self.assertEqual((137, 83), result.size)
                    self.assertEqual(suffix.lstrip(".").replace("jpg", "JPEG").upper(), result.format.upper())

    def test_png_keeps_transparency_and_untouched_pixels(self) -> None:
        source = self.root / "transparent.png"
        destination = self.root / "result.png"
        Image.new("RGBA", (120, 80), (10, 20, 30, 0)).save(source)
        process_image(source, destination, self.options)
        with Image.open(destination) as result:
            self.assertEqual("RGBA", result.mode)
            self.assertEqual((10, 20, 30, 0), result.getpixel((0, 0)))

    def test_jpeg_uses_quality_95_and_preserves_exif(self) -> None:
        self.assertEqual(95, JPEG_QUALITY)
        source = self.root / "source.jpg"
        destination = self.root / "result.jpg"
        exif = Image.Exif()
        exif[315] = "toolbox-test"
        Image.new("RGB", (160, 90), "navy").save(source, quality=95, exif=exif)
        process_image(source, destination, self.options)
        with Image.open(destination) as result:
            self.assertEqual("toolbox-test", result.getexif().get(315))
            self.assertLessEqual(max(max(table) for table in result.quantization.values()), 12)

    def test_tiled_render_keeps_size(self) -> None:
        image = Image.new("RGBA", (200, 120), (255, 255, 255, 100))
        result = render_watermark(image, WatermarkOptions(text="tile", tiled=True, angle=35, spacing=20))
        self.assertEqual(image.size, result.size)

    def test_output_path_never_overwrites(self) -> None:
        source = self.root / "photo.png.webp"
        Image.new("RGB", (10, 10)).save(source, format="WEBP")
        first = output_path(source, self.root)
        self.assertEqual("photo_水印版.webp", first.name)
        first.touch()
        self.assertEqual("photo_水印版_2.webp", output_path(source, self.root).name)

    def test_format_conversion_transparency_and_quality(self) -> None:
        source = self.root / "transparent.webp"
        Image.new("RGBA", (20, 20), (255, 0, 0, 0)).save(source)

        png = output_path(source, self.root, "png")
        process_image(source, png, self.options, "png")
        with Image.open(png) as result:
            self.assertEqual(("PNG", "RGBA", 0), (result.format, result.mode, result.getpixel((0, 0))[3]))

        jpg = output_path(source, self.root, "jpg")
        process_image(source, jpg, self.options, "jpg", 95)
        with Image.open(jpg) as result:
            self.assertEqual(("JPEG", "RGB"), (result.format, result.mode))
            self.assertGreater(min(result.getpixel((0, 0))), 245)

    def test_animated_image_is_rejected(self) -> None:
        for suffix in ("gif", "webp"):
            with self.subTest(suffix=suffix):
                source = self.root / f"animated.{suffix}"
                frames = [Image.new("RGB", (10, 10), color) for color in ("red", "blue")]
                frames[0].save(source, save_all=True, append_images=frames[1:], duration=100, loop=0)
                with self.assertRaisesRegex(ValueError, "暂不支持动态图片水印"):
                    output_path(source, self.root, "png")


if __name__ == "__main__":
    unittest.main()
