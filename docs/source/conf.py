"""Sphinx configuration for Rapid Catchment Generator documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------

project = "Rapid Catchment Generator"
copyright = "2023-2026, Rafał Buczyński"
author = "Rafał Buczyński"
release = "2.0.0"
version = "2.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]

# Heavy third-party dependencies are mocked so the docs build (e.g. on Read the Docs)
# without compiling scientific C/Fortran extensions or GUI toolkits.
autodoc_mock_imports = ["skfuzzy", "swmmio", "pandas", "numpy", "scipy", "networkx", "PySide6"]
autodoc_member_order = "bysource"

# Napoleon settings for NumPy style docstrings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

templates_path = ["_templates"]
exclude_patterns: list[str] = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "titles_only": False,
}
