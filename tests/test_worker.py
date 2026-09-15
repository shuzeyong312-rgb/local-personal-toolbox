import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.image_processing import WatermarkOptions
from services.image_resize import ResizeOptions
from tools.compression.worker import CompressionWorker
from tools.conversion.worker import ConversionWorker
from services.image_conversion import ConversionOptions
from tools.resize.worker import ResizeWorker
from tools.watermark.worker import WatermarkWorker


class WorkerTests(unittest.TestCase):
    def test_conversion_worker_continues_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            invalid, valid = root / "broken.png", root / "valid.png"
            invalid.write_text("not an image", encoding="utf-8")
            Image.new("RGBA", (10, 12), (255, 0, 0, 0)).save(valid)
            completed = []
            worker = ConversionWorker([invalid, valid], root / "output", ConversionOptions(target_format="jpg"))
            worker.completed.connect(lambda *result: completed.append(result))
            worker.run()
            self.assertEqual((1, 0, 1), completed[0][:3])
            self.assertTrue((root / "output" / "valid.jpg").exists())

    def test_one_failure_does_not_stop_batch(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            valid = root / "valid.png"
            invalid = root / "invalid.jpg"
            output = root / "output"
            Image.new("RGB", (40, 30), "red").save(valid)
            invalid.write_text("not an image", encoding="utf-8")
            completed = []
            worker = WatermarkWorker([invalid, valid], output, WatermarkOptions(text="x"))
            worker.completed.connect(lambda success, failed, errors: completed.append((success, failed, errors)))
            worker.run()
            self.assertEqual((1, 1), completed[0][:2])
            self.assertTrue((output / "valid_水印版.png").exists())

    def test_resize_worker_continues_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            valid, invalid, output = root / "valid.png", root / "invalid.jpg", root / "output"
            Image.new("RGB", (40, 30), "red").save(valid)
            invalid.write_text("not an image", encoding="utf-8")
            completed = []
            worker = ResizeWorker([invalid, valid], output, ResizeOptions(mode="width", width=20))
            worker.completed.connect(lambda success, failed, errors: completed.append((success, failed, errors)))
            worker.run()
            self.assertEqual((1, 1), completed[0][:2])
            self.assertTrue((output / "valid_resized.png").exists())

    def test_watermark_output_names_keep_input_order(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            sources = [root / "z.png", root / "a.png"]
            for source in sources:
                Image.new("RGB", (10, 10), "red").save(source)

            WatermarkWorker(
                sources, root / "output", WatermarkOptions(text="x"), preserve_order=True
            ).run()

            self.assertEqual(
                ["001_z_水印版.png", "002_a_水印版.png"],
                sorted(path.name for path in (root / "output").iterdir()),
            )

    def test_compression_worker_continues_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            valid, invalid = root / "valid.jpg", root / "invalid.jpg"
            Image.effect_noise((400, 400), 80).save(valid, quality=100)
            invalid.write_text("not an image", encoding="utf-8")
            completed = []
            worker = CompressionWorker([invalid, valid], 65, root / "output")
            worker.completed.connect(lambda *result: completed.append(result))
            worker.run()
            self.assertEqual((1, 0, 1), completed[0][:3])
            self.assertTrue((root / "output" / "valid.jpg").exists())


if __name__ == "__main__":
    unittest.main()
