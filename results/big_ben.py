from __future__ import annotations

"""
Build plan — Big Ben tower

1) Site and setting
   - Create a simple paved site slab as the global base for the model.
   - Add a slightly raised podium block near the center so the tower has a civic plinth.
   - Keep the ground treatment spare so the tower silhouette remains dominant.

2) Lower tower and entrance stage
   - Build a broad square lower stage as the tower base.
   - Cut the main south-facing entrance and add regular windows on the other visible faces.
   - Add slim corner buttress columns and a trim band near the top of the base.

3) Main shaft
   - Stack a narrower lower shaft directly on the base, centered.
   - Stack a slightly narrower upper shaft on top of that lower shaft, also centered.
   - Add repeated narrow windows to the shaft faces so the elevation reads tall and vertical.
   - Continue the corner columns upward to suggest the tower's Gothic framing.

4) Clock stage and belfry
   - Place a slightly wider clock stage on top of the upper shaft so it projects beyond the shaft below.
   - Add one large clock-face opening on each side and wrap the stage with accent trim.
   - Stack a smaller belfry block above the clock stage and add taller bell-stage openings.

5) Roof and final composition
   - Add a steep upper roof block and a smaller spire block above the belfry.
   - Place four corner pinnacles around the roof and a thin central finial on top.
   - Assemble all stages vertically in one tower group and place that group on the site podium.
"""

import sys
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "work_instructions"))

from py2bricks import (
    Scene,
    Group,
    Box,
    FloorSlab,
    Column,
    PartType,
    Color,
)


# --- Overall scene ----------------------------------------------------------
SITE_W = 40
SITE_D = 40
PLAZA_W = 24
PLAZA_D = 24
PODIUM_W = 22
PODIUM_D = 22
PODIUM_H = 2  # bricks

# --- Tower stages -----------------------------------------------------------
BASE_W = 18
BASE_D = 18
BASE_H = 9

LOWER_SHAFT_W = 14
LOWER_SHAFT_D = 14
LOWER_SHAFT_H = 21

UPPER_SHAFT_W = 12
UPPER_SHAFT_D = 12
UPPER_SHAFT_H = 12

CLOCK_W = 16
CLOCK_D = 16
CLOCK_H = 6

BELFRY_W = 10
BELFRY_D = 10
BELFRY_H = 8

ROOF_W = 8
ROOF_D = 8
ROOF_H = 4

SPIRE_W = 4
SPIRE_D = 4
SPIRE_H = 5
FINIAL_H = 6
PINNACLE_H = 4

# --- Placement --------------------------------------------------------------
PLAZA_X = (SITE_W - PLAZA_W) // 2
PLAZA_Z = (SITE_D - PLAZA_D) // 2
PODIUM_X = (SITE_W - PODIUM_W) // 2
PODIUM_Z = (SITE_D - PODIUM_D) // 2
TOWER_X = PODIUM_X + (PODIUM_W - BASE_W) // 2
TOWER_Z = PODIUM_Z + (PODIUM_D - BASE_D) // 2

# --- Colors ----------------------------------------------------------------
GROUND = Color.LIGHT_BLUISH_GREY
PAVING = Color.DARK_BLUISH_GREY
STONE = Color.TAN
TRIM = Color.DARK_TAN
ROOF = Color.DARK_GREY
CLOCK = Color.WHITE
ACCENT = Color.YELLOW
DOOR = Color.BLACK
GLASS = Color.TRANS_LIGHT_BLUE


# --- Helpers ----------------------------------------------------------------
def add_window(wall, x: int, y: int, width: int, height: int, part_type: PartType, color: int = GLASS) -> None:
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part_type, x=x, y=y, color=color)


def add_trim(shell: Box, y: int, color: int = TRIM) -> None:
    for wall in shell.walls():
        wall.ledge(y=y, overhang=1, color=color, part_type=PartType.PLATE_2X4)


