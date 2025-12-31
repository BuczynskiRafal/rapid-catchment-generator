"""Input validation utilities."""
import argparse
from pathlib import Path

from .fuzzy.categories import LandForm, LandCover


class ValidationError(argparse.ArgumentTypeError):
    """Custom validation error for argparse."""
    pass


def validate_file_path(file_path: str) -> Path:
    """
    Validate SWMM input file path and accessibility.

    Parameters
    ----------
    file_path : str
        Path to the file to validate

    Returns
    -------
    Path
        Validated path object

    Raises
    ------
    ValidationError
        If file doesn't exist, is not a file, has wrong extension,
        is empty, or cannot be read

    Examples
    --------
    validate_file_path('model.inp') -> Path('model.inp') if valid
    """
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    if path.suffix.lower() != '.inp':
        raise ValidationError(f"File must have .inp extension (case-insensitive), got: {path.suffix}")

    try:
        with path.open('r') as f:
            content = f.read(10)
            if not content:
                raise ValidationError(f"File is empty: {file_path}")
    except PermissionError:
        raise ValidationError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise ValidationError(f"Error reading file: {e}")

    return path


def validate_area(area_str: str) -> float:
    """
    Validate area parameter as positive float <= 10000 ha.

    Parameters
    ----------
    area_str : str
        Area value as string

    Returns
    -------
    float
        Validated area value

    Raises
    ------
    ValidationError
        If area is not a valid number, not positive, or exceeds 10000 ha

    Examples
    --------
    validate_area('5.5') -> 5.5
    validate_area('abc') raises ValidationError
    """
    try:
        area = float(area_str)
    except ValueError:
        raise ValidationError(f"Area must be a valid number, got: '{area_str}'")

    if area <= 0:
        raise ValidationError(f"Area must be positive, got: {area}")

    if area > 10000:
        raise ValidationError(f"Area seems too large (>10000 ha), got: {area}. If intended, adjust limit.")

    return area


def validate_land_form(land_form_str: str) -> LandForm:
    """Validate and convert land form to Enum (case-insensitive).

    Example: validate_land_form('flats_and_plateaus') -> LandForm.FLATS_AND_PLATEAUS.
    Raises ValidationError if invalid.
    """
    if not land_form_str:
        raise ValidationError("Land form cannot be empty.")

    normalized = land_form_str.lower()

    for form_name in LandForm.get_all_categories():
        if form_name.lower() == normalized:
            return getattr(LandForm, form_name)

    valid_list = sorted(LandForm.get_all_categories())
    raise ValidationError(
        f"Invalid land form '{land_form_str}' (case-insensitive). Valid options: {', '.join(valid_list)}"
    )


def validate_land_cover(land_cover_str: str) -> LandCover:
    """Validate and convert land cover to Enum (case-insensitive).

    Example: validate_land_cover('urban_moderately_impervious') -> LandCover.URBAN_MODERATELY_IMPERVIOUS.
    Raises ValidationError if invalid.
    """
    if not land_cover_str:
        raise ValidationError("Land cover cannot be empty.")

    normalized = land_cover_str.lower()

    for cover_name in LandCover.get_all_categories():
        if cover_name.lower() == normalized:
            return getattr(LandCover, cover_name)

    valid_list = sorted(LandCover.get_all_categories())
    raise ValidationError(
        f"Invalid land cover '{land_cover_str}' (case-insensitive). Valid options: {', '.join(valid_list)}"
    )
