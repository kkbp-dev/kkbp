# Sourced by the scripts that use the Golden Samples. Each developer exports their own into
# contract/samples/<game>/ from contract/sample-cards/<game>.png with scripts/export-sample.sh
# (ADR 0031); beside each one, <game>.stamp records which exporter and contract made it.
# Callers may run under `set -e`; nothing here fails them.
#
#   golden_stamp           prints the stamp of the working tree's exporters and contract (docs aside)
#   golden_report          prints a notice for each Game with no Golden Sample, and a warning for
#                          each sample whose stamp is missing or differs from golden_stamp; never fails
#   golden_games           the Games that have a Sample Card

golden_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

golden_games() {
  local card
  for card in "$golden_repo"/contract/sample-cards/*.png; do
    [[ -f "$card" ]] && basename "$card" .png
  done
}

# The paths whose files decide what an export writes: the exporters and the contract's schemas and
# expression tables (embedded into the exporters).
golden_inputs=(exporters contract/schema contract/expressions)

# One hash of every file under golden_inputs but the Markdown docs, as it is on disk (uncommitted
# changes included, ignored build output left out). It reads the files only and writes nothing to git.
golden_stamp() {
  (cd "$golden_repo" &&
    git ls-files -z --cached --others --exclude-standard -- "${golden_inputs[@]}" ':(exclude)*.md' \
      | sort -zu | xargs -0 sha256sum -- 2>/dev/null | sha256sum | cut -d' ' -f1)
}

golden_report() {
  local game samples="$golden_repo/contract/samples" now
  now="$(golden_stamp)" || { echo "warning: couldn't compute the Golden Sample stamp"; return 0; }
  for game in $(golden_games); do
    if [[ ! -f "$samples/$game/manifest.json" ]]; then
      echo "notice: no Golden Sample for $game, so its sample tests are skipped; make it with scripts/export-sample.sh $game"
    elif [[ ! -f "$samples/$game.stamp" ]]; then
      echo "warning: the $game Golden Sample has no stamp, so it may be out of date; remake it with scripts/export-sample.sh $game"
    elif [[ "$(cat "$samples/$game.stamp")" != "$now" ]]; then
      echo "warning: the $game Golden Sample was made by an exporter or contract that differs from this working tree's; remake it with scripts/export-sample.sh $game"
    fi
  done
}
