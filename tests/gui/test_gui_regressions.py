"""Regression tests for the GUI fix round: one test (or a few) per reported defect."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from gui_helpers import (
    APPLY_TIMEOUT_MS,
    ENGINE_TIMEOUT_MS,
    LONG_ERROR,
    PREVIEW_TIMEOUT_MS,
    add_and_wait,
    dark_palette,
    make_us_model,
    save_screenshot,
    select,
    subcatchment_areas,
    subcatchment_ids,
)
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QAbstractButton, QApplication, QLabel

from rcg.catchment import INFILTRATION_FIELDS, infiltration_for
from rcg.fuzzy.categories import LandCover, LandForm

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def us_model(model_copy: Path) -> Path:
    """A CFS / HORTON variant of the example model."""
    return make_us_model(model_copy, model_copy.with_name("us_model.inp"))


def _visible_texts(window) -> list[str]:
    """Every label/button text and tooltip of the window (user-facing strings)."""
    texts: list[str] = []
    for widget in (*window.findChildren(QLabel), *window.findChildren(QAbstractButton)):
        texts.extend((widget.text(), widget.toolTip()))
    return [text for text in texts if text]


# --------------------------------------------------------------------------- 1. save as copy
def test_save_as_copy_then_add_again_builds_on_the_copy(qtbot, window, model_copy, gui_settings, monkeypatch):
    """After a copy is written the session edits the copy, so a second Add keeps the first."""
    from rcg.gui.main_window import OUTPUT_COPY

    output = model_copy.with_name("example_copy.inp")
    calls: list[Path] = []

    def choose(source: Path) -> Path:
        calls.append(source)
        return output

    monkeypatch.setattr(window, "_choose_output_path", choose)
    original = model_copy.read_bytes()
    source_count = len(subcatchment_ids(model_copy))

    window.copy_radio.setChecked(True)
    window.path_field.set_path(model_copy)
    add_and_wait(qtbot, window)

    first = window.history.entries[0]
    assert window.path_field.path() == output.resolve()
    assert window.in_place_radio.isChecked()
    assert f"Now editing {output.name}" in window.status_text()
    # The automatic switch is not the user's choice: the remembered mode stays "copy".
    assert gui_settings.value("output/mode") == OUTPUT_COPY

    add_and_wait(qtbot, window)
    second = window.history.entries[0]

    assert calls == [model_copy.resolve()], "the save dialog is only shown for the first Add"
    assert model_copy.read_bytes() == original
    ids = subcatchment_ids(output)
    assert len(ids) == source_count + 2
    assert set(first.subcatchment_ids) | set(second.subcatchment_ids) <= set(ids)
    assert second.output_path == output.resolve() and second.backup_path is not None

    # The second Add was an in-place update of the copy, so it can be undone.
    assert window.history.undo_candidate() is second
    assert window.undo_entry(second)
    assert len(subcatchment_ids(output)) == source_count + 1


# --------------------------------------------------------------------------- 2. output name
@pytest.mark.parametrize(
    ("chosen", "expected"),
    [("model_v1.1", "model_v1.1.inp"), ("model", "model.inp"), ("model.INP", "model.INP"), ("a.b.inp", "a.b.inp")],
)
def test_output_suffix_is_appended_never_substituted(chosen, expected):
    from rcg.gui.main_window import normalise_output_path

    assert normalise_output_path(Path("/data") / chosen) == Path("/data") / expected


def test_adjusted_output_name_is_confirmed_when_it_exists(window, tmp_path, monkeypatch):
    source = tmp_path / "model.inp"
    sibling = tmp_path / "model_v1.inp"  # what with_suffix() would have overwritten
    adjusted = tmp_path / "model_v1.1.inp"
    for path in (source, sibling, adjusted):
        path.write_text("[TITLE]\n")
    asked: list[Path] = []
    answer = {"value": False}

    def confirm(path: Path) -> bool:
        asked.append(path)
        return answer["value"]

    monkeypatch.setattr(window, "_ask_save_path", lambda suggestion: str(tmp_path / "model_v1.1"))
    monkeypatch.setattr(window, "_confirm_replace", confirm)

    assert window._choose_output_path(source) is None
    assert asked == [adjusted]
    answer["value"] = True
    assert window._choose_output_path(source) == adjusted

    # A name the dialog already confirmed (it ends in .inp) is not asked about again.
    asked.clear()
    monkeypatch.setattr(window, "_ask_save_path", lambda suggestion: str(sibling))
    assert window._choose_output_path(source) == sibling
    assert asked == []


# --------------------------------------------------------------------------- 3. close during warm-up
def test_closing_during_warm_up_hides_at_once_and_stops_cleanly(qtbot, qtlog, rcg_app, gui_settings, gui_engine, monkeypatch):
    from rcg import service
    from rcg.gui.main_window import MainWindow

    def slow_warm_up(engine=None):
        time.sleep(1.5)
        return gui_engine

    monkeypatch.setattr(service, "warm_up", slow_warm_up)
    win = MainWindow(gui_settings)
    qtbot.addWidget(win)
    win.show()
    qtbot.waitUntil(win.engine_thread_running, timeout=5_000)

    started = time.monotonic()
    win.close()
    elapsed = time.monotonic() - started

    assert elapsed < 1.0, f"closing blocked for {elapsed:.2f} s"
    assert not win.isVisible()
    assert gui_settings.value("window/geometry") is not None, "settings are saved before waiting"
    # The thread finishes in the background; wait for it here so it is never torn down running.
    qtbot.waitUntil(lambda: not win.engine_thread_running(), timeout=10_000)
    assert not win.engine_ready, "a result arriving after close is ignored"
    assert not any("Destroyed while thread" in record.message for record in qtlog.records)


# --------------------------------------------------------------------------- 4 + 8. minimum size, banner
def _assert_inputs_fully_visible(window) -> None:
    scroll = window.inputs_scroll
    content = scroll.widget()
    cap = int(window.screen().availableGeometry().height() * scroll.SCREEN_SHARE)
    if content.minimumSizeHint().height() <= cap:  # otherwise scrolling is the intended fallback
        assert scroll.verticalScrollBar().maximum() == 0
        assert scroll.viewport().height() >= content.minimumSizeHint().height()
    for widget in (window.path_field.edit, window.in_place_radio, window.copy_radio, window.area_spin):
        assert not widget.visibleRegion().isEmpty(), widget.accessibleName() or widget.text()
    assert content.width() <= scroll.viewport().width(), "the cards are never clipped on the right"


def _assert_preview_not_squeezed(window) -> None:
    preview = window.preview
    assert preview.height() >= preview.minimumSizeHint().height()
    for lbl in preview.findChildren(QLabel):
        if lbl.isVisible():
            assert lbl.height() >= lbl.minimumSizeHint().height(), repr(lbl.text())


def test_cards_fit_at_minimum_size(qtbot, window, screenshot_dirs):
    window.resize(window.minimumSizeHint())
    qtbot.waitUntil(lambda: window.size() == window.minimumSizeHint(), timeout=2_000)
    QApplication.processEvents()
    _assert_inputs_fully_visible(window)
    _assert_preview_not_squeezed(window)
    save_screenshot(window, screenshot_dirs, "rcg-gui-min.png")


def test_long_banner_grows_the_window_instead_of_squeezing(qtbot, window, model_copy, screenshot_dirs):
    window.path_field.set_path(model_copy)
    window.resize(window.minimumSizeHint())
    QApplication.processEvents()
    before = window.minimumSizeHint()

    window.banner.show_error(LONG_ERROR)
    QApplication.processEvents()
    grown = window.minimumSizeHint()
    window.resize(grown)
    qtbot.waitUntil(lambda: window.size() == window.minimumSizeHint(), timeout=2_000)
    QApplication.processEvents()

    text = window.banner._text
    assert grown.width() == before.width()
    assert grown.height() > before.height()
    assert text.height() >= text.heightForWidth(text.width()), "the message is not clipped"
    assert text.heightForWidth(text.width()) > 2 * text.fontMetrics().lineSpacing(), "the message wraps"
    _assert_inputs_fully_visible(window)
    _assert_preview_not_squeezed(window)
    save_screenshot(window, screenshot_dirs, "rcg-gui-min-banner.png")

    window.banner.dismiss()
    QApplication.processEvents()
    assert window.minimumSizeHint() == before


# --------------------------------------------------------------------------- 5. focus
def test_focus_colour_never_matches_a_state_colour(rcg_app):
    from rcg.gui.theme import tokens

    for palette in (QPalette(rcg_app.palette()), dark_palette()):
        t = tokens(palette)
        states = {
            t.accent,
            t.accent_button,
            t.accent_hover,
            t.accent_pressed,
            t.accent_disabled,
            t.accent_soft,
            t.input_border,
            t.border,
            t.hover,
            t.pressed,
            t.card,
        }
        assert t.focus not in states, (t.dark, t.focus)
        # The primary button's ring (on_accent) differs from every fill the button can have.
        assert t.on_accent not in {t.accent_button, t.accent_hover, t.accent_pressed, t.accent_disabled}


def test_keyboard_focus_is_visible_on_add_and_radio(qtbot, window, model_copy, screenshot_dirs):
    from rcg.gui import theme

    window.path_field.set_path(model_copy)
    window.activateWindow()
    sheet = QApplication.instance().styleSheet()
    focus = theme.current_tokens().focus
    assert f"QRadioButton:focus {{ border-color: {focus}; }}" in sheet

    window.add_button.setFocus(Qt.FocusReason.TabFocusReason)
    qtbot.waitUntil(window.add_button.hasFocus, timeout=2_000)
    assert window.add_button.focus_ring_visible()
    save_screenshot(window, screenshot_dirs, "rcg-gui-focus-add.png")

    assert window.in_place_radio.isChecked()
    window.in_place_radio.setFocus(Qt.FocusReason.TabFocusReason)
    qtbot.waitUntil(window.in_place_radio.hasFocus, timeout=2_000)
    assert not window.add_button.focus_ring_visible()
    save_screenshot(window, screenshot_dirs, "rcg-gui-focus-radio.png")


# --------------------------------------------------------------------------- 6 + 12. infiltration, model summary
def test_infiltration_row_and_summary_follow_the_model(qtbot, window, model_copy, us_model, screenshot_dirs):
    from rcg.gui.widgets.path_field import US_UNITS_NOTE, format_size
    from rcg.gui.widgets.preview import NO_MODEL_INFILTRATION_NOTE

    panel = window.preview
    green_ampt = list(infiltration_for("GREEN_AMPT"))[: len(INFILTRATION_FIELDS["GREEN_AMPT"])]

    # No model: the Green-Ampt row, no units (they depend on the model), and a muted note.
    assert window.path_field.path() is None
    assert list(panel.infiltration_text()) == green_ampt
    assert list(panel.infiltration_text().values()) == ["3.5", "0.5", "0.25"]
    assert panel.infiltration_note.full_text() == NO_MODEL_INFILTRATION_NOTE
    assert panel.infiltration_note.property("role") == "caption"

    # SI model (CMS, MODIFIED_GREEN_AMPT): SI units, summary line from inspect().
    window.path_field.set_path(model_copy)
    assert panel.infiltration_text() == {"Suction": "3.5 mm", "Ksat": "0.5 mm/h", "IMD": "0.25"}
    size = format_size(model_copy.stat().st_size)
    assert window.path_field.message.full_text() == f"15 subcatchments · CMS · Modified Green-Ampt · {size}"
    assert window.path_field.detail.full_text().startswith("Rain gage ")

    # US model (CFS, HORTON): the Horton fields, US units and the conversion note.
    window.path_field.set_path(us_model)
    assert panel.infiltration_text() == {
        "MaxRate": "3 in/h",
        "MinRate": "0.5 in/h",
        "Decay": "4 1/h",
        "DryTime": "7 days",
        "MaxInfil": "0 in",
    }
    assert "Horton" in panel.infiltration_note.full_text()
    assert window.path_field.message.full_text().startswith("15 subcatchments · CFS · Horton · ")
    assert window.path_field.detail.full_text() == US_UNITS_NOTE
    assert window.path_field.detail.property("role") == "caption"
    for name in ("MaxRate", "DryTime"):
        assert name in "".join(cell.toolTip() for cell in panel.infiltration_row.headers)

    # No file names (configuration files, module names) in user-facing text.
    for text in _visible_texts(window):
        assert ".json" not in text and ".py" not in text, text

    select(window.cover_combo, LandCover.urban_highly_impervious)
    window.area_spin.setValue(5.5)
    qtbot.waitUntil(lambda: window.current_parameters() is not None, timeout=PREVIEW_TIMEOUT_MS)
    save_screenshot(window, screenshot_dirs, "rcg-gui-us-units.png")


# --------------------------------------------------------------------------- 7. stable minimum size
def test_minimum_size_is_stable_from_construction(qtbot, rcg_app, gui_settings, gui_engine, model_copy, us_model):
    from rcg.gui.main_window import MainWindow

    win = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(win)
    win.show()
    assert win.preview.is_preparing(), "measured before the engine thread has even started"
    start, start_preview = win.minimumSizeHint(), win.preview.minimumSizeHint()
    assert 860 <= start.width() <= 900, start
    assert start.height() >= 560

    qtbot.waitUntil(lambda: win.engine_ready, timeout=ENGINE_TIMEOUT_MS)
    qtbot.waitUntil(lambda: win.current_parameters() is not None, timeout=PREVIEW_TIMEOUT_MS)
    QApplication.processEvents()
    assert (win.minimumSizeHint(), win.preview.minimumSizeHint()) == (start, start_preview), "after warm-up"

    for path in (model_copy, us_model):
        win.path_field.set_path(path)
        QApplication.processEvents()
        assert (win.minimumSizeHint(), win.preview.minimumSizeHint()) == (start, start_preview), path.name

    win.area_spin.setValue(10_000)  # the widest width value (5000 m)
    select(win.form_combo, LandForm.highest_mountains)
    qtbot.waitUntil(lambda: (p := win.current_parameters()) is not None and p.area_ha == 10_000, timeout=10_000)
    QApplication.processEvents()
    assert (win.minimumSizeHint(), win.preview.minimumSizeHint()) == (start, start_preview), "large values"

    win.flash_status("Added S99. Now editing a_copy_with_a_rather_long_file_name_for_the_status.inp")
    QApplication.processEvents()
    assert win.minimumSizeHint() == start, "a longer status message"


# --------------------------------------------------------------------------- 9. SWMM wording
def test_zero_storage_row_uses_swmm_wording(window):
    texts = _visible_texts(window)
    assert not any("Without storage" in text for text in texts)
    zero = next(lbl for lbl in window.preview.findChildren(QLabel) if lbl.text() == "Zero-storage share")
    assert "%Zero-Imperv" in zero.toolTip()
    assert window.preview.pct_zero.toolTip() == "SWMM: %Zero-Imperv"


# --------------------------------------------------------------------------- 10. pending add
def test_pending_add_uses_the_inputs_of_the_click(qtbot, window, model_copy):
    window.path_field.set_path(model_copy)
    before = set(subcatchment_ids(model_copy))
    select(window.cover_combo, LandCover.forests)
    window.area_spin.setValue(7.77)
    # Clicked before the debounced preview for 7.77 ha has even been requested ...
    qtbot.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
    assert window.busy
    # ... and the inputs change while the subcatchment is computed and written.
    window.area_spin.setValue(8.88)
    select(window.cover_combo, LandCover.urban_highly_impervious)
    qtbot.waitUntil(lambda: not window.busy and bool(window.history.entries), timeout=APPLY_TIMEOUT_MS)

    entry = window.history.entries[0]
    assert entry.area_ha == pytest.approx(7.77)
    (new_id,) = set(subcatchment_ids(model_copy)) - before
    assert subcatchment_areas(model_copy)[new_id] == pytest.approx(7.77)
    qtbot.waitUntil(lambda: window.current_parameters() is not None, timeout=PREVIEW_TIMEOUT_MS)
    assert window.current_parameters().area_ha == pytest.approx(8.88), "the preview follows the new inputs"


# --------------------------------------------------------------------------- 11. theme cache file
def test_chevron_is_written_to_the_per_user_cache(tmp_path, monkeypatch):
    from rcg.gui import theme

    monkeypatch.setattr(theme, "_cache_dir", lambda: tmp_path / "cache" / "rcg")
    path = theme._chevron_svg("#123456")
    assert path == tmp_path / "cache" / "rcg" / "theme" / "chevron-123456.svg"
    assert 'stroke="#123456"' in path.read_text()
    assert not list(path.parent.glob("*.tmp")), "written atomically"


def test_chevron_falls_back_when_the_cache_is_not_writable(tmp_path, monkeypatch, rcg_app):
    from rcg.gui import theme

    blocker = tmp_path / "not-a-folder"
    blocker.write_text("")
    monkeypatch.setattr(theme, "_cache_dir", lambda: blocker / "rcg")
    assert theme._chevron_svg("#654321") is None
    assert "url(" not in theme.stylesheet(theme.tokens(rcg_app.palette()), 13.0)


def test_cache_dir_is_per_user_and_named_rcg():
    from rcg.gui import theme

    folder = theme._cache_dir()
    assert folder is None or folder.name == "rcg"


# --------------------------------------------------------------------------- 13. category texts
def test_categories_docstring_credits_the_readme_only_where_it_applies():
    import rcg.gui.categories as categories

    doc = categories.__doc__ or ""
    assert "Only some descriptions are" in doc and "first nine land covers" in doc
    assert "rural" in doc


# --------------------------------------------------------------------------- 16. CI must not skip
def test_missing_gui_dependency_fails_when_required(gui_requirements):
    check = gui_requirements
    assert check.gui_tests_required({"RCG_REQUIRE_GUI_TESTS": "1"})
    assert check.gui_tests_required({"RCG_REQUIRE_GUI_TESTS": "true"})
    for value in ("", "0", "false", "no"):
        assert not check.gui_tests_required({"RCG_REQUIRE_GUI_TESTS": value})
    assert not check.gui_tests_required({})

    with pytest.raises(pytest.fail.Exception, match="RCG_REQUIRE_GUI_TESTS"):
        check.require_module("rcg_no_such_gui_dependency", required=True)
    with pytest.raises(pytest.skip.Exception):
        check.require_module("rcg_no_such_gui_dependency", required=False)
    assert check.require_module("PySide6", required=True).__name__ == "PySide6"


# --------------------------------------------------------------------------- lazy heavy imports
def test_window_construction_does_not_load_the_fuzzy_stack(tmp_path):
    """skfuzzy and matplotlib are only imported by the engine worker, never on the GUI thread."""
    script = f"""
