"""The body follows the shown Outfit (ADR 0055): showing one Outfit's Collection puts that
Outfit's body textures, such as its alpha mask, into the body's materials and their copies."""

import bpy
import pytest

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")
templates = submodule("templates")
settings = submodule("settings")
outfit_textures = submodule("outfit_textures")

RED, BLUE, GREEN = (255, 0, 0, 255), (0, 0, 255, 255), (0, 255, 0, 255)


@pytest.fixture(autouse=True)
def no_preferences(monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})


def _two_outfits(game="KK", second_mask=True):
    """The default Character (Outfit 00 sets a red alpha mask) with an Outfit 01 that sets a blue one,
    and on SVS a bottom mask for each. With `second_mask` False, Outfit 01 sets none."""
    b = BundleBuilder(game)
    body = next(m for m in b.materials if m["role"] == "body")
    b.passes[0]["body_textures"][0]["texture"] = b.add_texture("_AlphaMask", role="alpha_mask", color=RED)
    b.add_material("ct_top_tank", blend_mode="cutout", shader="Shader Forge/main_opaque",
                   textures=[b.add_texture("_MainTex", role="main")])
    b.add_mesh("o_top_tank", ["ct_top_tank"], outfit=1, bone="cf_j_spine01")
    if second_mask:
        b.add_body_texture(1, body["id"], b.add_texture("_AlphaMask", role="alpha_mask", color=BLUE))
    if game == "SVS":
        b.add_body_texture(0, body["id"], b.add_texture("_Cloth_alpha_bot", color=GREEN))
        if second_mask:
            b.add_body_texture(1, body["id"], b.add_texture("_Cloth_alpha_bot", color=BLUE))
    return b, body["id"]


def _import(path, hooks=()):
    result = kkbp.api.import_bundle(path, hooks=list(hooks))
    assert result.ok, f"{result.failed_step}: {result.error}"
    assert all(h.status == "ran" for h in result.hooks), result.hooks
    return character.Character(result.character_key)


def _color(node):
    """The image's first pixel, as 0-255 RGBA, or None for no image."""
    if node.image is None:
        return None
    return tuple(round(c * 255) for c in node.image.pixels[:4])


def _show(ch, outfit):
    """Shows only Outfit `outfit`'s Collection, as the eye icons in the Outliner do."""
    def walk(layer):
        number = layer.collection.get(character.OUTFIT)
        if layer.collection.get(character.KEY) == ch.key and number is not None:
            layer.hide_viewport = number != outfit
        for child in layer.children:
            walk(child)
    walk(bpy.context.view_layer.layer_collection)
    bpy.context.view_layer.update()


@pytest.mark.parametrize("game", ["KK", "SVS"])
def test_showing_an_outfit_puts_its_masks_on_the_body(game, build):
    b, body_id = _two_outfits(game)
    ch = _import(build(b))
    body = ch.material(body_id)
    slots = ["alpha_mask"] + (["alpha_mask_bottom"] if game == "SVS" else [])
    first = {"alpha_mask": RED, "alpha_mask_bottom": GREEN}
    assert outfit_textures.outfits(body) == [0, 1]
    for slot in slots:
        assert _color(templates.texture_node(body, slot)) == first[slot]
    _show(ch, 1)
    for slot in slots:
        assert _color(templates.texture_node(body, slot)) == BLUE, slot
    _show(ch, 0)
    for slot in slots:
        assert _color(templates.texture_node(body, slot)) == first[slot], slot


def test_an_outfit_with_no_mask_shows_the_body_unmasked(build):
    """The slot gets the template's own image back, as an import of that Outfit alone would leave."""
    b, body_id = _two_outfits(second_mask=False)
    ch = _import(build(b))
    body = ch.material(body_id)
    node = templates.texture_node(body, "alpha_mask")
    own = templates.texture_node(templates.template_material(body[templates.TEMPLATE]), "alpha_mask").image
    assert _color(node) == RED
    _show(ch, 1)
    assert node.image == own
    _show(ch, 0)
    assert _color(node) == RED


def test_several_or_no_outfits_shown_keep_the_masks(build):
    b, body_id = _two_outfits()
    ch = _import(build(b))
    node = templates.texture_node(ch.material(body_id), "alpha_mask")
    _show(ch, 1)
    for layer in bpy.context.view_layer.layer_collection.children[ch.collection.name].children:
        layer.hide_viewport = False  # both shown
    bpy.context.view_layer.update()
    assert _color(node) == BLUE
    _show(ch, None)  # none shown
    assert _color(node) == BLUE


def test_one_outfit_stores_nothing(build):
    b = BundleBuilder()
    ch = _import(build(b))
    body = next(iter(ch.materials(roles="body")))
    assert outfit_textures.TEXTURES not in body
    assert templates.texture_node(body, "alpha_mask").image is not None


def test_the_body_outline_follows(build):
    b, body_id = _two_outfits()
    face = next(m for m in b.materials if m["role"] == "face")  # baked, or Body gets no outline
    face["textures"] += [b.add_texture("_MainTex", role="main", variant="light"),
                         b.add_texture("_MainTex", role="main", variant="dark")]
    ch = _import(build(b), hooks=["Outlines"])
    outline = next(m for m in bpy.data.materials if m.get("kkbp_outline") == body_id)
    node = templates.texture_node(outline, "alpha_mask")
    assert _color(node) == RED
    _show(ch, 1)
    assert _color(node) == BLUE


def test_the_shown_outfit_survives_saving(build, tmp_path):
    b, body_id = _two_outfits()
    ch = _import(build(b))
    _show(ch, 1)
    path = str(tmp_path / "saved.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    bpy.ops.wm.open_mainfile(filepath=path)
    ch = character.Character.all(bpy.context.scene)[0]
    node = templates.texture_node(ch.material(body_id), "alpha_mask")
    bpy.context.view_layer.update()
    assert _color(node) == BLUE
    _show(ch, 0)
    assert _color(node) == RED


def test_a_frame_change_updates_no_material_with_two_outfits(build):
    """Playing an animation doesn't re-evaluate the body's materials: the masks change only when
    the shown Outfit does, never by a driver (ADR 0042, "Consequences")."""
    b, _ = _two_outfits("SVS")
    ch = _import(build(b))
    _show(ch, 1)
    seen = []

    def note(scene, depsgraph):
        seen.append({type(u.id).__name__ + " " + u.id.name for u in depsgraph.updates})

    bpy.app.handlers.frame_change_post.append(note)
    try:
        for frame in range(1, 9):
            bpy.context.scene.frame_set(frame)
    finally:
        bpy.app.handlers.frame_change_post.remove(note)
    for updated in seen[2:]:
        assert not {u for u in updated if u.startswith("Material")}, sorted(updated)


def test_export_prep_atlases_the_shown_outfits_mask(build):
    """Export Prep folds the body's alpha mask into its atlas (atlas/alpha.py): the shown Outfit's."""
    atlas = submodule("tools.export_prep.atlas")
    b, body_id = _two_outfits()
    ch = _import(build(b))
    body = ch.material(body_id)
    _show(ch, 1)
    assert tuple(round(c * 255) for c in atlas._image(body, "alpha_mask").pixels[:4]) == BLUE
