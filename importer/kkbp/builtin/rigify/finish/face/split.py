"""Left and right halves of a symmetric shape key: copies whose offsets fade out across the face's
middle, so a control on one side moves only that side (`<key> (L)` and `<key> (R)`). The
Character's left is +X."""

from __future__ import annotations

import numpy as np

BLEND = 0.008  # metres either side of the middle over which a half fades out


def halves(body, name, blend=BLEND) -> tuple:
    """Adds `name (L)` and `name (R)`, once, and returns their names; () if Body has no `name`."""
    blocks = body.data.shape_keys.key_blocks
    if name not in blocks:
        return ()
    n = len(body.data.vertices)
    basis = np.empty(n * 3)
    blocks[0].data.foreach_get("co", basis)
    source = np.empty(n * 3)
    blocks[name].data.foreach_get("co", source)
    basis, source = basis.reshape(n, 3), source.reshape(n, 3)
    t = np.clip((basis[:, 0] + blend) / (2 * blend), 0.0, 1.0)
    left = t * t * (3 - 2 * t)  # smoothstep: 0 on the right, 1 on the left
    made = []
    for side, weight in (("L", left), ("R", 1.0 - left)):
        half = f"{name} ({side})"
        if half not in blocks:
            key = body.shape_key_add(name=half, from_mix=False)
            key.value = 0.0  # a new key starts at 1
            key.data.foreach_set("co", (basis + (source - basis) * weight[:, None]).ravel())
        made.append(half)
    return tuple(made)
