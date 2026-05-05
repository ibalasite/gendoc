---
doc-type: ALIGN-FIX
target-path: docs/ALIGN_REPORT.md
special-skill: gendoc-align-fix
reviewer-roles:
  primary: "資深 Software Architect（對齊修復審查者）"
  primary-scope: "修復完整性、前後一致性驗證、無新引入差距"
quality-bar: "所有 ALIGN 報告中標記的差距均已被修復，ALIGN_REPORT.md 更新反映修復後狀態，無新引入的不一致。"
---

# ALIGN-FIX Review Items

本檔案定義 gendoc-align-fix 執行後的審查標準。審查對象為修復後更新的 `docs/ALIGN_REPORT.md` 及相關文件。

---

## §A — 修復完整性驗證

**[CRITICAL] AF-01 — 所有標記差距均已修復**

**Check**: 對比修復前後的 ALIGN_REPORT.md，所有原始差距是否均已標記為「已修復」或「已確認無需修復（附理由）」？

**Risk**: 未修復的差距留在報告中，下次 align-check 重新觸發時會造成循環。

**Fix**: 重新執行 align-fix，確保所有 CRITICAL 和 HIGH 差距均已處理。

---

**[HIGH] AF-02 — 修復未引入新差距**

**Check**: 修復操作是否在修改的文件中引入新的不一致（例如修改 API.md 後，SCHEMA.md 或 BDD 的引用出現新差距）？

**Risk**: 連帶修改可能引入更多差距，導致修復工作發散。

**Fix**: 對修復涉及的文件重新執行 align-check（局部），確認無新差距引入。

---

## Self-Check：修復結果驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。

**指令：**
1. 讀取 `docs/ALIGN_REPORT.md`，確認修復後的報告格式正確
2. 計算仍標記為「未修復」的差距數量
3. 任何 CRITICAL 或 HIGH 差距仍未修復 → CRITICAL finding

**通過條件：**
- 所有 CRITICAL 差距已修復（或有明確的不修復理由）
- 所有 HIGH 差距已修復（或降級為 MEDIUM 並有理由）
- ALIGN_REPORT.md 的修復狀態標記完整
