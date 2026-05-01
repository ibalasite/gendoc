# CONSTANTS — 業務常數與量化參數文件（已棄用）

> **[DEPRECATED]** 此文件自 pipeline v3.0 起已棄用。
>
> CONSTANTS 不再是獨立 pipeline step。業務常數現由 **EDD Pass-0** 負責提取，
> 輸出至 `docs/CONSTANTS.md`（結構相同）和 `docs/constants.json`。
>
> **遷移方式：** 執行 `/gendoc edd`，EDD Pass-0 會自動生成並維護 CONSTANTS 內容。
> 不需要單獨執行 `/gendoc constants`。

<!-- 跨文件數值一致性的唯一真相來源（由 EDD Pass-0 生成） -->
<!-- 所有下游文件（EDD/BDD/test-plan/runbook）必須讀取此文件並引用，不得自行填寫未驗證數字 -->

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **DOC-ID** | CONSTANTS-{{PROJECT_CODE}}-{{YYYYMMDD}} |
| **產品名稱** | {{PROJECT_NAME}} |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **上游 PRD** | [PRD.md](PRD.md) |
| **同步輸出** | [constants.json](constants.json) |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初稿（從 PRD 提取） |

---

## 使用指引

> ⚠️ **唯一真相來源**：本文件中所有數值均來源於 PRD，
> 下游文件（EDD/BDD/test-plan/runbook）必須引用此文件中的數值，
> **不得在下游文件中自行定義任何量化數值**。
> 若發現 PRD 與本文件有衝突，以 PRD 為準並更新本文件。

---

## §1 遊戲/產品核心數值（Game/Product Core Values）

| 常數名稱 | 數值 | 單位 | 說明 | PRD 來源 |
|---------|------|------|------|---------|
| {{CONSTANT_NAME_1}} | {{VALUE_1}} | {{UNIT_1}} | {{DESCRIPTION_1}} | PRD §{{SECTION}} |
| {{CONSTANT_NAME_2}} | {{VALUE_2}} | {{UNIT_2}} | {{DESCRIPTION_2}} | PRD §{{SECTION}} |

---

## §2 倍率與賠率（Multipliers & Payouts）

| 常數名稱 | 數值 | 說明 | PRD 來源 |
|---------|------|------|---------|
| {{MULTIPLIER_NAME}} | {{MULTIPLIER_VALUE}}x | {{DESCRIPTION}} | PRD §{{SECTION}} |

---

## §3 閾值與觸發條件（Thresholds & Triggers）

| 常數名稱 | 數值 | 單位 | 觸發條件說明 | PRD 來源 |
|---------|------|------|------------|---------|
| {{THRESHOLD_NAME}} | {{THRESHOLD_VALUE}} | {{UNIT}} | {{TRIGGER_DESCRIPTION}} | PRD §{{SECTION}} |

---

## §4 SLO / SLI 目標（Service Level Objectives）

| 指標名稱 | 目標值 | 測量方式 | PRD 來源 |
|---------|--------|---------|---------|
| 可用性（Availability） | {{AVAILABILITY}}% | {{MEASUREMENT_METHOD}} | PRD §{{SECTION}} |
| 回應時間 P99 | {{P99_LATENCY}}ms | API 呼叫延遲 | PRD §{{SECTION}} |
| 錯誤率 | < {{ERROR_RATE}}% | HTTP 5xx 比率 | PRD §{{SECTION}} |
| {{CUSTOM_SLO_NAME}} | {{CUSTOM_SLO_VALUE}} | {{CUSTOM_SLO_METHOD}} | PRD §{{SECTION}} |

---

## §5 RTP / 機率設計（Return-to-Player / Probability Design）

> 若非遊戲類型，此章節可標記 N/A。

| 常數名稱 | 數值 | 說明 | PRD 來源 |
|---------|------|------|---------|
| 目標 RTP | {{RTP_TARGET}}% | 整體回報率目標 | PRD §{{SECTION}} |
| {{SCENARIO_NAME}} RTP | {{SCENARIO_RTP}}% | {{SCENARIO_DESCRIPTION}} | PRD §{{SECTION}} |

---

## §6 Rate Limit 設定（Rate Limiting）

| 端點 / 功能 | 限制值 | 時間窗口 | 說明 | PRD 來源 |
|-----------|--------|---------|------|---------|
| {{ENDPOINT_1}} | {{RATE_LIMIT_1}} | {{WINDOW_1}} | {{RL_DESC_1}} | PRD §{{SECTION}} |
| {{ENDPOINT_2}} | {{RATE_LIMIT_2}} | {{WINDOW_2}} | {{RL_DESC_2}} | PRD §{{SECTION}} |

---

## §7 業務規則數值（Business Rule Values）

| 常數名稱 | 數值 | 單位 | 業務規則描述 | PRD 來源 |
|---------|------|------|------------|---------|
| {{BUSINESS_RULE_NAME}} | {{BUSINESS_RULE_VALUE}} | {{UNIT}} | {{BUSINESS_RULE_DESC}} | PRD §{{SECTION}} |

---

## §8 系統容量規劃（Capacity Planning Constants）

| 常數名稱 | 數值 | 單位 | 說明 | PRD 來源 |
|---------|------|------|------|---------|
| 最大並發用戶 | {{MAX_CONCURRENT_USERS}} | 人 | 設計目標並發量 | PRD §{{SECTION}} |
| 峰值 TPS | {{PEAK_TPS}} | 次/秒 | 峰值交易數 | PRD §{{SECTION}} |
| 資料保留期限 | {{DATA_RETENTION}} | 天 | 日誌/交易紀錄保留 | PRD §{{SECTION}} |

---

## Appendix A：constants.json 同步格式

本文件生成後，必須同步輸出 `docs/constants.json`，格式如下：

```json
{
  "version": "1.0",
  "generated_from": "docs/PRD.md",
  "last_updated": "{{DATE}}",
  "core": {
    "{{CONSTANT_NAME_1}}": {{VALUE_1}},
    "{{CONSTANT_NAME_2}}": {{VALUE_2}}
  },
  "slo": {
    "availability": {{AVAILABILITY}},
    "p99_latency_ms": {{P99_LATENCY}},
    "error_rate_pct": {{ERROR_RATE}}
  },
  "rate_limits": {
    "{{ENDPOINT_1}}": {"limit": {{RATE_LIMIT_1}}, "window": "{{WINDOW_1}}"}
  }
}
```
