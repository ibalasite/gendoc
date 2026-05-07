---
doc-type: DRYRUN
version: 2.0.0
description: |
  DRYRUN 產出物雙軌驗證 + 從嚴收斂審查標準。
  Track A = dryrun_core.py 量化（已寫入 .gendoc-rules/）vs Track B = AI + bash 配合產出
  itemized list 的專家計算。不一致時預設取高（從嚴），較低方須舉證對方為 false positive
  才能採低。fix subagent 在 P-8 邊界內：只寫 target project 檔，不改 runtime/上游 source。
  詳見 docs/PRD.md §7.10。
reviewer-roles:
  - role: Quantitative Anchor Auditor
    scope: 對 dryrun_core.py 提取的 7 個量化錨點逐一執行雙軌獨立驗證
  - role: Rules JSON Validator
    scope: .gendoc-rules/*.json 結構完整性、JSON 語法、無公式字串殘留
  - role: Developer Feedback Reporter
    scope: 不一致時生成 docs/DRYRUN_DEV_FEEDBACK.md（給 gendoc 開發者的 regex 修正建議）
quality-bar:
  - docs/MANIFEST.md 已生成、無裸 placeholder（與 .gen.md sanity check 一致）
  - .gendoc-rules/ 目錄存在、≥ 1 個 rules JSON、所有 JSON 語法合法
  - 7 個量化錨點通過雙軌驗證（一致 PASS / 不一致依從嚴規則收斂）
  - 不一致時：docs/DRYRUN_DEV_FEEDBACK.md 已生成，含 itemized 證據與 regex 修正建議
upstream-alignment:
  - dryrun_core.py extract_parameters() 7 個 metric 提取邏輯與本 review.md 7 條雙軌條目一一對應
  - pipeline.json 各 step spec_rules 公式套用結果，必須能在 .gendoc-rules/<step>-rules.json 找到整數對應
---

# DRYRUN.review.md — 雙軌驗證 + 從嚴收斂審查標準

DRYRUN 產出物（`.gendoc-rules/*.json` + `docs/MANIFEST.md`）是下游 22 個 step 的 quality gate 依據。本 review 採**雙軌獨立驗證**：Track A 是 dryrun_core.py 量化結果，Track B 是 AI + bash 重新算出的專家計算。**任一錨點不一致 → finding**。

---

## 0. 全域原則（reviewer subagent 必讀）

### 0.1 從嚴收斂規則（核心）

**預設立場：取雙軌中較高的數值。** 較低方必須**逐項舉證**對方為何多算（指出 false positive 的具體實例 + 排除依據）才能採低。

| 比對結果 | 動作 |
|---|---|
| Track A == Track B | ✅ PASS（finding 0），共識值 = 兩者 |
| **Track B (AI) > Track A (core)** | AI 必須指出 grep 漏抓的具體項（名稱 + source 位置 + 漏抓原因）→ 共識值 = Track B；舉證不成立 → 共識值仍 = Track B（從嚴默認，採高） |
| **Track A (core) > Track B (AI)** | AI 必須指出 grep 多算的具體項（哪一筆是 false positive + 排除規則）→ 共識值 = Track B（採低）；舉證不成立 → 共識值 = Track A（從嚴默認，採高） |

**舉證標準**：
- ❌ 不接受：「我覺得應該是 N」「依語意判斷是 N」
- ✅ 接受：「core 抓到的清單第 X 個是 `<具體名稱>`，依據 source `<具體章節>/<排除規則>`，該項不應計入」

### 0.2 Track B 強制執行形式（AI + bash itemized list）

reviewer subagent **必須**對每個 metric 執行以下形式的 Track B 計算（不接受純 AI 估算）：

```
1. 用 Read 工具讀 source（EDD/PRD/ARCH 全文，或 dryrun_core.py 提取邏輯指定章節）
2. 用 Bash 工具跑 grep/awk 抓候選清單作為舉證材料
3. 對每筆候選逐項判讀：是 / 不是 / 邊界 case（含理由）
4. 產出 itemized list（每筆名稱 + source 位置 + 是否計入 + 理由）
5. 計數 = list 中「是」的個數
```

**為什麼必須 itemized**：從嚴規則下，AI 主張「比 core 多」或「比 core 少」時都要列出**具體哪一筆**才有舉證資格。純估算數字無法驗證。

### 0.3 Fix subagent 邊界（P-8）

不一致經從嚴收斂後，fix subagent **只能**修改以下 target project 檔：

| 動作 | 檔案 | 邊界 |
|---|---|---|
| (I) 寫共識值 | `.gendoc-rules/<step>-rules.json` 對應 metric 欄位 | target project，**可寫** |
| (II) 生成 dev feedback | `docs/DRYRUN_DEV_FEEDBACK.md`（僅當有不一致時生成） | target project，**可寫** |
| (III) 同步 MANIFEST | `docs/MANIFEST.md` 對應 metric 行 | target project，**可寫** |

**禁止動作（P-8 鐵律）**：
- ❌ `~/.claude/skills/gendoc/tools/bin/dryrun_core.py`（runtime）
- ❌ `~/.claude/skills/gendoc/templates/DRYRUN.gen.md` / `DRYRUN.review.md`（runtime）
- ❌ `docs/EDD.md` / `docs/PRD.md` / `docs/ARCH.md` / 其他上游 source

理由：runtime 修改不會回到 gendoc repo（其他使用者拿不到）、下次 `setup upgrade` 會被覆蓋、原開發者不知情 → 沒有正向反饋路徑。修正 dryrun_core.py 的 regex 是 gendoc 開發者在 repo 端的工作，使用者透過 `docs/DRYRUN_DEV_FEEDBACK.md` 反饋。

### 0.4 Developer Feedback Report 結構

**僅當任一 metric 雙軌不一致時**，fix subagent 生成 / 追加 `docs/DRYRUN_DEV_FEEDBACK.md`。每個不一致 metric 一個區塊：

```markdown
## <metric_name>

- **Track A (core)**: <N1>
- **Track B (AI)**: <N2>（清單見下）
- **共識值**: <N3>
- **不一致原因**: <core regex 漏抓 / 多算 / etc>
- **AI 舉證清單**:
  - <item_1>（source: <檔>:§<章節>，是否計入: 是/否，理由）
  - <item_2>（source: <檔>:§<章節>，...）
- **建議修正（給 gendoc 開發者）**:
  - 檔案：`tools/bin/dryrun_core.py`
  - 函式：`<extract_parameter_method>`
  - 現行 pattern：`<current regex>`
  - 建議 pattern：`<suggested regex>`
  - 理由：<具體解釋為何此修正能對齊共識>
```

**反饋路徑**：使用者讀完 → 貼到 [github.com/ibalasite/gendoc](https://github.com/ibalasite/gendoc) issue → 開發者在 repo fix `dryrun_core.py` 的 regex → release 新版 → 所有使用者 `gendoc-upgrade` 拿到修正。

---

## Layer 1：產出物存在性與結構（共 4 項）

### [CRITICAL] R-01：MANIFEST.md 存在且無裸 placeholder

**Check**：
```bash
[[ -f docs/MANIFEST.md ]] || echo "MISSING"
grep -cE '\{\{[A-Z_]+\}\}' docs/MANIFEST.md
```

**Pass**：檔案存在 + bare placeholder count = 0
**Fail**：缺檔 / count > 0 → finding，fix 路徑：重跑 `gendoc-flow --only DRYRUN`（dryrun_core.py 應自動填值；若 fail 表示 dryrun_core.py bug，記錄到 DRYRUN_DEV_FEEDBACK.md）

### [CRITICAL] R-02：.gendoc-rules/ 目錄與 JSON 完整性

**Check**：
```bash
[[ -d .gendoc-rules ]] || echo "MISSING_DIR"
ls .gendoc-rules/*.json 2>/dev/null | wc -l
for f in .gendoc-rules/*.json; do python3 -c "import json; json.load(open('$f'))" || echo "BAD: $f"; done
```

**Pass**：目錄存在 + JSON 數 ≥ 1 + 全部語法合法
**Fail**：任一條件失敗 → finding

### [CRITICAL] R-03：rules JSON 無公式字串殘留

`dryrun_core.py` 應將 `pipeline.json` 內 `spec_rules` 的公式字串（如 `"max(5, {rest_endpoint_count})"`）評估為實際整數。.gendoc-rules/*.json 中**只應有整數**，無 `{...}` 佔位符。

**Check**：
```bash
grep -lE '\{[a-z_]+\}' .gendoc-rules/*.json 2>/dev/null
```

**Pass**：grep 無輸出（所有 JSON 已是整數）
**Fail**：有 JSON 仍含公式字串 → finding（dryrun_core.py 評估邏輯有漏；記錄到 DRYRUN_DEV_FEEDBACK.md）

### [CRITICAL] R-04：rules JSON 與 pipeline.json active step 對齊

dryrun_core.py 應為**每個 active step**（依 client_type / has_admin_backend 條件過濾後）產生對應 rules JSON。

**Check**：
1. 從 `.gendoc-state-*.json` 讀 client_type / has_admin_backend
2. 從 `templates/pipeline.json` 列出 condition 通過的 step
3. 比對 `.gendoc-rules/*.json` 是否每個 active step 都有對應檔案

**Pass**：active step 數 == rules JSON 數
**Fail**：缺檔 → finding（記錄缺哪個 step）

---

## Layer 2：7 個量化錨點雙軌驗證（每錨點一條 [CRITICAL]）

### [CRITICAL] R-05：entity_count 雙軌一致

**Track A（量化軌）**
- 來源：`.gendoc-rules/SCHEMA-rules.json`（`min_table_count = max(3, entity_count)`）或 `docs/MANIFEST.md`
- 取值：
  ```bash
  jq -r '.min_table_count // .quantitative_specs.min_table_count // empty' .gendoc-rules/SCHEMA-rules.json
  # 或從 MANIFEST.md §2.1 直接讀
  grep -E '^\| entity_count' docs/MANIFEST.md | awk -F'|' '{print $3}' | tr -d ' '
  ```

**Track B（專家軌）**
- 來源：`docs/EDD.md`（dryrun_core.py 對齊 pattern：Mermaid classDiagram 的 `class/interface/enum/struct/abstract class` 定義；fallback：`### ClassName` headings 大寫開頭）
- 計算指引（reviewer 必須執行）：
  ```bash
  # 候選清單 1：Mermaid classDiagram 內定義
  grep -nE '^\s*(class|interface|enum|struct|abstract\s+class)\s+[A-Za-z][a-zA-Z0-9_]*' docs/EDD.md

  # 候選清單 2（fallback）：### Heading 大寫開頭
  grep -nE '^###\s+[A-Z][a-zA-Z0-9]*\b' docs/EDD.md
  ```
- 逐項判讀：每筆候選依「是 entity / 不是」標記，理由參照 EDD §3.1（資料模型）/ §3.4（Bounded Context）的定義
- 輸出：
  - itemized list：`[(name_1, EDD:§X, 是/否, 理由), ...]`
  - count = list 中「是」的個數

**比對與從嚴收斂規則**

| 結果 | 動作 |
|---|---|
| Track A == Track B | ✅ PASS |
| Track B > Track A | finding：「core 漏抓 N 個 entity，分別是 [...]」→ 共識值 = Track B；建議 regex 修正寫入 DRYRUN_DEV_FEEDBACK.md |
| Track A > Track B | reviewer 須舉證：「core 第 X 個 `<name>` 是 `<abstract / nested / etc>`，依 EDD §X 不應計入」；舉證成立 → 共識值 = Track B；舉證不成立 → 共識值 = Track A（從嚴默認） |

---

### [CRITICAL] R-06：avg_entity_field_count 雙軌一致

**Track A**：
- 來源：`.gendoc-rules/SCHEMA-rules.json`（`min_columns_per_table = max(3, avg_entity_field_count)`）

**Track B**：
- 來源：`docs/EDD.md`（dryrun_core.py 對齊 pattern：table cell 含 ≥ 3 commas 的欄位定義；如「id, name, email, created_at, ...」）
- 計算指引：
  ```bash
  # 候選：所有 table data row 內含 commas ≥ 3 的 cell
  awk -F'|' '/^\|/ && !/^\|[-: ]+\|/ {for(i=1;i<=NF;i++){c=gsub(/,/,",",$i); if(c>=3) print NR": "$i" (commas="c+1")"}}' docs/EDD.md
  ```
- 逐項判讀：每筆候選 cell 是否真為 entity field 列表（vs comma 出現在說明文字中）
- avg = sum(field_counts) / len(field_counts)，clamp 至 [3, 20]

**比對**：依 0.1 從嚴規則（取較大或較完整的計算）。

---

### [CRITICAL] R-07：rest_endpoint_count 雙軌一致

**Track A**：
- 來源：`.gendoc-rules/API-rules.json`（`min_endpoint_count = max(5, rest_endpoint_count)`）

**Track B**：
- 來源：`docs/PRD.md`（dryrun_core.py 對齊 pattern：HTTP method + path 配對）
- 計算指引：
  ```bash
  grep -nE '(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+/[a-zA-Z0-9/_{}-]+' docs/PRD.md
  ```
- 逐項判讀：每個候選是否為真實 endpoint（vs 範例 / 文件描述 / deprecated 標記）；同一個 endpoint 多次出現只算 1 次（dryrun_core.py 用 `set()` 去重）
- count = unique 後的個數

**比對**：依 0.1 從嚴規則。

---

### [CRITICAL] R-08：user_story_count 雙軌一致

**Track A**：
- 來源：`.gendoc-rules/RTM-rules.json`（`min_row_count = user_story_count`）+ BDD-server / BDD-client（`min_scenario_count = ceil(user_story_count * 0.8 / 0.6)`）

**Track B**：
- 來源：`docs/PRD.md`（dryrun_core.py 對齊 pattern：`US-N` / `US_N` / `User Story N` / `Story-N` heading）
- 計算指引：
  ```bash
  grep -nE '^#{1,4}\s+(US[-_][0-9]+|User\s+Story[-_\s][0-9]+|Story-[0-9]+)\b' docs/PRD.md
  ```
- 逐項判讀：每筆是否為真實 US（vs 範例 / 模板殘留 / 標題引用）

**比對**：依 0.1 從嚴規則。

---

### [CRITICAL] R-09：acceptance_criteria_count 雙軌一致

**Track A**：
- 來源：`.gendoc-rules/BDD-server-rules.json`（`min_steps_per_scenario = acceptance_criteria_count` 等）

**Track B**：
- 來源：`docs/PRD.md`（dryrun_core.py 對齊 pattern：US block 內 `- AC` / `* AC` / 數字編號 `1.` 等 AC 條目）
- 計算指引：
  ```bash
  # 抓 ### US-N 標題，再對每個 US block 內計數 AC 條目
  awk '/^###\s+(US-|Story-)/{us=$0; next} /^[-*]\s+(AC|Acceptance)/||/^[0-9]+\./ {if(us) print us": "$0}' docs/PRD.md
  ```
- 逐項判讀：每個候選是否為實質 AC（vs 解釋性 bullet / 範例）
- avg = sum(ac_per_us) / len(us_list)，最小 2

**比對**：依 0.1 從嚴規則。

---

### [CRITICAL] R-10：arch_layer_count 雙軌一致

**Track A**：
- 來源：`.gendoc-rules/test-plan-rules.json`（`min_h2_sections = arch_layer_count + 4` 等）

**Track B**：
- 來源：`docs/ARCH.md`（dryrun_core.py 對齊 pattern：第一個 markdown table 的 data rows；fallback：`### ...Layer / ...Service / ...層 / ...服務` heading）
- 計算指引：
  ```bash
  # 候選 1：第一個 markdown table 的 data rows
  awk 'BEGIN{intab=0; rows=0} /^\|/ {if(/^\|[-: ]+\|/){intab=1; next} if(intab) rows++; next} {if(intab && rows>0) exit} END{print rows}' docs/ARCH.md

  # 候選 2（fallback）：layer/service heading
  grep -nE '^###\s+(.*Layer|.*Service|.*層|.*服務)' docs/ARCH.md
  ```
- 逐項判讀：每個 row / heading 是否為真實 layer（vs 範例對照 / 概念說明）

**比對**：依 0.1 從嚴規則。

---

### [CRITICAL] R-11：component_count 雙軌一致

**Track A**：
- 來源：`.gendoc-rules/FRONTEND-rules.json`（`min_component_count = component_count`）

**Track B**：
- 來源：`docs/ARCH.md`（dryrun_core.py 對齊 pattern：`#### ` heading；fallback：`- ` / `* ` bullet items）
- 計算指引：
  ```bash
  # 候選 1：#### heading
  grep -nE '^####\s+\w+' docs/ARCH.md

  # 候選 2（fallback）：bullet items
  grep -cE '^[-*]\s+\w+' docs/ARCH.md
  ```
- 逐項判讀：每個候選是否為真實 component（vs 章節標題 / 範例）

**比對**：依 0.1 從嚴規則。

---

## Layer 3：MANIFEST.md 量化錨點顯示一致性（共 1 項）

### [HIGH] R-12：MANIFEST.md §2.1 顯示值與 .gendoc-rules/ 一致

`docs/MANIFEST.md` §2.1 列出的 7 個量化錨點，必須與 `.gendoc-rules/*.json` 中對應 metric 的計算結果**完全一致**。任一不一致 → finding。

**Check**：對每個 metric，從 MANIFEST.md 讀數值，與 `.gendoc-rules/<step>-rules.json` 比對。
**Fix**：fix subagent 重寫 MANIFEST.md 對應行（在 P-8 邊界內，target project 檔可寫）。

---

## Layer 4：Developer Feedback Report 完整性（共 2 項）

### [HIGH] R-13：不一致時必須生成 DRYRUN_DEV_FEEDBACK.md

**Trigger**：R-05 ~ R-11 任一條目 finding > 0 + 共識值 ≠ Track A
**Check**：`docs/DRYRUN_DEV_FEEDBACK.md` 存在
**Fail**：缺檔 → finding（fix subagent 必須生成）

### [HIGH] R-14：DRYRUN_DEV_FEEDBACK.md 結構完整

`docs/DRYRUN_DEV_FEEDBACK.md` 內每個 metric 區塊必須含完整六欄位（依 §0.4 範本）：

| 欄位 | 必填 |
|---|---|
| Track A (core) 數值 | ✅ |
| Track B (AI) 數值 + itemized 清單 | ✅ |
| 共識值 | ✅ |
| 不一致原因（一句話分類） | ✅ |
| AI 舉證清單（每筆名稱 + source 位置 + 是否計入 + 理由） | ✅ |
| 建議修正（檔案 + 函式 + 現行 pattern + 建議 pattern + 理由） | ✅ |

任一欄位缺失 → finding。

---

## Layer 5：共識落地完整性（共 1 項）

### [CRITICAL] R-15：共識值已寫回 .gendoc-rules

對於 R-05 ~ R-11 任一不一致 metric，fix subagent 必須將共識值寫入對應的 `.gendoc-rules/<step>-rules.json` 欄位（覆蓋 dryrun_core.py 的原始輸出）。

**Check**：對每個有 finding 的 metric，比對 `.gendoc-rules/` 中對應數值是否 == 共識值。
**Fail**：rules JSON 仍是 Track A 原值 → finding（fix 未落地，下游 review.sh 會用錯誤門檻）。

---

## Quality Gate（最終驗收）

| # | 驗收項 | 標準 |
|---|---|---|
| 1 | Layer 1（4 項） | 全 PASS |
| 2 | Layer 2（7 項，雙軌錨點） | 全 PASS（一致或經從嚴收斂達共識） |
| 3 | Layer 3 MANIFEST 一致性 | PASS |
| 4 | Layer 4 dev feedback | 若 Layer 2 有不一致 → DRYRUN_DEV_FEEDBACK.md 存在且結構完整 |
| 5 | Layer 5 共識落地 | 不一致 metric 的共識值已寫回 .gendoc-rules |
| 6 | P-8 邊界 | 整個 review→fix 過程未動 runtime / 上游 source（log 內無對應 Edit/Write 操作） |

任一項未通過 → finding，fix subagent 在 P-8 邊界內處理：

| Fail 類型 | Fix 動作 |
|---|---|
| L1 R-01~R-04 | 重跑 `gendoc-flow --only DRYRUN`（重新呼叫 dryrun_core.py） |
| L2 R-05~R-11（雙軌不一致） | 共識值寫回 `.gendoc-rules/`、生成 DRYRUN_DEV_FEEDBACK.md |
| L3 R-12（MANIFEST 不一致）| 改寫 docs/MANIFEST.md 對應行 |
| L4 R-13~R-14（dev feedback 缺）| 生成 / 補完 docs/DRYRUN_DEV_FEEDBACK.md |
| L5 R-15（共識未落地）| 補寫 `.gendoc-rules/` 對應 metric |

---

## 設計原則對應 PRD §7.10

| 本 review.md 條目 | PRD §7.10 原則 |
|---|---|
| §0.1 從嚴收斂規則 | P-7 雙軌獨立驗證 + 從嚴收斂 |
| §0.2 Track B 強制 itemized | P-7 + 完成判準 12 |
| §0.3 Fix subagent 邊界 | P-8 + 完成判準 13 |
| §0.4 Dev Feedback 結構 | §7.10.3 + 完成判準 14 |
| R-05 ~ R-11（7 個雙軌條目）| 完成判準 9（覆蓋率 100%）+ 10 |
| R-13 ~ R-14 Dev Feedback 觸發 + 結構 | §7.10.8 反饋閉環 |
| R-15 共識落地 | §7.10.2「共識落地」段 |
