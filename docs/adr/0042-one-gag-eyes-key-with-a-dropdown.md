# One Gag eyes key, with a dropdown that picks the gag expression

The importer no longer makes one shape key per gag expression (`Gag Heart Eyes`, `Gag Spiral Eyes`, …). Body, the tears and every other Part they moved get one key, `Gag eyes`, and the gag eyes' first material gets a dropdown, `Gag expression`, listing the gag expressions by name, as the face cards' mouth card picks its mouth (issue 35). Raising `Gag eyes` shows the picked expression: its gag mesh, its texture and its animation, with the pupils and eyelines it hides.

In every Game the gag expressions move the face the same way, except Fiery Eyes, which leaves the eyes open and moves the nose line. So `Gag eyes` holds the shape most of the expressions share, and each other shape gets a correction key, `Gag eyes (Fiery Eyes)`, holding the difference, which a driver raises with `Gag eyes` while one of its expressions is picked. The groups are found from the vertices, not from names: two expressions share a shape when no vertex of any Part is more than 0.01 mm apart between them.

A dropdown (a Menu socket) can't be keyframed in Blender, so the dropdown's group also has an integer `Number` input: above 0 it picks the expression at that place in the list, for animations that switch gag expressions.

## Considered Options

- **Keep one key per expression**: what the bundle gives and the legacy importer made, but ten to thirteen keys in Body's list where only one is ever on at a time.
- **One key, with Fiery Eyes on the shared shape**: one key in the list, but Fiery Eyes would push the eyes into the head 11 mm instead of 5 and leave the nose line still.
- **One key and correction keys, picked by a dropdown (chosen)**: the game's shapes exactly, and one key the user moves; the correction keys are driven.
- **A dropdown on each of KK's three gag materials**: each would list only its own mesh's expressions, and `Gag eyes` would have to be told which mesh to show. One dropdown on the first material, which the other materials follow, is one control.

## Consequences

- Drivers read the dropdown as the number of the picked item, counting from 0 in the order the items were made. The importer makes the Menu Switch's items in the list's order, renaming the two Blender makes with the node, so the numbers are the places in the list from 0 (a test checks). Items added to the dropdown by hand aren't seen by the drivers.
- Blender doesn't re-evaluate a driver when a node socket it reads is edited, only when the socket is keyframed and the frame changes. The add-on subscribes to edits of menu and integer sockets on Blender's message bus and tags the node trees of the materials with a dropdown (`kkbp.dropdowns`), so the shape keys follow the dropdown at once. Without the add-on enabled, a file's dropdown still changes the texture on the first gag material, but the shape keys and the other materials only catch up on the next change that tags them.
- The material panel lists only what feeds the Surface output, nested by link. So `.Gag output` has an `Expression` input, first, that the dropdown feeds: it draws nothing while `Expression` is 0 and defaults to 1, so materials without a dropdown are unchanged. The panel then shows `Expression ▸ Gag expression`, one level down, as the mouth card's dropdown is. An input the shader didn't use would be greyed out. The library's `TEMPLATE_VERSION` went to 2, so a file holding the old `.Gag output` gets the new one next to it.
- The gag eyes' pick nodes are one per gag expression, not one per pattern: each shows its expression's pattern while the choice is that expression's number, so two expressions can share a pattern (SVS's `> <` and `Cartoony Wink 2`).
- Animations keyed on the old per-expression keys don't carry over to a new import.
- A bundle with no gag eye material keeps the separate keys, since there is nowhere to put the dropdown.
