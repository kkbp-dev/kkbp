"""Loads one Pass's .glb (docs/design/blender-compat-and-testing.md, "Mesh Loader").

This is the only caller of `bpy.ops.import_scene.gltf`, and it sets every option the importer has
apart from its file-browser ones, so a Blender update that changes a default can't change an
import. `problems()` reports an option that no longer exists; it is checked when the add-on starts
and before every import.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import bpy

from . import compat

log = logging.getLogger("kkbp")

GLTF_OPTIONS = {
    "import_shading": "NORMALS",  # keep the exported normals
    "merge_vertices": False,
    "bone_heuristic": "BLENDER",  # keep the game's bone axes; Phase 4 sets tails and roll
    "guess_original_bind_pose": False,  # the rest pose is the node tree (ADRs 0006, 0008)
    "disable_bone_shape": True,  # no "Icosphere" bone-shape object
    "bone_shape_scale_factor": 1.0,
    "import_pack_images": False,  # no images are embedded
    "import_webp_texture": False,
    "import_unused_materials": False,
    "import_select_created_objects": False,
    "import_scene_extras": True,  # extras.id becomes the "id" custom property
    "import_scene_as_collection": False,
    "import_merge_material_slots": False,  # one slot per primitive, in the Pass's material order
    "import_point_as_pointcloud": False,
    "export_import_convert_lighting_mode": "SPEC",
    "loglevel": 0,
}
# The operator's file-browser properties, which aren't import options.
_UI_PROPERTIES = {"rna_type", "filepath", "filter_glob", "directory", "files"}

_checked_ok = False


class MeshLoaderError(Exception):
    pass


@dataclass
class LoadedPass:
    """The objects one .glb made: its armature, and its meshes by Id."""

    armature: bpy.types.Object
    meshes: dict[str, bpy.types.Object] = field(default_factory=dict)


def problems() -> list[str]:
    """What stops the Mesh Loader working in this Blender, as messages for the user."""
    global _checked_ok
    if _checked_ok:
        return []
    try:
        properties = {p.identifier for p in bpy.ops.import_scene.gltf.get_rna_type().properties}
    except (AttributeError, KeyError):
        return ["Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences."]
    found = [f"glTF importer option {name} no longer exists in Blender {bpy.app.version_string}"
             for name in GLTF_OPTIONS if name not in properties]
    _checked_ok = not found
    return found


def unset_options() -> list[str]:
    """Options the glTF importer has that GLTF_OPTIONS doesn't set (new in a Blender update)."""
    properties = _properties()
    return [name for name in properties if name not in compat.gltf_options(GLTF_OPTIONS, properties)
            and name not in _UI_PROPERTIES]


def _properties() -> list[str]:
    return [p.identifier for p in bpy.ops.import_scene.gltf.get_rna_type().properties]


def check_at_startup():
    """Logs what problems() finds. Run from a timer, once Blender's own add-ons are registered."""
    for message in problems():
        log.error(message)


def load(path: str | Path, collection) -> LoadedPass:
    """Imports one .glb and links everything it made into `collection` only."""
    found = problems()
    if found:
        raise MeshLoaderError("; ".join(found))
    before = set(bpy.data.objects)
    result = bpy.ops.import_scene.gltf(filepath=str(path), **compat.gltf_options(GLTF_OPTIONS, _properties()))
    if "FINISHED" not in result:
        raise MeshLoaderError(f"Blender's glTF importer couldn't read {path} ({', '.join(sorted(result))})")
    made = [o for o in bpy.data.objects if o not in before]
    for obj in made:
        for other in list(obj.users_collection):
            other.objects.unlink(obj)
        collection.objects.link(obj)

    armatures = [o for o in made if o.type == "ARMATURE"]
    if len(armatures) != 1:
        raise MeshLoaderError(f"{path} made {len(armatures)} armatures; a Pass has exactly one")
    loaded = LoadedPass(armature=armatures[0])
    for obj in made:
        if obj.type != "MESH":
            continue
        id = obj.get("id")
        if not isinstance(id, str):
            raise MeshLoaderError(f"{path}: mesh object {obj.name} has no Id")
        loaded.meshes[id] = obj
    return loaded
