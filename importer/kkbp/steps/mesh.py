"""Mesh Steps: loading the Passes, making the Character's Parts, and their shape keys.

Each Pass's .glb gives one object per mesh. Every mesh becomes a Part as soon as it is loaded, with
the Part Role its materials' Material Roles give it; `build_parts` then joins each Pass's Parts of
one role into the single object the legacy importer made.
"""

from __future__ import annotations

from collections import defaultdict

import bpy

from .. import compat, mesh_loader, templates
from ..collection_colors import color
from ..editing import editing
from ..character import ID, KEY, OUTFIT, ROLE, SUB_COLLECTION

# Material Role -> Part Role, the same for every Game (docs/design/game-profile.md). The first role
# in this order that one of a mesh's materials has decides; a mesh with none is `body` in the Body
# Pass and `outfit` in an Outfit Pass. The tongue is part of Body (ADR 0039).
PART_FOR_MATERIAL_ROLE = {"tears": "tears", "gag_eyes": "gag_eyes", "hair": "hair"}

# UV sets by their index in the .glb, the same for every Game.
UV_NAMES = ("uv_main", "uv_nipple_and_shine", "uv_underhair", "uv_eyeshadow")

ARMATURE_MODIFIER = "Armature modifier"
FACE_KEYS = "kkbp_face_keys"  # on Body's shape keys: Face Key Role -> [[Expression Name, weight], ...]
COLLECTION = SUB_COLLECTION  # on the Character's sub-Collections: which one it is

# What the Character's objects are called. Names are for display only; nothing looks them up.
NAMES = {
    "body": "Body {name}",
    "armature": "Armature {name}",
    "tears": "Tears {name}",
    "gag_eyes": "Gag Eyes {name}",
    "outfit": "Outfit {outfit:02d} {name}",
    "hair": "Hair Outfit {outfit:02d} {name}",
    "alt_outfit": "{mesh} {outfit:02d} {name}",
}
# Parts that move with the face, parented to Body as the legacy importer did.
FACE_PARTS = ("tears", "gag_eyes")
# How much the SVS eyelid and eyelashes move forward (Blender -Y) so they don't clip into the eyes.
EYELID_OFFSET = 0.0005
# How much the upper eyeline moves forward off the shadow beneath it, so Blender's X Mirror can tell them
# apart (ADR 0049).
UPPER_EYELINE_OFFSET = 0.0001


def load_passes(ctx):
    """Loads every Pass's .glb into the Character's Collection and makes each mesh a Part."""
    ch, bundle = ctx.character, ctx.bundle
    for p in bundle.passes:
        loaded = mesh_loader.load(p.mesh_path, ch.collection)
        ch.add_part(loaded.armature, "armature", outfit=p.outfit)
        for mesh in p.meshes:
            obj = loaded.meshes.get(mesh.id)
            if obj is None:
                raise RuntimeError(f"{p.mesh_path.name} has no mesh {mesh.id}, which {p.data_path.name} lists")
            ch.add_part(obj, part_role(bundle, p, mesh), outfit=p.outfit)
            modifier = next(m for m in obj.modifiers if m.type == "ARMATURE")
            modifier.name = ARMATURE_MODIFIER
            modifier.show_in_editmode = modifier.show_on_cage = True
            modifier.show_expanded = False
        extra = set(loaded.meshes) - {m.id for m in p.meshes}
        if extra:
            ctx.log.warning(f"{p.mesh_path.name} has meshes {p.data_path.name} doesn't list: {', '.join(sorted(extra))}")


def part_role(bundle, p, mesh) -> str:
    if p.kind == "outfit" and mesh.alternate:
        return "alt_outfit"
    roles = {bundle.material(m).role for m in mesh.materials if bundle.material(m) is not None}
    for material_role, role in PART_FOR_MATERIAL_ROLE.items():
        if material_role in roles:
            return role
    return "body" if p.kind == "body" else "outfit"


