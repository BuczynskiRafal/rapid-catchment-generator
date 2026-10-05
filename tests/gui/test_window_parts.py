"""The window's building blocks on their own: cards, file actions, menus."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def inputs_card(qtbot, rcg_app):
    from rcg.gui.cards import InputsCard

    card = InputsCard()
    qtbot.addWidget(card)
    return card


def test_inputs_key_rounds_the_area_like_the_spin_box(inputs_card):
    from rcg.fuzzy.categories import LandCover, LandForm

    inputs_card.area_spin.setValue(2.345)
    area, form, cover = inputs_card.inputs_key()
    assert area == pytest.approx(round(inputs_card.area_spin.value(), 2))
    assert isinstance(form, LandForm) and isinstance(cover, LandCover)


def test_inputs_card_signals_every_input_change(qtbot, inputs_card):
    for change in (
        lambda: inputs_card.area_spin.setValue(3.0),
        lambda: inputs_card.cover_combo.setCurrentIndex(1),
        lambda: inputs_card.form_combo.setCurrentIndex(1),
    ):
        with qtbot.waitSignal(inputs_card.inputsChanged, timeout=1_000):
            change()


def test_a_flashed_confirmation_survives_state_updates_until_cleared(inputs_card):
    inputs_card.flash_status("Added S1", 60_000)
    inputs_card.show_add_state(enabled=True, busy=False, hint="Press Ctrl+Return to add")
    assert inputs_card.add_hint.text() == "Added S1"
    assert inputs_card.add_hint.property("role") == "captionSuccess"

    inputs_card.show_add_state(enabled=False, busy=True, hint="Writing the model…")  # busy always shows
    assert inputs_card.add_hint.text() == "Writing the model…"
    assert inputs_card.add_button.text() == "Adding…" and not inputs_card.add_button.isEnabled()

    inputs_card.flash_status("Added S2", 60_000)
    inputs_card.clear_status()
    inputs_card.show_add_state(enabled=False, busy=False, hint="Choose a SWMM model first.")
    assert inputs_card.add_hint.text() == "Choose a SWMM model first."
    assert inputs_card.add_button.toolTip() == "Choose a SWMM model first."


def test_switching_the_model_card_to_in_place_is_silent(qtbot, rcg_app):
    from rcg.gui.cards import OUTPUT_COPY, OUTPUT_IN_PLACE, ModelCard

    card = ModelCard()
    qtbot.addWidget(card)
    toggled: list[object] = []
    card.output_group.buttonToggled.connect(lambda *args: toggled.append(args))
    card.copy_radio.setChecked(True)
    assert card.output_mode() == OUTPUT_COPY and toggled
    toggled.clear()
    card.switch_to_in_place()
    assert card.output_mode() == OUTPUT_IN_PLACE and toggled == []


def test_copy_suggestion_skips_existing_files(tmp_path):
    from rcg.gui.file_actions import copy_suggestion

    source = tmp_path / "model.inp"
    assert copy_suggestion(source) == tmp_path / "model_rcg.inp"
    (tmp_path / "model_rcg.inp").write_text("")
    (tmp_path / "model_rcg_2.inp").write_text("")
    assert copy_suggestion(source) == tmp_path / "model_rcg_3.inp"


def test_choose_output_path_without_dialogs(tmp_path):
    from rcg.gui.file_actions import choose_output_path

    source = tmp_path / "model.inp"
    asked: list[Path] = []

    def never(_path: Path) -> bool:
        raise AssertionError("no confirmation expected")

    assert choose_output_path(source, ask=lambda s: asked.append(s) or None, confirm=never) is None
    assert asked == [tmp_path / "model_rcg.inp"]
    assert choose_output_path(source, ask=lambda s: str(tmp_path / "out"), confirm=never) == tmp_path / "out.inp"


def test_menus_carry_the_actions_and_shortcuts(qtbot, rcg_app):
    from PySide6.QtWidgets import QMainWindow

    from rcg.gui.menus import install_menus, shortcut_text

    window = QMainWindow()
    qtbot.addWidget(window)
    calls: list[str] = []
    actions = install_menus(
        window,
        open_model=lambda: calls.append("open"),
        add=lambda: calls.append("add"),
        show_help=lambda: calls.append("help"),
        show_about=lambda: calls.append("about"),
    )
    for action in (actions.open, actions.add, actions.help):
        action.trigger()
    assert calls == ["open", "add", "help"]
    assert shortcut_text(actions.add)  # Ctrl+Return (Cmd+Return on macOS)
    assert [action.text() for action in window.menuBar().actions()] == ["&File", "&Help"]
