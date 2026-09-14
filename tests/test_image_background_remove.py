import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from services.image_background_remove import (
    BackgroundRemoveOptions,
    background_remove_output_path,
    process_background_remove,
    remove_background,
)


class BackgroundRemoveTests(unittest.TestCase):
    def test_white_background_is_transparent_and_dark_product_remains(self) -> None:
        image = Image.new("RGB", (80, 80), "white")
        ImageDraw.Draw(image).rectangle((20, 20, 59, 59), fill="#202020")
        result, is_complex = remove_background(image)
        self.assertEqual(0, result.getpixel((0, 0))[3])
        self.assertEqual(255, result.getpixel((40, 40))[3])
        self.assertFalse(is_complex)

    def test_enclosed_white_product_and_highlight_are_preserved(self) -> None:
        image = Image.new("RGB", (100, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((20, 20, 80, 80), fill="#707070")
        draw.ellipse((35, 35, 65, 65), fill="white")
        draw.ellipse((25, 45, 32, 52), fill="#fafafa")
        result, _ = remove_background(image)
        self.assertEqual(255, result.getpixel((50, 50))[3])
        self.assertEqual(255, result.getpixel((28, 48))[3])

    def test_gray_background_modes_and_soft_edge(self) -> None:
        image = Image.new("RGB", (60, 60), "#dddddd")
        ImageDraw.Draw(image).rectangle((15, 15, 44, 44), fill="#303030")
        result, _ = remove_background(image, BackgroundRemoveOptions("strong"))
        self.assertEqual(0, result.getpixel((0, 0))[3])
        self.assertEqual(255, result.getpixel((30, 30))[3])

        edge = Image.new("RGB", (3, 3), "white")
        edge.putpixel((1, 1), (215, 215, 215))
        softened, _ = remove_background(edge)
        self.assertLess(0, softened.getpixel((1, 1))[3])
        self.assertLess(softened.getpixel((1, 1))[3], 255)

    def test_png_size_and_existing_alpha_are_preserved(self) -> None:
        image = Image.new("RGBA", (37, 29), (255, 255, 255, 255))
        image.putpixel((18, 14), (0, 0, 0, 90))
        result, _ = remove_background(image)
        self.assertEqual((37, 29), result.size)
        self.assertEqual(90, result.getpixel((18, 14))[3])

    def test_jpeg_noise_is_removed_and_output_names_do_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source = root / "产品.jpg"
            image = Image.new("RGB", (80, 80), "white")
            ImageDraw.Draw(image).rectangle((20, 20, 59, 59), fill="#222222")
            image.save(source, quality=55)
            output = background_remove_output_path(source, root)
            process_background_remove(source, output, BackgroundRemoveOptions())
            with Image.open(output) as result:
                self.assertEqual(0, result.getpixel((2, 2))[3])
                self.assertEqual((80, 80), result.size)
            second = background_remove_output_path(source, root)
            self.assertEqual("产品_透明_2.png", second.name)

    def test_damaged_file_does_not_prevent_later_processing(self) -> None:
        from tools.background_remove.worker import BackgroundRemoveWorker

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            damaged = root / "损坏.png"
            valid = root / "正常.png"
            damaged.write_bytes(b"not an image")
            Image.new("RGB", (20, 20), "white").save(valid)
            worker = BackgroundRemoveWorker([damaged, valid], root / "output", BackgroundRemoveOptions())
            completed = []
            worker.completed.connect(lambda success, failed, failures: completed.append((success, failed, failures)))
            worker.run()
            self.assertEqual((1, 1), completed[0][:2])
            self.assertIn("损坏.png", completed[0][2][0])
            self.assertTrue((root / "output" / "正常_透明.png").exists())


if __name__ == "__main__":
    unittest.main()
