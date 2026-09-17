DASHBOARD_BG = "#F7F9FD"
TEXT_PRIMARY = "#182033"
TEXT_SECONDARY = "#71809C"
TEXT_MUTED = "#9AA6BA"
PRIMARY = "#3478F6"
PRIMARY_HOVER = "#2A67DB"
BORDER = "rgba(215, 225, 240, 145)"
GLASS = "rgba(255, 255, 255, 205)"
GLASS_SOFT = "rgba(255, 255, 255, 178)"

DASHBOARD_STYLE = f"""
QWidget#dashboardPage, QWidget#dashboardCanvas, QWidget#dashboardContent {{
    background: transparent;
}}
QScrollArea#dashboardScroll {{
    background: transparent;
    border: 0;
}}
QScrollArea#dashboardScroll > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
    margin: 2px 0 2px 0;
}}
QScrollBar::handle:vertical {{
    min-height: 30px;
    background: rgba(142, 158, 184, 92);
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(116, 134, 164, 125);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    width: 0;
    height: 0;
    background: transparent;
}}
QWidget#searchSurface {{
    background: {GLASS};
    border: 1px solid rgba(255, 255, 255, 220);
    border-radius: 25px;
}}
QLineEdit#dashboardSearch {{
    min-height: 48px;
    max-height: 48px;
    background: transparent;
    border: 0;
    padding: 0 4px;
    color: {TEXT_PRIMARY};
    font-size: 14px;
    selection-background-color: {PRIMARY};
}}
QLabel#shortcutBadge {{
    color: #66758F;
    background: rgba(244, 247, 252, 220);
    border: 1px solid rgba(210, 220, 236, 180);
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
}}
QLabel#dashboardTitle {{
    color: {TEXT_PRIMARY};
    font-size: 31px;
    font-weight: 700;
}}
QLabel#dashboardSubtitle {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}
QLabel#toolCount {{
    color: {TEXT_MUTED};
    font-size: 11px;
}}
QPushButton#filterChip {{
    min-height: 34px;
    max-height: 34px;
    padding: 0 14px;
    color: #66758F;
    background: rgba(255, 255, 255, 145);
    border: 1px solid rgba(210, 220, 236, 150);
    border-radius: 17px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#filterChip:hover {{
    background: rgba(255, 255, 255, 210);
    border-color: rgba(177, 193, 218, 180);
}}
QPushButton#filterChip:checked {{
    color: white;
    background: {PRIMARY};
    border-color: {PRIMARY};
}}
QFrame#toolCard {{
    background: rgba(255, 255, 255, 205);
    border: 1px solid rgba(216, 226, 241, 150);
    border-radius: 18px;
}}
QFrame#toolCard[hovered="true"] {{
    background: rgba(255, 255, 255, 228);
    border: 1px solid rgba(174, 194, 226, 190);
}}
QLabel#toolCardTitle {{
    color: {TEXT_PRIMARY};
    font-size: 16px;
    font-weight: 700;
}}
QLabel#toolCardCategory {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#toolCardDescription {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}
QLabel#emptySearch {{
    color: {TEXT_SECONDARY};
    background: rgba(255, 255, 255, 150);
    border: 1px solid rgba(216, 226, 241, 130);
    border-radius: 16px;
    padding: 22px;
    font-size: 13px;
}}
QWidget#dockSurface {{
    background: rgba(255, 255, 255, 212);
    border: 1px solid rgba(255, 255, 255, 232);
    border-radius: 24px;
}}
QPushButton#dockItem {{
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    padding: 0;
    background: rgba(244, 247, 252, 190);
    border: 1px solid rgba(216, 226, 241, 120);
    border-radius: 12px;
}}
QPushButton#dockItem:hover {{
    background: rgba(235, 241, 251, 230);
    border-color: rgba(177, 193, 218, 170);
}}
QPushButton#dockHome {{
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
    padding: 0;
    background: #3478F6;
    border: 1px solid #3478F6;
    border-radius: 12px;
}}
"""

SIDEBAR_STYLE = f"""
QWidget#toolboxSidebar {{
    background: rgba(247, 249, 253, 122);
    border-right: 1px solid rgba(218, 227, 239, 100);
}}
QLabel#sidebarBrand {{
    color: {TEXT_PRIMARY};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#sidebarBrandHint {{
    color: {TEXT_MUTED};
    font-size: 10px;
}}
QLabel#sidebarSection {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#sidebarCount {{
    color: #A8B3C5;
    font-size: 10px;
}}
QPushButton#sidebarItem {{
    min-height: 40px;
    max-height: 40px;
    padding: 0 12px;
    text-align: left;
    color: #65738B;
    background: transparent;
    border: 0;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#sidebarItem:hover {{
    color: #365A92;
    background: rgba(232, 240, 252, 160);
}}
QPushButton#sidebarItem:checked {{
    color: {PRIMARY};
    background: rgba(225, 237, 255, 220);
    font-weight: 700;
}}
QWidget#privacyCard {{
    background: rgba(255, 255, 255, 154);
    border: 1px solid rgba(218, 227, 239, 130);
    border-radius: 16px;
}}
QLabel#privacyTitle {{
    color: #44536B;
    font-size: 12px;
    font-weight: 700;
}}
QLabel#privacyHint {{
    color: {TEXT_MUTED};
    font-size: 10px;
}}
QLabel#versionLabel {{
    color: #A5B0C2;
    font-size: 9px;
}}
"""
