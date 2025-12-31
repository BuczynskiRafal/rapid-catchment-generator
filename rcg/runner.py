"""
Interactive command-line interface for creating and adding multiple subcatchments
to an existing SWMM model through step-by-step prompts.

Usage:
    python3 runner.py file_path

Example:
    python3 runner.py example.inp
"""

import logging
import sys
from typing import Union

from rcg.fuzzy.categories import LandCover, LandForm
from rcg.inp_manage.inp import BuildCatchments
from rcg.logging_config import setup_logging as setup_central_logging
from rcg.validation import validate_area, validate_file_path, validate_land_cover, validate_land_form


def setup_logging() -> logging.Logger:
    """
    Configure basic logging using centralized config.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return setup_central_logging(level=logging.INFO, name="rcg.runner")


def prompt_for_float(prompt: str) -> float:
    """Prompt user for a float value with validation."""
    while True:
        try:
            value = input(prompt)
            return validate_area(value)
        except ValueError as e:
            print(f"Invalid input: {e}. Try again.")


def prompt_for_category(prompt: str, validator, categories) -> Union[LandForm, LandCover]:
    """Prompt user for a category with validation and list of options."""
    print(f"Available options: {', '.join(sorted(categories.get_all_categories()))}")
    while True:
        try:
            value = input(prompt).strip()
            return validator(value)
        except ValueError as e:
            print(f"Invalid input: {e}. Try again.")


def add_multiple_subcatchments(model: BuildCatchments, logger: logging.Logger) -> None:
    """Add multiple subcatchments to the model interactively with validation."""
    subcatchment_count = 0
    logger.info("Starting interactive subcatchment generator")

    try:
        while True:
            logger.info(f"Adding subcatchment #{subcatchment_count + 1}")

            area = prompt_for_float("Enter area in hectares (ha, positive number <=10000): ")
            land_form = prompt_for_category("Enter land form: ", validate_land_form, LandForm)
            land_cover = prompt_for_category("Enter land cover: ", validate_land_cover, LandCover)

            model.add_subcatchment(area, land_form, land_cover)
            subcatchment_count += 1
            logger.info(f"Subcatchment #{subcatchment_count} added successfully")

            while True:
                user_input = input("\nDo you want to add another subcatchment? (y/n): ").lower().strip()
                if user_input == "y":
                    break
                elif user_input == "n":
                    logger.info(f"Finished adding {subcatchment_count} subcatchment(s)")
                    return
                else:
                    print("Please enter 'y' or 'n'")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        if subcatchment_count > 0:
            logger.info(f"Added {subcatchment_count} subcatchment(s) before interruption")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def generate_subcatchment(file_path: str, area: float, land_form: str, land_cover: str):
    """
    Adds a subcatchment to an existing SWMM model.

    Parameters
    ----------
    file_path : str
        The path to the SWMM input file (INP) to which subcatchments will be added.
    area : float
        The area of the subcatchment [ha].
    land_use_type : str
        The land use type of the subcatchment.
    land_form_type : str
        The land form type of the subcatchment.
    """
    model = BuildCatchments(file_path)
    model.add_subcatchment(area, land_form, land_cover)


if __name__ == "__main__":
    logger = setup_logging()

    if len(sys.argv) != 2:
        logger.error("Usage: python runner.py <path_to_inp_file>")
        logger.info("For CLI, try: python -m rcg.cli --help")
        sys.exit(1)

    file_path_str = sys.argv[1]
    logger.info(f"Validating and loading SWMM model: {file_path_str}")

    try:
        file_path = validate_file_path(file_path_str)  # Validate before loading
        user_model = BuildCatchments(str(file_path))
        add_multiple_subcatchments(user_model, logger)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        sys.exit(1)
