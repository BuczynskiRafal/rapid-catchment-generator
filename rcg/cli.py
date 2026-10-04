"""Command-line interface: ``rcg add | preview | inspect | list-options``.

Exit codes: 0 success, 2 usage or validation error, 1 any other failure.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Callable, Sequence
from typing import Any

from rcg import __version__
from rcg.catchment import LAND_COVER_LABELS, LAND_FORM_LABELS, ModelInfo, SubcatchmentParameters, is_metric
from rcg.exceptions import RCGError, ValidationError
from rcg.logging_config import get_logger

logger = get_logger("cli")

EXIT_OK, EXIT_FAILURE, EXIT_USAGE = 0, 1, 2
JSON_DECIMALS = 4
"""Floats in ``--json`` output are rounded for presentation; files keep full precision."""

EPILOG = """\
examples:
  rcg add model.inp --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious
  rcg add model.inp --area 2 --land-form mountains --land-cover "Forests" --output copy.inp --json
  rcg preview --area 5.5 --land-form "Flats and plateaus" --land-cover "Urban, moderately impervious"
  rcg inspect model.inp
  rcg list-options

Categories are case-insensitive and accept snake_case names or the labels shown by
`rcg list-options`.
"""


def _add_category_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--area", required=True, metavar="HA", help="subcatchment area in hectares, e.g. 5.5")
    parser.add_argument("--land-form", required=True, metavar="NAME", help="land form (see `rcg list-options`)")
    parser.add_argument("--land-cover", required=True, metavar="NAME", help="land cover (see `rcg list-options`)")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the ``rcg`` command."""
    parser = argparse.ArgumentParser(
        prog="rcg",
        description="Rapid Catchment Generator: add fuzzy-parameterised subcatchments to SWMM models.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="log debug information to stderr")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    add = sub.add_parser("add", help="append a subcatchment to a SWMM model", description="Append a subcatchment to a model.")
    add.add_argument("model", metavar="MODEL.inp", help="SWMM input file to update")
    _add_category_args(add)
    add.add_argument("--output", "-o", metavar="OUT.inp", help="write to this file instead of updating MODEL.inp")
    add.add_argument("--no-backup", action="store_true", help="do not keep a backup when updating MODEL.inp in place")
    add.set_defaults(handler=_cmd_add)

    prev = sub.add_parser("preview", help="show the parameters without writing anything")
    _add_category_args(prev)
    prev.set_defaults(handler=_cmd_preview)

    info = sub.add_parser(
        "inspect",
        help="show the units, infiltration method, rain gage and outlet of a model",
        description="Describe a SWMM model without changing it.",
    )
    info.add_argument("model", metavar="MODEL.inp", help="SWMM input file to read")
    info.add_argument("--json", action="store_true", help="print the result as JSON")
    info.set_defaults(handler=_cmd_inspect)

    options = sub.add_parser("list-options", help="list land forms and land covers")
    options.add_argument("--json", action="store_true", help="print the lists as JSON")
    options.set_defaults(handler=_cmd_list_options)
    return parser


def _format_parameters(p: SubcatchmentParameters) -> str:
    infil = ", ".join(f"{k}={v:g}" for k, v in p.infiltration.items())
    return "\n".join(
        [
            f"Land form          {LAND_FORM_LABELS[p.land_form]}",
            f"Land cover         {LAND_COVER_LABELS[p.land_cover]}",
            f"Area               {p.area_ha:g} ha",
            f"Catchment type     {p.catchment_type}",
            f"Slope              {p.slope_pct:.2f} %",
            f"Impervious         {p.impervious_pct:.2f} %",
            f"Width              {p.width_m:.2f} m",
            f"Manning n          imperv {p.n_imperv:g}, perv {p.n_perv:g}",
            f"Depression storage imperv {p.s_imperv_mm:.2f} mm, perv {p.s_perv_mm:.2f} mm",
            f"% zero storage     {p.pct_zero}",
            f"Infiltration       {infil}",
        ]
    )


def _format_model_info(info: ModelInfo) -> str:
    units = "SI: hectares, metres, millimetres" if info.is_metric else "US: acres, feet, inches"
    raingage = info.raingage if info.raingage is not None else "none (RG1 will be created)"
    outlet = info.outlet if info.outlet is not None else "none (each new subcatchment drains to itself)"
    return "\n".join(
        [
            f"Model              {info.path}",
            f"Flow units         {info.flow_units} ({units})",
            f"Infiltration       {info.infiltration_method}",
            f"Subcatchments      {info.subcatchment_count}",
            f"Rain gage          {raingage}",
            f"Outlet             {outlet}",
            f"Size               {info.size_bytes:,} bytes",
        ]
    )


def _rounded(value: Any, decimals: int = JSON_DECIMALS) -> Any:
    """Round every float in a JSON-ready structure (presentation only)."""
    if isinstance(value, float):
        return round(value, decimals)
    if isinstance(value, dict):
        return {k: _rounded(v, decimals) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_rounded(v, decimals) for v in value]
    return value


def _json(data: Any) -> str:
    return json.dumps(_rounded(data), indent=2)


def _list_options(as_json: bool = False) -> str:
    if as_json:
        data = {
            "land_forms": [{"name": m.name, "label": lbl} for m, lbl in LAND_FORM_LABELS.items()],
            "land_covers": [{"name": m.name, "label": lbl} for m, lbl in LAND_COVER_LABELS.items()],
        }
        return json.dumps(data, indent=2)
    lines = ["Land forms:"]
    lines += [f"  {m.name:<46} {lbl}" for m, lbl in LAND_FORM_LABELS.items()]
    lines += ["", "Land covers:"]
    lines += [f"  {m.name:<46} {lbl}" for m, lbl in LAND_COVER_LABELS.items()]
    return "\n".join(lines)


def _cmd_list_options(args: argparse.Namespace) -> str:
    return _list_options(as_json=args.json)


def _cmd_inspect(args: argparse.Namespace) -> str:
    from rcg.service import inspect

    info = inspect(args.model)
    return _json(info.to_dict()) if args.json else _format_model_info(info)


def _cmd_preview(args: argparse.Namespace) -> str:
    from rcg.service import preview

    params = preview(args.area, args.land_form, args.land_cover)
    return _json(params.to_dict()) if args.json else _format_parameters(params)


def _cmd_add(args: argparse.Namespace) -> str:
    from rcg.service import apply, preview
    from rcg.validation import validate_inp_path

    # Fail fast on the paths, before preview() spends seconds building the fuzzy engine.
    validate_inp_path(args.model)
    if args.output is not None:
        validate_inp_path(args.output, must_exist=False)

    params = preview(args.area, args.land_form, args.land_cover)
    result = apply(args.model, params, output_path=args.output, backup=not args.no_backup)
    if args.json:
        payload: dict[str, Any] = {**result.to_dict(), "parameters": params.to_dict()}
        return _json(payload)
    units = "SI units" if is_metric(result.flow_units) else "US units: acres, feet, inches"
    lines = [
        f"Added {', '.join(result.subcatchment_ids)} ({params.catchment_type}, {params.area_ha:g} ha) to {result.output_path}",
        f"Rain gage {result.raingage}, outlet {result.outlet}",
        f"Flow units {result.flow_units} ({units}), infiltration {result.infiltration_method}",
    ]
    if result.backup_path is not None:
        lines.append(f"Backup: {result.backup_path}")
    return "\n".join(lines)


def _run(args: argparse.Namespace) -> str:
    handler: Callable[[argparse.Namespace], str] = args.handler  # set by build_parser per subcommand
    return handler(args)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        output = _run(args)
    except ValidationError as e:
        parser.error(str(e))  # exits with status 2
    except RCGError as e:
        print(f"rcg: error: {e}", file=sys.stderr)
        return EXIT_FAILURE
    except KeyboardInterrupt:
        print("rcg: interrupted", file=sys.stderr)
        return EXIT_FAILURE
    except Exception:
        logger.exception("Unexpected error")
        return EXIT_FAILURE
    print(output)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
