# `import_bundle` returns a failed import instead of raising

`kkbp.import_bundle()` raises only for problems found before anything is built: a bundle it can't open (`BundleError`), Pillow not installed, an unknown or wrongly typed Import Option (`OptionError`), or a glTF importer option that no longer exists (`MeshLoaderError`). Once the Character's Collection exists, a failing Step doesn't raise. The import stops, the partly built scene stays, and the returned `ImportResult` has `ok=False`, the failed Step's name and the error. The traceback is in the KKBP log. A failing Hook is a warning in the same result, and the import still counts as done.

## Considered Options

- **Raise on a failed Step**: the usual Python behaviour, but the panel, `auto_import`, `bulklaunch` and the harness would all have to catch it and rebuild the summary. The timings, the Hook outcomes and the log path would only be reachable through the exception.
- **Return every outcome, even an unopenable bundle**: one code path for callers, but nothing has been built yet, so there is no Character or Step to report on. An error raised before the scene changes is easier to act on.
- **Raise before building, return after (chosen)**: callers get one result for everything that touched the scene. The panel shows `result.summary()` whatever happened.

## Consequences

- A caller that needs an exception checks `result.ok`.
- Each Step's outcome (`ran`, `failed`, `skipped` for this Game) and each Hook's (`ran`, `failed`, `skipped`, `off`) are in the result, so the harness can test the Core Import with `hooks=[]` and then each Hook alone.
