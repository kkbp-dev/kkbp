"""The Face Key Roles the Core Import wrote on Body's shape keys (the record_face_keys Step, from
the Game Profile): which Expression Names, at what weights, each control of the face rig drives."""

from __future__ import annotations

import json

from ... import names


class FaceKeys:
    def __init__(self, body):
        keys = body.data.shape_keys if body is not None else None
        text = keys.get(names.FACE_KEYS_PROPERTY) if keys is not None else None
        self._roles = {role: [(name, float(weight)) for name, weight in pairs]
                       for role, pairs in json.loads(text).items()} if text else {}
        self.body = body

    def __contains__(self, role):
        return role in self._roles

    def get(self, role) -> list:
        """[(Expression Name, weight)] for `role`, or [] when the Game has no key for it."""
        return list(self._roles.get(role, ()))

    def first(self, role):
        """The role's first Expression Name, or None."""
        pairs = self._roles.get(role)
        return pairs[0][0] if pairs else None
