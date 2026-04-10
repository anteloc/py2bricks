"""
Build plan — 3-story apartment building with inner walls

1) Site and footprint
   - Create a simple rectangular site pad slightly larger than the building.
   - Center the building on the pad so there is a narrow sidewalk band around it.

2) Story module
   - Build one rectangular apartment-story shell with a floor slab and a 4-wall exterior box.
   - Ground story: use two apartment entry doors on the south elevation plus regular windows.
   - Upper stories: use only regular apartment windows on all elevations.
   - Add a trim ledge at the top of every exterior wall.

3) Apartment partitions on every story
   - Split the interior into two side-by-side apartments with one central party wall.
   - In each apartment add one transverse room-divider wall to split living and sleeping zones.
   - Add one short north-south bathroom wall inside each apartment.
   - Cut doorway openings in each inner wall so the rooms connect.
   - Place all inner walls directly on the story floor slab, inside the exterior shell.

4) Vertical composition
   - Build one ground story and one upper-story template.
   - Stack the upper-story template twice to make stories two and three.
   - Place the stacked upper stories directly on top of the ground story, origin-aligned.

5) Roof and final assembly
   - Place a dark roof deck slab on top of the full three-story stack.
   - Add a low parapet box on the roof perimeter and a small centered roof bulkhead.
   - Add a front stoop slab on the site aligned with the two ground-floor doors.
   - Add the whole assembled composition to the scene and export it as an MPD model.
"""

from __future__ import annotations

from py2bricks import (
    Scene,
    Group,
    Box,
    FloorSlab,
    WallLayout,
    PartType,
    Color,
    place,
)


# Overall dimensions
BUILDING_WIDTH = 28
BUILDING_DEPTH = 20
STORY_HEIGHT = 8          # bricks
STORY_COUNT = 3
PARAPET_HEIGHT = 2        # bricks

SITE_WIDTH = 36
SITE_DEPTH = 28
STOOP_WIDTH = 18
STOOP_DEPTH = 4

# Interior clear area inside the 2-stud-thick shell
INNER_X = 2
INNER_Z = 2
INNER_WIDTH = BUILDING_WIDTH - 4   # 24
INNER_DEPTH = BUILDING_DEPTH - 4   # 16
PARTY_WALL_X = 13                  # 11 + 2 + 11
ROOM_DIVIDER_Z = 9                 # 7 + 2 + 7
APARTMENT_WIDTH = 11
PRIVATE_ZONE_DEPTH = 7

# Colors
SITE_COLOR = Color.LIGHT_BLUISH_GREY
EXTERIOR_COLOR = Color.TAN
TRIM_COLOR = Color.WHITE
ROOF_COLOR = Color.DARK_BLUISH_GREY
WINDOW_COLOR = Color.TRANS_LIGHT_BLUE
DOOR_COLOR = Color.DARK_RED
INTERIOR_WALL_COLOR = Color.WHITE
BULKHEAD_COLOR = Color.LIGHT_GREY



def cut_and_insert(wall, *, x: int, y: int, width: int, height: int, part: PartType, color: int) -> None:
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part, x=x, y=y, color=color)



def add_exterior_openings(shell: Box, include_entry: bool) -> None:
    """Dress the shell with windows, and ground-floor apartment doors if requested."""
    if include_entry:
        cut_and_insert(shell.south, x=3, y=0, width=4, height=6, part=PartType.DOOR_1X4X6, color=DOOR_COLOR)
        cut_and_insert(shell.south, x=9, y=2, width=4, height=3, part=PartType.WINDOW_1X4X3, color=WINDOW_COLOR)
        cut_and_insert(shell.south, x=15, y=2, width=4, height=3, part=PartType.WINDOW_1X4X3, color=WINDOW_COLOR)
        cut_and_insert(shell.south, x=21, y=0, width=4, height=6, part=PartType.DOOR_1X4X6, color=DOOR_COLOR)
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

    for wall in shell.walls():
        wall.ledge(
            y=STORY_HEIGHT - 1,
            overhang=1,
            color=TRIM_COLOR,
            part_type=PartType.PLATE_2X4,
        )



