"""Append subcatchments to a SWMM ``.inp`` file without risking the user's model.

How a write works:

1. Paths are resolved (symbolic links followed), so a linked model is updated where
   it really lives and the link itself is kept.
2. The file is read as bytes and must pass a structural check: 8-bit text (no NUL
   bytes, no UTF-16/32 byte order mark) with at least one SWMM section header, and
   not an EPANET network. It is split into ``[SECTION]`` blocks (headers matched
   case-insensitively, a section may appear more than once). New rows are appended
   to the first block of the matching section, or a new block is created when the
   section is missing. Every other byte is kept as is: comments, unknown sections,
   line endings and the original text encoding.
3. ``FLOW_UNITS`` and ``INFILTRATION`` from ``[OPTIONS]`` decide the units written
   (hectares/metres/millimetres or acres/feet/inches) and the ``[INFILTRATION]`` row.
4. The edited text is checked twice before anything touches the disk: every new id
   must occur exactly once (case-insensitively, four times in ``[Polygons]``) in each
   edited section, and swmmio must read every new subcatchment back from
   ``[SUBCATCHMENTS]``, ``[SUBAREAS]``, ``[INFILTRATION]`` and ``[Polygons]``.
5. The result is written to a temporary file next to the target. An existing target
   is backed up to ``<dir>/.rcg_backups/`` (unless ``backup=False``), the source is
   re-read to make sure nobody changed it meanwhile, and the temporary file
   atomically replaces the target with :func:`os.replace`.

swmmio's own ``inp.save`` is deliberately not used for writing: it matches section
headers case-sensitively and appends a second ``[Polygons]`` section to files that
spell it ``[POLYGONS]``, and its index parsing turns ids such as ``001`` into ``1``.
"""

from __future__ import annotations

import contextlib
import hashlib
import math
import os
import re
import secrets
import shutil
import tempfile
import warnings
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rcg.catchment import (
    ACRES_PER_HECTARE,
    FEET_PER_METRE,
    FLOW_UNITS_SI,
    FLOW_UNITS_US,
    INFILTRATION_METHODS,
    MM_PER_INCH,
    ApplyResult,
    ModelInfo,
    SubcatchmentParameters,
    base_infiltration_method,
    infiltration_for,
    is_metric,
)
from rcg.exceptions import ModelOperationError, ValidationError
from rcg.inp_manage.backups import BACKUP_DIR_NAME, create_backup
from rcg.logging_config import get_logger
from rcg.validation import validate_parameters

# BACKUP_DIR_NAME and create_backup live in rcg.inp_manage.backups; re-exported for 2.0.0 callers.
__all__ = ["BACKUP_DIR_NAME", "DESIGN_STORM", "append_subcatchments", "create_backup", "inspect_model"]

logger = get_logger("inp_manage.writer")

DESIGN_STORM: tuple[tuple[str, float], ...] = (
    ("1:00", 1),
    ("2:00", 2),
    ("3:00", 4),
    ("4:00", 4),
    ("5:00", 12),
    ("6:00", 13),
    ("7:00", 11),
    ("8:00", 20),
    ("9:00", 15),
    ("10:00", 10),
    ("11:00", 5),
    ("12:00", 3),
)
"""Hourly intensities of ``generator_series``, created when the model has no time series."""

DESIGN_STORM_NAME = "generator_series"
DEFAULT_RAINGAGE_NAME = "RG1"
DEFAULT_RAIN_INTERVAL = "1:00"
"""Recording interval of a created rain gage when it cannot be derived from its series."""

DEFAULT_FLOW_UNITS = "CFS"
DEFAULT_INFILTRATION = "HORTON"
"""SWMM's own defaults when ``[OPTIONS]`` does not set ``FLOW_UNITS`` / ``INFILTRATION``."""

INFILTRATION_KEYS = ("Suction", "Ksat", "IMD", "Param4", "Param5")
"""Keys of :attr:`SubcatchmentParameters.infiltration`, written for Green-Ampt models."""

# Rows written per new subcatchment in each edited section (a polygon is a square).
_ROWS_PER_ID = {"SUBCATCHMENTS": 1, "SUBAREAS": 1, "INFILTRATION": 1, "POLYGONS": 4}

