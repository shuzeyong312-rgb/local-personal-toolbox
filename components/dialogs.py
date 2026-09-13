from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from utils.system import open_folder


class BaseDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("baseDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(460)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 20)
        self.layout.setSpacing(16)
        self.layout.addWidget(QLabel(title, objectName="dialogTitle"))


class ResultDialog(BaseDialog):
    def __init__(self, success: int, failed: int, output_dir: Path, failures: list[str], parent: QWidget | None = None) -> None:
        super().__init__("处理结果", parent)
        self.output_dir = output_dir

        counts = QHBoxLayout()
        counts.addWidget(QLabel(f"成功 {success} 张", objectName="resultSuccess"))
        counts.addWidget(QLabel(f"失败 {failed} 张", objectName="resultFailure"))
        counts.addStretch()
        self.layout.addLayout(counts)

        output = QLabel(f"输出目录：{output_dir}")
        output.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        output.setWordWrap(True)
        self.layout.addWidget(output)

        if failed and failures:
            details_button = QPushButton("查看失败详情")
            details_button.setCheckable(True)
            details = QPlainTextEdit("\n".join(failures))
            details.setObjectName("failureDetails")
            details.setReadOnly(True)
            details.setMaximumHeight(180)
            details.hide()
            details_button.toggled.connect(details.setVisible)
            details_button.toggled.connect(lambda shown: details_button.setText("收起失败详情" if shown else "查看失败详情"))
            self.layout.addWidget(details_button)
            self.layout.addWidget(details)

        actions = QHBoxLayout()
        actions.addStretch()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        open_button = QPushButton("打开文件夹", objectName="primary")
        open_button.clicked.connect(lambda: open_folder(self.output_dir))
        actions.addWidget(close_button)
        actions.addWidget(open_button)
        self.layout.addLayout(actions)
