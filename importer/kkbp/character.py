"""Finding an imported Character's Blender objects, materials and images (docs/design/character.md).

A Character holds only its Character Key. Every lookup scans the Blender data again, because undo
invalidates Python references to it. Membership is decided by the Key alone, never by names or
Collections. `add_part`, `tag_material` and `tag_image` are the only places that write the tags.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import bpy

from .bundle import Bundle, open_bundle

PART_ROLES = ("body", "hair", "outfit", "alt_outfit", "tears", "gag_eyes", "armature", "rig", "face_card", "eyes",
              "eyebrows")
# Roles a Character has at most one of.
SINGLE_ROLES = ("body", "armature", "rig", "tears", "gag_eyes")
# Roles whose Parts must name their Outfit.
OUTFIT_ROLES = ("outfit", "alt_outfit")

# Custom property names. Parts carry all but ID; materials and images carry KEY, ID and (materials) ROLE.
KEY = "kkbp_key"
ROLE = "kkbp_role"
OUTFIT = "kkbp_outfit"
NAME = "kkbp_name"
GAME = "kkbp_game"
BUNDLE = "kkbp_bundle"
ID = "kkbp_id"
SUB_COLLECTION = "kkbp_collection"  # on the Collections inside the Character's own: which one it is


class CharacterError(Exception):
    """A Character lookup can't give one clear answer."""


class BundleMissingError(CharacterError):
    """The Export Bundle a Character came from is no longer where it was imported from."""

    def __init__(self, character_name: str, path: Path):
        self.path = path
        super().__init__(f"{character_name}'s Export Bundle is no longer at {path}")