# Header comments written when a section has to be created.
_SECTION_TEMPLATES: dict[str, tuple[str, str]] = {
    "RAINGAGES": ("[RAINGAGES]", ";;Name           Format    Interval SCF      Source"),
    "SUBCATCHMENTS": (
        "[SUBCATCHMENTS]",
        ";;Name           Rain Gage        Outlet           Area     %Imperv  Width    %Slope   CurbLen",
    ),
    "SUBAREAS": ("[SUBAREAS]", ";;Subcatchment   N-Imperv   N-Perv     S-Imperv   S-Perv     PctZero    RouteTo"),
    "INFILTRATION": ("[INFILTRATION]", ";;Subcatchment   Param1     Param2     Param3     Param4     Param5"),
    "POLYGONS": ("[Polygons]", ";;Subcatchment   X-Coord            Y-Coord"),
    "TIMESERIES": ("[TIMESERIES]", ";;Name           Date       Time       Value"),
}

# Sections of SWMM 5.1/5.2 input files.
_SWMM_SECTIONS = frozenset(
    """TITLE OPTIONS REPORT FILES RAINGAGES EVAPORATION TEMPERATURE ADJUSTMENTS SUBCATCHMENTS SUBAREAS
    INFILTRATION LID_CONTROLS LID_USAGE AQUIFERS GROUNDWATER GWF SNOWPACKS JUNCTIONS OUTFALLS DIVIDERS
    STORAGE CONDUITS PUMPS ORIFICES WEIRS OUTLETS XSECTIONS TRANSECTS STREETS INLETS INLET_USAGE LOSSES
    CONTROLS POLLUTANTS LANDUSES COVERAGES LOADINGS BUILDUP WASHOFF TREATMENT INFLOWS DWF RDII
    HYDROGRAPHS CURVES TIMESERIES PATTERNS MAP COORDINATES VERTICES POLYGONS SYMBOLS LABELS BACKDROP
    TAGS PROFILES EVENTS""".split()
)
# Sections EPANET input files have too.
_SHARED_WITH_EPANET = frozenset(
    "TITLE OPTIONS REPORT FILES JUNCTIONS PUMPS CONTROLS PATTERNS CURVES MAP COORDINATES VERTICES LABELS BACKDROP TAGS".split()
)
# SWMM sections EPANET does not have: one of them settles that a file is a SWMM model.
_SWMM_ONLY_SECTIONS = _SWMM_SECTIONS - _SHARED_WITH_EPANET
# EPANET sections SWMM does not have.
_EPANET_ONLY_SECTIONS = frozenset(
    "PIPES RESERVOIRS TANKS VALVES EMITTERS DEMANDS ENERGY REACTIONS MIXING SOURCES STATUS TIMES QUALITY".split()
)
# Longer marks first: the UTF-32-LE mark starts with the UTF-16-LE one.
_WIDE_BOMS = (
    (b"\xff\xfe\x00\x00", "UTF-32"),
    (b"\x00\x00\xfe\xff", "UTF-32"),
    (b"\xff\xfe", "UTF-16"),
    (b"\xfe\xff", "UTF-16"),
)
_UTF8_BOM = "\xef\xbb\xbf"  # the UTF-8 byte order mark, decoded as latin-1

_HEADER_RE = re.compile(r"^\s*\[([^\]]+)\]")
_HEADER_LINE_RE = re.compile(r"(?m)^([ \t]*)\[([^\]\r\n]+)\]")
_TOKEN_RE = re.compile(r'"[^"]*"|\S+')


# --------------------------------------------------------------------------- document


@dataclass
class _Block:
    """One ``[SECTION]`` of the file (``name`` is ``None`` for text before the first header)."""

    name: str | None
    lines: list[str] = field(default_factory=list)

    def rows(self) -> list[list[str]]:
        """Return the tokens of every data line (comments and blank lines skipped)."""
        rows = []
        for line in self.lines[1:] if self.name is not None else self.lines:
            data = line.split(";", 1)[0].strip()
            if data:
                rows.append(_TOKEN_RE.findall(data))
        return rows


