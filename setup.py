import os
import pip
import codecs
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = "0.0.11"
DESCRIPTION = "Rapid catchment generator - is a tool for rapid prototyping of a hydraulic model catchments that can be read and edited with SWMM."

# Setting up
setup(
    name="rcg",
    version=VERSION,
    author="Rafał Buczyński",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[
        "scikit-fuzzy",
        "numpy",
        "pandas",
        "swmmio",
        "pyswmm",
        "matplotlib"
    ],
    project_urls={
        "Homepage": "https://github.com/BuczynskiRafal/rapid-catchment-generator"
    },
)

# python setup.py sdist
