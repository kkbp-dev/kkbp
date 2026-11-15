# KK and KKS create materials in the bundle

A material's `extensions.kk.create` section: what it holds, which materials carry one, and who reads it. It is in the bundle schema, the contract tests, the Core's material sections, and the KK and KKS adapter, with KK's create shaders in `shader-properties.json`. Terms are in [CONTEXT.md](../../CONTEXT.md).

## Why

In Koikatsu and Koikatsu Sunshine the game doesn't colour the body, the face, the eyes and most clothes in their rendered material. A separate **create material** (`CustomTextureCreate.matCreate`) composites an uncoloured base texture, colour and pattern masks and the Character's chosen colours into a texture. The rendered material then shows that texture as its `_MainTex`.

A rendered material's own slots hold the composited result but not what it was made from. In the KK Golden Sample, `cf_m_face_00` and `cf_m_body` have no `_Color`. `cf_m_top_inner01` has neither colours nor pattern masks.

The importer's edit material tool (D27, D37) rebuilds the game's colouring in Blender so the colours can be changed and baked again. It needs exactly those inputs.

SVS needs nothing: its shaders carry their creation inputs as ordinary slots (`_Create_main_texture`, `_Create_jm_main_skin_head`), and the importer has no SVS edit templates.

## The change

### Bundle (`contract/`)

A material in `materials.json` may carry, in its Game Extension, the create material that makes its main texture:

```json
{
  "id": "cf_m_body",
  "...": "the material as today",
  "extensions": {
    "kk": {
      "create": {
        "shader": "Custom/CreateTexture/BodySkin",
        "colors":  { "_Color": [1, 0.87, 0.79, 1], "_Color2": [...], "_Color5": [...] },
        "floats":  { "...": 0.5 },
        "vectors": {},
        "textures": [
          { "role": "main", "raw": "_MainTex", "file": "textures/0123.png", "offset": [0, 0], "scale": [1, 1] },
          { "role": "color_mask", "raw": "_ColorMask", "file": "textures/0124.png", "offset": [0, 0], "scale": [1, 1] },
          { "raw": "_Texture3", "file": "textures/0125.png", "offset": [0, 0], "scale": [1, 1] }
        ]
      }
    }
  }
}
```

The shader name above is illustrative; the adapter writes the create material's real shader name.

- `create` has the shape of a material's shader data: `shader`, `colors`, `floats`, `vectors` (keyed by Raw Property, encoded as the material's own are) and `textures` (the existing `#/$defs/texture`). It has no `id`, `name`, `role` or `blend_mode`; the material it sits on gives those.
- **Values:** every colour, float and vector property of the create material's shader, as the adapter already captures a material's.
- **Textures:** every texture slot the create material holds, by Raw Property, with its Texture Role where the shared table gives one (`_ColorMask` → `color_mask`). In addition, `_MainTex` is `CustomTextureCreate.texMain`, the uncoloured base the game colours, with role `main`. It takes the slot's place if the create material also has one. There are no `light` or `dark` variants and no patterns.
- **Which materials carry one**:

  | Create material | Material that carries it |
  |---|---|
  | `customTexCtrlBody` | the body (Material Role `body`) |
  | `customTexCtrlFace` | the face (`face`) |
  | `ctCreateEyeW` | each eye white (`eye_white`) |
  | `ctCreateEyeL`, `ctCreateEyeR` | `eye_l`, `eye_r` |
  | `ctCreateClothes[kind, i]`, `ctCreateClothesSub[kind, i]` | the first material slot of each renderer the game gives that texture, in that Outfit's Pass: `rendNormal01`, `rendAlpha01` and `rendAccessory` for `i` = 0, `rendNormal02` for 1, `rendNormal03` for 2, on the main or sub clothes component |

  A material the game doesn't composite carries none. The clothes row follows the game's `ChangeCustomClothes`, which sets each texture on `renderer.material`, the first slot only.
