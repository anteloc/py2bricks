"""
GableRoof: a peaked roof made of sloped brick rows.

The roof sits on top of a rectangular footprint. The ridge runs
along one axis (east_west or north_south). The two sloping sides
step inward, each row 2 studs narrower per side (slope brick depth)
and 1 brick taller.

Anatomy (cross-section, ridge running east-west, viewed from east):

         /\\            <- ridge
        /  \\
       /    \\          Each "step" is one brick row, 2 studs wide (slope
      /      \\            brick depth), rising 1 brick per step.
     /________\\        <- base = full width (underlying wall, not part of roof)

The gable ends (triangular walls closing the ends) are generated
as brick walls, creating a smooth transition from the roof to the walls.


Anatomy (sloped brick placement):

 ^ = stud
[ ] = anti-stud/peg hole/etc.

Slope bricks are 2 anti-studs deep (bottom), but only 1 stud deep (top).

Side view (showing how roof sits on underlying structure):

         /    ^  |         <-  Slope 45 deg. brick 2 x length (on top of base roof + 1 offset stud, makes smooth slope)
       / [ ] [ ] |
    /     ^  |             <- Slope 45 deg. brick 2 x length (base roof)
   / [ ] [ ] |
       |  ^   ^  |         <- Brick 2 x length (base - part of underlying wall/box, NOT roof)
       | [ ] [ ] |

The roof itself starts at y=0 with slope bricks directly.
"""

from __future__ import annotations

from .coords import PLATES_PER_BRICK
from .parts import Part, PARTS, FILL_BRICKS, FILL_SLOPES, PartType, Color
from .core import BuilderError, BrickPlacement
from .wall import WALL_DEPTH_STUDS


def _tile_row(
    span: int,
    y_plate: int,
    x0: float,
    z0: float,
    along_x: bool,
    rotation: int,
    color: int,
    comment: str,
    fill: list[Part] | None = None,
) -> list[BrickPlacement]:
    """Greedily fill a single brick row using the provided fill list.

    Walks from 0 to `span`, placing the widest fitting part at each step.
    Used by GableRoof slope and gable builders.

    Args:
        span: Total studs to fill along the tiling axis.
        y_plate: Vertical position in plates.
        x0, z0: Starting position in studs.
        along_x: True = tile along X; False = tile along Z.
        rotation: Brick rotation angle (0 or 90).
        color: LDraw color code.
        comment: LDraw comment string for each placed brick.
        fill: Parts to use for tiling. Defaults to FILL_BRICKS.

    Returns:
        List of BrickPlacements for this row.
    """
    if fill is None:
        fill = FILL_BRICKS
    placements: list[BrickPlacement] = []
    pos = 0
    while pos < span:
        placed = False
        for brick in fill:
            if pos + brick.width_studs <= span:
                placements.append(BrickPlacement(
                    part=brick,
                    x=x0 + (pos if along_x else 0),
                    y=y_plate,
                    z=z0 + (0 if along_x else pos),
                    rotation=rotation,
                    color=color,
                    comment=comment,
                ))
                pos += brick.width_studs
                placed = True
                break
        if not placed:
            pos += 1  # skip unfillable stud (shouldn't happen with 1x1 fallback)
    return placements


