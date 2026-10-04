"""Application service: the only module the CLI and the GUI call into.

* :func:`preview` computes the parameters of one subcatchment (pure, no I/O).
* :func:`apply` appends one or more previewed subcatchments to a SWMM model with a
  single load and one atomic write.
* :func:`inspect` describes a model (units, infiltration method, rain gage, outlet)
  without changing it.
* :func:`restore` undoes an :func:`apply` from its backup.
* :func:`warm_up` builds the shared fuzzy engine ahead of time (takes seconds).

The fuzzy engine (scikit-fuzzy and its scientific stack) is imported only inside
:func:`preview`, :func:`apply` and :func:`warm_up`; importing this module and calling
:func:`inspect` stay fast.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from rcg.catchment import MM_PER_INCH, ApplyResult, ModelInfo, SubcatchmentParameters, width_m
from rcg.config import load_defaults
from rcg.exceptions import ConfigurationError, ValidationError
from rcg.fuzzy.categories import LandCover, LandForm
from rcg.logging_config import get_logger
from rcg.validation import (
    validate_area,
    validate_inp_path,
    validate_land_cover,
    validate_land_form,
    validate_parameters,
)

if TYPE_CHECKING:
    from rcg.fuzzy.engine import FuzzyEngine

__all__ = [
    "ApplyResult",
    "ModelInfo",
    "SubcatchmentParameters",
    "apply",
    "inspect",
    "preview",
    "restore",
    "warm_up",
]

logger = get_logger("service")


def _default_engine() -> FuzzyEngine:
    from rcg.fuzzy.engine import get_default_fuzzy_engine  # heavy: scikit-fuzzy, scipy, networkx

    return get_default_fuzzy_engine()


def warm_up(engine: FuzzyEngine | None = None) -> FuzzyEngine:
    """Build (if needed) and exercise the fuzzy engine so later previews are instant.

    Parameters
    ----------
    engine : FuzzyEngine, optional
        Engine to warm up. Defaults to the shared engine, which is built on first use.

    Returns
    -------
    FuzzyEngine
        The warmed-up engine. Safe to call from a worker thread.
    """
    engine = engine if engine is not None else _default_engine()
    engine.compute_all(LandForm.flats_and_plateaus.value, LandCover.urban_moderately_impervious.value)
    return engine


def preview(
    area_ha: float,
    land_form: LandForm | str,
    land_cover: LandCover | str,
    *,
    engine: FuzzyEngine | None = None,
) -> SubcatchmentParameters:
    """Compute the SWMM parameters of a subcatchment without touching any file.

    Parameters
    ----------
    area_ha : float
        Area in hectares, ``0.0001 <= area_ha <= 10 000``.
    land_form : LandForm or str
        Land form as enum, snake_case name or human label (case-insensitive).
    land_cover : LandCover or str
        Land cover as enum, snake_case name or human label (case-insensitive).
    engine : FuzzyEngine, optional
        Engine to use. Defaults to the shared engine.

    Returns
    -------
    SubcatchmentParameters
        All values needed to write the subcatchment (Python floats/ints only).

    Raises
    ------
    ValidationError
        If any input is invalid.
    """
    area = validate_area(area_ha)
    form = validate_land_form(land_form)
    cover = validate_land_cover(land_cover)
    engine = engine if engine is not None else _default_engine()

    results = engine.compute_all(form.value, cover.value)
    catchment_type = engine.classify_catchment(results["catchment"])

    defaults = load_defaults()
    try:
        n_imperv, n_perv = defaults.manning_coefficients[catchment_type]
        s_imperv_in, s_perv_in, pct_zero = defaults.depression_storage[catchment_type]
    except KeyError as e:
        raise ConfigurationError(f"defaults.json has no parameters for catchment type {catchment_type!r}") from e

    return SubcatchmentParameters(
        land_form=form,
        land_cover=cover,
        area_ha=area,
        slope_pct=float(results["slope"]),
        impervious_pct=float(results["impervious"]),
        catchment_score=float(results["catchment"]),
        catchment_type=catchment_type,
        width_m=width_m(area),
        n_imperv=float(n_imperv),
        n_perv=float(n_perv),
        s_imperv_mm=float(s_imperv_in) * MM_PER_INCH,
        s_perv_mm=float(s_perv_in) * MM_PER_INCH,
        pct_zero=int(pct_zero),
        infiltration=dict(defaults.infiltration),
    )


def apply(
    inp_path: str | Path,
    parameters: Sequence[SubcatchmentParameters] | SubcatchmentParameters,
    *,
    output_path: str | Path | None = None,
    backup: bool = True,
) -> ApplyResult:
    """Append subcatchments to a SWMM model.

    The model is loaded once, edited in memory and written to a temporary file next
    to the destination, which then atomically replaces it. Values are written in the
    model's units (acres, feet and inches for ``CFS``/``GPM``/``MGD`` models) and the
    ``[INFILTRATION]`` row matches the model's ``INFILTRATION`` option.

    Parameters
    ----------
    inp_path : str or Path
        Source ``.inp`` file. Symbolic links are followed.
    parameters : SubcatchmentParameters or sequence of them
        Subcatchments to add, typically from :func:`preview`.
    output_path : str or Path, optional
        Destination file. Defaults to ``inp_path`` (update in place); a different path
        leaves the source untouched.
    backup : bool, optional
        Before overwriting an existing file (``inp_path`` when updating in place, or an
        existing ``output_path``), copy it to
        ``<dir>/.rcg_backups/<stem>_backup_<timestamp>.inp`` (default ``True``).
        ``False`` is the explicit opt-out.

    Returns
    -------
    ApplyResult
        Written (resolved) path, backup path, new ids, rain gage, outlet, flow units
        and infiltration method.

    Raises
    ------
    ValidationError
        If the paths or parameters are invalid (every numeric value is checked).
    ModelOperationError
        If the model cannot be read, edited or written, the target is read-only or the
        source changed while it was being edited.
    """
    from rcg.inp_manage.writer import append_subcatchments

    source = validate_inp_path(inp_path)
    target = source if output_path is None else validate_inp_path(output_path, must_exist=False)

    items = (parameters,) if isinstance(parameters, SubcatchmentParameters) else tuple(parameters)
    if not items:
        raise ValidationError("At least one subcatchment is required", field="parameters", value=parameters)
    for item in items:
        validate_parameters(item)

    result = append_subcatchments(source, items, output_path=target, backup=backup)
    logger.info(
        "Added %s to %s (raingage=%s, outlet=%s)",
        ", ".join(result.subcatchment_ids),
        result.output_path,
        result.raingage,
        result.outlet,
    )
    return result


def inspect(inp_path: str | Path) -> ModelInfo:
    """Describe a SWMM model without changing it (fast; no fuzzy engine needed).

    Parameters
    ----------
    inp_path : str or Path
        The ``.inp`` file to read.

    Returns
    -------
    ModelInfo
        Units, infiltration method, subcatchment count and the rain gage and outlet
        :func:`apply` would use.

    Raises
    ------
    ValidationError
        If the path is unusable.
    ModelOperationError
        If the file cannot be read or is not a SWMM model.
    """
    from rcg.inp_manage.writer import inspect_model

    return inspect_model(validate_inp_path(inp_path))


def restore(backup_path: str | Path, target_path: str | Path, *, expected_sha256: str | None = None) -> None:
    """Undo an :func:`apply` by copying its backup back over the written file.

    Parameters
    ----------
    backup_path : str or Path
        :attr:`ApplyResult.backup_path` of the apply to undo. The backup is kept.
    target_path : str or Path
        :attr:`ApplyResult.output_path` of that apply.
    expected_sha256 : str, optional
        :attr:`ApplyResult.written_sha256`. When given, the file is restored only if it
        is still exactly as RCG wrote it, so edits made elsewhere are not lost.

    Raises
    ------
    BackupError
        If the backup is gone, the file changed since it was written, or the copy
        fails. The file is replaced atomically, never left half-written.
    """
    from rcg.inp_manage.backups import restore_backup

    restore_backup(Path(backup_path), Path(target_path), expected_sha256=expected_sha256)
    logger.info("Restored %s from %s", target_path, backup_path)
