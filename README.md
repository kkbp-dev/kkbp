# KKBP

Exporters that capture a Koikatsu, Koikatsu Sunshine or Summer Vacation Scramble Character into an Export Bundle, and a Blender importer that rebuilds the Character from that bundle.

This is the redesign. Terms are defined in [CONTEXT.md](CONTEXT.md), the agreed design and roadmap are in [docs/design/](docs/design/README.md), and decisions are in [docs/adr/](docs/adr/).

| Folder | Contents |
|---|---|
| [contract/](contract/) | The Export Bundle contract: schemas, closed sets, Sample Cards |
| [exporters/](exporters/) | Exporter Core and Game Adapters |
| [importer/](importer/) | Blender importer and its [test harness](importer/tests/harness/README.md) |
| [docs/](docs/) | Design docs and ADRs |

The legacy exporters, the legacy importer, the legacy exporters' output and the game installs sit beside these folders in the working copy and are ignored by git, as are the Golden Samples in `contract/samples/`, which `scripts/export-sample.sh` makes from the Sample Cards (ADR 0031).

On a new computer, follow "First-time setup" in [CLAUDE.md](CLAUDE.md) before running any test: the tests need the Golden Samples, and making them needs the games and a game launcher.

## Credits

The importer's export atlas follows shotariya's [Material Combiner](https://github.com/Grim-es/material-combiner-addon) and Jake Gordon's bin packer, and its Merge Weights follows the [Cats Blender Plugin](https://github.com/michaeldegroot/cats-blender-plugin); all three are MIT-licensed. The edit materials' shadow colours follow xukmi's MIT-licensed recreations of the game's shaders (KKShadersPlus, KKShadersRecreated). None of their code is bundled. The Rigify Hook's joint corrections come mostly from a file by johnbbob_la_petite. Details are in [NOTICE](NOTICE).
