---
name: gendoc-upgrade
description: |
  手動升級 gendoc skills（git pull + re-deploy）。
  呼叫時機：user 說「升級 gendoc」「gendoc 更新」「update gendoc」「/gendoc-upgrade」。
allowed-tools:
  - Bash
---

# gendoc-upgrade — 手動升級 gendoc

> 版本更新通常由 SessionStart hook 自動處理（每小時一次）。  
> 此 skill 供手動觸發使用。

---

## Step 1：執行升級

```bash
source "$HOME/.claude/skills/gendoc/bin/gendoc-env.sh"

if [[ ! -d "$GENDOC_DIR/.git" ]]; then
  echo "❌ 找不到 gendoc runtime（$GENDOC_DIR）"
  echo "請先安裝：git clone https://github.com/ibalasite/gendoc.git ~/.claude/skills/gendoc && ~/.claude/skills/gendoc/setup"
  exit 1
fi

bash "$GENDOC_DIR/setup" upgrade
```

升級完成後告知使用者：「✅ gendoc 已更新至最新版，重開 Claude Code 讓新 skill 生效。」
