"""
FloorSlab: horizontal plate surface.
"""

from __future__ import annotations

from .parts import PartType, FILL_PLATES, Color
from .core import BrickPlacement
from .structures import _tile_area_greedy

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
        """Tile the floor area with plates using a greedy 2D fill (largest first).

        Returns:
            List of BrickPlacement in floor-local coordinates.
        """
        return _tile_area_greedy(
            self.width, self.depth, 0, 0, 0,
            FILL_PLATES, self.color,
            f"{comment_prefix}{self.name}",
        )