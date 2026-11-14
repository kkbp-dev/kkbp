"""Bundles that break the contract: open_bundle raises one BundleError listing every problem."""

import pytest

import bundle
from bundle_builder import BundleBuilder, edit_json


def _bone(files, id):
    return next(b for b in files["skeleton.json"]["bones"] if b["id"] == id)


def _material(files, id):
    return next(m for m in files["materials.json"]["materials"] if m["id"] == id)


def _create(files, id):
    return _material(files, id)["extensions"]["kk"]["create"]


def _set(path, value):
    def change(files):
        *keys, last = path
        node = files
        for k in keys:
            node = node[k]
        node[last] = value
    return change


# (what is broken, change to the builder's files, text of the one expected problem)
CASES = [
    # Fields and types.
    ("missing field", lambda f: f["manifest.json"].pop("exported_at"), "manifest.json: 'exported_at' is missing"),
    ("wrong type", _set(["manifest.json", "options", "physics"], "yes"),
     "manifest.json.options.physics: should be true or false"),
    ("bool as number", lambda f: _bone(f, "cf_j_head").update(translation=[0, True, 0]),
     "translation[1]: should be a number"),
    ("short vector", lambda f: _bone(f, "cf_j_head").update(rotation=[0, 0, 1]), "should be a list of 4 numbers"),
    ("bad Id", lambda f: _bone(f, "cf_j_head").update(id="cf__head"), "'cf__head' isn't a valid Id"),
    ("long Id", lambda f: _bone(f, "cf_j_head").update(id="b" * 64), "isn't a valid Id"),
    ("bad time", _set(["manifest.json", "exported_at"], "2026-11-01 12:00"), "should be an RFC 3339 time in UTC"),
    ("bad card", _set(["manifest.json", "card"], "face.png"), "should be 'card.png' or null"),
    ("bad texture path", lambda f: _material(f, "cf_m_body")["textures"][0].update(file="../x.png"),
     "should be a path like 'textures/0001.png'"),
    ("no passes", _set(["manifest.json", "passes"], []), "manifest.json.passes: should have at least 1 item"),
    ("body pass path", lambda f: f["manifest.json"]["passes"][0].update(mesh="outfits/00/outfit.glb"),
     "a body Pass has outfit null"),
    ("outfit pass path", lambda f: f["manifest.json"]["passes"][1].update(data="outfit.json"),
     "an Outfit Pass has an Outfit index"),
    ("empty effect", lambda f: f["expressions.json"]["effects"].append({"target": "Eye Happy"}),
     "names no shows, hides or material_changes"),
    ("collider direction", lambda f: f["physics.json"]["colliders"][0].update(direction="w"), "should be one of"),

    # Closed sets, in a bundle whose minor version this importer knows.
    ("unknown Bone Role", lambda f: _bone(f, "cf_j_head").update(role="halo"), "'halo' isn't a Bone Role"),
    ("unknown Bone Group", lambda f: _bone(f, "cf_j_head").update(group="tail"), "'tail' isn't a Bone Group"),
    ("unknown Material Role", lambda f: _material(f, "ct_top_shirt").update(role="shirt"),
     "'shirt' isn't a Material Role"),
    ("unknown Blend Mode", lambda f: _material(f, "ct_top_shirt").update(blend_mode="additive"),
     "'additive' isn't a Blend Mode"),
    ("unknown Texture Role", lambda f: _material(f, "cf_m_body")["textures"][3].update(role="bump"),
     "'bump' isn't a Texture Role"),
    ("unknown Expression Name", lambda f: f["expressions.json"]["expressions"][0].update(name="Eye Sparkle"),
     "'Eye Sparkle' isn't a Expression Name"),

    # Pass rules.
    ("data doesn't match Manifest", lambda f: f["outfits/00/outfit.json"].update(outfit=1),
     "outfits/00/outfit.json doesn't match its Manifest entry"),
    ("body textures on Body Pass", lambda f: f["body.json"].update(body_textures=f["outfits/00/outfit.json"]["body_textures"]),
     "the Body Pass has no body_textures"),
    ("two body Passes", lambda f: f["manifest.json"]["passes"].append(dict(f["manifest.json"]["passes"][0])),
     "the Manifest lists 2 body Passes"),
    ("Outfit folder isn't its index", lambda f: (f["manifest.json"]["passes"][1].update(outfit=1),
                                                 f["outfits/00/outfit.json"].update(outfit=1)),
     "Outfit 01's files outfits/00/outfit.glb and outfits/00/outfit.json aren't in outfits/01/"),
    ("Outfit twice", lambda f: f["manifest.json"]["passes"].append(dict(f["manifest.json"]["passes"][1])),
     "the Manifest lists Outfit 00 2 times"),

    # Uniqueness.
    ("bone Id twice", lambda f: f["skeleton.json"]["bones"].append(dict(_bone(f, "N_Hair_pony"))),
     "bone Id N_Hair_pony appears twice"),
    ("unique Bone Role twice", lambda f: _bone(f, "cf_j_neck").update(role="head"), "Bone Role head appears 2 times"),
    ("unique Material Role twice", lambda f: _material(f, "c_m_namida").update(role="face"),
     "Material Role face appears 2 times"),
    ("material Id twice", lambda f: f["materials.json"]["materials"].append(dict(_material(f, "c_m_namida"))),
     "material Id c_m_namida appears twice"),
    ("texture slot twice", lambda f: _material(f, "cf_m_body")["textures"].append(
        dict(_material(f, "cf_m_body")["textures"][4])), "material cf_m_body repeats texture slot _liquidmask"),
    ("bake without eyeshadow alone", lambda f: _material(f, "cf_m_body")["textures"].append(
        {**_material(f, "cf_m_body")["textures"][0], "variant": "light_no_eyeshadow"}),
     "has _MainTex without eyeshadow but no dark_no_eyeshadow Variant of it"),
    ("Texture Role twice", lambda f: _material(f, "cf_m_body")["textures"][3].update(role="main"),
     "material cf_m_body repeats Texture Role main"),
    ("create texture slot twice", lambda f: _create(f, "cf_m_body")["textures"].append(
        {k: v for k, v in _create(f, "cf_m_body")["textures"][1].items() if k != "role"}),
     "material cf_m_body's create repeats texture slot _ColorMask"),
    ("create Texture Role twice", lambda f: _create(f, "cf_m_body")["textures"][1].update(role="main"),
     "material cf_m_body's create repeats Texture Role main"),
    ("create without shader", lambda f: _create(f, "ct_top_shirt").pop("shader"),
     "materials.json.materials[7].extensions.kk.create: 'shader' is missing"),
    ("mesh Id twice", lambda f: f["outfits/00/outfit.json"]["meshes"][0].update(id="o_body_a"),
     "mesh Id o_body_a appears twice"),
    ("expression twice", lambda f: f["expressions.json"]["expressions"].append(
        dict(f["expressions.json"]["expressions"][0], name=None, category="other")),
     "expression Eye Happy appears twice on mesh cf_O_face"),
    # A repeated name always comes with a target that isn't the name, so this case has two problems.
    ("Expression Name twice", lambda f: f["expressions.json"]["expressions"].append(
        dict(f["expressions.json"]["expressions"][0], target="Eye Happy 2")),
     "Expression Name Eye Happy appears twice on mesh cf_O_face", 2),
    ("collider twice", lambda f: f["physics.json"]["colliders"].append(dict(f["physics.json"]["colliders"][0])),
     "collider Col_Head appears twice"),

    # References.
    ("unknown parent", lambda f: _bone(f, "cf_j_head").update(parent="cf_j_neck_x"),
     "bone cf_j_head has unknown parent cf_j_neck_x"),
    ("unknown mesh material", lambda f: f["body.json"]["meshes"][1].update(materials=["cf_m_skin"]),
     "mesh cf_O_face uses unknown material cf_m_skin"),
    ("expression on unknown mesh", lambda f: f["expressions.json"]["expressions"][0].update(mesh="cf_O_head"),
     "expression Eye Happy is on unknown mesh cf_O_head"),
    ("target isn't the name", lambda f: f["expressions.json"]["expressions"][0].update(target="eye_happy"),
     "expression Eye Happy has target name eye_happy"),
    ("wrong category", lambda f: f["expressions.json"]["expressions"][0].update(category="mouth"),
     "expression Eye Happy has category mouth"),
    ("effects twice", lambda f: f["expressions.json"]["effects"].append(
        {"target": "Gag Heart Eyes", "hides": ["cf_O_namida_L"]}), "expression Gag Heart Eyes has two effects entries"),
    ("effect without records", lambda f: f["expressions.json"]["effects"][0].update(target="Gag Spiral Eyes"),
     "effects name expression Gag Spiral Eyes, which no record has"),
    ("hides a mesh in another Pass", lambda f: f["expressions.json"]["effects"][0].update(hides=["o_hair_b"]),
     "expression Gag Heart Eyes hides mesh o_hair_b, which isn't in its Pass"),
    ("shows a mesh without showing key", lambda f: f["expressions.json"]["effects"][0].update(shows=["cf_Ohitomi_L"]),
     "expression Gag Heart Eyes shows mesh cf_Ohitomi_L, which has no showing key"),
    ("changes unknown material", lambda f: f["expressions.json"]["effects"][0]["material_changes"][0].update(
        material="cf_m_gageye_01"), "expression Gag Heart Eyes changes unknown material cf_m_gageye_01"),
    ("sets unknown pattern", lambda f: f["expressions.json"]["effects"][0]["material_changes"][0]["textures"][0].update(
        pattern="cf_t_gageye_05"), "sets pattern cf_t_gageye_05 on _MainTex, which material cf_m_gageye_00 doesn't have"),
    ("body texture on outfit material", lambda f: f["outfits/00/outfit.json"]["body_textures"][0].update(
        material="ct_top_shirt"), "has a body texture on ct_top_shirt, which no Body Pass mesh uses"),
    ("body texture fills own slot", lambda f: f["outfits/00/outfit.json"]["body_textures"][0]["texture"].update(
        raw="_MainTex", role="main"), "body texture _MainTex on cf_m_body fills a slot that is already filled"),
    ("body texture twice", lambda f: f["outfits/00/outfit.json"]["body_textures"].append(
        dict(f["outfits/00/outfit.json"]["body_textures"][0])), "fills a slot that is already filled"),
    ("create on a material two Passes use", lambda f: f["body.json"]["meshes"][1]["materials"].append("ct_top_shirt"),
     "material ct_top_shirt has a create but is used by the Body Pass, Outfit 00, not only by an Outfit Pass"),
    ("create on an Outfit's Role material", lambda f: _material(f, "c_m_hair_00").update(
        extensions={"kk": {"create": dict(_create(f, "ct_top_shirt"))}}),
     "material c_m_hair_00 has a create but is used by Outfit 00, not only by the Body Pass"),
    ("collider on unknown bone", lambda f: f["physics.json"]["colliders"][0].update(bone="cf_j_head2"),
     "collider Col_Head refers to unknown bone cf_j_head2"),
    ("chain root unknown", lambda f: f["physics.json"]["chains"][0].update(root="cf_J_hairF"),
     "chain root refers to unknown bone cf_J_hairF"),
    ("chain collider unknown", lambda f: f["physics.json"]["chains"][0].update(colliders=["Col_Neck"]),
     "uses unknown collider Col_Neck"),
    ("chain particle unknown", lambda f: f["physics.json"]["chains"][0]["particles"][0].update(bone="x"),
     "particle refers to unknown bone x"),
]