class _InpDocument:
    """A SWMM input file as an ordered list of blocks that renders back byte-for-byte."""

    def __init__(self, text: str) -> None:
        self.newline = "\r\n" if "\r\n" in text else "\n"
        # A UTF-8 byte order mark is kept aside so the first header is still recognised.
        self.bom = _UTF8_BOM if text.startswith(_UTF8_BOM) else ""
        self.blocks: list[_Block] = [_Block(None)]
        # Split on "\n" only: str.splitlines() would also break on bytes such as 0x85,
        # which is a printable character ("...") in cp1252-encoded files.
        for line in re.findall(r"[^\n]*\n|[^\n]+$", text[len(self.bom) :]):
            match = _HEADER_RE.match(line)
            if match:
                self.blocks.append(_Block(match.group(1).strip().upper(), [line]))
            else:
                self.blocks[-1].lines.append(line)

    def render(self) -> str:
        return self.bom + "".join(line for block in self.blocks for line in block.lines)

    def sections(self) -> set[str]:
        return {b.name for b in self.blocks if b.name is not None}

    def find(self, name: str) -> _Block | None:
        """Return the first block called ``name`` (names are upper case)."""
        return next((b for b in self.blocks if b.name == name), None)

    def rows(self, section: str) -> list[list[str]]:
        """Return the data rows of every block called ``section``, in file order."""
        return [row for b in self.blocks if b.name == section for row in b.rows()]

    def names(self, section: str) -> list[str]:
        return [row[0] for row in self.rows(section)]

    def append_rows(self, section: str, rows: Iterable[str], *, after: Sequence[str] = (), before: Sequence[str] = ()) -> None:
        """Append data lines to ``section``, creating the block if it does not exist.

        A new block is placed after the first existing section in ``after``, else before
        the first existing section in ``before``, else at the end of the file.
        """
        new_lines = [row + self.newline for row in rows]
        block = self.find(section)
        if block is None:
            block = self._insert_block(section, after, before)
        # Insert after the last non-blank line so trailing blank lines stay trailing.
        idx = len(block.lines)
        while idx > 1 and not block.lines[idx - 1].strip():
            idx -= 1
        self._terminate(block.lines, idx - 1)
        block.lines[idx:idx] = new_lines

    def _insert_block(self, section: str, after: Sequence[str], before: Sequence[str]) -> _Block:
        header, comment = _SECTION_TEMPLATES[section]
        block = _Block(section, [header + self.newline, comment + self.newline, self.newline])
        position = len(self.blocks)
        anchor = next((self.find(s) for s in after if self.find(s) is not None), None)
        if anchor is not None:
            position = self.blocks.index(anchor) + 1
        else:
            anchor = next((self.find(s) for s in before if self.find(s) is not None), None)
            if anchor is not None:
                position = self.blocks.index(anchor)
        previous = self.blocks[position - 1].lines
        if previous:
            self._terminate(previous, len(previous) - 1)
            if previous[-1].strip():
                previous.append(self.newline)
        self.blocks.insert(position, block)
        return block

    def _terminate(self, lines: list[str], idx: int) -> None:
        """Make sure ``lines[idx]`` ends with a line break (the last line of a file may not)."""
        if 0 <= idx < len(lines) and not lines[idx].endswith(("\n", "\r")):
            lines[idx] += self.newline


# --------------------------------------------------------------------------- reading


@dataclass(frozen=True)
class _Model:
    """A model as read from disk: its exact bytes, parsed blocks and relevant options."""

    path: Path
    raw: bytes
    doc: _InpDocument
    flow_units: str
    infiltration_method: str

    @property
    def is_metric(self) -> bool:
        return is_metric(self.flow_units)  # the module-level rcg.catchment.is_metric


def _read_error(path: Path, message: str) -> ModelOperationError:
    return ModelOperationError(message, operation="read", model_path=str(path))


