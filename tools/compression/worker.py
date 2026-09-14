from pathlib import Path

from PySide6.QtCore import QThread, Signal

from services.image_compression import compress_image, compression_output_path


class CompressionWorker(QThread):
    current = Signal(str)
    progress = Signal(int, int, int, int, str)
    item_completed = Signal(object)
    item_failed = Signal(object, str)
    completed = Signal(int, int, int, int, int, list)

    def __init__(self, sources: list[Path], quality: int, output_dir: Path | None = None) -> None:
        super().__init__()
        self.sources = sources
        self.quality = quality
        self.output_dir = output_dir

    def run(self) -> None:
        success = skipped = 0
        before = after = 0
        failures: list[str] = []
        total = len(self.sources)
        for done, source in enumerate(self.sources, 1):
            if self.isInterruptionRequested():
                return
            self.current.emit(source.name)
            destination = compression_output_path(source, self.output_dir)
            try:
                result = compress_image(source, destination, self.quality)
                before += result.original_size
                after += result.compressed_size
                success += result.status == "压缩成功"
                skipped += result.status == "无需压缩"
                self.item_completed.emit(result)
            except Exception as exc:
                destination.unlink(missing_ok=True)
                failures.append(f"{source.name}: {exc}")
                self.item_failed.emit(source, str(exc))
            self.progress.emit(done, total, success + skipped, len(failures), source.name)
        self.completed.emit(success, skipped, len(failures), before, after, failures)
