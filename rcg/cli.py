"""Command-line interface for Rapid Catchment Generator."""
import argparse
import logging
import sys
from typing import Tuple

from .fuzzy.categories import LandForm, LandCover
from .inp_manage.inp import BuildCatchments
from .validation import validate_file_path, validate_area, validate_land_form, validate_land_cover


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr
    )
    return logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser with examples and options."""
    all_land_forms = sorted(LandForm.get_all_categories())  # Sorted for readability
    all_land_covers = sorted(LandCover.get_all_categories())

    parser = argparse.ArgumentParser(
        description="Rapid Catchment Generator - Add subcatchments to SWMM models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
    Examples:
        %(prog)s model.inp --area 5.5 --land-form flats_and_plateaus --land-cover urban_moderately_impervious
        %(prog)s model.inp --area 2.1 --land-form mountains --land-cover forests --verbose
        %(prog)s --list-options

    Land Form Options (sorted): {', '.join(all_land_forms[:5])}...
    Land Cover Options (sorted): {', '.join(all_land_covers[:5])}...
    (use --list-options for full lists)
    """
    )

    parser.add_argument(
        'input_file',
        type=validate_file_path,
        help='Path to the SWMM input (.inp) file'
    )

    parser.add_argument(
        '--area',
        type=validate_area,
        required=True,
        help='Area of the subcatchment in hectares (ha), e.g., 5.5'
    )

    parser.add_argument(
        '--land-form',
        type=validate_land_form,
        required=True,
        help='Land form type (use --list-options for choices)'
    )

    parser.add_argument(
        '--land-cover',
        type=validate_land_cover,
        required=True,
        help='Land cover type (use --list-options for choices)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--list-options',
        action='store_true',
        help='List all available land form and cover options (sorted alphabetically)'
    )

    return parser


def list_options() -> None:
    """Display all available land form and cover options, sorted alphabetically."""
    print("Available Land Form Options (sorted):")
    for i, form in enumerate(sorted(LandForm.get_all_categories()), 1):
        print(f"  {i:2d}. {form}")

    print("\nAvailable Land Cover Options (sorted):")
    for i, cover in enumerate(sorted(LandCover.get_all_categories()), 1):
        print(f"  {i:2d}. {cover}")


def add_subcatchment(
    model: BuildCatchments,
    area: float,
    land_form: LandForm,
    land_cover: LandCover,
    logger: logging.Logger
) -> None:
    """Add subcatchment to the model with logging."""
    logger.info(f"Starting subcatchment generation: Area={area:.2f} ha, Land form={land_form.name}, Land cover={land_cover.name}")

    try:
        model.add_subcatchment(area, land_form, land_cover)
        logger.info("Successfully generated subcatchment")
    except Exception as e:
        logger.error(f"Failed to generate subcatchment: {e}")
        raise


def parse_args() -> Tuple[argparse.Namespace, argparse.ArgumentParser]:
    """Parse command-line arguments."""
    parser = create_parser()
    return parser.parse_args(), parser


def main() -> int:
    """Main CLI entry point."""
    args, parser = parse_args()

    if args.list_options:
        list_options()
        return 0

    logger = setup_logging(args.verbose)

    try:
        logger.info(f"Loading SWMM model: {args.input_file}")
        model = BuildCatchments(str(args.input_file))

        add_subcatchment(
            model=model,
            area=args.area,
            land_form=args.land_form,
            land_cover=args.land_cover,
            logger=logger
        )

        logger.info("Process completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
