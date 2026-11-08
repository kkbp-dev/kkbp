# One Gag template for every Game, built per material from the bundle

The gag eyes of every Game use one Material Template, Gag. Its material holds only a frame counter, the expression choice and the output; `templates.apply` adds one `.Gag UV` group, image and `.Gag pick` group for each pattern the bundle gives the material, and the material-changes Step sets each pattern's animation values (`_AngleSpeed`, `_SizeSpeed`, `_SizeWidth`, `_TileAnimation`, mapped by the Game Profile) and drives the choice from the gag expressions. The animation is the legacy SVS gag group's, split so that the images sit on the material.

## Considered Options

- **Keep KK's three hand-wired templates (Gag00, Gag01, Gag02)**: closest to the legacy KK look, but each template hard-codes which game textures it shows and how they move, the Template Set would need a key beyond (Material Role, Blend Mode) to tell the three gag meshes apart, and the per-expression values in the bundle would be ignored.
- **One template per Game** (KK's and SVS's own): what material-template.md first planned, but both Games' bundles describe gag eyes the same way, through `material_changes`.
- **One template built from the bundle (chosen)**: the game's own animation values drive it, and any number of gag patterns works.

## Consequences

- SVS's Template Set overrides only the Light Dark templates and render methods, not Gag.
- KK's gag eyes move by the game's values rather than the legacy templates' hand-tuned ones; how close that looks to the game is checked by eye, since the summaries can't show it.
- SVS gag eyes show one texture per expression on both eyes; the bundle records no separate right-eye texture per expression.
