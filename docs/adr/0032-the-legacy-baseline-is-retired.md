# The legacy baseline is retired

The new importer is no longer compared with the legacy importer. Phase 0 recorded the legacy importer's scene summaries of the three legacy sample exports (`importer/tests/snapshots/baseline/`), and `run.py compare` sorted every difference from them by cause (D13). The new importer has been released (10.0.0), its own reviewed snapshots are the regression target (D50), and the baseline needed the legacy exports, the legacy add-on and mmd_tools, which only one working copy has. So the baseline, `run.py baseline` and `compare`, `causes.py`, `compare_legacy.py`, `legacy_names.toml`, `scripts/compare-baseline.sh` and the harness's `[legacy]`, `[samples]` and `[profiles]` settings are deleted.

## Considered Options

- **Keep the baseline files as a frozen record nothing reads (rejected)**: git history keeps them.
- **Delete it all (chosen)**.

## Consequences

- The legacy code stays in the working copy as read-only reference (`Blender addons/`, `kkbp_exporter/`, `svs_exporter/`, `Sample exporter output files/`), for porting questions only.
- `hooks --each` keeps diffing each Hook's import with the Core Import; the item-by-item diff it used moved from `compare_legacy.py` into `hook_owns.py`. `scene_summary.py` keeps its legacy-era branches (the `Metarig_ID` cleanup, file-named images), because the ported Rigify scripts and the template library still produce them.
- ADRs and design docs that cite baseline differences stay as history.
