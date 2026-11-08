# SVS eye whites are copies of the eyes, resting 1 mm behind them

KK and KKS draw each eye with two meshes: an eye white (`cf_m_sirome_00`, Material Role `eye_white`) and, about 1.2 mm in front of it, the pupil (`cf_m_hitomi_00`, `eye_l` or `eye_r`). SVS draws each eye with one mesh, `cf_O_hitomi_L` or `_R`, and one material, `LIF/lif_main_eye`, whose shader paints the eye white, the iris, the pupil, the highlights and the eyelid's shadow together. Its light and dark bakes were one opaque picture of the whole eye, so in Blender anything that moves the pupil, such as the Rigify Hook's eye UV warps, slid the eye white and its shadow along with it (issue 19).

So the SVS adapter gives each eye a separate eye white, shaped as KK's: a copy of the eye mesh (`cf_O_hitomi_L_white`, `_R_white`, `EyeWhites` in the AdapterKit), its vertices moved 1 mm back along their normals, with a material of its own (`cf_m_hitomi_00_L_white`, `_R_white`) that has the `eye_white` Material Role and the Opaque Blend Mode. The copy has the eye's weights and UVs, and every expression that hides the eye hides the copy too. The light and dark bakes draw the two layers apart, with the game's own shader:

- **Eye white**: the eye with its iris textures (`_Eye_mask`, `_Pipil_texture`, `_Grade_texture`, the three `_Highlight_texture_0N`) set to black. It keeps the white's two colours and the shadow gradient between them.
- **Pupil**: the shader writes an opaque colour everywhere, so the pupil's coverage comes from two more renders with both eye white colours set to black and to white. Where nothing covers the eye white, they differ by the lit white; the share of that difference left at each pixel is how much of the white shows. The colour is then solved so that the pupil laid over the eye white gives back the game's whole eye, blended in linear light as Blender blends (`LightBake.Pupil`). For the Sample Card, the coverage has to be measured in linear light: measured on the sRGB values, the recomposed eye was off by up to 74 of 255. In linear light it is off by less than 0.1 on average and 2 at the 99th percentile, in both bakes.

## Considered Options

- **One mesh, the eye white as another texture of the eye's material**: no geometry is made up, but it needs a new Texture Variant or Texture Role in the contract, and an importer template that layers two textures on two UV maps, one the UV warps leave alone.
- **A copy of the eye mesh as its eye white, made by the exporter (chosen)**: no contract change; the bundle has the shape KK's has, so the importer's `eye_white` row in the SVS Template Set, the Rigify eye groups (built from `eye_l` and `eye_r` alone), Link shape keys and the atlas tool work on SVS eyes as they do on KK's.

## Consequences

- Like the tear and gag-eye meshes ([ADR 0010](0010-tear-and-gag-meshes-rest-inside-the-head.md)), the eye whites are geometry the exporter makes on purpose: each SVS Body Pass has two meshes and two materials more than the game.
- 1 mm is short of KK's 1.2 mm median and clear of SVS's face, which is at least 2.1 mm behind the eye for the Sample Card; a face whose eye sockets sit closer to the eyes could show the face through the eye white.
- The eye white material keeps the game material's shader values and its shadow mask, but leaves out the iris textures, which draw nothing on the eye white; written twice, they would add about 3 MB to every SVS bundle.
