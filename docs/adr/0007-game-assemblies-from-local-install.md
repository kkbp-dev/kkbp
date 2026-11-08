# Adapters build against the local game install

The Game Adapters reference the game, Unity and BepInEx assemblies straight from a game install on the build machine, through HintPaths under one MSBuild property, `KKBPGamesDir`. It defaults to `games/` in the working copy and can be set with the `KKBP_GAMES_DIR` environment variable. The references are `Private=false`, so no game assembly is copied into the build output, and none is ever committed. A build without an install fails with a message naming the missing file.

## Considered Options

- **The IllusionLibs NuGet packages, as the legacy exporters did**: builds work on any machine, but the packages redistribute the games' own code, and their versions don't always match the patched game being exported from.
- **The local install (chosen)**: the adapter compiles against exactly the assemblies it will run with, including the IL2CPP interop assemblies that BepInEx 6 generates for SVS on first launch.

## Consequences

- Building an adapter needs the game installed, with BepInEx run at least once for SVS. A CI job would need the same.
- No assembly is publicized. KK and KKS reach the few private members they need through Harmony's `AccessTools`; the IL2CPP interop types are public already.
- A game update can change the assemblies under a build without any change in the repository.
