# Hooks

A Hook is a script that runs on each character after it is imported. KKBP's own finishing steps (outlines, Rigify, SFW mode and the rest) are Hooks, and you can add your own.

## Running a Hook on an imported character

Run Hook, in the Tools panel, runs any Hook on a character already in the file. Select any part of the character, click Run Hook and pick the Hook. For example:

- Rigify, on a character imported without a rig
- Separate Eyes, once you decide to composite the eyes over the hair
- Convert shaders, to change shader

## Adding your own

1. Put your `.py` scripts in a folder.
2. Open KKBP in Preferences > Add-ons and set Hooks folder to it. The Hooks section of the KKBP panel shows the folder too.
3. The scripts are loaded when Blender starts, when you click Reload Hooks, and before each import.

> **Picture to come:** `images/hooks/panel.jpg`, the Hooks section of the panel with a loaded script.

Your Hooks run after the built-in ones, in the order shown in Preferences, where each can be switched off or moved. A Hook can declare options of its own, which appear among the Import Options. A script that fails to load is shown in the panel with the reason, and a Hook that fails during an import is reported in the log without stopping the import.

## Writing a Hook

[The hook interface](../hook-interface.md) has a complete example and the API: how a Hook finds the character's objects, materials and bones, reads the export, and declares options. A Hook written against it works on all three games and keeps working when objects are renamed.
