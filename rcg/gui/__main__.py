"""``python -m rcg.gui`` (also the PyInstaller entry script)."""

from __future__ import annotations

import sys

from rcg.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
