# Material Template

How the importer turns bundle materials into Blender materials built from KKBP's shader templates. Terms are defined in [CONTEXT.md](../../CONTEXT.md).

## Template Descriptions

- Each Material Template has a declarative Template Description:
  - which Texture Role and Texture Variant goes to which image node;
  - which named parameter maps to which node and socket, for example `"light_alpha" → ("shader", "Light image alpha")`.
- Code uses only Roles and parameter names, never node or socket strings and never input positions.
- A harness test checks every description against the library: each template, node and socket it names must exist.

## The library

- One shader template library holds the KK and SVS templates, which share node groups.
- Assets that aren't templates belong to the built-in Hooks that use them: Rigify widgets to the Rigify Hook, the face-card rig to the Face cards Hook. Each Hook owns its own asset file.
- The library is `importer/kkbp/library/library.blend`, built by `scripts/build-library.sh` from one Python module per node group and material ([ADR 0040](../adr/0040-the-library-is-built-from-code.md)). [library-from-code.md](library-from-code.md) has how. In it:
  - image nodes have role names (`tex.main.light`, `tex.alpha_mask`);
  - per-material data (image nodes, values) sits at the top level of each material and feeds group inputs;
  - every shader group has a `Hidden` input, which expressions that hide a mesh drive ([ADR 0021](../adr/0021-expressions-hide-meshes-through-their-materials.md)).
- The descriptions and sets are data in `importer/kkbp/library/`, which never imports bpy; `importer/kkbp/templates.py` is the interface below.

## Choosing a template

- The exporter writes a Blend Mode per material (`opaque`, `cutout`, `alpha`, `glasses`) in `materials.json` ([ADR 0002](../adr/0002-exporters-write-game-meaning.md)). An imported material's template is never chosen by the game's shader name; only an edit template can be ([library-from-code.md](library-from-code.md)).
- A Template Set is a selection table keyed on (Material Role, Blend Mode), plus the Template Descriptions for its templates.
- The Game Profile names its Template Set. A set can extend another and override only what differs: SVS's set extends KK's, swaps in SVS Light Dark and sets its own render methods. Both use the one Gag template ([ADR 0019](../adr/0019-one-gag-template-built-per-material.md)).
- A row can set parameter values and the render method. A material that lacks a slot its template requires (Light Dark needs `main.light`) gets the set's fallback, Transparent. A row can also name slots a material `needs` to match it; the next row is tried for a material without them. The face's first row is `KK Light Dark Face` (`SVS Light Dark Face` on SVS), which needs the bakes without eyeshadow and has an Eyeshadow parameter that fades them ([ADR 0046](../adr/0046-the-face-is-also-baked-without-its-eyeshadow.md)).
- Raw Properties a template has a slot for (`_expression`, SVS's `_Cloth_alpha_bot`) and the per-pattern values an expression sets (`_AngleSpeed`, …) are mapped to slots and parameters in the Game Profile.

## Appending and sharing

- Templates are appended into the user's file, not linked, so a `.blend` works without KKBP or with a different version installed.
- Node groups are appended once per file and shared by every material and every Character. They are not copied per material, and the Character's name is not added to them.
- Each appended group carries a `kkbp_template_version` custom property, so a later "upgrade materials" tool could swap groups in place.

## No custom template libraries

- The importer always uses the built-in library. A `.blend` in the bundle folder is never picked up, and there is no Import Option for a custom library.
- A user who wants other templates replaces them after the import with a Hook, which can bring its own `.blend` and resources.

## Interface

```python
templates.apply(ch, blender_material, bundle_material)  # pick, append/copy, set textures + parameters, tag Key and Id
templates.param(material, "light_alpha")                # the socket for a named parameter
templates.texture(material, "main", variant="light")    # the image node for a Role
templates.swap(material, "cycles")                      # used by the convert-shaders Hook
```

- The edit material tool, baking and the Convert shaders Hook all go through these functions rather than looking up nodes by name.
