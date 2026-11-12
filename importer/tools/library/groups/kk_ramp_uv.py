"""`.KK ramp uv`: where an item reads its `_AnotherRamp`: at the toon value along u, the middle of v.
The bake's fixed toon value (1 for light, 0 for dark) reads it where the game's bake does (n.h 1 and 0);
in the viewport it follows the shading. Toon shading passes through, as `.KK hair gloss uv`'s does.
Written by hand."""

NAME = '.KK ramp uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('OUTPUT', 'Toon shading', 'NodeSocketFloat')
    t.socket('INPUT', 'Toon shading', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-400, 0))
    t.make('NodeGroupOutput', 'out', (200, 0))
    t.make('ShaderNodeCombineXYZ', 'uv', (-100, 100), ins={'X': ('in', 'Toon shading'), 'Y': 0.5, 'Z': 0.0})
    t.link('uv', 'Vector', 'out', 'Vector')
    t.link('in', 'Toon shading', 'out', 'Toon shading')
    return t
