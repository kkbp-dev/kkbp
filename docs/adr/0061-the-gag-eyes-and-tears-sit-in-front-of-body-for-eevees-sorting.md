# The gag eyes and tears sit in front of Body for Eevee's sorting

In KK and KKS, the gag eyes and the tears are Blended, like the eyes, eye whites and eyelines on Body. Eevee draws Blended objects from the farthest origin to the nearest. The Gag Eyes and Tears Parts are parented to Body and have exactly Body's origin, so the order is a tie, and Eevee can draw Body's eyes over them. The gag expressions that close or cover the eyes hide this. Fiery Eyes leaves them open, and its flames stayed behind the eyes whether it was picked on the dropdown or on the face board.

`draw_face_parts_in_front` (`steps/mesh.py`) gives each Part a delta location forward (Blender -Y): Gag Eyes 0.1 mm and Tears 0.2 mm. The tears draw over the gag eyes, and both draw over Body. The delta location belongs to the Part, so it follows Body when the Character moves or turns, and clearing the location (Alt+G) keeps it. Every Game runs the step. SVS's gag eyes are Dithered and don't need it, and the offset is too small to see.

## Considered Options

- **A smaller offset, such as 1 µm**: this works with the Character at the world origin. Rendered 50 m away, the flames were hidden again, because the origins' distances are floats and 1 µm is lost to rounding there. 0.1 mm still worked at 50 m.
- **Moving the meshes' vertices forward**, like the upper eyeline (ADR 0049): this doesn't change the origin, which is what Eevee sorts by.
- **Delta location (chosen)**: it changes only the origin used for sorting, and it leaves the location free for the user.

## Consequences

- From behind the head the order is reversed, but there the face hides both Parts.
- An object a user adds with the same origin as Body still ties with it.
