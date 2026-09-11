import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.image_processing import WatermarkOptions
from tools.watermark.worker import WatermarkWorker


class WorkerTests(unittest.TestCase):
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
            self.assertTrue((output / "valid_watermarked.png").exists())


if __name__ == "__main__":
    unittest.main()
