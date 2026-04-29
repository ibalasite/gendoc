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

# Templates 安裝到 ~/.claude/gendoc/templates/ — 與 gencode 同層級，不依賴開發 repo
TEMPLATES_SRC="$GENDOC_DIR/templates"
TEMPLATES_DST="$HOME/.claude/gendoc/templates"
if [[ -d "$TEMPLATES_SRC" ]]; then
  mkdir -p "$TEMPLATES_DST"
  cp -r "$TEMPLATES_SRC/." "$TEMPLATES_DST/"
  log "  ✓ templates → $TEMPLATES_DST"
fi

# Clear throttle stamp so next session will check for further updates
rm -f "$GENDOC_DIR/.last-update-check" 2>/dev/null || true

# Write installed version stamp so Fix-D version checks work
_VERSION_DIR="$HOME/.claude/gendoc"
mkdir -p "$_VERSION_DIR"
git -C "$GENDOC_DIR" rev-parse --short HEAD 2>/dev/null > "$_VERSION_DIR/.installed-version" || true
log "  ✓ version stamp → $_VERSION_DIR/.installed-version"

log "[install] 完成"
