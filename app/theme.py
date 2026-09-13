BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
SIDEBAR = "#111827"
PRIMARY = "#3478F6"
PRIMARY_HOVER = "#2563EB"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#64748B"
TEXT_MUTED = "#94A3B8"
BORDER = "#E4E9F0"
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"


STYLE = f"""
QWidget {{ color: {TEXT_PRIMARY}; font-family: "Microsoft YaHei UI"; font-size: 14px; }}
QMainWindow, QWidget#appRoot, QWidget#page, QStackedWidget, QScrollArea#settingsScroll {{ background: {BACKGROUND}; }}
QWidget#sidebar {{ background: {SIDEBAR}; }}
QLabel#brand {{ color: #F8FAFC; font-size: 20px; font-weight: 700; }}
QLabel#brandHint {{ color: #64748B; font-size: 11px; font-weight: 500; }}
QLabel#sidebarSection {{ color: #7F8DA3; font-size: 12px; font-weight: 600; padding: 18px 20px 8px; }}
QListWidget#navigation {{ background: transparent; color: #AAB4C3; border: 0; outline: 0; padding: 0 10px; }}
QListWidget#navigation::item {{ min-height: 42px; padding: 0 12px; border-radius: 8px; margin: 2px 0; }}
QListWidget#navigation::item:hover {{ background: #1E293B; color: #F8FAFC; }}
QListWidget#navigation::item:selected {{ background: {PRIMARY_HOVER}; color: white; font-weight: 600; }}
QLabel#privacy {{ color: #526075; font-size: 11px; padding: 10px 20px; }}
QWidget#titleBar {{ background: {BACKGROUND}; }}
QPushButton#windowButton {{ background: transparent; border: 0; border-radius: 0; min-width: 46px; max-width: 46px; min-height: 48px; max-height: 48px; padding: 0; font-size: 16px; }}
QPushButton#windowButton:hover {{ background: #EEF2F7; }}
QPushButton#closeButton {{ background: transparent; border: 0; border-radius: 0; min-width: 46px; max-width: 46px; min-height: 48px; max-height: 48px; padding: 0; font-size: 18px; }}
QPushButton#closeButton:hover {{ background: #E81123; color: white; }}
QLabel#pageEyebrow {{ color: {PRIMARY}; font-size: 12px; font-weight: 600; }}
QLabel#pageTitle {{ color: {TEXT_PRIMARY}; font-size: 27px; font-weight: 700; }}
QLabel#pageSubtitle {{ color: {TEXT_SECONDARY}; font-size: 13px; }}
QWidget#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel#cardTitle {{ color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700; }}
QLabel#fieldLabel {{ color: #344258; font-size: 13px; font-weight: 500; }}
QLabel#fieldValue {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#helperText {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLineEdit, QSpinBox, QComboBox {{ background: {SURFACE}; border: 1px solid #D7DEE8; border-radius: 8px; padding: 0 12px; min-height: 38px; selection-background-color: {PRIMARY}; }}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{ border-color: #AAB7C8; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {PRIMARY}; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 22px; border-left: 1px solid {BORDER}; background: #F8FAFC; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 8px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 8px; }}
QComboBox::drop-down {{ width: 30px; border: 0; }}
QPushButton {{ background: {SURFACE}; border: 1px solid #D7DEE8; border-radius: 8px; padding: 0 14px; min-height: 38px; font-weight: 500; }}
QPushButton:hover {{ background: #F8FAFC; border-color: #AAB7C8; }}
QPushButton:pressed {{ background: #EEF2F7; }}
QPushButton#primary {{ background: {PRIMARY}; border-color: {PRIMARY}; color: white; font-weight: 600; }}
QPushButton#primary:hover {{ background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}
QPushButton#startButton {{ background: {PRIMARY}; border-color: {PRIMARY}; color: white; min-height: 44px; font-weight: 600; }}
QPushButton#startButton:hover {{ background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}
QPushButton#ghost {{ color: {TEXT_SECONDARY}; border-color: transparent; background: transparent; }}
QPushButton#ghost:hover {{ color: {DANGER}; background: #FEF2F2; }}
QPushButton#rowRemove {{ color: {TEXT_MUTED}; border: 0; background: transparent; min-width: 32px; max-width: 32px; min-height: 32px; padding: 0; font-size: 17px; }}
QPushButton#rowRemove:hover {{ color: {DANGER}; background: #FEF2F2; }}
QPushButton:disabled {{ background: #EDF0F4; color: #A1AAB8; border-color: #E3E7ED; }}
QCheckBox {{ spacing: 9px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid #B8C3D2; border-radius: 4px; background: white; }}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border-color: {PRIMARY}; }}
QSlider::groove:horizontal {{ height: 5px; background: #DFE5ED; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {PRIMARY}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: white; border: 2px solid {PRIMARY}; width: 15px; margin: -6px 0; border-radius: 8px; }}
QListWidget#dropList {{ background: #FAFBFD; border: 1px solid {BORDER}; border-radius: 8px; outline: 0; padding: 4px; }}
QListWidget#dropList::item {{ min-height: 40px; border-radius: 6px; color: #344258; }}
QListWidget#dropList::item:selected {{ background: #E8F0FF; color: #1F57BD; }}
QLabel#countLabel {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#preview {{ background: #F8FAFC; border: 1px solid {BORDER}; border-radius: 12px; color: #74839A; padding: 24px; }}
QLabel#preview[dropActive="true"] {{ background: #EFF6FF; border: 1px solid {PRIMARY}; color: {PRIMARY}; }}
QWidget#statusPanel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel#statusText {{ color: #536175; font-size: 12px; }}
QLabel#statusText[status="success"] {{ color: {SUCCESS}; font-weight: 600; }}
QLabel#statusText[status="warning"] {{ color: {WARNING}; font-weight: 600; }}
QLabel#statusText[status="danger"] {{ color: {DANGER}; font-weight: 600; }}
QProgressBar {{ background: #E5EAF1; border: 0; border-radius: 4px; min-height: 8px; max-height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 4px; }}
QSplitter::handle {{ background: transparent; width: 16px; }}
QScrollArea {{ border: 0; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
