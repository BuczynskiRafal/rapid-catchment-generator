# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `rcg.restore(backup_path, target_path, expected_sha256=None)` undoes an apply from its backup. With
  `expected_sha256` it refuses (and keeps the file) when the model was edited after RCG wrote it. The desktop app's Undo
  uses it. A refused or failed restore raises `BackupError`.
- `ApplyResult.written_sha256`: SHA-256 of the bytes written, also in `to_dict()` and `rcg add --json`.
- Backup handling lives in `rcg.inp_manage.backups`; `rcg.inp_manage.writer.create_backup` and `BACKUP_DIR_NAME` are
  still importable from the writer.
- `rcg.catchment.is_metric(flow_units)` tells whether a model takes SI values.

### Changed
- Desktop app layout: the SWMM model card spans the window; the inputs and the preview sit side by side at equal height,
  with *Add subcatchment* at the bottom of the inputs card; the history spans the window below and takes any extra
  height, so no empty gaps open up when the window grows. The header shows the application icon.
- New application icon (a water drop over layered terrain), drawn as a vector source (`rcg/gui/resources/icon.svg`);
  `packaging/make_icons.py` renders `icon.png` and a multi-size `icon.ico` from it.
- The fuzzy rules are defined as one table, `rcg.fuzzy.rule_definitions.RULE_TABLE` (a row per land cover and output
  combination). `define_all_rules` accepts another table and raises `RuleDefinitionError` when it misses or repeats a
  land cover x land form pair. Rule names follow the pair (`<land_cover>_on_<land_form>`); the results are unchanged.
- Malformed fuzzy rules raise `RuleDefinitionError` naming the rule (an unknown output such as a misspelt `slope=` is
  no longer dropped silently), and out-of-range inputs to `FuzzyEngine` raise `FuzzyEngineError`. Both exceptions also
  derive from `ValueError`, which 2.0.0 raised in these cases.
