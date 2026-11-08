# The importer checks bundles in its own code, not with the JSON Schemas

`open_bundle` checks each file while reading it into its dataclasses, using only the standard library: required fields, types, Id patterns, closed-set values, and every rule in [contract/README.md](../../contract/README.md) that doesn't need the `.glb` files. The JSON Schemas are still the contract. The importer's tests check every bundle the test-bundle builder writes, and the golden samples, against them with jsonschema, which is a development dependency only. The closed sets are copied from the schemas into a generated module, `bundle/_contract.py`, and a test fails when the copy is out of date.

## Considered Options

- **Validate against the schemas at runtime**: one source of truth, but Blender ships no validator for draft 2020-12 (only `fastjsonschema`, which stops at draft 7), so the add-on would have to bundle jsonschema and its compiled `rpds-py` as wheels for every platform. The schemas are also strict (`additionalProperties: false`), while the importer has to ignore unknown fields from newer minor versions, so they would need a second, loose copy anyway.
- **Hand-written checks, schemas in tests (chosen)**: no extra wheels, error messages written for users, and unknown fields are ignored as the version rules require.

## Consequences

- A schema change needs the generator run (`scripts/gen-importer-contract.sh`) and, for anything beyond a closed set, a matching change in `bundle/reader.py`. The schema tests on the builder's bundles catch a builder that drifts from the schemas, not a reader that does.
- The rules that need the `.glb` files (the glTF Validator, `extras.id`, rest poses, morph targets) are checked only by the contract tests, never on open.
- `open_bundle` also rejects a Manifest with other than one body Pass, a repeated Outfit, or an Outfit whose files aren't in its own `outfits/NN/`. The contract doesn't list these rules yet.
