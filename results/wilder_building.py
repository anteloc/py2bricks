from __future__ import annotations

"""
Build plan — historic red-brick corner block inspired by the reference photo

1) Site / corner lot
   - Create a dark road plate for the full scene.
   - Add raised light-grey sidewalks along the south and east edges so the model reads as a city corner.
   - Place the building near that corner with just enough pavement around it.

2) Storefront / stone base
   - Build one tan masonry base for the ground floor.
   - Cut tall storefront openings on all sides, with a side entrance on the east face.
   - Cap the base with a light stone band.

3) Lower brick office tier
   - Stack one dark-red office floor above the stone base.
   - Use narrow repeated windows and a strong brick ledge to separate it from the taller upper floors.

4) Main arched-window tier
   - Build a repeated floor module with tall stacked windows to suggest the large round-arched bays in the photo.
   - Stack that module twice.
   - Add extra horizontal ledges so this band reads as the most ornate part of the facade.

5) Upper tiers and crown
   - Add two denser small-window tiers near the top.
   - Finish with a compact crown floor, a roof slab, and simple rooftop edging.

6) Corner piers
   - Add slim exterior corner columns above the stone base so the building keeps the rounded corner-pier feel from the photo.

Connection logic
   - roads are the global base.
   - sidewalks sit directly on the roads.
   - the stone storefront sits on the sidewalks / site corner.
   - all brick tiers stack directly on the storefront in a straight vertical pile.
   - corner piers are added beside the stacked mass, starting above the stone base.
"""

from py2bricks import Scene, Group, Box, FloorSlab, Column, PartType, Color


# --- Overall proportions ----------------------------------------------------
SITE_W = 48
SITE_D = 48

BUILDING_W = 28
BUILDING_D = 32

STORE_H = 6
LOWER_H = 6
MID_H = 8
MID_FLOORS = 2
UPPER_H = 6
UPPER_FLOORS = 2
CROWN_H = 6

BUILDING_X = 15
BUILDING_Z = 5

# --- Palette ----------------------------------------------------------------
ROAD = Color.DARK_BLUISH_GREY
SIDEWALK = Color.LIGHT_BLUISH_GREY
STONE = Color.TAN
STONE_DARK = Color.DARK_TAN
BRICK = Color.DARK_RED
BRICK_TRIM = Color.REDDISH_BROWN
WINDOW = Color.TRANS_CLEAR
ROOF = Color.LIGHT_BLUISH_GREY
BLACK = Color.BLACK


# --- Window rhythms ---------------------------------------------------------
LONG_NARROW = (3, 7, 11, 15, 19, 23)
DEEP_NARROW = (3, 7, 11, 15, 19, 23, 27)

LONG_BIG = (2, 8, 14, 20)
DEEP_BIG = (2, 8, 14, 20, 26)

LONG_DENSE = (2, 6, 10, 14, 18, 22, 26)
DEEP_DENSE = (2, 6, 10, 14, 18, 22, 26, 30)


def add_window(wall, x: int, y: int, width: int, height: int, part_type: PartType, color: int = WINDOW):
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part_type, x=x, y=y, color=color)


def add_window_series(wall, xs: tuple[int, ...], y: int, width: int, height: int, part_type: PartType):
    for x in xs:
        add_window(wall, x=x, y=y, width=width, height=height, part_type=part_type)


