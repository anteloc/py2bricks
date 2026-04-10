"""
Scene: top-level container and LDraw exporter.

The Scene is the top-level container. It holds all elements and groups, 
and exports the final LDraw .mpd file.

Usage:
  scene = Scene("building")
  tower = Box(
            width=8,
            depth=6,
            height=4,
            color=TOWER_COLOR,
            fill_part=PartType.BRICK_2X4,
            name="tower",
        ),
        x=10,
        y=1,
        z=7,
    )
  scene.add(tower)
  ...
  scene.export("tower_building.mpd")

"""

from __future__ import annotations

import os
from typing import Literal

from .parts import PartType, Color
from .core import BrickPlacement
from .wall import Wall, Box, WallLayout
from .floor import FloorSlab
from .stairs import StaircaseShaft
from .roof import GableRoof
from .structures import Column
from .assembly import Group

class Scene:
    """Top-level container and LDraw exporter.

    Handles final coordinate resolution and LDraw output.

    Internally, all top-level elements are held in an anonymous root Group
    so placement collection reuses Group.to_placements() with no duplication.

    Attributes:
        name: Model name (used in LDraw file header).
    """

    def __init__(self, name: str = "model"):
        """Create a scene.

        Args:
            name: Model name for LDraw file header.
        """
        self.name = name
        # Root group with empty name so it adds no prefix to LDraw comments.
        self._root = Group(name="")

    def add(self, element, x: float = 0, y: float = 0, z: float = 0):
        """Add an existing element to the scene at a specific position."""
        self._root.add(element, x=x, y=y, z=z)

    # --- Export ---

    def _collect_all_placements(self) -> list[BrickPlacement]:
        """Collect all BrickPlacements in global coordinates.

        Delegates to the root Group, which recursively resolves all children.
        """
        return self._root.to_placements()

    def export(self, filename: str) -> str:
        """Export the scene as an LDraw .mpd file.

        Collects all placements, converts to LDraw coordinates, and
        writes to file. Returns the file path.

        The output file structure:
          0 FILE <n>.ldr
          0 <n>
          0 Name: <n>.ldr
          0 Author: py2bricks
          0 // <comment>
          1 <color> <x> <y> <z> <matrix> <part>
          ...
          0 NOFILE

        Args:
            filename: Output file path (e.g. "building.mpd").

        Returns:
            The filename (for convenience).
        """
        placements = self._collect_all_placements()

        lines = []
        # MPD file header
        model_name = self.name.replace(" ", "_")
        lines.append(f"0 FILE {model_name}.ldr")
        lines.append(f"0 {self.name}")
        lines.append(f"0 Name: {model_name}.ldr")
        lines.append(f"0 Author: py2bricks")
        lines.append(f"0 !LDRAW_ORG Unofficial_Model")
        lines.append("")

        # Sort placements by Y (bottom to top) for readable output
        placements.sort(key=lambda p: (p.y, p.z, p.x))

        # Write each placement as LDraw type-1 line with comment
        current_y = None
        for p in placements:
            # Add a blank line between different Y levels for readability
            if current_y is not None and p.y != current_y:
                lines.append("")
            current_y = p.y

            lines.append(p.to_ldraw_line())

        lines.append("")
        lines.append("0 NOFILE")
        lines.append("")

        # Write to file
        content = "\n".join(lines)
        with open(filename, "w") as f:
            f.write(content)

        print(f"Model created: {filename}")

        return filename

    def help(self) -> str:
        """Print the py2bricks quick reference and return it as a string.

        Reads QUICK_REFERENCE.md from the project root (two directories above
        this file: src/py2bricks/ → src/ → project root).

        Returns:
            The quick reference text (also printed to stdout).
        """
        ref_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "QUICK_REFERENCE.md"
        )
        ref_path = os.path.normpath(ref_path)
        try:
            with open(ref_path) as f:
                text = f.read()
        except FileNotFoundError:
            text = (
                "QUICK_REFERENCE.md not found. "
                f"Expected at: {ref_path}\n"
                "See CLAUDE.md or the project README for API documentation."
            )
        print(text)
        return text

    def stats(self) -> dict:
        """Return model statistics: part count, unique parts, dimensions.

        Useful for the LLM to verify the model looks reasonable.

        Returns:
            Dict with keys: total_parts, unique_parts, width, depth, height,
            part_counts (dict of part description -> count).
        """
        placements = self._collect_all_placements()

        part_counts: dict[str, int] = {}
        for p in placements:
            desc = p.part.description
            part_counts[desc] = part_counts.get(desc, 0) + 1

        xs = [p.x for p in placements] if placements else [0]
        ys = [p.y for p in placements] if placements else [0]
        zs = [p.z for p in placements] if placements else [0]

        return {
            "total_parts": len(placements),
            "unique_parts": len(part_counts),
            "width_studs": max(xs) - min(xs) + 4,  # approximate
            "depth_studs": max(zs) - min(zs) + 2,
            "height_plates": max(ys) + 3,
            "part_counts": part_counts,
        }
