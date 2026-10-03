"""Rapid Catchment Generator: fuzzy-logic parameterisation of SWMM subcatchments.

Typical use::

    import rcg

    info = rcg.inspect("model.inp")
    params = rcg.preview(5.0, "flats_and_plateaus", "Urban, moderately impervious")
    result = rcg.apply("model.inp", params)

The public names are loaded on first access (PEP 562), so ``import rcg`` stays cheap:
the fuzzy engine and its scientific stack are only imported by :func:`preview`,
:func:`apply` and :func:`warm_up`.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

__version__ = "2.0.0"

__all__ = [
    "ApplyResult",
    "LandCover",
    "LandForm",
    "ModelInfo",
    "SubcatchmentParameters",
    "__version__",
    "apply",
    "inspect",
    "preview",
    "warm_up",
]

_LAZY: dict[str, str] = {
    "ApplyResult": "rcg.catchment",
    "ModelInfo": "rcg.catchment",
    "SubcatchmentParameters": "rcg.catchment",
    "LandCover": "rcg.fuzzy.categories",
    "LandForm": "rcg.fuzzy.categories",
    "apply": "rcg.service",
    "inspect": "rcg.service",
    "preview": "rcg.service",
    "warm_up": "rcg.service",
}

# Submodules reachable as attributes after a bare ``import rcg`` (as when 1.x and
# early 2.0 imported rcg.service eagerly), loaded on first access too.
_SUBMODULES = frozenset({"catchment", "cli", "config", "exceptions", "fuzzy", "inp_manage", "service", "validation"})

if TYPE_CHECKING:
    from rcg.catchment import ApplyResult, ModelInfo, SubcatchmentParameters
    from rcg.fuzzy.categories import LandCover, LandForm
    from rcg.service import apply, inspect, preview, warm_up


def __getattr__(name: str) -> Any:
    if name in _SUBMODULES:
        return importlib.import_module(f"{__name__}.{name}")
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module), name)
    globals()[name] = value  # later lookups bypass __getattr__
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