class Character:
    """One imported Character, identified by its Character Key."""

    def __init__(self, key: str, *, name: str | None = None, game: str | None = None,
                 bundle_path: str | Path | None = None):
        self.key = key
        # Character-level values for a Character with no Parts yet; add_part writes them on every Part.
        self._pending = {NAME: name, GAME: game, BUNDLE: None if bundle_path is None else str(bundle_path)}

    @classmethod
    def new(cls, name: str, game: str, bundle_path: str | Path) -> Character:
        """A Character with a new, unique Key and no Parts yet."""
        return cls(uuid.uuid4().hex, name=name, game=game, bundle_path=bundle_path)

    @classmethod
    def of(cls, obj) -> Character | None:
        """The Character `obj` belongs to, or None."""
        key = obj.get(KEY) if obj is not None else None
        return cls(key) if isinstance(key, str) else None

    @classmethod
    def all(cls, scene) -> list[Character]:
        """Every Character with a Part in `scene`, in the order their Parts appear."""
        keys = dict.fromkeys(o[KEY] for o in scene.objects if isinstance(o.get(KEY), str))
        return [cls(k) for k in keys]

    @classmethod
    def for_tool(cls, context) -> Character:
        """The Character a tool works on: the active object's, or the scene's only one."""
        ch = cls.of(context.active_object)
        if ch is not None:
            return ch
        found = cls.all(context.scene)
        if len(found) == 1:
            return found[0]
        if not found:
            raise CharacterError("There is no KKBP Character in this scene.")
        raise CharacterError("This scene has several Characters. Select an object of the one you mean.")

    def __eq__(self, other):
        return isinstance(other, Character) and other.key == self.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return f"Character({self.name!r}, key={self.key!r})"

    # --- Character-level values -------------------------------------------------------

    def _value(self, prop):
        for obj in self._objects():
            if prop in obj:
                return obj[prop]
        return self._pending[prop]

    @property
    def name(self) -> str | None:
        return self._value(NAME)

    @property
    def game(self) -> str | None:
        return self._value(GAME)

    @property
    def bundle_path(self) -> Path | None:
        value = self._value(BUNDLE)
        return None if value is None else Path(value)

    def bundle(self) -> Bundle:
        """Reopens the Export Bundle this Character was imported from."""
        path = self.bundle_path
        if path is None or not (path / "manifest.json").is_file():
            raise BundleMissingError(self.name or self.key, path)
        return open_bundle(path)  # raises BundleError if it has changed into something it can't read

    # --- Parts ------------------------------------------------------------------------

    def _objects(self):
        return [o for o in bpy.data.objects if o.get(KEY) == self.key and o.users_collection]

    def parts(self, roles=None, outfit: int | None = None) -> list:
        """This Character's Parts, optionally only those with one of `roles` or of Outfit `outfit`."""
        if isinstance(roles, str):
            roles = (roles,)
        return [o for o in self._objects()
                if (roles is None or o.get(ROLE) in roles) and (outfit is None or o.get(OUTFIT) == outfit)]

    def _one(self, role):
        found = self.parts(role)
        if len(found) > 1:
            names = ", ".join(sorted(o.name for o in found))
            raise CharacterError(f"{self.name} has {len(found)} {role} Parts ({names}); there should be one.")
        return found[0] if found else None

    body = property(lambda self: self._one("body"))
    armature = property(lambda self: self._one("armature"), doc="The deform armature from the import.")
    rig = property(lambda self: self._one("rig"), doc="The Rigify control rig, or None.")
    tears = property(lambda self: self._one("tears"))
    gag_eyes = property(lambda self: self._one("gag_eyes"))
    hairs = property(lambda self: self.parts("hair"))
    outfits = property(lambda self: self.parts("outfit"))
    alt_outfits = property(lambda self: self.parts("alt_outfit"))

    @property
    def control(self):
        """The rig if there is one, else the armature: what animation and posing tools act on."""
        return self.rig or self.armature

    def outfit(self, index: int) -> list:
        """Every Part of Outfit `index`."""
        return self.parts(outfit=index)

    def add_part(self, obj, role: str, outfit: int | None = None):
        """Makes `obj` a Part of this Character with Part Role `role`."""
        if role not in PART_ROLES:
            raise ValueError(f"{role!r} isn't a Part Role")
        if role in OUTFIT_ROLES and outfit is None:
            raise ValueError(f"a Part with role {role} needs its Outfit index")
        other = obj.get(KEY)
        if isinstance(other, str) and other != self.key:
            raise CharacterError(f"{obj.name} is already a Part of another Character")
        values = {NAME: self.name, GAME: self.game, BUNDLE: self._value(BUNDLE)}
        obj[KEY] = self.key
        obj[ROLE] = role
        if outfit is None:
            obj.pop(OUTFIT, None)
        else:
            obj[OUTFIT] = outfit
        for prop, value in values.items():
            if value is not None:
                obj[prop] = value
        return obj

    # --- the Collection -----------------------------------------------------------------

    @property
    def collection(self):
        """The Collection the import made for this Character, or None. It is there for tidiness;
        it doesn't decide which objects are Parts."""
        return next((c for c in bpy.data.collections if c.get(KEY) == self.key and SUB_COLLECTION not in c), None)

    def add_collection(self, parent):
        """Makes this Character's Collection, named after it, inside `parent`."""
        collection = bpy.data.collections.new(self.name or "Character")
        collection[KEY] = self.key
        parent.children.link(collection)
        return collection

    # --- materials and images ---------------------------------------------------------

    def tag_material(self, material, id: str, role: str | None = None):
        """Marks a Blender material as bundle material `id` (Material Role `role`) of this Character."""
        material[KEY] = self.key
        material[ID] = id
        if role is None:
            material.pop(ROLE, None)
        else:
            material[ROLE] = role
        return material

    def tag_image(self, image, id: str):
        """Marks a Blender image as belonging to this Character; `id` names it within the Character."""
        image[KEY] = self.key
        image[ID] = id
        return image

    def material(self, id: str):
        """The Blender material made from bundle material `id`, or None."""
        found = [m for m in bpy.data.materials if m.get(KEY) == self.key and m.get(ID) == id]
        if len(found) > 1:
            names = ", ".join(sorted(m.name for m in found))
            raise CharacterError(f"{self.name} has {len(found)} materials for {id} ({names}); there should be one.")
        return found[0] if found else None

    def materials(self, roles=None, parts=None) -> list:
        """This Character's materials, optionally only those with one of the Material Roles `roles`
        and/or used by its Parts with one of the Part Roles `parts`."""
        if isinstance(roles, str):
            roles = (roles,)
        found = [m for m in bpy.data.materials if m.get(KEY) == self.key]
        if roles is not None:
            found = [m for m in found if m.get(ROLE) in roles]
        if parts is not None:
            used = {slot.material for obj in self.parts(parts) for slot in obj.material_slots if slot.material}
            found = [m for m in found if m in used]
        return found

    def image(self, id: str):
        found = [i for i in bpy.data.images if i.get(KEY) == self.key and i.get(ID) == id]
        if len(found) > 1:
            raise CharacterError(f"{self.name} has {len(found)} images for {id}; there should be one.")
        return found[0] if found else None
