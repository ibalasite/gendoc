#!/usr/bin/env bash
# bin/gendoc-env.sh — single source of truth for gendoc runtime paths
# Usage: source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

GENDOC_DIR="${GENDOC_DIR:-$HOME/.claude/skills/gendoc}"
GENDOC_BIN="$GENDOC_DIR/bin"
GENDOC_TEMPLATES="$GENDOC_DIR/templates"
GENDOC_TOOLS="$GENDOC_DIR/tools/bin"
