"""
Stairs: single straight flight of steps.
StaircaseShaft: multi-floor staircase composed of Stairs flights and FloorSlab landings.
"""

from __future__ import annotations

from typing import Literal, cast

from .coords import PLATES_PER_BRICK, _Facing
from .parts import PartType, FILL_BRICKS, FILL_PLATES, Color
from .core import BuilderError, BrickPlacement
from .floor import FloorSlab
from .structures import _tile_area_greedy
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
        """Delegate to _tile_area_greedy with this stair's color."""
        return _tile_area_greedy(region_w, region_d, 0, z_offset, y, parts, self.color, comment)

    def _canonical_placements(self, prefix: str) -> list[BrickPlacement]:
        """Generate placements in canonical north-facing orientation.

        For each step i:
          - Tread:  one plate layer at y = i * step_height, z = i * tread_depth.
          - Fill:   brick rows from y=0 up to the tread level, same z column.
                    Only complete brick rows are filled; a sub-brick gap at the
                    top is acceptable when step_height % PLATES_PER_BRICK != 0.
        """
        result = []
        W = self._canonical_width

        for i in range(self.steps):
            y_tread = i * self.step_height
            z_step  = i * self.tread_depth

            # Tread: flat plate layer at the top surface of this step.
            result.extend(self._tile_area(
                W, self.tread_depth,
                y=y_tread, z_offset=z_step,
                parts=FILL_PLATES,
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

        # Select the coordinate transform once — self.facing never changes.
        # Canonical rotation is always 0, so part dimensions need no swapping.
        transforms = {
            "south": lambda p: (W - p.x - p.part.width_studs, D - p.z - p.part.depth_studs, 180),
            "east":  lambda p: (p.z,                           W - p.x - p.part.width_studs,  90),
            "west":  lambda p: (D - p.z - p.part.depth_studs, p.x,                           270),
        }
        tf = transforms[self.facing]
        return [
            BrickPlacement(p.part, x, p.y, z, rot, p.color, p.comment)
            for p in canonical
            for x, z, rot in (tf(p),)
        ]

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

# FIXME TODO: These are broken, not interconnected by landings, collide with FloorSlabs, too wide...
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
        self.fill_part          = fill_part
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