def make_storefront() -> Group:
    tier = Group("storefront")
    shell = Box(BUILDING_W, BUILDING_D, STORE_H, color=STONE, name="storefront_shell")

    # South: open shopfront rhythm.
    for x in (2, 8, 14, 20):
        add_window(shell.south, x=x, y=0, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
        add_window(shell.south, x=x, y=3, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    # East: one entrance plus three glazing bays.
    shell.east.opening(x=4, y=0, width=4, height=6)
    shell.east.insert(PartType.DOOR_1X4X6, x=4, y=0, color=BLACK)
    for x in (10, 16, 22):
        add_window(shell.east, x=x, y=0, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
        add_window(shell.east, x=x, y=3, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    # Simpler rear/service elevations.
    for wall, xs in ((shell.north, LONG_BIG), (shell.west, DEEP_BIG)):
        for x in xs:
            add_window(wall, x=x, y=0, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
            add_window(wall, x=x, y=3, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    for wall in shell.walls():
        wall.ledge(y=1, overhang=1, color=STONE_DARK, part_type=PartType.PLATE_2X4)
        wall.ledge(y=STORE_H - 1, overhang=1, color=SIDEWALK, part_type=PartType.PLATE_2X4)

    tier.add(shell, x=0, y=0, z=0)
    tier.add(
        FloorSlab(BUILDING_W, BUILDING_D, color=SIDEWALK, fill_part=PartType.PLATE_2X4, name="storefront_cap"),
        x=0,
        y=shell.height_plates,
        z=0,
    )
    return tier


def make_lower_tier() -> Group:
    tier = Group("lower_office_tier")
    shell = Box(BUILDING_W, BUILDING_D, LOWER_H, color=BRICK, name="lower_shell")

    add_window_series(shell.south, LONG_NARROW, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, LONG_NARROW, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.east, DEEP_NARROW, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.west, DEEP_NARROW, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=LOWER_H - 1, overhang=1, color=BRICK_TRIM, part_type=PartType.PLATE_2X4)

    tier.add(shell, x=0, y=0, z=0)
    tier.add(
        FloorSlab(BUILDING_W, BUILDING_D, color=BRICK_TRIM, fill_part=PartType.PLATE_2X4, name="lower_cap"),
        x=0,
        y=shell.height_plates,
        z=0,
    )
    return tier


def make_mid_tier() -> Group:
    tier = Group("mid_tier")
    shell = Box(BUILDING_W, BUILDING_D, MID_H, color=BRICK, name="mid_shell")

    # Lower + upper stacked windows suggest the tall arched openings.
    for wall, xs in ((shell.south, LONG_BIG), (shell.north, LONG_BIG), (shell.east, DEEP_BIG), (shell.west, DEEP_BIG)):
        for x in xs:
            add_window(wall, x=x, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
            add_window(wall, x=x, y=4, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
        wall.ledge(y=3, overhang=1, color=BRICK_TRIM, part_type=PartType.PLATE_2X4)
        wall.ledge(y=MID_H - 1, overhang=1, color=BRICK_TRIM, part_type=PartType.PLATE_2X4)

    tier.add(shell, x=0, y=0, z=0)
    tier.add(
        FloorSlab(BUILDING_W, BUILDING_D, color=BRICK_TRIM, fill_part=PartType.PLATE_2X4, name="mid_cap"),
        x=0,
        y=shell.height_plates,
        z=0,
    )
    return tier


def make_upper_tier() -> Group:
    tier = Group("upper_tier")
    shell = Box(BUILDING_W, BUILDING_D, UPPER_H, color=BRICK, name="upper_shell")

    add_window_series(shell.south, LONG_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, LONG_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.east, DEEP_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.west, DEEP_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=UPPER_H - 1, overhang=1, color=BRICK_TRIM, part_type=PartType.PLATE_2X4)

    tier.add(shell, x=0, y=0, z=0)
    tier.add(
        FloorSlab(BUILDING_W, BUILDING_D, color=BRICK_TRIM, fill_part=PartType.PLATE_2X4, name="upper_cap"),
        x=0,
        y=shell.height_plates,
        z=0,
    )
    return tier


def make_crown() -> Group:
    crown = Group("crown")
    shell = Box(BUILDING_W, BUILDING_D, CROWN_H, color=BRICK, name="crown_shell")

    add_window_series(shell.south, LONG_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, LONG_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.east, DEEP_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.west, DEEP_DENSE, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=CROWN_H - 1, overhang=1, color=SIDEWALK, part_type=PartType.PLATE_2X4)

    crown.add(shell, x=0, y=0, z=0)
    crown.add(
        FloorSlab(BUILDING_W, BUILDING_D, color=ROOF, fill_part=PartType.PLATE_2X4, name="roof"),
        x=0,
        y=shell.height_plates,
        z=0,
    )

    # A simple parapet rhythm around the roof edge.
    crown.add(Box(4, 2, 1, color=BRICK_TRIM, name="roof_parapet_s"), x=12, y=shell.height_plates + 1, z=-1)
    crown.add(Box(4, 2, 1, color=BRICK_TRIM, name="roof_parapet_n"), x=12, y=shell.height_plates + 1, z=BUILDING_D - 1)
    crown.add(Box(2, 4, 1, color=BRICK_TRIM, name="roof_parapet_w"), x=-1, y=shell.height_plates + 1, z=14)
    crown.add(Box(2, 4, 1, color=BRICK_TRIM, name="roof_parapet_e"), x=BUILDING_W - 1, y=shell.height_plates + 1, z=14)
    return crown


def add_corner_piers(building: Group) -> None:
    # Start the rounded brick piers above the stone storefront.
    start_y = make_storefront().height_plates
    pier_height_bricks = LOWER_H + (MID_H * MID_FLOORS) + (UPPER_H * UPPER_FLOORS) + CROWN_H

    pier_positions = (
        (0, -1),
        (BUILDING_W - 1, -1),
        (0, BUILDING_D),
        (BUILDING_W - 1, BUILDING_D),
        (-1, 0),
        (-1, BUILDING_D - 1),
        (BUILDING_W, 0),
        (BUILDING_W, BUILDING_D - 1),
    )

    for idx, (x, z) in enumerate(pier_positions, start=1):
        building.add(
            Column(height=pier_height_bricks, color=BRICK_TRIM, part_type=PartType.BRICK_1X1, name=f"corner_pier_{idx}"),
            x=x,
            y=start_y,
            z=z,
        )


def main() -> None:
    scene = Scene("wilder_building")

    # Corner streets and sidewalks.
    scene.add(FloorSlab(SITE_W, SITE_D, color=ROAD, fill_part=PartType.PLATE_2X4, name="roads"), x=0, y=0, z=0)
    scene.add(FloorSlab(SITE_W, 5, color=SIDEWALK, fill_part=PartType.PLATE_2X4, name="south_sidewalk"), x=0, y=1, z=0)
    scene.add(FloorSlab(5, SITE_D, color=SIDEWALK, fill_part=PartType.PLATE_2X4, name="east_sidewalk"), x=SITE_W - 5, y=1, z=0)

    building = Group("historic_corner_block")
    current_y = 0

    storefront = make_storefront()
    building.add(storefront, x=0, y=current_y, z=0)
    current_y += storefront.height_plates

    lower = make_lower_tier()
    building.add(lower, x=0, y=current_y, z=0)
    current_y += lower.height_plates

    mid_stack = make_mid_tier().stack(times=MID_FLOORS)
    building.add(mid_stack, x=0, y=current_y, z=0)
    current_y += mid_stack.height_plates

    upper_stack = make_upper_tier().stack(times=UPPER_FLOORS)
    building.add(upper_stack, x=0, y=current_y, z=0)
    current_y += upper_stack.height_plates

    crown = make_crown()
    building.add(crown, x=0, y=current_y, z=0)

    add_corner_piers(building)

    # Place the building so its south and east faces front the sidewalks.
    scene.add(building, x=BUILDING_X, y=2, z=BUILDING_Z)

    out_path = __file__.replace(".py", ".mpd")
    output = scene.export(out_path)
    print(scene.stats())
    print(output)


if __name__ == "__main__":
    main()
