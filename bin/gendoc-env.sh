#!/usr/bin/env bash
# bin/gendoc-env.sh — single source of truth for gendoc runtime paths
# Usage: source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

_PY_HOME=$(python3 -c "import os; print(os.path.expanduser('~').replace('\\\\', '/'))" 2>/dev/null || echo "$HOME")
export GENDOC_DIR="${GENDOC_DIR:-$_PY_HOME/.claude/skills/gendoc}"
export GENDOC_BIN="$GENDOC_DIR/bin"
export GENDOC_TEMPLATES="$GENDOC_DIR/templates"
export GENDOC_TOOLS="$GENDOC_DIR/tools/bin"
