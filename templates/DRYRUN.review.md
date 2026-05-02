---
doc-type: DRYRUN
version: 1.0.0
reviewer-roles:
  - role: Pipeline Completeness Auditor
    scope: MANIFEST.md correctness, placeholder elimination, quantitative anchor accuracy
  - role: Rules JSON Validator
    scope: .gendoc-rules/ completeness, JSON schema correctness, formula application
quality-bar:
  - Zero bare {{PLACEHOLDER}} in MANIFEST.md output
  - §2.1 four quantitative anchors are computed values (not default 0)
  - §2.2 conditional steps table has ≥ 11 rows
  - §4 per-step completeness standards table covers ≥ 20 steps
  - .gendoc-rules/ has one JSON per active step
upstream-alignment:
  - EDD.md entity_count / rest_endpoint_count bash commands match §2.1 parameter definitions
  - PRD.md user_story_count grep pattern matches §2.1 description
  - ARCH.md arch_layer_count awk command matches §2.1 description
  - pipeline.json condition logic matches §2.2 condition column definitions
  - .gendoc-state.json client_type / has_admin_backend keys match Step 3 condition table
  - `.gendoc-rules/<step-id>-rules.json` schema matches Step 4 JSON template（step_id / output_files / anti_fake_rules 三欄均存在且型別正確）
---

# DRYRUN.review.md — Pipeline Execution Manifest 審查標準

---

## Layer 1：核心輸出完整性（共 3 項）

### [CRITICAL] R-01：MANIFEST.md 含裸 Placeholder

**Check**：掃描輸出的 `docs/MANIFEST.md`，確認無任何 `{{...}}` 格式的未替換 placeholder。重點確認以下欄位已替換：
- Document Control：`{{GENERATED_DATE}}`、`{{PIPELINE_VERSION}}`、`{{EDD_VERSION}}`、`{{CLIENT_TYPE}}`、`{{HAS_ADMIN_BACKEND}}`、`{{ACTIVE_STEPS_COUNT}}`、`{{SKIPPED_STEPS_COUNT}}`
- §2.1 System Parameters：`{{ENTITY_COUNT}}`、`{{REST_ENDPOINT_COUNT}}`、`{{USER_STORY_COUNT}}`、`{{ARCH_LAYER_COUNT}}`
- §2.2 Active Conditional Steps：所有 `{{*_ACTIVE}}` placeholder
- §3 Mandatory Steps Checklist：所有 `{{*_STATUS}}` placeholder
- §4 quantitative columns：`{{ARCH_LAYER_COUNT_PLUS_2}}` 及所有量化閾值 placeholder

**Risk**：殘留 placeholder 代表 DRYRUN 生成不完整；後續所有步驟 gate-check 引用的量化基準都將失效，形成系統性品質盲點。

**Fix**：逐行修正 DRYRUN.gen.md Step 6 的替換邏輯，確保所有 `{{PLACEHOLDER}}` 在填充時均有對應的計算值或讀取來源。

---

### [CRITICAL] R-02：.gendoc-rules/ 目錄不完整

**Check**：確認 gen.md 明確要求為每個 Active 步驟生成 `<step-id>-rules.json`，且 Step 4 包含：
- `mkdir -p .gendoc-rules` 指令
- rules JSON 的完整 schema（含 `step_id`、`output_files`、`anti_fake_rules` 欄位）
- 說明 Skipped 步驟不生成 JSON

**Risk**：.gendoc-rules/ 缺少任何 active step 的 JSON → gate-check 無法載入對應步驟的驗收標準，等同於讓步驟跳過品質門。

**Fix**：確認 gen.md Step 4 的 JSON schema 完整，並在 Quality Gate Step 7 中包含「Active step 數 = rules JSON 文件數」的驗證命令。

---

### [CRITICAL] R-03：Quality Gate 缺少殘留 Placeholder 驗證命令

**Check**：確認 gen.md Step 7 Quality Gate 表格包含以下驗證項：
1. 無殘留 placeholder（`grep -n '{{' docs/MANIFEST.md`）
2. .gendoc-rules/ 完整性驗證（`ls .gendoc-rules/*.json | wc -l`）
3. 量化錨點非零驗證
4. 條件步驟一致性驗證
5. rules JSON 語法驗證（`jq .`）

**Risk**：缺少任一驗證 → AI 生成完後不做自我檢查，品質門形同虛設。

