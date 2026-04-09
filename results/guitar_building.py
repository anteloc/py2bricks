from __future__ import annotations

"""
Build plan — guitar-shaped landmark building

1) Site / plaza
   - Create one paved city-plaza slab as the global base.
   - Place the guitar building slightly back from the south edge so the front elevation reads clearly.

2) Guitar body
   - Build a tall central body block as the structural core.
   - Add two larger lower lobes at ground level, one west and one east.
   - Add two smaller upper shoulder blocks higher up on the sides so the facade pinches inward at the waist.
   - Add a dark sound-hole / stage band on the front of the body plus six thin vertical string lines.

3) Entry / bridge
   - Add a small glazed lobby projecting from the front of the body.
   - Cap it with a shallow canopy so the entrance feels like a public building instead of a pure sculpture.

4) Neck and headstock
   - Stack a narrow neck tower directly on top of the body, centered.
   - Stack a slightly wider headstock block on top of the neck.
   - Add side pegs to the headstock to suggest tuning machines.

5) Connection logic
   - plaza is the global base.
   - all body pieces sit directly on the plaza and overlap into one mass.
   - the lobby projects from the south face of the body.
   - the neck stacks on the body core.
   - the headstock stacks on the neck.
   - string columns run in front of the south facade from the upper body to the headstock.
"""

from py2bricks import Scene, Group, Box, FloorSlab, Column, PartType, Color


# --- Site -------------------------------------------------------------------
SITE_W = 72
SITE_D = 52
BUILDING_X = 16
BUILDING_Z = 12

# --- Guitar body proportions -------------------------------------------------
LOWER_LOBE_W = 10
CORE_W = 20
LOWER_LOBE_H = 9
CORE_H = 18
UPPER_LOBE_W = 8
UPPER_LOBE_H = 6
UPPER_LOBE_Y = 8 * 3  # 8 bricks up, in plates
BODY_D = 18
BODY_TOTAL_W = LOWER_LOBE_W + CORE_W + LOWER_LOBE_W

# --- Neck / headstock --------------------------------------------------------
NECK_W = 8
NECK_D = 12
NECK_H = 16
HEAD_W = 12
HEAD_D = 12
HEAD_H = 5

# --- Entry ------------------------------------------------------------------
ENTRY_W = 10
ENTRY_D = 6
ENTRY_H = 6

# --- Colors -----------------------------------------------------------------
PLAZA = Color.DARK_BLUISH_GREY
PAVING = Color.LIGHT_BLUISH_GREY
BODY = Color.WHITE
TRIM = Color.LIGHT_GREY
GLASS = Color.TRANS_LIGHT_BLUE
ENTRY = Color.DARK_BLUE
CANOPY = Color.DARK_RED
DETAIL = Color.BLACK
STRINGS = Color.LIGHT_GREY
PEG = Color.LIGHT_GREY


def add_window(wall, x: int, y: int, width: int, height: int, part_type: PartType, color: int = GLASS) -> None:
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part_type, x=x, y=y, color=color)


def add_window_series(wall, xs: tuple[int, ...], y: int, width: int, height: int, part_type: PartType) -> None:
    for x in xs:
        add_window(wall, x=x, y=y, width=width, height=height, part_type=part_type)


