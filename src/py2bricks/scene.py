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

from .core import BrickPlacement
from .assembly import Group
from .coords import to_ldraw_coords


def _section_key(comment: str) -> str:
    """Strip trailing 'word_N' suffix from a brick comment.

    Turns 'building_body > north_wall row_3' into 'building_body > north_wall',
    'roof_name south step_3' into 'roof_name south', etc.
    Comments with no such suffix (e.g. 'floor_slab') are returned unchanged.
    """
    parts = comment.rsplit(" ", 1)
    if len(parts) == 2 and "_" in parts[1] and parts[1].split("_")[-1].isdigit():
        return parts[0]
    return comment


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
    
    def _bottom_up_export(self, placements: list[BrickPlacement]) -> list[str]:
        """Export the scene in bottom-up order (parts before groups).

        This is a simpler export method that writes parts as they are encountered
        in the hierarchy. It may be easier for debugging but results in less
        organized LDraw files.

        Returns:
            List of LDraw lines (for testing).
        """

        lines = []

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

        return lines
    
    def _render_leaf(self, elem, x_off: float, y_off: float, z_off: float) -> list[str]:
        """Render a leaf (non-Group) element as annotated LDraw lines.

        Emits:
          0 // <elem_name>                   once, at the start of the element
          0 // <elem_name>, <sub_section>    at each section change within the element
          1 <color> ...                      each brick line

        Section boundaries are detected by watching the brick comment's section key
        (trailing 'row_N' / 'step_N' suffix stripped). Sections equal to the element
        name itself (e.g. a plain FloorSlab) are not repeated.
        """
        lines: list[str] = []
        elem_name: str = getattr(elem, "name", "")
        if elem_name:
            lines.append(f"0 // {elem_name}")

        current_section: str | None = None
        for p in elem.to_placements():
            section = _section_key(p.comment)
            if section != current_section:
                current_section = section
                if section != elem_name:
                    lines.append(f"0 // {section.replace(' > ', ', ')}")
            lines.append(p.offset_by(x_off, y_off, z_off).to_ldraw_line())

        return lines

    def _group_to_file_lines(self, group: Group, seen: set[int]) -> list[str]:
        """Emit a FILE section for a named group, recursing into named sub-groups.

        For each child:
        - Named Group  → a type-1 reference line at local coords + FILE section (once per object)
        - Leaf element → part lines inlined at local coords

        `seen` tracks Python object ids of groups already emitted, so that groups
        reused by stack() (same object, multiple offsets) produce one FILE definition
        and multiple reference lines — which is correct LDraw MPD behavior.

        Returns the FILE header + body + NOFILE, followed by all new descendant FILE sections.
        """
        IDENTITY = "1 0 0 0 1 0 0 0 1"
        body: list[str] = []
        sub_lines: list[str] = []

        for elem, x_off, y_off, z_off in group.children:
            if isinstance(elem, Group) and elem.name:
                sn = elem.name.replace(" ", "_")
                lx, ly, lz = to_ldraw_coords(x_off, y_off, z_off)
                body.append(f"1 16 {lx:.1f} {ly:.1f} {lz:.1f} {IDENTITY} {sn}.ldr")
                if id(elem) not in seen:
                    seen.add(id(elem))
                    sub_lines += self._group_to_file_lines(elem, seen)
            else:
                body.extend(self._render_leaf(elem, x_off, y_off, z_off))

        sn = group.name.replace(" ", "_")
        header = [f"0 FILE {sn}.ldr", f"0 {group.name}", f"0 Name: {sn}.ldr", "0 Author: py2bricks", ""]
        return header + body + ["", "0 NOFILE"] + sub_lines

    def _semantic_export(self) -> list[str]:
        """Export the scene as a multi-FILE MPD with one FILE per named Group.

        Walks the element hierarchy recursively via _group_to_file_lines.
        The main FILE (header added by export()) references top-level named Groups
        and inlines any leaf children directly.

        Output structure (the main FILE header is added by export()):

            1 16 ox oy oz 1 0 0 0 1 0 0 0 1 <sn>.ldr   <- top-level group reference
            ...                                          <- inline parts for leaf children

            0 NOFILE                                     <- closes main FILE
            0 FILE <sn>.ldr                              <- one FILE per named Group
            ...                                          <- recursive structure
            0 NOFILE
            ...

        The final 0 NOFILE is added by export() to close the last FILE section.

        Returns:
            List of LDraw lines (for testing).
        """
        IDENTITY = "1 0 0 0 1 0 0 0 1"
        main_lines: list[str] = []
        sub_lines: list[str] = []
        seen: set[int] = set()

        for elem, x_off, y_off, z_off in self._root.children:
            if isinstance(elem, Group) and elem.name:
                sn = elem.name.replace(" ", "_")
                lx, ly, lz = to_ldraw_coords(x_off, y_off, z_off)
                main_lines.append(f"1 16 {lx:.1f} {ly:.1f} {lz:.1f} {IDENTITY} {sn}.ldr")
                if id(elem) not in seen:
                    seen.add(id(elem))
                    sub_lines += self._group_to_file_lines(elem, seen)
            else:
                main_lines.extend(self._render_leaf(elem, x_off, y_off, z_off))

        # Close main FILE, then all subfile sections depth-first.
        # export() adds the final blank + 0 NOFILE which closes the last subfile.
        return main_lines + ["", "0 NOFILE"] + sub_lines

    def export(self, filename: str, export_type: Literal["bottom-up", "semantic"] = "semantic") -> str:
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
        lines = []
        # MPD file header
        model_name = self.name.replace(" ", "_")
        lines.append(f"0 FILE {model_name}.ldr")
        lines.append(f"0 {self.name}")
        lines.append(f"0 Name: {model_name}.ldr")
        lines.append("0 Author: py2bricks")
        lines.append("0 !LDRAW_ORG Unofficial_Model")
        lines.append("")

        if export_type == "bottom-up":
            placements = self._collect_all_placements()
            lines.extend(self._bottom_up_export(placements))
            lines.append("")
            lines.append("0 NOFILE")
            lines.append("")
        elif export_type == "semantic":
            lines.extend(self._semantic_export())
            lines.append("")

        # Write to file
        content = "\n".join(lines)
        with open(filename, "w") as f:
            f.write(content)

        print(f"Model created: {filename}")

        return filename

    def help(self) -> str:
        """Print the py2bricks quick reference and return it as a string.

        Reads QUICK_REFERENCE.md from the project root (same directory as this file: src/py2bricks/).

        Returns:
            The quick reference text (also printed to stdout).
        """
        ref_path = os.path.join(
            os.path.dirname(__file__), "QUICK_REFERENCE.md"
        )
        ref_path = os.path.normpath(ref_path)
        try:
            with open(ref_path) as f:
                text = f.read()
        except FileNotFoundError:
            text = (
                "QUICK_REFERENCE.md not found. "
                f"Expected at: {ref_path}\n"
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
