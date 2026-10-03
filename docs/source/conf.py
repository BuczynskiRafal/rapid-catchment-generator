import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Rapid Catchment Generator"
copyright = "2023-2026, Rafał Buczyński"
author = "Rafał Buczyński"
release = "2.0.0"
version = "2.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    # 'recommonmark',
]

# Heavy third-party dependencies are mocked so the docs build (e.g. on Read the Docs)
# without installing them.
autodoc_mock_imports = ["skfuzzy", "swmmio", "pandas", "numpy", "scipy", "networkx", "PySide6"]
autodoc_member_order = "bysource"

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
