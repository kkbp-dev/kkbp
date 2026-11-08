"""The built-in Hooks as registered by the add-on (docs/design/hooks-and-tools.md)."""

from conftest import submodule

hooks = submodule("pipeline.hooks")
steps = submodule("pipeline.steps")
ui_options = submodule("ui.options")


def test_every_built_in_hook_is_in_the_fixed_order_and_has_a_switch():
    builtin = [h for h in hooks.registered() if h.builtin]
    ordered = hooks.builtin_in_order(steps.BUILTIN_HOOKS)  # raises if one is missing from the list
    assert [h.name for h in ordered] == [n for n in steps.BUILTIN_HOOKS if n in {h.name for h in builtin}]
    for h in builtin:
        assert h.switch is not None, f"built-in Hook {h.name} has no switch"
        assert h.source.rpartition(".builtin.")[1], f"built-in Hook {h.name} isn't in builtin/"


def test_the_panel_lists_the_built_in_hooks_in_the_order_they_run():
    names = {h.name for h in hooks.registered() if h.builtin}
    listed = [owner for owner, _ in ui_options.owners() if owner in names]
    assert listed == [n for n in steps.BUILTIN_HOOKS if n in names]
    assert listed[-1] == "Delete default scene"
