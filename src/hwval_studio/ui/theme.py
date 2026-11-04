"""Light theme tokens, SVG icons and the macOS-style stylesheet (SRS section 4)."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

# LNF-003 reference palette.
COLORS: dict[str, str] = {
    "window": "#FFFFFF",
    "bg": "#FFFFFF",
    "sidebar": "#F5F5F7",
    "sidebar_alt": "#EFEFF2",
    "separator": "#E5E5EA",
    "border": "#D2D2D7",
    "text": "#1D1D1F",
    "secondary": "#6E6E73",
    "muted": "#8E8E93",
    "accent": "#007AFF",
    "accent_dark": "#0062CC",
    "accent_soft": "#E5F0FF",
    "pass": "#34C759",
    "pass_soft": "#E9F9EE",
    "fail": "#FF3B30",
    "fail_soft": "#FFEBEA",
    "skip": "#FF9F0A",
    "skip_soft": "#FFF4E5",
    "na": "#8E8E93",
    "na_soft": "#F0F0F2",
    "warning": "#FF9F0A",
    "running": "#007AFF",
    "selected": "#DDEBFF",
    "surface": "#FFFFFF",
    "surface_alt": "#FAFAFC",
    "row_alt": "#FBFBFD",
    "shadow": "rgba(0,0,0,0.08)",
}

STATE_COLORS = {
    "PASS": COLORS["pass"],
    "FAIL": COLORS["fail"],
    "SKIP": COLORS["skip"],
    "N/A": COLORS["na"],
    "NA": COLORS["na"],
    "RUNNING": COLORS["running"],
    "NOT RUN": COLORS["muted"],
    "IDLE": COLORS["muted"],
    "WARN": COLORS["warning"],
    "ERROR": COLORS["fail"],
    "INFO": COLORS["accent"],
    "DEBUG": COLORS["muted"],
}

STATE_ICONS = {
    "PASS": "check",
    "FAIL": "x",
    "SKIP": "skip",
    "N/A": "na",
    "NA": "na",
    "RUNNING": "running",
    "NOT RUN": "dot",
    "IDLE": "dot",
    "WARN": "warning",
    "ERROR": "warning",
}

_RESOURCE_PACKAGE = "hwval_studio.resources"


@lru_cache(maxsize=256)
def icon(name: str, color: str | None = None, size: int = 24) -> QIcon:
    """Load a bundled SVG and tint it at run time (ICN-001/002)."""
    color = color or COLORS["text"]
    try:
        raw = resources.files(_RESOURCE_PACKAGE).joinpath("icons", f"{name}.svg").read_text()
    except (FileNotFoundError, ModuleNotFoundError):
        raw = (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<rect x="6" y="6" width="12" height="12" rx="2" fill="none" '
            f'stroke="{color}" stroke-width="1.8"/></svg>'
        )
    svg = raw.replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def state_icon(state: str, size: int = 18) -> QIcon:
    key = state.upper().replace("_", " ")
    return icon(STATE_ICONS.get(key, "dot"), STATE_COLORS.get(key, COLORS["muted"]), size)


def state_color(state: str) -> QColor:
    return QColor(STATE_COLORS.get(state.upper().replace("_", " "), COLORS["muted"]))


def apply_theme(app: QApplication) -> None:
    """Apply the explicit light palette and macOS-like stylesheet (LNF-002/004)."""
    c = COLORS
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(c["window"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(c["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(c["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(c["surface_alt"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["surface"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(c["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(c["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(c["text"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Link, QColor(c["accent"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(c["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(c["secondary"]))
    app.setStyle("Fusion")
    app.setPalette(palette)
    load_fonts(app)
    app.setStyleSheet(_stylesheet())


def load_fonts(app: QApplication) -> None:
    """Load bundled open-licence fonts when present (LNF-005)."""
    try:
        font_dir = resources.files(_RESOURCE_PACKAGE).joinpath("fonts")
        entries = list(font_dir.iterdir())
    except (FileNotFoundError, ModuleNotFoundError):
        return
    for entry in entries:
        if entry.name.lower().endswith((".ttf", ".otf")):
            data = entry.read_bytes()
            QFontDatabase.addApplicationFontFromData(QByteArray(data))
    # The system font is used on macOS; the bundled Inter/JetBrains Mono are
    # picked up by the stylesheet on Windows and Linux when installed.
    base = QFont()
    base.setPointSizeF(10.5)
    app.setFont(base)


def _stylesheet() -> str:
    c = COLORS
    return f"""
    * {{
        font-family: "Inter", -apple-system, "SF Pro Text", "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
        font-size: 13px;
        color: {c["text"]};
    }}
    QMainWindow, QWidget#Root, QWidget#Page {{ background: {c["window"]}; }}
    QWidget#Sidebar {{ background: {c["sidebar"]}; }}
    QFrame#Toolbar {{
        background: {c["surface"]};
        border-bottom: 1px solid {c["separator"]};
    }}
    QFrame#Card {{
        background: {c["surface"]};
        border: 1px solid {c["separator"]};
        border-radius: 10px;
    }}
    QFrame#SubtleCard {{
        background: {c["surface_alt"]};
        border: 1px solid {c["separator"]};
        border-radius: 10px;
    }}
    QFrame#Separator {{ background: {c["separator"]}; max-height: 1px; }}
    QLabel#Title {{ font-size: 20px; font-weight: 700; }}
    QLabel#PageTitle {{ font-size: 17px; font-weight: 700; }}
    QLabel#Heading {{ font-size: 14px; font-weight: 700; }}
    QLabel#SectionHeader {{
        color: {c["secondary"]};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.8px;
        padding: 12px 12px 4px 12px;
    }}
    QLabel#Secondary, QLabel#Muted {{ color: {c["secondary"]}; }}
    QLabel#Metric {{ font-size: 22px; font-weight: 700; }}
    QLabel#Mono {{ font-family: "JetBrains Mono", "SF Mono", "Consolas", "DejaVu Sans Mono", monospace; }}
    QLabel#Banner {{
        background: {c["accent_soft"]};
        border: 1px solid {c["accent"]}44;
        border-radius: 8px;
        padding: 8px 12px;
        color: {c["text"]};
    }}
    QPushButton {{
        background: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 5px 12px;
        min-height: 22px;
    }}
    QPushButton:hover {{ background: {c["surface_alt"]}; }}
    QPushButton:pressed {{ background: {c["sidebar_alt"]}; }}
    QPushButton:disabled {{ color: {c["muted"]}; background: {c["surface_alt"]}; }}
    QPushButton#Primary {{
        background: {c["accent"]};
        color: #FFFFFF;
        border: 1px solid {c["accent"]};
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{ background: {c["accent_dark"]}; }}
    QPushButton#Primary:disabled {{ background: #B9D8FF; border-color: #B9D8FF; color: #FFFFFF; }}
    QPushButton#Danger {{
        background: {c["fail"]};
        color: #FFFFFF;
        border: 1px solid {c["fail"]};
        font-weight: 600;
    }}
    QPushButton#Success {{
        background: {c["pass"]};
        color: #FFFFFF;
        border: 1px solid {c["pass"]};
        font-weight: 600;
    }}
    QPushButton#LargeAction {{
        background: {c["accent"]};
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 18px 32px;
        font-size: 20px;
        font-weight: 700;
    }}
    QPushButton#LargeAction:disabled {{ background: #B9D8FF; color: #FFFFFF; }}
    QPushButton#Flat {{
        background: transparent;
        border: none;
        padding: 4px 7px;
    }}
    QPushButton#Flat:hover {{ background: {c["sidebar_alt"]}; border-radius: 6px; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
        background: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 4px 8px;
        min-height: 22px;
        selection-background-color: {c["accent"]};
        selection-color: #FFFFFF;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {c["accent"]};
    }}
    QLineEdit#SearchField {{
        background: {c["surface_alt"]};
        border-radius: 12px;
        padding-left: 4px;
    }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox QAbstractItemView {{
        background: {c["surface"]};
        border: 1px solid {c["separator"]};
        selection-background-color: {c["accent"]};
        selection-color: #FFFFFF;
        outline: none;
    }}
    QCheckBox, QRadioButton {{ spacing: 7px; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px; height: 16px;
        border: 1px solid {c["border"]};
        border-radius: 4px;
        background: {c["surface"]};
    }}
    QRadioButton::indicator {{ border-radius: 8px; }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {c["accent"]};
        border-color: {c["accent"]};
    }}
    QTableWidget, QTableView, QTreeWidget, QListWidget {{
        background: {c["surface"]};
        border: 1px solid {c["separator"]};
        border-radius: 8px;
        gridline-color: #F0F0F2;
        alternate-background-color: {c["row_alt"]};
        outline: none;
    }}
    QTableView::item, QTreeWidget::item, QListWidget::item {{ padding: 4px 6px; }}
    QTableView::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {{
        background: {c["selected"]};
        color: {c["text"]};
    }}
    QHeaderView::section {{
        background: {c["surface_alt"]};
        border: none;
        border-bottom: 1px solid {c["separator"]};
        padding: 6px 8px;
        font-weight: 600;
        color: {c["secondary"]};
    }}
    QTableCornerButton::section {{ background: {c["surface_alt"]}; border: none; }}
    QProgressBar {{
        background: {c["sidebar_alt"]};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{ background: {c["accent"]}; border-radius: 4px; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: #C7C7CC; border-radius: 5px; min-height: 24px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: #C7C7CC; border-radius: 5px; min-width: 24px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QSplitter::handle {{ background: {c["separator"]}; }}
    QSplitter::handle:horizontal {{ width: 1px; }}
    QSplitter::handle:vertical {{ height: 1px; }}
    QMenuBar {{ background: {c["surface"]}; border-bottom: 1px solid {c["separator"]}; }}
    QMenuBar::item {{ padding: 5px 10px; background: transparent; }}
    QMenuBar::item:selected {{ background: {c["sidebar_alt"]}; border-radius: 5px; }}
    QMenu {{ background: {c["surface"]}; border: 1px solid {c["separator"]}; padding: 5px; }}
    QMenu::item {{ padding: 5px 26px 5px 26px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {c["accent"]}; color: #FFFFFF; }}
    QMenu::item:disabled {{ color: {c["muted"]}; }}
    QMenu::separator {{ height: 1px; background: {c["separator"]}; margin: 4px 8px; }}
    QToolTip {{
        background: {c["text"]};
        color: #FFFFFF;
        border: none;
        padding: 5px 7px;
        border-radius: 4px;
    }}
    QTabWidget::pane {{
        border: 1px solid {c["separator"]};
        border-radius: 8px;
        background: {c["surface"]};
    }}
    QTabBar::tab {{
        background: transparent;
        padding: 7px 14px;
        color: {c["secondary"]};
    }}
    QTabBar::tab:selected {{
        color: {c["text"]};
        font-weight: 600;
        border-bottom: 2px solid {c["accent"]};
    }}
    QDialog {{ background: {c["window"]}; }}
    QGroupBox {{
        border: 1px solid {c["separator"]};
        border-radius: 8px;
        margin-top: 10px;
        padding: 10px;
        font-weight: 600;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
    QStatusBar {{ background: {c["surface"]}; border-top: 1px solid {c["separator"]}; }}
    QSlider::groove:horizontal {{
        height: 4px; background: {c["separator"]}; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {c["surface"]}; border: 1px solid {c["border"]};
        width: 16px; height: 16px; margin: -7px 0; border-radius: 8px;
    }}
    """


def color_for_state(state: str) -> QColor:
    return QColor(STATE_COLORS.get(state.upper().replace("_", " "), COLORS["muted"]))


def apply_zoom(app: QApplication, percent: int) -> None:
    """Scale the stylesheet and application font (GNFR-006 View > Zoom)."""
    import re

    factor = max(0.7, min(2.0, percent / 100.0))
    css = _stylesheet()

    def scale(match: re.Match[str]) -> str:
        value = float(match.group(1)) * factor
        return f"font-size: {value:.1f}px"

    css = re.sub(r"font-size: (\d+(?:\.\d+)?)px", scale, css)
    app.setStyleSheet(css)
    font = app.font()
    font.setPointSizeF(10.5 * factor)
    app.setFont(font)
