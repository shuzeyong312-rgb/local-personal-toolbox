import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageCms

from services.image_resize import ResizeOptions, calculate_output_size, process_resize, resize_image, resize_output_path


class ImageResizeTests(unittest.TestCase):
    def test_required_resize_modes(self) -> None:
        image = Image.new("RGB", (1200, 800), "red")
        contained = resize_image(image, ResizeOptions())
        self.assertEqual((800, 800), contained.size)
        self.assertEqual((255, 255, 255), contained.getpixel((0, 0)))
        self.assertEqual((255, 0, 0), contained.getpixel((400, 400)))
        self.assertEqual((255, 255, 255), contained.getpixel((400, 132)))
        self.assertEqual((255, 0, 0), contained.getpixel((400, 133)))
        self.assertEqual((255, 0, 0), contained.getpixel((400, 665)))
        self.assertEqual((255, 255, 255), contained.getpixel((400, 666)))
        self.assertEqual((800, 800), resize_image(image, ResizeOptions(fit_mode="cover")).size)
        self.assertEqual((800, 800), resize_image(image, ResizeOptions(fit_mode="stretch")).size)
        self.assertEqual((800, 600), calculate_output_size((1600, 1200), ResizeOptions(mode="width", width=800)))
        self.assertEqual((800, 600), calculate_output_size((1600, 1200), ResizeOptions(mode="height", height=600)))
        self.assertEqual((1600, 1200), calculate_output_size((4000, 3000), ResizeOptions(mode="max", width=1600, height=1600)))
        self.assertEqual((800, 600), calculate_output_size((800, 600), ResizeOptions(mode="width", width=1600)))
        self.assertEqual((1600, 1200), calculate_output_size((800, 600), ResizeOptions(mode="width", width=1600, prevent_upscale=False)))

    def test_formats_alpha_metadata_orientation_failure_and_names(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for suffix, mode in (("jpg", "RGB"), ("png", "RGBA"), ("webp", "RGB")):
                source = root / f"source.{suffix}"
                destination = root / f"result.{suffix}"
                image = Image.new(mode, (40, 20), (1, 2, 3, 0) if mode == "RGBA" else (1, 2, 3))
                if suffix == "jpg":
                    exif = Image.Exif()
                    exif[274] = 6
                    exif[315] = "resize-test"
                    image.save(source, exif=exif)
                else:
                    image.save(source)
                process_resize(source, destination, ResizeOptions(mode="width", width=10, prevent_upscale=False))
                with Image.open(destination) as result:
                    expected = (10, 20) if suffix == "jpg" else (10, 5)
                    self.assertEqual(expected, result.size)
                    if suffix == "png":
                        self.assertEqual(0, result.getpixel((0, 0))[3])
                    if suffix == "jpg":
                        self.assertEqual("resize-test", result.getexif().get(315))
                        self.assertIsNone(result.getexif().get(274))
            source = root / "source.png"
            first = resize_output_path(source, root)
            self.assertEqual("source_resized.png", first.name)
            first.touch()
            self.assertEqual("source_resized_2.png", resize_output_path(source, root).name)
            damaged = root / "damaged.jpg"
            damaged.write_text("bad", encoding="utf-8")
            with self.assertRaises(Exception):
                process_resize(damaged, root / "bad.jpg", ResizeOptions())

    def test_icc_profile_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, destination = root / "source.png", root / "result.png"
            profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
            Image.new("RGB", (20, 10)).save(source, icc_profile=profile)
            process_resize(source, destination, ResizeOptions(mode="width", width=10))
            with Image.open(destination) as result:
                self.assertEqual(profile, result.info.get("icc_profile"))


if __name__ == "__main__":
    unittest.main()
