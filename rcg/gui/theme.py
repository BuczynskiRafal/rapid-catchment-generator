"""Palette-derived styling.

Nothing here hard-codes a background: every surface colour is mixed from the active
:class:`~PySide6.QtGui.QPalette` (which follows the operating system's light/dark
setting), plus one accent colour. The style is Fusion on every platform so the style
sheet renders identically everywhere, including the headless test platform.

When the application palette changes (the user flips the system appearance, or a test
forces a dark palette) the style sheet is rebuilt automatically.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QStandardPaths, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from rcg.logging_config import get_logger

__all__ = ["ThemeController", "Tokens", "current_tokens", "install_theme", "is_dark", "mix", "tokens"]

logger = get_logger("gui")  # one logger for the whole GUI (rcg.gui)

# The single accent, tuned per appearance so it keeps contrast on light and dark surfaces.
_ACCENT_LIGHT = "#2B6A96"
_ACCENT_DARK = "#5A9FD0"
_DANGER_LIGHT = "#B3261E"
_DANGER_DARK = "#F2867E"
_SUCCESS_LIGHT = "#2E7D4F"
_SUCCESS_DARK = "#6CC28E"


def mix(a: QColor, b: QColor, t: float) -> QColor:
    """Linear blend from *a* (``t = 0``) to *b* (``t = 1``) in sRGB."""
    t = max(0.0, min(1.0, t))
    return QColor.fromRgbF(
        a.redF() + (b.redF() - a.redF()) * t,
        a.greenF() + (b.greenF() - a.greenF()) * t,
        a.blueF() + (b.blueF() - a.blueF()) * t,
        1.0,
    )


def is_dark(palette: QPalette) -> bool:
    """True when the window background is darker than the window text."""
    window = palette.color(QPalette.ColorRole.Window).lightnessF()
    text = palette.color(QPalette.ColorRole.WindowText).lightnessF()
    return window < text


@dataclass(frozen=True)
class Tokens:
    """Resolved colours (``#rrggbb``) for one palette."""

    dark: bool
    window: str
    card: str
    border: str
    divider: str
    text: str
    muted: str
    input_bg: str
    input_border: str
    hover: str
    pressed: str
    accent: str
    accent_button: str
    accent_hover: str
    accent_pressed: str
    accent_disabled: str
    accent_soft: str
    accent_soft_text: str
    on_accent: str
    focus: str
    """Keyboard focus ring of buttons and radio buttons: a strong neutral that is never the
    colour of a control state (the accent marks checked, hover and pressed), so focus
    stays visible on a checked radio button. Text fields keep the accent border."""
    danger: str
    danger_soft: str
    danger_border: str
    success: str
    success_soft: str
    success_border: str


def tokens(palette: QPalette) -> Tokens:
    """Derive the design tokens from *palette*."""
    dark = is_dark(palette)
    window = palette.color(QPalette.ColorRole.Window)
    text = palette.color(QPalette.ColorRole.WindowText)
    base = palette.color(QPalette.ColorRole.Base)
    accent = QColor(_ACCENT_DARK if dark else _ACCENT_LIGHT)
    danger = QColor(_DANGER_DARK if dark else _DANGER_LIGHT)
    success = QColor(_SUCCESS_DARK if dark else _SUCCESS_LIGHT)
    white, black = QColor("#ffffff"), QColor("#000000")

    # Cards sit one step "above" the window: Base in light mode, a slightly lighter
    # window tone in dark mode (Base is usually darker than Window there).
    card = mix(window, text, 0.05) if dark else mix(window, base, 0.85)
    input_bg = mix(card, black, 0.18) if dark else base
    # White text needs a deeper accent for the filled button in dark mode.
    accent_button = mix(accent, black, 0.22) if dark else accent

    return Tokens(
        dark=dark,
        window=window.name(),
        card=card.name(),
        border=mix(card, text, 0.13 if dark else 0.11).name(),
        divider=mix(card, text, 0.08 if dark else 0.07).name(),
        text=text.name(),
        muted=mix(text, card, 0.42).name(),
        input_bg=input_bg.name(),
        input_border=mix(card, text, 0.22).name(),
        hover=mix(card, text, 0.06).name(),
        pressed=mix(card, text, 0.11).name(),
        accent=accent.name(),
        accent_button=accent_button.name(),
        accent_hover=mix(accent_button, white if dark else black, 0.10).name(),
        accent_pressed=mix(accent_button, black, 0.20).name(),
        accent_disabled=mix(accent_button, card, 0.55).name(),
        accent_soft=mix(card, accent, 0.20 if dark else 0.10).name(),
        accent_soft_text=(mix(accent, white, 0.30) if dark else mix(accent, black, 0.12)).name(),
        on_accent="#ffffff",
        focus=mix(text, card, 0.15).name(),
        danger=danger.name(),
        danger_soft=mix(card, danger, 0.14 if dark else 0.07).name(),
        danger_border=mix(card, danger, 0.45 if dark else 0.32).name(),
        success=success.name(),
        success_soft=mix(card, success, 0.14 if dark else 0.08).name(),
        success_border=mix(card, success, 0.45 if dark else 0.32).name(),
    )


def _cache_dir() -> Path | None:
    """This user's cache folder for RCG (``<user cache>/rcg``), or ``None`` if there is none."""
    folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericCacheLocation)
    return Path(folder) / "rcg" if folder else None


