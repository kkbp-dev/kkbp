# Contributing to KKBP

How the repository is laid out and how to build and test it. Using KKBP is covered by the [README](README.md) and the [wiki](docs/wiki/README.md).

KKBP is exporters that capture a Koikatsu, Koikatsu Sunshine or Summer Vacation Scramble Character into an Export Bundle, and a Blender importer that rebuilds the Character from that bundle.

Terms are defined in [CONTEXT.md](CONTEXT.md), the design is in [docs/design/](docs/design/README.md), and decisions that need their context are in [docs/adr/](docs/adr/).

| Folder | Contents |
|---|---|
| [contract/](contract/) | The Export Bundle contract: schemas, closed sets, Sample Cards |
| [exporters/](exporters/) | Exporter Core and Game Adapters |
| [importer/](importer/) | Blender importer and its [test harness](importer/tests/harness/README.md) |
| [docs/design/](docs/design/README.md), [docs/adr/](docs/adr/) | Design docs and ADRs |
| [docs/wiki/](docs/wiki/README.md) | The user documentation |

The game installs (`games/`) sit beside these folders in the working copy and are ignored by git, as are the Golden Samples in `contract/samples/`, which `scripts/export-sample.sh` makes from the Sample Cards (ADR 0031).

On a new computer, follow "First-time setup" in [CLAUDE.md](CLAUDE.md) before running any test: the tests need the Golden Samples, and making them needs the games and a game launcher.

## Referring to issues

- Code, tests and docs say what was asked and why, not an issue or pull request number, so the text stands without the issue page. An open issue may be cited by number (`issue #1`) for the work it still tracks.

## Changing the user documentation

- A change to what a user sees (an option, a label, a default, a tool) changes its page in `docs/wiki/` in the same pull request.
- The wiki uses the names the UI shows, and plain words elsewhere: "character" and "export folder", not the capitalised terms of `CONTEXT.md`.
- Pictures go in `docs/wiki/images/<page>/`, as JPEG or WebP, at most 1200 px wide and about 300 KB. They are kept out of Git LFS (`.gitattributes`), so that showing them doesn't use LFS bandwidth. They must be safe for work.
