#!/usr/bin/env bash
# Install/sync gendoc skills from repo to ~/.claude/skills/
# Usage: ./install.sh [--quiet]
set -e

GENDOC_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$GENDOC_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"
QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

log() { [[ $QUIET -eq 1 ]] || echo "$@"; }

[[ -d "$SKILLS_SRC" ]] || { echo "❌ skills/ 目錄不存在：$SKILLS_SRC"; exit 1; }

log "[install] 同步 gendoc skills → $SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
  skill_name="$(basename "$skill_dir")"
  dst="$SKILLS_DST/$skill_name"
  mkdir -p "$dst"
  cp "$skill_dir/SKILL.md" "$dst/SKILL.md"
  log "  ✓ $skill_name"
done

# Clear throttle stamp so next session will check for further updates
rm -f "$GENDOC_DIR/.last-update-check" 2>/dev/null || true

log "[install] 完成"