def _chevron_svg(color: str) -> Path | None:
    """Return a small down-chevron SVG in *color*, written once to the per-user cache.

    The file lives in this user's cache folder (never a shared temporary directory) and
    is written atomically. Returns ``None`` when it cannot be written; the combo boxes
    then keep the style's default arrow.
    """
    folder = _cache_dir()
    if folder is None:
        return None
    path = folder / "theme" / f"chevron-{color.lstrip('#')}.svg"
    if path.is_file():
        return path
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12">'
        f'<path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="{color}" stroke-width="1.6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(svg, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        logger.warning("Cannot write the combo box arrow to %s; using the default arrow", path, exc_info=True)
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    return path


def stylesheet(t: Tokens, base_pt: float) -> str:
    """Return the application style sheet for tokens *t* and base font size *base_pt*."""

    def pt(factor: float) -> str:
        return f"{base_pt * factor:.1f}pt"

    chevron_path = _chevron_svg(t.muted)
    chevron_rule = (
        f'QComboBox::down-arrow {{ image: url("{chevron_path.as_posix()}"); width: 12px; height: 12px; }}'
        if chevron_path is not None
        else ""
    )
    return f"""
QWidget {{
    selection-background-color: {t.accent_soft};
    selection-color: {t.text};
}}
QMainWindow, QDialog {{ background-color: {t.window}; }}

QToolTip {{
    background-color: {t.card};
    color: {t.text};
    border: 1px solid {t.border};
    border-radius: 6px;
    padding: 6px 8px;
}}

/* Cards ---------------------------------------------------------------- */
QFrame[card="true"] {{
    background-color: {t.card};
    border: 1px solid {t.border};
    border-radius: 10px;
}}
QFrame[divider="true"] {{
    background-color: {t.divider};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

/* Typography ----------------------------------------------------------- */
QLabel[role="title"] {{ font-size: {pt(1.45)}; font-weight: 600; }}
QLabel[role="subtitle"] {{ color: {t.muted}; }}
QLabel[role="sectionTitle"] {{ font-size: {pt(1.05)}; font-weight: 600; }}
QLabel[role="fieldLabel"] {{ color: {t.text}; }}
QLabel[role="caption"] {{ color: {t.muted}; font-size: {pt(0.92)}; }}
QLabel[role="captionError"] {{ color: {t.danger}; font-size: {pt(0.92)}; }}
QLabel[role="captionSuccess"] {{ color: {t.success}; font-size: {pt(0.92)}; font-weight: 500; }}
QLabel[role="metricLabel"] {{ color: {t.muted}; font-size: {pt(0.92)}; }}
QLabel[role="metricValue"] {{ font-size: {pt(1.45)}; font-weight: 600; }}
QLabel[role="metricUnit"] {{ color: {t.muted}; font-size: {pt(1.0)}; }}
QLabel[role="tableHeader"] {{ color: {t.muted}; font-size: {pt(0.92)}; }}
QLabel[role="value"] {{ font-weight: 500; }}
QLabel[role="historyTitle"] {{ font-weight: 600; }}
QLabel[role="historyTitle"][undone="true"] {{ color: {t.muted}; text-decoration: line-through; }}
QLabel[role="placeholder"] {{ color: {t.muted}; }}
QLabel[role="badge"] {{
    background-color: {t.accent_soft};
    color: {t.accent_soft_text};
    border-radius: 10px;
    padding: 3px 10px;
    font-weight: 600;
}}
QLabel[role="pill"] {{
    background-color: {t.hover};
    color: {t.muted};
    border-radius: 8px;
    padding: 1px 8px;
    font-size: {pt(0.85)};
}}

/* Inputs --------------------------------------------------------------- */
QComboBox, QLineEdit, QDoubleSpinBox {{
    background-color: {t.input_bg};
    color: {t.text};
    border: 1px solid {t.input_border};
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 20px;
}}
QComboBox:hover, QLineEdit:hover, QDoubleSpinBox:hover {{ border-color: {mix_hex(t.input_border, t.text, 0.25)}; }}
QComboBox:focus, QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:on {{ border: 1px solid {t.accent}; }}
QLineEdit[invalid="true"] {{ border-color: {t.danger_border}; }}
QLineEdit[invalid="true"]:focus {{ border-color: {t.danger}; }}
QLineEdit[dropTarget="true"] {{ border: 1px dashed {t.accent}; background-color: {t.accent_soft}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 22px;
    border: none;
}}
{chevron_rule}
QComboBox QAbstractItemView {{
    background-color: {t.card};
    color: {t.text};
    border: 1px solid {t.border};
    border-radius: 6px;
    padding: 4px;
    outline: 0;
    selection-background-color: {t.accent_soft};
    selection-color: {t.text};
}}
QComboBox QAbstractItemView::item {{ min-height: 24px; padding: 2px 6px; border-radius: 4px; }}

/* The focus ring wraps the whole control, a few pixels away from the indicator, in the
   neutral focus colour, so it never reads as one of the indicator's states (checked and
   hover use the accent). */
QRadioButton {{
    spacing: 8px;
    padding: 2px 8px 2px 4px;
    margin-left: -5px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
}}
QRadioButton:focus {{ border-color: {t.focus}; }}
QRadioButton::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {t.input_border};
    border-radius: 8px;
    background-color: {t.input_bg};
}}
QRadioButton::indicator:hover {{ border-color: {t.accent}; }}
QRadioButton::indicator:checked {{
    width: 8px; height: 8px;
    border: 4px solid {t.accent_button};
    background-color: {t.input_bg if not t.dark else t.text};
}}

/* Buttons -------------------------------------------------------------- */
QPushButton {{
    background-color: {t.card};
    color: {t.text};
    border: 1px solid {t.input_border};
    border-radius: 6px;
    padding: 5px 14px;
    min-height: 20px;
}}
QPushButton:hover {{ background-color: {t.hover}; }}
QPushButton:pressed {{ background-color: {t.pressed}; }}
QPushButton:focus {{ border-color: {t.focus}; }}
QPushButton:disabled {{ color: {t.muted}; border-color: {t.divider}; }}
QPushButton[primary="true"] {{
    background-color: {t.accent_button};
    color: {t.on_accent};
    border: 1px solid {t.accent_button};
    font-weight: 600;
    padding: 7px 20px;
}}
QPushButton[primary="true"]:hover {{ background-color: {t.accent_hover}; border-color: {t.accent_hover}; }}
QPushButton[primary="true"]:pressed {{ background-color: {t.accent_pressed}; border-color: {t.accent_pressed}; }}
/* Primary focus: PrimaryButton paints an inner ring in on_accent (see widgets/buttons.py). */
QPushButton[primary="true"]:disabled {{
    background-color: {t.accent_disabled};
    border-color: {t.accent_disabled};
    color: {mix_hex(t.on_accent, t.accent_disabled, 0.25)};
}}
QPushButton[flat="true"], QToolButton[flat="true"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {t.accent_soft_text};
    padding: 3px 8px;
    border-radius: 6px;
}}
QPushButton[flat="true"]:hover, QToolButton[flat="true"]:hover {{ background-color: {t.accent_soft}; }}
QPushButton[flat="true"]:focus, QToolButton[flat="true"]:focus {{ border-color: {t.focus}; }}
QToolButton[role="help"] {{
    background-color: {t.card};
    color: {t.muted};
    border: 1px solid {t.border};
    border-radius: 14px;
    min-width: 26px; max-width: 26px;
    min-height: 26px; max-height: 26px;
    font-weight: 600;
}}
QToolButton[role="help"]:hover {{ color: {t.text}; background-color: {t.hover}; }}
QToolButton[role="help"]:focus {{ border-color: {t.focus}; color: {t.text}; }}

/* Banner --------------------------------------------------------------- */
QFrame[banner="error"] {{ background-color: {t.danger_soft}; border: 1px solid {t.danger_border}; border-radius: 8px; }}
QFrame[banner="success"] {{ background-color: {t.success_soft}; border: 1px solid {t.success_border}; border-radius: 8px; }}
QFrame[banner="info"] {{ background-color: {t.accent_soft}; border: 1px solid {mix_hex(t.accent_soft, t.accent, 0.35)}; border-radius: 8px; }}
QFrame#messageBanner QLabel {{ background: transparent; color: {t.text}; }}
QFrame#messageBanner QLabel[role="bannerMark"] {{ font-weight: 700; }}
QFrame#messageBanner[banner="error"] QLabel[role="bannerMark"] {{ color: {t.danger}; }}
QFrame#messageBanner[banner="success"] QLabel[role="bannerMark"] {{ color: {t.success}; }}
QFrame#messageBanner[banner="info"] QLabel[role="bannerMark"] {{ color: {t.accent}; }}
QFrame#messageBanner QToolButton {{
    background: transparent; border: none; color: {t.muted}; padding: 0 4px; font-size: {pt(1.15)};
}}
QFrame#messageBanner QToolButton:hover {{ color: {t.text}; }}

/* Progress, scrolling -------------------------------------------------- */
QProgressBar {{
    background-color: {t.divider};
    border: none;
    border-radius: 2px;
    max-height: 4px;
    min-height: 4px;
}}
QProgressBar::chunk {{ background-color: {t.accent}; border-radius: 2px; }}
QScrollArea, QWidget#historyContent, QWidget#inputsContent {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t.input_border}; border-radius: 3px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QTextBrowser {{
    background-color: {t.card};
    border: 1px solid {t.border};
    border-radius: 8px;
    padding: 8px 12px;
}}
"""