@pytest.mark.parametrize("change, expected, count", [(c[1], c[2], c[3] if len(c) > 3 else 1) for c in CASES],
                         ids=[c[0] for c in CASES])
def test_contract_violation(build, change, expected, count):
    files = BundleBuilder().files()
    change(files)
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(build(files=files))
    assert len(caught.value.problems) == count, caught.value.problems
    assert expected in caught.value.problems[0]


def test_every_problem_is_listed(build):
    files = BundleBuilder().files()
    _bone(files, "cf_j_head").update(group="tail")
    _material(files, "cf_m_body").update(blend_mode="additive")
    files["physics.json"]["colliders"][0].pop("bound")
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(build(files=files))
    assert len(caught.value.problems) == 3
    assert "(3 problems)" in str(caught.value)


def test_missing_folder(tmp_path):
    with pytest.raises(bundle.BundleError, match="the folder doesn't exist"):
        bundle.open_bundle(tmp_path / "nothing")


def test_unfinished_export(build):
    files = BundleBuilder().files()
    del files["manifest.json"]
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(build(files=files))
    assert caught.value.problems == [
        "there is no manifest.json, so this is an unfinished export or not an Export Bundle"]


@pytest.mark.parametrize("relative, expected", [
    ("skeleton.json", "skeleton.json is missing"),
    ("outfits/00/outfit.json", "outfits/00/outfit.json is missing"),
    ("outfits/00/outfit.glb", "Pass file outfits/00/outfit.glb is missing"),
    ("textures/0002.png", "material cf_m_body texture file textures/0002.png is missing"),
    ("card.png", "the Manifest names card.png but it is missing"),
    ("textures/0017.png", "material cf_m_body's create texture file textures/0017.png is missing"),
])
def test_missing_file(build, relative, expected):
    path = build()
    (path / relative).unlink()
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(path)
    assert caught.value.problems == [expected]


