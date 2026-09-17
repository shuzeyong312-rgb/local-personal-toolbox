DASHBOARD_STYLE = r"""
QWidget#appRoot { background: transparent; }
QWidget#mainArea { background: transparent; }
QStackedWidget#mainStack { background: transparent; border: 0; }
QWidget#dashboardPage, QScrollArea#dashboardScroll, QScrollArea#dashboardScroll > QWidget > QWidget,
QWidget#dashboardContent, QWidget#dashboardGridHost { background: transparent; border: 0; }
QWidget#sidebar { background: rgba(255,255,255,166); border: 0; border-right: 1px solid rgba(220,229,242,155); }
QWidget#brandBox { background: transparent; }
QLabel#brand { color: #182033; font-size: 14px; font-weight: 700; }
QLabel#brandHint { color: #8C99AD; font-size: 10px; font-weight: 500; }
QListWidget#navigation { background: transparent; color: #71809C; border: 0; outline: 0; padding: 0 2px; }
QListWidget#navigation::item { min-height: 39px; padding: 0 10px; margin: 2px 0; border-radius: 12px; }
QListWidget#navigation::item:hover { background: rgba(239,244,252,190); color: #26334A; }
QListWidget#navigation::item:selected { background: rgba(229,239,255,225); color: #2765E8; font-weight: 600; }
QWidget#sidebarSection { background: transparent; }
QLabel#sidebarSectionLabel { color: #98A5B8; font-size: 10px; font-weight: 600; }
QLabel#sidebarSectionCount { color: #B2BDCC; font-size: 10px; }
QFrame#privacyCard { background: rgba(255,255,255,158); border: 1px solid rgba(218,228,242,178); border-radius: 14px; }
QLabel#privacyIcon { color: #2F72E8; background: rgba(230,239,255,220); border-radius: 9px; min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; font-size: 12px; }
QLabel#privacyTitle { color: #3B4960; font-size: 11px; font-weight: 600; }
QLabel#privacyHint { color: #99A5B7; font-size: 9px; }
QLabel#privacyArrow { color: #9AA8BA; font-size: 13px; }
QLabel#sidebarVersion { color: #B5BFCD; font-size: 9px; padding-top: 8px; }
QWidget#titleBar { background: transparent; border: 0; min-height: 78px; max-height: 78px; }
QFrame#globalSearchShell { background: rgba(255,255,255,198); border: 1px solid rgba(255,255,255,228); border-radius: 25px; min-height: 50px; max-height: 50px; min-width: 500px; max-width: 700px; }
QLineEdit#globalSearch { background: transparent; border: 0; min-height: 46px; padding: 0; color: #26334A; font-size: 12px; selection-background-color: #DDE9FF; selection-color: #204FAD; }
QLineEdit#globalSearch:hover, QLineEdit#globalSearch:focus { background: transparent; border: 0; }
QLabel#searchShortcutBadge { color: #8794A8; background: rgba(244,247,252,210); border: 1px solid rgba(220,227,238,180); border-radius: 8px; padding: 4px 7px; font-size: 9px; font-weight: 600; }
QPushButton#headerBackButton { min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; padding: 0; border-radius: 12px; background: rgba(255,255,255,165); border: 1px solid rgba(220,228,240,145); }
QPushButton#headerBackButton:hover { background: rgba(255,255,255,220); border-color: #C9D7EA; }
QLabel#headerTitle { color: #182033; font-size: 14px; font-weight: 700; }
QLabel#headerDescription { color: #71809C; font-size: 10px; }
QPushButton#windowButton, QPushButton#closeButton { min-width: 42px; max-width: 42px; min-height: 50px; max-height: 50px; background: transparent; border: 0; }
QPushButton#windowButton:hover { background: rgba(236,241,248,155); }
QLabel#dashboardTitle { color: #182033; font-size: 31px; font-weight: 700; }
QLabel#dashboardSubtitle { color: #71809C; font-size: 12px; }
QLabel#toolCount { color: #A0ACBD; background: transparent; font-size: 10px; }
QPushButton#filterChip { min-height: 31px; padding: 0 12px; border-radius: 15px; border: 1px solid rgba(211,221,235,170); background: rgba(255,255,255,126); color: #7B899E; font-size: 10px; font-weight: 600; }
QPushButton#filterChip:hover { background: rgba(255,255,255,205); border-color: #C7D5E8; color: #40516A; }
QPushButton#filterChip:checked { background: #356CF0; border-color: #356CF0; color: white; }
QLabel#dashboardEmpty { color: #71809C; background: rgba(255,255,255,150); border: 1px dashed rgba(190,204,222,185); border-radius: 18px; padding: 42px; }
QToolButton#toolCard { background: rgba(255,255,255,188); border: 1px solid rgba(255,255,255,220); border-radius: 19px; text-align: left; padding: 0; }
QToolButton#toolCard:hover { background: rgba(255,255,255,225); border-color: rgba(189,207,233,190); }
QToolButton#toolCard:focus { border: 1px solid #7EA5F6; }
QLabel#toolCardCategory { color: #9AA6BA; font-size: 10px; font-weight: 600; background: transparent; }
QLabel#featuredBadge { color: #3568F4; background: rgba(231,239,255,220); border-radius: 7px; padding: 2px 6px; font-size: 8px; font-weight: 700; }
QLabel#toolCardArrow { color: #A7B1C0; font-size: 14px; background: transparent; }
QLabel#toolCardTitle { color: #182033; font-size: 15px; font-weight: 700; background: transparent; }
QLabel#toolCardDescription { color: #7B899E; font-size: 10px; background: transparent; }
QWidget#toolPreviewCanvas { background: transparent; }
QFrame#floatingDock { background: rgba(255,255,255,202); border: 1px solid rgba(255,255,255,228); border-radius: 25px; min-height: 62px; max-height: 62px; }
QToolButton#dockButton { background: rgba(245,248,252,172); border: 1px solid rgba(224,231,241,150); border-radius: 12px; padding: 0; }
QToolButton#dockButton:hover { background: rgba(237,243,252,230); border-color: #CAD8EA; }
QToolButton#dockButton[active="true"] { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #3479F6,stop:1 #3157D9); border: 1px solid #3968DF; }
QScrollArea#dashboardScroll QScrollBar:vertical { background: transparent; width: 6px; margin: 0; }
QScrollArea#dashboardScroll QScrollBar::handle:vertical { background: rgba(154,166,186,120); border-radius: 3px; min-height: 34px; }
QScrollArea#dashboardScroll QScrollBar::handle:vertical:hover { background: rgba(126,141,164,165); }
QScrollArea#dashboardScroll QScrollBar::add-line:vertical, QScrollArea#dashboardScroll QScrollBar::sub-line:vertical { height: 0; }
QScrollArea#dashboardScroll QScrollBar::add-page:vertical, QScrollArea#dashboardScroll QScrollBar::sub-page:vertical { background: transparent; }
"""
