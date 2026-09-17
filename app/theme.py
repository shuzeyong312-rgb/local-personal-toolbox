APP_BACKGROUND = "#F7F8FA"
SURFACE = "#FFFFFF"
SURFACE_HOVER = "#F4F6FA"
SIDEBAR = "#FFFFFF"
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#3478F6"
TEXT_PRIMARY = "#172033"
TEXT_SECONDARY = "#71809C"
TEXT_DISABLED = "#A0AABD"
BORDER = "#E7EAF0"
FOCUS = PRIMARY
SUCCESS = "#16A34A"
WARNING = "#D97706"
DANGER = "#DC2626"
CONTROL_HEIGHT = 40
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 18


STYLE = f"""
QWidget {{ color: {TEXT_PRIMARY}; font-family: "Segoe UI Variable", "Microsoft YaHei UI"; font-size: 14px; }}
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
QLabel#statLabel {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#statValue {{ color: {TEXT_PRIMARY}; font-size: 22px; font-weight: 700; }}
QLabel#fieldLabel {{ color: #344258; font-size: 13px; font-weight: 500; }}
QLabel#fieldValue {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#helperText {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit, QTimeEdit {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 0 12px; min-height: {CONTROL_HEIGHT}px; selection-background-color: {PRIMARY}; }}
QPlainTextEdit {{ padding: 9px 12px; }}
QLineEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, QDateEdit:hover, QTimeEdit:hover {{ border-color: #AAB7C8; }}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {{ border: 1px solid {FOCUS}; background: #FCFDFF; }}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled, QDateEdit:disabled, QTimeEdit:disabled {{ background: #EDF0F4; color: {TEXT_DISABLED}; border-color: #E3E7ED; }}
QLineEdit[error="true"] {{ border: 1px solid {DANGER}; background: #FFF9F9; }}
QFrame#datePopover {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; }}
QLabel#datePickerMonth {{ font-size: 15px; font-weight: 700; }}
QPushButton#iconButton {{ min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; padding: 0; border-color: transparent; }}
QPushButton#linkButton {{ color: {PRIMARY}; border-color: transparent; background: transparent; }}
QWidget#dateInput {{ background: transparent; }}
QLineEdit#dateInput {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}
QPushButton#dateButton {{ min-width: 40px; max-width: 40px; padding: 0; border-left: 0; border-top-left-radius: 0; border-bottom-left-radius: 0; color: {TEXT_SECONDARY}; }}
QCalendarWidget#datePickerCalendar {{ background: {SURFACE}; border: 0; }}
QCalendarWidget#datePickerCalendar QAbstractItemView {{ background: {SURFACE}; color: {TEXT_PRIMARY}; border: 0; outline: 0; selection-background-color: {PRIMARY}; selection-color: white; }}
QCalendarWidget#datePickerCalendar QHeaderView::section {{ background: {SURFACE}; color: {TEXT_SECONDARY}; border: 0; padding: 5px; }}
QCalendarWidget#taskCalendar QAbstractItemView {{ outline: 0; selection-background-color: #F0F5FF; selection-color: #1F2937; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 28px; border-left: 1px solid {BORDER}; background: {SURFACE_HOVER}; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 7px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 7px; border-top: 1px solid {BORDER}; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #EEF2F7; }}
QSpinBox::up-arrow, QSpinBox::down-arrow {{ image: none; width: 0; height: 0; }}
QComboBox::drop-down {{ width: 30px; border: 0; border-left: 1px solid {BORDER}; background: {SURFACE_HOVER}; border-top-right-radius: 7px; border-bottom-right-radius: 7px; }}
QComboBox::down-arrow {{ width: 9px; height: 6px; }}
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
QDialog#baseDialog {{ background: transparent; }}
QWidget#dialogShell {{ background: #F8FBFF; border: 1px solid #D7E3F5; border-radius: 16px; }}
QWidget#dialogContent {{ background: {SURFACE}; border: 0; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px; }}
QLabel#dialogTitle {{ color: #102A56; font-size: 18px; font-weight: 700; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F6FAFF, stop:1 #EEF5FF); border-top-left-radius: 16px; border-top-right-radius: 16px; }}
QWidget#dialogFooter {{ border-top: 1px solid #E7EEF8; padding-top: 14px; }}
QScrollArea#planDialogScroll, QScrollArea#planDialogScroll > QWidget > QWidget {{ background: {SURFACE}; border: 0; }}
QLabel#sectionTitle {{ color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 700; }}
QLabel#sectionHint {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QFrame#sectionDivider {{ color: #E8EDF3; max-height: 1px; }}
QWidget#stageCard {{ background: #F8FAFC; border: 1px solid #E5EAF1; border-radius: {RADIUS_MD}px; }}
QLabel#stageTitle {{ font-size: 14px; font-weight: 700; }}
QPushButton#dangerLink {{ color: {DANGER}; border: 0; background: transparent; min-height: 30px; padding: 0 6px; }}
QPushButton#dangerLink:hover {{ background: #FEF2F2; }}
QWidget#planPreview {{ background: #F8FAFC; border: 1px solid #E8EDF3; border-radius: {RADIUS_MD}px; }}
QLabel#previewItem {{ color: #344258; background: {SURFACE}; border: 1px solid #E5EAF1; border-radius: 6px; padding: 8px 10px; }}
QScrollArea#calendarTaskArea, QScrollArea#pendingReviewArea, QScrollArea#orderCalendarPageScroll,
QScrollArea#orderCalendarPageScroll > QWidget > QWidget, QWidget#orderCalendarContent,
QWidget#calendarTaskContainer {{ background: transparent; border: 0; }}
QWidget#emptyState {{ background: {SURFACE}; }}
QWidget#pendingReviewList, QWidget#reviewEmpty {{ background: transparent; }}
QWidget#reviewRow {{ background: transparent; border-top: 1px solid #EEF2F7; }}
QPushButton#reviewName {{ color: {PRIMARY}; font-weight: 700; background: transparent; border: 0; min-width: 70px; text-align: left; padding: 0; }}
QLabel#reviewDate, QLabel#reviewStatus {{ color: {TEXT_SECONDARY}; }}
QLabel#progressCount {{ color: #344258; font-size: 13px; font-weight: 600; }}
QLabel#resultIcon {{ color: #237A57; background: #EAF7F0; border-radius: 16px; min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; font-size: 17px; font-weight: 700; qproperty-alignment: AlignCenter; }}
QLabel#resultSuccess {{ color: #315F4D; background: #F0F8F4; border-radius: 6px; padding: 7px 10px; font-size: 13px; font-weight: 600; }}
QLabel#resultFailure {{ color: #A34A4A; background: #FFF4F4; border-radius: 6px; padding: 7px 10px; font-size: 13px; font-weight: 600; }}
QLabel#resultFailure[empty="true"] {{ color: {TEXT_SECONDARY}; background: #F3F5F8; font-weight: 500; }}
QWidget#outputSummary {{ background: #F8FAFC; border: 1px solid #E8EDF3; border-radius: {RADIUS_MD}px; }}
QLabel#outputCaption {{ color: {TEXT_SECONDARY}; font-size: 11px; background: transparent; }}
QLabel#outputName {{ color: #344258; font-size: 14px; font-weight: 600; background: transparent; }}
QLabel#outputPath {{ color: {TEXT_DISABLED}; font-size: 11px; background: transparent; }}
QPlainTextEdit#failureDetails {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; padding: 8px; }}
QTableWidget#previewTable {{ background: {SURFACE}; alternate-background-color: #F8FAFC; border: 1px solid {BORDER}; border-radius: {RADIUS_MD}px; gridline-color: #EEF2F7; outline: 0; }}
QTableWidget#previewTable::item {{ padding: 7px; }}
QTableWidget#previewTable::item:selected {{ background: #E8F0FF; color: #1F57BD; }}
QHeaderView::section {{ background: #F8FAFC; color: #526175; border: 0; border-bottom: 1px solid {BORDER}; padding: 9px 7px; font-weight: 600; }}
QLabel#statusText {{ color: #536175; font-size: 12px; }}
QLabel#fieldError {{ color: {DANGER}; font-size: 12px; }}
QLabel#warningText {{ color: {WARNING}; font-size: 12px; }}
QProgressBar {{ background: #E5EAF1; border: 0; border-radius: 4px; min-height: 8px; max-height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 4px; }}
QProgressBar#monitorProgressBar {{ min-height: 26px; max-height: 26px; border-radius: 6px; }}
QProgressBar#monitorProgressBar::chunk {{ background: #93C5FD; border-radius: 6px; }}
QLabel#monitorProgressText {{ color: #16345F; font-weight: 700; background: transparent; }}
QFrame#monitorHero {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0B1A33, stop:1 #153B6C); border: 1px solid #244B7E; border-radius: 16px; }}
QLabel#monitorEyebrow {{ color: #80B8EC; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#monitorPageTitle {{ color: #F7FAFC; font-size: 26px; font-weight: 700; }}
QLabel#monitorPageSubtitle {{ color: #B8C9DC; font-size: 13px; }}
QLabel#monitorLive {{ color: #D5E4F5; background: #173D6C; border: 1px solid #315B90; border-radius: 8px; padding: 5px 9px; font-size: 12px; font-weight: 600; }}
QLabel#monitorHeroHint {{ color: #9EB4CC; font-size: 11px; }}
QTabWidget#monitorTabs::pane {{ background: transparent; border: 0; top: -1px; }}
QTabWidget#monitorTabs QTabBar {{ background: #E9EFF6; border: 1px solid #D9E2ED; border-radius: 10px; padding: 3px; }}
QTabWidget#monitorTabs QTabBar::tab {{ background: transparent; color: #5C6E84; border: 0; min-height: 38px; padding: 0 24px; margin: 0; border-radius: 7px; }}
QTabWidget#monitorTabs QTabBar::tab:hover {{ background: #F5F8FC; color: #173E70; }}
QTabWidget#monitorTabs QTabBar::tab:selected {{ background: #FFFFFF; color: #153B6C; font-weight: 700; border: 1px solid #D5DFEC; }}
QFrame#monitorCard, QFrame#batchBar, QFrame#monitorToolbar {{ background: {SURFACE}; border: 1px solid #DDE5EE; border-radius: 12px; }}
QFrame#monitorToolbar {{ background: #FBFCFE; }}
QFrame#batchBar {{ background: #EAF3FF; border-color: #BFD7FB; }}
QLineEdit#monitorSearch {{ background: #F9FBFF; border-color: #C9DCF7; border-radius: 10px; min-height: 40px; }}
QLineEdit#monitorSearch:focus {{ background: #FFFFFF; border: 2px solid #5C99FF; }}
QCheckBox#filterChip {{ color: #385474; background: #FFFFFF; border: 1px solid #CADAF1; border-radius: 10px; padding: 0 10px; min-height: 38px; spacing: 7px; font-weight: 600; }}
QCheckBox#filterChip:hover {{ background: #F1F6FF; border-color: #8FB9F8; }}
QCheckBox#filterChip:checked {{ color: #1556CC; background: #E7F0FF; border-color: #80AEF8; }}
QCheckBox#filterChip::indicator {{ width: 14px; height: 14px; border-radius: 4px; }}
QPushButton#monitorPrimary {{ color: white; background: #174A88; border: 1px solid #174A88; border-radius: 8px; min-height: 40px; padding: 0 15px; font-weight: 700; }}
QPushButton#monitorPrimary:hover {{ background: #103966; border-color: #103966; }}
QPushButton#monitorCollect {{ color: #174A88; background: #FFFFFF; border: 1px solid #B7C9DE; border-radius: 8px; min-height: 40px; padding: 0 14px; font-weight: 700; }}
QPushButton#monitorCollect:hover {{ background: #F1F6FC; border-color: #7897B9; }}
QPushButton#monitorQuiet {{ color: #52667E; background: transparent; border: 1px solid transparent; border-radius: 8px; min-height: 40px; padding: 0 9px; }}
QPushButton#monitorQuiet:hover {{ color: #173E70; background: #EFF4FA; border-color: #D9E4F0; }}
QLabel#productTitle {{ color: #10264A; font-size: 13px; font-weight: 800; line-height: 1.3; }}
QLabel#productMeta {{ color: #7186A4; font-size: 12px; }}
QLabel#monitorMeta {{ color: {TEXT_SECONDARY}; }}
QFrame#statCard {{ background: #FFFFFF; border: 1px solid #DDE5EE; border-radius: 12px; min-height: 76px; }}
QFrame#statCard[tone="primary"] {{ background: #102D55; border-color: #102D55; }}
QFrame#statCard[tone="primary"] QLabel#statLabel {{ color: #B5C9E0; }}
QFrame#statCard[tone="primary"] QLabel#statValue {{ color: #FFFFFF; }}
QFrame#statCard[tone="cyan"] QLabel#statValue, QFrame#statCard[tone="violet"] QLabel#statValue, QFrame#statCard[tone="orange"] QLabel#statValue, QFrame#statCard[tone="rose"] QLabel#statValue {{ color: #183B66; }}
QTableWidget#monitorTable {{ background: #FFFFFF; alternate-background-color: #F7FAFF; border: 1px solid #D6E4F7; border-radius: 16px; gridline-color: transparent; outline: 0; }}
QTableWidget#monitorTable::item {{ color: #20385C; padding: 9px 8px; border-bottom: 1px solid #EDF3FC; }}
QTableWidget#monitorTable::item:hover {{ background: #F1F7FF; }}
QTableWidget#monitorTable::item:selected {{ background: #E3F0FF; color: #124FAE; }}
QTableWidget#monitorTable QHeaderView::section {{ background: #F1F6FF; color: #426080; border: 0; border-bottom: 1px solid #CEDDF3; padding: 11px 8px; font-weight: 800; }}
QDateEdit#monitorDate, QLineEdit#monitorTime {{ background: #FFFFFF; border: 1px solid #C6D9F3; border-radius: 9px; min-height: 38px; padding: 0 10px; color: #1C3B66; font-weight: 600; }}
QDateEdit#monitorDate:hover, QLineEdit#monitorTime:hover {{ border-color: #76A8F4; background: #F8FBFF; }}
QDateEdit#monitorDate:focus, QLineEdit#monitorTime:focus {{ border: 2px solid #5E98F8; }}
QDateEdit#monitorDate::drop-down {{ width: 28px; border: 0; border-left: 1px solid #D6E4F7; background: #F1F6FF; border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
QLineEdit#monitorNumber {{ background: #FFFFFF; border: 1px solid #C6D9F3; border-radius: 9px; min-height: 38px; padding: 0 10px; color: #1C3B66; font-weight: 600; }}
QLineEdit#monitorNumber:hover {{ border-color: #76A8F4; background: #F8FBFF; }}
QLineEdit#monitorNumber:focus {{ border: 2px solid #5E98F8; }}
QLabel#statusTag {{ color: #176B45; background: #EAF7F0; border: 1px solid #C9ECDD; border-radius: 11px; padding: 3px 8px; margin: 18px 6px; font-size: 12px; font-weight: 700; }}
QLabel#statusTag[status="暂停"] {{ color: #6B7280; background: #EEF1F4; }}
QLabel#statusTag[status="异常"], QLabel#statusTag[status="采集失败"] {{ color: #B42318; background: #FEF0F0; }}
QLabel#statusTag[status="采集中"] {{ color: #1F57BD; background: #E8F0FF; }}
QLabel#trendPlaceholder {{ color: {TEXT_DISABLED}; background: #F8FAFC; border: 1px dashed #D8E0EA; border-radius: 7px; padding: 14px; qproperty-alignment: AlignCenter; }}
QLabel#monitorEmpty {{ color: {TEXT_SECONDARY}; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: {RADIUS_LG}px; padding: 32px; }}
QPushButton#segmentButton {{ min-width: 64px; border-radius: 0; margin-right: -1px; }}
QPushButton#segmentButton:hover {{ background: #F1F5F9; }}
QPushButton#segmentButton:checked {{ color: #1F57BD; background: #E8F0FF; border-color: #B8CCF2; }}
QToolButton#rowMenu {{ color: #60718A; background: transparent; border: 0; border-radius: 8px; min-width: 36px; min-height: 36px; font-size: 18px; font-weight: 700; }}
QToolButton#rowMenu:hover {{ color: #1859C9; background: #EAF2FF; }}
QMenu {{ background: {SURFACE}; border: 1px solid #D6E2F1; border-radius: 10px; padding: 6px; }}
QMenu::item {{ min-width: 140px; padding: 9px 18px; border-radius: 7px; }}
QMenu::item:selected {{ background: #E8F1FF; color: #1859C9; }}
QSplitter#workspaceSplitter::handle {{ background: transparent; width: 14px; }}
QScrollArea {{ border: 0; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #CBD5E1; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* Phase 1: Personal Toolbox app shell and dashboard */
QMainWindow, QWidget#appRoot, QWidget#mainArea, QWidget#dashboardPage, QScrollArea#dashboardScroll, QWidget#dashboardContent {{ background: {APP_BACKGROUND}; }}
QWidget#sidebar {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}
QLabel#brand {{ color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 700; }}
QLabel#brandHint {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
QLabel#privacy {{ color: #97A3B5; font-size: 11px; padding: 12px 8px 0; }}
QListWidget#navigation {{ background: transparent; color: {TEXT_SECONDARY}; border: 0; outline: 0; padding: 0 4px; }}
QListWidget#navigation::item {{ min-height: 40px; padding: 0 10px; border-radius: 10px; margin: 2px 0; }}
QListWidget#navigation::item:hover {{ background: #F1F5FB; color: {TEXT_PRIMARY}; }}
QListWidget#navigation::item:selected {{ background: #EAF1FF; color: {PRIMARY}; font-weight: 600; }}
QWidget#titleBar {{ background: {APP_BACKGROUND}; border-bottom: 1px solid {BORDER}; }}
QFrame#globalSearchShell {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; min-height: 42px; max-width: 580px; }}
QFrame#globalSearchShell:focus-within {{ border: 1px solid {PRIMARY}; }}
QLineEdit#globalSearch {{ background: transparent; border: 0; min-height: 40px; padding: 0; color: {TEXT_PRIMARY}; }}
QLineEdit#globalSearch:focus {{ background: transparent; border: 0; }}
QPushButton#headerBackButton {{ min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px; padding: 0; border-radius: 10px; background: transparent; border: 1px solid transparent; }}
QPushButton#headerBackButton:hover {{ background: #EEF3FA; border-color: #DCE5F2; }}
QLabel#headerTitle {{ color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 700; }}
QLabel#headerDescription {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
QPushButton#windowButton, QPushButton#closeButton {{ min-width: 42px; max-width: 42px; min-height: 64px; max-height: 64px; }}
QLabel#dashboardTitle {{ color: {TEXT_PRIMARY}; font-size: 28px; font-weight: 700; }}
QLabel#dashboardSubtitle {{ color: {TEXT_SECONDARY}; font-size: 13px; }}
QLabel#toolCount {{ color: #526175; background: #EEF3F8; border-radius: 10px; padding: 6px 10px; font-size: 12px; font-weight: 600; }}
QLabel#dashboardEmpty {{ color: {TEXT_SECONDARY}; background: {SURFACE}; border: 1px dashed #CCD6E4; border-radius: 16px; padding: 42px; }}
QToolButton#toolCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 18px; text-align: left; padding: 0; }}
QToolButton#toolCard:hover {{ background: #FCFDFF; border-color: #B7C9E6; }}
QToolButton#toolCard:focus {{ border: 2px solid {PRIMARY}; }}
QLabel#toolCardIcon {{ background: #EAF1FF; border-radius: 9px; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; qproperty-alignment: AlignCenter; }}
QLabel#toolCardCategory {{ color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 600; }}
QLabel#toolCardArrow {{ color: #97A3B5; font-size: 15px; }}
QLabel#toolCardTitle {{ color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent; }}
QLabel#toolCardDescription {{ color: {TEXT_SECONDARY}; font-size: 12px; background: transparent; }}
QFrame#toolPreview {{ background: #F6F8FC; border: 1px solid #EEF1F5; border-radius: 10px; }}
QLabel#toolPreviewValue {{ color: #40516A; font-size: 11px; font-weight: 600; background: transparent; }}
QLabel#toolPreviewArrow {{ color: {PRIMARY}; font-size: 14px; font-weight: 700; background: transparent; }}
QFrame#floatingDock {{ background: {SURFACE}; border: 1px solid #DFE6EF; border-radius: 20px; }}
QToolButton#dockButton {{ color: #5A687C; background: transparent; border: 1px solid transparent; border-radius: 12px; min-width: 72px; min-height: 52px; padding: 3px 6px; font-size: 10px; }}
QToolButton#dockButton:hover {{ color: {PRIMARY}; background: #EEF4FF; border-color: #E0EAFA; }}
QToolButton#dockButton:focus {{ border-color: {PRIMARY}; }}

/* Phase 1.5: compact bento refinement */
QWidget#sidebar {{ border-right: 1px solid #EEF1F4; }}
QLabel#brand {{ font-size: 14px; font-weight: 700; }}
QLabel#brandHint {{ color: #97A3B5; font-size: 10px; }}
QLabel#privacy {{ color: #A4AFBF; font-size: 10px; padding: 10px 8px 0; }}
QListWidget#navigation {{ padding: 0 3px; }}
QListWidget#navigation::item {{ min-height: 38px; padding: 0 9px; margin: 1px 0; border-radius: 10px; }}
QListWidget#navigation::item:hover {{ background: #F5F7FB; }}
QListWidget#navigation::item:selected {{ background: #EAF1FF; color: #2563EB; }}
QWidget#titleBar {{ min-height: 56px; max-height: 56px; }}
QFrame#globalSearchShell {{ min-height: 44px; max-width: 540px; border-color: #E5EAF1; }}
QLineEdit#globalSearch {{ min-height: 42px; color: #526175; font-size: 12px; }}
QLineEdit#globalSearch::placeholder {{ color: #A0AABD; }}
QPushButton#windowButton, QPushButton#closeButton {{ min-height: 56px; max-height: 56px; }}
QLabel#dashboardTitle {{ font-size: 25px; }}
QLabel#dashboardSubtitle {{ font-size: 12px; }}
QLabel#toolCount {{ color: #9AA6B8; background: transparent; border-radius: 0; padding: 0; font-size: 11px; font-weight: 500; }}
QToolButton#toolCard {{ border-radius: 17px; }}
QToolButton#toolCard:hover {{ background: #FFFFFF; border-color: #C9D8F0; }}
QToolButton#toolCard:focus {{ border: 2px solid #2563EB; }}
QLabel#toolCardIcon {{ border-radius: 11px; min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px; }}
QLabel#toolCardCategory {{ color: #97A3B5; font-size: 10px; font-weight: 500; }}
QLabel#toolCardArrow {{ color: #B0BAC8; font-size: 13px; }}
QLabel#toolCardTitle {{ font-size: 15px; font-weight: 700; }}
QLabel#toolCardDescription {{ color: #7F8DA3; font-size: 11px; }}
QFrame#toolPreview {{ background: #F7F9FC; border: 1px solid #EEF2F6; border-radius: 11px; }}
QFrame#previewPhoto {{ background: #DCEAFF; border-radius: 7px; min-width: 64px; }}
QLabel#previewWatermark {{ color: #3264B7; background: #FFFFFF; border: 1px solid #C6D9FA; border-radius: 4px; padding: 2px 5px; font-size: 10px; font-weight: 700; qproperty-alignment: AlignCenter; }}
QLabel#previewCaption {{ color: #71809C; background: transparent; font-size: 10px; }}
QLabel#previewMetric {{ color: #334155; background: transparent; font-size: 11px; font-weight: 700; }}
QLabel#previewDimension {{ color: #3A4B63; background: #FFFFFF; border: 1px solid #E1E8F0; border-radius: 6px; padding: 4px 5px; font-size: 10px; font-weight: 600; }}
QLabel#previewArrow {{ color: #6E8FC9; background: transparent; font-size: 13px; font-weight: 700; }}
QFrame#previewWhiteTile {{ background: #FFFFFF; border: 1px solid #DCE3EC; border-radius: 5px; }}
QWidget#previewChecker {{ border: 1px solid #DCE3EC; border-radius: 5px; }}
QFrame#previewCheckerLight {{ background: #FFFFFF; }}
QFrame#previewCheckerDark {{ background: #DCE6F0; }}
QFrame#previewProgressTrack {{ background: #E3EAF3; border-radius: 4px; min-height: 7px; max-height: 7px; }}
QFrame#previewProgressFill {{ background: #7CA6F8; border-radius: 4px; min-height: 7px; max-height: 7px; }}
QLabel#previewFormat {{ color: #4267AF; background: #EAF1FF; border-radius: 5px; padding: 4px 8px; font-size: 10px; font-weight: 700; }}
QLabel#previewFilename {{ color: #526175; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 5px; padding: 4px; font-size: 10px; }}
QFrame#previewDateTile {{ background: #FFFFFF; border: 1px solid #DDE7F5; border-radius: 6px; min-width: 32px; max-width: 32px; }}
QLabel#previewDateMonth {{ color: #6B8BC4; font-size: 7px; font-weight: 700; }}
QLabel#previewDateDay {{ color: #2E4A74; font-size: 13px; font-weight: 700; }}
QLabel#previewBadge {{ color: #34835F; background: #EAF8F2; border-radius: 6px; padding: 4px 7px; font-size: 10px; font-weight: 600; }}
QWidget#previewTrend {{ min-width: 36px; }}
QFrame#previewTrendBar {{ background: #77A1ED; border-radius: 3px; }}
QFrame#floatingDock {{ border-color: #E7EBF0; border-radius: 19px; }}
QToolButton#dockButton {{ min-width: 61px; min-height: 46px; padding: 2px 4px; font-size: 9px; color: #6B788B; }}
QToolButton#dockButton:hover {{ color: #2563EB; background: #F1F5FF; border-color: #E3EBFA; }}
"""
