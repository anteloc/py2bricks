import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from py2bricks import (
    Scene,
    Group,
    FloorSlab,
    StaircaseShaft,
    Color,
    PartType,
)


def make_open_story(width: int, depth: int, story_height_bricks: int, story_index: int) -> Group:
    """A story with only a floor/ceiling slab and no exterior wall shell."""
    story = Group(name=f"open_story_{story_index}")

    ceiling = FloorSlab(
        width=width,
        depth=depth,
        color=Color.LIGHT_GREY,
        fill_part=PartType.PLATE_2X4.value,
        name=f"ceiling_{story_index}",
    )

    story.add(ceiling, y=story_height_bricks * 3)
    return story



def build_open_ten_story_building():
    scene = Scene("ten_story_building_open_for_stairs")

    building_width = 28
    building_depth = 20
    story_height_bricks = 10
    story_height_plates = story_height_bricks * 3
    num_stories = 10

    tower = Group("open_tower")
    for i in range(num_stories):
        tower.add(
            make_open_story(building_width, building_depth, story_height_bricks, i),
            y=i * (story_height_plates + 1),
        )

    stairs = StaircaseShaft(
        floors=num_stories,
        floor_height_bricks=story_height_bricks,
        stair_width=8,
        tread_depth=2,
        style="switchback",
        first_facing="north",
        color=Color.LIGHT_GREY,
        fill_part=PartType.BRICK_2X4.value,
        name="stairs",
    )

    base = FloorSlab(
        width=building_width + 4,
        depth=building_depth + 4,
        color=Color.DARK_TAN,
        fill_part=PartType.PLATE_2X4.value,
        name="base",
    )

    roof = FloorSlab(
        width=building_width,
        depth=building_depth,
        color=Color.DARK_BLUISH_GREY,
        fill_part=PartType.PLATE_2X4.value,
        name="roof",
    )

    scene.add(base, x=0, y=0, z=0)
    scene.add(tower, x=2, y=3, z=2)
    scene.add(stairs, x=8, y=3, z=6)
    scene.add(roof, x=2, y=3 + num_stories * (story_height_plates + 1), z=2)

    out_path = os.path.join(os.path.dirname(__file__), "ten_story_building_open_for_stairs.mpd")
    scene.export(out_path)
    return out_path


if __name__ == "__main__":
    output = build_open_ten_story_building()
    print(output)
