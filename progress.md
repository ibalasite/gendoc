# gendoc-repair v2.0 進度追蹤

**目標**：把任何不完整的目標專案補到與 `gendoc-auto` + `gendoc-flow` 從頭執行完全一致的狀態。
**硬性約束**：只動 `skills/gendoc-repair/SKILL.md`，不碰其他任何 skill。

---

## 符號說明

| 符號 | 意義 |
|------|------|
| `[ ]` | 待執行 |
| `[x]` | 已完成 + commit done |
| `[~]` | 進行中 |

---

## 前置文件更新

| 狀態 | 項目 |
|------|------|
| `[x]` | CLAUDE.md — 新增 repair 設計原則區段（目標定義 / DRYRUN 相位邊界 / 修改邊界 / 七項需求摘要） |
| `[x]` | PRD.md — 新增 v3.1 changelog entry（repair v2.0 完整摘要） |
| `[x]` | README.md — 更新 repair skill 說明行 |
| `[x]` | progress.md — 本文件建立 |

---

## TASK-R1：Step 1 Phase 邊界識別

**目標**：diff 結果分三區顯示，而非 flat list。

**驗收標準**：
- 輸出包含 `Phase A（pre-DRYRUN）缺 N 個`、`DRYRUN Gate：[ 狀態 ]`、`Phase B（post-DRYRUN）缺 M 個`
- 機器可讀標記：`PHASE_A_MISSING_COUNT:N`、`DRYRUN_GATE_STATUS:xxx`、`PHASE_B_MISSING_COUNT:M`
- 條件過濾邏輯與 gendoc-flow 保持完全一致

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 修改 Step 1 Python diff 腳本，在 diff 計算後加入三區分類邏輯 |
| `[ ]` | 更新 Step 1 輸出格式：分區表格 + 機器可讀標記 |
| `[ ]` | 更新 Step 2（無缺漏判斷）也檢查三區均為 0 |
| `[ ]` | commit [done]: TASK-R1 |

---

## TASK-R2：Step 1.6 DRYRUN 三態偵測

**目標**：偵測 DRYRUN 狀態為「未執行 / 用預設值執行 / 正常執行」。

