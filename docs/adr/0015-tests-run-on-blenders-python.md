# The importer's tests run on Blender's own Python

The host tests (pytest on `bundle/` and the source rules) run in a venv, `importer/.venv`, created from the Python interpreter inside the minimum Blender build by `scripts/setup-importer-dev.sh`. The tests that need `bpy` run pytest inside headless Blender, which loads pytest from that venv's site-packages at runtime. Nothing is installed into Blender's own Python, and Blender is never used as a Python module.

## Considered Options

- **The system Python**: no setup, but it is 3.14 on the development machine while Blender 5.2 runs 3.13, and 3.14 changed how annotations are evaluated, so a test could pass on the host and fail in Blender.
- **A separately installed CPython 3.13 (uv, pyenv)**: the right version, but one more tool to install and keep in step with Blender's patch release.
- **`bpy` from PyPI**: tests import Blender as a module, but it is a different build from the one users run and needs the exact Python version it was built for.
- **A venv from Blender's interpreter (chosen)**: the exact interpreter the add-on runs on, and the venv's packages have the right ABI for the tests inside Blender too.

## Consequences

- The venv breaks when the Blender build moves (a snap refresh changes the revision path); running the setup script again rebuilds it.
- The dev tools are pinned in `importer/requirements-dev.txt` and must have wheels for Blender's Python version.
