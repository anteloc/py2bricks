from __future__ import annotations

"""
Build plan — Cosy Country Cottage

1) Site
   - Wide green grass slab as the base for the entire scene.
   - A gravel path (tan) runs from the south edge to the front door.
   - A small flower-bed strip (bright green) lines the south face.

2) Main cottage body
   - Single-storey Box, warm tan/dark-tan walls, 8 bricks tall.
   - South face: centred front door + one window each side.
   - North face: two windows.
   - East & West faces: one window each.
   - Stone-effect ledge trim at wall top (light-grey plate).

3) Porch
   - Small shallow Box attached to the south face, centred.
   - Flat FloorSlab canopy above porch sitting on two corner columns.

4) Gable roof
   - GableRoof (ridge east-west) placed on the cottage body, dark-red.
   - Overhangs both north and south naturally via GableRoof geometry.

5) Chimney
   - Narrow Column stack placed at the roof level, slightly off-centre.

6) Rear garden shed
   - Tiny Box attached to the north face, same wall colour.
   - Lean-to-style flat slab as a simple roof.

Connections
   - porch attached to main body south face.
   - shed  attached to main body north face.
   - roof  placed on top of main body (with porch+shed group).
   - chimney placed on top of roof.
   - whole assembly placed on site slab.
"""

from py2bricks import (
    Scene,
    Group,
    Box,
    FloorSlab,
    Column,
    GableRoof,
    PartType,
    Color,
    attach,
    place,
)

# ── Dimensions ────────────────────────────────────────────────────────────────
SITE_W = 48
SITE_D = 44

COTTAGE_W = 24       # east-west studs
COTTAGE_D = 18       # north-south studs
COTTAGE_H = 8        # brick rows

PORCH_W = 8
PORCH_D = 3
PORCH_H = 4          # column height bricks (supports canopy)

SHED_W = 10
SHED_D = 6
SHED_H = 4

PATH_W = 6
PATH_D = 8           # from south site edge to porch

FLOWERBED_W = COTTAGE_W
FLOWERBED_D = 2

# ── Palette ───────────────────────────────────────────────────────────────────
GRASS       = Color.BRIGHT_GREEN
GRAVEL      = Color.TAN
STONE       = Color.LIGHT_BLUISH_GREY
WALL        = Color.DARK_TAN
TRIM        = Color.TAN
ROOF_COL    = Color.DARK_RED
CHIMNEY_COL = Color.DARK_BLUISH_GREY
GLASS       = Color.TRANS_LIGHT_BLUE
DOOR_COL    = Color.DARK_GREEN
SHED_COL    = Color.DARK_TAN
FLOWER      = Color.BRIGHT_GREEN
POST_COL    = Color.REDDISH_BROWN
PORCH_ROOF  = Color.DARK_RED


# ── Helpers ───────────────────────────────────────────────────────────────────
def win(wall, x, y, w, h, part, color=None):
    """Cut + insert a window/door shorthand."""
    wall.opening(x=x, y=y, width=w, height=h)
    wall.insert(part, x=x, y=y, color=color or GLASS)


# ── Site ──────────────────────────────────────────────────────────────────────
def make_site() -> Group:
    site = Group("site")

    # Grass base
    site.add(
        FloorSlab(SITE_W, SITE_D, color=GRASS, fill_part=PartType.PLATE_2X4, name="grass"),
        x=0, y=0, z=0,
    )
    # Gravel path (south approach)
    site.add(
        FloorSlab(PATH_W, PATH_D, color=GRAVEL, fill_part=PartType.PLATE_2X4, name="path"),
        x=(SITE_W - PATH_W) // 2, y=1, z=2,
    )
    # Flower bed strip just in front of the cottage south face
    site.add(
        FloorSlab(FLOWERBED_W, FLOWERBED_D, color=FLOWER, fill_part=PartType.PLATE_2X4, name="flowerbed"),
        x=(SITE_W - FLOWERBED_W) // 2, y=1, z=PATH_D + 2,
    )
    return site