def mix_hex(a: str, b: str, t: float) -> str:
    """Hex-string convenience wrapper around :func:`mix`."""
    return mix(QColor(a), QColor(b), t).name()


_current: Tokens | None = None


def current_tokens() -> Tokens:
    """Return the tokens of the active palette (computed on demand)."""
    if _current is not None:
        return _current
    app = QApplication.instance()
    palette = app.palette() if isinstance(app, QApplication) else QPalette()
    return tokens(palette)


class ThemeController(QObject):
    """Applies the style sheet and re-applies it whenever the application palette changes."""

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self._app = app
        self._signature: tuple[str, ...] | None = None
        self._pending = False
        app.installEventFilter(self)
        self.apply()

    def _palette_signature(self) -> tuple[str, ...]:
        p = self._app.palette()
        roles = (QPalette.ColorRole.Window, QPalette.ColorRole.WindowText, QPalette.ColorRole.Base, QPalette.ColorRole.Text)
        return tuple(p.color(role).name() for role in roles) + (f"{self._app.font().pointSizeF():.2f}",)

    def apply(self) -> None:
        """Rebuild and install the style sheet for the current palette and font."""
        global _current
        self._pending = False
        signature = self._palette_signature()
        if signature == self._signature:
            return
        self._signature = signature
        _current = tokens(self._app.palette())
        base_pt = self._app.font().pointSizeF()
        if base_pt <= 0:
            base_pt = 10.0
        self._app.setStyleSheet(stylesheet(_current, base_pt))

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            watched is self._app
            and event.type() in (QEvent.Type.ApplicationPaletteChange, QEvent.Type.ApplicationFontChange)
            and not self._pending
        ):
            self._pending = True
            QTimer.singleShot(0, self.apply)
        return False


def install_theme(app: QApplication) -> ThemeController:
    """Switch *app* to Fusion and install the palette-following style sheet (idempotent)."""
    existing = app.findChild(ThemeController)
    if existing is not None:
        existing.apply()
        return existing
    if app.style().name().lower() != "fusion":
        app.setStyle("Fusion")
    return ThemeController(app)