def rename_uv_maps(ctx):
    """Names each mesh's UV maps by what they are for."""
    for obj in _meshes(ctx.character):
        for layer, name in zip(obj.data.uv_layers, UV_NAMES):
            layer.name = name


def merge_rigged_tongue(ctx):
    """Makes one tongue that has the mouth's shape keys and is weighted to the tongue bones (ADR 0020).

    The game has two copies of one tongue mesh: the head's, moved by the mouth expressions, and the
    body's rigged one, weighted to the bones under the `tongue_root` Bone Role. The head tongue takes
    the rigged one's weights by vertex index, the tongue bones move by the offset between the two,
    and the rigged copy goes. The tongues are found by their `tongue` Material Role; both are Body
    Parts, and `build_parts` joins the one left into Body (ADR 0039).
    """
    ch, bundle = ctx.character, ctx.bundle
    tongues = [o for o in _meshes(ch) if any(_role(bundle, s.material) == "tongue" for s in o.material_slots)]
    if len(tongues) < 2:
        return
    root = bundle.skeleton.by_role("tongue_root")
    chain = _subtree(bundle, root.id) if root else set()
    rigged = [t for t in tongues if _weight_share(t, chain) > 0.5]
    head = [t for t in tongues if t not in rigged]
    if len(rigged) != 1 or len(head) != 1:
        ctx.log.warning(f"Expected one head tongue and one rigged tongue, found {len(head)} and {len(rigged)}; "
                        "the tongues are left as they are")
        return
    head, rigged = head[0], rigged[0]
    if not _same_topology(head.data, rigged.data):
        ctx.log.warning(f"The rigged tongue {rigged.get('id')} doesn't match the head tongue {head.get('id')} "
                        "vertex for vertex; it is left out")
        _remove(rigged)
        return
    offset = _mean_offset(head.data, rigged.data)
    _copy_weights(rigged, head)
    _remove(rigged)
    armature = ch.armature
    with editing(armature, "EDIT"):
        for bone_id in chain:
            bone = armature.data.edit_bones.get(bone_id)
            if bone is not None:
                bone.head += offset
                bone.tail += offset
    ctx.log.info(f"Merged the rigged tongue into the head tongue; tongue bones moved by "
                 f"({offset.x:.4f}, {offset.y:.4f}, {offset.z:.4f}) m")


def build_parts(ctx):
    """Joins each Pass's Parts of one Part Role into one object, names the Character's objects and
    parents the face Parts to Body. Alternate clothes stay one Part per mesh."""
    ch = ctx.character
    groups = defaultdict(list)
    for obj in _meshes(ch):
        groups[(obj.get(ROLE), obj.get(OUTFIT))].append(obj)
    order = {m.id: i for i, m in enumerate(m for p in ctx.bundle.passes for m in p.meshes)}
    for (role, outfit), objs in groups.items():
        objs.sort(key=lambda o: order.get(o.get("id"), len(order)))
        if role == "alt_outfit":
            for obj in objs:
                obj.name = NAMES[role].format(mesh=ctx.bundle.mesh(obj.get("id")).name, outfit=outfit, name=ch.name)
            continue
        target = compat.join_meshes(objs[0], objs[1:])
        target.name = target.data.name = NAMES[role].format(outfit=outfit if outfit is not None else 0, name=ch.name)
    armature = ch.armature
    armature.name = NAMES["armature"].format(name=ch.name)
    body = ch.body
    for role in FACE_PARTS:
        part = ch.parts(role)
        if part and body is not None:
            matrix = part[0].matrix_world.copy()
            part[0].parent = body
            part[0].matrix_world = matrix


