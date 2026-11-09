"""Load the Cessna side view and remove the drawn propeller.

The file on disk keeps its original pixels. Preparation (mask, flip, level)
happens in memory. Only the procedural propeller is drawn on top.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

from cessna_sim.config import Config, project_root
from cessna_sim.sprite_geometry import rotate_offset


AIRCRAFT_PNG = project_root() / "assets" / "aircraft" / "2004_cessna_172s.png"


@dataclass
class PreparedAircraft:
    image: Image.Image
    cg_px: tuple[float, float]
    prop_hub_px: tuple[float, float]
    level_correction_deg: float


def _mask_disk(image: Image.Image, center: tuple[float, float], radius: float) -> None:
    pixels = image.load()
    width, height = image.size
    cx, cy = center
    radius_sq = radius * radius
    x0 = max(0, int(math.floor(cx - radius)))
    x1 = min(width, int(math.ceil(cx + radius)) + 1)
    y0 = max(0, int(math.floor(cy - radius)))
    y1 = min(height, int(math.ceil(cy + radius)) + 1)
    for x in range(x0, x1):
        for y in range(y0, y1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius_sq:
                pixels[x, y] = (0, 0, 0, 0)


def _flip_horizontal(image: Image.Image, points: list[tuple[float, float]]):
    flipped = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    width = image.size[0]
    moved = [((width - 1) - x, y) for x, y in points]
    return flipped, moved


def _rotate_expand(image: Image.Image, points: list[tuple[float, float]], angle_deg: float):
    """Counter-clockwise rotation, y down, expanding the canvas.

    Positive angle raises a nose that points right. This is the same sign as
    pygame.transform.rotozoom.
    """
    if abs(angle_deg) < 1e-9:
        return image, points
    width, height = image.size
    rotated = image.rotate(
        angle_deg,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor=(0, 0, 0, 0),
    )
    new_width, new_height = rotated.size
    moved = [
        _rotate_point(x, y, width, height, angle_deg, new_width, new_height) for x, y in points
    ]
    return rotated, moved


def _rotate_point(
    x: float,
    y: float,
    width: int,
    height: int,
    angle_deg: float,
    new_width: int,
    new_height: int,
) -> tuple[float, float]:
    dx, dy = rotate_offset(x - width / 2.0, y - height / 2.0, angle_deg)
    return (dx + new_width / 2.0, dy + new_height / 2.0)


def _opaque_bounds(image: Image.Image) -> tuple[int, int, int, int]:
    pixels = image.load()
    width, height = image.size
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found = False
    for x in range(width):
        for y in range(height):
            if pixels[x, y][3] > 40:
                found = True
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if not found:
        raise ValueError("Aircraft image has no opaque pixels")
    return min_x, min_y, max_x, max_y


def measure_cg(image: Image.Image) -> tuple[float, float]:
    """One third of the fuselage length aft of the nose, near the wing.

    The nose is the right-hand end after preparation. Vertically the point sits
    just under the local upper contour, which is the wing at that station.
    """
    pixels = image.load()
    min_x, _, max_x, _ = _opaque_bounds(image)
    cg_x = max_x - (max_x - min_x) / 3.0
    column = int(round(cg_x))
    ys = [y for y in range(image.size[1]) if pixels[column, y][3] > 40]
    if not ys:
        raise ValueError("No opaque pixels at the CG station")
    top = min(ys)
    return (cg_x, top + 36.0)


def window_line_angle_deg(image: Image.Image) -> float:
    """Angle of the dark cabin windows, y down. Zero is a horizontal fuselage."""
    pixels = image.load()
    width, height = image.size
    points: list[tuple[float, float]] = []
    for x in range(width // 5, 4 * width // 5):
        for y in range(height // 6, 3 * height // 4):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 200 and 40 < red < 130 and abs(int(red) - int(green)) < 30 and abs(int(green) - int(blue)) < 30:
                points.append((float(x), float(y)))
    if len(points) < 50:
        return 0.0
    mean_x = sum(point[0] for point in points) / len(points)
    mean_y = sum(point[1] for point in points) / len(points)
    sxx = sum((point[0] - mean_x) ** 2 for point in points)
    sxy = sum((point[0] - mean_x) * (point[1] - mean_y) for point in points)
    if sxx == 0.0:
        return 0.0
    return math.degrees(math.atan(sxy / sxx))


def prepare_aircraft(config: Config, path=AIRCRAFT_PNG) -> PreparedAircraft:
    """Mask the drawn propeller, point the nose right, and level the fuselage."""
    image = Image.open(path).convert("RGBA")
    _mask_disk(image, config.prop_hub_source_px, config.prop_mask_radius_px)
    hub = config.prop_hub_source_px
    if config.sprite_flip_horizontal:
        image, moved = _flip_horizontal(image, [hub])
        hub = moved[0]
    image, moved = _rotate_expand(image, [hub], config.sprite_level_correction_deg)
    hub = moved[0]
    cg = measure_cg(image)
    return PreparedAircraft(
        image=image,
        cg_px=cg,
        prop_hub_px=hub,
        level_correction_deg=config.sprite_level_correction_deg,
    )


def disk_is_clear(image: Image.Image, center: tuple[float, float], radius: float) -> bool:
    """True when the masked hub contains no opaque propeller pixels."""
    pixels = image.load()
    cx, cy = center
    checked = 0
    for x in range(int(cx - radius / 2), int(cx + radius / 2)):
        for y in range(int(cy - radius / 2), int(cy + radius / 2)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= (radius / 2) ** 2:
                checked += 1
                if pixels[x, y][3] > 10:
                    return False
    return checked > 0
