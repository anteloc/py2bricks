"""
Build plan for a building inspired by a Spanish guitar.

1. Site and forecourt
- Lay down a simple plaza slab as the site.
- Center a narrow entry path on the building axis.
- Add a shallow front terrace so the body of the building can begin behind it.

2. Guitar body volumes
- Build the body from three stacked north-south masonry volumes: a broad lower bout,
  a narrower waist, and a slightly smaller upper bout.
- Keep all three sections centered on the same axis so the changing width reads as a
  guitar silhouette when viewed from above.
- Cap each body section with its own terracotta roof so they remain legible as separate
  parts of the instrument-inspired massing.

3. Neck and headstock tower
- Continue the centerline north with a narrower neck tower rising above the body.
- Finish the neck with a projecting cap and small finials so the top suggests a headstock.
- Add shallow ledges on the south face of the neck to evoke guitar frets.

4. Spanish-guitar facade details
- Place the main entry in the lower bout on the south elevation.
- Build a rosette-inspired window composition in the waist above a small balcony.
- Add six slender front pilasters in front of the lower bout to suggest guitar strings.
- Use warm stucco walls, dark wood accents, and a dark red tile roof palette.

5. Final assembly
- Collect all volumes and details into one centered group.
- Place the completed building on the site slab, export the MPD file, and print stats.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py2bricks import (
    Scene,
    Group,
    Box,
    FloorSlab,
    GableRoof,
    Column,
    PartType,
    Color,
    place,
)


SITE_W = 64
SITE_D = 96

BODY_H = 8
NECK_H = 13

LOWER_W = 38
LOWER_D = 18
WAIST_W = 24
WAIST_D = 16
UPPER_W = 34
UPPER_D = 14
NECK_W = 12
NECK_D = 16

BUILDING_W = LOWER_W
BUILDING_D = 4 + LOWER_D + WAIST_D + UPPER_D + 17

SITE_COLOR = Color.LIGHT_BLUISH_GREY
PATH_COLOR = Color.DARK_TAN
TERRACE_COLOR = Color.DARK_TAN
WALL_COLOR = Color.TAN
NECK_COLOR = Color.DARK_TAN
TRIM_COLOR = Color.DARK_RED
ROOF_COLOR = Color.DARK_RED
WINDOW_COLOR = Color.TRANS_LIGHT_BLUE
DOOR_COLOR = Color.REDDISH_BROWN
STRING_COLOR = Color.DARK_BLUISH_GREY
STONE_COLOR = Color.LIGHT_GREY
WOOD_COLOR = Color.REDDISH_BROWN


LOWER_X = 0
LOWER_Z = 4
WAIST_X = (LOWER_W - WAIST_W) // 2
WAIST_Z = LOWER_Z + LOWER_D
UPPER_X = (LOWER_W - UPPER_W) // 2
UPPER_Z = WAIST_Z + WAIST_D
NECK_X = (LOWER_W - 16) // 2
NECK_Z = UPPER_Z + UPPER_D



def add_cornice(box: Box, height: int) -> None:
    for wall in box.walls():
        wall.ledge(
            y=height - 1,
            overhang=1,
            color=TRIM_COLOR,
            part_type=PartType.PLATE_2X4,
        )



def dress_lower_bout(box: Box) -> None:
    south = box.south
    south.opening(x=17, y=0, width=4, height=6)
    south.insert(PartType.DOOR_1X4X6, x=17, y=0, color=DOOR_COLOR)
    for x in (5, 29):
        south.opening(x=x, y=2, width=4, height=3)
        south.insert(PartType.WINDOW_1X4X3, x=x, y=2, color=WINDOW_COLOR)

    box.north.window_row(
        y=2,
        width=4,
        height=3,
        count=3,
        part_type=PartType.WINDOW_1X4X3,
        spacing="even",
        color=WINDOW_COLOR,
    )

    for wall in (box.east, box.west):
        wall.window_row(
            y=2,
            width=2,
            height=3,
            count=3,
            part_type=PartType.WINDOW_1X2X3,
            spacing="even",
            color=WINDOW_COLOR,
        )

    add_cornice(box, BODY_H)



def dress_waist(box: Box) -> None:
    south = box.south
    south.opening(x=10, y=2, width=4, height=3)
    south.insert(PartType.WINDOW_1X4X3, x=10, y=2, color=WINDOW_COLOR)
    for x in (7, 15):
        south.opening(x=x, y=2, width=2, height=3)
        south.insert(PartType.WINDOW_1X2X3, x=x, y=2, color=WINDOW_COLOR)
    south.opening(x=11, y=5, width=2, height=2)
    south.insert(PartType.WINDOW_1X2X2, x=11, y=5, color=WINDOW_COLOR)

    box.north.window_row(
        y=2,
        width=4,
        height=3,
        count=2,
        part_type=PartType.WINDOW_1X4X3,
        spacing="even",
        color=WINDOW_COLOR,
    )

    for wall in (box.east, box.west):
        wall.window_row(
            y=2,
            width=2,
            height=3,
            count=2,
            part_type=PartType.WINDOW_1X2X3,
            spacing="even",
            color=WINDOW_COLOR,
        )

    add_cornice(box, BODY_H)



def dress_upper_bout(box: Box) -> None:
    for wall in (box.south, box.north):
        wall.window_row(
            y=2,
            width=4,
            height=3,
            count=3,
            part_type=PartType.WINDOW_1X4X3,
            spacing="even",
            color=WINDOW_COLOR,
        )

    for wall in (box.east, box.west):
        wall.window_row(
            y=2,
            width=2,
            height=3,
            count=2,
            part_type=PartType.WINDOW_1X2X3,
            spacing="even",
            color=WINDOW_COLOR,
        )

    add_cornice(box, BODY_H)



def dress_neck(box: Box) -> None:
    south = box.south
    for y in (2, 6, 10):
        south.opening(x=5, y=y, width=2, height=3)
        south.insert(PartType.WINDOW_1X2X3, x=5, y=y, color=WINDOW_COLOR)

    north = box.north
    north.opening(x=5, y=3, width=2, height=3)
    north.insert(PartType.WINDOW_1X2X3, x=5, y=3, color=WINDOW_COLOR)
    north.opening(x=5, y=8, width=2, height=3)
    north.insert(PartType.WINDOW_1X2X3, x=5, y=8, color=WINDOW_COLOR)

    for wall in (box.east, box.west):
        wall.window_row(
            y=4,
            width=2,
            height=3,
            count=2,
            part_type=PartType.WINDOW_1X2X3,
            spacing="even",
            color=WINDOW_COLOR,
        )

    add_cornice(box, NECK_H)



def make_body_section(name: str, width: int, depth: int, roof_name: str, *, color: int) -> Group:
    section = Group(name)
    shell = Box(width, depth, BODY_H, color=color, fill_part=PartType.BRICK_2X4, name=f"{name}_shell")
    if name == "lower_bout":
        dress_lower_bout(shell)
    elif name == "waist":
        dress_waist(shell)
    else:
        dress_upper_bout(shell)

    roof = GableRoof(width, depth, ridge="north_south", color=ROOF_COLOR, name=roof_name)
    shell_with_roof = place(roof, on=shell, align="center")
    section.add(shell_with_roof, x=0, y=0, z=0)
    return section



def make_neck_tower() -> Group:
    tower = Group("neck_tower")
    neck = Box(NECK_W, NECK_D, NECK_H, color=NECK_COLOR, fill_part=PartType.BRICK_2X4, name="neck_shell")
    dress_neck(neck)
    tower.add(neck, x=2, y=0, z=1)

    # Flat projecting cap to suggest a headstock.
    headstock = FloorSlab(
        width=16,
        depth=8,
        color=TRIM_COLOR,
        fill_part=PartType.PLATE_2X4,
        name="headstock_cap",
    )
    tower.add(headstock, x=0, y=neck.height_plates, z=7)

    # Small finials / tuners on the cap.
    tower.add(Column(height=2, color=WOOD_COLOR, part_type=PartType.BRICK_1X1, name="tuner_west"), x=1, y=neck.height_plates + 1, z=8)
    tower.add(Column(height=2, color=WOOD_COLOR, part_type=PartType.BRICK_1X1, name="tuner_east"), x=14, y=neck.height_plates + 1, z=8)
    tower.add(Column(height=2, color=WOOD_COLOR, part_type=PartType.BRICK_1X1, name="tuner_west_rear"), x=1, y=neck.height_plates + 1, z=13)
    tower.add(Column(height=2, color=WOOD_COLOR, part_type=PartType.BRICK_1X1, name="tuner_east_rear"), x=14, y=neck.height_plates + 1, z=13)

    # Shallow fret-like ledges on the south face.
    for idx, y in enumerate((11, 20, 29), start=1):
        tower.add(
            FloorSlab(
                width=10,
                depth=1,
                color=STONE_COLOR,
                fill_part=PartType.PLATE_1X4,
                name=f"fret_{idx}",
            ),
            x=3,
            y=y,
            z=0,
        )

    return tower



def make_guitar_building() -> Group:
    building = Group("guitar_building")

    lower = make_body_section("lower_bout", LOWER_W, LOWER_D, "lower_roof", color=WALL_COLOR)
    waist = make_body_section("waist", WAIST_W, WAIST_D, "waist_roof", color=WALL_COLOR)
    upper = make_body_section("upper_bout", UPPER_W, UPPER_D, "upper_roof", color=WALL_COLOR)
    neck = make_neck_tower()

    building.add(lower, x=LOWER_X, y=0, z=LOWER_Z)
    building.add(waist, x=WAIST_X, y=0, z=WAIST_Z)
    building.add(upper, x=UPPER_X, y=0, z=UPPER_Z)
    building.add(neck, x=NECK_X, y=0, z=NECK_Z)

    # Front terrace and balcony.
    building.add(
        FloorSlab(
            width=18,
            depth=4,
            color=TERRACE_COLOR,
            fill_part=PartType.PLATE_2X4,
            name="front_terrace",
        ),
        x=10,
        y=0,
        z=0,
    )

    building.add(
        FloorSlab(
            width=12,
            depth=3,
            color=TRIM_COLOR,
            fill_part=PartType.PLATE_2X4,
            name="rosette_balcony",
        ),
        x=13,
        y=9,
        z=19,
    )
    building.add(Column(height=3, color=STONE_COLOR, part_type=PartType.BRICK_1X1, name="balcony_post_w"), x=14, y=0, z=20)
    building.add(Column(height=3, color=STONE_COLOR, part_type=PartType.BRICK_1X1, name="balcony_post_e"), x=23, y=0, z=20)

    # Six string-like pilasters in front of the lower bout.
    for idx, x in enumerate((8, 12, 16, 20, 24, 28), start=1):
        building.add(
            Column(
                height=7,
                color=STRING_COLOR,
                part_type=PartType.BRICK_1X1,
                name=f"string_{idx}",
            ),
            x=x,
            y=0,
            z=3,
        )

    # Low stone plinths to anchor the terrace corners.
    building.add(Column(height=2, color=STONE_COLOR, part_type=PartType.BRICK_1X1, name="plinth_sw"), x=10, y=0, z=0)
    building.add(Column(height=2, color=STONE_COLOR, part_type=PartType.BRICK_1X1, name="plinth_se"), x=27, y=0, z=0)

    return building



def main() -> None:
    scene = Scene("spanish_guitar_building")

    site = FloorSlab(SITE_W, SITE_D, color=SITE_COLOR, fill_part=PartType.PLATE_2X4, name="site")
    scene.add(site, x=0, y=0, z=0)

    building = make_guitar_building()
    building_x = (SITE_W - BUILDING_W) // 2
    building_z = 12
    scene.add(building, x=building_x, y=1, z=building_z)

    path = FloorSlab(6, 12, color=PATH_COLOR, fill_part=PartType.PLATE_2X4, name="entry_path")
    scene.add(path, x=building_x + (BUILDING_W - 6) // 2, y=1, z=0)

    out_path = __file__.replace(".py", ".mpd")
    scene.export(out_path)
    print(scene.stats())


if __name__ == "__main__":
    main()
