#!/usr/bin/env python3
"""Entry point for Rapid Catchment Generator CLI."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rcg.cli import main

if __name__ == "__main__":
    sys.exit(main())