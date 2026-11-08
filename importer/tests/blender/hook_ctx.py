"""A `ctx` for calling a built-in Hook's function on a hand-built scene."""

from types import SimpleNamespace

from conftest import submodule

context = submodule("pipeline.context")
options = submodule("pipeline.options")


def fake_ctx(character, bundle=None, **option_values):
    return SimpleNamespace(character=character, bundle=bundle, options=options.Options(option_values),
                           game=character.game, log=context.ImportLog())
