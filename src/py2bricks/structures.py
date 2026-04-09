"""
Structural elements: Box, FloorSlab, and Column.

Box: 4-wall rectangular enclosure.
FloorSlab: horizontal plate surface.
Column: vertical stack of identical bricks.
"""

from __future__ import annotations

from typing import Literal, cast

from .coords import PLATES_PER_BRICK, FACING_TO_ROTATION
from .parts import PartType, Part, PARTS, FILL_BRICKS, find_part, Color
from .core import BuilderError, BrickPlacement
from .wall import Wall, WALL_DEPTH_STUDS

# Shorthand for the cardinal-direction Literal used in several classes.
_Facing = Literal["north", "south", "east", "west"]

# ---------------------------------------------------------------------------
# WallLayout Class
# ---------------------------------------------------------------------------
#
# A WallLayout is a convenience that creates a series of joined walls forming 
# an arbitrary shape composed by walls extending east, west, north or south, joined by corners.
# It handles wall positioning so the LLM never calculates wall coordinates.
#
# The WallLayout lives in its own local coordinate space:
#   - Origin (0, 0, 0) is at the starting point for the first wall.
#   - X axis represents east-west orientation, while Z axis represents north-south, and Y is up.
#
# TODO Wall layout (viewed from above)
#
#


class WallLayout:
    """An arbitrary layout of N walls with named accessors.

    The LLM creates a WallLayout to define a set of interconnected walls, joined by corners, then modifies
    individual walls via [wall_name] dict keys.

    The LLM acts in a similar way as if it was controlling a Logo turtle walking a continuous path and building walls along the way:
    it starts at the origin, facing an initial direction (e.g. north), builds a wall extending in that
    direction forward, turns to another direction, builds another wall in that direction, and so on.

    Attributes:
        name: Identifier for LDraw comments.
        height_bricks: Walls uniform height in brick rows.
        height_plates: Walls uniform height in plates.
        color: Default LDraw color for all walls.
        fill_part: Part catalog key for wall fill bricks.
    """

    # Wall facing is derived from travel direction to match Box coordinate conventions:
    #   travel east  → south-facing wall  (Box south-wall analog, runs E-W)
    #   travel west  → north-facing wall  (Box north-wall analog, runs E-W)
    #   travel north → west-facing wall   (Box west-wall analog,  runs N-S)
    #   travel south → east-facing wall   (Box east-wall analog,  runs N-S)
    _TRAVEL_TO_FACING: dict[str, str] = {
        "east": "south", "west": "north",
        "north": "west", "south": "east",
    }
    _OPPOSITES: dict[str, str] = {
        "north": "south", "south": "north",
        "east": "west",   "west": "east",
    }

    def __init__(
        self,
        height: int,
        color: int = Color.WHITE,
        fill_part: PartType = PartType.BRICK_2X4,
        name: str = "",
        initial_direction: Literal["north", "south", "east", "west"] = "north",
    ):
        self.name = name or "layout"
        self.height_bricks = height
        self.height_plates = height * PLATES_PER_BRICK
        self.color = color
        self.fill_part = fill_part

        self._facing: str = initial_direction
        self._position: tuple[int, int] = (0, 0)  # (x, z) outer-corner, layout-local

        # Ordered list of (wall, cx_start, cz_start, travel_direction).
        # cx/cz are the outer-corner coords recorded when build_wall() was called.
        self._wall_records: list[tuple[Wall, int, int, str]] = []
        self._wall_map: dict[str, Wall] = {}

    def turn(self, direction: Literal["north", "south", "east", "west"]):
        """Turn facing to a new direction for the next wall.
        Turning to the opposite direction is **not allowed** (would create overlapping walls)."""
        if direction == self._OPPOSITES[self._facing]:
            raise BuilderError(
                f"Cannot turn to opposite direction '{direction}' "
                f"(currently facing '{self._facing}'): would create overlapping walls."
            )
        self._facing = direction

    def build_wall(self, wall_name: str, length: int):
        """Build a wall with the given name, extending in the current facing direction,
        with a given length in studs."""
        if wall_name in self._wall_map:
            raise BuilderError(f"Duplicate wall name '{wall_name}' in layout '{self.name}'")
        if length < 1:
            raise BuilderError(f"Wall length must be >= 1, got {length}")

        wall = Wall(
            length=length,
            height=self.height_bricks,
            facing=self._TRAVEL_TO_FACING[self._facing],
            color=self.color,
            fill_part=self.fill_part,
            name=wall_name,
        )

        cx, cz = self._position
        self._wall_records.append((wall, cx, cz, self._facing))
        self._wall_map[wall_name] = wall

        # Advance the turtle to the next outer corner.
        advances: dict[str, tuple[int, int]] = {
            "east":  (cx + length, cz),
            "west":  (cx - length, cz),
            "north": (cx, cz + length),
            "south": (cx, cz - length),
        }
        self._position = advances[self._facing]

    def place_wall(
        self,
        wall_name: str,
        length: int,
        cx: int,
        cz: int,
        travel_dir: Literal["north", "south", "east", "west"],
    ):
        """Place a wall at an explicit corner position, bypassing the turtle.

        Used by structures (e.g. Box) whose geometry cannot be expressed as a
        single continuous turtle path — typically when required wall corners are
        not reachable in sequence without introducing extra walls.

        Args:
            wall_name: Unique name for the wall within this layout.
            length:    Wall length in studs.
            cx, cz:   Outer-corner position in layout-local coordinates.
            travel_dir: Direction the turtle would have been travelling to place
                        this wall; determines facing and coordinate transforms.
        """
        if wall_name in self._wall_map:
            raise BuilderError(f"Duplicate wall name '{wall_name}' in layout '{self.name}'")
        wall = Wall(
            length=length,
            height=self.height_bricks,
            facing=self._TRAVEL_TO_FACING[travel_dir],
            color=self.color,
            fill_part=self.fill_part,
            name=wall_name,
        )
        self._wall_records.append((wall, cx, cz, travel_dir))
        self._wall_map[wall_name] = wall

    def __getitem__(self, wall_name: str) -> Wall:
        """Access a wall by name for modification (add openings, inserts, ledges)."""
        if wall_name not in self._wall_map:
            raise KeyError(f"No wall named '{wall_name}' in layout '{self.name}'")
        return self._wall_map[wall_name]

    def walls(self) -> list[Wall]:
        """Return all walls in the layout as a list."""
        return [record[0] for record in self._wall_records]

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate BrickPlacements for all walls, positioned correctly.

        Transforms each wall's local-space placements into the WallLayout's
        local coordinate space. The WallLayout itself may later be transformed
        by a Group or place() call.

        Coordinate transforms mirror Box conventions exactly (see Box.to_placements):
          east travel  → south wall: x=cx+p.x,                   z=cz+p.z,                rot=180
          west travel  → north wall: x=cx-p.x-part.width,        z=cz-WALL_DEPTH+p.z,     rot=0
          north travel → west wall:  x=cx+p.z,                   z=cz+p.x,                rot=270
          south travel → east wall:  x=cx-WALL_DEPTH+p.z,        z=cz-p.x-part.width,     rot=90

        Returns:
            List of BrickPlacement in WallLayout-local coordinates.
        """
        prefix = f"{comment_prefix}{self.name} > "
        result = []

        for wall, cx, cz, travel_dir in self._wall_records:
            _facing = self._TRAVEL_TO_FACING[travel_dir]
            rotation = FACING_TO_ROTATION[_facing]

            for p in wall.to_placements(prefix):
                if travel_dir == "east":
                    x = cx + p.x
                    z = cz + p.z
                elif travel_dir == "west":
                    x = cx - p.x - p.part.width_studs
                    z = cz - WALL_DEPTH_STUDS + p.z
                elif travel_dir == "north":
                    x = cx + p.z
                    z = cz + p.x
                else:  # south
                    x = cx - WALL_DEPTH_STUDS + p.z
                    z = cz - p.x - p.part.width_studs

                result.append(BrickPlacement(
                    p.part, x, p.y, z, rotation, p.color, p.comment
                ))

        return result



# ---------------------------------------------------------------------------
# Box Class
# ---------------------------------------------------------------------------
#
# A Box is a convenience that creates 4 walls forming a rectangular enclosure.
# It handles wall positioning so the LLM never calculates wall coordinates.
#
# The Box lives in its own local coordinate space:
#   - Origin (0, 0, 0) is at the bottom-left-front corner.
#   - X axis runs east (width), Z axis runs north (depth), Y is up.
#   - The four walls are placed at the edges of the footprint.
#
# Wall layout (viewed from above):
#
#        north wall (length = width)
#      +--------------------------+
#      |                          |
#  west|                          |east
#  wall|   interior (hollow)      |wall
#  (len|                          |(len
#  =dep|                          |=dep
#  th) |                          |th)
#      +--------------------------+
#        south wall (length = width)
#
#   origin (0,0) is at south-west corner


class Box:
    """A rectangular enclosure of 4 walls with named accessors.

    The LLM creates a Box to define a floor's walls, then modifies
    individual walls via .north, .south, .east, .west accessors.

    Attributes:
        name: Identifier for LDraw comments.
        width: East-west dimension in studs.
        depth: North-south dimension in studs.
        height_bricks: Wall height in brick rows.
        color: Default LDraw color for all walls.
        north: The north-facing wall.
        south: The south-facing wall.
        east: The east-facing wall.
        west: The west-facing wall.
    """

    def __init__(
        self,
        width: int,
        depth: int,
        height: int,
        color: int = Color.WHITE,
        fill_part: PartType = PartType.BRICK_2X4,
        name: str = "",
    ):
        """Create a box with 4 walls.

        Args:
            width: East-west dimension in studs.
            depth: North-south dimension in studs.
            height: Wall height in brick rows.
            color: LDraw color code for all walls.
            fill_part: Part catalog key for fill bricks.
            name: Identifier for LDraw comments.
        """
        
        self.name = name or "box"
        self.width = width
        self.depth = depth
        self.color = color

        # layout direction north
        self.wall_layout = WallLayout(
            height=height,
            color=color,
            fill_part=fill_part,
            name=f"{name}_layout",
        )

        self.height_bricks = self.wall_layout.height_bricks
        self.height_plates = self.wall_layout.height_plates

        west_name  = f"{self.name}_west"
        north_name = f"{self.name}_north"
        east_name  = f"{self.name}_east"
        south_name = f"{self.name}_south"

        # Box corners cannot be reached in sequence by the turtle (required corners
        # are (0,0) and (width,depth) — diagonally opposite), so we place walls
        # at their exact corners directly instead of using turn()/build_wall().
        #
        # Corner/travel assignments (verified against WallLayout.to_placements transforms):
        #   south wall: corner (0,     0    ), travel east  → south-facing, runs along X
        #   west  wall: corner (0,     0    ), travel north → west-facing,  runs along Z
        #   north wall: corner (width, depth), travel west  → north-facing, runs along X
        #   east  wall: corner (width, depth), travel south → east-facing,  runs along Z
        self.wall_layout.place_wall(south_name, width, 0,     0,     "east")
        self.wall_layout.place_wall(west_name,  depth, 0,     0,     "north")
        self.wall_layout.place_wall(north_name, width, width, depth, "west")
        self.wall_layout.place_wall(east_name,  depth, width, depth, "south")

        self.north, self.south, self.east, self.west = \
            self.wall_layout[north_name], self.wall_layout[south_name], \
            self.wall_layout[east_name], self.wall_layout[west_name]

    def walls(self) -> list[Wall]:
        """Return all four walls as a list."""
        return [self.north, self.south, self.east, self.west]

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate BrickPlacements for all four walls, positioned correctly.

        Transforms each wall's local-space placements into the Box's
        local coordinate space. The Box itself may later be transformed
        by a Group or place() call.

        Wall positions in Box-local space:
          - South wall: at z=0, running along X from 0 to width
          - North wall: at z=depth, running along X from 0 to width
          - West wall:  at x=0, running along Z from 0 to depth
          - East wall:  at x=width, running along Z from 0 to depth

        Returns:
            List of BrickPlacement in Box-local coordinates.
        """

        return self.wall_layout.to_placements(comment_prefix)

