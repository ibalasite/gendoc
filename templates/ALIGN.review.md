---
doc-type: ALIGN
target-path: docs/ALIGN_REPORT.md
special-skill: gendoc-align-check
reviewer-roles:
  primary: "資深 Software Architect（文件一致性審查者）"
  primary-scope: "跨文件一致性、上游對齊完整性、ALIGN_REPORT 結構正確性"
quality-bar: "ALIGN_REPORT.md 完整記錄四個對齊維度的差距，每個差距有明確的 Fix 建議，無遺漏的對齊維度。"
---

# ALIGN Review Items

本檔案定義 `docs/ALIGN_REPORT.md`（align-check 輸出）的審查標準。

---

## §A — 四維對齊覆蓋完整性

**[CRITICAL] AL-01 — 四個對齊維度均已覆蓋**

**Check**: ALIGN_REPORT.md 是否涵蓋以下四個維度？
1. docs ↔ docs（文件間一致性）
2. docs ↔ code（文件與程式碼一致性）
3. code ↔ test（程式碼與測試一致性）
4. docs ↔ test（文件與測試一致性）

**Risk**: 缺少任何維度意味著系統性的不一致沒有被發現。

**Fix**: 補充缺少的維度分析，確保四個維度均有對齊結果。

---

**[HIGH] AL-02 — 每個差距有明確 Fix 建議**

**Check**: ALIGN_REPORT.md 中每個標記的差距（inconsistency）是否都有具體的修復建議？

**Risk**: 無 Fix 建議的差距報告無法指導後續修復工作。

**Fix**: 為每個差距補充具體的修復步驟或文件更新建議。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。

**指令：**
1. 讀取 `docs/ALIGN_REPORT.md`，確認包含以下區段：四個對齊維度的分析結果
2. 每個維度下有差距清單（或明確說明「無差距」）
3. 每個差距有 Fix 建議
4. 任何缺失 → CRITICAL finding

**通過條件：**
- ALIGN_REPORT.md 存在且非空
- 四個對齊維度均有對應的分析結果章節
- 每個差距有對應的 Fix 建議