def make_apartment_partitions() -> Group:
    """Two apartments per floor with simple room and bathroom walls."""
    partitions = Group("apartment_partitions")

    party = WallLayout(
        height=STORY_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="party_wall",
        initial_direction="north",
    )
    party.build_wall("wall", INNER_DEPTH)
    partitions.add(party, x=PARTY_WALL_X, y=1, z=INNER_Z)

    west_divider = WallLayout(
        height=STORY_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_1X4,
        name="west_room_divider",
        initial_direction="east",
    )
    west_divider.build_wall("wall", APARTMENT_WIDTH)
    west_divider["wall"].opening(x=8, y=0, width=2, height=6)
    partitions.add(west_divider, x=INNER_X, y=1, z=ROOM_DIVIDER_Z)

    east_divider = WallLayout(
        height=STORY_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_1X4,
        name="east_room_divider",
        initial_direction="east",
    )
    east_divider.build_wall("wall", APARTMENT_WIDTH)
    east_divider["wall"].opening(x=1, y=0, width=2, height=6)
    partitions.add(east_divider, x=15, y=1, z=ROOM_DIVIDER_Z)

    west_bath = WallLayout(
        height=STORY_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_1X4,
        name="west_bath_wall",
        initial_direction="north",
    )
    west_bath.build_wall("wall", PRIVATE_ZONE_DEPTH)
    west_bath["wall"].opening(x=1, y=0, width=2, height=6)
    partitions.add(west_bath, x=7, y=1, z=ROOM_DIVIDER_Z)

    east_bath = WallLayout(
        height=STORY_HEIGHT,
        color=INTERIOR_WALL_COLOR,
        fill_part=PartType.BRICK_1X4,
        name="east_bath_wall",
        initial_direction="north",
    )
    east_bath.build_wall("wall", PRIVATE_ZONE_DEPTH)
    east_bath["wall"].opening(x=4, y=0, width=2, height=6)
    partitions.add(east_bath, x=20, y=1, z=ROOM_DIVIDER_Z)

    return partitions



def make_story(name: str, include_entry: bool) -> Group:
    story = Group(name)
    story.add(
        FloorSlab(
            width=BUILDING_WIDTH,
            depth=BUILDING_DEPTH,
            color=SITE_COLOR,
            fill_part=PartType.PLATE_2X4,
            name=f"{name}_floor_slab",
        ),
        x=0,
        y=0,
        z=0,
    )

    shell = Box(
        BUILDING_WIDTH,
        BUILDING_DEPTH,
        STORY_HEIGHT,
        color=EXTERIOR_COLOR,
        fill_part=PartType.BRICK_2X4,
        name=f"{name}_shell",
    )
    add_exterior_openings(shell, include_entry=include_entry)
    story.add(shell, x=0, y=1, z=0)
    story.add(make_apartment_partitions(), x=0, y=0, z=0)
    return story



def make_roof() -> Group:
    roof = Group("roof")
    roof.add(
        FloorSlab(
            width=BUILDING_WIDTH,
            depth=BUILDING_DEPTH,
            color=ROOF_COLOR,
            fill_part=PartType.PLATE_2X4,
            name="roof_deck",
        ),
        x=0,
        y=0,
        z=0,
    )

    parapet = Box(
        BUILDING_WIDTH,
        BUILDING_DEPTH,
        PARAPET_HEIGHT,
        color=ROOF_COLOR,
        fill_part=PartType.BRICK_2X4,
        name="parapet",
    )
    for wall in parapet.walls():
        wall.ledge(y=PARAPET_HEIGHT - 1, overhang=1, color=TRIM_COLOR, part_type=PartType.PLATE_2X4)
    roof.add(parapet, x=0, y=1, z=0)

    bulkhead = Box(8, 6, 6, color=BULKHEAD_COLOR, fill_part=PartType.BRICK_2X4, name="roof_bulkhead")
    bulkhead.south.opening(x=2, y=0, width=4, height=6)
    bulkhead.south.insert(PartType.DOOR_1X4X6, x=2, y=0, color=DOOR_COLOR)
    roof.add(bulkhead, x=10, y=1, z=7)
    return roof



def build_building() -> Group:
    ground_story = make_story("ground_story", include_entry=True)
    upper_template = make_story("upper_story", include_entry=False)
    upper_stories = upper_template.stack(times=STORY_COUNT - 1)

    building = place(upper_stories, on=ground_story, align="origin")
    # TODO uncomment this to add the roof, open for now to inspect apartments partitions
    # building = place(make_roof(), on=building, align="origin")
    return building



def main() -> None:
    scene = Scene("three_story_apartments")

    site = Group("site")
    site_pad = FloorSlab(
        width=SITE_WIDTH,
        depth=SITE_DEPTH,
        color=SITE_COLOR,
        fill_part=PartType.PLATE_2X4,
        name="site_pad",
    )
    site.add(site_pad, x=0, y=0, z=0)

    stoop = FloorSlab(
        width=STOOP_WIDTH,
        depth=STOOP_DEPTH,
        color=TRIM_COLOR,
        fill_part=PartType.PLATE_2X4,
        name="front_stoop",
    )
    site.add(stoop, x=(SITE_WIDTH - STOOP_WIDTH) // 2, y=0, z=0)

    building = build_building()
    site.add(building, x=(SITE_WIDTH - BUILDING_WIDTH) // 2, y=1, z=(SITE_DEPTH - BUILDING_DEPTH) // 2)

    scene.add(site, x=0, y=0, z=0)

    out_path = __file__.replace(".py", ".mpd")
    output = scene.export(out_path)
    print(scene.stats())
    print(output)


if __name__ == "__main__":
    main()
