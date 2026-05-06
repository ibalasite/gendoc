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
# 不依賴 source：直接計算路徑，確保跨 subprocess 可用
_GENDOC_DIR="${GENDOC_DIR:-$HOME/.claude/skills/gendoc}"

if [[ ! -d "$_GENDOC_DIR/.git" ]]; then
  echo "❌ 找不到 gendoc runtime（$_GENDOC_DIR）"
  echo "請先安裝：git clone https://github.com/ibalasite/gendoc.git ~/.claude/skills/gendoc && ~/.claude/skills/gendoc/setup"
  exit 1
fi

bash "$_GENDOC_DIR/setup" upgrade
```

升級完成後告知使用者：「✅ gendoc 已更新至最新版。」
