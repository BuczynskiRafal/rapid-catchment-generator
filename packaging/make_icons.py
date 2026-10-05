"""Render the application icon from its SVG source.

    python packaging/make_icons.py

Reads ``rcg/gui/resources/icon.svg`` and writes, next to it:

* ``icon.png``: 1024 x 1024, the window icon and the source PyInstaller turns into
  ``.icns`` on macOS;
* ``icon.ico``: 16 to 256 px, each size rendered from the vector source (not
  downscaled from one bitmap), for the Windows executable and taskbar.

Needs PySide6 (QtSvg) only; the ``.ico`` container is written directly.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

RESOURCES = Path(__file__).resolve().parent.parent / "rcg" / "gui" / "resources"
SVG = RESOURCES / "icon.svg"
PNG_SIZE = 1024
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def render(renderer: QSvgRenderer, size: int) -> QImage:
    """Rasterise the SVG at *size* x *size* with antialiasing on a transparent background."""
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return image


def png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("PNG encoding failed")
    buffer.close()
    return bytes(data)


def write_ico(path: Path, images: dict[int, bytes]) -> None:
    """Write PNG-compressed entries into one ``.ico`` (supported since Windows Vista)."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    directory, blobs = b"", b""
    for size, blob in sorted(images.items()):
        dim = 0 if size >= 256 else size  # 0 means 256 in the directory entry
        directory += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(blob), offset + len(blobs))
        blobs += blob
    path.write_bytes(header + directory + blobs)


def main() -> int:
    _app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    renderer = QSvgRenderer(str(SVG))
    if not renderer.isValid():
        print(f"Cannot read {SVG}", file=sys.stderr)
        return 1
    if not render(renderer, PNG_SIZE).save(str(RESOURCES / "icon.png"), "PNG"):
        print("Cannot write icon.png", file=sys.stderr)
        return 1
    write_ico(RESOURCES / "icon.ico", {size: png_bytes(render(renderer, size)) for size in ICO_SIZES})
    print(f"Wrote icon.png ({PNG_SIZE} px) and icon.ico ({', '.join(map(str, ICO_SIZES))} px) to {RESOURCES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
