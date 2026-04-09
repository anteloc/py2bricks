# py2bricks Quick Reference

## Setup

```bash
# Install once (then scripts can just import py2bricks):
pip install -e /path/to/py2bricks

# Run to produce the .mpd model
python generated_model_name.py # should output: generated_model_name.mpd
```

---

## General Structure

```python
from py2bricks import Scene, PartType, Color, place, attach
"""
Build plan docstring
...
"""
# ... utility functions ...
scene = Scene("model_name")
# ... build model ...
out_path = __file__.replace(".py", ".mpd")
scene.export(out_path)
print(scene.stats())
```

---

## Coordinate System

| Axis | Direction | Unit |
|------|-----------|------|
| X | East (+) / West (−) | studs |
| Z | North (+) / South (−) | studs |
| Y | Up (+) | plates |

- 1 brick = 3 plates. 1 stud = 20 LDU. 1 plate = 8 LDU.
- All walls are 2 studs deep (`WALL_DEPTH_STUDS = 2`).
- LDraw Y inversion is handled internally — never use negative Y.

---

## Scene & Elements

```python

# Create a scene.
Scene(name: str) -> Scene
scene.add(element, x=0, y=0, z=0)   # add pre-built element (e.g. Group, Box, etc.) at position

# Create a group, optionally with initial elements at origin.
Group(name: str, elements: list | None = None) -> Group

# Create a box with 4 walls
Box(
    width: int,              # east-west studs
    depth: int,              # north-south studs
    height: int,             # brick rows
    color: int = Color.WHITE,
    fill_part: PartType = PartType.BRICK_2X4,
    name: str = "",
) -> Box

# Create a wall. All cells start as solid (True).
Wall(
    length: int,             # studs along face
    height: int,             # brick rows
    facing: str,             # "north" | "south" | "east" | "west"
    color: int = Color.WHITE,
    fill_part: PartType = PartType.BRICK_2X4,
    name: str = "",
) -> Wall

# Create an arbitrary layout of N walls with named accessors.
WallLayout(
    height: int,
    color: int = Color.WHITE,
    fill_part: PartType = PartType.BRICK_2X4,
    name: str = "",
    initial_direction: str = "east",  # starting travel direction
) -> WallLayout

# Create a horizontal rectangular surface tiled with plates.
FloorSlab(
    width: int,              # east-west studs
    depth: int,              # north-south studs
    color: int = Color.LIGHT_GREY,
    fill_part: PartType = PartType.PLATE_2X4,
    name: str = "",
) -> FloorSlab

# Create a vertical stack of identical bricks.
Column(
    height: int,             # brick rows
    color: int = Color.WHITE,
    part_type: PartType = PartType.BRICK_1X1,
    name: str = "",
) -> Column

# Create a gable roof.
GableRoof(
    width: int,              # east-west studs
    depth: int,              # north-south studs
    ridge: str = "east_west",  # "east_west" | "north_south"
    color: int = Color.DARK_BLUISH_GREY,
    fill_part: PartType = PartType.BRICK_2X4,
    name: str = "",
) -> GableRoof

# Create a multi-floor staircase built from Stairs flights and FloorSlab landings.
StaircaseShaft(
    floors: int,
    floor_height_bricks: int,
    stair_width: int,        # studs
    tread_depth: int = 2,    # studs per step
    style: str = "switchback",  # "switchback" | "straight"
    first_facing: str = "north",
    color: int = Color.WHITE,
    name: str = "",
) -> StaircaseShaft


```

---

## Wall Methods (modify after creation)

```python
# Access walls on a Box:
box.north  box.south  box.east  box.west   # → Wall

# Cut a rectangular opening (x/width in studs, y/height in brick rows):
wall.opening(x, y, width, height)

# Insert a window or door into an existing opening:
wall.insert(part_type: PartType, x, y, color=None)

# Cut + insert a row of evenly spaced windows in one call:
wall.window_row(
    y,                         # brick row from base
    width,                     # each window width in studs
    height,                    # each window height in brick rows
    count,                     # number of windows
    part_type: PartType,
    spacing="even",            # "even" or int (explicit gap in studs)
    color=None,
)

# Add an overhanging ledge / cornice:
wall.ledge(y, overhang=1, color=None, part_type=PartType.PLATE_2X4)
```

---

## WallLayout (turtle-style path)

```python
layout = WallLayout(height=10, color=Color.WHITE, initial_direction="east")
layout.build_wall("south_wall", length=24)  # builds in current direction
layout.turn("north")                         # 90° turn only; no 180° turns
layout.build_wall("east_wall", length=16)
layout.turn("west")
layout.build_wall("north_wall", length=24)

# Access and modify individual walls:
layout["south_wall"].window_row(y=2, width=4, height=3, count=3,
                                 part_type=PartType.WINDOW_1X4X3)
```

---

## Spatial Composition

### place() — stack one element on top of another

```python
group = place(
    element,
    on=target,            # element to stack on top of
    at_level=None,        # OR absolute Y in plates (mutually exclusive with on=)
    align="center",       # see align options below
    offset=(x, z),        # additional studs offset after alignment
)
```

| `align` | Meaning |
|---------|---------|
| `"center"` | center element on target (both axes) |
| `"flush_north"` | center X, align north edges |
| `"flush_south"` | center X, align south edges |
| `"flush_east"` | align east edges, center Z |
| `"flush_west"` | align west edges, center Z |
| `"origin"` | no horizontal shift |

### attach() — place element beside a face

```python
group = attach(
    element,
    to=target,            # element to attach beside
    face="south",         # which face of target: "north"|"south"|"east"|"west"
    align="center",       # see align options below
    offset=(along_face, vertical),  # studs / plates
) -> Group
```

| `face` | `align` options |
|--------|----------------|
| `"north"` / `"south"` | `"center"`, `"flush_east"`, `"flush_west"`, `"origin"` |
| `"east"` / `"west"` | `"center"`, `"flush_north"`, `"flush_south"`, `"origin"` |

### Group — manual composition

```python
g = Group("floor_1")
g.add(element, x=0, y=0, z=0)   # x/z in studs, y in plates
stacked = g.stack(times=3)       # repeat vertically N times
```

---

## PartType Enum

PART_{DEPTH}x{WIDTH}X{HEIGHT}

### Bricks (height = always 3 plates)
```
BRICK_1X1  BRICK_1X2  BRICK_1X3  BRICK_1X4
BRICK_2X2  BRICK_2X3  BRICK_2X4
```

### Plates (height = always 1 plate)
```
PLATE_1X1  PLATE_1X2  PLATE_1X4
PLATE_2X2  PLATE_2X3  PLATE_2X4
```

### Windows & Doors
```
WINDOW_1X2X2
WINDOW_1X2X3
WINDOW_1X4X3
DOOR_1X4X6
```

### Slopes
```
SLOPE_2X2  SLOPE_2X4
```

---

## Color Constants

```python
Color.BLACK
Color.GREEN
Color.BROWN
Color.DARK_GREY
Color.BRIGHT_GREEN
Color.WHITE
Color.DARK_BLUE
Color.DARK_TAN
Color.REDDISH_BROWN
Color.DARK_BLUISH_GREY
Color.TRANS_CLEAR 
Color.BLUE
Color.RED
Color.LIGHT_GREY
Color.LIGHT_BLUE
Color.YELLOW
Color.TAN
Color.DARK_RED
Color.DARK_GREEN
Color.SAND_GREEN
Color.LIGHT_BLUISH_GREY
Color.TRANS_LIGHT_BLUE
```

---

