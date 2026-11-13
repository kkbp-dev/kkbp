"""The names in a rig fingerprint that change from run to run, and what they become. No bpy, so the
host tests check it (test_fingerprint.py); rig_fingerprint.py uses it inside Blender."""

import re

# The legacy Rigify scripts name a bone "Metarig_ID:" plus 16 random characters.
RANDOM_ID = re.compile(r"(Metarig_ID:)[A-Za-z0-9]{16}")
# Rigify writes Python set literals of bone names into its UI script, in hash order, which changes
# from run to run (PYTHONHASHSEED).
SET_LITERAL = re.compile(r"\{('[^{}]*')\}")


class Cleaner:
    """Replaces the names that change from run to run: whatever is in `replacements` (the
    Character's name and key, Rigify's rig_id), and the metarig's random id."""

    def __init__(self):
        self.replacements = {}

    def __call__(self, text):
        if not isinstance(text, str):
            return text
        for old, new in self.replacements.items():
            if old:
                text = text.replace(old, new)
        return RANDOM_ID.sub(r"\1{random}", text)


def sorted_sets(line):
    """`line` with the items of each set literal of strings sorted."""
    return SET_LITERAL.sub(lambda m: "{" + ", ".join(sorted(m.group(1).split(", "))) + "}", line)