def _check_structure(raw: bytes, doc: _InpDocument, path: Path) -> None:
    """Reject files that are not 8-bit text SWMM input files (with a message for the user)."""
    for bom, encoding in _WIDE_BOMS:
        if raw.startswith(bom):
            raise _read_error(
                path,
                f"{path.name} is saved as {encoding} text, which SWMM cannot read. "
                "Save it as UTF-8 or ANSI (for example from the SWMM GUI) and try again.",
            )
    if b"\x00" in raw:
        raise _read_error(path, f"{path.name} is not a text file (it contains binary data), so it cannot be a SWMM model.")
    sections = doc.sections()
    if not sections & _SWMM_SECTIONS:
        raise _read_error(
            path,
            f"{path.name} is not a SWMM model: it has no SWMM section such as [TITLE], [OPTIONS], "
            "[JUNCTIONS] or [SUBCATCHMENTS].",
        )
    epanet = set(sections & _EPANET_ONLY_SECTIONS)
    if {"JUNCTIONS", "PATTERNS"} <= sections:  # shared names, but EPANET's core pair without SWMM links
        epanet.add("PATTERNS")
    if epanet and not sections & _SWMM_ONLY_SECTIONS:
        raise _read_error(
            path,
            f"{path.name} looks like an EPANET network ({', '.join(f'[{s}]' for s in sorted(epanet))}), not a SWMM model.",
        )


def _options(doc: _InpDocument, path: Path) -> tuple[str, str]:
    """Return ``(FLOW_UNITS, INFILTRATION)`` from ``[OPTIONS]``, with SWMM's defaults."""
    values: dict[str, str] = {}
    for row in doc.rows("OPTIONS"):
        if len(row) >= 2:
            values[row[0].upper()] = row[1].strip('"').upper()  # SWMM keeps the last value given
    flow_units = values.get("FLOW_UNITS", DEFAULT_FLOW_UNITS)
    if flow_units not in FLOW_UNITS_SI + FLOW_UNITS_US:
        raise _read_error(
            path,
            f"{path.name} has an unknown FLOW_UNITS {flow_units!r}; expected one of "
            f"{', '.join(FLOW_UNITS_US + FLOW_UNITS_SI)}.",
        )
    method = values.get("INFILTRATION", DEFAULT_INFILTRATION)
    if method not in INFILTRATION_METHODS:
        raise _read_error(
            path,
            f"{path.name} has an unknown INFILTRATION method {method!r}; expected one of {', '.join(INFILTRATION_METHODS)}.",
        )
    return flow_units, method


def _read_model(path: Path) -> _Model:
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise _read_error(path, f"Cannot read {path}: {e}") from e
    # latin-1 maps every byte to one code point, so untouched text round-trips exactly
    # whatever the file's real encoding (UTF-8, cp1250, ...); everything we add is ASCII.
    doc = _InpDocument(raw.decode("latin-1"))
    _check_structure(raw, doc, path)
    flow_units, method = _options(doc, path)
    return _Model(path=path, raw=raw, doc=doc, flow_units=flow_units, infiltration_method=method)


def _existing_raingage(doc: _InpDocument) -> str | None:
    names = doc.names("RAINGAGES")
    return names[0] if names else None


def _existing_outlet(doc: _InpDocument) -> str | None:
    outfalls, junctions = doc.names("OUTFALLS"), doc.names("JUNCTIONS")
    return outfalls[-1] if outfalls else junctions[-1] if junctions else None


def _resolve(path: str | Path) -> Path:
    return Path(os.path.realpath(Path(path).expanduser()))


def inspect_model(path: str | Path) -> ModelInfo:
    """Describe a model the way :func:`append_subcatchments` would see it.

    Raises
    ------
    ModelOperationError
        If the file cannot be read or fails the structural check.
    """
    model = _read_model(_resolve(path))
    return ModelInfo(
        path=model.path,
        flow_units=model.flow_units,
        is_metric=model.is_metric,
        infiltration_method=model.infiltration_method,
        subcatchment_count=len(model.doc.names("SUBCATCHMENTS")),
        raingage=_existing_raingage(model.doc),
        outlet=_existing_outlet(model.doc),
        size_bytes=len(model.raw),
    )


# --------------------------------------------------------------------------- formatting


def _num(value: float | int) -> str:
    """Format a number compactly: six decimals, or six significant digits below 1."""
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    number = float(value)
    decimals = 6
    if 0 < abs(number) < 1:
        decimals = max(decimals, 5 - math.floor(math.log10(abs(number))))
    text = f"{number:.{decimals}f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _row(name: str, *values: str | float | int) -> str:
    cells = [name.ljust(16)] + [(v if isinstance(v, str) else _num(v)).ljust(10) for v in values]
    return " ".join(cells).rstrip()


# --------------------------------------------------------------------------- rain gage