def order_material_slots(ctx):
    """Puts each Part's material slots in the bundle's order, with the lower eyeline before the
    upper ones, as the legacy importer did so the lower one draws first."""
    bundle = ctx.bundle
    order = list(dict.fromkeys(m for p in bundle.passes for mesh in p.meshes for m in mesh.materials))
    roles = {m: bundle.material(m).role for m in order}
    lower = [m for m in order if roles[m] == "eyeline_lower"]
    upper = [m for m in order if roles[m] == "eyeline_upper"]
    if lower and upper:
        for m in lower:
            order.remove(m)
        at = order.index(upper[0])
        order[at:at] = lower
    rank = {m: i for i, m in enumerate(order)}
    for obj in _meshes(ctx.character):
        _sort_slots(obj, lambda mat: rank.get(material_id(mat), len(rank)))


def order_shape_keys(ctx):
    """Orders each Part's shape keys as the legacy importer did: the basis, the gag-eye expressions
    (`Gag eyes`, ADR 0042), the rest (tears, untranslated keys), then the Eye, Mouth and Eyebrow
    expressions each in alphabetical order, and the driven keys last: the meshes' showing keys and
    the gag correction keys."""
    from . import gag

    category = {gag.GAG_KEY: "gag"}
    showing = set()
    for e in ctx.bundle.expressions.records:
        category.setdefault(e.target, e.category)
        if e.category in ("tears", "gag") and e.game_name is None:
            showing.add(e.target)
    order = {"gag": 0, "eye": 2, "mouth": 3, "eyebrow": 4}
    for obj in _meshes(ctx.character):
        keys = obj.data.shape_keys
        if keys is None:
            continue
        names = [k.name for k in keys.key_blocks][1:]
        driven = showing | set(gag.corrections(obj))

        def rank(item):
            position, name = item
            if name in driven:
                return (5, position, "")
            group = order.get(category.get(name), 1)
            return (group, position if group <= 1 else 0, name if group > 1 else "")

        wanted = [name for _, name in sorted(enumerate(names), key=rank)]
        if wanted != names:
            for name in wanted:
                compat.move_shape_key(obj, keys.key_blocks.find(name), "BOTTOM")


def record_face_keys(ctx):
    """Writes the Game Profile's Face Key Roles onto Body's shape keys, as JSON (`FACE_KEYS`), keeping
    only the Expression Names Body has: the Rigify Hook's face rig reads them there, since Hooks
    don't get the profile (ADR 0058)."""
    import json

    body = ctx.character.body
    if body is None or body.data.shape_keys is None:
        return
    have = body.data.shape_keys.key_blocks
    found, missing = {}, []
    for role, pairs in ctx.profile.face_keys.items():
        kept = [[name, weight] for name, weight in pairs if name in have]
        if kept:
            found[role] = kept
        else:
            missing.append(role)
    body.data.shape_keys[FACE_KEYS] = json.dumps(found, ensure_ascii=False, sort_keys=True)
    if missing:
        ctx.log.info(f"Body has no key for the face rig's {', '.join(sorted(missing))}")


def add_tear_controls(ctx):
    """Gives Body the tear meshes' showing keys (`Tears big`, …), in the tears Part's order. Body has no
    tear geometry, so on Body they move nothing: they are the controls `link_expression_keys` drives the
    tears Part's keys from, so the tears are keyed with the rest of the face (issue 69)."""
    ch = ctx.character
    body = ch.body
    if body is None or body.data.shape_keys is None:
        return
    showing = {e.target for e in ctx.bundle.expressions.records if e.category == "tears" and e.game_name is None}
    for obj in ch.parts("tears"):
        for key in obj.data.shape_keys.key_blocks if obj.data.shape_keys else ():
            if key.name in showing and key.name not in body.data.shape_keys.key_blocks:
                control = body.shape_key_add(name=key.name, from_mix=False)
                control.value = 0.0  # a new key starts at 1


