"""How close an unedited edit material comes to the game (ADR 0026, issue 30).

For every editable material of the kk, kks and svs Golden Samples (copies), edit it with the profile's
default saturation, bake light and dark as Save does without saving, and compare each bake with the
bundle's own `main.light` and `main.dark`: the mean absolute difference per channel, on the
sRGB-encoded values, over pixels opaque in both. Each Game's numbers go to
`importer/tests/.work/edit-accuracy/<game>.json`; the test fails if a material is further from the
game than `importer/tests/data/edit_accuracy.json` records (with a small margin for render noise).
Re-record after a template change that brings a material closer, on the minimum build alone (the
numbers ADR 0041 gives; other builds bake a few thousandths apart, within the margin); the legacy
templates' numbers are in ADR 0041.

    python3 importer/tests/blender/launch.py -k edit_accuracy
    KKBP_RECORD_EDIT_ACCURACY=1 KKBP_BLENDER_LATEST=<the min build> python3 importer/tests/blender/launch.py -k edit_accuracy
"""

import json
import os
from pathlib import Path

import bpy
import numpy as np
import pytest

from conftest import REPO, submodule

edit_material = submodule("tools.edit_material")
bake = submodule("tools.bake")
profiles = submodule("profiles")

RECORD = REPO / "importer" / "tests" / "data" / "edit_accuracy.json"
REPORT = REPO / "importer" / "tests" / ".work" / "edit-accuracy"
MARGIN = 0.01  # bakes of the same material differ this little between runs


def _pixels(image):
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    return px.reshape(h, w, 4)


def _load(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = "sRGB"
    return image


def difference(baked, reference):
    """Mean absolute difference per channel over pixels opaque in both, after bringing the bake to
    the reference's size. Image.pixels gives an 8-bit sRGB image's values as stored (sRGB-encoded)."""
    if tuple(baked.size) != tuple(reference.size):
        baked = baked.copy()
        baked.scale(*reference.size)
    a, b = _pixels(baked), _pixels(reference)
    opaque = (a[..., 3] > 0.5) & (b[..., 3] > 0.5)
    if not opaque.any():
        return None
    return float(np.abs(a[..., :3] - b[..., :3])[opaque].mean())


def measure(ch, log=lambda *_: None):
    """{material id: {"light": d, "dark": d}} for every editable material of `ch`."""
    profile = profiles.get(ch.game)
    bundle = ch.bundle()
    out = {}
    for bm in bundle.materials:
        if edit_material.template_for(profile, bm) is None:
            continue
        light, dark = bm.texture("main", "light"), bm.texture("main", "dark")
        material = ch.material(bm.id)
        if light is None or dark is None or material is None:
            continue
        edit = edit_material.edit(ch, material, log=log)
        try:
            ref_light, ref_dark = _load(light.file), _load(dark.file)
            baked_light, baked_dark = bake.bake(ch, edit, f"accuracy {bm.id}", at_least=tuple(ref_light.size), log=log)
            out[bm.id] = {"template": edit[submodule("templates").TEMPLATE],
                          "light": difference(baked_light, ref_light), "dark": difference(baked_dark, ref_dark)}
        finally:
            edit_material.cancel(edit)
    return out


@pytest.mark.parametrize("game", ["kk", "kks", "svs"])
def test_unedited_edit_materials_bake_close_to_the_game(game, golden_import):
    numbers = measure(golden_import(game)[1])
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / f"{game}.json").write_text(json.dumps(numbers, indent=1, sort_keys=True) + "\n")

    recorded = json.loads(RECORD.read_text()) if RECORD.is_file() else {}
    if os.environ.get("KKBP_RECORD_EDIT_ACCURACY"):
        recorded[game] = {k: {"light": v["light"], "dark": v["dark"]} for k, v in numbers.items()}
        RECORD.write_text(json.dumps(recorded, indent=1, sort_keys=True) + "\n")
        return
    worse = []
    for mid, was in recorded.get(game, {}).items():
        now = numbers.get(mid)
        assert now is not None, f"{mid} is no longer measured"
        for kind in ("light", "dark"):
            if was[kind] is not None and now[kind] is not None and now[kind] > was[kind] + MARGIN:
                worse.append(f"{mid} {kind}: {now[kind]:.3f}, recorded {was[kind]:.3f}")
    assert not worse, "edit materials further from the game:\n" + "\n".join(worse)


def test_svs_clothes_composite_their_create_material(golden_import):
    """With a create material in the bundle (Schema Version 1.3), an SVS clothing edit material
    composites it in nodes rather than taking the composited texture (ADR 0050)."""
    ch = golden_import("svs")[1]
    templates = submodule("templates")
    bm = next(m for m in ch.bundle().materials if m.shader == "LIF/lif_main_cloth" and m.create is not None)
    edit = edit_material.edit(ch, ch.material(bm.id), log=lambda *_: None)
    try:
        assert templates.param(edit, "use_create").default_value == 1.0
        filled = set(edit[edit_material.FILLED])
        assert {"create_main", "create_mask", "create"} <= filled
        assert templates.param(edit, "create_main_color1").default_value[:3] != (1.0, 1.0, 1.0)
    finally:
        edit_material.cancel(edit)