**Fix**：在 gen.md Step 7 Quality Gate 表格補充缺少的驗證命令列。

---

## Layer 2：量化錨點正確性（共 3 項）

### [CRITICAL] R-04：§2.1 量化錨點 bash 命令不正確

**Check**：逐一核對 gen.md Step 2 的四個 bash 命令：
- **entity_count**：`grep -c '^\s*class ' docs/EDD.md`（偵測 Mermaid classDiagram 中的 class 定義）
- **rest_endpoint_count**：`grep -cE '(<<REST>>|<<Interface>>|HTTP...(GET|POST|PUT|DELETE|PATCH))' docs/EDD.md`；且含 fallback：若 < 5，使用預設值 10
- **user_story_count**：`grep -c '^## US-\|^### US-' docs/PRD.md`
- **arch_layer_count**：`awk '/## §3|^## 3 |^# §3/{found=1} found && /^\|[^-]/{count++} ...'`；且含最小值 4

確認每個命令的 fallback 邏輯與 DRYRUN.md §2.1 說明欄完全一致。

**Risk**：計算命令錯誤 → 所有依賴錨點的量化門檻均基於錯誤數字，等同於整個品質系統失效。

**Fix**：比對 DRYRUN.md §2.1 的說明欄，修正 gen.md Step 2 中與說明不符的 bash 命令。

---

### [HIGH] R-05：§4 Per-Step 量化門檻公式未應用錨點

**Check**：核對 gen.md Step 5 的六個量化公式是否都有使用錨點變數（而非常數）：
- API：`min_endpoint_count = max(_REST_COUNT, 5)`
- SCHEMA：`min_table_count = max(_ENTITY_COUNT, 3)`
- test-plan：`min_h2_sections = _ARCH_LAYER_COUNT + 2`
- RTM：`min_row_count = _US_COUNT`
- BDD-server：`min_scenario_count = ceil(_US_COUNT * 0.8)`
- BDD-client：`min_scenario_count = ceil(_US_COUNT * 0.6)`

確認 gen.md Step 6 的填充步驟包含所有 placeholder 的計算結果替換（含 `{{ARCH_LAYER_COUNT_PLUS_2}}`）。

**Risk**：公式未套用錨點（或 Step 6 未替換對應 placeholder）→ MANIFEST.md §4 殘留 placeholder，gate-check 無法讀取門檻值。

**Fix**：在 gen.md Step 6 第 4 小點補充所有量化 placeholder 的計算替換，確保 `{{ARCH_LAYER_COUNT_PLUS_2}}` 等均被替換。

---

### [HIGH] R-06：§2.1 System Parameters 說明欄與 bash 命令不一致

**Check**：比對 DRYRUN.md §2.1 表格「說明」欄的 grep 命令描述（括號內）與 gen.md Step 2 的實際 bash 命令。例如：
- `entity_count` 說明欄：`grep -c '^\s*class '` → gen.md Step 2-A 是否相符？
- `user_story_count` 說明欄：`grep -c '^## US-\|^### US-'` → gen.md Step 2-C 是否相符？

**Risk**：骨架說明欄與 gen.md 命令不一致 → AI 可能優先採用骨架的說明，導致生成的 MANIFEST.md §2.1 計算邏輯與 gen.md 有偏差。

**Fix**：統一骨架 §2.1 說明欄的括號描述與 gen.md Step 2 命令，以 gen.md 為 Source of Truth。

---

## Layer 3：條件步驟邏輯（共 2 項）

### [HIGH] R-07：§2.2 Active Conditional Steps 表格缺少必要步驟

**Check**：確認 DRYRUN.md §2.2 表格包含以下 11 個條件步驟（全部必要）：
1. PDD（`client_type != none`）
2. VDD（`client_type != none`）
3. FRONTEND（`client_type != none`）
4. AUDIO（`client_type == game`）
5. ANIM（`client_type == game`）
6. CLIENT_IMPL（`client_type != none`）
7. ADMIN_IMPL（`has_admin_backend`）
8. RESOURCE（`client_type != none`）
9. BDD-client（`client_type != none`）
10. MOCK（`client_type != api-only`）
11. PROTOTYPE（`client_type != api-only`）

**Risk**：缺少任何條件步驟 → Active/Skipped 計數不準確，`ACTIVE_STEPS_COUNT` 和 `SKIPPED_STEPS_COUNT` 誤報。

