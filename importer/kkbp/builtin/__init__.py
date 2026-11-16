"""The built-in Hooks (docs/design/hooks-and-tools.md). Importing this package registers them.

Each module registers one Hook with `kkbp.hook` and its switch. The order they run in is
`BUILTIN_HOOKS` in pipeline/steps.py, not the order they are imported in. Built-in Hooks never read
ctx.game and don't get the Game Profile: what they need comes from the bundle's Roles, Groups and
Names, Character and the templates module. A bone name a legacy script needed, with no Role or Group
that marks the bone, is written in the Hook with a note on why.
"""

from . import default_scene  # noqa: E402,F401
from . import shaders  # noqa: E402,F401
from . import separate  # noqa: E402,F401
from . import outlines  # noqa: E402,F401
from . import face_cards  # noqa: E402,F401
from . import sfw  # noqa: E402,F401
from . import rigify  # noqa: E402,F401
from . import separate_eyes  # noqa: E402,F401
