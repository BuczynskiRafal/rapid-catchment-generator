"""
Shared pytest fixtures for RCG tests.

This module provides reusable fixtures for testing the rapid-catchment-generator
project, including isolated instances for dependency injection testing.
"""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_inp_file() -> Generator[Path, None, None]:
    """
    Create a temporary copy of the test INP file.

    This fixture creates a temporary directory with a copy of the test INP file,
    allowing tests to modify the file without affecting the original.

    Yields
    ------
    Path
        Path to the temporary INP file.
    """
    test_file = Path(__file__).parent / "rcg" / "inp_manage" / "test_inp_manage" / "test_file.inp"

    with tempfile.TemporaryDirectory() as tempdir:
        temp_path = Path(tempdir) / "test_file.inp"
        shutil.copy2(test_file, temp_path)
        yield temp_path


@pytest.fixture
def clean_memberships():
    """
    Create an isolated Memberships instance for testing.

    This fixture creates a fresh Memberships instance that is not shared
    with other tests, ensuring test isolation.

    Returns
    -------
    Memberships
        A new isolated Memberships instance.
    """
    from rcg.fuzzy.memberships import create_memberships

    return create_memberships()


@pytest.fixture
def clean_rule_engine(clean_memberships):
    """
    Create an isolated RuleEngine instance for testing.

    This fixture creates a fresh RuleEngine instance with its own
    memberships, ensuring test isolation.

    Parameters
    ----------
    clean_memberships : Memberships
        The isolated memberships instance to use.

    Returns
    -------
    RuleEngine
        A new isolated RuleEngine instance.
    """
    from rcg.fuzzy.rule_engine import create_rule_engine

    return create_rule_engine(memberships=clean_memberships)


@pytest.fixture
def clean_fuzzy_engine(clean_memberships, clean_rule_engine):
    """
    Create an isolated FuzzyEngine instance for testing.

    This fixture creates a fresh FuzzyEngine instance with its own
    memberships and rule engine, ensuring complete test isolation.

    Note: Rules must be defined on the rule_engine before creating the fuzzy engine.

    Parameters
    ----------
    clean_memberships : Memberships
        The isolated memberships instance to use.
    clean_rule_engine : RuleEngine
        The isolated rule engine instance to use.

    Returns
    -------
    FuzzyEngine
        A new isolated FuzzyEngine instance.
    """
    from rcg.fuzzy.engine import create_fuzzy_engine

    # Rules are defined on import of the module
    return create_fuzzy_engine(memberships=clean_memberships)


@pytest.fixture
def mock_memberships(mocker):
    """
    Create a mock Memberships object for isolated unit tests.

    This fixture uses pytest-mock to create a mock memberships object,
    useful for testing components in complete isolation.

    Parameters
    ----------
    mocker : MockerFixture
        pytest-mock fixture.

    Returns
    -------
    MagicMock
        A mock Memberships object.
    """
    mock = mocker.MagicMock()
    mock.land_form_type.label = "land_form"
    mock.land_cover_type.label = "land_cover"
    mock.slope.label = "slope"
    mock.impervious.label = "impervious"
    mock.catchment.label = "catchment"
    return mock


@pytest.fixture
def sample_land_form():
    """
    Provide a sample LandForm enum value for testing.

    Returns
    -------
    LandForm
        A sample LandForm enum value.
    """
    from rcg.fuzzy.categories import LandForm

    return LandForm.flats_and_plateaus


@pytest.fixture
def sample_land_cover():
    """
    Provide a sample LandCover enum value for testing.

    Returns
    -------
    LandCover
        A sample LandCover enum value.
    """
    from rcg.fuzzy.categories import LandCover

    return LandCover.rural


@pytest.fixture
def build_catchments_with_backup(temp_inp_file):
    """
    Create a BuildCatchments instance with backup enabled.

    Parameters
    ----------
    temp_inp_file : Path
        Path to a temporary INP file.

    Returns
    -------
    BuildCatchments
        A BuildCatchments instance with backup enabled.
    """
    from rcg.inp_manage.inp import BuildCatchments

    return BuildCatchments(str(temp_inp_file), backup=True)


@pytest.fixture
def build_catchments_without_backup(temp_inp_file):
    """
    Create a BuildCatchments instance with backup disabled.

    Parameters
    ----------
    temp_inp_file : Path
        Path to a temporary INP file.

    Returns
    -------
    BuildCatchments
        A BuildCatchments instance with backup disabled.
    """
    from rcg.inp_manage.inp import BuildCatchments

    return BuildCatchments(str(temp_inp_file), backup=False)
