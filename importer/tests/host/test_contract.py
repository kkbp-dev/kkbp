"""The builder's bundles and the Golden Samples against the contract's JSON Schemas, and the
importer's copy of the closed sets against the schemas it was generated from."""

import pytest

import gen_contract
import schemas
from bundle_builder import BundleBuilder
from conftest import golden


def test_generated_sets_match_the_schemas():
    assert gen_contract.TARGET.read_text(encoding="utf-8") == gen_contract.render(), \
        "bundle/_contract.py is out of date; run scripts/gen-importer-contract.sh"


@pytest.mark.parametrize("game", ["KK", "KKS", "SVS"])
def test_builder_bundles_follow_the_schemas(build, game):
    assert schemas.problems(build(BundleBuilder(game))) == []


def test_builder_bundle_with_two_outfits_follows_the_schemas(build):
    b = BundleBuilder()
    b.add_material("ct_bot_skirt", blend_mode="cutout")
    b.add_mesh("o_bot_skirt", ["ct_bot_skirt"], outfit=3, bone="cf_j_hips")
    assert schemas.problems(build(b)) == []


def test_empty_builder_bundle_follows_the_schemas(build):
    assert schemas.problems(build(BundleBuilder(empty=True))) == []


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_golden_samples_follow_the_schemas(sample):
    assert schemas.problems(golden(sample)) == []
