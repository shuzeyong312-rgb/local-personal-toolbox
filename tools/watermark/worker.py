from pathlib import Path

from PySide6.QtCore import QThread, Signal

from services.image_processing import WatermarkOptions, output_path, process_image


class WatermarkWorker(QThread):
    progress = Signal(int, int, int, int)
    completed = Signal(int, int, list)

    def __init__(
        self,
        sources: list[Path],
        output_dir: Path,
        options: WatermarkOptions,
        output_format: str = "original",
        quality: int = 95,
        preserve_order: bool = False,
    ) -> None:
        super().__init__()
        self.sources = sources
        self.output_dir = output_dir
        self.options = options
        self.output_format = output_format
        self.quality = quality
        self.preserve_order = preserve_order

    def run(self) -> None:
        success = 0
        failures: list[str] = []
        total = len(self.sources)
        for done, source in enumerate(self.sources, 1):
            if self.isInterruptionRequested():
                return
            try:
                prefix = str(done).zfill(max(3, len(str(total)))) if self.preserve_order else ""
                destination = output_path(source, self.output_dir, self.output_format, prefix)
                process_image(source, destination, self.options, self.output_format, self.quality)
                success += 1
            except Exception as exc:
                failures.append(f"{source.name}: {exc}")
            self.progress.emit(done, total, success, len(failures))
        self.completed.emit(success, len(failures), failures)
