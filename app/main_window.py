import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from tools.watermark.page import WatermarkPage


STYLE = """
QWidget { color: #172033; font-family: "Microsoft YaHei UI"; font-size: 14px; }
QMainWindow, QWidget#appRoot, QWidget#page, QStackedWidget { background: #f5f7fb; }
QWidget#sidebar { background: #111827; }
QLabel#brand { color: #f8fafc; font-size: 20px; font-weight: 700; }
QLabel#brandHint { color: #64748b; font-size: 11px; }
QLabel#sidebarSection { color: #7f8da3; font-size: 12px; font-weight: 600; padding: 18px 20px 7px; }
QListWidget#navigation { background: transparent; color: #bac5d6; border: 0; outline: 0; padding: 0 10px; }
QListWidget#navigation::item { min-height: 42px; padding: 0 14px; border-radius: 8px; margin: 2px 0; }
QListWidget#navigation::item:hover { background: #1e293b; color: #f8fafc; }
QListWidget#navigation::item:selected { background: #2f6fed; color: white; font-weight: 600; }
QLabel#version { color: #526075; font-size: 11px; padding: 10px 20px; }
QLabel#pageEyebrow { color: #2f6fed; font-size: 12px; font-weight: 700; }
QLabel#pageTitle { color: #111827; font-size: 27px; font-weight: 700; }
QLabel#pageSubtitle { color: #64748b; font-size: 13px; }
QGroupBox { background: #ffffff; border: 1px solid #e3e8f0; border-radius: 12px; margin-top: 16px; padding: 20px 16px 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 7px; color: #273449; background: #ffffff; }
QLineEdit, QSpinBox, QComboBox { background: #ffffff; border: 1px solid #cfd7e3; border-radius: 7px; padding: 0 10px; min-height: 36px; selection-background-color: #2f6fed; }
QLineEdit:hover, QSpinBox:hover, QComboBox:hover { border-color: #9aa9bd; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #2f6fed; }
QSpinBox::up-button, QSpinBox::down-button { width: 22px; border-left: 1px solid #e2e7ef; background: #f8fafc; }
QSpinBox::up-button { subcontrol-position: top right; border-top-right-radius: 7px; }
QSpinBox::down-button { subcontrol-position: bottom right; border-bottom-right-radius: 7px; }
QComboBox::drop-down { width: 30px; border: 0; }
QPushButton { background: #ffffff; border: 1px solid #cfd7e3; border-radius: 7px; padding: 0 14px; min-height: 36px; font-weight: 500; }
QPushButton:hover { background: #f8fafc; border-color: #8fa1b8; }
QPushButton:pressed { background: #eef2f7; }
QPushButton#primary { background: #2f6fed; border-color: #2f6fed; color: white; min-height: 40px; font-weight: 600; }
QPushButton#primary:hover { background: #245fd6; border-color: #245fd6; }
QPushButton#ghost { color: #64748b; border-color: transparent; background: transparent; }
QPushButton#ghost:hover { color: #dc2626; background: #fef2f2; }
QPushButton:disabled { background: #edf0f4; color: #a1aab8; border-color: #e3e7ed; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 17px; height: 17px; border: 1px solid #b8c3d2; border-radius: 4px; background: white; }
QCheckBox::indicator:checked { background: #2f6fed; border-color: #2f6fed; }
QSlider::groove:horizontal { height: 5px; background: #dfe5ed; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #2f6fed; border-radius: 2px; }
QSlider::handle:horizontal { background: white; border: 2px solid #2f6fed; width: 15px; margin: -6px 0; border-radius: 8px; }
QListWidget#dropList { background: #fafbfd; border: 1px dashed #c8d2df; border-radius: 9px; outline: 0; padding: 6px; }
QListWidget#dropList::item { min-height: 32px; padding: 0 8px; border-radius: 5px; color: #344258; }
QListWidget#dropList::item:selected { background: #e8f0ff; color: #1f57bd; }
QLabel#countChip { background: #eef4ff; color: #245fc8; border-radius: 6px; padding: 5px 9px; font-size: 12px; }
QLabel#preview { background: #f8fafc; border: 1px dashed #c8d2df; border-radius: 10px; color: #74839a; }
QWidget#statusPanel { background: #ffffff; border: 1px solid #e3e8f0; border-radius: 10px; }
QLabel#statusText { color: #536175; font-size: 12px; }
QProgressBar { background: #e5eaf1; border: 0; border-radius: 4px; min-height: 8px; max-height: 8px; text-align: center; }
QProgressBar::chunk { background: #2f6fed; border-radius: 4px; }
QSplitter::handle { background: transparent; width: 18px; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("本地个人工具箱")
        self.resize(1240, 820)
        self.setMinimumSize(1080, 700)

        root = QWidget(objectName="appRoot")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QWidget(objectName="sidebar")
        sidebar.setFixedWidth(208)
        side_layout = QHBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_container = QWidget(objectName="sidebar")
        column = QVBoxLayout(side_container)
        column.setContentsMargins(0, 0, 0, 12)
        column.setSpacing(0)
        brand_box = QWidget()
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(20, 24, 20, 16)
        brand_layout.setSpacing(2)
        brand_layout.addWidget(QLabel("个人工具箱", objectName="brand"))
        brand_layout.addWidget(QLabel("LOCAL TOOLBOX", objectName="brandHint"))
        column.addWidget(brand_box)
        column.addWidget(QLabel("图片工具", objectName="sidebarSection"))
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.addItem("批量打水印")
        self.navigation.setCurrentRow(0)
        column.addWidget(self.navigation)
        column.addWidget(QLabel("本地处理 · 数据不上传", objectName="version"))
        side_layout.addWidget(side_container)

        self.pages = QStackedWidget()
        self.watermark_page = WatermarkPage()
        self.pages.addWidget(self.watermark_page)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)

    def closeEvent(self, event) -> None:
        self.watermark_page.stop_worker()
        super().closeEvent(event)


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("本地个人工具箱")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return app.exec()
