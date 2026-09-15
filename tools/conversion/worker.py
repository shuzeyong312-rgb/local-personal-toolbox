from pathlib import Path

from PySide6.QtCore import QThread, Signal

from services.image_conversion import ConversionOptions, convert_image, output_path


class ConversionWorker(QThread):
    current = Signal(str)
    progress = Signal(int, int, int, int, str)
    completed = Signal(int, int, int, list, bool)

    def __init__(self, sources: list[Path], output_dir: Path | None, options: ConversionOptions) -> None:
        super().__init__()
        self.sources = sources
        self.output_dir = output_dir
        self.options = options

    def run(self) -> None:
        success = skipped = 0
        failures: list[str] = []
        total = len(self.sources)
        cancelled = False
        for done, source in enumerate(self.sources, 1):
            if self.isInterruptionRequested():
                cancelled = True
                break
            self.current.emit(source.name)
            destination = output_path(source, self.output_dir or source.parent, self.options)
            if destination is None:
                skipped += 1
            else:
                temporary = destination.with_name(f".{destination.name}.tmp") if self.options.collision == "overwrite" and destination.exists() else destination
                try:
                    convert_image(source, temporary, self.options)
                    if temporary != destination:
                        temporary.replace(destination)
                    success += 1
                except Exception as exc:
                    temporary.unlink(missing_ok=True)
                    failures.append(f"{source.name}: {exc}")
            self.progress.emit(done, total, success, len(failures), source.name)
        self.completed.emit(success, skipped, len(failures), failures, cancelled)
