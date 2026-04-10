"""
Structural elements: Column.

Box: 4-wall rectangular enclosure.
FloorSlab: horizontal plate surface.
Column: vertical stack of identical bricks.
"""

from __future__ import annotations

from .coords import PLATES_PER_BRICK
from .parts import PartType, Part, find_part, Color
from .core import  BrickPlacement



def _tile_area_greedy(
    region_w: int,
    region_d: int,
    x0: int,
    z0: int,
    y: int,
    parts: list[Part],
    color: int,
    comment: str,
) -> list[BrickPlacement]:
    """Greedily tile a (region_w × region_d) stud area at height y.

    Iterates z then x, placing the largest fitting part at each unfilled
    cell. All parts are placed at rotation=0 (lying flat).

    Args:
        region_w, region_d: Area dimensions in studs.
        x0, z0: Absolute origin of the area in the caller's coordinate space.
        y: Y position in plates.
        parts: Candidate parts in preference order (largest/widest first).
        color: LDraw color code.
        comment: LDraw comment string for all placements in this area.
    """
    placements: list[BrickPlacement] = []
    filled = [[False] * region_d for _ in range(region_w)]

    for z in range(region_d):
        for x in range(region_w):
            if filled[x][z]:
                continue
            for part in parts:
                pw, pd = part.width_studs, part.depth_studs
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
                    part=part, x=x0 + x, y=y, z=z0 + z,
                    rotation=0, color=color, comment=comment,
                ))
                break  # placed — move to next unfilled cell

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
        prefix = f"{comment_prefix}{self.name}"
        return [
            BrickPlacement(
                part=self.part,
                x=0, y=row * PLATES_PER_BRICK, z=0,
                rotation=0, color=self.color,
                comment=f"{prefix} row_{row}",
            )
            for row in range(self.height_bricks)
        ]


