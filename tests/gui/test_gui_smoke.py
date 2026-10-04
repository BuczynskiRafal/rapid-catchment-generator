"""Headless smoke tests of the PySide6 window: warm-up, live preview, add, undo, errors."""

from __future__ import annotations

import logging

import pytest
from gui_helpers import (
    ENGINE_TIMEOUT_MS,
    add_and_wait,
    dark_palette,
    save_screenshot,
    select,
    subcatchment_ids,
)
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent

from rcg.catchment import INFILTRATION_FIELDS
from rcg.catchment import label as category_label
from rcg.exceptions import ModelOperationError
from rcg.fuzzy.categories import LandCover, LandForm
from rcg.gui.categories import land_cover_options, land_form_options

APPLY_TIMEOUT_MS = 30_000


# --------------------------------------------------------------------------- start-up
def test_window_opens_and_warms_up_in_background(qtbot, rcg_app, gui_settings):
    """Cold start: the engine is built by the worker while the window stays responsive."""
    from rcg.gui.main_window import MainWindow

    win = MainWindow(gui_settings)
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)

    assert win.windowTitle() == "Rapid Catchment Generator"
    assert win.minimumSizeHint().width() >= 860 and win.minimumSizeHint().height() >= 560
    assert not win.add_button.isEnabled()
    if not win.engine_ready:  # an engine built by an earlier test makes warm-up instant
        assert win.preview.is_preparing()
        assert "Preparing fuzzy engine" in win.add_hint.text()

    qtbot.waitUntil(lambda: win.engine_ready, timeout=ENGINE_TIMEOUT_MS)
    qtbot.waitUntil(lambda: win.current_parameters() is not None, timeout=10_000)
    assert not win.preview.is_preparing()
    assert not win.add_button.isEnabled(), "no model chosen yet"
    assert "Choose a SWMM model" in win.add_hint.text()


def test_area_range_follows_the_validation_limit(window):
    from rcg.validation import max_area_ha, min_area_ha

    assert window.area_spin.maximum() == max_area_ha()
    assert window.area_spin.minimum() >= min_area_ha()
    assert "0.01 to 10 000 ha" in window.area_spin.toolTip()


def test_category_combos_use_labels_in_enum_order(window):
    covers = [window.cover_combo.itemData(i) for i in range(window.cover_combo.count())]
    forms = [window.form_combo.itemData(i) for i in range(window.form_combo.count())]
    assert covers == list(LandCover)
    assert forms == list(LandForm)
    assert window.cover_combo.itemText(covers.index(LandCover.urban_moderately_impervious)) == "Urban, moderately impervious"
    assert window.form_combo.itemText(2) == category_label(LandForm.flats_and_plateaus_in_combination_with_hills)
    for i in range(window.cover_combo.count()):
        assert window.cover_combo.itemData(i, Qt.ItemDataRole.ToolTipRole), "every option has a description"
    for option in (*land_cover_options(), *land_form_options()):
        assert option.hint and len(option.hint) <= 48, option
    assert window.cover_hint.full_text() == land_cover_options()[0].hint
    assert window.cover_hint.toolTip() == window.cover_combo.currentData(Qt.ItemDataRole.ToolTipRole)