def test_missing_body_texture_file(build):
    path = build()
    bt = BundleBuilder().files()["outfits/00/outfit.json"]["body_textures"][0]["texture"]["file"]
    (path / bt).unlink()
    with pytest.raises(bundle.BundleError, match=f"body texture file {bt} is missing"):
        bundle.open_bundle(path)


@pytest.mark.parametrize("content, expected", [
    (b"\xef\xbb\xbf{}", "materials.json starts with a byte order mark"),
    (b'{"materials": [', "materials.json isn't valid JSON"),
    (b'{"materials": NaN}', "materials.json isn't valid JSON (NaN isn't a JSON number)"),
    (b'{"materials": "\xff"}', "materials.json isn't UTF-8"),
    (b"[]", "materials.json: should be an object"),
])
def test_unreadable_file(build, content, expected):
    path = build()
    (path / "materials.json").write_bytes(content)
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(path)
    assert len(caught.value.problems) == 1 and caught.value.problems[0].startswith(expected)


def test_unreadable_manifest_stops_there(build):
    path = build()
    (path / "manifest.json").write_bytes(b"{")
    (path / "skeleton.json").unlink()
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(path)
    assert len(caught.value.problems) == 1 and "manifest.json isn't valid JSON" in caught.value.problems[0]


def test_unknown_fields_are_ignored(build):
    path = build()
    edit_json(path, "manifest.json", lambda d: d.update(future={"x": 1}))
    edit_json(path, "materials.json", lambda d: d["materials"][0].update(glow=2.0))
    edit_json(path, "materials.json", lambda d: d["materials"][0].update(extensions={"kk": {"later": 1}, "ac": {}}))
    b = bundle.open_bundle(path)
    assert b.warnings == ()
    assert b.materials[0].extension("kk") == {"later": 1} and b.materials[0].extension("ac") is None