def link_expression_keys(ctx):
    """Drives the expression keys of the tears and gag-eye Parts from Body's keys of the same name,
    so one slider on Body moves the whole face."""
    ch = ctx.character
    body = ch.body
    if body is None or body.data.shape_keys is None:
        return
    source = body.data.shape_keys
    for obj in ch.parts(FACE_PARTS):
        keys = obj.data.shape_keys
        if keys is None:
            continue
        for key in list(keys.key_blocks)[1:]:
            if key.name in source.key_blocks:
                for prop in ("value", "mute"):
                    _single_prop_driver(key, prop, source, f'key_blocks["{_quote(key.name)}"].{prop}')


def drive_showing_keys(ctx):
    """Shows each tear and gag-eye mesh while an expression that `shows` it is on (ADR 0010). Once
    the gag keys are one key, `drive_gag_eyes` drives what the gag expressions show (ADR 0042). A
    showing key Body has (the tears', `add_tear_controls`) is the user's to move and gets no driver."""
    from . import gag

    ch, bundle = ctx.character, ctx.bundle
    showing_key = {e.mesh: e.target for e in bundle.expressions.records
                   if e.category in ("tears", "gag") and e.game_name is None}
    combined = set(gag.gag_expressions(bundle)) if _part_with_key(ch, _meshes(ch), gag.GAG_KEY) else set()
    by_mesh = defaultdict(list)
    for effect in bundle.expressions.effects:
        if effect.target in combined:
            continue
        for mesh in effect.shows:
            by_mesh[mesh].append(effect.target)
    for mesh, targets in by_mesh.items():
        key_name = showing_key.get(mesh)
        if _part_with_key(ch, [p for p in (ch.body,) if p], key_name):
            ctx.log.info(f"Mesh {mesh}'s showing key {key_name} is moved from Body, so {', '.join(targets)} "
                         f"don't show it")
            continue
        part = _part_with_key(ch, ch.parts(("tears", "gag_eyes")), key_name)
        if part is None:
            ctx.log.warning(f"Mesh {mesh}'s showing key {key_name} wasn't found")
            continue
        sources = [(t, _expression_owner(ch, t)) for t in targets]
        missing = [t for t, owner in sources if owner is None]
        if missing:
            ctx.log.warning(f"Expressions {', '.join(missing)} weren't found, so they don't show {mesh}")
        sources = [(t, owner) for t, owner in sources if owner is not None]
        if sources:
            key = part.data.shape_keys.key_blocks[key_name]
            add_driver(key, "value", [(owner.data.shape_keys, f'key_blocks["{_quote(t)}"].value') for t, owner in sources],
                       lambda names: f"1 if {' + '.join(names)} > 0 else 0")


