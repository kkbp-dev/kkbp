"""Runs the in-Blender tests (importer/tests/blender/) on every harness build.

    python3 importer/tests/blender/launch.py [--blender min] [--serial] [pytest arguments]

Each build gets an empty Blender profile (BLENDER_USER_RESOURCES) under importer/tests/.work/
whose `user_default` extension repository holds a copy of importer/kkbp, so nothing a test does
(such as installing Pillow) touches the source tree or your own Blender settings. pytest comes from
importer/.venv, which is built from Blender's own Python; nothing is installed into Blender.

The builds run at the same time, each writing its output to
importer/tests/.work/blender-tests/<build>/pytest.log, which is printed when the build ends.
With one build, or `--serial`, they run one after another with their output as it happens.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / "importer" / "tests" / ".work" / "blender-tests"
sys.path.insert(0, str(REPO / "importer" / "tests" / "harness"))
import run as harness  # noqa: E402


def main():
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--blender", action="append", help="build name from harness.toml (repeatable; default: all)")
    parser.add_argument("--serial", action="store_true", help="one build after another, output as it happens")
    args, pytest_args = parser.parse_known_args()

    site = harness.venv_site_packages()
    wheel = harness.pillow_wheel()
    builds = _distinct(args.blender)
    if args.serial or len(builds) == 1:
        failed = [name for name, build in builds if not _run_serial(name, build, site, wheel, pytest_args)]
    else:
        failed = _run_together(builds, site, wheel, pytest_args)
    if failed:
        raise SystemExit(f"In-Blender tests failed on: {', '.join(failed)}")


def _distinct(names):
    """[(name, build)] in config order, less builds that are the same binary and version as an earlier one."""
    seen, out = {}, []
    for name, build in harness._builds(harness._load_config(), names).items():
        if not harness._version_ok(build):
            raise SystemExit(f"Blender build '{name}' reports {build['reported']}, expected {build['version']}.x")
        same = (os.path.realpath(build["path"]), build["reported"])
        if same in seen:
            print(f"== Blender {name}: same build as {seen[same]}, skipped")
            continue
        seen[same] = name
        out.append((name, build))
    return out


def _command(name, build, site, wheel, pytest_args):
    """The command and environment for one build's run, with a fresh profile."""
    profile = harness.addon_profile(WORK / name)
    # pytest's temporary folders go to disk beside the profile, not to /tmp (a RAM disk on some
    # machines, and a Golden Sample copy is 50-60 MB); pytest empties the folder on each run. Each
    # build has its own, so the builds can run at the same time.
    basetemp = WORK / name / "tmp"
    command = [build["path"], "--background", "--factory-startup", "--python-exit-code", "1",
               "--python", str(HERE / "runner.py"), "--", "--site", str(site), "--",
               "--basetemp", str(basetemp), *pytest_args]
    env = {**os.environ, "BLENDER_USER_RESOURCES": str(profile), "KKBP_TEST_PILLOW_WHEEL": str(wheel)}
    return command, env


def _run_serial(name, build, site, wheel, pytest_args):
    print(f"== Blender {name} ({build['reported']})")
    command, env = _command(name, build, site, wheel, pytest_args)
    return subprocess.run(command, env=env).returncode == 0


def _run_together(builds, site, wheel, pytest_args):
    """Starts every build at once and prints each one's log, in config order, as it ends. Returns the
    names of the builds that failed."""
    running = []
    for name, build in builds:
        command, env = _command(name, build, site, wheel, pytest_args)
        log = WORK / name / "pytest.log"
        log_file = open(log, "w", encoding="utf-8")
        process = subprocess.Popen(command, env=env, stdout=log_file, stderr=subprocess.STDOUT)
        running.append((name, build, log, log_file, process, time.monotonic()))
        print(f"== Blender {name} ({build['reported']}): started, output in {harness._rel(log)}")
    failed = []
    for name, build, log, log_file, process, started in running:
        code = process.wait()
        log_file.close()
        print(f"== Blender {name} ({build['reported']}): {'passed' if code == 0 else 'FAILED'}"
              f" after {round(time.monotonic() - started)} s")
        print(log.read_text(encoding="utf-8", errors="replace"), end="")
        if code != 0:
            failed.append(name)
    return failed


if __name__ == "__main__":
    main()
