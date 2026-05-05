---
reviewer-roles:
  - "PRD 數值稽核師（PRD Value Auditor）：逐一核對 CONSTANTS.md 每個數值與 PRD 對應來源，驗證數值正確性"
  - "一致性審查員（Consistency Reviewer）：確認 constants.json 與 CONSTANTS.md 數值完全吻合，確認下游文件引用的數值與本文件一致"
quality-bar: "全文無 {{PLACEHOLDER}}；每個數值有 PRD §來源；constants.json 已生成且與 .md 一致；§4 SLO 三項均有量化數值；§8 容量三項均有量化數值；§7 業務規則已填入或明確標記「本 PRD 無額外業務規則數值」"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥12 個）均存在且有實質內容"
  - "所有常數有具體數值（無 TBD 或 {{PLACEHOLDER}}）"
status: DEPRECATED
deprecated-since: pipeline-v3.0
replaced-by: EDD Pass-0 (in EDD.gen.md)
upstream-alignment:
  - docs/PRD.md       # 數值真相來源對照
  - docs/BRD.md       # SLO 業務依據
  - docs/constants.json  # JSON 同步一致性
---

> **[DEPRECATED — pipeline v3.0]**
>
> CONSTANTS 不再是獨立 pipeline step，此審查規則不應被單獨呼叫。
>
> 業務常數現由 **EDD Pass-0** 生成，審查應在 EDD Review 環節中一併完成。
> 詳見 `templates/EDD.review.md` 中的 Pass-0 相關審查項目。
>
> **若需驗證 CONSTANTS 品質**：執行 `/reviewdoc edd` 或 `/reviewtemplate EDD`。

# CONSTANTS Review 標準（已棄用）

## [CRITICAL] 1 — 存在未替換的 Placeholder

**Check**：全文搜尋 `{{` 字樣，任何殘留 `{{XXX}}` 視為未完成。

**Risk**：下游文件引用空值，導致 EDD/BDD/runbook 的數值全部錯誤。

**Fix**：逐一回到 PRD 對應章節找實際數值填入；確無對應則填 `TBD（PRD 未定義）`，不得留 `{{...}}`。

---

## [CRITICAL] 2 — constants.json 未生成或與 .md 不一致

**Check**：確認 `docs/constants.json` 存在；抽取 5 個數值比對 .md 與 json 的一致性。

**Risk**：下游 AI 讀取 constants.json 取得的數值與 .md 不同，導致不同文件用不同值。

**Fix**：重新生成 constants.json，確保所有數值完整同步；TBD 值記為 `null`。

---

## [CRITICAL] 3 — 數值與 PRD 來源不符

**Check**：隨機抽取 §1-§8 的 5 個數值，讀取對應 PRD §來源，驗證數值是否一致。

**Risk**：CONSTANTS.md 的數值是 AI 推斷，而非 PRD 實際定義，導致全局數值錯誤。

**Fix**：對不符的數值，讀取 PRD 來源章節重新提取正確值並更新。

---

## [HIGH] 4 — §4 SLO 關鍵三項缺失或為 TBD

**Check**：確認 §4 的可用性（%）、P99 延遲（ms）、錯誤率（%）三項均為具體數值，非 TBD。

**Risk**：下游 EDD 的 SLO/SLI 章節、runbook 的告警閾值無法準確設計。

**Fix**：若 PRD 未明確，讀取 BRD §成功指標補充，或將 TBD 原因說明清楚（標注需要 PM 決策）。

---

## [HIGH] 5 — §8 容量規劃三項缺失或為 TBD

**Check**：確認最大並發用戶、峰值 TPS、資料保留期限三項均為具體數值。

**Risk**：EDD §11 容量規劃、runbook 的 infrastructure sizing 無根據。

**Fix**：從 PRD §非功能需求 或 BRD §業務規模 補充；若 PRD 未定義，標記 TBD 並說明業務依據。

---

## [HIGH] 6 — §2 倍率數值完整性與範圍驗證

**Check**：確認 §2 所有倍率數值均已填入（無空白行/placeholder），並與 PRD 倍率定義章節比對，驗證最大倍率未超過 PRD 上限。

**Risk**：倍率錯誤直接導致遊戲賠率計算錯誤，影響 EDD 的機率引擎設計。

**Fix**：對照 PRD 倍率章節逐一核驗，確認每個倍率數值與觸發條件均已正確填入；非遊戲類型確認 §2 已標記 N/A。

---

## [HIGH] 7 — 每個數值缺乏 PRD §來源標注

**Check**：§1-§8 的每個數值的「PRD 來源」欄位是否填寫了具體的 §章節編號。

**Risk**：數值可信度無法驗證，未來 PRD 更新時無法追蹤哪些常數需要同步。

**Fix**：補上每個數值的 PRD 來源章節號碼；若確實無法追溯，標記 `[NO_SOURCE]`。

---

## [MEDIUM] 8 — §7 業務規則數值完整性

**Check**：確認 §7 中的項目涵蓋了 PRD 中所有未被 §1-§6 歸類的量化業務規則；若 PRD 確實無此類數值，§7 應標記「本 PRD 無額外業務規則數值」而非保留 placeholder。

**Risk**：§7 空白或僅有 placeholder 導致下游 BDD 的業務規則測試案例缺少數值依據。

**Fix**：重新掃描 PRD，找出未被 §1-§6 涵蓋的量化業務規則補入 §7；確無則明確標記「本 PRD 無額外業務規則數值」（不得保留 placeholder）。

---

## [MEDIUM] 9 — §3 觸發條件缺乏完整觸發-結果描述

**Check**：§3 每條觸發條件是否同時描述了「觸發條件」和「觸發後的行為/結果」。

**Risk**：下游 BDD 的 Given-When-Then 無法準確描述業務行為。

**Fix**：補充每個閾值的觸發結果，例如：「超過 N 觸發 [具體行為]」。

---

## [MEDIUM] 10 — 發現 PRD 章節間數值衝突未標注

**Check**：比對 §1-§8 中同類數值（如：不同章節提到的同一倍率），確認是否有衝突。

**Risk**：AI 不知道應用哪個版本的數值，下游文件各自採用不同值。

**Fix**：對衝突數值加入 `[CONFLICT: PRD §X 值=A vs PRD §Y 值=B]` 標注，並說明採用依據。

---

## [MEDIUM] 11 — §5 RTP（遊戲類型）缺乏多情境拆分

**Check**：遊戲類型的 §5 是否涵蓋所有遊戲情境（Main/ExtraBet/BuyFG 等）的獨立 RTP 值。

**Risk**：EDD 的機率引擎設計、BDD 的測試用例缺少獨立情境的數值依據。

**Fix**：從 PRD 的機率設計章節補充各情境的 RTP 目標值；非遊戲類型確認標記 N/A。

---

## [LOW] 12 — §6 Rate Limit 未覆蓋主要業務端點

**Check**：§6 是否至少涵蓋登入、主要業務 API、管理後台的 rate limit 設定。

**Risk**：EDD §9 安全設計的 rate limit 無數值依據。

**Fix**：補充缺少的端點；若 PRD 未定義，標記行業通用值（如：登入 10次/分鐘）並說明。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/CONSTANTS.md`，提取所有 `^## ` heading（含條件章節），共約 12 個
2. 讀取 `docs/CONSTANTS.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
