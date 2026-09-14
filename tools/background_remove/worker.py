from pathlib import Path

from PySide6.QtCore import QThread, Signal

from services.image_background_remove import (
    BackgroundRemoveOptions,
    background_remove_output_path,
    process_background_remove,
)


class BackgroundRemoveWorker(QThread):
    progress = Signal(int, int, int, int)
    current_file = Signal(str)
    completed = Signal(int, int, list)

    def __init__(self, sources: list[Path], output_dir: Path, options: BackgroundRemoveOptions) -> None:
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
            self.current_file.emit(source.name)
            try:
                process_background_remove(source, background_remove_output_path(source, self.output_dir), self.options)
                success += 1
            except Exception as exc:
                failures.append(f"{source.name}: {exc}")
            self.progress.emit(done, total, success, len(failures))
        self.completed.emit(success, len(failures), failures)