import json, sys
from PySide6.QtCore import QSettings
from rcg.gui.app import create_application
from rcg.gui.main_window import MainWindow

app = create_application(["rcg-gui"])
window = MainWindow(QSettings({str(tmp_path / "s.ini")!r}, QSettings.Format.IniFormat))
window.show()
loaded = {{name: name in sys.modules for name in ("skfuzzy", "matplotlib", "rcg.fuzzy.engine")}}
window.close()
print(json.dumps(loaded))
"""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": str(REPO_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=REPO_ROOT, timeout=120
    )
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stdout.strip().splitlines()[-1])
    assert loaded == {"skfuzzy": False, "matplotlib": False, "rcg.fuzzy.engine": False}


def test_settings_are_untouched_by_the_automatic_copy_switch_across_sessions(
    qtbot, rcg_app, gui_engine, gui_settings: QSettings, model_copy, monkeypatch
):
    """Restarting after a copy keeps the user's choice ("copy"), not the automatic switch."""
    from rcg.gui.main_window import MainWindow

    first = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(first)
    first.show()
    qtbot.waitUntil(lambda: first.engine_ready, timeout=ENGINE_TIMEOUT_MS)
    monkeypatch.setattr(first, "_choose_output_path", lambda source: model_copy.with_name("copy.inp"))
    first.copy_radio.setChecked(True)
    first.path_field.set_path(model_copy)
    add_and_wait(qtbot, first)
    assert first.in_place_radio.isChecked()
    first.close()

    second = MainWindow(gui_settings, engine=gui_engine)
    qtbot.addWidget(second)
    assert second.copy_radio.isChecked()