# --------------------------------------------------------------------------- preview
@pytest.mark.parametrize(
    ("area", "land_form", "land_cover"),
    [
        (5.5, LandForm.flats_and_plateaus, LandCover.urban_moderately_impervious),
        (12.0, LandForm.mountains, LandCover.forests),
        (0.75, LandForm.hills_with_gentle_slopes, LandCover.suburban_highly_impervious),
    ],
)
def test_preview_matches_service(qtbot, window, gui_engine, area, land_form, land_cover):
    from rcg import service
    from rcg.gui.categories import catchment_type_label

    # The window is idle (first preview shown), so the shared engine is free to use here.
    expected = service.preview(area, land_form, land_cover, engine=gui_engine)

    select(window.cover_combo, land_cover)
    select(window.form_combo, land_form)
    window.area_spin.setValue(area)
    qtbot.waitUntil(lambda: window.current_parameters() is not None, timeout=10_000)

    shown = window.current_parameters()
    assert shown == expected
    panel = window.preview
    assert panel.badge.isVisible()
    assert panel.badge.text() == catchment_type_label(expected.catchment_type)
    assert panel.slope.value.text() == f"{expected.slope_pct:.2f}"
    assert panel.impervious.value.text() == f"{expected.impervious_pct:.2f}"
    assert panel.width_metric.value.text() == f"{expected.width_m:.2f}"
    assert panel.n_imperv.text() == f"{expected.n_imperv:.3f}"
    assert panel.n_perv.text() == f"{expected.n_perv:.3f}"
    assert panel.s_imperv.text() == f"{expected.s_imperv_mm:.2f} mm"
    assert panel.s_perv.text() == f"{expected.s_perv_mm:.2f} mm"
    assert panel.pct_zero.text() == f"{expected.pct_zero} %"
    # No model chosen: the Green-Ampt row, labelled by its SWMM field names.
    assert list(panel.infiltration_text()) == list(expected.infiltration)[: len(INFILTRATION_FIELDS["GREEN_AMPT"])]


def test_preview_is_debounced(qtbot, window):
    """Rapid edits produce one computation for the final value, not one per keystroke."""
    seen: list[int] = []
    window._engine_worker.previewReady.connect(lambda rid, _p: seen.append(rid))
    for value in (2.0, 3.0, 4.0, 5.0, 6.25):
        window.area_spin.setValue(value)
    qtbot.waitUntil(lambda: window.current_parameters() is not None, timeout=10_000)
    assert window.current_parameters().area_ha == pytest.approx(6.25)
    assert len(seen) == 1


# --------------------------------------------------------------------------- model picker
def test_model_path_validation_is_inline(qtbot, window, tmp_path, model_copy):
    window.path_field.set_path(tmp_path / "missing.inp")
    assert window.path_field.path() is None
    assert window.path_field.message.property("role") == "captionError"
    assert not window.add_button.isEnabled()

    not_a_model = tmp_path / "notes.txt"
    not_a_model.write_text("x")
    window.path_field.set_path(not_a_model)
    assert window.path_field.path() is None
    assert ".inp" in window.path_field.message.full_text()

    window.path_field.set_path(model_copy)
    assert window.path_field.path() == model_copy.resolve()
    assert window.path_field.message.full_text().startswith("15 subcatchments")
    assert window.add_button.isEnabled()


def test_dropping_a_file_sets_the_model(window, model_copy):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(model_copy))])
    event = QDropEvent(
        QPointF(20, 20), Qt.DropAction.CopyAction, mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    )
    window.dropEvent(event)
    assert window.path_field.path() == model_copy.resolve()


def test_open_model_sets_the_path_and_focuses_the_field(qtbot, window, model_copy):
    window.open_model(str(model_copy))
    assert window.path_field.path() == model_copy.resolve()
    if window.isActiveWindow():  # focus is only reported for the active window
        assert window.path_field.edit.hasFocus()


# --------------------------------------------------------------------------- add / undo
def test_add_subcatchment_writes_model_and_records_history(qtbot, window, model_copy, screenshot_dirs):
    before_bytes = model_copy.read_bytes()
    before_ids = subcatchment_ids(model_copy)

    select(window.cover_combo, LandCover.urban_moderately_impervious)
    select(window.form_combo, LandForm.flats_and_plateaus_in_combination_with_hills)
    window.area_spin.setValue(5.5)
    window.path_field.set_path(model_copy)
    assert window.add_button.isEnabled()

    add_and_wait(qtbot, window)

    assert model_copy.read_bytes() != before_bytes
    after_ids = subcatchment_ids(model_copy)
    assert len(after_ids) == len(before_ids) + 1
    entry = window.history.entries[0]
    assert set(after_ids) - set(before_ids) == set(entry.subcatchment_ids)
    assert entry.output_path == model_copy.resolve()
    assert entry.backup_path is not None and entry.backup_path.is_file()
    assert entry.backup_path.read_bytes() == before_bytes
    assert entry.catchment_type == "urban"
    assert window.history.undo_button_for(entry).isVisibleTo(window)
    assert entry.title in window.status_text()
    assert not window.banner.isVisible()

    # Second add, so the screenshot shows a history with more than one row.
    add_and_wait(qtbot, window)
    assert len(subcatchment_ids(model_copy)) == len(before_ids) + 2
    save_screenshot(window, screenshot_dirs, "rcg-gui.png")


