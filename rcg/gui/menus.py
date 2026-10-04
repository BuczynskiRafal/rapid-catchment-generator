"""The window's menu bar, its actions and their keyboard shortcuts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow

__all__ = ["WindowActions", "install_menus", "shortcut_text"]


@dataclass(frozen=True)
class WindowActions:
    """The actions other parts of the window enable, trigger or describe."""

    open: QAction
    add: QAction
    help: QAction


def _shortcuts(*keys: QKeySequence | QKeySequence.StandardKey | str) -> list[QKeySequence]:
    """All bindings of *keys* on this platform, without empty or repeated sequences."""
    unique: list[QKeySequence] = []
    for key in keys:
        for seq in QKeySequence.keyBindings(key) if isinstance(key, QKeySequence.StandardKey) else [QKeySequence(key)]:
            if not seq.isEmpty() and seq not in unique:
                unique.append(seq)
    return unique


def shortcut_text(action: QAction) -> str:
    """The action's primary shortcut as the platform shows it (``""`` without one)."""
    return action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)


def install_menus(
    window: QMainWindow,
    *,
    open_model: Callable[[], object],
    add: Callable[[], object],
    show_help: Callable[[], object],
    show_about: Callable[[], object],
) -> WindowActions:
    """Build the File and Help menus of *window*, connected to the given callbacks."""
    open_action = QAction("Open Model…", window)
    open_action.setShortcuts(_shortcuts(QKeySequence.StandardKey.Open))
    open_action.triggered.connect(open_model)

    add_action = QAction("Add Subcatchment", window)
    add_action.setShortcuts(_shortcuts("Ctrl+Return", "Ctrl+Enter"))
    add_action.triggered.connect(add)

    quit_action = QAction("Quit", window)
    quit_action.setMenuRole(QAction.MenuRole.QuitRole)
    quit_action.setShortcuts(_shortcuts(QKeySequence.StandardKey.Quit))
    quit_action.triggered.connect(window.close)

    help_action = QAction("Rapid Catchment Generator Help", window)
    help_action.setShortcuts(_shortcuts("F1", QKeySequence.StandardKey.HelpContents))
    help_action.triggered.connect(show_help)

    about_action = QAction("About Rapid Catchment Generator", window)
    about_action.setMenuRole(QAction.MenuRole.AboutRole)
    about_action.triggered.connect(show_about)

    file_menu = window.menuBar().addMenu("&File")
    file_menu.addAction(open_action)
    file_menu.addAction(add_action)
    file_menu.addSeparator()
    file_menu.addAction(quit_action)
    help_menu = window.menuBar().addMenu("&Help")
    help_menu.addAction(help_action)
    help_menu.addAction(about_action)
    return WindowActions(open=open_action, add=add_action, help=help_action)
