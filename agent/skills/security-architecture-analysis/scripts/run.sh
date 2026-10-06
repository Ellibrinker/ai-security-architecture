#!/bin/bash
# security-architecture-analysis
# Prints the methodology so the agent can load it into context before
# starting a black-box security architecture engagement.
#
# Usage: run.sh <target-url> [scope statement]
# Typically invoked by the agent runtime's skill loader; the printed output
# is injected into the agent's context.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Security Architecture Analysis: methodology loaded ==="
echo
if [ "$#" -gt 0 ]; then
  echo "Arguments passed: $*"
  echo
fi
cat "$SKILL_DIR/SKILL.md"