def _hours(token: str) -> float | None:
    """Parse a SWMM time (``H:MM``, ``H:MM:SS`` or decimal hours) into hours."""
    try:
        if ":" in token:
            parts = [float(p) for p in token.split(":")]
            if len(parts) > 3 or any(p < 0 for p in parts):
                return None
            return float(sum(p / 60**i for i, p in enumerate(parts)))
        return float(token)
    except ValueError:
        return None


def _series_interval(doc: _InpDocument, series: str) -> str:
    """Return the spacing of the first two values of ``series`` as ``H:MM`` (``1:00`` if unknown)."""
    stamps: list[float] = []
    day = 0.0
    for row in doc.rows("TIMESERIES"):
        if row[0].casefold() != series.casefold():
            continue
        tokens = row[1:]
        if not tokens or tokens[0].upper() == "FILE":
            return DEFAULT_RAIN_INTERVAL
        if "/" in tokens[0]:  # optional date (SWMM's default M/D/Y)
            try:
                day = float(datetime.strptime(tokens[0], "%m/%d/%Y").toordinal())
            except ValueError:
                return DEFAULT_RAIN_INTERVAL
            tokens = tokens[1:]
        for token in tokens[0::2]:  # time value [time value ...]
            hours = _hours(token)
            if hours is None:
                return DEFAULT_RAIN_INTERVAL
            stamps.append(day * 24 + hours)
            if len(stamps) == 2:
                minutes = (stamps[1] - stamps[0]) * 60
                whole = round(minutes)
                if whole <= 0 or abs(minutes - whole) > 1e-6:
                    return DEFAULT_RAIN_INTERVAL
                return f"{whole // 60}:{whole % 60:02d}"
    return DEFAULT_RAIN_INTERVAL


# --------------------------------------------------------------------------- planning


@dataclass(frozen=True)
class _Plan:
    ids: tuple[str, ...]
    raingage: str
    outlet: str


def _new_ids(doc: _InpDocument, count: int) -> list[str]:
    """Return ``count`` unused ids ``S<n>``; SWMM compares names case-insensitively."""
    taken = {name.casefold() for section in _ROWS_PER_ID for name in doc.names(section)}
    ids: list[str] = []
    n = len(doc.names("SUBCATCHMENTS"))
    for _ in range(count):
        n += 1
        while f"s{n}" in taken:
            n += 1
        ids.append(f"S{n}")
        taken.add(f"s{n}")
    return ids


def _last_vertex(doc: _InpDocument) -> tuple[float, float]:
    rows = doc.rows("POLYGONS")
    if rows:
        try:
            return float(rows[-1][1]), float(rows[-1][2])
        except (IndexError, ValueError):
            logger.warning("Could not read the last polygon vertex; placing the new polygon at the origin")
    return 0.0, 0.0


def _infiltration_row(p: SubcatchmentParameters, method: str) -> list[float]:
    if base_infiltration_method(method) == "GREEN_AMPT":
        missing = [k for k in INFILTRATION_KEYS if k not in p.infiltration]
        if missing:
            raise ModelOperationError(f"Infiltration parameters missing: {', '.join(missing)}", operation="apply")
        return [p.infiltration[k] for k in INFILTRATION_KEYS]
    return list(infiltration_for(method).values())


def _ensure_raingage(doc: _InpDocument) -> str:
    raingage = _existing_raingage(doc)
    if raingage is not None:
        return raingage
    series = doc.names("TIMESERIES")
    if series:
        series_name, interval = series[0], _series_interval(doc, series[0])
    else:
        series_name, interval = DESIGN_STORM_NAME, DEFAULT_RAIN_INTERVAL
        doc.append_rows("TIMESERIES", (_row(series_name, time, value) for time, value in DESIGN_STORM))
    doc.append_rows(
        "RAINGAGES",
        [_row(DEFAULT_RAINGAGE_NAME, "INTENSITY", interval, "1.0", "TIMESERIES", series_name)],
        before=("SUBCATCHMENTS",),
    )
    return DEFAULT_RAINGAGE_NAME


