#!/usr/bin/env bash
# An example game launcher. scripts/auto-export.sh (and so scripts/export-sample.sh) starts each game
# with games/play.sh, which every computer needs its own of: copy this file to games/play.sh (or
# $KKBP_GAMES_DIR/play.sh), make it executable, and point the paths below at your Proton setup.
# "The game launcher" in exporters/README.md says what it must do.
#
#   play.sh <game> [program] [args...]
#
#   game     koikatsu | kks | svs
#   program  exe relative to the game folder (e.g. CharaStudio.exe, InitSetting.exe)
#            or a full path (e.g. the HF Patch installer). Defaults to the main game exe.
#
# This one runs the game through umu-launcher with a pinned GE-Proton, one Wine prefix per game.
# Environment: KKBP_WINE_PREFIXES (default ~/Games/prefixes), KKBP_GAME_LOGS (default ~/Games/logs),
# PROTONPATH (default a GE-Proton in Steam's compatibilitytools.d), KKBP_UMU_RUN (default ~/Games/umu/umu/umu-run).
set -euo pipefail

GAMES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIXES="${KKBP_WINE_PREFIXES:-$HOME/Games/prefixes}"
LOGS="${KKBP_GAME_LOGS:-$HOME/Games/logs}"
UMU_RUN="${KKBP_UMU_RUN:-$HOME/Games/umu/umu/umu-run}"

# loader = the proxy DLL BepInEx's doorstop uses in that game folder; Wine must load it native, or
# BepInEx (and so the exporter) never starts.
case "${1:-}" in
  koikatsu) prefix=koikatsu-proton; dir="Koikatsu";                 exe="Koikatu.exe";          loader=winhttp ;;
  kks)      prefix=kks-proton;      dir="Koikatsu Sunshine";        exe="KoikatsuSunshine.exe"; loader=winhttp ;;
  svs)      prefix=svs-proton;      dir="Summer Vacation Scramble"; exe="SamabakeScramble.exe"; loader=hid ;;
  *) sed -n '7,12p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
shift
[[ $# -gt 0 ]] && { exe="$1"; shift; }
[[ "$exe" = /* ]] || exe="$GAMES_DIR/$dir/$exe"
[[ -f "$exe" ]] || { echo "Not found: $exe" >&2; exit 1; }

mkdir -p "$LOGS"
export WINEPREFIX="$PREFIXES/$prefix"
export WINEDEBUG="${WINEDEBUG:-fixme-all}"
export DXVK_LOG_PATH="$LOGS"
# Pinned so launches don't auto-update. Proton merges this with its own overrides.
export GAMEID=umu-default PROTONPATH="${PROTONPATH:-$HOME/.local/share/Steam/compatibilitytools.d/GE-Proton11-11-x86_64}"
export WINEDLLOVERRIDES="$loader=n,b${WINEDLLOVERRIDES:+;$WINEDLLOVERRIDES}"
log="$LOGS/$prefix-$(basename "$exe" .exe).log"

echo "prefix: $WINEPREFIX"
echo "exe:    $exe"
echo "log:    $log"
# Run from the program's own folder: Unity and the BepInEx proxy DLL both expect it.
cd "$(dirname "$exe")"
exec "$UMU_RUN" "$exe" "$@" >"$log" 2>&1
