"""Erzeugt deterministisch alle Icons des Plugins VEQRA FORM.

Erzeugt werden (gemaess offizieller Allplan 2025 ALLEP-Dokumentation,
Abschnitt Tools: je Werkzeug ein 24x24- und ein 128x128-PNG; Aufbau wie
im offiziellen PythonPart SDK Paket):

- PythonPartsActionbar/VeqraFormCuboid_24.png
- PythonPartsActionbar/VeqraFormCuboid_128.png
- Library/VeqraFormCuboid.png (Vorschaubild in der Bibliothek)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parent.parent

ACTIONBAR_DIR = REPO_ROOT / "PythonPartsActionbar"
LIBRARY_DIR = REPO_ROOT / "Library"

LIGHT_LINE = (28, 60, 100, 255)
LIGHT_FILL = (86, 156, 214, 255)
LIGHT_TOP = (140, 195, 240, 255)
DARK_LINE = (220, 232, 245, 255)
DARK_FILL = (70, 130, 190, 255)
DARK_TOP = (110, 170, 225, 255)


def _draw_cuboid(size: int, dark: bool) -> Image.Image:
    """Zeichnet ein isometrisches Quader-Icon in der gewuenschten Groesse."""

    line = DARK_LINE if dark else LIGHT_LINE
    fill = DARK_FILL if dark else LIGHT_FILL
    top = DARK_TOP if dark else LIGHT_TOP

    scale = 4
    px = size * scale
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    m = px * 0.12          # Rand
    dx = px * 0.30         # isometrischer Versatz X
    dy = px * 0.18         # isometrischer Versatz Y

    x0, y0 = m, m + dy
    x1, y1 = px - m - dx, px - m

    front = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    top_face = [(x0, y0), (x0 + dx, y0 - dy), (x1 + dx, y0 - dy), (x1, y0)]
    side = [(x1, y0), (x1 + dx, y0 - dy), (x1 + dx, y1 - dy), (x1, y1)]

    width = max(scale, px // 24)

    draw.polygon(front, fill=fill, outline=line)
    draw.polygon(top_face, fill=top, outline=line)
    draw.polygon(side, fill=fill, outline=line)

    for face in (front, top_face, side):
        draw.line(face + [face[0]], fill=line, width=width, joint="curve")

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    ACTIONBAR_DIR.mkdir(parents=True, exist_ok=True)
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    targets = [
        (ACTIONBAR_DIR / "VeqraFormCuboid_24.png", 24, False),
        (ACTIONBAR_DIR / "VeqraFormCuboid_128.png", 128, False),
        (LIBRARY_DIR / "VeqraFormCuboid.png", 128, False),
    ]

    for path, size, dark in targets:
        _draw_cuboid(size, dark).save(path, format="PNG")
        print(f"erzeugt: {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
