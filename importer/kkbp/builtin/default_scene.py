"""Delete default scene: removes the cube, camera and light of Blender's startup file (legacy
importbuttons did this before every import).

The default scene is known by its objects' names and types: nothing else marks it. Legacy deleted
them only when they were the file's only three objects; here they are deleted only when every other
object belongs to an imported Character, so the Hook never touches a scene someone has started.
"""

import bpy

from ..character import KEY
from ..pipeline.hooks import hook
from ..pipeline.options import Option

# Blender's startup file: object name -> object type.
DEFAULT_OBJECTS = {"Cube": "MESH", "Camera": "CAMERA", "Light": "LIGHT"}
DATA = {"MESH": "meshes", "CAMERA": "cameras", "LIGHT": "lights"}  # their data, removed once unused

SWITCH = Option(
    "delete_default_scene", bool, True, "Delete default scene",
    description="Deletes the cube, camera and light of Blender's startup file, if the file holds nothing "
                "else but imported Characters")


@hook(name="Delete default scene", switch=SWITCH)
def delete_default_scene(ctx):
    defaults = [bpy.data.objects.get(name) for name in DEFAULT_OBJECTS]
    if not all(obj is not None and obj.type == kind for obj, kind in zip(defaults, DEFAULT_OBJECTS.values())):
        return
    characters = _character_collections()
    others = [o for o in bpy.data.objects if o not in defaults and not _belongs(o, characters)]
    if others:
        ctx.log.info(f"The default scene stays: the file holds other objects too ({others[0].name}, …)")
        return
    for obj in defaults:
        data, kind = obj.data, obj.type
        bpy.data.objects.remove(obj)
        if data.users == 0:
            getattr(bpy.data, DATA[kind]).remove(data)
    ctx.log.info("Deleted the default cube, camera and light")


def _character_collections():
    """Every Collection inside a Character's Collection, and those Collections themselves."""
    found = set()

    def walk(collection):
        found.add(collection)
        for child in collection.children:
            walk(child)
    for collection in [c for c in bpy.data.collections if KEY in c]:
        walk(collection)
    return found


def _belongs(obj, characters):
    """A Character's object: a Part, or anything inside a Character's Collection (Rigify widgets)."""
    return KEY in obj or any(c in characters for c in obj.users_collection)