**Fix**：參照 `templates/pipeline.json` 補齊所有條件步驟行。

---

### [MEDIUM] R-08：gen.md Step 3 條件邏輯表格未涵蓋所有條件類型

**Check**：確認 gen.md Step 3 的條件邏輯表格包含所有五種條件類型：
- `always`
- `client_type != none`
- `client_type == game`
- `client_type != api-only`
- `has_admin_backend`

**Risk**：缺少條件類型定義 → AI 判斷 Y/N 時可能對未定義的條件產生錯誤推理。

**Fix**：補充缺少的條件類型及其觸發條件說明。

---

## Layer 4：§3 Mandatory Steps 清單（共 2 項）

### [HIGH] R-09：§3 Mandatory Steps Checklist 缺少必要步驟

**Check**：確認 DRYRUN.md §3 表格包含以下「condition: always」的強制步驟（≥ 16 項）：
IDEA / BRD / PRD / CONSTANTS / EDD / ARCH / API / SCHEMA / UML / test-plan / BDD-server / RTM / runbook / LOCAL_DEPLOY / CICD / DEVELOPER_GUIDE / UML-CICD / ALIGN / CONTRACTS / HTML

**Risk**：強制步驟清單不完整 → MANIFEST.md §3 遺漏步驟，gate-check 無法追蹤這些步驟的完成狀態。

**Fix**：參照 `templates/pipeline.json` 的 `condition: always` 步驟，補齊 §3 表格缺漏行。

---

### [MEDIUM] R-10：§4 Per-Step Completeness Standards 缺少必要步驟行

**Check**：確認 DRYRUN.md §4 表格包含所有必要步驟（≥ 20 行）。特別確認以下高複雜度步驟有明確的量化規則：
- API（含 `min_endpoint_count` 公式）
- SCHEMA（含 `min_table_count` 公式）
- test-plan（含 `min_h2_sections` 公式）
- BDD-server / BDD-client（含 `min_scenario_count` 公式）
- RTM（含 `min_row_count` 公式）
- EDD（含 `min_h2_sections ≥ 8`）
- ARCH（含 `min_h2_sections ≥ 6`）

**Risk**：缺少步驟行 → gate-check 缺少驗收標準，等同於允許步驟以任意品質通過。

**Fix**：補充缺少的步驟行，量化欄位填入 `{{PLACEHOLDER}}` 格式（生成時由錨點替換）。

---

## Layer 5：Anti-Fake Guard 規則（共 2 項）

### [HIGH] R-11：§5 Anti-Fake Guard Summary 缺少必要防偽規則

**Check**：確認 DRYRUN.md §5 表格包含以下 5 條防偽規則：
1. `no_bare_placeholder`（殘留 `{{...}}` 語法）
2. `min_section_words_30`（任何 ## 章節正文 < 30 字）
3. `no_duplicate_paragraphs_150`（長度 ≥ 150 字元的重複段落）
4. `required_keywords_per_section`（特定章節缺少必要關鍵字）
5. `no_trivial_entity_names`（虛假實體名稱如 FooBar / TestEntity）

確認每條規則均有「觸發條件」和「說明」欄。

**Risk**：缺少防偽規則說明 → AI 生成 rules JSON 的 `anti_fake_rules` 陣列時不知道有哪些合法值，可能生成錯誤的規則名稱。

**Fix**：補充缺少的防偽規則行，規則名稱必須與 rules JSON `anti_fake_rules` 陣列中使用的字串一致（下底線命名：`no_bare_placeholder`）。

---

### [MEDIUM] R-12：gen.md Iron Rule 缺少「禁止在 DRYRUN 前生成文件」的強制聲明

**Check**：確認 gen.md 的 Iron Rule 區段明確包含：
- DRYRUN 是 pipeline 第零步，在任何文件生成之前執行
- 明確聲明「禁止在 DRYRUN 之前執行任何文件生成步驟」
- 說明若 MANIFEST.md 或 .gendoc-rules/ 不存在時 gendoc-flow 的強制行為

**Risk**：Iron Rule 不明確 → AI 可能在上游文件不存在時跳過 DRYRUN，或允許其他步驟在 DRYRUN 前執行。

**Fix**：在 gen.md Iron Rule 區段加入明確的「禁止前置生成」聲明，並說明缺少 MANIFEST.md 時的強制 DRYRUN 執行邏輯。

