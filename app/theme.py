APP_BACKGROUND = "#F5F7FA"
SURFACE = "#FFFFFF"
SURFACE_HOVER = "#F8FAFC"
SIDEBAR = "#111827"
PRIMARY = "#3478F6"
PRIMARY_HOVER = "#2563EB"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#64748B"
TEXT_DISABLED = "#A1AAB8"
BORDER = "#DDE3EB"
FOCUS = PRIMARY
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
CONTROL_HEIGHT = 38
RADIUS_SM = 4
RADIUS_MD = 8
RADIUS_LG = 10


STYLE = f"""
QWidget {{ color: {TEXT_PRIMARY}; font-family: "Microsoft YaHei UI"; font-size: 14px; }}
QMainWindow, QWidget#appRoot, QWidget#page, QStackedWidget, QScrollArea#settingsScroll {{ background: {APP_BACKGROUND}; }}
QWidget#sidebar {{ background: {SIDEBAR}; }}
QLabel#brand {{ color: #F8FAFC; font-size: 20px; font-weight: 700; }}
QLabel#brandHint {{ color: #64748B; font-size: 11px; font-weight: 500; }}
QLabel#sidebarSection {{ color: #7F8DA3; font-size: 12px; font-weight: 600; padding: 18px 20px 8px; }}
QListWidget#navigation {{ background: transparent; color: #AAB4C3; border: 0; outline: 0; padding: 0 10px; }}
QListWidget#navigation::item {{ min-height: 42px; padding: 0 12px; border-radius: {RADIUS_MD}px; margin: 2px 0; }}
QListWidget#navigation::item:hover {{ background: #1E293B; color: #F8FAFC; }}
QListWidget#navigation::item:selected {{ background: {PRIMARY_HOVER}; color: white; font-weight: 600; }}
QLabel#privacy {{ color: #526075; font-size: 11px; padding: 10px 20px; }}
QWidget#titleBar {{ background: {APP_BACKGROUND}; }}
QPushButton#windowButton {{ background: transparent; border: 0; border-radius: 0; min-width: 46px; max-width: 46px; min-height: 48px; max-height: 48px; padding: 0; font-size: 16px; }}
QPushButton#windowButton:hover {{ background: #EEF2F7; }}
QPushButton#closeButton {{ background: transparent; border: 0; border-radius: 0; min-width: 46px; max-width: 46px; min-height: 48px; max-height: 48px; padding: 0; font-size: 18px; }}
QPushButton#closeButton:hover {{ background: #E81123; color: white; }}
QLabel#pageTitle {{ color: {TEXT_PRIMARY}; font-size: 27px; font-weight: 700; }}
QLabel#pageSubtitle {{ color: {TEXT_SECONDARY}; font-size: 13px; }}
QWidget#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_LG}px; }}
QLabel#cardTitle {{ color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700; }}
QLabel#fieldLabel {{ color: #344258; font-size: 13px; font-weight: 500; }}
QLabel#fieldValue {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#helperText {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLineEdit, QSpinBox, QComboBox {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 0 12px; min-height: {CONTROL_HEIGHT}px; selection-background-color: {PRIMARY}; }}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{ border-color: #AAB7C8; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {FOCUS}; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ background: #EDF0F4; color: {TEXT_DISABLED}; border-color: #E3E7ED; }}
QLineEdit[error="true"] {{ border: 1px solid {DANGER}; background: #FFF9F9; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 28px; border-left: 1px solid {BORDER}; background: {SURFACE_HOVER}; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 7px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 7px; border-top: 1px solid {BORDER}; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #EEF2F7; }}
QSpinBox::up-arrow, QSpinBox::down-arrow, QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
QComboBox::drop-down {{ width: 30px; border: 0; border-left: 1px solid {BORDER}; background: {SURFACE_HOVER}; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 4px; outline: 0; selection-background-color: #E8F0FF; selection-color: #1F57BD; }}
QComboBox QAbstractItemView::item {{ min-height: 32px; padding: 0 8px; border-radius: {RADIUS_SM}px; }}
QComboBox QAbstractItemView::item:hover {{ background: #F1F5F9; }}
QPushButton {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 0 14px; min-height: {CONTROL_HEIGHT}px; font-weight: 500; }}
QPushButton:hover {{ background: {SURFACE_HOVER}; border-color: #AAB7C8; }}
QPushButton:focus {{ border: 1px solid {FOCUS}; }}
QPushButton:pressed {{ background: #EEF2F7; }}
QPushButton#primary {{ background: {PRIMARY}; border-color: {PRIMARY}; color: white; font-weight: 600; }}
QPushButton#primary:hover {{ background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}
QPushButton#startButton {{ background: {PRIMARY}; border-color: {PRIMARY}; color: white; min-height: 44px; font-weight: 600; }}
QPushButton#startButton:hover {{ background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}
QPushButton#outputButton {{ color: {TEXT_SECONDARY}; background: #F8FAFC; text-align: left; padding: 0 12px; }}
QPushButton#outputButton:hover {{ color: {TEXT_PRIMARY}; background: #F1F5F9; border-color: #AAB7C8; }}
QPushButton#outputButton[error="true"] {{ color: {DANGER}; border-color: {DANGER}; background: #FFF9F9; }}
QPushButton#ghost {{ color: {TEXT_SECONDARY}; border-color: transparent; background: transparent; }}
QPushButton#ghost:hover {{ color: {DANGER}; background: #FEF2F2; }}
QPushButton#rowRemove {{ color: {TEXT_DISABLED}; border: 0; background: transparent; min-width: 32px; max-width: 32px; min-height: 32px; padding: 0; font-size: 17px; }}
QPushButton#rowRemove:hover {{ color: {DANGER}; background: #FEF2F2; }}
QPushButton:disabled {{ background: #EDF0F4; color: {TEXT_DISABLED}; border-color: #E3E7ED; }}
QCheckBox {{ spacing: 9px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border: 1px solid #B8C3D2; border-radius: 4px; background: white; }}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border-color: {PRIMARY}; }}
QSlider {{ min-height: 28px; }}
QSlider::groove:horizontal {{ height: 5px; background: #DFE5ED; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {PRIMARY}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: white; border: 2px solid {PRIMARY}; width: 14px; height: 14px; margin: -7px 0; border-radius: 9px; }}
QListWidget#dropList {{ background: #FAFBFD; border: 1px solid {BORDER}; border-radius: 7px; outline: 0; padding: 4px; }}
QListWidget#dropList::item {{ min-height: 40px; border-radius: 6px; color: #344258; }}
QListWidget#dropList::item:selected {{ background: #E8F0FF; color: #1F57BD; }}
QLabel#countLabel {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#preview {{ background: #F8FAFC; border: 1px solid {BORDER}; border-radius: 8px; color: #74839A; padding: 18px; }}
QLabel#preview[dropActive="true"] {{ background: #EFF6FF; border: 1px solid {PRIMARY}; color: {PRIMARY}; }}
QWidget#previewEmpty {{ background: transparent; }}
QLabel#emptyTitle {{ color: #344258; font-size: 14px; font-weight: 600; }}
QLabel#emptyHint {{ color: {TEXT_DISABLED}; font-size: 12px; }}
QDialog#baseDialog {{ background: {APP_BACKGROUND}; }}
QLabel#dialogTitle {{ color: {TEXT_PRIMARY}; font-size: 18px; font-weight: 700; }}
QLabel#resultSuccess {{ color: {SUCCESS}; font-size: 15px; font-weight: 600; }}
QLabel#resultFailure {{ color: {DANGER}; font-size: 15px; font-weight: 600; }}
QPlainTextEdit#failureDetails {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 8px; }}
QWidget#statusPanel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QLabel#statusText {{ color: #536175; font-size: 12px; }}
QLabel#fieldError {{ color: {DANGER}; font-size: 12px; }}
QLabel#warningText {{ color: {WARNING}; font-size: 12px; }}
QLabel#statusText[status="success"] {{ color: {SUCCESS}; font-weight: 600; }}
QLabel#statusText[status="warning"] {{ color: {WARNING}; font-weight: 600; }}
QLabel#statusText[status="danger"] {{ color: {DANGER}; font-weight: 600; }}
QProgressBar {{ background: #E5EAF1; border: 0; border-radius: 4px; min-height: 8px; max-height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 4px; }}
QSplitter#workspaceSplitter::handle {{ background: transparent; width: 14px; }}
QScrollArea {{ border: 0; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