# ── Porch ─────────────────────────────────────────────────────────────────────
def make_porch() -> Group:
    porch = Group("porch")

    # Canopy slab
    canopy = FloorSlab(PORCH_W, PORCH_D, color=PORCH_ROOF, fill_part=PartType.PLATE_2X4, name="canopy")
    porch.add(canopy, x=0, y=PORCH_H * 3, z=0)    # top of columns (3 plates/brick)

    # Two timber corner columns
    for name, cx in (("post_w", 0), ("post_e", PORCH_W - 1)):
        porch.add(
            Column(height=PORCH_H, color=POST_COL, part_type=PartType.BRICK_1X1, name=name),
            x=cx, y=0, z=0,
        )
    return porch


# ── Garden shed ───────────────────────────────────────────────────────────────
def make_shed() -> Group:
    shed = Group("shed")
    body = Box(SHED_W, SHED_D, SHED_H, color=SHED_COL, name="shed_body")

    # One small window on the north face
    win(body.north, x=3, y=2, w=2, h=2, part=PartType.WINDOW_1X2X2)
    # Simple door on south (interior-facing) face left open as an opening only
    body.south.opening(x=3, y=0, width=4, height=SHED_H)

    # Flat lean-to roof = just a floor slab
    lean_roof = FloorSlab(SHED_W, SHED_D, color=ROOF_COL, fill_part=PartType.PLATE_2X4, name="shed_roof")
    shed.add(body, x=0, y=0, z=0)
    shed.add(lean_roof, x=0, y=body.height_plates, z=0)
    return shed


# ── Main cottage body ─────────────────────────────────────────────────────────
def make_cottage_body() -> Box:
    body = Box(COTTAGE_W, COTTAGE_D, COTTAGE_H, color=WALL,
               fill_part=PartType.BRICK_2X4, name="cottage_body")

    # South face — centred door + one window each side
    win(body.south, x=10, y=0, w=4, h=6, part=PartType.DOOR_1X4X6, color=DOOR_COL)
    win(body.south, x=2,  y=2, w=4, h=3, part=PartType.WINDOW_1X4X3)
    win(body.south, x=18, y=2, w=4, h=3, part=PartType.WINDOW_1X4X3)

    # North face — two windows
    win(body.north, x=4,  y=2, w=4, h=3, part=PartType.WINDOW_1X4X3)
    win(body.north, x=16, y=2, w=4, h=3, part=PartType.WINDOW_1X4X3)

    # East & West — one window each
    win(body.east, x=7,  y=2, w=4, h=3, part=PartType.WINDOW_1X4X3)
    win(body.west, x=7,  y=2, w=4, h=3, part=PartType.WINDOW_1X4X3)

    # Stone-effect trim ledge at top of all walls
    for wall in body.walls():
        wall.ledge(y=COTTAGE_H - 1, overhang=1, color=STONE, part_type=PartType.PLATE_2X4)

    return body


# ── Chimney ───────────────────────────────────────────────────────────────────
def make_chimney(roof: GableRoof) -> Column:
    return Column(height=5, color=CHIMNEY_COL, part_type=PartType.BRICK_1X1, name="chimney")


# ── Scene assembly ────────────────────────────────────────────────────────────
def main() -> None:
    scene = Scene("country_cottage")

    # Site
    site = make_site()

    # Cottage body + roof — place roof on body FIRST, before attaching
    # porch/shed, so the roof centers on the 24×18 body footprint exactly.
    body = make_cottage_body()

    roof = GableRoof(COTTAGE_W, COTTAGE_D, ridge="east_west",
                     color=ROOF_COL, name="cottage_roof")
    cottage_roofed = place(roof, on=body, align="center")

    # Now attach porch and shed to the roofed assembly (Group).
    # attach() uses the body's original width/depth for alignment because
    # the Group's bounding box hasn't been inflated by porch/shed yet.
    porch = make_porch()
    cottage_roofed = attach(porch, to=cottage_roofed, face="south", align="center")

    shed = make_shed()
    full_cottage = attach(shed, to=cottage_roofed, face="north", align="flush_east", offset=(-2, 0))

    # Chimney — sits near the east end of the ridge
    chimney = make_chimney(roof)
    chimney_x_offset = 6     # studs east of centre
    place(chimney, on=full_cottage, align="center", offset=(chimney_x_offset, 0))

    # Place entire building on site, centred, slightly north of centre
    place(full_cottage, on=site, align="center", offset=(0, -3))

    scene.add(site)

    out_path = __file__.replace(".py", ".mpd")
    scene.export(out_path)
    print(f"Exported → {out_path}")
    print(scene.stats())


if __name__ == "__main__":
    main()