---

## Layer 6：gen.md 生成規則完整性（共 2 項）

### [HIGH] R-13：gen.md 缺少 Iron Law 標準聲明（必讀 skeleton + gen.md）

**Check**：確認 gen.md 頂部有標準 Iron Law 聲明：
```
> **Iron Law**：生成任何 MANIFEST.md 之前，必須先讀取 `DRYRUN.md`（結構）和 `DRYRUN.gen.md`（本規則）。
> **禁止保留 Bare Placeholder**：輸出的 MANIFEST.md 中不得含任何 `{{...}}` 格式的未替換 placeholder。
```

**Risk**：缺少 Iron Law → AI 可能不讀 skeleton 直接按照 gen.md 生成，導致輸出與骨架結構不一致。

**Fix**：在 gen.md 頂部（`## Iron Rule` 之後）加入 `> **Iron Law**：...` 和 `> **禁止保留 Bare Placeholder**：...` 兩行標準聲明。

---

### [MEDIUM] R-14：gen.md frontmatter expert-roles 僅有列表格式，缺少表格說明

**Check**：確認 gen.md frontmatter 的 `expert-roles` 欄位包含 ≥ 2 個角色定義，且正文（`## 專家角色說明`段落）包含完整的角色職責說明：
- **Pipeline Analyst**：職責描述是否完整（讀取 pipeline.json + state + 決定 Y/N + 計算計數）？
- **Quantitative Rules Architect**：職責描述是否完整（執行 bash + 推導公式 + 生成 JSON + 填充 MANIFEST）？

**Risk**：角色職責說明不完整 → AI 不知道兩個角色的分工邊界，可能混淆執行順序。

**Fix**：補充 `## 專家角色說明` 段落中缺少的職責說明，確保每個角色的職責範圍與 gen.md Steps 的對應關係清晰。

---

## Layer 7：Step 5 量化公式覆蓋完整性（共 1 項）

### [HIGH] R-16：gen.md Step 5 缺少 §4 步驟的個別量化公式

**Check**：確認 gen.md Step 5 為以下步驟提供了個別公式段落（而非僅依靠「所有其他步驟」兜底的 min_h2_sections=3）：
- BRD：min_h2_sections=5
- PRD：min_h2_sections=6
- PDD：min_h2_sections=4
- VDD：min_h2_sections=4
- FRONTEND：min_h2_sections=4
- CLIENT_IMPL：min_h2_sections=4
- ADMIN_IMPL：min_h2_sections=4（含 no_trivial_entity_names）
- LOCAL_DEPLOY：min_h2_sections=4
- CICD：min_h2_sections=4
- IDEA：anti_fake_rules += no_trivial_entity_names
- PRD：anti_fake_rules += no_trivial_entity_names

**Risk**：兜底段落（min_h2_sections=3）對 BRD（應為 5）和 PRD（應為 6）等步驟設定了過低的品質門檻，gate-check 將因此漏放低品質輸出。DRYRUN 作為整個流水線的品質基準，若錨點公式錯誤，所有下游驗收均受影響。

**Fix**：在 gen.md Step 5 的「所有其他步驟」段落之前，補充各步驟的個別公式段落，對齊 DRYRUN.md §4 表格的 Min §Sections 值。

---

## Layer 8：§1 文件說明一致性（共 1 項）

### [LOW] R-17：§1 文件說明的 §章節引用是否與骨架一致

**Check**：確認 MANIFEST.md §1「它回答三個問題」的括號 §引用（§2.1 / §2.2 / §4）與骨架實際章節號一致。

**Risk**：骨架章節號變更時 §1 描述過時，誤導讀者理解文件結構。

**Fix**：更新 §1 正文中的括號章節引用，與骨架 §N 標題保持同步。

---

## 審查完成標準

| 級別 | 數量要求 |
|------|---------|
| CRITICAL | 0（R-01/R-02/R-03/R-04 必須全數修復）|
| HIGH | 0（首次生成，R-05/R-06/R-07/R-09/R-11/R-13/R-16 必須全數修復）；後續迭代允許 ≤ 1（需附風險說明）|
| MEDIUM | ≤ 2 |
| LOW | ≤ 5 |

**CRITICAL 為 0 且 HIGH 為 0 → PASSED，可進行 commit。**
