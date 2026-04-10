"""
Build plan — 4-floor residential apartment building

1) Site
   - Create a ground slab slightly larger than the building footprint to act as a site pad.

2) Ground floor
   - Lay a site-coloured floor plate matching the building footprint.
   - Build a solid exterior shell (28 × 20 studs, 8 bricks tall) in a warm base colour.
   - South elevation: four apartment windows flanking a wider, taller centred entry door.
   - North elevation: four apartment windows at the same rhythm.
   - East and west elevations: three evenly-spaced narrow windows each.
   - Add an accent-coloured trim ledge along the top of every exterior wall.
   - Inside the shell add two apartment units separated by a longitudinal party wall.
   - Each apartment is further split into two rooms by a transverse room-divider wall
     with a doorway opening.
   - Add a small canopy slab above the main entry door and a wider stoop slab in front.

3) Residential floors (× 3)
   - Lay a light-coloured floor plate on each level.
   - Build the same exterior shell shape and window rhythm as the ground floor, but
     without the entry door (all four sides get plain window rows).
   - Replicate the same interior apartment partitions on every upper floor.
   - Add two shallow balcony slabs on the south elevation, each supported by a pair of
     slender corner posts and fronted by a low railing wall.

4) Roof
   - Lay a dark-coloured roof plate across the full footprint.
   - Build a low parapet (2 bricks tall) around the perimeter with a white trim ledge.
   - Place a small rooftop bulkhead box at the centre (stair-tower access and mechanical).
   - Add a thin HVAC vent column near the rear corner of the roof.

5) Composition / connections
   - The site pad is the global base for the whole scene.
   - The ground floor sits directly on the site pad.
   - The three residential floors are produced by stacking one template floor three times,
     then placed on top of the ground floor aligned to the same origin.
   - The roof is placed on top of the full residential stack, also origin-aligned.
"""

from __future__ import annotations

# Make the sibling py2bricks package importable when this script sits next to it.

from py2bricks import (
    Scene,
    Group,
    Box,
    FloorSlab,
    WallLayout,
    Column,
    PartType,
    Color,
    place,
)


# Overall dimensions in studs.
BUILDING_WIDTH = 28
BUILDING_DEPTH = 20
FLOOR_HEIGHT = 8          # bricks
FLOOR_COUNT = 4
PARAPET_HEIGHT = 2        # bricks

# Interior apartment layout (inside the 2-stud-thick exterior shell).
INNER_X = 2
INNER_Z = 2
INNER_WIDTH = BUILDING_WIDTH - 4   # 24
INNER_DEPTH = BUILDING_DEPTH - 4   # 16
PARTY_WALL_X = 13                  # 11-stud apt + 2-stud wall + 11-stud apt
ROOM_DIVIDER_Z = 9                 # 7-stud room + 2-stud wall + 7-stud room
APARTMENT_WIDTH = 11
ROOM_DEPTH = 7

# Colors: warm residential palette.
SITE_COLOR = Color.LIGHT_BLUISH_GREY
BASE_COLOR = Color.DARK_TAN
WALL_COLOR = Color.TAN
TRIM_COLOR = Color.WHITE
ACCENT_COLOR = Color.SAND_GREEN
ROOF_COLOR = Color.DARK_BLUISH_GREY
WINDOW_COLOR = Color.TRANS_LIGHT_BLUE
DOOR_FRAME_COLOR = Color.DARK_BLUISH_GREY
DOOR_PANEL_COLOR = Color.DARK_RED
INTERIOR_WALL_COLOR = Color.WHITE
STAIR_TOWER_COLOR = Color.LIGHT_BLUISH_GREY
RAILING_COLOR = Color.SAND_GREEN
HVAC_COLOR = Color.DARK_GREY



def add_floor_plate(floor: Group, name: str, color: int) -> None:
    floor.add(
        FloorSlab(
            width=BUILDING_WIDTH,
            depth=BUILDING_DEPTH,
            color=color,
            fill_part=PartType.PLATE_2X4,
            name=name,
        ),
        x=0,
        y=0,
        z=0,
    )


