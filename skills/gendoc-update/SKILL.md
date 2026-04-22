---
name: gendoc-update
description: |
  手動升級 gendoc skills（git pull + install）。
  呼叫時機：user 說「升級 gendoc」「gendoc 更新」「update gendoc」「/gendoc-upgrade」。
allowed-tools:
  - Bash
---

# gendoc-upgrade — 手動升級 gendoc

> 版本更新通常由 SessionStart hook 自動處理（每小時一次）。  
> 此 skill 供手動觸發使用。

---

## Step 1：定位 repo

```bash
for _c in "$HOME/projects/gendoc" "$HOME/MYDEVSOP"; do
  if [[ -d "$_c/.git" ]] && [[ -f "$_c/bin/gendoc-upgrade" ]]; then
    _REPO="$_c"; break
  fi
done

if [[ -z "${_REPO:-}" ]]; then
  echo "❌ 找不到 gendoc git repo（需先執行 ./setup 並設定 git remote）"
  exit 1
fi
```

## Step 2：執行升級

```bash
bash "$_REPO/bin/gendoc-upgrade"
```

升級完成後告知使用者：「✅ gendoc 已更新至最新版，重開 Claude Code 讓新 skill 生效。」

## 若 repo 不存在（尚未初始化）

輸出安裝指引：
```
gendoc 尚未設定 git remote，自動更新無法運作。
請先：
  1. cd ~/projects/gendoc
  2. git init && git remote add origin <your-repo-url>
  3. git push -u origin main
  4. 在其他機器：git clone <url> ~/projects/gendoc && cd ~/projects/gendoc && ./setup
```