- `rcg.inp_manage.writer.append_subcatchments` called with no parameters raises `ValidationError` ("At least one
  subcatchment is required"), the same error as `rcg.apply`, instead of `ModelOperationError`. Parameters are validated
  once per apply instead of twice.
- Logging: the CLI and the desktop app both configure it through `rcg.logging_config.setup_logging`, which gained
  `console_level` and `propagate` arguments, replaces only the handlers it installed when called again, writes to the
  current `sys.stderr` and opens the log file before changing anything. `log_file_path()` returns the file in use.
  `rcg -v` now shows RCG's debug messages only (it configures the `rcg` logger, not the root logger).
- Desktop app: the area field's upper limit (and the range shown under it) follows `validation_limits.area_max_hectares` in
  `defaults.json` instead of a separate hard-coded value. A model opened with the app or dropped on the window also
  focuses the path field.

### Deprecated
- `rcg.fuzzy.engine.create_fuzzy_engine`: call `FuzzyEngine(...)` directly.
- The 1.x aliases in `rcg.fuzzy.categories` (`land_form`, `land_cover`, `slope_ctgr`, `impervious_ctgr`,
  `catchment_ctgr`): use the enum classes. Both still work and emit a `DeprecationWarning`.

## [2.0.0]

A rewrite around one service layer (`rcg.preview` / `rcg.apply`) that the CLI, the desktop app and the Python API all
share. The fuzzy rules, membership functions and `defaults.json` values are unchanged, with the one exception
listed under "Changed".

### Added
- New desktop app built with PySide6 (`rcg-gui`, `python -m rcg.gui`): a single window with live preview, drag and
  drop of `.inp` files, update in place or save as a copy, a history list with Undo and Show in folder, light and dark
  themes, keyboard shortcuts and built-in help. Install with `pip install ".[gui]"`.
- Command line rewritten: `rcg add`, `rcg preview`, `rcg inspect`, `rcg list-options`, with `--json` output,
  `--output`, `--no-backup`, documented exit codes (0 ok, 2 usage/validation, 1 failure) and `python -m rcg`.
- Public Python API: `rcg.preview`, `rcg.apply`, `rcg.inspect`, `rcg.warm_up`, `SubcatchmentParameters`,
  `ApplyResult` and `ModelInfo`. The package ships type information (`py.typed`).
- Category arguments are case-insensitive and accept snake_case names as well as the human labels.
- `rcg inspect MODEL.inp [--json]` and `rcg.inspect()` summarise a model (flow units, infiltration method, subcatchment
  count, rain gage and outlet) without changing it. `--json` floats are rounded to 4 decimals, and `add --json` reports
  `flow_units` and `infiltration_method`.
- Safety checks before writing: read-only targets, non-SWMM files (EPANET, UTF-16/32, binary) and unknown `FLOW_UNITS` or
  `INFILTRATION` values are refused; a lost-update guard re-reads the source and writes nothing if it changed; symbolic
  links are resolved so the real file is updated and the link kept; an existing `--output` file is backed up too.
- Several subcatchments can be added in one call with a single read and a single atomic write.
- Timestamped backups in `.rcg_backups/` next to the model, also from the GUI.
- Test suite in `tests/` (golden test for all 126 land form x land cover combinations, writer, CLI, end-to-end runs in
  SWMM with pyswmm, headless GUI tests), CI on Linux, Windows and macOS with Python 3.10-3.13, and PyInstaller specs in
  `packaging/` for the desktop app and the CLI.
- Sphinx API documentation for the new modules.

### Changed
- Python 3.10 or newer is required.
- Heavy initialisation (building the fuzzy engine) is deferred to first use; the GUI does it in a background thread.
- Models are written by editing the file text directly: untouched content is preserved, section headers are matched
  case-insensitively, and the result replaces the target atomically.
- **Intentional numerical change:** the duplicate fuzzy rule for `mountains_vegetated` x
  `hills_and_outcrops_of_mountain_ranges` was removed. The slope for that single combination is now 14.33 instead of
  12.16. All other combinations are unchanged and pinned by the golden test.
- Table 4 in the README documents the actual width formula, `sqrt(area_m2) / 2`.
- The README land cover table uses the 14 labels shown in the app (the five categories rural, forests, meadows,
  arable and marshes are now described).

### Fixed
- A duplicate `[POLYGONS]` section was appended when the model spelled the header differently from `[Polygons]`.
- The `[RAINGAGES]` table was overwritten when a rain gage had to be added.
- Models were rewritten four times, non-atomically, so a failure could leave a half-written file; there is now one
  atomic write.
- The GUI made no backup of the model before changing it.
- The hourly design-storm series was bound to a rain gage with a 1-minute interval.
- A Green-Ampt infiltration row was written regardless of the infiltration method of the model. The row now follows
  `INFILTRATION`: Green-Ampt / Modified Green-Ampt keep `3.5 0.5 0.25 7 0`, Horton / Modified Horton get `3 0.5 4 7 0`, and
  Curve Number gets `80 0.5 7` (defaults in `defaults.json`, `infiltration_defaults`).
- SI values were written into models that use US units; such models (`CFS`, `GPM`, `MGD`) now receive the area in acres
  (x 2.4710538), the width in feet (x 3.2808399) and depression storage in inches (/ 25.4). Infiltration values and
  polygon coordinates are not converted.
- The generated rain gage `RG1` now uses a 1:00 interval (or the interval of the existing time series) instead of 0:01.
- A subcatchment area below 0.0001 ha, which could be written as `0`, is rejected; the maximum stays 10 000 ha.
- An enum conversion bug (fixed just before the rewrite).

### Deprecated
- `rcg.inp_manage.inp.BuildCatchments` is a thin facade over the new service and will be removed in a future release.

### Removed
- `rcg.runner` and `rcg.interfaces`.
- The Tkinter GUI (`gui/`), `main.py` and `setup.py` (packaging is configured in `pyproject.toml`).
- The stale `rcg/config/rules.json`; rules live only in `rcg/fuzzy/rule_definitions.py`.
- The `RCG.exe` download from the repository; desktop builds are published as GitHub Releases assets.
- Tests inside the package (moved to `tests/`).

[2.0.0]: https://github.com/BuczynskiRafal/rapid-catchment-generator/releases/tag/v2.0.0