def add_perimeter_windows(shell: Box, include_entry: bool = False) -> None:
    """Add a regular apartment-window rhythm to the exterior shell."""
    if include_entry:
        # Ground floor south elevation with centered main entry and apartment windows.
        south = shell.south
        for x in [2, 7, 17, 22]:
            south.opening(x=x, y=2, width=4, height=3)
            south.insert(PartType.WINDOW_1X4X3, x=x, y=2, color=WINDOW_COLOR)
        south.opening(x=12, y=0, width=4, height=6)
        south.insert(PartType.DOOR_1X4X6, x=12, y=0, color=DOOR_FRAME_COLOR)
    else:
        shell.south.window_row(
            y=2,
            width=4,
            height=3,
            count=4,
            part_type=PartType.WINDOW_1X4X3,
            spacing=2,
            color=WINDOW_COLOR,
        )

    shell.north.window_row(
        y=2,
        width=4,
        height=3,
        count=4,
        part_type=PartType.WINDOW_1X4X3,
        spacing=2,
        color=WINDOW_COLOR,
    )

    for wall in [shell.east, shell.west]:
        wall.window_row(
            y=2,
            width=2,
            height=3,
            count=3,
            part_type=PartType.WINDOW_1X2X3,
            spacing="even",
            color=WINDOW_COLOR,
        )

    # Light trim band at the top of the floor.
    for wall in shell.walls():
        wall.ledge(
            y=FLOOR_HEIGHT - 1,
            overhang=1,
            color=ACCENT_COLOR,
            part_type=PartType.PLATE_2X4,
        )


def make_apartments_partitions() -> Group:
    """Create two apartments, each split into two rooms."""
    partitions = Group("apartments_partitions")

    # Central party wall separating the two apartments.
    party = WallLayout(
        height=FLOOR_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="party_wall",
        initial_direction="north",
    )
    party.build_wall("party_wall", INNER_DEPTH)
    partitions.add(party, x=PARTY_WALL_X, y=1, z=INNER_Z)

    # West apartment room divider (living room / bedroom).
    west_divider = WallLayout(
        height=FLOOR_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="west_divider",
        initial_direction="east",
    )
    west_divider.build_wall("room_split", APARTMENT_WIDTH)
    west_divider["room_split"].opening(x=8, y=0, width=2, height=6)
    partitions.add(west_divider, x=INNER_X, y=1, z=ROOM_DIVIDER_Z)

    # East apartment room divider.
    east_divider = WallLayout(
        height=FLOOR_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="east_divider",
        initial_direction="east",
    )
    east_divider.build_wall("room_split", APARTMENT_WIDTH)
    east_divider["room_split"].opening(x=1, y=0, width=2, height=6)
    partitions.add(east_divider, x=15, y=1, z=ROOM_DIVIDER_Z)

    return partitions


def add_entry_details(ground_floor: Group) -> None:
    """Add visible front doors, steps, and a small canopy to the main entry."""

    # Small canopy above the entrance.
    ground_floor.add(
        FloorSlab(
            width=6,
            depth=3,
            color=ACCENT_COLOR,
            fill_part=PartType.PLATE_2X4,
            name="entry_canopy",
        ),
        x=11,
        y=1 + 6 * 3,
        z=-2,
    )

    # Front stoop / sidewalk.
    ground_floor.add(
        FloorSlab(
            width=12,
            depth=4,
            color=SITE_COLOR,
            fill_part=PartType.PLATE_2X4,
            name="entry_stoop",
        ),
        x=8,
        y=0,
        z=-4,
    )


def add_balconies(residential_floor: Group) -> None:
    """Add two shallow balconies on the south elevation for upper floors."""
    balcony_y = 1
    balcony_z = -3
    for idx, x in enumerate([1, 19], start=1):
        residential_floor.add(
            FloorSlab(
                width=8,
                depth=3,
                color=ACCENT_COLOR,
                fill_part=PartType.PLATE_2X4,
                name=f"balcony_{idx}",
            ),
            x=x,
            y=balcony_y,
            z=balcony_z,
        )
        # Slender support posts so the slabs read as attached balconies.
        residential_floor.add(
            Column(
                height=FLOOR_HEIGHT - 1,
                color=TRIM_COLOR,
                part_type=PartType.BRICK_1X1,
                name=f"balcony_support_left_{idx}",
            ),
            x=x,
            y=0,
            z=balcony_z + 2,
        )
        residential_floor.add(
            Column(
                height=FLOOR_HEIGHT - 1,
                color=TRIM_COLOR,
                part_type=PartType.BRICK_1X1,
                name=f"balcony_support_right_{idx}",
            ),
            x=x + 7,
            y=0,
            z=balcony_z + 2,
        )


        front_rail = WallLayout(
            height=2,
            color=RAILING_COLOR,
            fill_part=PartType.BRICK_1X4,
            name=f"balcony_front_rail_{idx}",
            initial_direction="east",
        )
        front_rail.build_wall("front", 8)
        residential_floor.add(front_rail, x=x, y=1 + 1, z=balcony_z)


