"""The Golden Samples in contract/samples/ are the full regression set for bundle/. Each developer
exports their own from the Sample Cards, so a Game with no Golden Sample is skipped."""

import json
import subprocess
import sys

import pytest

import bundle
from conftest import ADDON, SAMPLES, golden

GAMES = {"kk": "KK", "kks": "KKS", "svs": "SVS"}


@pytest.fixture(scope="module", params=sorted(GAMES))
def sample(request):
    return request.param, bundle.open_bundle(golden(request.param))


def _json(sample_id, relative):
    return json.loads((SAMPLES / sample_id / relative).read_text(encoding="utf-8"))


def test_opens_without_warnings(sample):
    sample_id, b = sample
    assert b.game == GAMES[sample_id]
    assert b.warnings == ()


def test_reads_every_record(sample):
    sample_id, b = sample
    assert len(b.skeleton.bones) == len(_json(sample_id, "skeleton.json")["bones"])
    assert len(b.materials) == len(_json(sample_id, "materials.json")["materials"])
    expressions = _json(sample_id, "expressions.json")
    assert len(b.expressions.records) == len(expressions["expressions"])
    assert len(b.expressions.effects) == len(expressions["effects"])
    physics = _json(sample_id, "physics.json")
    assert (len(b.physics.chains), len(b.physics.colliders)) == (len(physics["chains"]), len(physics["colliders"]))
    for p in b.passes:
        assert len(p.meshes) == len(_json(sample_id, p.data_path.relative_to(b.path).as_posix())["meshes"])


def test_roles_the_importer_relies_on(sample):
    _, b = sample
    for role in ("body_root", "hips", "head", "left_eye", "right_eye"):
        assert b.skeleton.by_role(role) is not None, role
    for role in ("body", "face", "hair"):
        assert b.materials_with_role(role), role
    assert [p.kind for p in b.passes] == ["body", "outfit"]


def test_opening_never_loads_bpy():
    games = [g for g in sorted(GAMES) if (SAMPLES / g / "manifest.json").is_file()]
    if not games:
        pytest.skip("no Golden Sample; make them with scripts/export-sample.sh")
    code = (f"import sys; sys.path.insert(0, {str(ADDON)!r}); import bundle\n"
            f"for g in {games!r}: bundle.open_bundle({str(SAMPLES)!r} + '/' + g)\n"
            "assert 'bpy' not in sys.modules, 'bundle/ loaded bpy'")
    subprocess.run([sys.executable, "-c", code], check=True)


def test_create_materials(sample):
    sample_id, b = sample
    creates = {m.id: m.create for m in b.materials if m.create is not None}
    assert len(creates) == {"kk": 14, "kks": 12, "svs": 7}[sample_id]
    if sample_id == "svs":
        # SVS's create shaders name their own slots; the body, face and every clothing material have one.
        assert all(m.create for role in ("body", "face") for m in b.materials_with_role(role))
        assert {c.shader for c in creates.values()} == {"LIF/lif_create_main_skin_body", "LIF/lif_create_main_skin_head",
                                                        "LIF/lif_create_main_cloth"}
        for create in creates.values():
            assert all(t.file.is_file() for t in create.textures)
    elif creates:
        for role in ("body", "face", "eye_white", "eye_l", "eye_r"):
            assert all(m.create for m in b.materials_with_role(role)), role
        for create in creates.values():
            assert create.texture("main") is not None and create.texture("main").file.is_file()
