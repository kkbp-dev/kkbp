# Exporters run an export when a request file appears

Each exporter plugin looks for `BepInEx/config/kkbp-autoexport.json` when the game starts. If it is there, the plugin opens the character maker, loads the card it names, exports with the Outfit and options it gives, writes a result file next to it, deletes the request and quits the game. Without the file the plugin does nothing different. `scripts/export-sample.sh` writes the request and starts the game, which is how the golden samples in `contract/samples/` are made.

## Considered Options

- **Export by hand in the game**: no extra code in the plugin, but golden samples couldn't be rebuilt from a script, and a re-export after a contract change would depend on someone clicking through the maker.
- **Drive the game window with input automation**: nothing changes in the plugin, but the IMGUI controls have no fixed position, and capturing the game window under Wine and Wayland doesn't work reliably.
- **A request file the plugin acts on (chosen)**: the export path is the same as a manual export; only the start is automated.

## Consequences

- Release builds include the auto-export code. It is inert unless the request file exists.
- The request names files outside the game folder, such as the legacy samples' cards, so the cards never need copying into the game.
