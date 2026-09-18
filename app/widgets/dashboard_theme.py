DASHBOARD_STYLE = r"""
QWidget#appRoot { background: transparent; }
QWidget#mainArea { background: transparent; }
QStackedWidget#mainStack { background: transparent; border: 0; }
QWidget#dashboardPage, QScrollArea#dashboardScroll, QScrollArea#dashboardScroll > QWidget > QWidget,
QWidget#dashboardContent, QWidget#dashboardGridHost { background: transparent; border: 0; }
QWidget#sidebar { background: rgba(255,255,255,174); border: 0; border-right: 1px solid rgba(224,232,244,145); }
QWidget#brandBox { background: transparent; }
QLabel#brand { color: #182033; font-size: 15px; font-weight: 700; }
QLabel#brandHint { color: #9AA6B8; font-size: 10px; font-weight: 500; }
QListWidget#navigation { background: transparent; color: #71809C; border: 0; outline: 0; padding: 0 2px; font-size: 13px; }
QListWidget#navigation::item { min-height: 39px; padding: 0 10px; margin: 2px 0; border-radius: 12px; }
QListWidget#navigation::item:hover { background: rgba(242,246,252,165); color: #334155; }
QListWidget#navigation::item:selected { background: rgba(231,239,253,205); color: #2C66DA; font-weight: 600; }
QWidget#sidebarSection { background: transparent; }
QLabel#sidebarSectionLabel { color: #A1ADBE; font-size: 10px; font-weight: 600; }
QLabel#sidebarSectionCount { color: #BBC4D1; font-size: 9px; }
QLabel#sidebarVersion { color: #B5BFCD; font-size: 9px; padding-top: 8px; }
QWidget#titleBar { background: transparent; border: 0; min-height: 78px; max-height: 78px; }
QFrame#globalSearchShell { background: rgba(255,255,255,222); border: 1px solid rgba(255,255,255,245); border-radius: 25px; min-height: 50px; max-height: 50px; min-width: 420px; max-width: 700px; }
QLineEdit#globalSearch { background: transparent; border: 0; min-height: 46px; padding: 0; color: #26334A; font-size: 13px; selection-background-color: #DDE9FF; selection-color: #204FAD; }
QLineEdit#globalSearch:hover, QLineEdit#globalSearch:focus { background: transparent; border: 0; }
QPushButton#headerAction { min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 0; border-radius: 18px; background: rgba(255,255,255,150); border: 1px solid rgba(255,255,255,205); }
QPushButton#headerAction:hover { background: rgba(255,255,255,220); border-color: rgba(203,215,233,190); }
QPushButton#headerAction:disabled { background: rgba(255,255,255,112); border-color: rgba(255,255,255,165); }
QPushButton#profileAction { min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 0; border-radius: 18px; background: rgba(225,234,248,190); border: 1px solid rgba(255,255,255,210); }
QPushButton#headerBackButton { min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; border-radius: 12px; background: rgba(255,255,255,165); border: 1px solid rgba(220,228,240,145); }
QPushButton#headerBackButton:hover { background: rgba(255,255,255,220); border-color: #C9D7EA; }
QLabel#headerTitle { color: #182033; font-size: 14px; font-weight: 700; }
QLabel#headerDescription { color: #71809C; font-size: 10px; }
QPushButton#windowButton, QPushButton#closeButton { min-width: 42px; max-width: 42px; min-height: 50px; max-height: 50px; background: transparent; border: 0; }
QPushButton#windowButton:hover { background: rgba(236,241,248,155); }
QLabel#dashboardTitle { color: #182033; font-size: 33px; font-weight: 800; }
QLabel#dashboardSubtitle { color: #66758D; font-size: 13px; }
QLabel#toolCount { color: #A0ACBD; background: transparent; font-size: 10px; }
QPushButton#filterChip { min-height: 33px; padding: 0 15px; border-radius: 16px; border: 1px solid rgba(211,221,235,170); background: rgba(255,255,255,145); color: #758398; font-size: 10px; font-weight: 600; }
QPushButton#filterChip:hover { background: rgba(255,255,255,205); border-color: #C7D5E8; color: #40516A; }
QPushButton#filterChip:checked { background: #356CF0; border-color: #356CF0; color: white; }
QLabel#dashboardEmpty { color: #71809C; background: rgba(255,255,255,150); border: 1px dashed rgba(190,204,222,185); border-radius: 18px; padding: 42px; }
QToolButton#toolCard { background: rgba(255,255,255,216); border: 1px solid rgba(255,255,255,238); border-radius: 19px; text-align: left; padding: 0; }
QToolButton#toolCard:hover { background: rgba(255,255,255,232); border-color: rgba(196,211,232,205); }
QToolButton#toolCard:focus { border: 1px solid #7EA5F6; }
QLabel#toolCardCategory { color: #8E9BB0; font-size: 11px; font-weight: 600; background: transparent; }
QLabel#featuredBadge { color: #3568F4; background: rgba(231,239,255,220); border-radius: 7px; padding: 2px 6px; font-size: 8px; font-weight: 700; }
QLabel#toolCardArrow { color: #A7B1C0; font-size: 14px; background: transparent; }
QLabel#toolCardTitle { color: #182033; font-size: 16px; font-weight: 700; background: transparent; }
QLabel#toolCardDescription { color: #66758D; font-size: 11px; background: transparent; }
QWidget#toolPreviewCanvas { background: transparent; }
QFrame#floatingDock { background: rgba(255,255,255,178); border: 1px solid rgba(255,255,255,220); border-radius: 22px; min-height: 54px; max-height: 54px; }
QToolButton#dockButton { background: rgba(247,249,253,145); border: 1px solid rgba(226,232,241,125); border-radius: 11px; padding: 0; }
QToolButton#dockButton:hover { background: rgba(237,243,252,230); border-color: #CAD8EA; }
QToolButton#dockButton[active="true"] { background: rgba(66,118,232,220); border: 1px solid rgba(71,111,210,190); }
QScrollArea#dashboardScroll QScrollBar:vertical { background: transparent; width: 6px; margin: 0; }
QScrollArea#dashboardScroll QScrollBar::handle:vertical { background: rgba(154,166,186,120); border-radius: 3px; min-height: 34px; }
QScrollArea#dashboardScroll QScrollBar::handle:vertical:hover { background: rgba(126,141,164,165); }
QScrollArea#dashboardScroll QScrollBar::add-line:vertical, QScrollArea#dashboardScroll QScrollBar::sub-line:vertical { height: 0; }
QScrollArea#dashboardScroll QScrollBar::add-page:vertical, QScrollArea#dashboardScroll QScrollBar::sub-page:vertical { background: transparent; }
"""
