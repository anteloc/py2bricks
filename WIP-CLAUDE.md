# py2bricks — Claude Working Guide

## What This Project Does

py2bricks is a Python DSL for generating LEGO LDraw models (.mpd files). An LLM writes a Python script using this library's primitives; the library handles all geometric correctness, brick tiling, and LDraw export. 
The primary workflow is: write script → run it → the user opens the .mpd in BrickLink Studio or LDraw viewer.

## Single Entry Point: `Scene`

**Always start with a `Scene`.** Never instantiate `Box`, `Wall`, `FloorSlab`, etc. directly — use the factory methods on `Scene` instead. They create elements and register them automatically.

```python
from py2bricks import Scene, PartType, Color, place, attach

scene = Scene("my_building")
box = scene.box(width=24, depth=16, height=10, color=Color.WHITE)
roof = scene.gable_roof(width=24, depth=16, ridge="east_west", color=Color.DARK_RED)
place(roof, on=box)
scene.export("my_building.mpd")
```

## Coordinate System — Read This First

| Axis | Direction | Unit | Notes |
|------|-----------|------|-------|
| X | East (+) / West (−) | studs | horizontal |
| Z | North (+) / South (−) | studs | horizontal |
| Y | Up (+) | plates | vertical; **LDraw inverts Y at export — never touch this** |

- **Studs** for all horizontal dimensions (width, depth, length, X, Z positions).
- **Plates** for all vertical dimensions (height, Y positions). 1 brick = 3 plates.
- **LDraw Y inversion happens only inside `BrickPlacement.to_ldraw_line()`.** Do not compensate for it anywhere else.
- All internal arithmetic uses positive-up Y. Do not write negative Y values anywhere in scene-building code.

### Key Constants

```python
LDU_PER_STUD  = 20   # 1 stud  = 20 LDraw Units horizontally
LDU_PER_PLATE =  8   # 1 plate =  8 LDraw Units vertically
PLATES_PER_BRICK = 3 # 1 brick =  3 plates
WALL_DEPTH_STUDS = 2 # every Wall is exactly 2 studs deep (1 brick)
```

## Universal `to_placements()` Contract

Every element implements:

```python
def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
```

