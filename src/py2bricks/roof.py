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
from .parts import Part, FILL_BRICKS, FILL_SLOPES, FILL_RIDGE, Color
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
        num_steps: How many slope rows per side (= slope_span // 2).
    """

    def __init__(
        self,
        width: int,
        depth: int,
        ridge: str = "east_west",
        color: int = Color.DARK_BLUISH_GREY,
        name: str = "",
    ):
        """Create a sloped roof.

        Args:
            width: Footprint width in studs (east-west).
            depth: Footprint depth in studs (north-south).
            ridge: "east_west" (ridge runs left-right, slopes along Z) or
                   "north_south" (ridge runs front-back, slopes along X).
            color: LDraw color code for roof bricks.
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

        # slope_span: dimension perpendicular to the ridge.
        # num_steps: one slope row per 2-stud slope brick depth.
        slope_span = depth if ridge == "east_west" else width
        self.num_steps = slope_span // 2 

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
        return [
            *self._build_slopes(prefix),
            *self._build_gables(prefix),
        ]

    def _build_slopes(self, prefix: str) -> list[BrickPlacement]:
        """Build slope rows from both sides toward the ridge.

        For each step level, place a slope row along the full ridge length
        on both sides. Steps advance 2 studs inward per level (slope brick
        depth), rising 1 brick per step.

        EW ridge: rows run along X, steps along Z.
          near (north) side: rotation=0;   far (south) side: rotation=180.
        NS ridge: rows run along Z, steps along X.
          near (west) side:  rotation=270; far (east) side:  rotation=90.
        """
        ew         = self.ridge == "east_west"
        row_span   = self.width  if ew else self.depth
        step_span  = self.depth  if ew else self.width
        along_x    = ew  # EW ridge → rows run along X; NS ridge → rows run along Z

        placements: list[BrickPlacement] = []
        for step in range(step_span // 2):
            y        = step * PLATES_PER_BRICK
            near_pos = step - 0.5
            far_pos  = step_span - step - 1.5
            sides = (
                (near_pos, ("north_slope", 0)   if ew else ("west_slope",  270)),
                (far_pos,  ("south_slope", 180) if ew else ("east_slope",   90)),
            )
            for perp_pos, (side, rot) in sides:
                x0 = 0        if along_x else perp_pos
                z0 = perp_pos if along_x else 0
                placements.extend(_tile_row(
                    span=row_span, y_plate=y,
                    x0=x0, z0=z0, along_x=along_x, rotation=rot,
                    color=self.color,
                    comment=f"{prefix} {side} step_{step}",
                    fill=FILL_SLOPES,
                ))

        # Ridge cap: even step_span → the two innermost slopes overlap by 1 stud,
        # leaving a visible 2-stud flat top (1 top-stud from each side).
        # A row of double-slope pieces caps this into a true peak.
        # Odd step_span → slopes meet exactly at a point; no flat, no cap needed.
        if step_span % 2 == 0:
            y   = self.num_steps * PLATES_PER_BRICK
            # Center the 2-stud-deep cap over the flat: starts 1 stud before midpoint.
            mid = self.num_steps - 1   # == step_span // 2 - 1
            x0  = 0   if along_x else mid
            z0  = mid if along_x else 0
            # Rotation keeps the cap's long axis (4 studs) aligned with the ridge.
            rot = 0 if ew else 90
            placements.extend(_tile_row(
                span=row_span, y_plate=y,
                x0=x0, z0=z0, along_x=along_x, rotation=rot,
                color=self.color,
                comment=f"{prefix} ridge_cap",
                fill=FILL_RIDGE,
            ))

        return placements

    def _build_gables(self, prefix: str) -> list[BrickPlacement]:
        """Build triangular gable end walls at the non-ridge ends.

        Each step level shrinks the gable span by 2 studs (1 per side),
        matching the slope step inward, to form the triangular profile.

        EW ridge: gables at west (x=0) and east (x=width-2) ends, tiling along Z.
        NS ridge: gables at south (z=0) and north (z=depth-2) ends, tiling along X.
        """
        ew         = self.ridge == "east_west"
        step_span  = self.depth  if ew else self.width
        along_x    = not ew   # gables tile perpendicular to the ridge
        rotation   = 90 if ew else 0

        placements: list[BrickPlacement] = []
        for step in range(step_span // 2):
            y    = step * PLATES_PER_BRICK
            span = step_span - 2 * step
            if span <= 0:
                break
            sides = (
                [(0,                             step, "west_gable"),
                 (self.width - WALL_DEPTH_STUDS, step, "east_gable")]
                if ew else
                [(step, 0,                              "south_gable"),
                 (step, self.depth - WALL_DEPTH_STUDS,  "north_gable")]
            )
            for x0, z0, side in sides:
                placements.extend(_tile_row(
                    span=span, y_plate=y,
                    x0=x0, z0=z0, along_x=along_x, rotation=rotation,
                    color=self.color,
                    comment=f"{prefix} {side} step_{step}",
                ))
        return placements