- A create whose materials weren't captured, such as the shoes not worn or half-off clothes without `all_variations`, is left out.
- **Where:** `extensions.kk`. It is data only KK and KKS have ([export-bundle.md](export-bundle.md#shared-core-and-game-extensions)), and it is the first Game-only field, which the rule allows because the edit material tool reads it. KKS writes it under `kk` too; `kks` stays empty.
- **Schema Version:** stays `1.0`. Changes before the first release don't bump it ([export-bundle.md](export-bundle.md#manifest)).

Schema work:

- `materials.schema.json` defines the material's `extensions` with a `kk` object allowing `create`. Other sections' Game Extensions stay empty, so the shared `common.schema.json#/$defs/extensions` keeps forbidding fields elsewhere.
- `create` reuses `#/$defs/texture` and the colour and vec4 definitions, with `additionalProperties: false`.

New rules for the contract tests (`contract/README.md`, "Rules the schemas can't express"):

- Within a `create`, `(raw, variant, pattern)` is unique. So is `(role, variant, pattern)`, as for a material's own textures, with the `overlay` exception.
- Every `create` texture `file` exists.
- A `create` sits only on a material of the Pass whose objects it colours: body, face and eyes in the Body Pass, clothes in their Outfit's Pass.

### Exporter Core (`exporters/core/`)

The Core stays game-independent. A material's Game Extension can hold a **material section**, a new Core type with the same fields as a material's shader data (shader, colours, floats, vectors, `TextureData` list). The Core writes it like the material's own: the textures' PNG bytes go into `textures/` in write order, and the section is serialised under the extension key and field name the adapter gives (`kk`, `create`). Plain `JsonObject` extensions stay as they are.

The fake adapter emits one, so the Core's tests cover it with the schemas and the new rules.

### KK and KKS adapter (`exporters/kk/`)

- Capture each create material in the table above with the same property walk `Materials.Capture` uses, plus `texMain` as `_MainTex`. Attach it to the matching materials' `kk` extension.
- Body, face and eye create materials are captured in the Body Pass. Each Outfit Pass captures its clothes' create materials, because `ctCreateClothes` reflects the Outfit being worn.
- `shader-properties.json` must list the create shaders' properties. If it doesn't yet, the shader dump the adapter already has (`dump_shaders` in the auto-export request) can produce them.
- Re-export the `kk` and `kks` golden samples. `svs` doesn't change.

### Documentation

- [export-bundle.md](export-bundle.md): "Shared core and Game Extensions" names the first Game-only field.
- [exporter-core.md](exporter-core.md): "What the adapters capture" adds create materials; "Split" adds the Core's material sections.
- `contract/README.md`: the new rules.

## How to check it is done

- The contract tests pass on all three golden samples, with the new rules.
- In the re-exported KK sample:
  - `cf_m_body` and `cf_m_face_00` carry a `create` with `_Color`, `_Color2`, a `_MainTex` texture, and the `_ColorMask` and `_Texture3`…`_Texture7` slots their create shader holds;
  - `cf_m_sirome_00`, `cf_m_sirome_00_2`, `cf_m_hitomi_00` and `cf_m_hitomi_00_2` carry theirs;
  - clothes such as `cf_m_top_inner01` carry `_Color`…`_Color3`, `_Color1_2`…`_Color3_2` and the `_PatternMask1`…`3` their create shader holds.
- The same in the KKS sample. The SVS sample has no `create`.
- Nothing else in the samples changes beyond new texture files and their numbering.

## What the importer does with it

- `bundle/` reads `create` into the material model, with its textures as ordinary texture records. `tools/gen_contract.py` and the test-bundle builder follow the schema.
- The edit material tool fills its edit templates from the material's own textures plus its `create`:
  - the base and rendered main textures;
  - the colour and pattern masks and the `_Texture3`…`_Texture7` layers;
  - the colours ([library-from-code.md](library-from-code.md) has how each template uses them).
- Bake and link hair follow.