def _edit(model: _Model, items: Sequence[SubcatchmentParameters]) -> _Plan:
    doc = model.doc
    ids = _new_ids(doc, len(items))
    raingage = _ensure_raingage(doc)
    node = _existing_outlet(doc)
    outlets = [node or sid for sid in ids]

    # Fuzzy results are in SI units; US-unit models get acres, feet and inches.
    area_factor, width_factor, depth_factor = (
        (1.0, 1.0, 1.0) if model.is_metric else (ACRES_PER_HECTARE, FEET_PER_METRE, 1 / MM_PER_INCH)
    )

    x, y = _last_vertex(doc)
    sub_rows: list[str] = []
    area_rows: list[str] = []
    infil_rows: list[str] = []
    poly_rows: list[str] = []
    for sid, outlet, p in zip(ids, outlets, items):
        width = p.width_m if model.is_metric else round(p.width_m * width_factor, 2)
        sub_rows.append(
            _row(sid, raingage, outlet, p.area_ha * area_factor, round(p.impervious_pct, 2), width, round(p.slope_pct, 2), 0)
        )
        area_rows.append(
            _row(
                sid,
                p.n_imperv,
                p.n_perv,
                p.s_imperv_mm * depth_factor,
                p.s_perv_mm * depth_factor,
                p.pct_zero,
                "OUTLET",
            )
        )
        infil_rows.append(_row(sid, *_infiltration_row(p, model.infiltration_method)))
        side = math.sqrt(p.area_ha * 10_000)  # map units are unknown; drawn in metres
        square = ((x, y), (x + side, y), (x + side, y - side), (x, y - side))
        poly_rows.extend(_row(sid, round(px, 3), round(py, 3)) for px, py in square)
        x, y = square[-1]

    doc.append_rows("SUBCATCHMENTS", sub_rows, after=("RAINGAGES",))
    doc.append_rows("SUBAREAS", area_rows, after=("SUBCATCHMENTS",))
    doc.append_rows("INFILTRATION", infil_rows, after=("SUBAREAS",))
    doc.append_rows("POLYGONS", poly_rows)
    return _Plan(ids=tuple(ids), raingage=raingage, outlet=outlets[0])


# --------------------------------------------------------------------------- checks


def _check_unique(text: str, ids: Sequence[str]) -> None:
    """Make sure every new id occurs exactly as often as written in each edited section."""
    doc = _InpDocument(text)
    for section, expected in _ROWS_PER_ID.items():
        counts = Counter(name.casefold() for name in doc.names(section))
        wrong = [f"{i} ({counts[i.casefold()]}x)" for i in ids if counts[i.casefold()] != expected]
        if wrong:
            raise ModelOperationError(
                f"[{section}] would not list each new subcatchment exactly {expected}x: {', '.join(wrong)}",
                operation="verify",
            )


def _swmmio_text(text: str) -> bytes:
    """Return an ASCII copy of ``text`` with section headers spelled the way swmmio expects.

    swmmio opens files with the platform's default encoding, so it is handed an ASCII
    copy (other characters become ``?``). It also looks section names up
    case-sensitively (``[SUBCATCHMENTS]``, ``[Polygons]``), whereas SWMM accepts any
    case, so headers are canonicalised in the copy.
    """

    def canonical(match: re.Match[str]) -> str:
        name = match.group(2).strip().upper()
        return f"{match.group(1)}[{'Polygons' if name == 'POLYGONS' else name}]"

    return _HEADER_LINE_RE.sub(canonical, text.removeprefix(_UTF8_BOM)).encode("ascii", errors="replace")


def _swmmio_ids(text: str, sections: Mapping[str, str]) -> dict[str, set[str]]:
    """Return the ids swmmio reads from ``sections`` (name -> swmmio header) of ``text``."""
    from swmmio.utils.dataframes import dataframe_from_inp

    with tempfile.TemporaryDirectory(prefix="rcg-") as tmpdir:
        path = Path(tmpdir) / "model.inp"
        path.write_bytes(_swmmio_text(text))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # swmmio warns for every missing section
            return {s: {str(i) for i in dataframe_from_inp(str(path), header).index} for s, header in sections.items()}


def _verify(text: str, ids: Sequence[str]) -> None:
    sections = {
        "SUBCATCHMENTS": "[SUBCATCHMENTS]",
        "SUBAREAS": "[SUBAREAS]",
        "INFILTRATION": "[INFILTRATION]",
        "POLYGONS": "[Polygons]",
    }
    try:
        found = _swmmio_ids(text, sections)
    except Exception as e:
        raise ModelOperationError(f"The updated model could not be re-read: {e}", operation="verify") from e
    for section in sections:
        lost = [i for i in ids if i not in found[section]]
        if lost:
            raise ModelOperationError(f"[{section}] is missing {', '.join(lost)} after the edit", operation="verify")


