"""The body follows the shown Outfit (issue 119, ADR 0055).

Each Outfit sets textures on body materials, such as the alpha mask that hides the skin under its
clothes (an Outfit Pass's `body_textures`). The import puts the first Outfit's into the materials
and, when the Character has more than one Outfit, stores every Outfit's on each material they go
on (`TEXTURES`). While the add-on is enabled, showing exactly one Outfit's Collection puts that
Outfit's textures into those materials' image nodes, and into the outlines copied from them.

Nothing is driven: the materials don't change with the frame, so playback costs the same as with
one Outfit, and the shaders keep one image node per slot. The file keeps whichever Outfit's textures
were put in last, also without the add-on. A copy of the material copies `TEXTURES` and follows too.
"""

from __future__ import annotations

import bpy

from . import templates
from .character import KEY, OUTFIT

# On a material: {"character": Key, "slots": {slot: {"NN": {"image"?, "offset", "scale"}}}}, one entry
# per Outfit for every slot an Outfit fills. An entry without "image" leaves the slot empty.
TEXTURES = "kkbp_outfit_textures"

_shown: dict[str, frozenset] = {}  # Character Key -> the Outfits last seen shown


def register():
    for handlers, handler in _HANDLERS:
        if handler not in handlers:
            handlers.append(handler)


def unregister():
    for handlers, handler in _HANDLERS:
        if handler in handlers:
            handlers.remove(handler)
    _shown.clear()


# --- at import -------------------------------------------------------------------------------

def store(material, key: str, slot: str, outfit: int, image, offset=(0.0, 0.0), scale=(1.0, 1.0)):
    """Records the image Outfit `outfit` puts in the material's `slot`, with its offset and scale.
    An `image` of None leaves the slot empty."""
    if TEXTURES not in material:
        material[TEXTURES] = {"character": key, "slots": {}}
    slots = material[TEXTURES]["slots"]
    if slot not in slots:
        slots[slot] = {}
    entry = {"offset": list(offset[:2]), "scale": list(scale[:2])}
    if image is not None:
        entry["image"] = image
    slots[slot][f"{outfit:02d}"] = entry


def outfits(material) -> list[int]:
    """The Outfits the material holds textures for, or none."""
    data = material.get(TEXTURES) if material is not None else None
    if data is None:
        return []
    return sorted({int(n) for by_outfit in data["slots"].values() for n in by_outfit.keys()})


# --- showing an Outfit -----------------------------------------------------------------------

def put(material, outfit: int) -> bool:
    """Puts Outfit `outfit`'s stored textures into the material. False if it holds none for it."""
    data = material.get(TEXTURES)
    if data is None:
        return False
    done = False
    number = f"{outfit:02d}"
    for slot, by_outfit in data["slots"].items():
        entry = by_outfit.get(number)
        node = templates.texture_node(material, slot) if entry is not None else None
        if node is None:
            continue
        done = True
        image = entry.get("image")
        if node.image != image:
            node.image = image
        offset, scale = tuple(entry["offset"]), tuple(entry["scale"])
        if templates.set_position(material, slot, offset, scale):
            continue
        if tuple(node.texture_mapping.translation[:2]) != offset:
            node.texture_mapping.translation[:2] = offset
        if tuple(node.texture_mapping.scale[:2]) != scale:
            node.texture_mapping.scale[:2] = scale
    return done


def show(key: str, outfit: int) -> int:
    """Puts Outfit `outfit`'s textures into every material of Character `key` that stores them.
    Returns how many materials took them."""
    return sum(put(m, outfit) for m in bpy.data.materials
               if m.get(TEXTURES) is not None and m[TEXTURES]["character"] == key)


def shown_outfits(view_layer) -> dict[str, frozenset]:
    """Character Key -> the Outfits whose Collection is visible in `view_layer`, for every Character
    with Outfit Collections there."""
    found: dict[str, set] = {}

    def walk(layer):
        collection = layer.collection
        key, outfit = collection.get(KEY), collection.get(OUTFIT)
        if key is not None and outfit is not None:
            outfits = found.setdefault(key, set())
            if not layer.exclude and layer.visible_get():
                outfits.add(outfit)
        for child in layer.children:
            walk(child)

    walk(view_layer.layer_collection)
    return {key: frozenset(outfits) for key, outfits in found.items()}


def sync(view_layer=None):
    """Puts in the textures of the one Outfit each Character shows, where that changed since the last
    look. A Character showing no Outfit or several keeps what it has."""
    view_layer = view_layer or bpy.context.view_layer
    for key, outfits in shown_outfits(view_layer).items():
        if _shown.get(key) == outfits:
            continue
        _shown[key] = outfits
        if len(outfits) == 1:
            show(key, next(iter(outfits)))


@bpy.app.handlers.persistent
def _after_update(scene, depsgraph):
    # Runs after every change, including the one it makes; it only acts when the shown Outfits change.
    sync(depsgraph.view_layer)


@bpy.app.handlers.persistent
def _after_load(*_):
    _shown.clear()


_HANDLERS = ((bpy.app.handlers.depsgraph_update_post, _after_update),
             (bpy.app.handlers.load_post, _after_load))
