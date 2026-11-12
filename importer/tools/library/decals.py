"""Helpers for the skin groups' decals (`groups/kk_create_*.py`, `kk_skin_overlays.py`): not a
datablock module. Written by hand."""


def decal(t, name, base, texture, texture_alpha, color, color_alpha, mask=None, location=(0, 0)):
    """mix(base, texture * color, texture alpha * colour alpha (* mask)): a create shader's decal.
    Returns the (node, output) of the result."""
    x, y = location
    amount = t.math(f'{name}.amount', 'MULTIPLY', texture_alpha, color_alpha, location=(x, y - 200))
    if mask is not None:
        amount = t.math(f'{name}.masked', 'MULTIPLY', amount, mask, location=(x + 150, y - 200))
    t.make('ShaderNodeVectorMath', f'{name}.color', (x, y), {'operation': 'MULTIPLY'},
           {'Vector': texture, 'Vector_001': color})
    t.make('ShaderNodeMix', name, (x + 300, y), {'data_type': 'RGBA'},
           {'Factor_Float': amount, 'A_Color': base, 'B_Color': (f'{name}.color', 'Vector')})
    return (name, 'Result_Color')