# --------------------------------------------------------------------------- file ops


def _ensure_unchanged(model: _Model) -> None:
    """Fail if the source changed on disk since it was read (e.g. saved from SWMM meanwhile)."""
    try:
        current = model.path.read_bytes()
    except OSError as e:
        raise ModelOperationError(f"Cannot re-read {model.path}: {e}", operation="write", model_path=str(model.path)) from e
    if current != model.raw:
        raise ModelOperationError(
            f"{model.path.name} was changed by another program while the subcatchments were being added; "
            "nothing was written. Try again.",
            operation="write",
            model_path=str(model.path),
        )


def _write_atomic(target: Path, data: bytes, *, backup: bool, source: _Model) -> Path | None:
    """Write ``data`` next to ``target``, back up an existing target, then replace it.

    Just before the replace the source is re-read; if it changed, nothing is replaced
    (and the backup made by this call is removed).
    """
    exists = target.exists()
    if exists and not os.access(target, os.W_OK):
        raise ModelOperationError(f"{target} is read-only", operation="write", model_path=str(target))
    # A plain exclusive open (rather than mkstemp) gives a new file the usual
    # umask-derived permissions; an existing target's mode is copied below.
    tmp = target.with_name(f".{target.stem}.{secrets.token_hex(4)}.inp.tmp")
    backup_path: Path | None = None
    replaced = False
    try:
        with open(tmp, "xb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        if exists:
            shutil.copymode(target, tmp)
        if exists and backup:
            backup_path = create_backup(target)
        _ensure_unchanged(source)
        os.replace(tmp, target)
        replaced = True
    except OSError as e:
        raise ModelOperationError(f"Cannot write {target}: {e}", operation="write", model_path=str(target)) from e
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()
        if not replaced and backup_path is not None:
            with contextlib.suppress(OSError):
                backup_path.unlink()
    return backup_path


def append_subcatchments(
    source: str | Path,
    parameters: Sequence[SubcatchmentParameters],
    *,
    output_path: str | Path | None = None,
    backup: bool = True,
) -> ApplyResult:
    """Append subcatchments to a SWMM model in one atomic write.

    Parameters
    ----------
    source : str or Path
        Model to read. Symbolic links are followed.
    parameters : sequence of SubcatchmentParameters
        Subcatchments to add, in order.
    output_path : str or Path, optional
        File to write; defaults to ``source``. Symbolic links are followed.
    backup : bool, optional
        Back up the file being overwritten (the source when updating in place, or an
        existing ``output_path``) to ``<dir>/.rcg_backups/`` first (default ``True``).

    Returns
    -------
    ApplyResult
        What was written; ``output_path`` is the resolved target.

    Raises
    ------
    ValidationError
        If there are no parameters or a parameter value is out of range.
    ModelOperationError
        If the model cannot be read, verified or written, the target is read-only or
        the source changed while it was being edited. The target is untouched then.
    """
    source_path = _resolve(source)
    target = _resolve(output_path) if output_path is not None else source_path
    # The only parameter checks on the way to disk: rcg.apply relies on them, so direct
    # callers of this function get exactly the same errors.
    items = tuple(parameters)
    if not items:
        raise ValidationError("At least one subcatchment is required", field="parameters", value=parameters)
    for item in items:
        validate_parameters(item)

    model = _read_model(source_path)
    plan = _edit(model, items)
    updated = model.doc.render()
    _check_unique(updated, plan.ids)
    _verify(updated, plan.ids)

    data = updated.encode("latin-1")
    backup_path = _write_atomic(target, data, backup=backup, source=model)
    logger.debug("Wrote %s (backup: %s)", target, backup_path)
    return ApplyResult(
        output_path=target,
        backup_path=backup_path,
        subcatchment_ids=plan.ids,
        raingage=plan.raingage,
        outlet=plan.outlet,
        flow_units=model.flow_units,
        infiltration_method=model.infiltration_method,
        written_sha256=hashlib.sha256(data).hexdigest(),
    )
