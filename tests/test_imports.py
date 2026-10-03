"""Importing ``rcg`` must stay cheap: the fuzzy stack loads only when it is needed."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXAMPLE_INP = Path(__file__).resolve().parent.parent / "rcg" / "example.inp"
HEAVY = ("skfuzzy", "matplotlib", "scipy", "networkx")


def _run(code: str) -> None:
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr


def test_import_rcg_and_service_does_not_load_the_fuzzy_stack():
    _run(
        "import rcg, rcg.service, rcg.cli, sys\n"
        f"loaded = [m for m in {HEAVY!r} if m in sys.modules]\n"
        "assert not loaded, loaded\n"
    )


def test_inspect_does_not_load_the_fuzzy_stack():
    _run(
        "import rcg, sys\n"
        f"info = rcg.inspect({str(EXAMPLE_INP)!r})\n"
        "assert info.subcatchment_count == 15\n"
        "assert rcg.ModelInfo is type(info)\n"
        f"loaded = [m for m in {HEAVY!r} if m in sys.modules]\n"
        "assert not loaded, loaded\n"
    )


def test_engine_selects_a_non_gui_matplotlib_backend():
    # scikit-fuzzy treats matplotlib as optional, so it may be absent; the env var
    # is our contract, the live backend is checked only when matplotlib exists.
    _run(
        "import os\n"
        "os.environ.pop('MPLBACKEND', None)\n"
        "import rcg.fuzzy.engine\n"
        "assert os.environ['MPLBACKEND'] == 'Agg'\n"
        "try:\n"
        "    import matplotlib\n"
        "except ImportError:\n"
        "    pass\n"
        "else:\n"
        "    assert matplotlib.get_backend().lower() == 'agg', matplotlib.get_backend()\n"
    )
