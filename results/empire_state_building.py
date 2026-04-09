from py2bricks import (
    Scene, Group, Box, FloorSlab, WallLayout, Column, PartType, Color, place
)

# === COLORS ===
LIMESTONE  = Color.LIGHT_BLUISH_GREY   # exterior cladding
GRANITE    = Color.DARK_BLUISH_GREY    # base / darker stone
GLASS      = Color.TRANS_LIGHT_BLUE
CHROME     = Color.LIGHT_GREY
FLOOR_C    = Color.LIGHT_GREY
SPIRE_C    = Color.WHITE
TRIM       = Color.LIGHT_BLUISH_GREY

# === PLAN DIMENSIONS (studs) ===
# Each setback tier shrinks the footprint
B0_W, B0_D = 48, 40   # ground base block
B1_W, B1_D = 36, 30   # setback 1 (floors 7-25)
B2_W, B2_D = 26, 20   # setback 2 (floors 26-72)
B3_W, B3_D = 18, 14   # setback 3 (floors 73-86)
CR_W, CR_D = 12, 10   # crown pyramid base
SP_W, SP_D =  6,  6   # spire base

# === FLOOR HEIGHTS (bricks) ===
FLOOR_H = 5   # standard floor height

# Number of floors per tier
BASE_FLOORS  = 6
T1_FLOORS    = 19
T2_FLOORS    = 18
T3_FLOORS    = 14
CROWN_STEPS  = 5   # stepped pyramid setbacks in the crown


def floor_slab(w, d, color=FLOOR_C):
    return FloorSlab(w, d, color=color, fill_part=PartType.PLATE_2X4, name="slab")


def add_windows_ns(box, w, count_ns, count_ew):
    """Add window rows to all 4 walls, scaled to wall width."""
    box.north.window_row(y=1, width=4, height=3, count=count_ns,
                         part_type=PartType.WINDOW_1X4X3, spacing="even", color=GLASS)
    box.south.window_row(y=1, width=4, height=3, count=count_ns,
                         part_type=PartType.WINDOW_1X4X3, spacing="even", color=GLASS)
    box.east.window_row(y=1, width=4, height=3, count=count_ew,
                        part_type=PartType.WINDOW_1X4X3, spacing="even", color=GLASS)
    box.west.window_row(y=1, width=4, height=3, count=count_ew,
                        part_type=PartType.WINDOW_1X4X3, spacing="even", color=GLASS)


def make_ledge(box, color=LIMESTONE):
    for wall in box.walls():
        wall.ledge(y=FLOOR_H - 1, overhang=1, color=color, part_type=PartType.PLATE_2X4)


def make_floor_stack(w, d, num_floors, win_ns, win_ew, label, color=LIMESTONE):
    g = Group(label)
    y = 0
    for i in range(num_floors):
        f = Group(f"{label}_f{i}")
        f.add(floor_slab(w, d), x=0, y=0, z=0)
        shell = Box(w, d, FLOOR_H, color=color, fill_part=PartType.BRICK_2X4, name="shell")
        add_windows_ns(shell, w, win_ns, win_ew)
        make_ledge(shell, color=TRIM)
        f.add(shell, x=0, y=1, z=0)
        g.add(f, x=0, y=y, z=0)
        y += 1 + FLOOR_H * 3
    return g


