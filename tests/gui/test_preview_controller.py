"""PreviewController without a window: warm-up, cache, pinned requests, lifecycle."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from gui_helpers import ENGINE_TIMEOUT_MS, PREVIEW_TIMEOUT_MS

from rcg.fuzzy.categories import LandCover, LandForm

FORM, OTHER_FORM = list(LandForm)[:2]
COVER = list(LandCover)[0]


class Inputs:
    """Stands in for the window's widgets: the key the controller asks for."""

    def __init__(self, area: float = 1.0, form: LandForm = FORM) -> None:
        self.key = (area, form, COVER)

    def __call__(self):
        return self.key


@pytest.fixture
def inputs() -> Inputs:
    return Inputs()


@pytest.fixture
def controller(qtbot, rcg_app, gui_engine, inputs) -> Iterator:
    """A started controller whose engine is ready and whose first preview has been shown."""
    from rcg.gui.preview_controller import PreviewController

    ctrl = PreviewController(inputs, engine=gui_engine)
    with qtbot.waitSignal(ctrl.previewReady, timeout=ENGINE_TIMEOUT_MS):
        ctrl.start()
    yield ctrl
    ctrl.shutdown()


def test_the_first_preview_follows_the_warm_up(controller, inputs):
    assert controller.ready and not controller.failed
    params = controller.parameters_for(inputs.key)
    assert params is not None and params.area_ha == pytest.approx(1.0)


def test_cached_inputs_are_shown_without_recomputing(qtbot, controller, inputs):
    first = inputs.key
    computed: list[int] = []
    controller._worker.previewReady.connect(lambda rid, _params: computed.append(rid))

    inputs.key = (2.0, FORM, COVER)
    with qtbot.waitSignal(controller.previewReady, timeout=PREVIEW_TIMEOUT_MS):
        controller.request()
    assert len(computed) == 1

    shown: list[tuple] = []
    controller.previewReady.connect(lambda key, params: shown.append((key, params)))
    inputs.key = first
    controller.request()  # answered from the cache, synchronously
    assert [key for key, _ in shown] == [first]
    assert len(computed) == 1
    assert controller.parameters_for(first) is shown[0][1]


def test_a_pinned_request_is_answered_even_when_newer_inputs_follow(qtbot, controller, inputs):
    pinned_key = (3.0, FORM, COVER)
    pinned: list[tuple] = []
    controller.pinnedReady.connect(lambda rid, params: pinned.append((rid, params)))
    with qtbot.waitSignal(controller.previewReady, timeout=PREVIEW_TIMEOUT_MS):
        request_id = controller.pin(pinned_key)
        inputs.key = (4.0, OTHER_FORM, COVER)
        controller.request()
    qtbot.waitUntil(lambda: bool(pinned), timeout=PREVIEW_TIMEOUT_MS)

    assert [rid for rid, _ in pinned] == [request_id]
    assert pinned[0][1].area_ha == pytest.approx(3.0)
    assert controller.lookup(pinned_key) is pinned[0][1]  # cached, though never shown
    assert controller.parameters_for(pinned_key) is None
    assert controller.parameters_for(inputs.key).area_ha == pytest.approx(4.0)


def test_lookup_knows_cached_and_shown_inputs_only(controller, inputs):
    assert controller.lookup(inputs.key) is controller.parameters_for(inputs.key)
    assert controller.lookup((9.0, FORM, COVER)) is None


def test_the_cache_drops_the_oldest_entry_at_its_limit(controller, monkeypatch):
    from rcg.gui import preview_controller

    monkeypatch.setattr(preview_controller, "_CACHE_LIMIT", 2)
    params = controller.parameters_for(controller._inputs())
    controller._cache.clear()
    keys = [(area, FORM, COVER) for area in (10.0, 11.0, 12.0)]
    for key in keys:
        controller._remember(key, params)
    assert list(controller._cache) == keys[1:]


def test_newer_requests_supersede_queued_ones(controller):
    first = controller._supersede()
    second = controller._supersede()
    assert second == first + 1
    assert controller._worker._is_stale(first) and not controller._worker._is_stale(second)


def test_nothing_is_requested_before_the_engine_is_ready(qtbot, rcg_app, gui_engine, inputs):
    from rcg.gui.preview_controller import PreviewController

    ctrl = PreviewController(inputs, engine=gui_engine)
    shown: list[object] = []
    ctrl.previewReady.connect(shown.append)
    ctrl.request()
    ctrl.close()  # a closed controller never starts its thread
    ctrl.start()
    qtbot.wait(50)
    assert not ctrl.ready and not ctrl.thread_running() and shown == []
    ctrl.shutdown()