- Returns placements in **element-local** coordinates (origin at element's own (0,0,0)).
- Parent `Group` applies offsets recursively when collecting for export.
- **Never call `to_placements()` directly** in scene-building code — `scene.export()` does it.
- `BrickPlacement` is a frozen dataclass: `(part, x, y, z, rotation, color, comment)`.

## Module Map

| Module | Owns |
|--------|------|
| `core.py` | `BuilderError`, `BrickPlacement` |
| `coords.py` | Unit constants, `to_ldraw_coords()`, `ROTATION_MATRICES`, `FACING_TO_ROTATION` |
| `parts.py` | `PartType` enum, `Part` dataclass, `PARTS` catalog, `FILL_BRICKS`, `Color` constants |
| `wall.py` | `Wall` class, `WALL_DEPTH_STUDS` |
| `structures.py` | `Box`, `WallLayout`, `FloorSlab`, `Column`, `Stairs`, `StaircaseShaft` |
| `roof.py` | `GableRoof` |
| `assembly.py` | `Group`, `place()`, `attach()`, `Element` type |
| `scene.py` | `Scene` (**only entry point** for model building) |

## Key Constraints and Invariants

### Walls

- **All walls are exactly `WALL_DEPTH_STUDS = 2` studs deep.** This cannot be changed.
- Wall bricks are oriented with their 2-stud depth going INTO the wall, width along the face.
- `wall.opening(x, y, width, height)` — x/width in **studs**, y/height in **brick rows**.
- `wall.insert(part_type, x, y)` — must be called AFTER `opening()` at the same position.
- `wall.window_row(y, width, height, count, part_type)` — cuts + inserts in one call.

### Box

- A `Box` creates 4 walls: `box.north`, `box.south`, `box.east`, `box.west`.
- Box `width` = east-west stud dimension; `depth` = north-south stud dimension.
- Corner overlaps are already handled — do not add extra studs to wall lengths.

### WallLayout (L-shapes, U-shapes, arbitrary outlines)

- Build walls along a turtle-like path: `turn(direction)` then `build_wall(name, length)`.
- `direction` options: `"north", "south", "east", "west"`
- Cannot turn back 180°; only 90° turns allowed.
- Access individual walls via `layout["wall_name"]` for modification.
- Useful for things like e.g. non-rectangular floor plans, inner walls, etc.

### FloorSlab

- Height is always **1 plate**. Use `place(slab, on=box)` to stack it.
- For multi-floor buildings, place slabs between `Box` instances.

### Stairs / StaircaseShaft

- `Stairs`: single flight, canonical orientation north-facing (+Z climb direction).
- `StaircaseShaft`: multi-floor with either `"switchback"` or `"straight"` style.
- `floor_height_bricks` must be divisible by `step_height` (switchback: by `2 × step_height`).

### GableRoof

- Uses stepped brick rows (not slope bricks) — creates a ziggurat/pyramid profile.
- `ridge="east_west"` — ridge runs along X, slopes face N/S.
- `ridge="north_south"` — ridge runs along Z, slopes face E/W.
- Roof `height_plates` property gives total height for stacking calculations.

## Spatial Composition

### `place(element, on=..., align=..., offset=(x, z))`

Positions `element` on top of `on`. Returns a `Group`.

```python
g = place(roof, on=building, align="center")
g = place(canopy, at_level=36, align="flush_north", offset=(2, 0))
```

`align` options: `"center"`, `"flush_north"`, `"flush_south"`, `"flush_east"`, `"flush_west"`, `"origin"`

### `attach(element, to=..., face=..., align=..., offset=(along_face, vertical))`

Positions `element` beside `to` at a face. Returns a `Group`.

```python
g = attach(porch, to=building, face="south", align="center")
```

`face` options: `"north"`, `"south"`, `"east"`, `"west"`

### `Group`

```python
g = Group("floor_1")
g.add(box, x=0, y=0, z=0)
g.add(slab, x=0, y=box.height_plates, z=0)
stacked = g.stack(times=3)  # repeat vertically 3×
```

When `place()` or `attach()` receives a `Group` as its target, it adds the element into that group directly (no new group created).


## Planning Before Building

Create a build plan for the building to be created, as a professional LEGO builder would do:

- Structure the build plan according to he elements to be built, like e.g. "ground floor" or "entrance".
- Split the building plan into steps.
- Make explicit the connections between elements: how they are attached to each other, placed on top of another, etc.
- Build plan should be just enough to create the building.
- **Don't** overthink the design: **KISS** is better that overengineering!

## Greedy Tiling and Running Bond

Walls, floors, and roofs tile with a greedy algorithm:

1. Try widest brick first (`BRICK_2X4`), then narrower, down to `BRICK_1X1`.
2. Odd rows are offset by half the primary brick width (running bond).
3. `FILL_BRICKS` list defines the greedy order — do not modify it.

## Error Handling

All errors raise `BuilderError` with an actionable message. When you see one, read it — it tells you exactly what was wrong and what to fix.

## Running Scripts

```bash
# Install once (then scripts can just import py2bricks):
pip install -e /path/to/py2bricks

# Or use the helper script (no install needed):
scripts/run-gen.sh results/my_script.py
```

## Known TODOs / Caveats

- **Rotation matrices 90° / 270° in `coords.py`**: The TODO comment in `ROTATION_MATRICES` explains that the 90° and 270° values need validation against actual LDraw convention (left-handed coordinate system). East/west walls may have off-by-one stud shifts. Do not silently "fix" these without running a concrete test case first.
- `find_part()` ignores `description` and `color` arguments for now (reserved for future RAG lookup).
- `scene.stats()` width/depth are approximate (±4 studs).

## Quick Reference

For the compact API cheat-sheet, or run: 

```
python -c "from py2bricks import Scene; s=Scene('sc'); s.help()"  
```
