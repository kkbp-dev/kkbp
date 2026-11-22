"""Builds the Material Template library and the Hooks' asset files from code and tracked files
(docs/design/library-from-code.md; ADR 0040).

    blender --background --factory-startup --python importer/tools/library/build.py -- [--out DIR] [FILE ...]

Run it through scripts/build-library.sh. FILE is `library`, `rigify`, `face_cards` or `outlines`;
with none, all four. They are written into `importer/kkbp/library/`, or DIR. Each file starts empty and gets only what its table below names, and what that
needs: node groups from `groups/`, materials from `materials/`, images from
`importer/library-src/images.json`, meshes and objects from `importer/library-src/meshes/` and `scenes/`.
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

HERE = Path(__file__).resolve().parent
IMPORTER = HERE.parents[1]
SRC = IMPORTER / "library-src"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(IMPORTER / "kkbp"))
import nodes  # noqa: E402
from library import EDIT_TEMPLATES, LIBRARY, TEMPLATE_VERSION, TEMPLATES, VERSION_PROP  # noqa: E402  (no bpy)
from library import hook_assets  # noqa: E402

# --- what each file holds ------------------------------------------------------------------

# library.blend: every Material Template, and what the variants and the Gag template need although
# no template holds it (`templates.swap`, `templates.apply`, the convert-shaders Hook's EXTRAS).
LIBRARY_FAKE_GROUPS = (".Cycles", ".Cycles Classic", ".Cycles no shadows", ".Eevee Mod", ".Principled",
                       ".Light Rotation Catcher", ".SDF_Cel_Shader", ".Gag UV", ".Gag pick")
LIBRARY_FAKE_IMAGES = ("Template: Black", "Template: Body neck shadow", "Lut_TimeDay.png", "Face SDF SVS",
                       "SVS hair contact shadows mask")

# Replacements for images the legacy file had broken: name -> generated settings.
FIXED_IMAGES = {
    # V9's had size 0 x 0 and no pixels, so it drew nothing; a black image is what its name says.
    "Template: Black": {"source": "GENERATED", "colorspace": "sRGB", "alpha_mode": "STRAIGHT", "size": [4, 4],
                        "generated_type": "BLANK", "generated_color": [0.0, 0.0, 0.0, 1.0], "float": False,
                        "file_format": "PNG"},
}


# --- the library object the modules build with ---------------------------------------------

class Library:
    def __init__(self):
        self.modules = {"groups": _modules(HERE / "groups"), "materials": _modules(HERE / "materials")}
        self.images = json.loads((SRC / "images.json").read_text())
        self.images.update(FIXED_IMAGES)
        self.meshes = {}
        for path in sorted((SRC / "meshes").glob("*.json")):
            data = json.loads(path.read_text())
            self.meshes[data["name"]] = data
        self.building = []
        self.deferred = []

    # Datablocks by name, built on first use.

    def group(self, name):
        return bpy.data.node_groups.get(name) or self._build("groups", name)

    def material(self, name):
        return bpy.data.materials.get(name) or self._build("materials", name)

    def _build(self, kind, name):
        if name in self.building:
            raise RuntimeError(f"{kind} cycle: {' -> '.join(self.building + [name])}")
        module = self.modules[kind].get(name)
        if module is None:
            raise KeyError(f"no module in {kind}/ makes {name!r}")
        self.building.append(name)
        try:
            return module.build(self).owner
        finally:
            self.building.pop()

    def image(self, name):
        found = bpy.data.images.get(name)
        if found is not None:
            return found
        entry = self.images[name]
        if entry["source"] == "GENERATED":
            w, h = entry["size"]
            image = bpy.data.images.new(name, w, h, alpha=True, float_buffer=entry["float"])
            image.generated_type = entry["generated_type"]
            image.generated_color = entry["generated_color"]
            image.file_format = entry["file_format"]
        else:
            if entry.get("missing"):
                raise RuntimeError(f"image {name!r} has no file; give it an entry in FIXED_IMAGES")
            path = SRC / "images" / entry["file"]
            image = bpy.data.images.load(str(path), check_existing=False)
            image.pack()
            image.name = name
            image.filepath = "//" + entry["file"]
        image.colorspace_settings.name = entry["colorspace"]
        image.alpha_mode = entry["alpha_mode"]
        return image

    def obj(self, name):
        return bpy.data.objects[name]

    # What the modules call.

    def new_group(self, name, kind, props):
        group = bpy.data.node_groups.new(name, kind)
        if group.name != name:
            raise RuntimeError(f"group {name!r} became {group.name!r}")
        nodes.set_props(group, props)
        return nodes.Tree(self, group, group)

    def new_material(self, name, props):
        mat = bpy.data.materials.new(name)
        if mat.name != name:
            raise RuntimeError(f"material {name!r} became {mat.name!r}")
        mat.use_nodes = True
        mat.node_tree.nodes.clear()
        nodes.set_props(mat, props)
        return nodes.Tree(self, mat.node_tree, mat)

    def later(self, fn):
        self.deferred.append(fn)

    def finish(self):
        for fn in self.deferred:
            fn()
        self.deferred.clear()


def _modules(folder):
    out = {}
    for path in sorted(folder.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"kkbp_library_{folder.name}_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if module.NAME in out:
            raise RuntimeError(f"{module.NAME!r} is made by two modules in {folder.name}/")
        out[module.NAME] = module
    return out


# --- meshes, objects, armatures --------------------------------------------------------------

def _ref(lib, value):
    """JSON values back to Blender ones: {"ref": [type, name]} to a datablock, {"set": [...]} to a set."""
    if isinstance(value, dict):
        if "ref" in value:
            kind, name = value["ref"]
            return {"Object": lib.obj, "Material": lib.material, "Image": lib.image,
                    "Mesh": lambda n: bpy.data.meshes[n], "Armature": lambda n: bpy.data.armatures[n]}[kind](name)
        if "set" in value:
            return set(value["set"])
        return {k: _ref(lib, v) for k, v in value.items()}
    if isinstance(value, list):
        return tuple(_ref(lib, v) for v in value)
    return value


def build_mesh(lib, data):
    m = bpy.data.meshes.new(data["name"])
    m.vertices.add(len(data["vertices"]) // 3)
    m.vertices.foreach_set("co", data["vertices"])
    m.edges.add(len(data["edges"]) // 2)
    m.edges.foreach_set("vertices", data["edges"])
    m.loops.add(len(data["loops"]["vertex_index"]))
    m.loops.foreach_set("vertex_index", data["loops"]["vertex_index"])
    m.loops.foreach_set("edge_index", data["loops"]["edge_index"])
    m.polygons.add(len(data["polygons"]["loop_start"]))
    m.polygons.foreach_set("loop_start", data["polygons"]["loop_start"])
    for a in data["attributes"]:
        attr = m.attributes.get(a["name"]) or m.attributes.new(a["name"], a["data_type"], a["domain"])
        attr.data.foreach_set(a["key"], a["values"])
    for name, uv in data["uv_layers"].items():
        layer = m.uv_layers.new(name=name)
        layer.data.foreach_set("uv", uv["uv"])
    for name, uv in data["uv_layers"].items():
        if uv["active"]:
            m.uv_layers.active = m.uv_layers[name]
        if uv["active_render"]:
            m.uv_layers[name].active_render = True
    for name in data["materials"]:
        m.materials.append(lib.material(name) if name else None)
    nodes.set_props(m, _ref(lib, data["props"]))
    m.update()
    return m


def add_shape_keys(obj, data):
    keys = data.get("shape_keys")
    if not keys:
        return
    for block in keys["blocks"]:
        obj.shape_key_add(name=block["name"], from_mix=False)
    k = obj.data.shape_keys
    k.name = keys["name"]
    k.use_relative = keys["use_relative"]
    for block, kb in zip(keys["blocks"], k.key_blocks):
        kb.data.foreach_set("co", block["co"])
        kb.relative_key = k.key_blocks[block["relative_key"]]
        for name in ("slider_min", "slider_max", "value", "mute", "vertex_group", "interpolation"):
            setattr(kb, name, block[name])


def build_armature(lib, name, data, owner_name):
    arm = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(owner_name, arm)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    for b in data["bones"]:
        eb = arm.edit_bones.new(b["name"])
        eb.head, eb.tail, eb.roll = b["head"], b["tail"], b["roll"]
    for b in data["bones"]:
        eb = arm.edit_bones[b["name"]]
        if b["parent"]:
            eb.parent = arm.edit_bones[b["parent"]]
        eb.use_connect = b["use_connect"]
    bpy.ops.object.mode_set(mode="OBJECT")
    for c in data["collections"]:
        coll = arm.collections.new(c["name"], parent=arm.collections_all[c["parent"]] if c["parent"] else None)
        nodes.set_props(coll, _ref(lib, c["props"]))
    for b in data["bones"]:
        bone = arm.bones[b["name"]]
        nodes.set_props(bone, _ref(lib, b["props"]))
        for c in b["collections"]:
            arm.collections_all[c].assign(bone)
    nodes.set_props(arm, _ref(lib, data["props"]))
    return obj


def build_scene(lib, key):
    scene = json.loads((SRC / "scenes" / f"{key}.json").read_text())
    objects = scene["objects"]
    armature_owner = {o["data"][1]: name for name, o in objects.items() if o["type"] == "ARMATURE"}
    made = {}
    for name, arm in scene["armatures"].items():
        made[armature_owner[name]] = build_armature(lib, name, arm, armature_owner[name])
    meshes = {}
    for name, o in objects.items():
        if name in made:
            continue
        data = None
        if o["data"] is not None:
            kind, data_name = o["data"]
            if kind != "Mesh":
                raise RuntimeError(f"object {name} has {kind} data; only meshes and armatures are built")
            data = meshes.get(data_name) or build_mesh(lib, lib.meshes[data_name])
            meshes[data_name] = data
        made[name] = bpy.data.objects.new(name, data)
    for name, o in objects.items():
        obj = made[name]
        if o["type"] == "MESH" and obj.data.shape_keys is None:
            add_shape_keys(obj, lib.meshes[o["data"][1]])
        nodes.set_props(obj, _ref(lib, o["props"]))
        if o["parent"]:
            obj.parent = made[o["parent"]]
            obj.parent_type = o["parent_type"]
            obj.parent_bone = o["parent_bone"]
        obj.matrix_parent_inverse = Matrix(o["matrix_parent_inverse"])  # rows; a plain list would be columns
        for g in o["vertex_groups"]:
            obj.vertex_groups.new(name=g["name"]).lock_weight = g["lock_weight"]
        for v, groups in enumerate(o.get("weights", ())):
            for index, weight in groups:
                obj.vertex_groups[index].add([v], weight, "REPLACE")
        for slot, (link, mat) in zip(obj.material_slots, o["material_slots"]):
            slot.link = link
            if link == "OBJECT":
                slot.material = lib.material(mat) if mat else None
        for md in o["modifiers"]:
            mod = obj.modifiers.new(md["name"], md["type"])
            if md["object"]:
                mod.object = made[md["object"]]
            if md["vertex_group"]:
                mod.vertex_group = md["vertex_group"]
            nodes.set_props(mod, _ref(lib, md["props"]))
        for c in o["constraints"]:
            _constraint(lib, obj.constraints, c, made)
    for name, o in objects.items():
        for bone, p in o.get("pose", {}).items():
            pb = made[name].pose.bones[bone]
            nodes.set_props(pb, _ref(lib, p["props"]))
            for attr in ("location", "rotation_quaternion", "rotation_euler", "rotation_axis_angle", "scale"):
                setattr(pb, attr, p[attr])
            pb.custom_shape = made[p["custom_shape"]] if p["custom_shape"] else None
            if p["custom_shape_transform"]:
                pb.custom_shape_transform = made[name].pose.bones[p["custom_shape_transform"]]
            for c in p["constraints"]:
                _constraint(lib, pb.constraints, c, made)
    for name, c in scene["collections"].items():
        coll = bpy.data.collections.new(name)
        for o in c["objects"]:
            coll.objects.link(made[o])
        for attr in ("use_fake_user", "hide_viewport", "hide_render", "hide_select"):
            setattr(coll, attr, c[attr])
    for name, c in scene["collections"].items():
        for child in c["children"]:
            bpy.data.collections[name].children.link(bpy.data.collections[child])
    # The files have no scene the collections are in (ADR 0024): the Hooks append the collection.
    for obj in list(bpy.context.scene.collection.objects):
        bpy.context.scene.collection.objects.unlink(obj)


def _constraint(lib, constraints, data, made):
    c = constraints.new(data["type"])
    c.name = data["name"]
    if data["target"]:
        c.target = made[data["target"]]
    if data["subtarget"]:
        c.subtarget = data["subtarget"]
    nodes.set_props(c, _ref(lib, data["props"]))


# --- the files ------------------------------------------------------------------------------

def empty_file():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for kind in ("objects", "meshes", "materials", "node_groups", "images", "collections", "worlds", "cameras",
                 "lights"):
        for datablock in list(getattr(bpy.data, kind)):
            getattr(bpy.data, kind).remove(datablock)


OUT = None  # --out: a folder to write into instead of importer/kkbp/library/


def save(path):
    if OUT is not None:
        path = OUT / path.name
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True, copy=False)
    backup = Path(str(path) + "1")
    if backup.exists():
        backup.unlink()
    print(f"Wrote {path.name}: {path.stat().st_size / 1e6:.1f} MB, {len(bpy.data.materials)} materials, "
          f"{len(bpy.data.node_groups)} node groups, {len(bpy.data.images)} images, {len(bpy.data.objects)} objects")


def library_file():
    lib = Library()
    names = [name for name in TEMPLATES]
    for name in names:
        lib.material(name).use_fake_user = True
    for name in LIBRARY_FAKE_GROUPS:
        lib.group(name).use_fake_user = True
    for name in LIBRARY_FAKE_IMAGES:
        lib.image(name).use_fake_user = True
    lib.finish()
    for name in names:
        bpy.data.materials[name][VERSION_PROP] = TEMPLATE_VERSION
    for group in bpy.data.node_groups:
        group[VERSION_PROP] = TEMPLATE_VERSION
    if set(EDIT_TEMPLATES) - set(names):
        raise RuntimeError("an edit template isn't in TEMPLATES")
    save(LIBRARY)


def asset_file(asset, scene=None, images=(), fake_images=()):
    lib = Library()
    if scene:
        build_scene(lib, scene)
    for name in images:
        lib.image(name).use_fake_user = True
    for name in fake_images:
        lib.image(name).use_fake_user = True
    lib.finish()
    for kind in ("collections", "objects", "meshes", "armatures", "materials", "node_groups", "images"):
        for datablock in getattr(bpy.data, kind):
            datablock[hook_assets.VERSION_PROP] = hook_assets.ASSET_VERSION
    save(asset.path)


FILES = {
    "library": library_file,
    "rigify": lambda: asset_file(hook_assets.RIGIFY, scene="rigify"),
    # SVS's eye white mask isn't used in the file; the Hook appends it by name (ADR 0037).
    "face_cards": lambda: asset_file(hook_assets.FACE_CARDS, scene="face_cards",
                                     fake_images=[hook_assets.FACE_CARDS.eye_white_masks["SVS Light Dark"]]),
    "outlines": lambda: asset_file(hook_assets.OUTLINES, images=[
        hook_assets.OUTLINES.black, hook_assets.OUTLINES.placeholder, *hook_assets.OUTLINES.face_masks.values()]),
}


def main():
    global OUT
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--out" in args:
        i = args.index("--out")
        OUT = Path(args[i + 1])
        OUT.mkdir(parents=True, exist_ok=True)
        args = args[:i] + args[i + 2:]
    for key in args or FILES:
        empty_file()
        FILES[key]()


main()
