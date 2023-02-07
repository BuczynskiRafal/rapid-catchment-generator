import os
import pip
import codecs
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = "0.0.2"
DESCRIPTION = (
    "A tool for rapid prototyping of a hydraulic model catchments that can be read and edited with SWMM.",
)
LONG_DESCRIPTION = (
    "Tool for rapid prototyping of a hydraulic model that can be read and edited with SWMM."
    "The generator was created using feature analysis and surface runoff research from the literature."
    "Fuzzy logic controller rules were developed using parameterized categories of soil, slope,"
    "and permeability. The catchment configuration procedure was simplified by mapping typical"
    "storage and Manning's coefficients. The use of fuzzy logic rules allows the system to be modified"
    "to adjust the categories to certain situations. The use of membership functions allows us to increase"
    "computation accuracy and customize the tool to diverse applications. Following alteration"
    "of the catchment in the SWMM GUI allows for accurate portrayal of the real condition of the catchment;"
    "no issues were encountered in altering the *inp file.",
)

# Setting up
setup(
    name="fuzzy catchments",
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
        "matplotlib",
        "swmmio",
        "pyswmm",
    ],
    project_urls={
        "Homepage": "https://github.com/BuczynskiRafal/catchment_prototyping",
    },
)

# python setup.py sdist