# ---------------------------------------------------------------------------
# FloorSlab Class
# ---------------------------------------------------------------------------
#
# A FloorSlab is a horizontal rectangular surface made of plates.
# Used for: foundations, floor/ceiling dividers, balcony surfaces, flat roofs.
#
# It tiles the area with plates using a simple greedy algorithm.
# No running bond needed for plates (they're only 1 plate tall).


class FloorSlab:
    """A horizontal rectangular surface tiled with plates.

    Lives in its own local coordinate space:
      - X axis: width (studs), Z axis: depth (studs), Y = 0 (one plate tall).

    Attributes:
        name: Identifier for LDraw comments.
        width: East-west dimension in studs.
        depth: North-south dimension in studs.
        color: LDraw color code.
        fill_part: Part catalog key for fill plates.
        height_plates: Always 1 (one plate tall).
    """

    def __init__(
        self,
        width: int,
        depth: int,
        color: int = Color.LIGHT_GREY,
        fill_part: PartType = PartType.PLATE_2X4,
        name: str = "",
    ):
        """Create a floor slab.

        Args:
            width: East-west dimension in studs.
            depth: North-south dimension in studs.
            color: LDraw color code.
            fill_part: Part catalog key for fill plates.
            name: Identifier for LDraw comments.
        """
        self.name = name or "floor"
        self.width = width
        self.depth = depth
        self.color = color
        self.fill_part = fill_part.value
        self.height_plates = 1  # one plate tall

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Tile the floor area with plates.

        Uses a greedy algorithm: fill rows along X with widest plates,
        advance along Z by the plate's depth.

        Available plates for tiling (sorted by area, largest first):
          plate_2x4 (8), plate_2x3 (6), plate_2x2 (4),
          plate_1x4 (4), plate_1x2 (2), plate_1x1 (1)

        Returns:
            List of BrickPlacement in floor-local coordinates.
        """
        placements: list[BrickPlacement] = []
        prefix = f"{comment_prefix}{self.name}"

        # Available plates sorted by depth then width (largest first)
        # so we fill with fewer, larger plates.
        fill_plates = [
            PARTS["plate_2x4"],  # 4w x 2d
            PARTS["plate_2x3"],  # 3w x 2d
            PARTS["plate_2x2"],  # 2w x 2d
            PARTS["plate_1x4"],  # 4w x 1d
            PARTS["plate_1x2"],  # 2w x 1d
            PARTS["plate_1x1"],  # 1w x 1d
        ]

        # Track which cells are filled: grid[x][z] = bool
        filled = [[False] * self.depth for _ in range(self.width)]

        # Iterate over the floor area and place plates greedily
        for z in range(self.depth):
            for x in range(self.width):
                if filled[x][z]:
                    continue

                # Try to place the largest plate that fits
                placed = False
                for plate in fill_plates:
                    pw = plate.width_studs
                    pd = plate.depth_studs

                    # Check bounds
                    if x + pw > self.width or z + pd > self.depth:
                        continue

                    # Check all cells are unfilled
                    if any(filled[cx][cz] for cx in range(x, x + pw) for cz in range(z, z + pd)):
                        continue

                    # Place this plate and mark cells as filled
                    for cx in range(x, x + pw):
                        for cz in range(z, z + pd):
                            filled[cx][cz] = True

                    placements.append(BrickPlacement(
                        part=plate,
                        x=x, y=0, z=z,
                        rotation=0,
                        color=self.color,
                        comment=prefix,
                    ))
                    placed = True
                    break

                if not placed:
                    filled[x][z] = True  # skip unfillable (shouldn't happen)

        return placements


# ---------------------------------------------------------------------------
# Column Class
# ---------------------------------------------------------------------------
#
# A Column is a vertical stack of bricks at a single point.
# Used for: porch columns, structural piers, decorative pillars.
#
# The column is 1x1 studs by default (using brick_1x1), but can use
# larger bricks (e.g. brick_2x2) for thicker columns.


class Column:
    """A vertical stack of identical bricks.

    Attributes:
        name: Identifier for LDraw comments.
        height_bricks: Number of brick rows.
        color: LDraw color code.
        part: The Part used for each row of the column.
    """

    def __init__(
        self,
        height: int,
        color: int = Color.WHITE,
        part_type: PartType = PartType.BRICK_1X1,
        name: str = "",
    ):
        """Create a column.

        Args:
            height: Column height in brick rows.
            color: LDraw color code.
            part_type: PartType for each brick in the column.
            name: Identifier for LDraw comments.
        """
        self.name = name or "column"
        self.height_bricks = height
        self.height_plates = height * PLATES_PER_BRICK
        self.color = color
        self.part = find_part(part_type)

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Stack bricks vertically from y=0 up.

        Returns:
            List of BrickPlacement in column-local coordinates.
        """
        placements = []
        prefix = f"{comment_prefix}{self.name}"

        for row in range(self.height_bricks):
            y_plate = row * PLATES_PER_BRICK
            placements.append(BrickPlacement(
                part=self.part,
                x=0, y=y_plate, z=0,
                rotation=0,
                color=self.color,
                comment=f"{prefix} row_{row}",
            ))

        return placements


