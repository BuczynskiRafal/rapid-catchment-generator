"""``python -m rcg`` runs the command-line interface."""

import sys

from rcg.cli import main

if __name__ == "__main__":
    sys.exit(main())
