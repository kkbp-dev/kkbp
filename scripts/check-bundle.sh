#!/usr/bin/env bash
# Checks exported bundles against the JSON Schemas, the contract checks and the Khronos glTF Validator,
# the same checks the Golden Samples get (it checks those too). Needs what scripts/check-core.sh needs.
#
# Usage: scripts/check-bundle.sh <bundle folder>...
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:$HOME/.dotnet:$HOME/.local/node/bin"
export DOTNET_NOLOGO=1 DOTNET_CLI_TELEMETRY_OPTOUT=1
[[ $# -gt 0 ]] || { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }

source "$repo/scripts/golden-samples.sh"
[[ -n "${KKBP_EXPORTING_SAMPLE:-}" ]] || golden_report  # export-sample.sh stamps after this check
bundles=()
for b in "$@"; do bundles+=("$(realpath "$b")"); done
[[ -d "$repo/contract/tools/node_modules/gltf-validator" ]] || (cd "$repo/contract/tools" && npm ci --ignore-scripts --no-audit --no-fund --silent)
KKBP_CHECK_BUNDLES="$(IFS=:; echo "${bundles[*]}")" dotnet test "$repo/exporters/core/tests/KKBP.Exporter.Core.Tests.csproj" \
  --nologo -c Release --filter "FullyQualifiedName~SampleBundleTests" --logger "console;verbosity=normal" 2>&1 \
  | grep -vE "^\s*$|Test run for|A total of|Starting test execution"
