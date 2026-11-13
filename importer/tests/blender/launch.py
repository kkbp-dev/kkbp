"""Runs the in-Blender tests (importer/tests/blender/) on every harness build.

    python3 importer/tests/blender/launch.py [--blender min] [pytest arguments]

Each build gets an empty Blender profile (BLENDER_USER_RESOURCES) under importer/tests/.work/
whose `user_default` extension repository holds a copy of importer/kkbp, so nothing a test does
(such as installing Pillow) touches the source tree or your own Blender settings. pytest comes from
importer/.venv, which is built from Blender's own Python; nothing is installed into Blender.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / "importer" / "tests" / ".work" / "blender-tests"
sys.path.insert(0, str(REPO / "importer" / "tests" / "harness"))
import run as harness  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--blender", action="append", help="build name from harness.toml (repeatable; default: all)")
    args, pytest_args = parser.parse_known_args()

    site = harness.venv_site_packages()
    wheel = harness.pillow_wheel()
    seen = {}
    failed = []
    for name, build in harness._builds(harness._load_config(), args.blender).items():
        if not harness._version_ok(build):
            raise SystemExit(f"Blender build '{name}' reports {build['reported']}, expected {build['version']}.x")
        same = (os.path.realpath(build["path"]), build["reported"])
        if same in seen:
            print(f"== Blender {name}: same build as {seen[same]}, skipped")
            continue
        seen[same] = name
        print(f"== Blender {name} ({build['reported']})", flush=True)
        profile = harness.addon_profile(WORK / name)
        # pytest's temporary folders go to disk beside the profile, not to /tmp (a RAM disk on some
        # machines, and a Golden Sample copy is 50-60 MB); pytest empties the folder on each run.
        basetemp = WORK / name / "tmp"
        command = [build["path"], "--background", "--factory-startup", "--python-exit-code", "1",
                   "--python", str(HERE / "runner.py"), "--", "--site", str(site), "--",
                   "--basetemp", str(basetemp), *pytest_args]
        env = {**os.environ, "BLENDER_USER_RESOURCES": str(profile), "KKBP_TEST_PILLOW_WHEEL": str(wheel)}
        if subprocess.run(command, env=env).returncode != 0:
            failed.append(name)
    if failed:
        raise SystemExit(f"In-Blender tests failed on: {', '.join(failed)}")


if __name__ == "__main__":
    main()