# ---------------------------------------------------------------------------
# Stairs Class
# ---------------------------------------------------------------------------
#
# A Stairs is a single straight flight of steps (one storey, no landing).
# Each step rises step_height plates and advances tread_depth studs in the
# climb direction. Step 0 starts at y=0.
#
# Canonical orientation is north-facing: climb direction is +Z, width is +X.
# The facing parameter rotates the entire flight about the Y axis.
#
# Cross-section viewed from the side (north-facing, 3 steps):
#
#           ___
#          |   |  step 2 tread  (y = 2 * step_height)
#        __|   |
#       |   |  step 1 tread     (y = 1 * step_height)
#     __|   |
#    |   |  step 0 tread        (y = 0)
#
# Solid fill under each tread makes the structure watertight from the side.
# Each fill column spans from y=0 up to the tread level above it.
#
# For assembly compatibility (place(), attach()):
#   north/south facing: self.width = stair width, self.depth = total climb depth
#   east/west  facing: self.width = total climb depth, self.depth = stair width


class Stairs:
    """A single straight flight of steps.

    Attributes:
        name: Identifier for LDraw comments.
        steps: Number of steps.
        tread_depth: Depth of each tread in studs (along the climb direction).
        step_height: Height per step in plates.
        facing: Direction you face when climbing.
        height_plates: Total height of the flight (steps * step_height).
        width: Footprint X dimension in studs (for assembly compatibility).
        depth: Footprint Z dimension in studs (for assembly compatibility).
    """

    def __init__(
        self,
        steps: int,
        width: int,
        tread_depth: int = 2,
        step_height: int = PLATES_PER_BRICK,
        facing: Literal["north", "south", "east", "west"] = "north",
        color: int = Color.WHITE,
        fill_part: PartType = PartType.BRICK_2X4,
        name: str = "",
    ):
        """Create a straight flight of stairs.

        Args:
            steps: Number of steps.
            width: Width in studs perpendicular to the climb direction.
            tread_depth: Depth of each tread in studs (min 1).
            step_height: Height per step in plates (default = 1 brick = 3 plates).
            facing: Direction you face when going up.
            color: LDraw color code for all bricks and plates.
            fill_part: Part catalog key for the solid fill beneath treads.
            name: Identifier for LDraw comments.
        """
        if steps < 1:
            raise BuilderError(f"Stairs steps must be >= 1, got {steps}")
        if width < 1:
            raise BuilderError(f"Stairs width must be >= 1, got {width}")
        if tread_depth < 1:
            raise BuilderError(f"Stairs tread_depth must be >= 1, got {tread_depth}")
        if step_height < 1:
            raise BuilderError(f"Stairs step_height must be >= 1, got {step_height}")
        if facing not in ("north", "south", "east", "west"):
            raise BuilderError(
                f"Invalid facing '{facing}'. Must be north, south, east, or west."
            )

        self.name = name or "stairs"
        self.steps = steps
        self.tread_depth = tread_depth
        self.step_height = step_height
        self.facing = facing
        self.color = color
        self.fill_part = fill_part

        self.height_plates = steps * step_height

        # Canonical extents (north-facing): width along X, climb along Z.
        self._canonical_width = width
        self._canonical_depth = steps * tread_depth

        # Footprint for assembly.place() / attach().
        # Swap axes for east/west so the bounding box reflects the rotated footprint.
        if facing in ("north", "south"):
            self.width = width
            self.depth = self._canonical_depth
        else:  # east / west
            self.width = self._canonical_depth
            self.depth = width

    # --- Internal helpers ---

    def _tile_area(
        self,
        region_w: int,
        region_d: int,
        y: int,
        z_offset: int,
        parts: list,
        comment: str,
    ) -> list[BrickPlacement]:
        """Greedily tile a (region_w × region_d) stud area at height y.

        Identical to FloorSlab's tiling loop, parameterised for reuse.
        All parts are placed at rotation=0 (lying flat).

        Args:
            region_w: Area width in studs (along X).
            region_d: Area depth in studs (along Z, relative to z_offset).
            y: Y position in plates.
            z_offset: Absolute Z origin of the area in studs.
            parts: Ordered list of candidate parts (widest/largest first).
            comment: LDraw comment string for all placements in this area.
        """
        placements = []
        filled = [[False] * region_d for _ in range(region_w)]

        for z in range(region_d):
            for x in range(region_w):
                if filled[x][z]:
                    continue
                for part in parts:
                    pw = part.width_studs
                    pd = part.depth_studs
                    if x + pw > region_w or z + pd > region_d:
                        continue
                    if any(filled[cx][cz]
                           for cx in range(x, x + pw)
                           for cz in range(z, z + pd)):
                        continue
                    for cx in range(x, x + pw):
                        for cz in range(z, z + pd):
                            filled[cx][cz] = True
                    placements.append(BrickPlacement(
                        part=part, x=x, y=y, z=z_offset + z,
                        rotation=0, color=self.color, comment=comment,
                    ))
                    break  # placed — move to next unfilled cell

        return placements

    def _canonical_placements(self, prefix: str) -> list[BrickPlacement]:
        """Generate placements in canonical north-facing orientation.

        For each step i:
          - Tread:  one plate layer at y = i * step_height, z = i * tread_depth.
          - Fill:   brick rows from y=0 up to the tread level, same z column.
                    Only complete brick rows are filled; a sub-brick gap at the
                    top is acceptable when step_height % PLATES_PER_BRICK != 0.
        """
        # Plate catalog for treads: same greedy order as FloorSlab.
        tread_plates = [
            PARTS["plate_2x4"],
            PARTS["plate_2x3"],
            PARTS["plate_2x2"],
            PARTS["plate_1x4"],
            PARTS["plate_1x2"],
            PARTS["plate_1x1"],
        ]

        result = []
        W = self._canonical_width

        for i in range(self.steps):
            y_tread = i * self.step_height
            z_step  = i * self.tread_depth

            # Tread: flat plate layer at the top surface of this step.
            result.extend(self._tile_area(
                W, self.tread_depth,
                y=y_tread, z_offset=z_step,
                parts=tread_plates,
                comment=f"{prefix}step_{i}_tread",
            ))

            # Solid fill beneath this step (step 0 sits at y=0, no fill needed).
            fill_rows = y_tread // PLATES_PER_BRICK
            for row in range(fill_rows):
                result.extend(self._tile_area(
                    W, self.tread_depth,
                    y=row * PLATES_PER_BRICK, z_offset=z_step,
                    parts=FILL_BRICKS,
                    comment=f"{prefix}step_{i}_fill",
                ))

        return result

    def _apply_facing(self, canonical: list[BrickPlacement]) -> list[BrickPlacement]:
        """Rotate canonical north-facing placements to the desired facing.

        All canonical placements have rotation=0, so effective part dimensions
        equal part.width_studs × part.depth_studs without any swapping.
        The transform remaps (x, z) and sets the output rotation so
        to_ldraw_line() produces the correct LDraw orientation.

        Transform derivation (W = canonical width, D = canonical depth):
          south (180°): mirror both axes  → x' = W-x-pw,  z' = D-z-pd
          east  ( 90°): climb becomes +X  → x' = z,        z' = W-x-pw
          west  (270°): climb becomes -X  → x' = D-z-pd,   z' = x
        """
        if self.facing == "north":
            return canonical

        W = self._canonical_width
        D = self._canonical_depth
        result = []

        for p in canonical:
            # Canonical rotation is always 0, so no dimension swapping.
            pw = p.part.width_studs
            pd = p.part.depth_studs

            if self.facing == "south":
                x   = W - p.x - pw
                z   = D - p.z - pd
                rot = 180
            elif self.facing == "east":
                x   = p.z
                z   = W - p.x - pw
                rot = 90
            else:  # west
                x   = D - p.z - pd
                z   = p.x
                rot = 270

            result.append(BrickPlacement(p.part, x, p.y, z, rot, p.color, p.comment))

        return result

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate all BrickPlacements for this flight of stairs.

        Returns placements in Stairs-local coordinates (origin at the base
        of step 0, south-west corner for north-facing).

        Returns:
            List of BrickPlacement in Stairs-local coordinates.
        """
        prefix = f"{comment_prefix}{self.name} > "
        return self._apply_facing(self._canonical_placements(prefix))


# ---------------------------------------------------------------------------
# StaircaseShaft Class
# ---------------------------------------------------------------------------
#
# A StaircaseShaft composes multiple Stairs flights and FloorSlab landings
# into a complete multi-floor staircase (no enclosing shaft walls).
#
# Two styles:
#   switchback — Two flights per floor facing opposite directions, placed side
#                by side perpendicular to the climb axis. A landing slab
#                connects them at the mid-floor height.
#
#                Top view (north first_facing):
#                  ┌──────────┬──────────┐  ← landing strip (z = D_flight)
#                  │ flight A │ flight B │
#                  │ (north)  │ (south)  │
#                  └──────────┴──────────┘  ← z = 0
#                    x=0    x=W  x=2W
#
#   straight  — One flight per floor, same facing and footprint, stacked
#               vertically. Suitable for single-direction stairwells.
#
# The landing is always at the +Z end for north/south first_facing, and at
# the +X end for east/west first_facing.


class StaircaseShaft:
    """Multi-floor staircase built from Stairs flights and FloorSlab landings.

    No enclosing shaft walls — place a Box or WallLayout around it separately.

    Attributes:
        name: Identifier for LDraw comments.
        floors: Number of floors spanned.
        height_plates: Total height (floors * floor_height_bricks * 3).
        width: Footprint X dimension in studs.
        depth: Footprint Z dimension in studs.
    """

    _OPPOSITES: dict[str, str] = {
        "north": "south", "south": "north",
        "east":  "west",  "west":  "east",
    }

    def __init__(
        self,
        floors: int,
        floor_height_bricks: int,
        stair_width: int,
        tread_depth: int = 2,
        step_height: int = PLATES_PER_BRICK,
        style: Literal["switchback", "straight"] = "switchback",
        first_facing: Literal["north", "south", "east", "west"] = "north",
        color: int = Color.WHITE,
        fill_part: PartType = PartType.BRICK_2X4,
        name: str = "",
    ):
        """Create a multi-floor staircase shaft.

        Args:
            floors: Number of floors to span.
            floor_height_bricks: Height of one floor in brick rows.
            stair_width: Width of each flight in studs.
            tread_depth: Depth of each tread in studs (default 2).
            step_height: Height per step in plates (default = 1 brick = 3 plates).
                         Must evenly divide floor_height (switchback: half-floor).
            style: "switchback" — two flights per floor; "straight" — one flight.
            first_facing: Direction faced when climbing the first flight.
            color: LDraw color for all flights and landings.
            fill_part: Part catalog key for solid fill beneath treads.
            name: Identifier for LDraw comments.
        """
        if floors < 1:
            raise BuilderError(f"StaircaseShaft floors must be >= 1, got {floors}")
        if floor_height_bricks < 1:
            raise BuilderError(f"floor_height_bricks must be >= 1, got {floor_height_bricks}")
        if stair_width < 1:
            raise BuilderError(f"stair_width must be >= 1, got {stair_width}")
        if tread_depth < 1:
            raise BuilderError(f"tread_depth must be >= 1, got {tread_depth}")
        if step_height < 1:
            raise BuilderError(f"step_height must be >= 1, got {step_height}")
        if style not in ("switchback", "straight"):
            raise BuilderError(f"Invalid style '{style}'. Must be 'switchback' or 'straight'.")
        if first_facing not in ("north", "south", "east", "west"):
            raise BuilderError(
                f"Invalid first_facing '{first_facing}'. Must be north, south, east, or west."
            )

        floor_height_plates = floor_height_bricks * PLATES_PER_BRICK

        if style == "switchback":
            divisor = 2 * step_height
            if floor_height_plates % divisor != 0:
                raise BuilderError(
                    f"floor_height_bricks={floor_height_bricks} ({floor_height_plates} plates) "
                    f"must be divisible by 2*step_height={divisor} plates for switchback. "
                    f"Adjust floor_height_bricks or step_height."
                )
            steps_per_flight = (floor_height_plates // 2) // step_height
        else:  # straight
            if floor_height_plates % step_height != 0:
                raise BuilderError(
                    f"floor_height_bricks={floor_height_bricks} ({floor_height_plates} plates) "
                    f"must be divisible by step_height={step_height} plates for straight stairs."
                )
            steps_per_flight = floor_height_plates // step_height

        D_flight     = steps_per_flight * tread_depth  # climb depth of one flight in studs
        landing_depth = tread_depth                    # landing strip is one tread wide

        self.name               = name or "staircase"
        self.floors             = floors
        self.floor_height_plates = floor_height_plates
        self.stair_width        = stair_width
        self.tread_depth        = tread_depth
        self.step_height        = step_height
        self.steps_per_flight   = steps_per_flight
        self.style              = style
        self.first_facing       = first_facing
        self.color              = color
        self.fill_part          = fill_part.value
        self.height_plates      = floors * floor_height_plates
        self._D_flight          = D_flight
        self._landing_depth     = landing_depth

        # Footprint for assembly.place() / attach().
        # switchback adds a landing strip beyond the flight depth.
        # north/south: flights run along Z, side by side in X.
        # east/west:   flights run along X, side by side in Z.
        if first_facing in ("north", "south"):
            self.width = (2 * stair_width) if style == "switchback" else stair_width
            self.depth = (D_flight + landing_depth) if style == "switchback" else D_flight
        else:  # east / west
            self.width = (D_flight + landing_depth) if style == "switchback" else D_flight
            self.depth = (2 * stair_width) if style == "switchback" else stair_width

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate BrickPlacements for all floors of the staircase.

        Each floor contributes:
          switchback: flight A + flight B + landing slab.
          straight:   one flight only.

        Returns:
            List of BrickPlacement in StaircaseShaft-local coordinates.
        """
        prefix        = f"{comment_prefix}{self.name} > "
        result        = []
        second_facing = self._OPPOSITES[self.first_facing]

        for k in range(self.floors):
            floor_prefix = f"{prefix}floor_{k} > "
            y_a = k * self.floor_height_plates  # Y base of floor k

            if self.style == "switchback":
                y_b = y_a + self.floor_height_plates // 2  # mid-floor: top of A, base of B

                stairs_a = Stairs(
                    steps=self.steps_per_flight, width=self.stair_width,
                    tread_depth=self.tread_depth, step_height=self.step_height,
                    facing=cast(_Facing, self.first_facing), color=self.color,
                    fill_part=self.fill_part, name="flight_a",
                )
                stairs_b = Stairs(
                    steps=self.steps_per_flight, width=self.stair_width,
                    tread_depth=self.tread_depth, step_height=self.step_height,
                    facing=cast(_Facing, second_facing), color=self.color,
                    fill_part=self.fill_part, name="flight_b",
                )

                # Landing slab dimensions depend on the climb axis.
                if self.first_facing in ("north", "south"):
                    landing = FloorSlab(
                        width=2 * self.stair_width, depth=self._landing_depth,
                        color=self.color, name="landing",
                    )
                    # Flights side by side in X; landing at +Z end.
                    ax, az = 0, 0
                    bx, bz = self.stair_width, 0
                    lx, lz = 0, self._D_flight
                else:  # east / west
                    landing = FloorSlab(
                        width=self._landing_depth, depth=2 * self.stair_width,
                        color=self.color, name="landing",
                    )
                    # Flights side by side in Z; landing at +X end.
                    ax, az = 0, 0
                    bx, bz = 0, self.stair_width
                    lx, lz = self._D_flight, 0

                result.extend(
                    p.offset_by(ax, y_a, az) for p in stairs_a.to_placements(floor_prefix)
                )
                result.extend(
                    p.offset_by(bx, y_b, bz) for p in stairs_b.to_placements(floor_prefix)
                )
                result.extend(
                    p.offset_by(lx, y_b, lz) for p in landing.to_placements(floor_prefix)
                )

            else:  # straight — one flight per floor, same XZ footprint, stacked in Y
                stairs = Stairs(
                    steps=self.steps_per_flight, width=self.stair_width,
                    tread_depth=self.tread_depth, step_height=self.step_height,
                    facing=cast(_Facing, self.first_facing), color=self.color,
                    fill_part=self.fill_part, name="flight",
                )
                result.extend(
                    p.offset_by(0, y_a, 0) for p in stairs.to_placements(floor_prefix)
                )

        return result