def test_undo_restores_the_backup(qtbot, window, model_copy):
    original = model_copy.read_bytes()
    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)
    first_written = model_copy.read_bytes()
    add_and_wait(qtbot, window)

    latest, older = window.history.entries
    assert window.history.undo_candidate() is latest
    qtbot.mouseClick(window.history.undo_button_for(latest), Qt.MouseButton.LeftButton)
    assert latest.undone
    assert model_copy.read_bytes() == first_written
    assert window.history.undo_candidate() is older

    assert window.undo_entry(older)
    assert model_copy.read_bytes() == original
    assert window.history.undo_candidate() is None
    assert latest.backup_path.is_file(), "backups are kept after undo"


def test_undo_refuses_when_the_file_changed_since(qtbot, window, model_copy):
    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)
    entry = window.history.entries[0]
    model_copy.write_text(model_copy.read_text() + "\n; edited by hand\n")

    assert not window.undo_entry(entry)
    assert not entry.undone
    assert window.banner.isVisible() and window.banner.kind == "error"
    assert "changed" in window.banner.text


def test_save_as_copy_leaves_source_untouched(qtbot, window, model_copy, monkeypatch):
    output = model_copy.with_name("example_copy.inp")
    monkeypatch.setattr(window, "_choose_output_path", lambda source: output)
    original = model_copy.read_bytes()

    window.copy_radio.setChecked(True)
    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)

    assert model_copy.read_bytes() == original
    assert output.is_file()
    assert len(subcatchment_ids(output)) == len(subcatchment_ids(model_copy)) + 1
    entry = window.history.entries[0]
    assert entry.output_path == output.resolve()
    assert entry.backup_path is None
    assert window.history.undo_candidate() is None


def test_cancelling_the_copy_dialog_does_nothing(qtbot, window, model_copy, monkeypatch):
    monkeypatch.setattr(window, "_choose_output_path", lambda source: None)
    window.copy_radio.setChecked(True)
    window.path_field.set_path(model_copy)
    qtbot.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
    assert not window.busy
    assert window.history.entries == []


# --------------------------------------------------------------------------- errors
def test_rcg_error_is_shown_in_the_banner(qtbot, window, model_copy, monkeypatch):
    from rcg import service

    def fail(*args, **kwargs):
        raise ModelOperationError("The model has no [SUBCATCHMENTS] section we can edit.")

    monkeypatch.setattr(service, "apply", fail)
    window.path_field.set_path(model_copy)
    qtbot.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.banner.isVisible(), timeout=APPLY_TIMEOUT_MS)
    qtbot.waitUntil(lambda: not window.busy, timeout=APPLY_TIMEOUT_MS)

    assert window.banner.kind == "error"
    assert window.banner.text == "The model has no [SUBCATCHMENTS] section we can edit."
    assert window.history.entries == []
    assert window.add_button.isEnabled()


def test_failed_add_after_success_resets_the_status(qtbot, window, model_copy, monkeypatch):
    from rcg import service

    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)
    assert "Added" in window.status_text()

    def fail(*args, **kwargs):
        raise ModelOperationError("disk full")

    monkeypatch.setattr(service, "apply", fail)
    qtbot.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.banner.isVisible() and not window.busy, timeout=APPLY_TIMEOUT_MS)
    assert "Added" not in window.status_text()
    assert "Writing" not in window.status_text()
    assert window.add_button.text() == "Add subcatchment"


