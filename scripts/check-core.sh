#!/usr/bin/env bash
# Checks the Exporter Core the way CI will: builds it alone for net35 (KK's runtime), installs the
# pinned glTF Validator, and runs the tests, which check the fake adapter's bundle and every Golden
# Sample in contract/samples/ against the JSON Schemas and the validator. Needs the .NET SDK
# (10 or later) and Node.js.
#
# Usage: scripts/check-core.sh
# Finds dotnet and node on PATH, then in ~/.dotnet and ~/.local/node/bin.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:$HOME/.dotnet:$HOME/.local/node/bin"
export DOTNET_NOLOGO=1 DOTNET_CLI_TELEMETRY_OPTOUT=1

for tool in dotnet node npm; do
  if ! command -v "$tool" >/dev/null; then
    echo "check-core: $tool not found. Install the .NET SDK and Node.js." >&2
    exit 1
  fi
done

echo "== Building the Core for net35"
dotnet build "$repo/exporters/core/build/KKBP.Exporter.Core.Net35.csproj" --nologo -v quiet -c Release

echo "== Installing the glTF Validator"
(cd "$repo/contract/tools" && npm ci --ignore-scripts --no-audit --no-fund --silent)

echo "== Running the tests"
source "$repo/scripts/golden-samples.sh"
golden_report
dotnet test "$repo/exporters/core/tests/KKBP.Exporter.Core.Tests.csproj" --nologo -v quiet -c Release