def make_ground_floor() -> Group:
    ground_floor = Group("ground_floor")
    add_floor_plate(ground_floor, "ground_floor_plate", SITE_COLOR)

    ground_shell = Box(
        width=BUILDING_WIDTH,
        depth=BUILDING_DEPTH,
        height=FLOOR_HEIGHT,
        color=BASE_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="ground_shell",
    )
    add_perimeter_windows(ground_shell, include_entry=True)
    ground_floor.add(ground_shell, x=0, y=1, z=0)

    ground_floor.add(make_apartments_partitions(), x=0, y=0, z=0)
    add_entry_details(ground_floor)
    return ground_floor


def make_residential_floor() -> Group:
    residential_floor = Group("residential_floor")
    add_floor_plate(residential_floor, "residential_floor_plate", TRIM_COLOR)

    shell = Box(
        width=BUILDING_WIDTH,
        depth=BUILDING_DEPTH,
        height=FLOOR_HEIGHT,
        color=WALL_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="residential_shell",
    )
    add_perimeter_windows(shell, include_entry=False)
    residential_floor.add(shell, x=0, y=1, z=0)

    residential_floor.add(make_apartments_partitions(), x=0, y=0, z=0)
    add_balconies(residential_floor)
    return residential_floor


def make_roof() -> Group:
    roof = Group("roof")
    add_floor_plate(roof, "roof_plate", ROOF_COLOR)

    parapet = Box(
        width=BUILDING_WIDTH,
        depth=BUILDING_DEPTH,
        height=PARAPET_HEIGHT,
        color=ROOF_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="roof_parapet",
    )
    for wall in parapet.walls():
        wall.ledge(y=PARAPET_HEIGHT - 1, overhang=1, color=TRIM_COLOR, part_type=PartType.PLATE_2X4)
    roof.add(parapet, x=0, y=1, z=0)

    # Small rooftop utility block.
    roof.add(
        Box(
            width=8,
            depth=6,
            height=4,
            color=STAIR_TOWER_COLOR,
            fill_part=PartType.BRICK_2X4,
            name="roof_bulkhead",
        ),
        x=10,
        y=1,
        z=7,
    )

    roof.add(
        Column(
            height=6,
            color=HVAC_COLOR,
            part_type=PartType.BRICK_1X1,
            name="roof_vent",
        ),
        x=22,
        y=1,
        z=14,
    )
    return roof


def make_building_site() -> Group:
    building_site = Group("building site")
    building_site.add(
        FloorSlab(
            width=BUILDING_WIDTH + 8,
            depth=BUILDING_DEPTH + 8,
            color=SITE_COLOR,
            fill_part=PartType.PLATE_2X4,
            name="site_pad",
        ),
        x=-4,
        y=0,
        z=-4,
    )
    return building_site


def make_scene(name: str) -> Scene:
    scene = Scene(name)
    scene.add(make_building_site())
    ground_floor = make_ground_floor()
    upper_stack = make_residential_floor().stack(FLOOR_COUNT - 1)
    building = place(upper_stack, on=ground_floor, align="origin")
    place(make_roof(), on=building, align="origin")

    scene.add(building)
    return scene

scene: Scene

if __name__ == "__main__":
    scene = make_scene("4-floor apartment building")
    # output model: same name as the script but with .mpd extension, in the current directory.
    out_path = __file__.replace(".py", ".mpd")
    scene.export(out_path)
    print(f"Exported to: {out_path}")
    print(scene.stats())
