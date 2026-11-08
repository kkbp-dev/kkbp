"""SFW on the builder's Character (golden samples: run.py hooks --each)."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")


def _with_nsfw_bones():
    b = BundleBuilder()
    b.add_bone("cf_j_kokan", "cf_j_hips", group="nsfw", translation=(0.0, -0.1, 0.05))
    b.add_bone("cf_J_Vagina_root", "cf_j_kokan", group="nsfw")
    b.add_bone("cf_s_bnip02_L", "cf_j_spine01", group="breast", translation=(0.05, 0.2, 0.1))
    b.add_material("cf_m_crotch", role=None, textures=[b.add_texture("_MainTex", role="main")])
    b.add_mesh("o_crotch", ["cf_m_body"], bone="cf_j_kokan")  # skinned to the crotch: goes
    b.add_mesh("o_nipple", ["cf_m_body"], bone="cf_s_bnip02_L")  # skinned to a nipple: goes
    b.add_mesh("o_panties", ["ct_top_shirt"], outfit=0, bone="cf_j_kokan")  # clothes keep crotch vertices
    return b


def test_removes_the_nsfw_and_nipple_vertices_and_bones(build):
    path = build(_with_nsfw_bones())
    core = kkbp.api.import_bundle(path, hooks=[])
    before = {o.get("kkbp_role"): len(o.data.vertices) for o in character.Character(core.character_key).parts()
              if o.type == "MESH" and o.get("kkbp_role") in ("body", "outfit")}
    result = kkbp.api.import_bundle(path, options={"sfw_mode": True}, hooks=["SFW"])
    assert result.ok and result.hooks[0].status == "ran", result.hooks
    ch = character.Character(result.character_key)
    assert len(ch.body.data.vertices) < before["body"]
    assert len(ch.outfits[0].data.vertices) == before["outfit"]
    bones = ch.armature.data.bones
    assert "cf_j_kokan" not in bones and "cf_J_Vagina_root" not in bones
    assert "cf_s_bnip02_L" in bones  # the legacy list deletes its vertices, not the bone
    assert "cf_j_kokan" not in ch.body.vertex_groups and "cf_s_bnip02_L" not in ch.body.vertex_groups
    assert "cf_j_kokan" in ch.outfits[0].vertex_groups
