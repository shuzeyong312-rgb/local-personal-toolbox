from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout, QWidget

from utils.system import open_folder


class BaseDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("baseDialog")
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(480)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        shell = QWidget(objectName="dialogShell")
        outer.addWidget(shell)
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        self.title_label = QLabel(title, objectName="dialogTitle")
        self.title_label.setContentsMargins(24, 20, 24, 18)
        shell_layout.addWidget(self.title_label)
        content = QWidget(objectName="dialogContent")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(16)
        shell_layout.addWidget(content)


class TaskDialog(BaseDialog):
    def __init__(self, total: int, output_dir: Path, parent: QWidget | None = None, title: str = "正在处理图片") -> None:
        super().__init__(title, parent)
        self.output_dir = output_dir
        self.total = total
        self.success = 0
        self.failed = 0
        self.processing = True

        self.progress = QProgressBar()
        self.progress.setRange(0, total)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.layout.addWidget(self.progress)
        self.progress_count = QLabel(f"已处理 0 / 总数 {total}", objectName="progressCount")
        self.layout.addWidget(self.progress_count)
        self.status = QLabel("正在处理，请稍候", objectName="statusText")
        self.layout.addWidget(self.status)

        self.result = QWidget()
        result_layout = QVBoxLayout(self.result)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(16)
        summary = QHBoxLayout()
        summary.setSpacing(10)
        self.result_icon = QLabel("✓", objectName="resultIcon")
        summary.addWidget(self.result_icon)
        counts = QHBoxLayout()
        counts.setSpacing(8)
        self.success_label = QLabel(objectName="resultSuccess")
        self.failure_label = QLabel(objectName="resultFailure")
        counts.addWidget(self.success_label)
        counts.addWidget(self.failure_label)
        counts.addStretch()
        summary.addLayout(counts, 1)
        result_layout.addLayout(summary)
        self.statistics = QLabel(objectName="statusText")
        self.statistics.setWordWrap(True)
        self.statistics.hide()
        result_layout.addWidget(self.statistics)
        output = QWidget(objectName="outputSummary")
        output_layout = QVBoxLayout(output)
        output_layout.setContentsMargins(14, 12, 14, 12)
        output_layout.setSpacing(3)
        output_layout.addWidget(QLabel("输出目录", objectName="outputCaption"))
        self.output_name = QLabel(objectName="outputName")
        output_layout.addWidget(self.output_name)
        self.output_path = QLabel(objectName="outputPath")
        self.output_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.output_path.setWordWrap(True)
        output_layout.addWidget(self.output_path)
        result_layout.addWidget(output)
        self.details_button = QPushButton("查看失败详情")
        self.details_button.setCheckable(True)
        self.details = QPlainTextEdit(objectName="failureDetails")
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(180)
        self.details.hide()
        self.details_button.toggled.connect(self.details.setVisible)
        self.details_button.toggled.connect(
            lambda shown: self.details_button.setText("收起失败详情" if shown else "查看失败详情")
        )
        result_layout.addWidget(self.details_button)
        result_layout.addWidget(self.details)
        actions = QHBoxLayout()
        actions.addStretch()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        open_button = QPushButton("打开文件夹", objectName="primary")
        open_button.clicked.connect(lambda: open_folder(self.output_dir))
        actions.addWidget(close_button)
        actions.addWidget(open_button)
        result_layout.addLayout(actions)
        self.result.hide()
        self.layout.addWidget(self.result)

    def update_progress(self, done: int, total: int, success: int, failed: int) -> None:
        self.success = success
        self.failed = failed
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        self.progress_count.setText(f"已处理 {done} / 总数 {total}")

    def set_current(self, name: str) -> None:
        self.status.setText(f"当前：{name}")

    def show_result(self, success: int, failed: int, failures: list[str], title: str = "处理完成") -> None:
        self.processing = False
        self.title_label.setText(title)
        self.setWindowTitle(title)
        self.progress.hide()
        self.progress_count.hide()
        self.status.hide()
        self.success_label.setText(f"成功 {success} 张")
        self.failure_label.setText(f"失败 {failed} 张")
        self.failure_label.setProperty("empty", failed == 0)
        self.failure_label.style().unpolish(self.failure_label)
        self.failure_label.style().polish(self.failure_label)
        self.output_name.setText(self.output_dir.name or str(self.output_dir))
        self.output_path.setText(str(self.output_dir))
        self.details.setPlainText("\n".join(failures))
        self.details_button.setVisible(bool(failures))
        self.result.show()

    def reject(self) -> None:
        if not self.processing:
            super().reject()

    def closeEvent(self, event) -> None:
        if self.processing:
            event.ignore()
        else:
            super().closeEvent(event)
