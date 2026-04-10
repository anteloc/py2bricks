"""
Build plan — single flat apartment module, open-top

1) Base and outer shell
   - Create one rectangular floor slab for the whole flat.
   - Build a single-storey perimeter shell with no roof so the layout reads as a cutaway module.
   - Add the main entrance door on the north side plus a few broad windows on the outer walls.

2) Interior zoning by floor finish
   - Overlay light wood flooring across the main living / bedroom spaces.

3) Inner wall layout
   - Build only the partitions visible in the plan: kitchen, bathroom enclosure,
     bedroom enclosure.
   - Cut simple open doorways in the kitchen, bathroom, and bedroom partitions.

4) Assembly / connections
   - The floor slab is the base layer.
   - The perimeter shell and all inner walls sit directly on top of the floor slab.
   - Interior cues sit on the finished floor inside the shell.
   - No roof is added anywhere; the model stays open from above.

Floorplan:

D = Door
W = Window


    ↑
    N
← W   E →
    S
    ↓

┌───────────────────────────  D ────────────────W──────────────────── ┐
│                  │                          │                       │
│      Kitchen     │                          │ Bathroom              │
│                  │                          │                       │
│                  │                          │                       │
│                  │                          │                       │
│─────────────── D ┘                          └ D ────────────────────│
│                                                                     │
│                                                                     │
│                                      ┌─────────────────────────── D │
│                                      │                              │
│                                      │                              │
│                                      │         Bedroom              │
W                                      │                              │
│                                      │                              │
│                                      │                              │
│                                      │                              │
│                                      │                              │
│                                      │                              │
│                                      │                              │
└──────────W──────────────W───────────────────────────────W───────────│
"""

from __future__ import annotations

from py2bricks import (
    Scene,
    Group,
    Box,
    WallLayout,
    FloorSlab,
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


def make_kitchen_walls(module: Group) -> None:
    # U-shape traced as a single chain: west → bridge → east.
    # The bridge sits at z=28, flush with the inner face of the outer north wall.
    walls = WallLayout(
        height=WALL_H,
        color=INNER_WALL,
        fill_part=PartType.BRICK_1X4,
        name="kitchen_south",
        initial_direction="south",
    )
    walls.build_wall("west", 12)
    walls.turn("west")
    walls.build_wall("south", 10)
    walls["south"].opening(x=1, y=0, width=2, height=6)
    module.add(walls, x=12, y=1, z=MODULE_W - 12)

def make_bathroom_walls(module: Group) -> None:
    # L-corner at (28,19) is start-start — two walls cannot be chained.
    west = WallLayout(
        height=WALL_H,
        color=INNER_WALL,
        fill_part=PartType.BRICK_1X4,
        name="bath_west",
        initial_direction="north",
    )
    west.build_wall("wall", 9)
    module.add(west, x=28, y=1, z=19)

    south = WallLayout(
        height=WALL_H,
        color=INNER_WALL,
        fill_part=PartType.BRICK_1X4,
        name="bath_south",
        initial_direction="east",
    )
    south.build_wall("wall", 10)
    south["wall"].opening(x=1, y=0, width=2, height=6)
    module.add(south, x=28, y=1, z=19)


def make_bedroom_walls(module: Group) -> None:
    # L-corner at (24,17) is end-end — two walls cannot be chained.
    north = WallLayout(
        height=WALL_H,
        color=INNER_WALL,
        fill_part=PartType.BRICK_1X4,
        name="bed_north",
        initial_direction="west",
    )
    north.build_wall("wall", 14)
    north["wall"].opening(x=1, y=0, width=2, height=6)
    module.add(north, x=38, y=1, z=17)

    west = WallLayout(
        height=WALL_H,
        color=INNER_WALL,
        fill_part=PartType.BRICK_1X4,
        name="bed_west",
        initial_direction="north",
    )
    west.build_wall("wall", 15)
    module.add(west, x=24, y=1, z=2)


def add_floor_finishes(module: Group) -> None:
    # Whole flat base finish.
    module.add(
        FloorSlab(MODULE_W, MODULE_D, color=WOOD, fill_part=PartType.PLATE_2X4, name="main_floor"),
        x=0,
        y=0,
        z=0,
    )


def build_module() -> Group:
    module = Group("flat_module")
    add_floor_finishes(module)
    module.add(make_shell(), x=0, y=1, z=0)
    make_kitchen_walls(module)
    make_bathroom_walls(module)
    make_bedroom_walls(module)
    return module



def main() -> None:
    scene = Scene("flat_module_floorplan")
    scene.add(build_module(), x=0, y=0, z=0)
    out_path = __file__.replace(".py", ".mpd")
    scene.export(out_path)
    print(scene.stats())


if __name__ == "__main__":
    main()