def test_unexpected_error_is_logged_and_shown_generically(qtbot, window, model_copy, monkeypatch, caplog):
    from rcg import service

    def crash(*args, **kwargs):
        raise RuntimeError("internal detail")

    monkeypatch.setattr(service, "apply", crash)
    window.path_field.set_path(model_copy)
    with caplog.at_level(logging.ERROR, logger="rcg.gui"):
        qtbot.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: window.banner.isVisible() and not window.busy, timeout=APPLY_TIMEOUT_MS)

    assert "internal detail" not in window.banner.text
    assert "unexpected error" in window.banner.text
    records = [r for r in caplog.records if r.name == "rcg.gui" and r.exc_info]
    assert records and "internal detail" in str(records[-1].exc_info[1])


# --------------------------------------------------------------------------- settings, help, shortcuts
def test_settings_persist_between_sessions(qtbot, rcg_app, gui_engine, gui_settings, model_copy):
    from rcg.gui.main_window import OUTPUT_COPY, MainWindow

    first = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(first)
    first.copy_radio.setChecked(True)
    first.path_field.set_path(model_copy)
    first.close()

    assert gui_settings.value("output/mode") == OUTPUT_COPY
    assert gui_settings.value("paths/last_dir") == str(model_copy.parent)
    assert gui_settings.value("window/geometry") is not None

    second = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(second)
    assert second.copy_radio.isChecked()
    assert second.output_mode() == OUTPUT_COPY


def test_shortcuts_and_accessibility(window):
    from PySide6.QtGui import QKeySequence

    assert QKeySequence("F1") in window.help_action.shortcuts()
    assert QKeySequence("Ctrl+Return") in window.add_action.shortcuts()
    assert QKeySequence(QKeySequence.StandardKey.Open) in window.open_action.shortcuts()
    for widget in (window.cover_combo, window.form_combo, window.area_spin, window.path_field.edit, window.add_button):
        assert widget.accessibleName()
        assert widget.focusPolicy() & Qt.FocusPolicy.TabFocus
    assert window.cover_combo.nextInFocusChain() is not None


def test_help_dialog_renders_the_category_tables(qtbot, window, screenshot_dirs):
    window.help_action.trigger()
    dialog = window._help
    assert dialog is not None and dialog.isVisible()
    text = dialog.browser.toPlainText()
    assert "Land form categories" in text
    assert "Urban, moderately impervious" in text
    assert "Flats and plateaus in combination with hills" in text
    save_screenshot(dialog, screenshot_dirs, "rcg-gui-help.png")
    dialog.close()


def test_resources_are_packaged():
    from rcg.gui.resources import read_text, resource_path

    assert resource_path("icon.png") is not None
    assert "Land cover categories" in read_text("help.md")
    assert resource_path("does-not-exist.txt") is None


# --------------------------------------------------------------------------- dark palette
def test_dark_palette_restyles_the_window(qtbot, rcg_app, window, model_copy, screenshot_dirs):
    from rcg.gui import theme

    original = rcg_app.palette()
    try:
        rcg_app.setPalette(dark_palette())
        qtbot.waitUntil(lambda: theme.current_tokens().dark, timeout=5_000)
        assert "#2b2b2d" in rcg_app.styleSheet()

        select(window.cover_combo, LandCover.urban_moderately_impervious)
        select(window.form_combo, LandForm.flats_and_plateaus_in_combination_with_hills)
        window.area_spin.setValue(5.5)
        window.path_field.set_path(model_copy)
        add_and_wait(qtbot, window)
        add_and_wait(qtbot, window)
        save_screenshot(window, screenshot_dirs, "rcg-gui-dark.png")
    finally:
        rcg_app.setPalette(original)
        qtbot.waitUntil(lambda: not theme.current_tokens().dark, timeout=5_000)