class GableRoof:
    """A peaked roof made of 45° slope brick rows.

    The roof's local coordinate space:
      - Origin at the bottom-left corner of the footprint (same as a Box).
      - Ridge runs along the specified axis.
      - Slope bricks step inward 2 studs per row (slope brick depth)
        and rise 1 brick per step from both sides toward the ridge.

    Slope rows use FILL_SLOPES (SLOPE_2X4, SLOPE_2X2).
    Gable end walls use FILL_BRICKS (regular bricks).

    Attributes:
        name: Identifier for LDraw comments.
        width: Footprint width in studs (perpendicular to ridge for north_south,
               along ridge for east_west).
        depth: Footprint depth in studs (along ridge for east_west).
        ridge: "east_west" or "north_south" — direction the ridge runs.
        color: LDraw color code for roof bricks.
        fill_part: Part catalog key for roof bricks.
        num_steps: How many slope rows per side (= slope_span // 4).
    """

    def __init__(
        self,
        width: int,
        depth: int,
        ridge: str = "east_west",
        color: int = Color.DARK_BLUISH_GREY,
        fill_part: PartType = PartType.BRICK_1X1,
        name: str = "",
    ):
        """Create a sloped roof.

        Args:
            width: Footprint width in studs (east-west).
            depth: Footprint depth in studs (north-south).
            ridge: "east_west" (ridge runs left-right, slopes along Z) or
                   "north_south" (ridge runs front-back, slopes along X).
            color: LDraw color code for roof bricks.
            fill_part: Unused (slopes always use FILL_SLOPES). Kept for
                       API parity with GableRoof.
            name: Identifier for LDraw comments.
        """
        if ridge not in ("east_west", "north_south"):
            raise BuilderError(
                f"Invalid ridge direction '{ridge}'. "
                f"Must be 'east_west' or 'north_south'."
            )

        self.name = name or "roof"
        self.width = width
        self.depth = depth
        self.ridge = ridge
        self.color = color
        self.fill_part = fill_part.value

        # The slope dimension is perpendicular to the ridge.
        # Each slope brick is WALL_DEPTH_STUDS (2) studs wide in slope direction,
        # so num_steps = (slope_span // 2) // 2 = slope_span // 4.
        if ridge == "east_west":
            self.slope_span = depth   # slopes run along Z
        else:
            self.slope_span = width   # slopes run along X

        self.num_steps = self.slope_span // 2 # slope bricks stack diagonally, so 2

    @property
    def height_plates(self) -> int:
        """Total height of the roof in plates."""
        return self.num_steps * PLATES_PER_BRICK

    def to_placements(self, comment_prefix: str = "") -> list[BrickPlacement]:
        """Generate brick placements for the sloped roof.

        Creates two mirrored slopes stepping inward toward the ridge
        (2 studs per step, 1 brick height per step), plus triangular
        gable end walls filled with regular bricks.

        All coordinates are in roof-local space. The roof's base
        is at y=0 (meant to be placed on top of walls via place()).

        Returns:
            List of BrickPlacement in roof-local coordinates.
        """
        prefix = f"{comment_prefix}{self.name}"
        placements: list[BrickPlacement] = []

        if self.ridge == "east_west":
            placements.extend(self._build_ew_slopes(prefix))
            placements.extend(self._build_ew_gables(prefix))
        else:  # north_south
            placements.extend(self._build_ns_slopes(prefix))
            placements.extend(self._build_ns_gables(prefix))

        return placements

    def _build_ew_slopes(self, prefix: str) -> list[BrickPlacement]:
        """Build slopes for east-west ridge (stepping along Z/depth).

        For each step level, place a row of slope bricks along the full
        width (X) on both the south slope (front) and north slope (back).

        South slope: rotation=180 (low/open end faces south, slope rises north).
        North slope: rotation=0   (low/open end faces north, slope rises south).
        """
        placements: list[BrickPlacement] = []
        for step in range(self.num_steps):
            y_plate = step * PLATES_PER_BRICK
            z_south = self.depth - step - 1.5
            z_north = step - 0.5

            for z_pos, side, rot in [
                (z_south, "south_slope", 180),
                (z_north, "north_slope", 0),
            ]:
                placements.extend(_tile_row(
                    span=self.width, y_plate=y_plate,
                    x0=0, z0=z_pos, along_x=True, rotation=rot,
                    color=self.color,
                    comment=f"{prefix} {side} step_{step}",
                    fill=FILL_SLOPES,
                ))
        return placements

    def _build_ew_gables(self, prefix: str) -> list[BrickPlacement]:
        """Build triangular gable end walls for east-west ridge.

        Gable walls fill the triangular space at the west (x=0) and
        east (x=width) ends of the roof. Each step level shrinks the
        gable span by 2 studs per side (matching the 2-stud slope step).
        """
        placements: list[BrickPlacement] = []
        for step in range(self.num_steps):
            y_plate = step * PLATES_PER_BRICK
            z_start = step
            z_end = self.depth - step
            gable_length = z_end - z_start
            if gable_length <= 0:
                break
            for x_pos, side in [
                (0, "west_gable"),
                (self.width - WALL_DEPTH_STUDS, "east_gable"),
            ]:
                placements.extend(_tile_row(
                    span=gable_length, y_plate=y_plate,
                    x0=x_pos, z0=z_start, along_x=False, rotation=90,
                    color=self.color,
                    comment=f"{prefix} {side} step_{step}",
                ))
        return placements

    def _build_ns_slopes(self, prefix: str) -> list[BrickPlacement]:
        """Build slopes for north-south ridge (stepping along X/width).

        Same logic as _build_ew_slopes but rotated: steps along X,
        rows run along Z (depth).

        West slope: rotation=270 (low/open end faces west, slope rises east).
        East slope: rotation=90  (low/open end faces east, slope rises west).
        """
        placements: list[BrickPlacement] = []
        for step in range(self.num_steps):
            y_plate = step * PLATES_PER_BRICK
            x_west = step - 0.5
            x_east = self.width - step - 1.5
            for x_pos, side, rot in [
                (x_west, "west_slope", 270),
                (x_east, "east_slope", 90),
            ]:
                placements.extend(_tile_row(
                    span=self.depth, y_plate=y_plate,
                    x0=x_pos, z0=0, along_x=False, rotation=rot,
                    color=self.color,
                    comment=f"{prefix} {side} step_{step}",
                    fill=FILL_SLOPES,
                ))
        return placements

    def _build_ns_gables(self, prefix: str) -> list[BrickPlacement]:
        """Build triangular gable end walls for north-south ridge.

        Gable walls at south (z=0) and north (z=depth) ends, running
        along X. Each step level shrinks the gable span by 2 studs per
        side (matching the 2-stud slope step).
        """
        placements: list[BrickPlacement] = []
        for step in range(self.num_steps):
            y_plate = step * PLATES_PER_BRICK

            x_start = step
            x_end = self.width - step
            
            gable_length = x_end - x_start
            if gable_length <= 0:
                break
            for z_pos, side in [
                (0, "south_gable"),
                (self.depth - WALL_DEPTH_STUDS, "north_gable"),
            ]:
                placements.extend(_tile_row(
                    span=gable_length, y_plate=y_plate,
                    x0=x_start, z0=z_pos, along_x=True, rotation=0,
                    color=self.color,
                    comment=f"{prefix} {side} step_{step}",
                ))
        return placements