def dress_core(shell: Box) -> None:
    add_window_series(shell.south, (2, 6, 12, 16), y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.south, (2, 6, 12, 16), y=8, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.south, (2, 6, 12, 16), y=14, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_window_series(shell.north, (2, 6, 12, 16), y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, (2, 6, 12, 16), y=8, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, (2, 6, 12, 16), y=14, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_window(shell.east, x=4, y=6, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.east, x=10, y=12, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.west, x=4, y=6, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.west, x=10, y=12, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    for wall in shell.walls():
        wall.ledge(y=CORE_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)
        wall.ledge(y=6, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)
        wall.ledge(y=12, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)


def dress_lobe(shell: Box) -> None:
    add_window_series(shell.south, (2, 6), y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.south, (2, 6), y=6, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, (2, 6), y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, (2, 6), y=6, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=7, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=7, y=3, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=LOWER_LOBE_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)


def dress_shoulder(shell: Box) -> None:
    add_window(shell.south, x=2, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=2, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.east, x=7, y=1, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=7, y=1, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=UPPER_LOBE_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)


def dress_neck(shell: Box) -> None:
    add_window_series(shell.south, (3,), y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.south, (3,), y=8, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.south, (3,), y=13, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_window_series(shell.north, (3,), y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, (3,), y=8, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window_series(shell.north, (3,), y=13, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_window(shell.east, x=4, y=6, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.west, x=4, y=6, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    for wall in shell.walls():
        wall.ledge(y=NECK_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)
        wall.ledge(y=6, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)
        wall.ledge(y=12, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)


def dress_head(shell: Box) -> None:
    add_window(shell.south, x=1, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.south, x=7, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=1, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=7, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    for wall in shell.walls():
        wall.ledge(y=HEAD_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)


def make_guitar_body() -> Group:
    body = Group("guitar_body")

    core = Box(CORE_W, BODY_D, CORE_H, color=BODY, name="body_core")
    dress_core(core)
    body.add(core, x=LOWER_LOBE_W, y=0, z=0)

    lower_w = Box(LOWER_LOBE_W, BODY_D, LOWER_LOBE_H, color=BODY, name="lower_lobe_w")
    dress_lobe(lower_w)
    body.add(lower_w, x=0, y=0, z=0)

    lower_e = Box(LOWER_LOBE_W, BODY_D, LOWER_LOBE_H, color=BODY, name="lower_lobe_e")
    dress_lobe(lower_e)
    body.add(lower_e, x=LOWER_LOBE_W + CORE_W, y=0, z=0)

    shoulder_w = Box(UPPER_LOBE_W, BODY_D, UPPER_LOBE_H, color=BODY, name="upper_shoulder_w")
    dress_shoulder(shoulder_w)
    body.add(shoulder_w, x=2, y=UPPER_LOBE_Y, z=0)

    shoulder_e = Box(UPPER_LOBE_W, BODY_D, UPPER_LOBE_H, color=BODY, name="upper_shoulder_e")
    dress_shoulder(shoulder_e)
    body.add(shoulder_e, x=BODY_TOTAL_W - UPPER_LOBE_W - 2, y=UPPER_LOBE_Y, z=0)

    # Dark "sound-hole / stage" band on the front.
    body.add(Box(8, 2, 3, color=DETAIL, name="soundhole_band"), x=16, y=8 * 3, z=-1)
    body.add(FloorSlab(12, 3, color=DETAIL, fill_part=PartType.PLATE_2X4, name="soundhole_balcony"), x=14, y=(8 * 3) + 9, z=-3)

    return body


def make_neck_and_head() -> Group:
    neck_group = Group("neck_and_head")

    neck = Box(NECK_W, NECK_D, NECK_H, color=BODY, name="neck")
    dress_neck(neck)
    neck_group.add(neck, x=(BODY_TOTAL_W - NECK_W) // 2, y=0, z=3)

    head_y = neck.height_plates
    head_x = (BODY_TOTAL_W - HEAD_W) // 2
    head_z = 3

    head = Box(HEAD_W, HEAD_D, HEAD_H, color=BODY, name="headstock")
    dress_head(head)
    neck_group.add(head, x=head_x, y=head_y, z=head_z)

    # Tuning pegs.
    peg_y_offsets = (1, 6, 11)
    for idx, peg_y in enumerate(peg_y_offsets, start=1):
        neck_group.add(Box(2, 2, 1, color=PEG, name=f"peg_w_{idx}"), x=head_x - 2, y=head_y + peg_y, z=head_z + 2)
        neck_group.add(Box(2, 2, 1, color=PEG, name=f"peg_e_{idx}"), x=head_x + HEAD_W, y=head_y + peg_y, z=head_z + 8)

    # Cap strip on the top edge.
    neck_group.add(FloorSlab(HEAD_W, HEAD_D, color=TRIM, fill_part=PartType.PLATE_2X4, name="head_cap"), x=head_x, y=head_y + head.height_plates, z=head_z)
    return neck_group


def make_entry() -> Group:
    entry = Group("entry")
    shell = Box(ENTRY_W, ENTRY_D, ENTRY_H, color=ENTRY, name="entry_shell")

    shell.south.opening(x=3, y=0, width=4, height=6)
    shell.south.insert(PartType.DOOR_1X4X6, x=3, y=0, color=DETAIL)
    add_window(shell.south, x=0, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.south, x=8, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=1, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.west, x=1, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    for wall in shell.walls():
        wall.ledge(y=ENTRY_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)

    entry.add(shell, x=0, y=0, z=0)
    entry.add(FloorSlab(ENTRY_W + 2, 3, color=CANOPY, fill_part=PartType.PLATE_2X4, name="entry_canopy"), x=-1, y=shell.height_plates + 1, z=-3)
    entry.add(Column(height=4, color=TRIM, part_type=PartType.BRICK_1X1, name="canopy_post_w"), x=0, y=0, z=-3)
    entry.add(Column(height=4, color=TRIM, part_type=PartType.BRICK_1X1, name="canopy_post_e"), x=ENTRY_W - 1, y=0, z=-3)
    return entry


def add_strings(building: Group, start_y: int, end_y_bricks: int) -> None:
    x_positions = (15, 18, 19, 20, 21, 24)
    for idx, x in enumerate(x_positions, start=1):
        building.add(
            Column(height=end_y_bricks, color=STRINGS, part_type=PartType.BRICK_1X1, name=f"string_{idx}"),
            x=x,
            y=start_y,
            z=-1,
        )


def main() -> None:
    scene = Scene("guitar_building")

    # Plaza with a lighter forecourt band.
    scene.add(FloorSlab(SITE_W, SITE_D, color=PLAZA, fill_part=PartType.PLATE_2X4, name="plaza"), x=0, y=0, z=0)
    scene.add(FloorSlab(SITE_W, 10, color=PAVING, fill_part=PartType.PLATE_2X4, name="forecourt"), x=0, y=1, z=0)

    guitar = Group("guitar_tower")
    body = make_guitar_body()
    guitar.add(body, x=0, y=1, z=0)

    neck_and_head = make_neck_and_head()
    guitar.add(neck_and_head, x=0, y=1 + (CORE_H * 3), z=0)

    entry = make_entry()
    guitar.add(entry, x=(BODY_TOTAL_W - ENTRY_W) // 2, y=1, z=-ENTRY_D)

    total_string_height = CORE_H + NECK_H + HEAD_H
    add_strings(guitar, start_y=(6 * 3), end_y_bricks=total_string_height - 6)

    scene.add(guitar, x=BUILDING_X, y=0, z=BUILDING_Z)

    out_path = __file__.replace(".py", ".mpd")

    output = scene.export(out_path)
    print(scene.stats())
    print(output)


if __name__ == "__main__":
    main()
