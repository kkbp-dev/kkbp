"""The Face panel in the KKBP sidebar: the face rig's emotion presets, its eye settings, and the
Face Properties sliders of the expressions no face control reaches (tools/face.py)."""

from __future__ import annotations

import bpy

from ..builtin.rigify import names
from ..character import Character
from ..tools import face
from ..translations import CONTEXT


def _rig(context):
    ch = Character.of(context.active_object) if context.active_object is not None else None
    rig = ch.rig if ch is not None else None
    return rig if face.data(rig) else None


class KKBP_OT_face_preset(bpy.types.Operator):
    bl_idname = "kkbp.face_preset"
    bl_label = "Face Preset"
    bl_description = "Poses the face as this emotion. Shift-click adds it on top of the face as it is"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.StringProperty(name="Preset", options={"HIDDEN"})
    add: bpy.props.BoolProperty(name="Add", description="Adds the preset on top of the face as it is",
                                options={"SKIP_SAVE"})

    def invoke(self, context, event):
        self.add = event.shift
        return self.execute(context)

    def execute(self, context):
        rig = _rig(context)
        if rig is None:
            return {"CANCELLED"}
        face.apply_preset(rig, self.preset, add=self.add)
        return {"FINISHED"}


class KKBP_OT_face_reset(bpy.types.Operator):
    bl_idname = "kkbp.face_reset"
    bl_label = "Reset Face"
    bl_description = "Puts every face control back and every face slider to 0"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        rig = _rig(context)
        if rig is None:
            return {"CANCELLED"}
        face.reset(rig)
        return {"FINISHED"}


class KKBP_OT_face_key(bpy.types.Operator):
    bl_idname = "kkbp.face_key"
    bl_label = "Key Face"
    bl_description = "Keys every face control and face slider at the current frame"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        rig = _rig(context)
        if rig is None:
            return {"CANCELLED"}
        face.key(rig, context.scene.frame_current)
        return {"FINISHED"}


class KKBP_PT_face(bpy.types.Panel):
    bl_idname = "KKBP_PT_face"
    bl_label = "Face"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_translation_context = CONTEXT

    @classmethod
    def poll(cls, context):
        return _rig(context) is not None

    def draw(self, context):
        row = self.layout.row(align=True)
        row.operator("kkbp.face_reset", icon="LOOP_BACK")
        row.operator("kkbp.face_key", icon="KEY_HLT")


class KKBP_PT_face_emotions(bpy.types.Panel):
    bl_label = "Emotions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_parent_id = "KKBP_PT_face"

    def draw(self, context):
        rig = _rig(context)
        layout = self.layout
        layout.prop(rig.pose.bones[names.FACE_PROPERTIES_BONE], f'["{face.STRENGTH}"]', text="Strength", slider=True)
        grid = layout.grid_flow(columns=3, even_columns=True, align=True)
        for preset in face.presets(rig):
            grid.operator("kkbp.face_preset", text=preset).preset = preset
        layout.label(text="Shift-click adds on top", icon="INFO")


class KKBP_PT_face_eyes(bpy.types.Panel):
    bl_label = "Eyes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_parent_id = "KKBP_PT_face"

    def draw(self, context):
        target = _rig(context).pose.bones[names.EYE_TARGET_BONE]
        col = self.layout.column()
        col.prop(target, '["follow_head"]', text="Target follows head", slider=True)
        col.prop(target, '["lid_follow"]', text="Lids follow gaze", slider=True)
        col.prop(target, "scale", index=0, text="Iris size")


# The expressions no face control reaches, by category, as the game names them (ADR 0004).
class KKBP_PT_face_sliders(bpy.types.Panel):
    bl_label = "More Expressions"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_parent_id = "KKBP_PT_face"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        rig = _rig(context)
        properties = rig.pose.bones[names.FACE_PROPERTIES_BONE]
        for category, keys in face.data(rig)["panel"]:
            box = self.layout.box()
            box.label(text=category)
            col = box.column(align=True)
            for key in keys:
                if key in properties:
                    col.prop(properties, f'["{key}"]', text=key, slider=True, translate=False)


operator_classes = (KKBP_OT_face_preset, KKBP_OT_face_reset, KKBP_OT_face_key)
panel_classes = (KKBP_PT_face, KKBP_PT_face_emotions, KKBP_PT_face_eyes, KKBP_PT_face_sliders)
