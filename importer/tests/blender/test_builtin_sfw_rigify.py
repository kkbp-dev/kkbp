"""SFW and Rigify together on the golden samples: the rig is built without the bones SFW
removes (D21)."""

import pytest

from conftest import submodule

sfw = submodule("builtin.sfw")


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_rigify_runs_on_a_character_sfw_has_trimmed(sample, golden_import):
    result, ch = golden_import(sample, hooks=["SFW", "Rigify"], options={"sfw_mode": True})
    assert {h.name: h.status for h in result.hooks} == {"SFW": "ran", "Rigify": "ran"}, result.hooks
    assert ch.rig is not None
    gone = {b.id for b in ch.bundle().skeleton.bones if b.group == sfw.NSFW_GROUP} | set(sfw.BONES)
    left = sorted(b.name for b in ch.rig.data.bones if b.name in gone or b.name[4:] in gone)  # ORG-, DEF-, MCH-
    assert not left
