"""Shown Colours (ADR 0056), for the groups in `groups/` to call: the colour inputs a shader group
draws with go through `.KK shown color`, switched by the group's `Shown colors` input, which the edit
template feeds from its `shown colors` Value node (edit_templates.begin). Not a module of its own
datablock: build.py's registry skips it.
"""

SOCKET = 'Shown colors'


def route(t, lib, *names):
    """Adds the `Shown colors` input to the group being built and puts a `.KK shown color` node
    (`shown.<name>`) between each named colour input and every node that reads it."""
    t.socket('INPUT', SOCKET, 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    tree = t.tree
    group_in = tree.nodes['in']
    x, y = group_in.location
    for row, name in enumerate(names):
        readers = [link.to_socket for link in tree.links if link.from_socket == group_in.outputs[name]]
        if not readers:
            raise RuntimeError(f"{tree.name} doesn't read its {name} input")
        node = t.make('ShaderNodeGroup', f'shown.{name}', (x + 200, y - 600 - row * 180),
                      {'node_tree': lib.group('.KK shown color'), 'hide': True},
                      {'Color': ('in', name), 'Shown': ('in', SOCKET)})
        for socket in readers:
            tree.links.new(tree.nodes[node].outputs['Color'], socket)
