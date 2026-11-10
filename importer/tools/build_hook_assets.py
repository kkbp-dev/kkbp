"""Builds the built-in Hooks' asset files from the legacy KK Shader V9.blend (D15, ADR 0018).

    blender --background --factory-startup --python importer/tools/build_hook_assets.py -- SOURCE

Run it through scripts/build-hook-assets.sh. SOURCE is never changed. Each file named in
kkbp/library/hook_assets.py is made from a fresh copy of SOURCE that keeps only what its Hook
uses; every difference from the legacy assets is made here:

- rigify.blend: the "Bone Widgets" collection;
- face_cards.blend: the "Face cards" collection, with the card image nodes named for the Material
  Role whose texture goes into them, and the 8192 x 4480 mouth atlas stored as WebP at quality 95
  instead of PNG (12.4 MB -> 3.3 MB; the difference is invisible, D15); plus SVS's eye white mask,
  `SVS Eye_White_Alpha.png` beside SOURCE, which isn't in the legacy file (ADR 0037);
- outlines.blend: the black, placeholder and face-mask images.

Every datablock gets `kkbp_asset_version`.
"""

import os
import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kkbp"))
from library import hook_assets  # noqa: E402  (no bpy: the asset descriptions)

# The legacy face card image nodes, by (material, legacy node name) -> the node name the
# description uses.
FACE_CARD_NODES = {
    ("Eyeline card", "up"): "tex.eyeline_upper",
    ("Eyeline card", "kage"): "tex.eyeline_shadow",
    ("Eyeline card", "down"): "tex.eyeline_lower",
    ("Eyewhite card", "_light.png"): "tex.eye_white",
    ("Eyewhite card", "Image Texture.001"): "tex.eye_white_mask",
    ("Pupil L card", "_light.png"): "tex.eye_l",
    ("Pupil R card", "_light.png"): "tex.eye_r",
}
# The legacy file's KK eye white mask, and the file beside SOURCE that SVS's is packed from
# (importer/tools/make_svs_eye_white_mask.py, ADR 0037).
LEGACY_EYE_WHITE_MASK = "Eye_White_Alpha"
SVS_EYE_WHITE_MASK_FILE = "SVS Eye_White_Alpha.png"
LEGACY_ATLAS = "MouthAtlas.png"
ATLAS_QUALITY = 95


def main():
    source = sys.argv[sys.argv.index("--") + 1]
    build(source, hook_assets.RIGIFY, keep_collections=[hook_assets.RIGIFY.collection])
    build(source, hook_assets.FACE_CARDS, keep_collections=[hook_assets.FACE_CARDS.collection],
          finish=lambda asset: finish_face_cards(asset, Path(source).parent))
    outlines = hook_assets.OUTLINES
    build(source, outlines, keep_images=[outlines.black, outlines.placeholder, *outlines.face_masks.values()])


def build(source, asset, keep_collections=(), keep_images=(), finish=None):
    bpy.ops.wm.open_mainfile(filepath=source, load_ui=False)
    keep = set(keep_collections)
    kept_objects = {o for name in keep for o in bpy.data.collections[name].all_objects}
    for obj in list(bpy.data.objects):
        if obj not in kept_objects:
            bpy.data.objects.remove(obj)
    for collection in list(bpy.data.collections):
        if collection.name not in keep and not any(collection.name in [c.name for c in
                                                                       bpy.data.collections[k].children_recursive]
                                                   for k in keep):
            bpy.data.collections.remove(collection)
    for scene_collection in [s.collection for s in bpy.data.scenes]:
        for child in list(scene_collection.children):
            scene_collection.children.unlink(child)
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)
    for datablock in list(bpy.data.materials) + list(bpy.data.node_groups) + list(bpy.data.images):
        datablock.use_fake_user = datablock.name in keep_images
    for name in keep:
        bpy.data.collections[name].use_fake_user = True  # the files have no scene the collection is in
    if finish:
        finish(asset)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    for kind in ("collections", "objects", "meshes", "armatures", "materials", "node_groups", "images"):
        for datablock in getattr(bpy.data, kind):
            datablock[hook_assets.VERSION_PROP] = hook_assets.ASSET_VERSION
    bpy.ops.wm.save_as_mainfile(filepath=str(asset.path), compress=True, copy=False)
    backup = Path(str(asset.path) + "1")
    if backup.exists():
        backup.unlink()
    print(f"Wrote {asset.path.name}: {asset.path.stat().st_size / 1e6:.1f} MB, {len(bpy.data.objects)} objects, "
          f"{len(bpy.data.images)} images")


def finish_face_cards(asset, source_folder):
    for (material, legacy), name in FACE_CARD_NODES.items():
        node = bpy.data.materials[material].node_tree.nodes[legacy]
        node.name = node.label = name
    eye_white_masks(asset, source_folder)
    atlas = bpy.data.images[LEGACY_ATLAS]
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, asset.atlas)
        save_webp(atlas, path)
        webp = bpy.data.images.load(path, check_existing=False)
        webp.pack()
    webp.name = asset.atlas
    webp.filepath = "//" + asset.atlas
    webp.colorspace_settings.name = atlas.colorspace_settings.name
    webp.alpha_mode = atlas.alpha_mode
    atlas.user_remap(webp)
    bpy.data.images.remove(atlas)


def eye_white_masks(asset, source_folder):
    """Checks that the legacy mask is the one the card uses, and packs SVS's beside it with the same
    settings. Nothing in the file uses SVS's, so a fake user keeps it; the Hook appends it by name."""
    material, node = asset.eye_white_mask
    legacy = bpy.data.materials[material].node_tree.nodes[node].image
    if legacy is None or legacy.name != LEGACY_EYE_WHITE_MASK:
        raise RuntimeError(f"{material}'s {node} doesn't hold {LEGACY_EYE_WHITE_MASK}")
    if set(asset.eye_white_masks.values()) != {LEGACY_EYE_WHITE_MASK, Path(SVS_EYE_WHITE_MASK_FILE).stem}:
        raise RuntimeError("hook_assets.FACE_CARDS.eye_white_masks names masks this script doesn't make")
    svs = bpy.data.images.load(str(source_folder / SVS_EYE_WHITE_MASK_FILE), check_existing=False)
    svs.pack()
    svs.name = Path(SVS_EYE_WHITE_MASK_FILE).stem
    svs.filepath = "//" + SVS_EYE_WHITE_MASK_FILE
    svs.colorspace_settings.name = legacy.colorspace_settings.name
    svs.alpha_mode = legacy.alpha_mode
    svs.use_fake_user = True


def save_webp(image, path):
    """Image.save ignores the quality for WebP and writes a larger file than the PNG, so the image is
    saved through the scene's output settings, with the Standard view transform so colours don't move."""
    scene = bpy.data.scenes[0]
    settings = scene.render.image_settings
    settings.file_format = "WEBP"
    settings.color_mode = "RGBA"
    settings.quality = ATLAS_QUALITY
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    image.save_render(path, scene=scene)


main()
