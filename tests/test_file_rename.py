import os
import tempfile
import unittest
from pathlib import Path

from services.file_rename import RenamePlan, build_rename_plan, execute_rename, find_conflicts


class FileRenameTests(unittest.TestCase):
    def test_sort_is_stable_and_extensions_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            later, first_b, first_a = root / "later.webp", root / "b.png", root / "A.jpg"
            for path in (later, first_b, first_a):
                path.write_text(path.name, encoding="utf-8")
            os.utime(later, (200, 200))
            os.utime(first_b, (100, 100))
            os.utime(first_a, (100, 100))
            plans = build_rename_plan([later, first_b, first_a], digits=2)
            self.assertEqual(["A.jpg", "b.png", "later.webp"], [plan.source.name for plan in plans])
            self.assertEqual(["详情页_01.jpg", "详情页_02.png", "详情页_03.webp"], [plan.destination.name for plan in plans])
            descending = build_rename_plan([first_b, later, first_a], sort_by="mtime_desc")
            self.assertEqual(["later.webp", "A.jpg", "b.png"], [plan.source.name for plan in descending])

    def test_external_conflict_blocks_without_modifying_files(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            source, occupied = root / "uuid.png", root / "详情页_1.png"
            source.write_text("source", encoding="utf-8")
            occupied.write_text("keep", encoding="utf-8")
            plans = build_rename_plan([source])
            self.assertEqual(["目标文件已存在：详情页_1.png"], find_conflicts(plans))
            success, failures = execute_rename(plans)
            self.assertEqual(0, success)
            self.assertTrue(failures)
            self.assertEqual("source", source.read_text(encoding="utf-8"))
            self.assertEqual("keep", occupied.read_text(encoding="utf-8"))

    def test_two_phase_rename_supports_batch_name_swap(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            first, second = root / "a.png", root / "b.png"
            first.write_text("A", encoding="utf-8")
            second.write_text("B", encoding="utf-8")
            plans = [RenamePlan(first, second, 0), RenamePlan(second, first, 0)]
            success, failures = execute_rename(plans)
            self.assertEqual((2, []), (success, failures))
            self.assertEqual("B", first.read_text(encoding="utf-8"))
            self.assertEqual("A", second.read_text(encoding="utf-8"))

    def test_invalid_prefix_and_mixed_folders_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            one = root / "one.txt"
            child = root / "child"
            child.mkdir()
            two = child / "two.txt"
            one.touch()
            two.touch()
            with self.assertRaisesRegex(ValueError, "前缀"):
                build_rename_plan([one], prefix="bad/name")
            with self.assertRaisesRegex(ValueError, "同一文件夹"):
                build_rename_plan([one, two])


if __name__ == "__main__":
    unittest.main()