def add_corner_columns(group: Group, width: int, depth: int, height: int, name: str, color: int = TRIM) -> None:
    for suffix, x, z in (
        ("sw", 0, 0),
        ("se", width - 1, 0),
        ("nw", 0, depth - 1),
        ("ne", width - 1, depth - 1),
    ):
        group.add(
            Column(height=height, color=color, part_type=PartType.BRICK_1X1, name=f"{name}_{suffix}"),
            x=x,
            y=0,
            z=z,
        )


def dress_base(shell: Box) -> None:
    shell.south.opening(x=7, y=0, width=4, height=6)
    shell.south.insert(PartType.DOOR_1X4X6, x=7, y=0, color=DOOR)
    add_window(shell.south, x=3, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.south, x=13, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_window(shell.north, x=4, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=10, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    add_window(shell.east, x=3, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=10, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=3, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=10, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_trim(shell, BASE_H - 2)


def dress_lower_shaft(shell: Box) -> None:
    for y in (3, 10, 17):
        add_window(shell.south, x=6, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(shell.north, x=6, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(shell.east, x=6, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(shell.west, x=6, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_trim(shell, LOWER_SHAFT_H - 2)


def dress_upper_shaft(shell: Box) -> None:
    for y in (2, 7):
        add_window(shell.south, x=5, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(shell.north, x=5, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(shell.east, x=5, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(shell.west, x=5, y=y, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_trim(shell, UPPER_SHAFT_H - 2)


def add_clock_face(wall) -> None:
    add_window(wall, x=6, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3, color=CLOCK)


def dress_clock_stage(shell: Box) -> None:
    for wall in shell.walls():
        add_clock_face(wall)
        wall.ledge(y=0, overhang=1, color=ACCENT, part_type=PartType.PLATE_2X4)
    add_trim(shell, CLOCK_H - 2, color=ACCENT)


def dress_belfry(shell: Box) -> None:
    for wall in shell.walls():
        add_window(wall, x=3, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_trim(shell, BELFRY_H - 2, color=ACCENT)


def make_big_ben() -> Group:
    tower = Group("big_ben")

    base = Box(BASE_W, BASE_D, BASE_H, color=STONE, fill_part=PartType.BRICK_2X4, name="base_stage")
    dress_base(base)
    base_group = Group("base_group")
    base_group.add(base, x=0, y=0, z=0)
    add_corner_columns(base_group, BASE_W, BASE_D, BASE_H, "base_corner")
    tower.add(base_group, x=0, y=0, z=0)

    lower = Box(LOWER_SHAFT_W, LOWER_SHAFT_D, LOWER_SHAFT_H, color=STONE, fill_part=PartType.BRICK_2X4, name="lower_shaft")
    dress_lower_shaft(lower)
    lower_group = Group("lower_shaft_group")
    lower_group.add(lower, x=0, y=0, z=0)
    add_corner_columns(lower_group, LOWER_SHAFT_W, LOWER_SHAFT_D, LOWER_SHAFT_H, "lower_corner")
    tower.add(lower_group, x=(BASE_W - LOWER_SHAFT_W) // 2, y=base.height_plates, z=(BASE_D - LOWER_SHAFT_D) // 2)

    upper = Box(UPPER_SHAFT_W, UPPER_SHAFT_D, UPPER_SHAFT_H, color=STONE, fill_part=PartType.BRICK_2X4, name="upper_shaft")
    dress_upper_shaft(upper)
    upper_group = Group("upper_shaft_group")
    upper_group.add(upper, x=0, y=0, z=0)
    add_corner_columns(upper_group, UPPER_SHAFT_W, UPPER_SHAFT_D, UPPER_SHAFT_H, "upper_corner")
    tower.add(
        upper_group,
        x=(BASE_W - UPPER_SHAFT_W) // 2,
        y=base.height_plates + lower.height_plates,
        z=(BASE_D - UPPER_SHAFT_D) // 2,
    )

    clock = Box(CLOCK_W, CLOCK_D, CLOCK_H, color=STONE, fill_part=PartType.BRICK_2X4, name="clock_stage")
    dress_clock_stage(clock)
    tower.add(
        clock,
        x=(BASE_W - CLOCK_W) // 2,
        y=base.height_plates + lower.height_plates + upper.height_plates,
        z=(BASE_D - CLOCK_D) // 2,
    )

    belfry = Box(BELFRY_W, BELFRY_D, BELFRY_H, color=STONE, fill_part=PartType.BRICK_2X4, name="belfry")
    dress_belfry(belfry)
    tower.add(
        belfry,
        x=(BASE_W - BELFRY_W) // 2,
        y=base.height_plates + lower.height_plates + upper.height_plates + clock.height_plates,
        z=(BASE_D - BELFRY_D) // 2,
    )

    roof = Box(ROOF_W, ROOF_D, ROOF_H, color=ROOF, fill_part=PartType.BRICK_2X4, name="roof_block")
    tower.add(
        roof,
        x=(BASE_W - ROOF_W) // 2,
        y=base.height_plates + lower.height_plates + upper.height_plates + clock.height_plates + belfry.height_plates,
        z=(BASE_D - ROOF_D) // 2,
    )

    roof_top_y = base.height_plates + lower.height_plates + upper.height_plates + clock.height_plates + belfry.height_plates + roof.height_plates

    spire = Box(SPIRE_W, SPIRE_D, SPIRE_H, color=ROOF, fill_part=PartType.BRICK_2X4, name="spire_block")
    tower.add(spire, x=(BASE_W - SPIRE_W) // 2, y=roof_top_y, z=(BASE_D - SPIRE_D) // 2)

    pinnacle_y = roof_top_y - 3
    for suffix, x, z in (
        ("sw", (BASE_W - ROOF_W) // 2, (BASE_D - ROOF_D) // 2),
        ("se", (BASE_W - ROOF_W) // 2 + ROOF_W - 1, (BASE_D - ROOF_D) // 2),
        ("nw", (BASE_W - ROOF_W) // 2, (BASE_D - ROOF_D) // 2 + ROOF_D - 1),
        ("ne", (BASE_W - ROOF_W) // 2 + ROOF_W - 1, (BASE_D - ROOF_D) // 2 + ROOF_D - 1),
    ):
        tower.add(Column(height=PINNACLE_H, color=ACCENT, part_type=PartType.BRICK_1X1, name=f"pinnacle_{suffix}"), x=x, y=pinnacle_y, z=z)

    tower.add(
        Column(height=FINIAL_H, color=ACCENT, part_type=PartType.BRICK_1X1, name="finial"),
        x=(BASE_W - 1) // 2,
        y=roof_top_y + spire.height_plates,
        z=(BASE_D - 1) // 2,
    )

    return tower


def main() -> None:
    scene = Scene("big_ben")

    site = Group("site")
    site.add(FloorSlab(SITE_W, SITE_D, color=GROUND, fill_part=PartType.PLATE_2X4, name="site_base"), x=0, y=0, z=0)
    site.add(FloorSlab(PLAZA_W, PLAZA_D, color=PAVING, fill_part=PartType.PLATE_2X4, name="plaza"), x=PLAZA_X, y=1, z=PLAZA_Z)
    podium = Box(PODIUM_W, PODIUM_D, PODIUM_H, color=STONE, fill_part=PartType.BRICK_2X4, name="podium")
    add_trim(podium, PODIUM_H - 1, color=TRIM)
    site.add(podium, x=PODIUM_X, y=1, z=PODIUM_Z)

    tower = make_big_ben()
    site.add(tower, x=TOWER_X, y=1 + podium.height_plates, z=TOWER_Z)

    scene.add(site, x=0, y=0, z=0)

    out_path = ROOT / "big_ben.mpd"
    output = scene.export(str(out_path))
    print(scene.stats())
    print(output)

    bundle_path = ROOT / "big_ben_bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(ROOT / "big_ben.py", arcname="big_ben.py")
        zf.write(out_path, arcname="big_ben.mpd")
    print(bundle_path)


if __name__ == "__main__":
    main()
