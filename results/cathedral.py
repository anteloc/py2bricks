from __future__ import annotations

"""
Build plan — cathedral

1) Site and forecourt
   - Create a rectangular site slab as the overall base for the model.
   - Add a paved forecourt and a straight processional path leading to the main west portal.
   - Keep the ground treatment simple so the cathedral massing remains the focus.

2) Nave and main body
   - Build a tall rectangular nave as the dominant central volume of the cathedral.
   - Cut a large main portal in the south-facing west front wall of the nave and add a rose-window-like opening above it.
   - Add clerestory windows to the nave sides and a trim band near the top to separate wall and roof.
   - Place a steep gable roof directly on top of the nave shell.

3) West front with twin towers
   - Build two tall front towers as a single westwork group.
   - Place the towers in front of the nave, one at each corner, leaving the central portal axis clear.
   - Add a shallow porch canopy between the towers so it reads as the main entrance composition.

4) Transepts, choir, and apse
   - Build two lower transept arms and place them beside the nave at mid-depth to create the cross plan.
   - Build a narrower choir block directly north of the nave.
   - Attach a still smaller apse block to the north side of the choir.
   - Place roofs on the transept arms, choir, and apse after their shells are built.

5) Crossing and final composition
   - Add a small crossing tower centered over the nave roof near the transept intersection.
   - Assemble the cathedral by positioning the westwork in front of the nave, the transept arms beside it,
     and the choir/apse behind it.
   - Place the complete cathedral on the site so the forecourt aligns with the main entry axis.
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
    GableRoof,
    Column,
    PartType,
    Color,
    attach,
    place,
)


# --- Overall scene ----------------------------------------------------------
SITE_W = 60
SITE_D = 64
FORECOURT_W = 26
FORECOURT_D = 10
PATH_W = 8
PATH_D = 10

# --- Main church body -------------------------------------------------------
NAVE_W = 20
NAVE_D = 30
NAVE_H = 10  # bricks

TR_ARM_W = 10
TR_ARM_D = 10
TR_ARM_H = 8
TR_ARM_Z = 10  # offset within nave depth

CHOIR_W = 16
CHOIR_D = 10
CHOIR_H = 8

APSE_W = 12
APSE_D = 8
APSE_H = 7

# --- West front -------------------------------------------------------------
TOWER_W = 7
TOWER_D = 8
TOWER_H = 15
WESTWORK_D = 11
PORCH_W = 6
PORCH_D = 3
PORCH_H = 6  # bricks

# --- Crossing tower ---------------------------------------------------------
CROSSING_W = 8
CROSSING_D = 8
CROSSING_H = 5

# --- Placement on site ------------------------------------------------------
CATHEDRAL_X = 10
CATHEDRAL_Z = 0
NAVE_X = TR_ARM_W
NAVE_Z = WESTWORK_D
WESTWORK_X = NAVE_X
WESTWORK_Z = 0
TRANSEPT_X = 0
TRANSEPT_Z = NAVE_Z + TR_ARM_Z
CHOIR_X = NAVE_X + (NAVE_W - CHOIR_W) // 2
CHOIR_Z = NAVE_Z + NAVE_D
FORECOURT_X = CATHEDRAL_X + NAVE_X - 3
FORECOURT_Z = 0
PATH_X = CATHEDRAL_X + NAVE_X + (NAVE_W - PATH_W) // 2
PATH_Z = 0

# --- Colors ----------------------------------------------------------------
GRASS = Color.DARK_GREEN
PAVING = Color.LIGHT_BLUISH_GREY
STONE = Color.LIGHT_GREY
TRIM = Color.DARK_BLUISH_GREY
ROOF = Color.DARK_RED
GLASS = Color.TRANS_LIGHT_BLUE
DOOR = Color.REDDISH_BROWN
METAL = Color.DARK_GREY
ACCENT = Color.DARK_TAN


# --- Helpers ----------------------------------------------------------------
def add_window(wall, x: int, y: int, width: int, height: int, part_type: PartType, color: int = GLASS) -> None:
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part_type, x=x, y=y, color=color)


def add_trim(shell: Box, top_y: int, color: int = TRIM) -> None:
    for wall in shell.walls():
        wall.ledge(y=top_y, overhang=1, color=color, part_type=PartType.PLATE_2X4)


def dress_nave(shell: Box) -> None:
    # Main west front / portal elevation.
    shell.south.opening(x=8, y=0, width=4, height=6)
    shell.south.insert(PartType.DOOR_1X4X6, x=8, y=0, color=DOOR)
    add_window(shell.south, x=8, y=6, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.south, x=3, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.south, x=15, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    # East end.
    add_window(shell.north, x=3, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.north, x=8, y=6, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=15, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    # Clerestory windows above the lower transept roofs.
    for wall in (shell.east, shell.west):
        add_window(wall, x=2, y=5, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
        add_window(wall, x=25, y=5, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_trim(shell, NAVE_H - 1)


def dress_transept_arm(shell: Box, outer_face: str) -> None:
    # Outer gable wall.
    outer = getattr(shell, outer_face)
    add_window(outer, x=3, y=3, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    # Long walls.
    add_window(shell.south, x=3, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=3, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_trim(shell, TR_ARM_H - 1)


def dress_choir(shell: Box) -> None:
    add_window(shell.north, x=6, y=4, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.east, x=3, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=7, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=3, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=7, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_trim(shell, CHOIR_H - 1)


def dress_apse(shell: Box) -> None:
    add_window(shell.north, x=4, y=3, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.east, x=3, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=3, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_trim(shell, APSE_H - 1)


def make_tower(name: str) -> Group:
    shell = Box(TOWER_W, TOWER_D, TOWER_H, color=STONE, fill_part=PartType.BRICK_2X4, name=f"{name}_tower_shell")

    # Bell-stage rhythm and lower lancet-like openings.
    add_window(shell.south, x=2, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.south, x=2, y=10, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.north, x=2, y=10, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=2, y=10, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=2, y=10, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_trim(shell, TOWER_H - 2, color=ACCENT)

    cap = FloorSlab(TOWER_W, TOWER_D, color=TRIM, fill_part=PartType.PLATE_2X4, name=f"{name}_tower_cap")
    tower = place(cap, on=shell, align="center")

    # Simple corner pinnacles and a low central roof block.
    pinnacle_y = shell.height_plates + 1
    for p_name, x, z in (
        ("sw", 0, 0),
        ("se", TOWER_W - 1, 0),
        ("nw", 0, TOWER_D - 1),
        ("ne", TOWER_W - 1, TOWER_D - 1),
    ):
        tower.add(
            Column(height=2, color=TRIM, part_type=PartType.BRICK_1X1, name=f"{name}_{p_name}_pinnacle"),
            x=x,
            y=pinnacle_y,
            z=z,
        )

    spire_base = Box(3, 4, 2, color=ROOF, fill_part=PartType.BRICK_2X4, name=f"{name}_spire_base")
    tower.add(spire_base, x=2, y=shell.height_plates + cap.height_plates, z=2)
    return tower


def make_westwork() -> Group:
    westwork = Group("westwork")
    westwork.add(make_tower("west"), x=0, y=0, z=3)
    westwork.add(make_tower("east"), x=NAVE_W - TOWER_W, y=0, z=3)

    porch = FloorSlab(PORCH_W, PORCH_D, color=ACCENT, fill_part=PartType.PLATE_2X4, name="main_porch_canopy")
    westwork.add(porch, x=(NAVE_W - PORCH_W) // 2, y=PORCH_H * 3, z=WESTWORK_D - PORCH_D)
    westwork.add(Column(height=PORCH_H, color=STONE, part_type=PartType.BRICK_1X1, name="porch_post_w"), x=8, y=0, z=WESTWORK_D - 1)
    westwork.add(Column(height=PORCH_H, color=STONE, part_type=PartType.BRICK_1X1, name="porch_post_e"), x=11, y=0, z=WESTWORK_D - 1)
    return westwork


def make_transept_group() -> Group:
    west_shell = Box(TR_ARM_W, TR_ARM_D, TR_ARM_H, color=STONE, fill_part=PartType.BRICK_2X4, name="west_transept_shell")
    dress_transept_arm(west_shell, "west")
    west_arm = place(GableRoof(TR_ARM_W, TR_ARM_D, ridge="east_west", color=ROOF, name="west_transept_roof"), on=west_shell)

    east_shell = Box(TR_ARM_W, TR_ARM_D, TR_ARM_H, color=STONE, fill_part=PartType.BRICK_2X4, name="east_transept_shell")
    dress_transept_arm(east_shell, "east")
    east_arm = place(GableRoof(TR_ARM_W, TR_ARM_D, ridge="east_west", color=ROOF, name="east_transept_roof"), on=east_shell)

    transepts = Group("transepts")
    transepts.add(west_arm, x=0, y=0, z=0)
    transepts.add(east_arm, x=TR_ARM_W + NAVE_W, y=0, z=0)
    return transepts


def make_choir_complex() -> Group:
    choir_shell = Box(CHOIR_W, CHOIR_D, CHOIR_H, color=STONE, fill_part=PartType.BRICK_2X4, name="choir_shell")
    dress_choir(choir_shell)
    choir = place(GableRoof(CHOIR_W, CHOIR_D, ridge="north_south", color=ROOF, name="choir_roof"), on=choir_shell)

    apse_shell = Box(APSE_W, APSE_D, APSE_H, color=STONE, fill_part=PartType.BRICK_2X4, name="apse_shell")
    dress_apse(apse_shell)
    apse = place(GableRoof(APSE_W, APSE_D, ridge="east_west", color=ROOF, name="apse_roof"), on=apse_shell)

    return attach(apse, to=choir, face="north", align="center")


def make_crossing_tower() -> Group:
    shell = Box(CROSSING_W, CROSSING_D, CROSSING_H, color=STONE, fill_part=PartType.BRICK_2X4, name="crossing_tower_shell")
    for wall in shell.walls():
        add_window(wall, x=3, y=1, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_trim(shell, CROSSING_H - 1, color=ACCENT)
    roof = GableRoof(CROSSING_W, CROSSING_D, ridge="east_west", color=ROOF, name="crossing_tower_roof")
    return place(roof, on=shell)


def main() -> None:
    scene = Scene("cathedral")

    site = Group("site")
    site.add(FloorSlab(SITE_W, SITE_D, color=GRASS, fill_part=PartType.PLATE_2X4, name="site_base"), x=0, y=0, z=0)
    site.add(FloorSlab(FORECOURT_W, FORECOURT_D, color=PAVING, fill_part=PartType.PLATE_2X4, name="forecourt"), x=FORECOURT_X, y=1, z=FORECOURT_Z)
    site.add(FloorSlab(PATH_W, PATH_D, color=PAVING, fill_part=PartType.PLATE_2X4, name="processional_path"), x=PATH_X, y=1, z=PATH_Z)

    cathedral = Group("cathedral")

    nave_shell = Box(NAVE_W, NAVE_D, NAVE_H, color=STONE, fill_part=PartType.BRICK_2X4, name="nave_shell")
    dress_nave(nave_shell)
    nave_roof = GableRoof(NAVE_W, NAVE_D, ridge="north_south", color=ROOF, name="nave_roof")
    nave = place(nave_roof, on=nave_shell)
    cathedral.add(nave, x=NAVE_X, y=1, z=NAVE_Z)

    cathedral.add(make_westwork(), x=WESTWORK_X, y=1, z=WESTWORK_Z)
    cathedral.add(make_transept_group(), x=TRANSEPT_X, y=1, z=TRANSEPT_Z)
    cathedral.add(make_choir_complex(), x=CHOIR_X, y=1, z=CHOIR_Z)

    crossing = make_crossing_tower()
    cathedral.add(
        crossing,
        x=NAVE_X + (NAVE_W - CROSSING_W) // 2,
        y=1 + nave_shell.height_plates + nave_roof.height_plates,
        z=NAVE_Z + TR_ARM_Z + 1,
    )

    site.add(cathedral, x=CATHEDRAL_X, y=0, z=CATHEDRAL_Z)
    scene.add(site, x=0, y=0, z=0)

    out_path = ROOT / "cathedral.mpd"
    output = scene.export(str(out_path))
    print(scene.stats())
    print(output)

if __name__ == "__main__":
    main()
