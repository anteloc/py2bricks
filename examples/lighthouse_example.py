from __future__ import annotations

"""
Build plan — compact coastal lighthouse

1) Site and setting
   - Create a rectangular ground slab for the whole scene.
   - Add a short rocky plinth near the back half of the site so the lighthouse reads as
     a building on a small headland instead of sitting flat on the ground.
   - Add a narrow path slab leading from the front edge of the site to the keeper's house door.

2) Lighthouse tower
   - Build a square masonry base with the main tower door and a few low windows.
   - Stack a taller, slightly narrower shaft on top of the base, centered, to create a simple taper.
   - Add small windows at staggered heights on each face so the tower feels climbable.
   - Place a gallery slab on top of the shaft, still centered on the base.

3) Lantern and crown
   - Place a glazed lantern room on the gallery slab, centered.
   - Add four corner posts on the gallery to suggest a safety rail.
   - Add a flat cap slab above the lantern, then a small red beacon block on top.

4) Keeper's house
   - Build a low attached house beside the tower using a simple box.
   - Cut a centered front door and regular windows on the long faces.
   - Place a gable roof on top of the house.
   - Attach a shallow porch canopy to the house front.

5) Composition / connections
   - site is the global base.
   - rocky plinth sits directly on the site.
   - tower and house both sit on the plinth, with the house attached to the tower's south face.
   - lantern and cap are stacked on top of the tower.
   - path sits directly on the site and lines up with the house entrance.
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
    place
)


# --- Overall scene ----------------------------------------------------------
SITE_W = 52
SITE_D = 40

PLINTH_W = 18
PLINTH_D = 30
PLINTH_H = 2  # bricks

PATH_W = 6
PATH_D = 4

# --- Lighthouse tower -------------------------------------------------------
BASE_W = PLINTH_W
BASE_D = 16
BASE_H = 7

SHAFT_W = BASE_W - 2
SHAFT_D = 12
SHAFT_H = 20

GALLERY_W = 14
GALLERY_D = 14

LANTERN_W = 8
LANTERN_D = 8
LANTERN_H = 5

CAP_W = 8
CAP_D = 8
BEACON_W = 4
BEACON_D = 4
BEACON_H = 2

# --- Keeper's house ---------------------------------------------------------
HOUSE_W = 18
HOUSE_D = 12
HOUSE_H = 6
PORCH_W = 8
PORCH_D = 2

# --- Colors ----------------------------------------------------------------
GROUND = Color.BRIGHT_GREEN
PATH = Color.TAN
ROCK = Color.DARK_BLUISH_GREY
TOWER = Color.WHITE
TRIM = Color.RED
LANTERN = Color.DARK_RED
HOUSE = Color.WHITE
ROOF = Color.DARK_RED
GLASS = Color.TRANS_LIGHT_BLUE
BLACK = Color.BLACK
POST = Color.LIGHT_GREY


# --- Helpers ----------------------------------------------------------------
def add_window(wall, x: int, y: int, width: int, height: int, part_type: PartType, color: int = GLASS):
    wall.opening(x=x, y=y, width=width, height=height)
    wall.insert(part_type, x=x, y=y, color=color)


def dress_tower_base(shell: Box) -> None:
    # Front door and side lights.
    shell.south.opening(x=6, y=0, width=4, height=6)
    shell.south.insert(PartType.DOOR_1X4X6, x=6, y=0, color=BLACK)
    add_window(shell.south, x=2, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.south, x=12, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    # Rear and side windows.
    add_window(shell.north, x=7, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=7, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=7, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=BASE_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)



def dress_tower_shaft(shell: Box) -> None:
    # Staggered windows so the shaft feels vertical and less repetitive.
    add_window(shell.south, x=5, y=4, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.south, x=5, y=12, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    add_window(shell.north, x=5, y=8, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=5, y=6, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.east, x=5, y=14, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=5, y=10, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=SHAFT_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)



def dress_lantern(shell: Box) -> None:
    for wall in shell.walls():
        add_window(wall, x=2, y=1, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
        wall.ledge(y=LANTERN_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)



def make_house() -> Group:
    house = Group("keepers_house")
    shell = Box(HOUSE_W, HOUSE_D, HOUSE_H, color=HOUSE, name="house_shell")

    shell.south.opening(x=7, y=0, width=4, height=6)
    shell.south.insert(PartType.DOOR_1X4X6, x=7, y=0, color=BLACK)
    add_window(shell.south, x=2, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.south, x=12, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    add_window(shell.north, x=2, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)
    add_window(shell.north, x=12, y=2, width=4, height=3, part_type=PartType.WINDOW_1X4X3)

    add_window(shell.east, x=4, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)
    add_window(shell.west, x=4, y=2, width=2, height=3, part_type=PartType.WINDOW_1X2X3)

    for wall in shell.walls():
        wall.ledge(y=HOUSE_H - 1, overhang=1, color=TRIM, part_type=PartType.PLATE_2X4)

    roof = GableRoof(HOUSE_W, HOUSE_D, ridge="east_west", color=ROOF, name="house_roof")
    house = place(roof, on=shell, align="center")

    porch = FloorSlab(PORCH_W, PORCH_D, color=ROOF, fill_part=PartType.PLATE_2X4, name="porch_canopy")
    attach(porch, to=house, face="south", align="center", offset=(0, 12))
    house.add(Column(height=4, color=POST, part_type=PartType.BRICK_1X1, name="porch_post_w"), x=6, y=0, z=-PORCH_D)
    house.add(Column(height=4, color=POST, part_type=PartType.BRICK_1X1, name="porch_post_e"), x=11, y=0, z=-PORCH_D)
    return house



def make_tower() -> Group:
    tower = Group("tower")

    base = Box(BASE_W, BASE_D, BASE_H, color=TOWER, name="tower_base")
    dress_tower_base(base)
    tower.add(base, x=0, y=0, z=0)

    shaft = Box(SHAFT_W, SHAFT_D, SHAFT_H, color=TOWER, name="tower_shaft")
    dress_tower_shaft(shaft)
    tower.add(shaft, x=(BASE_W - SHAFT_W) // 2, y=base.height_plates, z=(BASE_D - SHAFT_D) // 2)

    gallery = FloorSlab(GALLERY_W, GALLERY_D, color=TRIM, fill_part=PartType.PLATE_2X4, name="gallery")
    gallery_x = (BASE_W - GALLERY_W) // 2
    gallery_z = (BASE_D - GALLERY_D) // 2
    tower.add(gallery, x=gallery_x, y=base.height_plates + shaft.height_plates, z=gallery_z)

    lantern = Box(LANTERN_W, LANTERN_D, LANTERN_H, color=LANTERN, name="lantern_room")
    dress_lantern(lantern)
    lantern_x = (BASE_W - LANTERN_W) // 2
    lantern_z = (BASE_D - LANTERN_D) // 2
    tower.add(lantern, x=lantern_x, y=base.height_plates + shaft.height_plates + gallery.height_plates, z=lantern_z)

    # Corner posts on the gallery deck to suggest a guard rail.
    post_y = base.height_plates + shaft.height_plates + 1
    for name, x, z in (
        ("rail_sw", gallery_x + 1, gallery_z + 1),
        ("rail_se", gallery_x + GALLERY_W - 2, gallery_z + 1),
        ("rail_nw", gallery_x + 1, gallery_z + GALLERY_D - 2),
        ("rail_ne", gallery_x + GALLERY_W - 2, gallery_z + GALLERY_D - 2),
    ):
        tower.add(Column(height=3, color=POST, part_type=PartType.BRICK_1X1, name=name), x=x, y=post_y, z=z)

    cap = FloorSlab(CAP_W, CAP_D, color=ROOF, fill_part=PartType.PLATE_2X4, name="lantern_cap")
    tower.add(cap, x=lantern_x, y=base.height_plates + shaft.height_plates + gallery.height_plates + lantern.height_plates, z=lantern_z)

    beacon = Box(BEACON_W, BEACON_D, BEACON_H, color=TRIM, name="beacon")
    tower.add(
        beacon,
        x=(BASE_W - BEACON_W) // 2,
        y=base.height_plates + shaft.height_plates + gallery.height_plates + lantern.height_plates + cap.height_plates,
        z=(BASE_D - BEACON_D) // 2,
    )

    return tower



def main() -> None:
    scene = Scene("coastal_lighthouse")

    # Site and setting.
    site = FloorSlab(SITE_W, SITE_D, color=GROUND, fill_part=PartType.PLATE_2X4, name="site")

    plinth = Box(PLINTH_W, PLINTH_D, PLINTH_H, color=ROCK, name="rock_plinth")
    path = FloorSlab(PATH_W, PATH_D, color=PATH, fill_part=PartType.PLATE_2X4, name="path")

    plinth_with_path = attach(path, to=plinth, face="south", align="center", offset=(0, 0))

    # 2) Tower + attached keeper's house.
    tower = make_tower()
    house = make_house()

    tower_with_house = attach(house, to=tower, face="south", align="center", offset=(0, 0))
    lighthouse = place(tower_with_house, on=plinth_with_path, align="flush_north")
    lighthouse_on_site = place(lighthouse, on=site, align="center")

    # 3) Add the whole composition to the scene and export.
    scene.add(lighthouse_on_site, x=0, y=0, z=0)

    out_path = __file__.replace(".py", ".mpd")

    output = scene.export(out_path)
    print(scene.stats())
    print(output)


if __name__ == "__main__":
    main()
