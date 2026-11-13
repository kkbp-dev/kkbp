"""Headless Blender test harness.

    python3 importer/tests/harness/run.py builds
    python3 importer/tests/harness/run.py core [--sample kk] [--blender min] [--keep-blend] [--update]
    python3 importer/tests/harness/run.py hooks [--sample kk] [--update] [--each] [--hook NAME]

`builds` lists the configured Blender builds and checks their versions.

`core` imports each Golden Sample in contract/samples/ with the Core Import (hooks=[]) on every
build and compares its scene summary with the reviewed snapshot,
importer/tests/snapshots/<sample>.core.json (D50): names exactly, positions within 1 mm, and the
bones physics moves within 3.5 cm (physics.py, ADR 0031). `--update` rewrites the snapshots from the
first build, then checks the other builds against them; review the diff before committing it. It
fails if an import fails or a summary differs. A Game in contract/sample-cards/ with no Golden
Sample is skipped with a notice (make it with scripts/export-sample.sh).

`hooks` imports each Golden Sample with the Core Import followed by every built-in Hook, with the
Import Options' defaults, compares with snapshots/<sample>.defaults.json in the same way, and fails
if an import or a Hook fails or a summary differs. With `--each` it imports once per Hook instead,
with only that Hook (`hooks=[that one]`) switched on, once per choice for a choice switch, and fails
if the Hook changes anything in the summary it doesn't own (hook_owns.py); the reports go to
importer/tests/.work/hooks/.

Each run gets its own Blender profile (BLENDER_USER_RESOURCES) and its own copy of the
sample, so the user's Blender settings and the sample folders are never touched.
Working files go to importer/tests/.work/.
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # importer/tests: bundle_copy
import compare  # noqa: E402
import physics  # noqa: E402
from bundle_copy import copy_bundle  # noqa: E402

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parents[2]
WORK = REPO / "importer" / "tests" / ".work"
# The reviewed snapshots (D50): <sample>.core.json and <sample>.defaults.json.
SNAPSHOTS = REPO / "importer" / "tests" / "snapshots"
GOLDEN = REPO / "contract" / "samples"  # the Golden Samples, made locally (ADR 0031)
SAMPLE_CARDS = REPO / "contract" / "sample-cards"
VENV = REPO / "importer" / ".venv"
ADDON = REPO / "importer" / "kkbp"
TIMEOUT_SECONDS = 1800

# Run details that change every time; left out of snapshots so updates diff cleanly.
VOLATILE_RUN_KEYS = ("seconds",)


def main():
    # Print each line as it happens, also when piped or run in the background.
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("builds", help="list Blender builds and check their versions")
    for name, help in (("core", "import the Golden Samples with the Core Import"),
                       ("hooks", "import the Golden Samples with the built-in Hooks")):
        cmd = sub.add_parser(name, help=help)
        cmd.add_argument("--sample", action="append", help="Golden Sample (repeatable; default: all)")
        cmd.add_argument("--blender", action="append", help="build name (repeatable; default: all)")
        cmd.add_argument("--keep-blend", action="store_true", help="save each imported scene as a .blend in .work/")
        cmd.add_argument("--jobs", type=int, default=2, help="Blender processes at once (default 2)")
        cmd.add_argument("--update", action="store_true", help="rewrite the snapshots from this run (review the diff)")
        if name == "hooks":
            cmd.add_argument("--each", action="store_true", help="run each Hook on its own and check what it changes")
            cmd.add_argument("--hook", action="append", help="with --each: only this Hook (repeatable)")
    args = parser.parse_args()

    config = _load_config()
    if args.command == "builds":
        return _cmd_builds(config)
    if not args.sample:
        for game in missing_samples():
            print(f"notice: no Golden Sample for {game}, so it is skipped; make it with scripts/export-sample.sh {game}")
        if not golden_samples():
            print("No Golden Samples in contract/samples/; make them with scripts/export-sample.sh")
            return 1
    if args.command == "core":
        return _cmd_core(config, args)
    return _cmd_hooks_each(config, args) if args.each else _cmd_hooks(config, args)


# --- configuration ----------------------------------------------------------------------

def _load_config():
    with open(HARNESS / "harness.toml", "rb") as f:
        return tomllib.load(f)


def _path(value):
    path = Path(os.path.expanduser(value))
    return path if path.is_absolute() else REPO / path


def _builds(config, names=None):
    """Resolve the configured builds. Returns {name: {path, version, ...}} in config order."""
    out = {}
    for name, build in config["blender"].items():
        if names and name not in names:
            continue
        path = os.environ.get(f"KKBP_BLENDER_{name.upper()}") or build["path"]
        resolved = shutil.which(os.path.expanduser(path)) or os.path.expanduser(path)
        out[name] = {**build, "path": resolved, "reported": _blender_version(resolved)}
    unknown = set(names or ()) - set(out)
    if unknown:
        raise SystemExit(f"Unknown Blender build(s): {', '.join(sorted(unknown))}")
    return out


def _blender_version(path):
    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as ex:
        return f"unavailable ({ex})"
    match = re.search(r"^Blender (\S+(?: LTS)?)", result.stdout, re.MULTILINE)
    return match.group(1) if match else "unknown"


def _version_ok(build):
    want = build.get("version", "")
    return not want or build["reported"].startswith(want + ".")


def _cmd_builds(config):
    ok = True
    for name, build in _builds(config).items():
        good = _version_ok(build)
        ok &= good
        want = build.get("version") or "any"
        print(f"{name:8} {build['reported']:16} want {want:5} {'ok' if good else 'WRONG VERSION'}  {build['path']}")
        print(f"         {build['description']}")
    return 0 if ok else 1


# --- the new importer -------------------------------------------------------------------

def golden_samples():
    """The Golden Samples this working copy has."""
    return sorted(p.name for p in GOLDEN.iterdir() if (p / "manifest.json").is_file()) if GOLDEN.is_dir() else []


def missing_samples():
    """The Games with a Sample Card but no Golden Sample."""
    return sorted(set(p.stem for p in SAMPLE_CARDS.glob("*.png")) - set(golden_samples()))


def _cmd_core(config, args):
    code = _import_all(config, args, "new", "none")
    return code | _check_snapshots(config, args, "new", "core")


def _cmd_hooks(config, args):
    code = _import_all(config, args, "hooks", "builtin")
    return code | _check_snapshots(config, args, "hooks", "defaults")


def _check_snapshots(config, args, variant, profile):
    """Compares each build's summary with snapshots/<sample>.<profile>.json (names exactly, positions
    within 1 mm, bones physics moves within physics.PHYSICS_TOLERANCE), or with --update rewrites it
    from the first build. 1 if anything differs."""
    failed = False
    builds = list(_distinct_builds(config, args.blender))
    for sample in args.sample or golden_samples():
        snapshot = SNAPSHOTS / f"{sample}.{profile}.json"
        if getattr(args, "update", False):
            first = _summary(builds[0], sample, variant)
            if first is None:
                print(f"{sample}.{profile}: not updated, the import on '{builds[0]}' failed")
                failed = True
                continue
            _write_snapshot(snapshot, first)
            print(f"{sample}.{profile}: snapshot written from '{builds[0]}' -> {_rel(snapshot)}")
        if not snapshot.exists():
            print(f"{sample}.{profile}: no snapshot; run with --update to record one")
            failed = True
            continue
        expected = json.loads(snapshot.read_text(encoding="utf-8"))
        skeleton = json.loads((GOLDEN / sample / "skeleton.json").read_text(encoding="utf-8"))
        tolerance = physics.tolerance_for(skeleton, expected)
        for build in builds:
            summary = _summary(build, sample, variant)
            if summary is None:
                failed = True
                continue
            diffs = compare.differences(expected, summary, tolerance=tolerance)
            failed |= bool(diffs)
            print(f"{sample}.{profile} on {build}: " + (f"{len(diffs)}{'+' if len(diffs) >= 200 else ''} "
                                                         "difference(s) from the snapshot" if diffs else "matches the snapshot"))
            for d in diffs[:40]:
                print(f"    {d}")
    return 1 if failed else 0


def _cmd_hooks_each(config, args):
    """Each Hook on its own, compared with the Core Import of the same build."""
    import hook_owns

    runs = [r for r in hook_owns.RUNS if not args.hook or r.hook in args.hook]
    unknown = set(args.hook or ()) - {r.hook for r in hook_owns.RUNS}
    if unknown:
        raise SystemExit(f"Unknown Hook(s): {', '.join(sorted(unknown))}")
    code = _cmd_core(config, args)
    for run in runs:
        code |= _import_all(config, args, run.variant, run.hook, run.options)
    out_dir = WORK / "hooks"
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = False
    for build_name in _distinct_builds(config, args.blender):
        for sample in args.sample or golden_samples():
            core = _summary(build_name, sample, "new")
            for run in runs:
                summary = _summary(build_name, sample, run.variant)
                if core is None or summary is None:
                    continue
                diffs = hook_owns.summary_differences(core, summary)
                owned, unowned = hook_owns.split(run, diffs)
                report = out_dir / f"{build_name}.{sample}.{run.variant}.md"
                report.write_text(hook_owns.markdown(sample, run, owned, unowned), encoding="utf-8")
                failed |= bool(unowned)
                print(f"  {build_name}/{sample} {run.label}: {len(owned)} change(s), "
                      f"{len(unowned)} outside what it owns  ({_rel(report)})")
    return 1 if failed or code else 0


def _distinct_builds(config, names):
    """The selected builds, less those that are the same binary and version as an earlier one."""
    builds, seen = {}, {}
    for name, build in _builds(config, names).items():
        key = (os.path.realpath(build["path"]), build["reported"])
        if key in seen:
            continue
        seen[key] = name
        builds[name] = build
    return builds


def _summary(build_name, sample, variant):
    path = run_dir(build_name, sample, variant) / "summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _import_all(config, args, variant, hooks, options=None):
    """Imports every selected sample on every distinct build; 1 if an import or a Hook failed."""
    builds = _builds(config, args.blender)
    for name, build in builds.items():
        if not _version_ok(build):
            raise SystemExit(f"Blender build '{name}' reports {build['reported']}, expected {build['version']}.x")
    samples = args.sample or golden_samples()
    unknown = set(samples) - set(golden_samples())
    if unknown:
        raise SystemExit(f"No Golden Sample for {', '.join(sorted(unknown))}; make it with scripts/export-sample.sh")
    distinct = _distinct_builds(config, args.blender)
    for name in builds:
        if name not in distinct:
            print(f"  '{name}' is the same build as another; skipped.")
    runs = [(name, build, s) for name, build in distinct.items() for s in samples]
    wheel = pillow_wheel()
    failed = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(_run_new, b, build, s, wheel, args.keep_blend, variant, hooks, options): (b, s)
                   for b, build, s in runs}
        for future in concurrent.futures.as_completed(futures):
            b, s = futures[future]
            r = future.result()
            ok = r["summary"] is not None
            hook_failures = [f"{h} {status}" for h, status in (r["summary"] or {}).get("run", {}).get("hooks", {}).items()
                             if status.startswith("failed")]
            failed |= not ok or bool(hook_failures)
            warnings = len(r["summary"]["run"]["log_warnings"]) if ok else 0
            state = "FAILED" if not ok else "HOOK FAILED" if hook_failures else "imported"
            print(f"  {b}/{s}.{variant}: {state} in {r['seconds']} s, {warnings} warning(s)"
                  f"  (log: {_rel(r['log'])})")
            for failure in hook_failures:
                print(f"      {failure}")
    return 1 if failed else 0


def run_dir(build_name, sample, variant):
    return WORK / "runs" / build_name / f"{sample}.{variant}"


def new_summary_path(build_name, sample):
    return run_dir(build_name, sample, "new") / "summary.json"


def _run_new(build_name, build, sample, wheel, keep_blend, variant="new", hooks="none", options=None):
    folder = run_dir(build_name, sample, variant)
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    profile = addon_profile(folder)
    bundle = folder / "bundle"
    copy_bundle(GOLDEN / sample, bundle)  # hard links: the import writes only into kkbp_cache/
    out, log = folder / "summary.json", folder / "blender.log"
    command = [build["path"], "--background", "--factory-startup", "--python-exit-code", "1",
               "--python", str(HARNESS / "blender" / "new_import.py"), "--",
               "--bundle", str(bundle), "--pillow", str(wheel), "--out", str(out),
               "--hooks", hooks, "--options", json.dumps(options or {})]
    if keep_blend:
        command += ["--save-blend", str(folder / "scene.blend")]
    started = time.monotonic()
    with open(log, "w", encoding="utf-8") as log_file:
        try:
            code = subprocess.run(command, env={**os.environ, "BLENDER_USER_RESOURCES": str(profile)},
                                  stdout=log_file, stderr=subprocess.STDOUT, timeout=TIMEOUT_SECONDS).returncode
        except subprocess.TimeoutExpired:
            code = None
            log_file.write(f"\n[harness] timed out after {TIMEOUT_SECONDS} s\n")
    summary = json.loads(out.read_text(encoding="utf-8")) if code == 0 and out.exists() else None
    if not keep_blend:
        shutil.rmtree(bundle, ignore_errors=True)
    return {"summary": summary, "log": log, "seconds": round(time.monotonic() - started, 1)}


def addon_profile(folder: Path) -> Path:
    """An empty Blender profile whose local repository holds a fresh copy of the add-on."""
    profile = folder / "profile"
    if profile.exists():
        shutil.rmtree(profile)
    repo = profile / "extensions" / "user_default"
    repo.mkdir(parents=True)
    shutil.copytree(ADDON, repo / "kkbp", ignore=shutil.ignore_patterns("__pycache__", "wheels"))
    return profile


def pillow_wheel() -> Path:
    """The pinned Pillow wheel every test profile installs, downloaded once with the venv's pip.
    (The venv is built from the minimum build's Python; a build with another Python would need its own.)"""
    text = (ADDON / "pillow.py").read_text(encoding="utf-8")
    version = re.search(r'^PILLOW_VERSION = "([^"]+)"', text, re.MULTILINE).group(1)
    folder = WORK / "wheels"
    found = sorted(folder.glob(f"pillow-{version}-*.whl"))
    if not found:
        print(f"== Downloading Pillow {version} for the test profiles", flush=True)
        subprocess.run([str(VENV / "bin" / "python"), "-m", "pip", "download", f"pillow=={version}",
                        "--only-binary=:all:", "--no-deps", "--disable-pip-version-check", "-q", "--dest", str(folder)],
                       check=True)
        found = sorted(folder.glob(f"pillow-{version}-*.whl"))
    return found[0]


def venv_site_packages() -> Path:
    found = sorted((VENV / "lib").glob("python3.*/site-packages"))
    if not found:
        raise SystemExit("importer/.venv is missing; run scripts/setup-importer-dev.sh first")
    return found[0]


def _write_snapshot(path, summary):
    summary = json.loads(json.dumps(summary))
    for key in VOLATILE_RUN_KEYS:
        summary.get("run", {}).pop(key, None)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def _rel(path):
    try:
        return str(Path(path).relative_to(REPO))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
