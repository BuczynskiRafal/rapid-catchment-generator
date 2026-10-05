# Rapid Catchment Generator 2.0 — design brief

This document is the contract for the 2.0 rewrite. The user-facing value stays exactly
what it is today: *pick a land form, pick a land cover, type an area, point at a SWMM
`.inp` file, press one button, get a correctly parameterised subcatchment appended to the
model.* Everything below exists to make that one flow robust, pleasant and verifiable.

## Non-negotiables

1. **Numbers are frozen.** `tests/test_golden.py` pins slope / imperviousness / catchment
   type / Manning / depression storage for all 126 land-form × land-cover combinations
   and the width formula. It must stay green. The fuzzy rule set, memberships and
   `defaults.json` values do not change in this rewrite, except for the deliberate
   changes listed under [Numerical changes vs 1.x](#numerical-changes-vs-1x).
2. **Never corrupt the user's model.** Writing is: load once → edit in memory → write a
   complete file to a temporary path next to the target → `os.replace`. A timestamped
   backup of whatever file is about to be overwritten (the source, or an existing
   output file) is created *before* the replace unless the caller opts out. Writing to
   a different output path leaves the source untouched.
3. **Python ≥ 3.10.** The `gui` extra needs PySide6 (wheels exist for 3.10–3.14).
4. **One source of truth per concept.** `defaults.json` is canonical for Manning /
   depression storage / infiltration / validation limits. Rules live only in
   `rcg/fuzzy/rule_definitions.py` (`rules.json` is stale and goes away).
5. **No prints in library code.** Use `logging` via `rcg.logging_config.get_logger`.
6. **`import rcg` is cheap.** `rcg/__init__.py` resolves its public names lazily
   (PEP 562) and `rcg.service` imports the fuzzy engine only inside `preview` /
   `apply` / `warm_up`, so `import rcg`, `import rcg.service` and `rcg.inspect()`
   never load scikit-fuzzy or matplotlib (`tests/test_imports.py`). The engine sets
   `MPLBACKEND=Agg` (if unset) before importing scikit-fuzzy.

## Numerical changes vs 1.x

* **Duplicated rule removed.** 1.x defined `mountains_vegetated × hills_and_outcrops_of_mountain_ranges`
  twice — once in its "Rule 3" loop (slope term `steeper_hills_and_foothills`) and once
  as "Rule 4" (slope term `hills_and_outcrops_of_mountain_ranges`) — so the two rules
  were OR-ed. 2.0 keeps only Rule 4: the rule set has exactly one rule per combination
  (126). For that one combination the slope is **14.333 %** instead of 1.x's 12.164 %;
  imperviousness, catchment score/type and all other combinations are unchanged.
  `tests/golden/fuzzy_outcomes.json` holds the 2.0 value and
  `tests/test_golden.py::test_rule_set_has_one_rule_per_combination` guards it.
* **Units follow the model.** 1.x always wrote hectares, metres and millimetres. 2.0
  reads `FLOW_UNITS` (SWMM default `CFS`) and, for US models (`CFS`/`GPM`/`MGD`), writes
  the area in acres (× 2.4710538), the width in feet (× 3.2808399, rounded to 2 dp) and
  depression storage in inches (÷ 25.4). SI models are written exactly as before.
* **Infiltration row follows the model's method.** 1.x always wrote the Green-Ampt row
  (`3.5 0.5 0.25 7 0`). 2.0 writes it for `GREEN_AMPT`/`MODIFIED_GREEN_AMPT` models
  (byte-identical), `3 0.5 4 7 0` (MaxRate, MinRate, Decay, DryTime, MaxInfil) for
  `HORTON`/`MODIFIED_HORTON` (also SWMM's default when `INFILTRATION` is absent) and
  `80 0.5 7` (CurveNum, conductivity — deprecated since SWMM 5.1, a 0.5 placeholder —
  DryTime) for `CURVE_NUMBER`. These values live in `defaults.json`
  (`infiltration_defaults`, keyed by method) and are written in the model's units
  without conversion.
* **Generated rain gage is hourly.** 1.x created `RG1` with interval `0:01` for the hourly
  `generator_series` (SWMM Warning 09). 2.0 uses `1:00`; for an existing series the
  interval is the spacing of its first two values, or `1:00` if that cannot be parsed.
* **Smallest area.** Areas below 0.0001 ha are rejected so the six-decimal writer never
  writes `0`; values below 1 are written with six significant digits.

## Package layout (target)

```
rcg/
  __init__.py          # lazy public API: preview, apply, inspect, warm_up, SubcatchmentParameters,
                       #   ApplyResult, ModelInfo, LandForm, LandCover, __version__
  __main__.py          # `python -m rcg` == CLI
  cli.py               # argparse, subcommands: add | preview | inspect | list-options
  service.py           # preview() / apply() / inspect() — the only module CLI and GUI call into
  catchment.py         # SubcatchmentParameters, ApplyResult, ModelInfo, width formula, label helpers,
                       #   SWMM units, INFILTRATION_FIELDS / infiltration_for()
  validation.py        # validate_area / validate_land_form / validate_land_cover / validate_inp_path /
                       #   validate_parameters
  exceptions.py        # RCGError, ValidationError, ModelOperationError, ConfigurationError
  logging_config.py
  config/
    __init__.py, loader.py, defaults.json        # loader simplified (no singleton), rules.json removed
  fuzzy/
    categories.py, memberships.py, rule_engine.py, rule_definitions.py, engine.py
  inp_manage/
    __init__.py, writer.py                        # text-level section editing, swmmio verification, atomic save
    inp.py                                        # thin deprecated facade: BuildCatchments.add_subcatchment -> service
  gui/
    __init__.py, __main__.py, app.py, main_window.py, widgets/..., resources/ (icon, help.md), theme.py
tests/
  conftest.py, test_golden.py, golden/fuzzy_outcomes.json
  test_service.py, test_writer.py, test_validation.py, test_cli.py, fuzzy/..., gui/test_gui_smoke.py
packaging/
  rcg-gui.spec, rcg.spec                           # PyInstaller: windowed GUI / console CLI, datas wired
```

Delete: `gui/` (old Tk app), `rcg/runner.py`, `rcg/interfaces.py`, `rcg/config/rules.json`,
`setup.py`, `main.py`, root `*.spec`, `RCG.exe` LFS pointer stays (release asset, out of scope),
in-package `test_*` folders (moved to `tests/`).

## Service contract (`rcg/service.py`)

```python
@dataclass(frozen=True)
class SubcatchmentParameters:
    land_form: LandForm
    land_cover: LandCover
    area_ha: float
    slope_pct: float  # fuzzy slope result, rounded to 2 dp when written
    impervious_pct: float  # fuzzy impervious result, rounded to 2 dp when written
    catchment_score: float  # raw fuzzy catchment output (0-100)
    catchment_type: str  # linguistic label: urban|suburban|rural|forests|meadows|arable|mountains
    width_m: float  # round(sqrt(area_ha*10_000)/2, 2)
    n_imperv: float
    n_perv: float
    s_imperv_mm: float  # defaults.json inches * 25.4
    s_perv_mm: float
    pct_zero: int
    infiltration: Mapping[str, float]  # Suction, Ksat, IMD, Param4, Param5 (Green-Ampt, from defaults.json)


def preview(
    area_ha: float, land_form: LandForm | str, land_cover: LandCover | str, *, engine: FuzzyEngine | None = None
) -> SubcatchmentParameters:
    ...
    # pure; validates inputs; raises rcg.exceptions.ValidationError


@dataclass(frozen=True)
class ApplyResult:
    output_path: Path  # resolved (symlinks followed)
    backup_path: Path | None  # copy of the overwritten file (source or existing output)
    subcatchment_ids: tuple[str, ...]
    raingage: str
    outlet: str
    flow_units: str = "CMS"  # model FLOW_UNITS (US units => acres/feet/inches written)
    infiltration_method: str = "GREEN_AMPT"  # model INFILTRATION option


def apply(
    inp_path: str | Path,
    parameters: Sequence[SubcatchmentParameters] | SubcatchmentParameters,
    *,
    output_path: str | Path | None = None,
    backup: bool = True,
) -> ApplyResult:
    ...
    # one read, in-memory edits, one atomic write; validates every written value
    # (ValidationError); raises ModelOperationError (not SWMM, read-only, changed meanwhile, ...)


@dataclass(frozen=True)
class ModelInfo:
    path: Path  # resolved
    flow_units: str  # FLOW_UNITS, "CFS" when absent
    is_metric: bool  # CMS / LPS / MLD
    infiltration_method: str  # INFILTRATION, "HORTON" when absent
    subcatchment_count: int
    raingage: str | None  # gage apply() would use; None => it would create RG1
    outlet: str | None  # outlet apply() would use; None => subcatchment drains to itself
    size_bytes: int


def inspect(inp_path: str | Path) -> ModelInfo:
    ...
    # read-only, fast (no fuzzy engine); same parser and structural check as apply();
    # raises ValidationError / ModelOperationError


# rcg.catchment
INFILTRATION_FIELDS: dict[str, tuple[tuple[str, str, str], ...]]


# method -> ((label, SI unit, US unit), ...) labelling the leading values of infiltration_for()
def infiltration_for(method: str) -> dict[str, float]:
    ...
    # ordered [INFILTRATION] row for a method (from defaults.json); MODIFIED_* share the base row


def warm_up(engine: FuzzyEngine | None = None) -> FuzzyEngine:
    ...
    # builds the default engine (≈ seconds); GUI calls it from a worker thread
```

Writer behaviour (`rcg/inp_manage/writer.py`), preserved from 1.x unless noted:

* Paths: source and target are resolved with `os.path.realpath` first, so a symlinked
  model is updated where it lives (the link survives) and backups go next to the real file.
* Structural check (also used by `inspect`): no UTF-16/32 byte order mark, no NUL bytes,
  at least one SWMM section header, and not EPANET (EPANET-only sections such as
  `[PIPES]`/`[RESERVOIRS]`/`[TANKS]`, or `[JUNCTIONS]` with `[PATTERNS]`, without any SWMM-only
  section). A UTF-8 BOM is kept.
* The file is edited as text (latin-1 round trip, so every untouched byte, the encoding
  and the line endings are kept). Section headers match case-insensitively and a section
  may appear more than once; names are collected from every block.
* Subcatchment id: `S{n}` where n = current count + k, skipping names already used in
  `[SUBCATCHMENTS]`/`[SUBAREAS]`/`[INFILTRATION]`/`[Polygons]`, compared
  case-insensitively like SWMM does. After rendering, every new id must occur exactly
  once (four times in `[Polygons]`) in each edited section.
* Raingage: first existing; if none, create `RG1` bound to the first time series (interval
  = spacing of its first two values, else `1:00`), creating `generator_series` (the
  12-value hourly design storm, interval `1:00`) if no series exists. **Do not overwrite
  an existing raingage table** (1.x bug: `_add_raingage` replaced the whole table).
* Outlet: last outfall, else last junction, else the subcatchment itself.
* Units: `FLOW_UNITS` decides hectares/metres/millimetres vs acres/feet/inches.
* Polygon: square of side `sqrt(area*10_000)` (map units, drawn in metres) placed right
  of the last polygon vertex (or origin), appended to the existing `[Polygons]` /
  `[POLYGONS]` block; 1.x appended a duplicate section when the case differed.
* Infiltration row for the model's `INFILTRATION` method, from `defaults.json`.
* Verification: swmmio re-reads the edited text (an ASCII copy with canonical header
  spelling, since swmmio matches `[SUBCATCHMENTS]` / `[Polygons]` case-sensitively) and
  must find every new id in the four sections. swmmio's `inp.save` is not used: it
  duplicates `[POLYGONS]` and turns ids such as `001` into `1`.
* Writing: refuse a read-only existing target; write a temp file next to the target,
  back up an existing target (unless `backup=False`), re-read the source and refuse if
  it changed since it was parsed (lost-update guard), then `os.replace`.

## CLI

```
rcg add MODEL.inp --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious
        [--output OUT.inp] [--no-backup] [--json]
rcg preview --area 5.5 --land-form ... --land-cover ...   [--json]
rcg inspect MODEL.inp [--json]
rcg list-options
rcg --version
```
Category arguments are case-insensitive and accept both `snake_case` names and the
human labels (“Urban, moderately impervious”). Exit codes: 0 ok, 2 usage/validation, 1 failure.
`--json` output rounds floats to 4 decimals for presentation (files keep full writer
precision); `add --json` includes `flow_units` and `infiltration_method`.

## GUI (PySide6) — one window, no wizard

* **Left column — inputs**: Land cover (combo, human labels, tooltip with description),
  Land form (combo), Area (`QDoubleSpinBox`, ha, 2 dp, 0.01–10 000), SWMM model (path field +
  Browse; accepts drag & drop of `.inp`), Output (radio: *Update model in place (backup kept)*
  / *Save as copy…*).
* **Right column — live preview**: updates on every input change (debounced ~150 ms):
  catchment type badge, slope %, imperviousness %, width, Manning n (imperv/perv),
  depression storage (mm), % zero storage, infiltration row. Before the engine is ready the
  panel shows a subtle “Preparing fuzzy engine…” state; warm-up runs in a `QThread`.
* **Primary action**: “Add subcatchment” (disabled until model + engine ready). Runs
  `apply()` in a worker; on success appends a row to a **history list** (id, area, type,
  file, backup) with “Undo” on the latest entry (restores backup) and “Show in folder”.
* Errors surface inline (non-modal banner) with the message from `RCGError`; unexpected
  exceptions are logged with traceback and shown generically.
* Help: `?` opens a dialog rendering `resources/help.md` (categories tables from README).
* Theme: follows the system light/dark palette; one accent colour; system font; min size
  ~ 860×560, resizable; everything keyboard reachable; no fixed geometry hacks.
* Testable headless: `QT_QPA_PLATFORM=offscreen`; pytest-qt smoke test drives the window,
  adds a subcatchment to a temp copy of `example.inp`, asserts the file changed and a
  screenshot (`widget.grab()`) is saved to the pytest tmp dir.

## Quality gates

* `ruff check .` and `ruff format --check .` clean.
* `pytest` < 60 s locally (engine fixtures session-scoped).
* End-to-end: `apply()` on a copy of `example.inp`, reload with swmmio, run with pyswmm.
* `mypy rcg` without `|| true` in CI for the non-GUI package.
