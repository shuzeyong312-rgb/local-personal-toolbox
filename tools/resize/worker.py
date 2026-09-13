from pathlib import Path

from PySide6.QtCore import QThread, Signal

from services.image_resize import ResizeOptions, process_resize, resize_output_path


class ResizeWorker(QThread):
    progress = Signal(int, int, int, int)
    completed = Signal(int, int, list)

    def __init__(self, sources: list[Path], output_dir: Path, options: ResizeOptions) -> None:
        super().__init__()
        self.sources = sources
        self.output_dir = output_dir
        self.options = options

    def run(self) -> None:
        success = 0
        failures: list[str] = []
        total = len(self.sources)
        for done, source in enumerate(self.sources, 1):
            if self.isInterruptionRequested():
                return
            try:
                process_resize(source, resize_output_path(source, self.output_dir), self.options)
                success += 1
            except Exception as exc:
                failures.append(f"{source.name}: {exc}")
            self.progress.emit(done, total, success, len(failures))
        self.completed.emit(success, len(failures), failures)
