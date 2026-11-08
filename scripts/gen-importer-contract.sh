#!/usr/bin/env bash
# Regenerates importer/kkbp/bundle/_contract.py, the importer's copy of the contract's closed sets,
# from contract/schema/. Run it after changing a schema; the bundle/ tests fail until you do.
#
# Usage: scripts/gen-importer-contract.sh [--check]
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$repo/importer/tools/gen_contract.py" "$@"