def move_eyelids_forward(ctx):
    """Moves the eyelid and eyelash vertices forward a little, so they don't clip into the eyes."""
    ch, bundle = ctx.character, ctx.bundle
    for obj in _meshes(ch):
        slots = {i for i, s in enumerate(obj.material_slots)
                 if _role(bundle, s.material) in ("eyelid", "eyelash")}
        if not slots:
            continue
        mesh = obj.data
        verts = {v for p in mesh.polygons if p.material_index in slots for v in p.vertices}
        layers = [mesh.vertices] + ([k.data for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [])
        for layer in layers:
            for v in verts:
                layer[v].co.y -= EYELID_OFFSET


def move_upper_eyeline_forward(ctx):
    """Moves the upper eyeline forward off its shadow (ADR 0049). KK and KKS draw the eyeline's shadow
    as a second copy of the upper eyeline, at exactly the same place, and Blender's X Mirror can pair a
    place with only one vertex. Only a mesh with both an `eyeline_upper` and an `eyeline_shadow` material
    moves, and only the vertices the upper eyeline uses alone."""
    ch, bundle = ctx.character, ctx.bundle
    for obj in _meshes(ch):
        roles = [_role(bundle, s.material) for s in obj.material_slots]
        if "eyeline_upper" not in roles or "eyeline_shadow" not in roles:
            continue
        mesh = obj.data
        upper = {i for i, r in enumerate(roles) if r == "eyeline_upper"}
        mine = {v for p in mesh.polygons if p.material_index in upper for v in p.vertices}
        others = {v for p in mesh.polygons if p.material_index not in upper for v in p.vertices}
        verts = mine - others
        layers = [mesh.vertices] + ([k.data for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [])
        for layer in layers:
            for v in verts:
                layer[v].co.y -= UPPER_EYELINE_OFFSET


def arrange_collections(ctx):
    """Puts each Outfit's Parts in an `Outfit NN` Collection (all but the first Outfit hidden), its
    alternate clothes in a hidden `Alts NN` one, and the tears and gag eyes in their own."""
    ch = ctx.character
    root = ch.collection
    outfits = sorted({o.get(OUTFIT) for o in ch.parts(("outfit", "hair", "alt_outfit"))})
    first = outfits[0] if outfits else None
    for index in outfits:
        name = f"Outfit {index:02d} {ch.name}"
        collection = color(child_collection(root, name), "outfit")
        collection[OUTFIT] = index  # the Collection that shows the Outfit (outfit_textures.py)
        move_to_collection(ch.parts(("outfit", "hair"), outfit=index), collection, hide=index != first)
        alts = ch.parts("alt_outfit", outfit=index)
        if alts:
            alts_collection = color(child_collection(root, f"Alts {index:02d} {ch.name}"), "alts")
            move_to_collection(alts, alts_collection, hide=True)
    face = ch.parts(("tears", "gag_eyes"))
    if face:
        face_collection = color(child_collection(root, f"Tears and gag eyes {ch.name}"), "face")
        move_to_collection(face, face_collection, hide=False)


# --- helpers ------------------------------------------------------------------------------

def add_driver(owner, prop, targets, expression):
    """A scripted driver on `owner.prop` reading each (id, data_path) target as a variable."""
    names = [_var(i) for i in range(len(targets))]
    fcurve = owner.driver_add(prop)
    driver = fcurve.driver
    driver.type = "SCRIPTED"
    for v in list(driver.variables):
        driver.variables.remove(v)
    for name, (id_block, path) in zip(names, targets):
        var = driver.variables.new()
        var.name = name
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = ("KEY" if isinstance(id_block, bpy.types.Key)
                                  else "MATERIAL" if isinstance(id_block, bpy.types.Material) else "OBJECT")
        var.targets[0].id = id_block
        var.targets[0].data_path = path
    driver.expression = expression(names)
    return fcurve


def drive_param(ch, mat, name, targets, expression, start=0, keep=False):
    """Drives the material's parameter `name` from `targets`, on a property of each of the Character's
    objects that uses the material, which the material reads (`templates.read_from_objects`, issue 70).
    Returns the drivers."""
    prop = templates.read_from_objects(mat, name, keep)
    drivers = []
    for obj in ch.parts():
        if obj.type == "MESH" and any(s.material == mat for s in obj.material_slots):
            obj[prop] = float(start)
            drivers.append(add_driver(obj, f'["{prop}"]', targets, expression))
    return drivers


def _single_prop_driver(owner, prop, key, path):
    fcurve = owner.driver_add(prop)
    driver = fcurve.driver
    driver.type = "AVERAGE"
    for v in list(driver.variables):
        driver.variables.remove(v)
    var = driver.variables.new()
    var.name = "value"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "KEY"
    var.targets[0].id = key
    var.targets[0].data_path = path


def _var(i):
    """Driver variable names: a, b, ... z, aa, ab, ..."""
    letters = "abcdefghijklmnopqrstuvwxyz"
    return letters[i] if i < 26 else letters[i // 26 - 1] + letters[i % 26]


def _quote(name):
    return name.replace("\\", "\\\\").replace('"', '\\"')


def _expression_owner(ch, target):
    """The Part whose shape key `target` drives the expression: Body if it has the key."""
    return _part_with_key(ch, [p for p in (ch.body,) if p] + ch.parts(FACE_PARTS), target)


def _part_with_key(ch, parts, name):
    for obj in parts:
        if name and obj.data.shape_keys and name in obj.data.shape_keys.key_blocks:
            return obj
    return None


def material_id(material):
    """The bundle Id of a Blender material: its tag once a template is applied, the glTF Id before."""
    if material is None:
        return None
    return material.get(ID) or material.get("id")


def _role(bundle, material):
    m = bundle.material(material_id(material)) if material is not None else None
    return m.role if m else None


def _meshes(ch):
    return [o for o in ch.parts() if o.type == "MESH"]


def _subtree(bundle, root_id):
    children = defaultdict(list)
    for b in bundle.skeleton.bones:
        children[b.parent].append(b.id)
    found, todo = set(), [root_id]
    while todo:
        bone = todo.pop()
        found.add(bone)
        todo.extend(children[bone])
    return found


def _weight_share(obj, bones):
    """How much of the object's weight is on `bones`, from 0 to 1."""
    names = {g.index: g.name in bones for g in obj.vertex_groups}
    total = on = 0.0
    for v in obj.data.vertices:
        for g in v.groups:
            total += g.weight
            if names.get(g.group):
                on += g.weight
    return on / total if total else 0.0


def _same_topology(a, b):
    if len(a.vertices) != len(b.vertices) or len(a.polygons) != len(b.polygons):
        return False
    return all(tuple(p.vertices) == tuple(q.vertices) for p, q in zip(a.polygons, b.polygons))


def _mean_offset(a, b):
    from mathutils import Vector
    total = Vector((0.0, 0.0, 0.0))
    for va, vb in zip(a.vertices, b.vertices):
        total += va.co - vb.co
    return total / max(1, len(a.vertices))


def _copy_weights(source, target):
    """Gives each of `target`'s vertices exactly the vertex-group weights of `source`'s vertex with
    the same index."""
    for group in target.vertex_groups:
        group.remove(range(len(target.data.vertices)))
    names = {g.index: g.name for g in source.vertex_groups}
    for v in source.data.vertices:
        for g in v.groups:
            name = names[g.group]
            group = target.vertex_groups.get(name) or target.vertex_groups.new(name=name)
            group.add([v.index], g.weight, "REPLACE")


def _remove(obj):
    mesh = obj.data
    materials = [m for m in mesh.materials if m]
    bpy.data.objects.remove(obj)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
    for m in materials:
        if m.users == 0:
            bpy.data.materials.remove(m)


def _sort_slots(obj, key):
    """Reorders the object's material slots by `key(material)`, keeping each face's material."""
    mesh = obj.data
    materials = list(mesh.materials)
    new_order = sorted(range(len(materials)), key=lambda i: (key(materials[i]), i))
    if new_order == list(range(len(materials))):
        return
    old_to_new = {old: new for new, old in enumerate(new_order)}
    indices = [0] * len(mesh.polygons)
    mesh.polygons.foreach_get("material_index", indices)
    mesh.materials.clear()
    for old in new_order:
        mesh.materials.append(materials[old])
    mesh.polygons.foreach_set("material_index", [old_to_new[i] for i in indices])
    mesh.update()


def child_collection(parent, name):
    """The Character's sub-Collection `name` under `parent`, made on first use."""
    for c in parent.children:
        if c.get(COLLECTION) == name:
            return c
    c = bpy.data.collections.new(name)
    c[KEY] = parent.get(KEY)
    c[COLLECTION] = name
    parent.children.link(c)
    return c


def move_to_collection(objs, collection, hide):
    for obj in objs:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    layer = _layer_collection(bpy.context.view_layer.layer_collection, collection)
    if layer is not None:
        layer.hide_viewport = hide
    collection.hide_render = hide


def _layer_collection(layer, collection):
    if layer.collection == collection:
        return layer
    for child in layer.children:
        found = _layer_collection(child, collection)
        if found is not None:
            return found
    return None
