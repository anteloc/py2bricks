"""
Build plan — single flat apartment module, open-top

1) Base and outer shell
   - Create one rectangular floor slab for the whole flat.
   - Build a single-storey perimeter shell with no roof so the layout reads as a cutaway module.
   - Add the main entrance door on the north side plus a few broad windows on the outer walls.

2) Interior zoning by floor finish
   - Overlay light wood flooring across the main living / bedroom spaces.
   - Overlay light grey tiled slabs in the kitchen strip and bathroom so the plan matches the attached image.

3) Inner wall layout
   - Build only the partitions visible in the plan: stair core, bathroom enclosure,
     bedroom enclosure, and a short hall wall near the bedroom / bathroom junction.
   - Keep the kitchen open to the living room, just as in the image.
   - Cut simple open doorways in the bathroom, bedroom, and stair core partitions.

4) Simple interior cues
   - Add a small stepped stair run inside the stair core.
   - Add a compact kitchen counter line and a simple bathroom tub block so the flat reads clearly from above.

5) Assembly / connections
   - The floor slab is the base layer.
   - The perimeter shell and all inner walls sit directly on top of the floor slab.
   - Interior cues sit on the finished floor inside the shell.
   - No roof is added anywhere; the model stays open from above.
"""

from __future__ import annotations

from py2bricks import (
    Scene,
    Group,
    Box,
    WallLayout,
    FloorSlab,
    Column,
    PartType,
    Color,
)


# Overall module dimensions (studs)
MODULE_W = 40
MODULE_D = 30
WALL_H = 8  # bricks

# Colors
OUTER_WALL = Color.BLACK
INNER_WALL = Color.WHITE
WOOD = Color.TAN
TILE = Color.LIGHT_GREY
GLASS = Color.TRANS_LIGHT_BLUE
DOOR = Color.DARK_BLUISH_GREY
STAIR = Color.DARK_GREY
COUNTER = Color.DARK_TAN
TUB = Color.WHITE


def cut_insert(wall, *, x: int, y: int, width: int, height: int, part: PartType, color: int) -> None:
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part, x=x, y=y, color=color)



def make_shell() -> Box:
    shell = Box(MODULE_W, MODULE_D, WALL_H, color=OUTER_WALL, fill_part=PartType.BRICK_2X4, name="outer_shell")

    # North entrance aligned with the top-center entry space.
    cut_insert(shell.north, x=22, y=0, width=4, height=6, part=PartType.DOOR_1X4X6, color=DOOR)

    # Kitchen north window.
    cut_insert(shell.north, x=7, y=2, width=4, height=3, part=PartType.WINDOW_1X4X3, color=GLASS)

    # Living / bedroom south windows.
    cut_insert(shell.south, x=7, y=2, width=4, height=3, part=PartType.WINDOW_1X4X3, color=GLASS)
    cut_insert(shell.south, x=18, y=2, width=4, height=3, part=PartType.WINDOW_1X4X3, color=GLASS)
    cut_insert(shell.south, x=31, y=2, width=4, height=3, part=PartType.WINDOW_1X4X3, color=GLASS)

    # Side light windows.
    cut_insert(shell.west, x=9, y=2, width=2, height=3, part=PartType.WINDOW_1X2X3, color=GLASS)
    cut_insert(shell.east, x=8, y=2, width=2, height=3, part=PartType.WINDOW_1X2X3, color=GLASS)

    return shell



def make_partitions() -> WallLayout:
    walls = WallLayout(
        height=WALL_H,
        color=INNER_WALL,
        fill_part=PartType.BRICK_1X4,
        name="inner_layout",
    )

    # Stair core near the north-center of the flat.
    walls.place_wall("stair_south", length=4, cx=17, cz=20, travel_dir="east")
    walls.place_wall("stair_west", length=8, cx=17, cz=20, travel_dir="north")
    walls.place_wall("stair_east", length=8, cx=21, cz=28, travel_dir="south")

    # Bathroom enclosure at the north-east corner.
    walls.place_wall("bath_south", length=10, cx=28, cz=19, travel_dir="east")
    walls.place_wall("bath_west", length=9, cx=28, cz=19, travel_dir="north")

    # Bedroom enclosure in the south-east quadrant.
    walls.place_wall("bed_north", length=14, cx=38, cz=17, travel_dir="west")
    walls.place_wall("bed_west", length=15, cx=24, cz=2, travel_dir="north")

    # Short hall return wall between living room and bathroom / bedroom passage.
    walls.place_wall("hall_stub", length=3, cx=22, cz=17, travel_dir="north")

    # Openings / doorways.
    walls["stair_south"].opening(x=1, y=0, width=2, height=6)
    walls["bath_south"].opening(x=1, y=0, width=2, height=6)
    walls["bed_north"].opening(x=1, y=0, width=2, height=6)

    return walls



def add_floor_finishes(module: Group) -> None:
    # Whole flat base finish.
    module.add(
        FloorSlab(MODULE_W, MODULE_D, color=WOOD, fill_part=PartType.PLATE_2X4, name="main_floor"),
        x=0,
        y=0,
        z=0,
    )

    # Kitchen tile strip.
    module.add(
        FloorSlab(17, 6, color=TILE, fill_part=PartType.PLATE_2X4, name="kitchen_tile"),
        x=2,
        y=1,
        z=22,
    )

    # Bathroom tile block.
    module.add(
        FloorSlab(10, 9, color=TILE, fill_part=PartType.PLATE_2X4, name="bath_tile"),
        x=28,
        y=1,
        z=19,
    )



def add_simple_details(module: Group) -> None:
    # Simple stepped stair run.
    for i in range(5):
        module.add(
            FloorSlab(2, 5, color=STAIR, fill_part=PartType.PLATE_1X4, name=f"stair_step_{i+1}"),
            x=18,
            y=1 + i,
            z=21 + i,
        )

    # Kitchen counters along the north wall.
    module.add(
        FloorSlab(13, 2, color=COUNTER, fill_part=PartType.PLATE_2X4, name="kitchen_counter_run"),
        x=3,
        y=2,
        z=26,
    )
    module.add(
        FloorSlab(4, 2, color=COUNTER, fill_part=PartType.PLATE_2X4, name="kitchen_side_counter"),
        x=16,
        y=2,
        z=26,
    )

    # Compact bathroom tub block.
    module.add(
        FloorSlab(6, 2, color=TUB, fill_part=PartType.PLATE_2X4, name="bath_tub"),
        x=31,
        y=2,
        z=25,
    )

    # Two slim posts to hint at the bedroom doorway jambs.
    module.add(Column(height=6, color=INNER_WALL, part_type=PartType.BRICK_1X1, name="bed_jamb_left"), x=25, y=1, z=16)
    module.add(Column(height=6, color=INNER_WALL, part_type=PartType.BRICK_1X1, name="bed_jamb_right"), x=27, y=1, z=16)



def build_module() -> Group:
    module = Group("flat_module")
    add_floor_finishes(module)
    module.add(make_shell(), x=0, y=1, z=0)
    module.add(make_partitions(), x=0, y=1, z=0)
    add_simple_details(module)
    return module



def main() -> None:
    scene = Scene("flat_module_floorplan")
    scene.add(build_module(), x=0, y=0, z=0)
    out_path = __file__.replace(".py", ".mpd")
    scene.export(out_path)
    print(scene.stats())


if __name__ == "__main__":
    main()
