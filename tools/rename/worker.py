from PySide6.QtCore import QThread, Signal

from services.file_rename import RenamePlan, execute_rename


class RenameWorker(QThread):
    progress = Signal(int, int, int, int)
    completed = Signal(int, int, list)

    def __init__(self, plans: list[RenamePlan]) -> None:
        super().__init__()
        self.plans = plans

    def run(self) -> None:
        success, failures = execute_rename(self.plans)
        failed = len(self.plans) - success
        self.progress.emit(len(self.plans), len(self.plans), success, failed)
        self.completed.emit(success, failed, failures)
