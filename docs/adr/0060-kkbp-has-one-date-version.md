# KKBP has one version, the release date

The importer and the exporters are released together, as one KKBP Version: the release date, `YYYY.MM.DD` (`2026.11.25`). It is the git tag (`v2026.11.25`), the release zips' names (`kkbp-2026.11.25.zip`, `kkbp-exporters-2026.11.25.zip`), the Exporter Version in each Manifest, and the exporter window's title. It is kept in one file, `VERSION` at the repository's root, which the exporter build reads.

Blender's extension manifest and BepInEx only accept versions without leading zeros. So `blender_manifest.toml` and the BepInEx plugin version hold the same date with the zeros dropped (`2027.01.05` is `2027.1.5`). The exporter build parses `VERSION` for the plugin version. The manifest keeps a copy, which `scripts/set-version.sh` writes and a host test checks against `VERSION`.

## Considered Options

- **Separate semantic versions for the importer and the exporters**: each part's number says how much it changed. But the two are always released together, and users had two unrelated numbers to match.
- **One date, written without leading zeros everywhere**: one form in every place. But it isn't `YYYY.MM.DD` from January to September or on days 1 to 9, and those dates don't sort as text.
- **One date, padded wherever the format allows (chosen)**: what users see (the tag, the zips, the exporter window) reads as a date, and the two strict places get the same numbers.

## Consequences

- There is at most one release a day. A second fix on the same day takes the next day's date.
- There is no `-dev` marker. Between releases the version stays at the last release's date; a release sets the new date with `scripts/set-version.sh` (today by default).
- Blender's Preferences show the unpadded form, `2027.1.5`, for an early-month or early-year release.
- The Exporter Version stays informational (the Schema Version decides whether a bundle is accepted), so an importer and an exporter from different releases still work together whenever their Schema Versions agree.
- The first release is `2026.11.25`. Before it, the importer and the exporters were numbered 10.0.0 and 6.0.0, but neither was released under those numbers.