def make_base_block():
    """Ground-level base — 6 floors, wide footprint, large lobby arches."""
    g = Group("base_block")
    g.add(floor_slab(B0_W, B0_D, color=GRANITE), x=0, y=0, z=0)

    for i in range(BASE_FLOORS):
        f = Group(f"base_f{i}")
        f.add(floor_slab(B0_W, B0_D), x=0, y=0, z=0)
        shell = Box(B0_W, B0_D, FLOOR_H, color=GRANITE if i == 0 else LIMESTONE,
                    fill_part=PartType.BRICK_2X4, name="shell")

        if i == 0:
            # Ground floor: large lobby entries + display windows
            for face, wall in [("south", shell.south), ("north", shell.north)]:
                wall.opening(x=4, y=0, width=4, height=5)
                wall.insert(PartType.DOOR_1X4X6, x=4, y=0, color=GRANITE)
                wall.opening(x=20, y=0, width=4, height=5)
                wall.insert(PartType.DOOR_1X4X6, x=20, y=0, color=GRANITE)
                wall.opening(x=36, y=0, width=4, height=5)
                wall.insert(PartType.DOOR_1X4X6, x=36, y=0, color=GRANITE)
            for face, wall in [("east", shell.east), ("west", shell.west)]:
                wall.opening(x=4, y=0, width=4, height=5)
                wall.insert(PartType.DOOR_1X4X6, x=4, y=0, color=GRANITE)
                wall.opening(x=26, y=0, width=4, height=5)
                wall.insert(PartType.DOOR_1X4X6, x=26, y=0, color=GRANITE)
        else:
            add_windows_ns(shell, B0_W, 6, 5)

        make_ledge(shell)
        f.add(shell, x=0, y=1, z=0)
        g.add(f, x=0, y=i * (1 + FLOOR_H * 3), z=0)

    return g


def make_crown():
    """Art Deco stepped pyramid crown — 5 setback steps."""
    g = Group("crown")

    # Step dimensions shrink each level
    steps = [
        (CR_W,     CR_D,     4, LIMESTONE),
        (CR_W - 2, CR_D - 2, 3, LIMESTONE),
        (CR_W - 4, CR_D - 4, 3, CHROME),
        (CR_W - 6, CR_D - 6, 2, CHROME),
        (CR_W - 8, CR_D - 8, 2, SPIRE_C),
    ]

    y = 0
    for i, (w, d, h, color) in enumerate(steps):
        step_g = Group(f"crown_step_{i}")
        step_g.add(floor_slab(w, d, color=color), x=0, y=0, z=0)
        shell = Box(w, d, h, color=color, fill_part=PartType.BRICK_2X4, name=f"step_{i}")
        for wall in shell.walls():
            wall.ledge(y=h-1, overhang=1, color=CHROME, part_type=PartType.PLATE_2X4)
        step_g.add(shell, x=0, y=1, z=0)

        # Center each step
        offset_x = i
        offset_z = i
        g.add(step_g, x=offset_x, y=y, z=offset_z)
        y += 1 + h * 3

    # Mooring mast / antenna — tall central column
    mast_y = y
    for height, color, width in [
        (12, CHROME, 2),
        (10, CHROME, 1),
        (18, SPIRE_C, 1),
    ]:
        cx = CR_W // 2
        cz = CR_D // 2
        g.add(Column(height, color=color, part_type=PartType.BRICK_1X1, name=f"mast_{height}"),
              x=cx, y=mast_y, z=cz)
        mast_y += height * 3

    return g


# ─────────────────────────────────────────────
# ASSEMBLE
# ─────────────────────────────────────────────
scene = Scene("Empire State Building")

# City block site pad
scene.add(FloorSlab(B0_W + 16, B0_D + 16, color=Color.DARK_GREY,
                    fill_part=PartType.PLATE_2X4, name="street"),
          x=-8, y=0, z=-8)
scene.add(FloorSlab(B0_W + 8, B0_D + 8, color=Color.LIGHT_GREY,
                    fill_part=PartType.PLATE_2X4, name="sidewalk"),
          x=-4, y=1, z=-4)

# Base block (floors 1-6)
base = make_base_block()
scene.add(base, x=0, y=2, z=0)

# Tier 1 (floors 7-25): first setback
tier1 = make_floor_stack(B1_W, B1_D, T1_FLOORS, win_ns=5, win_ew=4, label="tier1")
place(tier1, on=base, align="center")

# Tier 2 (floors 26-72): second setback
tier2 = make_floor_stack(B2_W, B2_D, T2_FLOORS, win_ns=4, win_ew=3, label="tier2")
place(tier2, on=tier1, align="center")

# Tier 3 (floors 73-86): third setback — slim shaft
tier3 = make_floor_stack(B3_W, B3_D, T3_FLOORS, win_ns=2, win_ew=2, label="tier3")
place(tier3, on=tier2, align="center")

# Crown — Art Deco stepped pyramid
crown = make_crown()
place(crown, on=tier3, align="center")

out_path = __file__.replace(".py", ".mpd")
scene.export(out_path)
print(scene.stats())
