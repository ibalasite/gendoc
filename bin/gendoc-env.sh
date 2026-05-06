#!/usr/bin/env bash
# bin/gendoc-env.sh — single source of truth for gendoc runtime paths
# Usage: source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

export GENDOC_DIR="${GENDOC_DIR:-$HOME/.claude/skills/gendoc}"
export GENDOC_BIN="$GENDOC_DIR/bin"
export GENDOC_TEMPLATES="$GENDOC_DIR/templates"
export GENDOC_TOOLS="$GENDOC_DIR/tools/bin"
