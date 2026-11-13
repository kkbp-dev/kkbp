"""What every phase of the Rigify Hook works on: one RigBuild, made by the Hook and handed to each
phase, instead of module state.

`kk_extras` says whether the KK-only parts run. It is not a Game check: it is whether the skeleton
has every joint-correction bone those parts need (ADR 0022, `prepare.kk_extras`).
"""

from __future__ import annotations

from dataclasses import dataclass

from ... import appending


@dataclass
class RigBuild:
    ctx: object
    metarig: object
    kk_extras: bool
    rig: object = None  # the generated rig, once Rigify has made it
    widgets: object = None  # the Character's copy of rigify.blend's Bone Widgets collection

    @property
    def character(self):
        return self.ctx.character

    @property
    def log(self):
        return self.ctx.log

    @property
    def body(self):
        return self.character.body

    def meshes(self) -> list:
        """The Character's meshes. (The legacy scripts scanned the scene, which reaches other
        Characters.)"""
        return [o for o in self.character.parts() if o.type == "MESH"]

    def widget(self, name):
        """The widget object `name` in the Character's widget collection."""
        return next(o for o in self.widgets.all_objects if appending.base_name(o.name) == name)

    def face_bone_names(self) -> list:
        """The face bones whose widgets the rig turns: the legacy importer listed KK's by name; they
        are the bones of the face Bone Groups outside the tongue."""
        skeleton = self.ctx.bundle.skeleton
        root = skeleton.by_role("tongue_root")
        tongue = _subtree(skeleton, root.id) if root else set()
        return [b.id for b in skeleton.bones
                if b.group in ("face", "eye", "eyebrow", "mouth") and b.id not in tongue]


def _subtree(skeleton, root_id):
    children = {}
    for b in skeleton.bones:
        children.setdefault(b.parent, []).append(b.id)
    found, todo = set(), [root_id]
    while todo:
        bone = todo.pop()
        found.add(bone)
        todo.extend(children.get(bone, ()))
    return found
