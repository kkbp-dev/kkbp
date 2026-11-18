# Vertex copies are found where the mesh stores them, not where physics leaves them

[ADR 0047](0047-the-exporter-makes-vertex-copies-one-and-mirrors-the-body.md) has the Exporter Core group the vertices within 0.01 mm of each other in one mesh as copies. It grouped them by the positions the adapter writes, which are skinned through the bones as the game leaves them, and physics moves those bones on every export. On SVS's hair, MagicaCloth moved copies up to 8.5 µm relative to each other between two exports of the Sample Card, and the hair holds pairs 7 to 13 µm apart (sixteen of the back hair's at 10.06 µm). Some pairs crossed the 0.01 mm line from one export to the next, and the importer's Hair Outfit 00 came out with 8555 or 8556 vertices and 24906 to 24913 edges, so the svs.core snapshot failed at random.

Where a cluster of nearby vertices can't all be one (it would collapse a triangle), the order the pairs were joined in also decided which copies went together. The Core took them in its grid's cell order and the importer's weld in Blender's nearest-first order, and a few micrometres of movement changed both.

Now:

1. **Copies are found by the mesh's stored vertices** (`MeshData.UnposedPositions`, never written to the bundle): each vertex as the game's mesh stores it, before any shape key or bone moves it, at the renderer's scale. Each group still gets the mean of its skinned positions, so the bundle is what it was apart from which vertices are copies.
   - A readable mesh gives them from `mesh.vertices`.
   - SVS's hair and clothes are unreadable meshes, which the adapter bakes with `BakeMesh` at the current pose. The SVS adapter reads their stored vertices back from the mesh's vertex buffer on the GPU (`Mesh.GetVertexBuffer`, Unity 2021). The interop's `GraphicsBuffer.GetData(Array)` needs `Il2CppSystem.Object.GetType`, which the game's build strips, so it calls `InternalGetData`. Two exports read back the same bytes. Undoing the skinning of the baked vertices instead left up to 0.3 µm of noise in a pair's distance, too much beside pairs 0.06 µm from the line.
   - KK and KKS can't read an unreadable mesh's vertex buffer (Unity 5.6 and 2019 have no `GetVertexBuffer`), so KKS's baked clothes are grouped by their skinned positions as before. Their snapshots haven't varied.
2. **The neck still pairs by skinned positions**: the face and body are different meshes, and only their skinned positions share a space.
3. **Each vertex joins its candidates in index order**, in the Core's `Welds.GroupWithin` and in the importer's `weld_copies`, so the groups depend only on which pairs are close.

The 0.01 mm distance stays. On the Golden Samples it groups as it did on skinned positions (see below), and with stored positions that are the same on every export, a pair near the line is on the same side every time.

Measured on the Golden Samples:

- **KK and KKS** group every mesh exactly as they did on skinned positions.
- **SVS** differs only in its hair, by two vertices out of 14,511.
- **Three exports of SVS in a row** gave Hair Outfit 00 the same 8556 vertices and 24908 edges each time. With the order fix alone they gave 24906, 24908 and 24908 edges.
- **The neck:** Body's edge count moved once, from 49235 to 49237, with the new join order, and stayed there.

The importer still welds by distance (1 µm, ADR 0047), on the positions the glTF importer gives it: each group's copies arrive at one position, a few nanometres apart.
