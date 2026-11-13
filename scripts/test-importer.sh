#!/usr/bin/env bash
# Runs the importer's tests: the host tests (bundle/, profiles/, library/ and source rules) and the
# harness's own unit tests on importer/.venv's Python, which is Blender's own interpreter; then the
# in-Blender tests on every harness build in an isolated profile, the builds at the same time; then,
# in one queue, the Core Import of every Golden Sample on every build, the same with every built-in
# Hook, and each Hook on its own (run.py all: each fails if an import or a Hook fails, a summary
# differs from its snapshot, or a Hook changes what it doesn't own). Needs
# scripts/setup-importer-dev.sh to have run once, and the Golden Samples from
# scripts/export-sample.sh; tests of a Game with no Golden Sample are skipped, with a notice.
#
# A full run (no arguments) that passes is recorded as green: a stamp of everything its result
# depends on goes into ~/.cache/kkbp/green/ (shared by every checkout and worktree). A later full run
# whose stamp is already there says so and stops; --force runs it anyway. The stamp covers the
# files under importer/, contract/, scripts/ and docs/hook-interface.md as they are on disk
# (uncommitted changes included), the Golden Samples, the venv, and each harness build.
#
# Usage: scripts/test-importer.sh [--force] [--host-only | --blender-only] [pytest arguments]
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python="$repo/importer/.venv/bin/python"
[[ -x "$python" ]] || { echo "test-importer: run scripts/setup-importer-dev.sh first" >&2; exit 1; }
source "$repo/scripts/golden-samples.sh"
golden_report

# One hash of everything a full run's result depends on. Reads files only.
green_stamp() {
  (cd "$repo" && {
    git ls-files -z --cached --others --exclude-standard -- importer contract scripts docs/hook-interface.md \
      | sort -zu | { xargs -0 sha256sum -- 2>/dev/null || true; }
    find contract/samples -type f -not -path '*/kkbp_cache/*' -print0 2>/dev/null \
      | sort -z | { xargs -0 -r sha256sum -- || true; }
    sha256sum importer/.venv/pyvenv.cfg
    python3 importer/tests/harness/run.py builds || true
  } | sha256sum | cut -d' ' -f1)
}

force=0
if [[ "${1:-}" == "--force" ]]; then force=1; shift; fi
host=1 blender=1
case "${1:-}" in
  --host-only) blender=0; shift ;;
  --blender-only) host=0; shift ;;
esac

full=$(( host && blender && $# == 0 ))
if (( full )); then
  stamp="$(green_stamp)"
  green="${XDG_CACHE_HOME:-$HOME/.cache}/kkbp/green/$stamp"
  if (( ! force )) && [[ -f "$green" ]]; then
    echo "test-importer: already green, nothing changed since: $(cat "$green")"
    echo "test-importer: the files, Golden Samples and Blender builds are the same; --force runs the tests anyway"
    exit 0
  fi
fi

if (( host )); then
  echo "== Host tests"
  "$python" -m pytest -q -p no:cacheprovider "$repo/importer/tests/host" "$@"
  echo "== Harness unit tests"
  "$python" -m unittest discover -s "$repo/importer/tests/harness" -t "$repo/importer/tests/harness" 2>&1 | tail -n 3
fi
if (( blender )); then
  "$python" "$repo/importer/tests/blender/launch.py" "$@"
  if (( $# == 0 )); then
    echo "== Golden samples: the Core Import, every built-in Hook, and each built-in Hook on its own"
    "$python" "$repo/importer/tests/harness/run.py" all
  fi
fi

# Every step passed (set -e). Record it, unless something it depends on changed while it ran.
if (( full )); then
  if [[ "$(green_stamp)" == "$stamp" ]]; then
    mkdir -p "$(dirname "$green")"
    dirty="$(git -C "$repo" status --porcelain -- importer contract scripts docs/hook-interface.md | head -c1)"
    echo "$(date '+%Y-%m-%d %H:%M') on $(git -C "$repo" rev-parse --abbrev-ref HEAD) at $(git -C "$repo" rev-parse --short HEAD)${dirty:+ with uncommitted changes}" > "$green"
    echo "== All passed; recorded as green ($(basename "$green" | cut -c1-12))"
  else
    echo "== All passed, but files changed during the run, so it isn't recorded as green"
  fi
fi
