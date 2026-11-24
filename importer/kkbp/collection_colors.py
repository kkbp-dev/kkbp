"""The colour each kind of Collection the importer makes shows in the Outliner, by what it holds
(issue #130). Every place that makes a Collection tags it here, so the colours are in one table.

Blender's colour tags are theme colours; in the default theme COLOR_01 is red, 02 orange, 03 yellow,
04 green, 05 blue, 06 violet, 07 pink and 08 brown. The Collections inside Junk (the widgets and the
face board labels) take no colour of their own.
"""

COLORS = {
    "character": "COLOR_05",  # blue: the Character's own Collection, its body and rig
    "outfit": "COLOR_04",  # green: an Outfit's clothes and hair
    "alts": "COLOR_02",  # orange: an Outfit's alternate clothes
    "low_poly": "COLOR_03",  # yellow: the Low poly Hook's copies of an Outfit
    "face": "COLOR_07",  # pink: the tears and gag eyes, the separated eyes and eyebrows, the face cards
    "junk": "COLOR_01",  # red: the Rigify Hook's widgets, metarig and face board labels; leave alone
    "atlas": "COLOR_08",  # brown: Export Prep's atlas copy
}


def color(collection, kind: str):
    """Gives `collection` the colour of `kind`, a key of COLORS, and returns it."""
    collection.color_tag = COLORS[kind]
    return collection
