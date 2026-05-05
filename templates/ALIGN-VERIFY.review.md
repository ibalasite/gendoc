---
doc-type: ALIGN-VERIFY
target-path: docs/ALIGN_REPORT.md
special-skill: gendoc-align-check
reviewer-roles:
  primary: "資深 Software Architect（對齊最終驗證者）"
  primary-scope: "全系統最終一致性確認、無殘留差距"
quality-bar: "所有文件間的對齊差距已清零，ALIGN_REPORT.md 最終狀態顯示四個維度全部通過。"
---

# ALIGN-VERIFY Review Items

本檔案定義 gendoc-align-check（驗證階段）執行後的審查標準。這是 Align 流程的最終確認步驟。

---

## §A — 最終一致性確認

**[CRITICAL] AV-01 — 四個維度全部通過**

**Check**: 最終 ALIGN_REPORT.md 是否顯示四個對齊維度（docs↔docs、docs↔code、code↔test、docs↔test）全部無差距（PASS）？

**Risk**: 任何殘留差距意味著系統文件仍不一致，影響後續開發。

**Fix**: 若有殘留差距，返回 ALIGN-FIX 流程重新修復。

---

**[HIGH] AV-02 — 無新增差距**

**Check**: 與上次 ALIGN 執行比較，ALIGN-VERIFY 是否發現任何新差距（即 ALIGN-FIX 修復後引入的新問題）？

**Risk**: 修復過程引入新差距表明修復邏輯有誤，需要更謹慎的修復策略。

**Fix**: 針對新差距進行精確修復，避免連帶修改範圍過大。

---

## Self-Check：最終一致性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。

**指令：**
1. 讀取最終 `docs/ALIGN_REPORT.md`
2. 確認四個維度的驗證狀態均為通過（PASS / 無差距）
3. 任何維度仍有未解決差距 → CRITICAL finding

**通過條件：**
- 所有四個對齊維度均顯示 PASS 或「無差距」
- ALIGN_REPORT.md 最終版本已 commit（有 git 記錄）
