# The exporter makes vertex copies one, and mirrors the Body

A glTF vertex has one normal and one UV per UV set, so wherever a corner differs from its neighbour (a UV seam, a hard edge) the mesh holds two vertices at one place: **copies**. Blender wants one vertex with two corners. The game also writes the copies up to a few micrometres apart, and with weights and shape-key offsets that can differ, and the face and the body meet at the neck along a seam whose two sides SVS writes up to 0.026 mm apart (issue 85). The Fix body seams Hook used to merge these by distance in Blender, for the face and body only, and the user had to choose between seams and changed weights. Separately, the Body is nearly but not exactly symmetrical: most vertices are 0.1 to 100 µm from their mirror image, so Blender's X Mirror misses them in Edit Mode (issue 101).

Now the Exporter Core decides what is a copy, for every mesh of every Pass (issue 100), and mirrors the Body Pass:

1. **Welds** (`core/src/Welds.cs`) groups the vertices within 0.01 mm of each other inside one mesh, and each face vertex with the nearest body vertex of another mesh within 0.1 mm (by Material Role, so an eyeline on the face, a nail on the body or an emblem on a jacket is never grouped). Each group gets one position (the mean), one set of weights and one offset per shape key; at the neck the body's weights and shape keys win, as the face's edge is welded onto the body. Normals, tangents, UVs and colours stay per copy.
2. **Symmetry** (`core/src/Symmetry.cs`) pairs each Body Pass position with the one nearest its mirror image across X = 0, when each is the other's nearest and they are within 0.1 mm, and moves both to the halfway mirror positions; a position within 0.05 mm of X = 0 moves onto it. It works on positions, so the copies Welds made the same move together and stay the same. Positions are paired within a mesh first, then across meshes (the eyes). Shape keys and bones stay as they are.
3. The importer's two weld Steps (`steps/welds.py`) weld what the exporter made one: `weld_copies` within each mesh as it is loaded, before `build_parts` joins the meshes of a Part Role, and `weld_neck` on Body between the face and body materials. They find copies within 1 µm, enough for the glTF importer's float rounding when it skins the mesh into its bind pose, and keep every face corner's custom normal. There is no option.

Both sides follow two rules: two vertices of one triangle are never welded (that would collapse it), and the vertices of two triangles that would then be the same triangle are left apart (the back of a double-sided hair card).

## Why the distances

On the Golden Samples, 0.01 mm groups every UV-seam copy and collapses no triangle; from 0.03 mm short edges start to collapse (SVS's bra and shirt, KKS's body). The neck's pairs need 0.1 mm, which is safe only between two meshes. Symmetry's 0.1 mm covers the vertices the game wrote as mirrors with rounding; the ones farther off come from the rest pose the meshes are skinned in (ADR 0006), which isn't symmetrical, and are issue 106.

## Considered Options

- **Blender's glTF "Merge Vertices"**: it merges only vertices whose position, normal, weights and shape keys all match, and gives the merged vertex one normal, so hard edges would either stay split or lose their shading. Hair and skirts have hundreds of such copies. It also can't merge across meshes, and the neck is two.
- **A weld map in the contract** (a vertex attribute naming each copy's group): exact, but a contract change for what the positions already say once the exporter makes them the same.
- **Keep the Hook, for every Part**: the importer would go on guessing, by distance, what the game meant, with an option to turn it off.
- **The exporter makes the copies the same and the importer welds only those (chosen)**: the decisions are made once, where the game's data is, and the importer's weld has nothing to tune.

## Consequences

- `fix_seams` and the Fix body seams Hook are gone. A script that passes `fix_seams` to `import_bundle` gets an "unknown Import Option" error.
- Imported meshes have fewer vertices, and the clothes, hair and accessories are welded too, so their outlines no longer crack at UV seams and hard edges.
- A bundle from an earlier exporter imports as before except at the SVS neck, whose pairs are farther apart than 1 µm, until it is exported again.
- The exported Body Pass moves up to 0.05 mm per vertex. Its vertices more than 0.1 mm from their mirror are left, so X Mirror doesn't yet work everywhere (issue 106).
