# Contributing Guide

Thank you for considering a contribution to Rapid Catchment Generator. This guide covers how to set up a
development environment, run the checks that CI runs, and build the desktop app.

## Reporting bugs and requesting features

Please open an issue in the [issue tracker](https://github.com/BuczynskiRafal/rapid-catchment-generator/issues) with
steps to reproduce, expected and actual behaviour, any error output, and (when relevant) the SWMM `.inp` file you used.

## Development setup

RCG requires Python 3.10 or newer. You can set up the environment with [`uv`](https://docs.astral.sh/uv/) (used in CI)
or with a standard `venv`:

```bash
git clone https://github.com/BuczynskiRafal/rapid-catchment-generator
cd rapid-catchment-generator

# With uv (recommended):
uv sync --extra dev --extra gui --extra docs

# Or with standard venv + pip:
python3 -m venv venv
venv/bin/pip install -e ".[dev,gui,docs]"
```

The `dev` extra brings `pytest`, `pytest-cov`, `pytest-mock`, `pytest-qt`, `pyswmm` (used by the end-to-end tests to
run written models in SWMM), `mypy`, and `ruff`. The `gui` extra brings `PySide6`, and `docs` brings `sphinx` and
`sphinx-rtd-theme`.

Numbers are frozen: the fuzzy rules, membership functions, and `rcg/config/defaults.json` must not change unless that is
the explicit goal of the pull request (see the golden test below).

## Tests

```bash
uv run pytest                                                   # full suite
uv run pytest tests/test_golden.py                              # numerical regression only
QT_QPA_PLATFORM=offscreen uv run pytest tests/gui               # GUI tests, headless
uv run pytest --cov=rcg --cov-report=term-missing               # with coverage
```

*(If using `venv` instead of `uv`, replace `uv run` with `venv/bin/python -m`.)*

On Linux the headless GUI tests need a few system libraries
(`libegl1 libgl1 libxkbcommon0 libfontconfig1 libdbus-1-3 libxcb-cursor0`). GUI tests are skipped when `PySide6` or
`pytest-qt` is not installed (unless `RCG_REQUIRE_GUI_TESTS=1` is set, as in CI).

**Golden test.** `tests/test_golden.py` compares slope, imperviousness, catchment type, Manning coefficients, and
depression storage for all 126 land form × land cover combinations (and the width formula) against
`tests/golden/fuzzy_outcomes.json`. A failure means the numbers changed. There is no automatic update switch: a changed
number must be a deliberate edit. Regenerate `tests/golden/fuzzy_outcomes.json` from the engine
(`FuzzyEngine.compute_all` for every combination, keeping the existing structure of the file), review the diff line by
line, and explain the rationale in the pull request description.

## Code style and type checking

```bash
uv run ruff check .
uv run ruff format --check .      # drop --check to apply formatting
uv run mypy rcg
```

All three run in CI and must pass. Library code must not use `print`; log through `rcg.logging_config.get_logger`.

## Documentation

Update `README.md`, `docs/source/`, and the docstrings (NumPy style) when behaviour or public API changes. The
documentation is built with Sphinx using `-W --keep-going` so any warning fails the check:

```bash
uv run python -m sphinx -W --keep-going -E -b html docs/source docs/_build/html
```

## Building the desktop app

Builds use [PyInstaller](https://pyinstaller.org/) and must be run on the target operating system, from the repository
root, in an environment with the `gui` extra installed:

```bash
uv pip install pyinstaller pillow
uv run pyinstaller packaging/rcg-gui.spec                      # desktop app -> dist/RCG.exe, dist/RCG.app or dist/RCG
uv run pyinstaller packaging/rcg.spec --distpath dist-cli      # command-line tool -> dist-cli/rcg[.exe]
```

See the docstring at the top of each spec file for options (for example `RCG_ONEDIR=1` for a folder build on Windows and
Linux). The `build` job in `.github/workflows/rcg.yaml` produces the same artifacts on tags named `v*` or when started
manually.

## Submitting a pull request

1. Fork the repository and create a branch with a descriptive name.
2. Make your change, with tests for new or changed behaviour.
3. Run `pytest`, `ruff`, `mypy`, and the Sphinx build as described above.
4. Push the branch and open a pull request that explains what changed and why.

Thank you for helping to make this project better.
