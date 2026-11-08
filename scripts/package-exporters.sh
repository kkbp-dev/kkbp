#!/usr/bin/env bash
# Builds the three Game Adapters and packs them into one release zip,
# exporters/dist/kkbp-exporters-<version>.zip. The zip has the repository's LICENSE and NOTICE at its
# root and a folder per Game holding the BepInEx folder to copy into that game's root folder (the
# one with the game's .exe):
#
#   Koikatsu/BepInEx/plugins/KKBP/KKBP.Exporter.KK.dll
#   Koikatsu Sunshine/BepInEx/plugins/KKBP/KKBP.Exporter.KKS.dll
#   Summer Vacation Scramble/BepInEx/plugins/KKBP/KKBP.Exporter.SVS.dll
#
# The version is the Exporter Version in exporters/Exporter.props. Building needs all three game
# installs (ADR 0007), so a missing one fails the script.
#
# Usage: scripts/package-exporters.sh
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dist="$repo/exporters/dist"
export PATH="$PATH:$HOME/.dotnet"
export DOTNET_NOLOGO=1 DOTNET_CLI_TELEMETRY_OPTOUT=1

[[ $# -eq 0 ]] || { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
command -v zip >/dev/null || { echo "package-exporters: zip not found. Install it." >&2; exit 1; }
command -v dotnet >/dev/null || { echo "package-exporters: dotnet not found. Install the .NET SDK." >&2; exit 1; }

version="$(dotnet msbuild "$repo/exporters/kk/KKBP.Exporter.KK.csproj" -getProperty:KKBPExporterVersion)"
[[ -n "$version" ]] || { echo "package-exporters: no KKBPExporterVersion in exporters/Exporter.props" >&2; exit 1; }

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

for game in kk kks svs; do
  case "$game" in
    kk)  folder="Koikatsu" ;;
    kks) folder="Koikatsu Sunshine" ;;
    svs) folder="Summer Vacation Scramble" ;;
  esac
  dll="$("$repo/scripts/build-exporters.sh" "$game")"
  mkdir -p "$stage/$folder/BepInEx/plugins/KKBP"
  cp "$dll" "$stage/$folder/BepInEx/plugins/KKBP/"
done
cp "$repo/LICENSE" "$repo/NOTICE" "$stage/"

mkdir -p "$dist"
zip_path="$dist/kkbp-exporters-$version.zip"
rm -f "$zip_path"
(cd "$stage" && zip -q -r -X "$zip_path" LICENSE NOTICE \
  "Koikatsu" "Koikatsu Sunshine" "Summer Vacation Scramble")
echo "Packaged $zip_path"