**驗收標準**：
- 新增 Step 1.6 到 repair SKILL.md
- 輸出 `DRYRUN_STATUS: NONE | DEFAULTS | OK`
- 偵測依據：completed_steps 是否含 DRYRUN + .gendoc-rules/*.json 數量 + MANIFEST.md 是否有「預設值」標記

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 在 Step 1 之後、Step 2 之前，新增 Step 1.6 區塊 |
| `[ ]` | 實作三態偵測邏輯（bash + python3） |
| `[ ]` | 提取 `_DRYRUN_STATUS`、`_RULES_COUNT`、`_DRYRUN_USED_DEFAULTS` 三個變數 |
| `[ ]` | commit [done]: TASK-R2 |

---

## TASK-R3：Step 1.6 DRYRUN 上游就緒度預檢

**目標**：在建議執行 DRYRUN 前，預先檢查 EDD/PRD/ARCH 的內容是否足夠豐富。

**驗收標準**：
- 三份文件不足時，顯示 ⚠️ 警告：「DRYRUN 將使用保守預設值，品質閘門可能偏鬆」
- 具體門檻：EDD entity ≥ 3、PRD US-* 標題 ≥ 3、ARCH table rows ≥ 4
- 輸出 `UPSTREAM_READY: true | false`

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 在 Step 1.6 末尾加入上游就緒度掃描（bash grep 計數）|
| `[ ]` | 不足時設 `_UPSTREAM_READY=false` 並顯示詳細說明 |
| `[ ]` | commit [done]: TASK-R3 |

---

## TASK-R4：Step 1.6 DRYRUN 基線過時偵測

**目標**：若 EDD/PRD/ARCH 比 `.gendoc-rules/` 更新，標示基線可能過時。

**驗收標準**：
- 輸出 `DRYRUN_STALE: true | false`
- 過時時顯示 ⚠️ 及時間戳差異說明
- 若無 git history（非 git 專案），靜默跳過此檢查

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 在 Step 1.6 加入 git log 時間戳比對邏輯 |
| `[ ]` | 比對 EDD/PRD/ARCH 最新 commit vs .gendoc-rules/ 最新 commit |
| `[ ]` | 過時時設 `_DRYRUN_STALE=true` + 警告訊息 |
| `[ ]` | commit [done]: TASK-R4 |

---

## TASK-R5：Step 1.5 品質門檻驗證升級

**目標**：原本只查檔案存在，升級為讀 `.gendoc-rules/<step-id>-rules.json` 驗品質。

**驗收標準**：
- 若 rules.json 存在，驗三項：min_h2_sections、required_sections 存在、no_placeholder_strings
- 新增 QUALITY_FAIL 嚴重性層級，與「未完成」、「語意不完整」分開列報
- 若 .gendoc-rules/ 不存在（DRYRUN 未跑），Step 1.5 退化回原有行為（不中斷）

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 在 Step 1.5 Python 腳本末尾加入 rules.json 品質驗證 loop |
| `[ ]` | 驗 min_h2_sections（數標題行數 vs 門檻）|
| `[ ]` | 驗 required_sections（grep section 標題是否存在）|
| `[ ]` | 驗 no_placeholder_strings（grep `{{[A-Z_]+}}` pattern）|
| `[ ]` | 新增 QUALITY_FAIL 輸出段落 + 機器可讀標記 `QUALITY_FAIL_COUNT:N` |
| `[ ]` | commit [done]: TASK-R5 |

---

## TASK-R6：Step 3 Phase-aware 互動提示

**目標**：依實際缺漏相位，給出不同的補跑引導（三條件分支）。

**驗收標準**：
- **情境 A**（Phase A 缺漏）：現有補跑流程，保持不變
- **情境 B**（Phase A 完整 + DRYRUN 未跑）：提示 DRYRUN 重要性，選項包含「先執行 DRYRUN」
- **情境 C**（DRYRUN 完整 + Phase B 缺漏）：顯示品質基線可用（N rules files），選項含兩階段補跑

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 重構 Step 3 為三條件分支（依 `_PHASE_A_MISSING_COUNT`、`_DRYRUN_STATUS`、`_PHASE_B_MISSING_COUNT` 判斷）|
| `[ ]` | 情境 B：新增 DRYRUN 引導說明文字 + 選項 [1] 先跑 DRYRUN |
| `[ ]` | 情境 C：顯示 rules files 數量 + 選項 [1] 兩階段補跑 |
| `[ ]` | SPAWNED_SESSION 時情境 B/C 自動選擇合理預設 |
| `[ ]` | commit [done]: TASK-R6 |

---

## TASK-R7：兩階段補跑模式

**目標**：完整實作「先補 Phase A → 自動觸發 DRYRUN → 再補 Phase B」的三段接力。

**驗收標準**：
- 選擇兩階段模式後，repair 依序執行：
  1. 設 `start_step` = 第一個 Phase A 缺漏步驟，呼叫 gendoc-flow
  2. gendoc-flow 完成後，偵測 ARCH 是否已在 completed_steps
  3. ARCH 完成 → 呼叫 gendoc-gen-dryrun（Skill tool）
  4. DRYRUN 完成 → 設 `start_step` = 第一個 Phase B 缺漏步驟，再呼叫 gendoc-flow

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 在 Step 4 新增兩階段模式分支 |
| `[ ]` | Phase A 補跑：設 `start_step` = first Phase A missing，呼叫 gendoc-flow |
| `[ ]` | DRYRUN 觸發：Skill tool 呼叫 `gendoc-gen-dryrun` |
| `[ ]` | Phase B 補跑：重讀 state file，更新 `start_step`，呼叫 gendoc-flow |
| `[ ]` | 加入重新讀取 state file 的邏輯（Phase A 完成後 state 已更新）|
| `[ ]` | commit [done]: TASK-R7 |

---

## 完成標準

所有 TASK-R1 ~ R7 的 `[x]` 均打勾，且：
- `gendoc-repair` 在新安裝的目標專案（0 完成步驟）可正確引導完整補跑
- `gendoc-repair` 在 Phase A 完整但 DRYRUN 未跑的專案，正確引導 DRYRUN
- `gendoc-repair` 在已有部分 Phase B 完成的專案，正確驗品質並補缺
