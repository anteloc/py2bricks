"""
Wall: rectangular brick wall with openings and inserts.
Box: 4-wall rectangular enclosure.
WallLayout: convenience for defining a set of interconnected walls forming an arbitrary shape.
"""

from __future__ import annotations
from typing import Literal

from .coords import PLATES_PER_BRICK, FACING_TO_ROTATION
from .parts import PartType, Part, PARTS, FILL_BRICKS, find_part, Color
from .core import BuilderError, BrickPlacement

# TODO reevaluate this, maybe allow variable wall depth depending on the fill_part used?
WALL_DEPTH_STUDS = 2  # all walls are 1 brick (2 studs) deep

# ---------------------------------------------------------------------------
# Wall Class
# ---------------------------------------------------------------------------
# A Wall is a rectangular surface of bricks, defined by:
#   - length (studs along its face)
#   - height (brick rows)
#   - facing (north/south/east/west)

# Internally, a wall stores a 2D boolean grid sized in studs × plates.
# True = solid (will be filled with bricks). False = opening (empty).

# The wall uses 2xN bricks oriented with their depth (2 studs) going
# INTO the wall, and their width along the wall face. This gives
# structurally realistic walls that are 2 studs (1 brick) deep.

# At export time, the solid regions are tiled with bricks using a greedy
# algorithm with running bond (each row offset by half a brick width).
class Wall:
    """A rectangular brick wall with openings and inserted parts.

    The wall lives in its own local coordinate space:
      - X axis: along the wall face, 0 = left end, length = right end (studs)
      - Y axis: up from the wall base, 0 = bottom (plates)
      - The wall is WALL_DEPTH_STUDS (2) deep in the Z direction.

    Global positioning (where the wall sits in the scene) is handled by
    its parent Box or Group, not by the wall itself.

    Attributes:
        name: Identifier for LDraw comments (e.g. "wall_north").
        length: Wall length in studs.
        height_bricks: Wall height in brick rows.
        height_plates: Wall height in plates (= height_bricks * 3).
        facing: Cardinal direction string.
        color: Default LDraw color code for bricks.
        fill_part: Default part key for filling solid regions.
        grid: 2D boolean array [x_stud][y_plate]. True = solid.
        inserts: List of (part, x_stud, y_plate, color) for windows/doors.
        ledges: List of (y_plate, overhang, color, part_key) tuples.
    """

    def __init__(
        self,
        length: int,
        height: int,
        facing: str,
        color: int = Color.WHITE,
        fill_part: PartType = PartType.BRICK_2X4,
        name: str = "",
    ):
        """Create a wall. All cells start as solid (True).

        Args:
            length: Wall length in studs (along the face).
            height: Wall height in brick rows (1 row = 3 plates).
            facing: "north", "south", "east", or "west".
            color: LDraw color code for the wall bricks.
            fill_part: Part catalog key for the fill brick.
            name: Identifier used in LDraw comments.
        """
        if facing not in FACING_TO_ROTATION:
            raise BuilderError(
                f"Invalid facing '{facing}'. Must be one of: "
                f"{list(FACING_TO_ROTATION.keys())}"
            )
        if length < 1:
            raise BuilderError(f"Wall length must be >= 1, got {length}")
        if height < 1:
            raise BuilderError(f"Wall height must be >= 1, got {height}")

        self.name = name or f"wall_{facing}"
        self.length = length
        self.height_bricks = height
        self.height_plates = height * PLATES_PER_BRICK
        self.facing = facing
        self.color = color
        self.fill_part = fill_part.value

        # Boolean grid: grid[x][y] where x=stud position along face,
        # y=plate position from base. True = solid, False = opening.
        self.grid: list[list[bool]] = [
            [True for _ in range(self.height_plates)]
            for _ in range(self.length)
        ]

        # Inserted parts (windows, doors) placed in openings.
        self.inserts: list[tuple[Part, int, int, int]] = []

        # Ledges: (y_plate, z_offset, color, part_key)
        # z_offset is pre-computed from overhang + side + facing at ledge() call time.
        self.ledges: list[tuple[int, int, int, str]] = []

    # --- Modification Methods ---

    def opening(self, x: int, y: int, width: int, height: int) -> None:
        """Cut a rectangular opening in the wall (for windows, doors, etc.).

        Clears grid cells to False in the specified rectangle.

        Args:
            x: Left edge of opening in studs from wall's left end.
            y: Bottom edge in brick rows from wall base.
            width: Opening width in studs.
            height: Opening height in brick rows.

        Raises:
            BuilderError: If the opening extends beyond wall bounds.
        """
        y_plates = y * PLATES_PER_BRICK
        h_plates = height * PLATES_PER_BRICK

        if x < 0 or x + width > self.length:
            raise BuilderError(
                f"Opening x={x}, width={width} exceeds wall '{self.name}' "
                f"length of {self.length} studs. "
                f"Opening would span studs {x}..{x + width - 1}, "
                f"but wall spans 0..{self.length - 1}."
            )
        if y < 0 or y_plates + h_plates > self.height_plates:
            raise BuilderError(
                f"Opening y={y}, height={height} exceeds wall '{self.name}' "
                f"height of {self.height_bricks} rows. "
                f"Opening would span rows {y}..{y + height - 1}, "
                f"but wall spans 0..{self.height_bricks - 1}."
            )

        for gx in range(x, x + width):
            for gy in range(y_plates, y_plates + h_plates):
                self.grid[gx][gy] = False

    def insert(self, part_type: PartType, x: int, y: int,
               color: int | None = None) -> None:
        """Place a part (window, door) into an existing opening.

        Args:
            part_type: The PartType enum value for the part to insert.
            x: Left edge in studs from wall's left end.
            y: Bottom edge in brick rows from wall base.
            color: LDraw color code. None = auto (TRANS_CLEAR for windows,
                   DARK_BLUISH_GREY for doors).

        Raises:
            BuilderError: If part not found or no opening at position.
        """
        part = find_part(part_type)
        y_plates = y * PLATES_PER_BRICK

        # Verify the full part footprint falls within an opening.
        # Checks every (stud, plate) cell the part occupies, not just the corner.
        if any(
            self.grid[cx][cy]
            for cx in range(x, x + part.width_studs)
            for cy in range(y_plates, y_plates + part.height_plates)
            if cx < self.length and cy < self.height_plates
        ):
            raise BuilderError(
                f"No opening for '{part_type.value}' at x={x}, y={y} on wall "
                f"'{self.name}'. Call .opening(x={x}, y={y}, "
                f"width={part.width_studs}, height={part.height_plates // PLATES_PER_BRICK}) first."
            )

        if color is None:
            if "window" in part_type.value:
                color = Color.TRANS_CLEAR
            elif "door" in part_type.value:
                color = Color.DARK_BLUISH_GREY
            else:
                color = self.color

        self.inserts.append((part, x, y_plates, color))

    def window_row(
        self,
        y: int,
        width: int,
        height: int,
        count: int,
        part_type: PartType,
        spacing: str | int = "even",
        color: int | None = None,
    ) -> None:
        """Cut openings and insert windows in a regular horizontal pattern.

        Args:
            y: Bottom edge of windows in brick rows from wall base.
            width: Each window's width in studs.
            height: Each window's height in brick rows.
            count: Number of windows to place.
            part_type: PartType for the window part.
            spacing: "even" to distribute evenly, or int for explicit gap.
            color: LDraw color for the windows. None = auto.

        Raises:
            BuilderError: If windows don't fit in the wall.
        """
        if count < 1:
            raise BuilderError("window_row count must be >= 1")

        # Calculate x positions for each window
        if spacing == "even":
            total_window = count * width
            if total_window > self.length:
                raise BuilderError(
                    f"Cannot fit {count} windows of width {width} "
                    f"(total {total_window} studs) in wall '{self.name}' "
                    f"of length {self.length} studs."
                )
            total_gap = self.length - total_window
            gap = total_gap / (count + 1)
            x_positions = [
                int(round(gap + i * (width + gap)))
                for i in range(count)
            ]
        else:
            gap = int(spacing)
            total_width = count * width + (count - 1) * gap
            if total_width > self.length:
                raise BuilderError(
                    f"Cannot fit {count} windows of width {width} "
                    f"with gap {gap} (total {total_width} studs) "
                    f"in wall '{self.name}' of length {self.length} studs."
                )
            start_x = (self.length - total_width) // 2
            x_positions = [
                start_x + i * (width + gap)
                for i in range(count)
            ]

        for x_pos in x_positions:
            self.opening(x=x_pos, y=y, width=width, height=height)
            self.insert(part_type=part_type, x=x_pos, y=y, color=color)

    def ledge(
        self,
        y: int,
        overhang: int = 1,
        color: int | None = None,
        part_type: PartType = PartType.PLATE_2X4,
        side: str = "outward",
    ) -> None:
        """Add an overhanging ledge/cornice at a given row height.

        Args:
            y: Row position in brick rows from wall base.
            overhang: How many studs the ledge projects from the wall face.
            color: LDraw color. None = use wall color.
            part_type: PartType for the ledge plates.
            side: "outward" (exterior face) or "inward" (interior face).

        Raises:
            BuilderError: If side is not "outward" or "inward".
        """
        if side not in ("outward", "inward"):
            raise BuilderError(
                f"Invalid side '{side}' for ledge on wall '{self.name}'. "
                "Must be 'outward' or 'inward'."
            )

        # z is a stud-edge coordinate; a plate at z_offset spans z_offset to
        # z_offset+depth_studs. The plate always overlaps the wall by 1 stud,
        # so only the sign of z_offset determines the direction.
        #
        # south/west: outer face at stud-edge z=0 → outward is negative z
        # north/east: outer face at stud-edge z=WALL_DEPTH_STUDS → outward is positive z
        outer_at_z0 = self.facing in ("south", "west")
        if side == "outward":
            z_offset = -overhang if outer_at_z0 else overhang
        else:  # inward
            z_offset = overhang if outer_at_z0 else -overhang

        y_plates = y * PLATES_PER_BRICK
        ledge_color = color if color is not None else self.color
        self.ledges.append((y_plates, z_offset, ledge_color, part_type.value))

    # --- Brick Tiling (for export) ---

    def _bond_offset(self, brick_row: int) -> int:
        """Running bond offset in studs for a given brick row.

        Even rows → 0. Odd rows → half the primary brick width.
        """
        primary_width = PARTS[self.fill_part].width_studs
        return (brick_row % 2) * (primary_width // 2)

    def _tile_solid_regions(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Fill solid grid cells with bricks using a greedy algorithm.

        Uses running bond: even brick-rows start at stud 0, odd brick-rows
        start offset by half the fill brick's width.

        Tries largest bricks first, falls back to smaller ones for gaps.

        Returns:
            List of BrickPlacement in wall-local coordinates.
        """
        placements: list[BrickPlacement] = []

        primary    = PARTS[self.fill_part]
        candidates = [primary] + [b for b in FILL_BRICKS if b != primary]

        for brick_row in range(self.height_bricks):
            y_plate     = brick_row * PLATES_PER_BRICK
            bond_offset = self._bond_offset(brick_row)
            comment     = f"{comment_prefix}{self.name} row_{brick_row}"

            # On offset rows, try to place a starter brick of exactly bond_offset width.
            # If the edge is an opening, no starter is placed; x = -bond_offset so the
            # while loop skips to x=0, keeping the row in the same phase as if the
            # starter sat just off the left edge of the wall.
            x = -bond_offset
            if bond_offset > 0 and self.grid[0][y_plate]:
                for brick in candidates:
                    if brick.width_studs == bond_offset and all(
                        self.grid[cx][y_plate] for cx in range(bond_offset)
                    ):
                        placements.append(BrickPlacement(
                            part=brick,
                            x=0, y=y_plate, z=0,
                            rotation=0, color=self.color, comment=comment,
                        ))
                        x = bond_offset
                        break

            while x < self.length:
                if x < 0:
                    x += 1
                    continue
                if not self.grid[x][y_plate]:
                    x += 1
                    continue

                # Find the widest brick that fits the remaining solid run.
                for brick in candidates:
                    bw = brick.width_studs
                    if x + bw > self.length:
                        continue
                    # Ensure the brick fits vertically within wall bounds.
                    if y_plate + brick.height_plates > self.height_plates:
                        continue
                    # Check full brick volume (width × height), not just 1 plate row.
                    if all(
                        self.grid[cx][cy]
                        for cx in range(x, x + bw)
                        for cy in range(y_plate, y_plate + brick.height_plates)
                    ):
                        placements.append(BrickPlacement(
                            part=brick,
                            x=x, y=y_plate, z=0,
                            rotation=0, color=self.color, comment=comment,
                        ))
                        x += bw
                        break
                else:
                    x += 1  # skip unfillable cell (shouldn't happen with 1x1 fallback)

        return placements

    def _insert_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate BrickPlacements for inserted parts (windows, doors)."""
        placements = []
        for part, x_stud, y_plate, color in self.inserts:
            comment = f"{comment_prefix}{self.name} {part.description}"
            placements.append(BrickPlacement(
                part=part, x=x_stud, y=y_plate, z=0,
                rotation=0, color=color, comment=comment,
            ))
        return placements

    def _ledge_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate BrickPlacements for ledges/cornices.

        z_offset was pre-computed in ledge() from overhang + side + facing,
        so no direction logic is needed here.
        """
        placements = []
        for y_plate, z_offset, color, part_key in self.ledges:
            part = PARTS[part_key]
            brick_row = y_plate // PLATES_PER_BRICK
            bond_offset = self._bond_offset(brick_row)

            x = -bond_offset
            while x < self.length:
                if x < 0:
                    x += 1
                    continue

                comment = f"{comment_prefix}{self.name} ledge"

                if x + part.width_studs <= self.length:
                    placements.append(BrickPlacement(
                        part=part, x=x, y=y_plate, z=z_offset,
                        rotation=0, color=color, comment=comment,
                    ))
                    x += part.width_studs
                else:
                    x += 1
        return placements

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate all BrickPlacements for this wall.

        Combines brick tiling + inserted parts + ledges.
        All coordinates are in wall-local space.

        Args:
            comment_prefix: Prepended to LDraw comments (e.g. "tier_1 > ").

        Returns:
            Combined list of all placements.
        """
        return [
            *self._tile_solid_regions(comment_prefix),
            *self._insert_placements(comment_prefix),
            *self._ledge_placements(comment_prefix),
        ]

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

# TODO Allow for thin walls (1 stud deep), useful for interior partitions
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
        self._register_wall(wall, cx, cz, self._facing)

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
        self._register_wall(wall, cx, cz, travel_dir)

    def _register_wall(self, wall: Wall, cx: int, cz: int, travel_dir: str) -> None:
        """Record a wall in both the ordered list and the name map."""
        self._wall_records.append((wall, cx, cz, travel_dir))
        self._wall_map[wall.name] = wall

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
            rotation = FACING_TO_ROTATION[self._TRAVEL_TO_FACING[travel_dir]]

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

