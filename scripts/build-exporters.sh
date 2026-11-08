#!/usr/bin/env bash
# Builds the Game Adapters: KK (NET35), KKS (NET46) and SVS (net6.0). They compile against the game,
# Unity and BepInEx assemblies of a local install (ADR 0007): games/ in the working copy, or the
# folder in KKBP_GAMES_DIR. Needs the .NET SDK (10 or later).
#
# Usage: scripts/build-exporters.sh [kk|kks|svs]...   (default: all three)
# Prints the path of each plugin DLL it built.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:$HOME/.dotnet"
export DOTNET_NOLOGO=1 DOTNET_CLI_TELEMETRY_OPTOUT=1

command -v dotnet >/dev/null || { echo "build-exporters: dotnet not found. Install the .NET SDK." >&2; exit 1; }

games=("$@")
[[ ${#games[@]} -gt 0 ]] || games=(kk kks svs)

for game in "${games[@]}"; do
  case "$game" in
    kk)  project=exporters/kk/KKBP.Exporter.KK.csproj;   config=NET35;   dll=exporters/kk/bin/NET35/KKBP.Exporter.KK.dll ;;
    kks) project=exporters/kk/KKBP.Exporter.KK.csproj;   config=NET46;   dll=exporters/kk/bin/NET46/KKBP.Exporter.KKS.dll ;;
    svs) project=exporters/svs/KKBP.Exporter.SVS.csproj; config=Release; dll=exporters/svs/bin/Release/KKBP.Exporter.SVS.dll ;;
    *) echo "build-exporters: unknown game '$game' (use kk, kks or svs)" >&2; exit 1 ;;
  esac
  echo "== Building $game" >&2
  dotnet build "$repo/$project" -c "$config" --nologo -v quiet >&2
  echo "$repo/$dll"
done
