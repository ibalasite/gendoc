# gendoc 17 項修改清單 — 完整版

**版本**：審計第 2 輪 / 17 項修改 / 按序執行  
**日期**：2026-05-03  
**審計來源**：Architecture Audit Phase 2（Phase A+DRYRUN Gate+Phase B 三區分離、正則精度、LOCAL_DEPLOY/DEVELOPER_GUIDE 職責分離）

---

## 缺陷 #1：DRYRUN_STATUS 三態偵測（5 項修改）

### 修改項 1.1

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 1 末尾（第 100 行）之後，新增 Step 1.6（新增段落）

**原內容**：
```
[第 100 行]
echo "[DRYRUN] entity_count=${_ENTITY_COUNT}  rest_count=${_REST_COUNT}  us_count=${_US_COUNT}  arch_layers=${_ARCH_LAYER_COUNT}  bdd_min=${_BDD_MIN}"
[第 101 行]
```

**修改原因**：
缺陷 #1-R1：DRYRUN_STATUS 三態偵測邏輯完全缺失。需在 Step 1 後插入 Step 1.6，完整偵測 DRYRUN 執行狀態（未執行 / 用預設值 / 正常執行），輸出機器可讀 marker 供 repair 的三區判定使用。

**修改後內容**（完整新段落，插入第 101 行之後）：
```
---

## Step 1.6：DRYRUN_STATUS 三態偵測 + 上游就緒度預檢

**[AI 指令]** 偵測 DRYRUN 執行狀態，判定為以下三態之一，並輸出 `DRYRUN_STATUS` marker：

### Step 1.6-A：檢查 .gendoc-rules/ 目錄是否存在與非空

```bash
# 檢查 DRYRUN 是否已執行過
if [[ -d "$_RULES_DIR" ]] && [[ $(ls "$_RULES_DIR"/*.json 2>/dev/null | wc -l) -gt 0 ]]; then
  _DRYRUN_PREV_EXIST="true"
  _RULES_FILE_COUNT=$(ls "$_RULES_DIR"/*.json 2>/dev/null | wc -l)
  echo "[INFO] .gendoc-rules/ 已存在，含 ${_RULES_FILE_COUNT} 個規則文件"
else
  _DRYRUN_PREV_EXIST="false"
  echo "[INFO] .gendoc-rules/ 為空或不存在（首次執行或曾清除）"
fi
```

### Step 1.6-B：檢查上游文件完整度 + 預設值偵測

```bash
# 統計上游文件完整度
_EDD_EXIST=$([[ -f "${_CWD}/docs/EDD.md" ]] && echo "true" || echo "false")
_PRD_EXIST=$([[ -f "${_CWD}/docs/PRD.md" ]] && echo "true" || echo "false")
_ARCH_EXIST=$([[ -f "${_CWD}/docs/ARCH.md" ]] && echo "true" || echo "false")

# 判定是否使用預設值
_USED_DEFAULTS="false"
if [[ "$_EDD_EXIST" == "false" ]] || [[ "$_PRD_EXIST" == "false" ]] || [[ "$_ARCH_EXIST" == "false" ]]; then
  _USED_DEFAULTS="true"
  echo "[WARN] 上游文件不完整，量化基線使用保守預設值"
  echo "       EDD: $_EDD_EXIST | PRD: $_PRD_EXIST | ARCH: $_ARCH_EXIST"
fi

# 統計基線是否全部為預設值
if [[ "$_ENTITY_COUNT" -eq 5 ]] && [[ "$_REST_COUNT" -eq 10 ]] && [[ "$_US_COUNT" -eq 10 ]] && [[ "$_ARCH_LAYER_COUNT" -eq 4 ]]; then
  _ALL_DEFAULTS="true"
  echo "[WARN] 所有量化基線使用預設值（EDD/PRD/ARCH 缺失或內容不足）"
else
  _ALL_DEFAULTS="false"
fi
```

### Step 1.6-C：判定三態並輸出 DRYRUN_STATUS

```bash
# 決策樹：判定 DRYRUN 執行狀態
if [[ "$_DRYRUN_PREV_EXIST" == "true" ]] && [[ "$_USED_DEFAULTS" == "false" ]]; then
  # 三態 A：已執行且使用真實數值 → 正常執行
  _DRYRUN_STATUS="ok"
  echo "[DRYRUN_STATUS] ok（已執行，基線已校準）"
elif [[ "$_DRYRUN_PREV_EXIST" == "false" ]] && [[ "$_ALL_DEFAULTS" == "true" ]]; then
  # 三態 B：未執行且全是預設值 → 未執行
  _DRYRUN_STATUS="none"
  echo "[DRYRUN_STATUS] none（未執行）"
else
  # 三態 C：混合狀態（規則存在但基線是預設值，或規則不存在但 _USED_DEFAULTS=false）
  _DRYRUN_STATUS="defaults"
  echo "[DRYRUN_STATUS] defaults（用預設值執行）"
fi

export DRYRUN_STATUS="$_DRYRUN_STATUS"
```

### Step 1.6-D：DRYRUN 上游就緒度警告

```bash
# 若基線使用預設值，在 MANIFEST.md 中記錄警告
if [[ "$_USED_DEFAULTS" == "true" ]]; then
  echo "[WARN⚠️ ] DRYRUN 基線使用保守預設值"
  echo "   EDD entity count < 3 或 EDD 未找到 → entity_count=5"
  echo "   REST endpoint < 5 或 EDD 未找到 → rest_count=10"
  echo "   PRD user story < 3 或 PRD 未找到 → us_count=10"
  echo "   ARCH layer < 4 或 ARCH 未找到 → arch_layers=4"
  echo ""
  echo "   品質閘門可能偏鬆，建議："
  echo "   1. 補完上游文件（EDD/PRD/ARCH）"
  echo "   2. 確認文件內容充分（entity/endpoint/story 數量達標）"
  echo "   3. 重新執行 DRYRUN 以更新基線"
fi
```

---

```

**影響範圍**：
- 直接影響：gendoc-gen-dryrun Step 3 寫規則文件時，需讀取 `$DRYRUN_STATUS` env var
- 下游依賴：gendoc-repair/SKILL.md Step 1.6 新增的 DRYRUN 三態偵測，依靠此 marker 判定補跑策略
- 測試驗證項：
  1. DRYRUN_STATUS=ok（.gendoc-rules/ 存在且非全預設值）
  2. DRYRUN_STATUS=none（.gendoc-rules/ 不存在且全預設值）
  3. DRYRUN_STATUS=defaults（混合狀態或規則存在但預設值）
  4. 上游不完整時的警告輸出正確

**決策**：Step 1 只計算數值，Step 1.6 負責檢查執行狀態及警告。此分離讓 gendoc-repair 可清楚區分「真實未執行」vs「預設值執行」，避免誤判補跑策略。

---

### 修改項 1.2

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 4「生成 docs/MANIFEST.md」，§3 Mandatory Steps Checklist 段落末尾（第 244-246 行）

**原內容**：
```
[第 244 行]
§3 Mandatory Steps Checklist → 用 active_steps 清單填入，Status 全設為 `PENDING`（後續 step 完成後由 gendoc-flow 更新）。
[第 245 行]
§4 Per-Step Completeness Standards → 用各 step 的 rules.json 中的 quantitative rules 填入。
[第 246 行]
§2.2 Active Conditional Steps → 用 skipped_steps 和 active_steps 的條件欄位填入。
```

**修改原因**：
缺陷 #1-R2、R3：MANIFEST.md 需記錄 DRYRUN_STATUS 和上游就緒度警告。當前模板未包含這兩項資訊，導致使用者無法判定基線是否真實校準。

**修改後內容**（替換第 244-246 行，擴充為 7 行）：
```
§2.3 DRYRUN Execution Status → 記錄 `DRYRUN_STATUS` 欄位（ok / defaults / none），如為 "defaults" 或 "none"，補充警告欄「⚠️ DRYRUN 基線使用保守預設值，建議重新執行 DRYRUN」。

§2.4 Upstream Readiness Warnings → 若 EDD/PRD/ARCH 不存在或內容不足（entity/endpoint/story < threshold），列舉缺失的上游文件 + 對應預設值 + 建議補全步驟。

§3 Mandatory Steps Checklist → 用 active_steps 清單填入，Status 全設為 `PENDING`（後續 step 完成後由 gendoc-flow 更新）。

§4 Per-Step Completeness Standards → 用各 step 的 rules.json 中的 quantitative rules 填入。

§2.2 Active Conditional Steps → 用 skipped_steps 和 active_steps 的條件欄位填入。
```

**影響範圍**：
- 直接影響：templates/DRYRUN.md（MANIFEST 骨架模板）需新增 §2.3 和 §2.4 區段
- 下游依賴：gendoc-flow 讀取 MANIFEST.md 時可偵測 DRYRUN_STATUS，決定是否提示使用者重新執行
- 測試驗證項：
  1. MANIFEST.md 含 DRYRUN_STATUS 欄位
  2. status=defaults 時，Upstream Readiness Warnings 列出所有預設值
  3. 警告格式清晰、可操作

**決策**：MANIFEST.md 作為「量化基線校準報告」，應清楚揭示基線品質狀態。放在 §2 Document Overview 中，與 §3 Checklist 平行，供用戶在執行 Phase B 前判定是否需先補上游文件。

---

### 修改項 1.3

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-repair/SKILL.md

**修改位置**：Step 1 後新增 Step 1.6（新增整個段落，約 450-550 行）

**原內容**（無，新增）

**修改原因**：
缺陷 #1-R2：gendoc-repair 必須偵測 DRYRUN 三態，並據此決定補跑策略。當前 repair 缺乏此邏輯，導致無法正確區分「上游不完整 vs 量化基線過時 vs DRYRUN 未執行」三種情況。

**修改後內容**（新增完整 Step 1.6 段落）：
```
---

## Step 1.6：DRYRUN 三態偵測 + 上游就緒度預檢

**[AI 指令]** 檢查 DRYRUN 執行狀態，判定為「未執行」/ 「預設值」/ 「正常」三態之一，並預檢上游文件完整度。

### Step 1.6-A：讀取 DRYRUN 狀態標記

```bash
# 檢查 .gendoc-rules/ 目錄是否存在非空
if [[ -d ".gendoc-rules" ]] && [[ $(ls .gendoc-rules/*.json 2>/dev/null | wc -l) -gt 0 ]]; then
  _RULES_EXIST="true"
  _RULES_COUNT=$(ls .gendoc-rules/*.json 2>/dev/null | wc -l)
  echo "[repair] .gendoc-rules/ 已存在（$_RULES_COUNT 個規則文件）"
else
  _RULES_EXIST="false"
  echo "[repair] .gendoc-rules/ 為空或不存在"
fi

# 檢查 MANIFEST.md 是否存在，並讀取 DRYRUN_STATUS
if [[ -f "docs/MANIFEST.md" ]]; then
  _MANIFEST_DRYRUN_STATUS=$(grep -oP 'DRYRUN Status.*?:\s*\K(ok|defaults|none)' docs/MANIFEST.md 2>/dev/null || echo "unknown")
  echo "[repair] MANIFEST.md DRYRUN_STATUS: $_MANIFEST_DRYRUN_STATUS"
else
  _MANIFEST_DRYRUN_STATUS="unknown"
  echo "[repair] MANIFEST.md 不存在，無法確定 DRYRUN 狀態"
fi

# 判定三態
if [[ "$_RULES_EXIST" == "true" ]] && [[ "$_MANIFEST_DRYRUN_STATUS" == "ok" ]]; then
  _DRYRUN_STATE="ok"
  echo "[repair-DRYRUN] State: OK（已執行，基線已校準）"
elif [[ "$_RULES_EXIST" == "false" ]] && [[ "$_MANIFEST_DRYRUN_STATUS" == "none" ]]; then
  _DRYRUN_STATE="none"
  echo "[repair-DRYRUN] State: NONE（未執行）"
else
  _DRYRUN_STATE="defaults"
  echo "[repair-DRYRUN] State: DEFAULTS（用預設值執行）"
fi

export REPAIR_DRYRUN_STATE="$_DRYRUN_STATE"
```

### Step 1.6-B：上游就緒度預檢

```bash
# 掃描 EDD/PRD/ARCH 完整度
_EDD_SIZE=$(wc -l < docs/EDD.md 2>/dev/null || echo "0")
_PRD_SIZE=$(wc -l < docs/PRD.md 2>/dev/null || echo "0")
_ARCH_SIZE=$(wc -l < docs/ARCH.md 2>/dev/null || echo "0")

_UPSTREAM_COMPLETE="true"
[[ $_EDD_SIZE -lt 50 ]] && _UPSTREAM_COMPLETE="false" && echo "[repair] ⚠️ EDD.md 過小（<50 行），上游可能不完整"
[[ $_PRD_SIZE -lt 50 ]] && _UPSTREAM_COMPLETE="false" && echo "[repair] ⚠️ PRD.md 過小（<50 行），上游可能不完整"
[[ $_ARCH_SIZE -lt 30 ]] && _UPSTREAM_COMPLETE="false" && echo "[repair] ⚠️ ARCH.md 過小（<30 行），上游可能不完整"

export REPAIR_UPSTREAM_COMPLETE="$_UPSTREAM_COMPLETE"
```

### Step 1.6-C：輸出三態決策樹

```bash
echo ""
echo "┌─────────────────────────────────────┐"
echo "│ DRYRUN 三態偵測結果                  │"
echo "├─────────────────────────────────────┤"
echo "│ State: $_DRYRUN_STATE"
echo "│ Upstream Complete: $_UPSTREAM_COMPLETE"
echo "└─────────────────────────────────────┘"
echo ""

if [[ "$_DRYRUN_STATE" == "none" ]] && [[ "$_UPSTREAM_COMPLETE" == "false" ]]; then
  echo "[repair] ⚠️ 情景 A：DRYRUN 未執行 + 上游不完整"
  echo "   建議："
  echo "   1. 先補完 Phase A 文件（EDD/PRD/ARCH 至少 50+ 行）"
  echo "   2. 執行 /gendoc-gen-dryrun 生成量化基線"
  echo "   3. 再執行 /gendoc-repair 補跑 Phase B"
elif [[ "$_DRYRUN_STATE" == "defaults" ]]; then
  echo "[repair] ⚠️ 情景 B：DRYRUN 用預設值執行"
  echo "   基線品質可能偏鬆，建議："
  echo "   1. 補完上游文件（尤其是 entity/endpoint/story 數量）"
  echo "   2. 重新執行 /gendoc-gen-dryrun 更新基線"
elif [[ "$_DRYRUN_STATE" == "ok" ]] && [[ "$_UPSTREAM_COMPLETE" == "true" ]]; then
  echo "[repair] ✅ DRYRUN 正常執行，基線已校準，可繼續補跑 Phase B"
fi
```

---

```

**影響範圍**：
- 直接影響：gendoc-repair Step 3 的補跑決策樹，依靠 `$REPAIR_DRYRUN_STATE` env var
- 下游依賴：Step 3 的 AskUserQuestion 邏輯將根據此狀態提供不同補跑選項
- 測試驗證項：
  1. REPAIR_DRYRUN_STATE=ok 時正確偵測
  2. REPAIR_DRYRUN_STATE=none / defaults 時提示用戶補跑 DRYRUN
  3. 上游不完整時的警告清晰

**決策**：三態偵測是 repair 核心邏輯，必須在 Phase Diff 之前完成，以便後續步驟根據狀態分支決策。

---

### 修改項 1.4

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-repair/SKILL.md

**修改位置**：Step 3「補跑選項」第二層菜單（約 650-750 行），新增情景 D 分支

**原內容**（當前無完整情景 D，需補齊）

**修改原因**：
缺陷 #1-R6：Step 3 提示應根據 DRYRUN 狀態分三條分支（Phase A 缺漏 / Phase A 完整但 DRYRUN 未跑 / DRYRUN 完整但 Phase B 缺漏），當前 repair 缺乏此邏輯，導致提示不夠精確。

**修改後內容**（完整的情景 D 分支，插入 Step 3 的補跑提示中）：
```
## Step 3c：Phase-Aware 補跑提示（情景 D：DRYRUN 用預設值執行）

**情景 D**：若 `_DRYRUN_STATE == "defaults"`（DRYRUN 已執行但使用預設值）

提示用戶：

```
╔════════════════════════════════════════════════════════════╗
║ 情景 D：DRYRUN 用預設值執行                                  ║
╚════════════════════════════════════════════════════════════╝

DRYRUN 規則文件已存在，但量化基線使用保守預設值。
本次補跑仍可繼續，但品質閘門可能偏鬆。

建議選項：
  A) 立即補跑 Phase B（使用當前預設值基線）
  B) 先更新上游文件，重新執行 DRYRUN，再補 Phase B

選擇 A 時：
  - 所有 Phase B 步驟（API、SCHEMA、test-plan...）將使用較寬鬆的量化閘門
  - 完成後可按需重跑 DRYRUN 以更新基線，Phase B 檔案無需重新生成

選擇 B 時：
  - 返回主菜單，執行 /gendoc-gen-dryrun 更新基線
  - DRYRUN 完成後自動更新 .gendoc-rules/*.json
  - 用戶確認後再執行此 repair 補 Phase B（此時 DRYRUN_STATE 應轉為 "ok"）
```

**AskUserQuestion 呼叫**：
```bash
read -p "選擇 (A/B) [A]: " -n 1 _CHOICE
_CHOICE=${_CHOICE:-A}

if [[ "$_CHOICE" == "B" ]] || [[ "$_CHOICE" == "b" ]]; then
  echo ""
  echo "您選擇更新上游文件 + 重新執行 DRYRUN"
  echo ""
  echo "建議步驟："
  echo "  1. 補完 EDD.md / PRD.md / ARCH.md（確保 entity/endpoint/story 數量達標）"
  echo "  2. 執行 /gendoc-gen-dryrun 重新計算量化基線"
  echo "  3. 檢查 docs/MANIFEST.md，確認 DRYRUN_STATUS 轉為 'ok'"
  echo "  4. 重新執行 /gendoc-repair，此時應進入情景 E 分支"
  echo ""
  exit 0
fi
```

---
```

**影響範圍**：
- 直接影響：gendoc-repair Step 3 補跑菜單邏輯
- 下游依賴：無（此為用戶面的提示，不影響後續自動流程）
- 測試驗證項：
  1. REPAIR_DRYRUN_STATE=defaults 時，提示正確
  2. 選 B 時正確退出並提示重跑 DRYRUN

**決策**：當基線使用預設值時，應明確告知使用者品質門檻可能偏鬆，並給予「繼續或延後」的選項，而不是盲目補跑。此設計保護品質。

---

### 修改項 1.5

**檔案路徑**：/Users/tobala/projects/gendoc/docs/PRD.md

**修改位置**：Change Log，第 27 行（v3.2）前新增 v3.2.1 版本行

**原內容**：
```
[第 27 行]
| v3.2 | 2026-05-03 | PM Agent | **UML Class Diagram...
```

**修改原因**：
缺陷 #1-R5：PRD v3.2 記錄了 gendoc-repair v2.0 初版，本輪修改新增 DRYRUN 三態偵測、repair Step 1.6、MANIFEST.md 警告等功能，應新增 v3.2.1 記錄此輪改動。

**修改後內容**（在 v3.2 行前新增 v3.2.1）：
```
| v3.2.1 | 2026-05-03 | PM Agent | **gendoc-repair Phase-Aware DRYRUN 完整化 + 三態偵測**：(1) **gendoc-gen-dryrun Step 1.6 新增**：DRYRUN_STATUS 三態偵測（未執行/預設值/正常）、上游就緒度預檢、基線品質警告；(2) **gendoc-repair Step 1.6 新增**：完整的 DRYRUN 三態偵測邏輯、上游文件完整度掃描、決策樹輸出；(3) **MANIFEST.md §2.3-2.4 擴充**：記錄 DRYRUN_STATUS 欄位、Upstream Readiness Warnings，使用者可清晰判定基線品質；(4) **Step 3c 情景 D 補齊**：當 DRYRUN 用預設值執行時，提示用戶「繼續或先更新基線」的選項；(5) **影響範圍**：gendoc-gen-dryrun (Step 1.6+Step 4)、gendoc-repair (Step 1.6+Step 3c)、templates/DRYRUN.md (§2.3-2.4)。 |
| v3.2 | 2026-05-03 | PM Agent | **UML Class Diagram...
```

**影響範圍**：
- 直接影響：PRD Change Log
- 下游依賴：文件版本追蹤、release note 生成
- 測試驗證項：
  1. v3.2.1 版本號清晰
  2. 變更摘要完整覆蓋 5 項修改點

**決策**：PRD 作為功能版本紀錄，應及時反映本輪修改，便於查證。

---

## 缺陷 #2：dryrun 正則精度（5 項修改）

### 修改項 2.1

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 1-2A「EDD entity count」（第 81-83 行）

**原內容**：
```
[第 81 行]
# ── 2-A：EDD entity count（classDiagram 中 class 定義數）
[第 82 行]
_ENTITY_COUNT=$(grep -c '^\s*class ' "${_CWD}/docs/EDD.md" 2>/dev/null || echo "5")
[第 83 行]
[[ "$_ENTITY_COUNT" -lt 3 ]] && _ENTITY_COUNT=5
```

**修改原因**：
缺陷 #2-P1：EDD 中的 entity 定義可能采多種格式（class / interface / enum / struct），當前正則只匹配 `^\s*class `，漏掉其他格式。需精化正則以支援多格式偵測 + non-standard format warning。

**修改後內容**（替換第 81-83 行，擴充為 8 行）：
```
# ── 2-A：EDD entity count（classDiagram 中 class/interface/enum 定義數）
# 支援多種格式：class / interface / enum / struct；非標準格式發出警告
_ENTITY_GREP=$(grep -E '^\s*(class|interface|enum|struct|abstract class) ' "${_CWD}/docs/EDD.md" 2>/dev/null | wc -l || echo "0")
_ENTITY_COUNT=$_ENTITY_GREP

# 偵測非標準格式（可能遺漏的定義）
_NONSTANDARD_ENTITY=$(grep -cE '^\s*[A-Z][A-Za-z0-9_]*\s*\{' "${_CWD}/docs/EDD.md" 2>/dev/null || echo "0")
[[ $_NONSTANDARD_ENTITY -gt 0 ]] && echo "[WARN] EDD.md 含 $_NONSTANDARD_ENTITY 個可能的非標準 entity 定義，請檢查格式"

[[ "$_ENTITY_COUNT" -lt 3 ]] && _ENTITY_COUNT=5 && echo "[WARN] entity count < 3，使用預設值 5"
```

**影響範圍**：
- 直接影響：_ENTITY_COUNT 計算值可能增大（涵蓋更多 entity 類型）
- 下游依賴：SCHEMA / test-plan 的 min_table_count / min_scenario_count 與此值相關
- 測試驗證項：
  1. class 正則匹配測試
  2. interface 正則匹配測試
  3. enum 正則匹配測試
  4. 非標準格式警告輸出測試

**決策**：多格式支援提高精度，同時發出 warning 讓使用者檢查非標準定義是否合法。

---

### 修改項 2.2

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 1-2B「EDD REST endpoint count」（第 85-87 行）

**原內容**：
```
[第 85 行]
# ── 2-B：EDD REST endpoint count
[第 86 行]
_REST_COUNT=$(grep -cE '(<<REST>>|<<Interface>>|HTTP\s*(GET|POST|PUT|DELETE|PATCH))' "${_CWD}/docs/EDD.md" 2>/dev/null || echo "10")
[第 87 行]
[[ "$_REST_COUNT" -lt 5 ]] && _REST_COUNT=10
```

**修改原因**：
缺陷 #2-P2：REST endpoint 偵測遺漏 PUT、PATCH、HEAD、OPTIONS、TRACE 等 HTTP method。當前正則不完整，導致計數偏低。

**修改後內容**（替換第 85-87 行，擴充為 6 行）：
```
# ── 2-B：REST endpoint count（HTTP method + API 標記）
# 支援全部 HTTP method：GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, TRACE
_REST_COUNT=$(grep -cE '(<<REST>>|<<Interface>>|HTTP\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE))' "${_CWD}/docs/EDD.md" 2>/dev/null || echo "0")

[[ "$_REST_COUNT" -lt 5 ]] && _REST_COUNT=10 && echo "[WARN] REST endpoint count < 5，使用預設值 10"
```

**影響範圍**：
- 直接影響：_REST_COUNT 計算值
- 下游依賴：API step 的 min_endpoint_count 規則
- 測試驗證項：
  1. GET/POST/PUT/DELETE/PATCH 各別測試
  2. HEAD/OPTIONS/TRACE 新增測試

**決策**：補全所有標準 HTTP method，提高精度。

---

### 修改項 2.3

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 1-2C「PRD user story count」（第 89-91 行）

**原內容**：
```
[第 89 行]
# ── 2-C：PRD user story count
[第 90 行]
_US_COUNT=$(grep -cE '^(## |### )US-' "${_CWD}/docs/PRD.md" 2>/dev/null || echo "10")
[第 91 行]
[[ "$_US_COUNT" -lt 3 ]] && _US_COUNT=10
```

**修改原因**：
缺陷 #2-P3：User Story 格式可能多樣（US-001 / US_001 / US 001 / Story-001 等），當前正則只匹配 `US-`，遺漏其他命名。需精化以支援多格式偵測 + 非標準 US 警告。

**修改後內容**（替換第 89-91 行，擴充為 12 行）：
```
# ── 2-C：PRD user story count（支援多種 US 命名格式）
# 標準格式：## US-001 / ### US-001 / ## US_001 等
_US_STANDARD=$(grep -cE '^(##+ )+(US[-_]?[0-9]+|User\s+Story[-_]?[0-9]+)' "${_CWD}/docs/PRD.md" 2>/dev/null || echo "0")

# 偵測可能的非標準 US 定義（### Feature XXX / ### Scenario XXX）
_US_NONSTANDARD=$(grep -cE '^\s*(###|####)\s+(Feature|Scenario|Use\s+Case|Acceptance\s+Criteria)[^A-Z0-9]' "${_CWD}/docs/PRD.md" 2>/dev/null || echo "0")
[[ $_US_NONSTANDARD -gt 0 ]] && echo "[WARN] PRD.md 含 $_US_NONSTANDARD 個可能的非標準 US 定義（Feature/Scenario），請檢查是否應轉為 US-xxx 格式"

_US_COUNT=$_US_STANDARD

[[ "$_US_COUNT" -lt 3 ]] && _US_COUNT=10 && echo "[WARN] user story count < 3，使用預設值 10"
```

**影響範圍**：
- 直接影響：_US_COUNT 計算值
- 下游依賴：test-plan / BDD 的 min_scenario_count / min_us_count
- 測試驗證項：
  1. US-001 格式匹配測試
  2. US_001 格式匹配測試
  3. User Story-001 格式匹配測試
  4. 非標準格式警告輸出測試

**決策**：精化正則以覆蓋多種實務命名，同時發出 warning 讓使用者意識到非標準格式。

---

### 修改項 2.4

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 1-2D「ARCH layer count」（第 93-95 行）

**原內容**：
```
[第 93 行]
# ── 2-D：ARCH layer count（Tech Stack table non-header rows）
[第 94 行]
_ARCH_LAYER_COUNT=$(grep -c '^| [A-Za-z]' "${_CWD}/docs/ARCH.md" 2>/dev/null || echo "4")
[第 95 行]
[[ "$_ARCH_LAYER_COUNT" -lt 4 ]] && _ARCH_LAYER_COUNT=4
```

**修改原因**：
缺陷 #2-P4：ARCH layer 計數使用簡單正則 `'^| [A-Za-z]'`，易誤計或遺漏。需改為 AWK 狀態機精確計數 Markdown table rows，並驗證格式。

**修改後內容**（替換第 93-95 行，擴充為 14 行）：
```
# ── 2-D：ARCH layer count（Tech Stack table 行數，用 AWK 狀態機精確計數）
# Markdown table 格式：| Header | ... | Content | ... |（跳過分隔線 |---|---|）
_ARCH_LAYER_COUNT=$(awk '
  /^\|.*\|/ {
    # 檢查是否為分隔線 (|---|---|...|)
    if ($0 ~ /^\|\s*[-:]+\s*\|/) {
      in_table = 1
      next
    }
    # 若已進入 table，計數非空行（排除分隔線）
    if (in_table && NF > 0) {
      row_count++
    }
  }
  END { print (row_count > 0 ? row_count : 0) }
' "${_CWD}/docs/ARCH.md" 2>/dev/null || echo "0")

[[ "$_ARCH_LAYER_COUNT" -lt 4 ]] && _ARCH_LAYER_COUNT=4 && echo "[WARN] ARCH layer count < 4，使用預設值 4"
```

**影響範圍**：
- 直接影響：_ARCH_LAYER_COUNT 計算值（精度提高）
- 下游依賴：test-plan § min_h2_section 動態調整（基於 ARCH layer 數）
- 測試驗證項：
  1. 空 table 計數為 0 測試
  2. 含分隔線的 table 計數正確
  3. 多行 table 計數準確

**決策**：AWK 狀態機比簡單正則更可靠，能應對 Markdown table 的邊界情況。

---

### 修改項 2.5

**檔案路徑**：/Users/tobala/projects/gendoc/docs/PRD.md

**修改位置**：新增 Appendix A（在 Change Log 表末尾後，§2 Executive Summary 前，約第 50-100 行）

**原內容**（無，新增）

**修改原因**：
缺陷 #2-R5：DRYRUN 的預設值選擇（entity_count=5 / rest_count=10 / us_count=10 / arch_layers=4）缺乏設計文檔。需補充 Appendix A 說明為什麼選這些數值，以及如何調整。

**修改後內容**（新增完整 Appendix 章節）：
```
---

## Appendix A：dryrun 量化基線的預設值選擇依據

### 背景

當上游文件（EDD/PRD/ARCH）缺失或內容不足時，gendoc-gen-dryrun 使用保守預設值確保 pipeline 不中斷。本附錄說明每個預設值的選擇邏輯及調整方法。

### A.1 Entity Count 預設值 = 5

**邏輯依據**：
- 最小可行系統（MVP）通常含 5-8 個核心 entity：User / Product / Order / Payment / Audit
- 低於 3 個 entity 視為高度簡化系統（不太現實），故設 threshold=3，預設值 5
- 對應 SCHEMA min_table_count ≥ 5，保證核心資料結構覆蓋

**調整建議**：
- 小型專案（計算簡單）：可降至 3-4
- 中型專案（支付/訂單系統）：通常 6-10
- 大型專案（含多租戶/權限）：通常 12+

**檢查方法**：
```bash
grep -E '^\s*(class|interface|enum) ' docs/EDD.md | wc -l
```

### A.2 REST Endpoint Count 預設值 = 10

**邏輯依據**：
- REST API 通常採 5 個主要資源 × 2 個操作（列表+詳情）= 10 endpoint（GET /users, GET /users/{id}, ...）
- 含少量跨資源操作（login, search, report）
- 低於 5 個視為高度簡化 API，故設 threshold=5，預設值 10

**調整建議**：
- 微服務（單責）：通常 6-15 endpoint
- 通用後端：通常 20-40 endpoint
- 網關層：通常 50+ endpoint

**檢查方法**：
```bash
grep -cE '(<<REST>>|HTTP\s+(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE))' docs/EDD.md
```

### A.3 User Story Count 預設值 = 10

**邏輯依據**：
- 一個合理的 sprint（1-2 週）通常包含 6-12 個中等粒度 user story
- 低於 3 個視為極度簡化需求，故設 threshold=3，預設值 10

**調整建議**：
- 簡單工具：5-8 US
- 標準應用：10-20 US
- 複雜系統：30+US

**檢查方法**：
```bash
grep -cE '^(##+ )+(US[-_]?[0-9]+|User\s+Story[-_]?[0-9]+)' docs/PRD.md
```

### A.4 ARCH Layer Count 預設值 = 4

**邏輯依據**：
- 現代雲端應用典型棧：1) Web/Gateway Layer 2) Service Layer 3) Data Access Layer 4) Infrastructure
- 低於 4 個視為不完整的分層設計，故設 threshold=4，預設值 4
- 對應 test-plan min_h2_section = ceil(ARCH_LAYER_COUNT + 2) = 6，覆蓋 layer 級測試

**調整建議**：
- 嵌入式/IoT：通常 2-3 層（firmware + protocol）
- 後端：通常 4-5 層
- 遊戲引擎：通常 6+ 層（rendering/physics/input/audio/network...）

**檢查方法**：
```bash
grep -c '^|' docs/ARCH.md | grep -v separator
```

### A.5 何時更新預設值

若上游文件已就緒，應立即重新執行 `/gendoc-gen-dryrun` 以更新基線：

```bash
# 確認上游文件
wc -l docs/{EDD,PRD,ARCH}.md

# 計算實際指標
echo "=== 量化檢查 ==="
echo "EDD entities: $(grep -cE '^\s*(class|interface|enum) ' docs/EDD.md)"
echo "REST endpoints: $(grep -cE '(<<REST>>|HTTP\s+(GET|POST|PUT|DELETE))' docs/EDD.md)"
echo "User stories: $(grep -cE '^(## |### )US-' docs/PRD.md)"
echo "ARCH layers: $(awk '/^\|.*\|/{if(/^\|\s*[-:]+\s*\|/){in_table=1;next}if(in_table)row_count++}END{print row_count}' docs/ARCH.md)"

# 若指標達標，重新執行 DRYRUN
/gendoc-gen-dryrun
```

---

```

**影響範圍**：
- 直接影響：PRD 文檔結構
- 下游依賴：使用者查閱時參考本附錄調整預設值
- 測試驗證項：
  1. 附錄邏輯清晰、可操作
  2. 檢查方法指令正確

**決策**：PRD 作為最高級的產品文檔，應包含設計決策的依據。Appendix A 讓使用者理解預設值選擇，並知道如何調整。

---

## 缺陷 #3：LOCAL_DEPLOY + DEVELOPER_GUIDE 分離（7 項修改）

### 修改項 3.1

**檔案路徑**：/Users/tobala/projects/gendoc/docs/PRD.md

**修改位置**：§「什麼是『可實作的藍圖』」，標準 #6（第 78-79 行）

**原內容**：
```
[第 78-79 行]
6. **LOCAL_DEPLOY.md + DEVELOPER_GUIDE.md（配套二件）**：LOCAL_DEPLOY.md 負責第一次建置（step-by-step，含 k8s 環境、所有服務、CI/CD 工具平台）；DEVELOPER_GUIDE.md 負責建置後的每日操作（git push → CI → CD → 驗證的完整工作流程，CI/CD 診斷，本地快速指令，常見問題，環境維護）；**client 也封進 k8s pod**，所有服務均在 k8s 內；**對外只有一個 port（Port 80）**，測試入口單一；同時提供 docker-compose 版本作為輔助（兩種方式均可無礙建置，不能有缺漏步驟或 TBD）；**Local Developer Platform 完整可用**：Gitea（Port 3000）+ Jenkins（Port 8080）+ ArgoCD（Port 8443）均以 k3s pod 運行，透過 `make dev-tools-up` 一鍵啟動；開發工具 port 與應用 port 80 域分離、不衝突；**Production Parity**：本地與生產使用完全相同工具鏈，差異只在規模與 TLS
```

**修改原因**：
缺陷 #3-R1：當前標準 #6 將 LOCAL_DEPLOY 和 DEVELOPER_GUIDE 混為一談，缺乏明確的職責邊界。需拆分為 6a / 6b / 6c 三項，清晰定義各自的範疇。

**修改後內容**（替換第 78-79 行整段，拆分為三項，共 ~30 行）：
```
6a. **LOCAL_DEPLOY.md（初始化層）**：
   - **責任**：從零到一，第一次在本機建起完整環境
   - **包含**：Prerequisite 工具列表；Rancher Desktop / k3s 設定；Namespace / RBAC 初始化；所有服務的 Kubernetes manifest（Deployment/Service/ConfigMap/Secret/Ingress）；Docker image 構建或拉取指令；資料庫初始化（migration + seed data）；一次性網路配置（mkcert 本地 HTTPS）；驗證 checklist
   - **禁止**：不含日常操作步驟（git push / CI 監控 / 問題診斷）；不含環境維護（rotate secret / 清理 image / 日誌輪替）
   - **成功標準**：完整執行 LOCAL_DEPLOY.md 後，`make k8s-apply` 一行指令即可啟動全部服務；所有 unit / integration / E2E 測試通過；對外 port 80（http）+ 3000/8080/8443（dev tools）均可訪問

6b. **DEVELOPER_GUIDE.md（日常操作層）**：
   - **責任**：第一次建置完成後，開發者每天的操作指南
   - **包含**：日常開發工作流（git push → Jenkins 觸發 → Pipeline 監控 → ArgoCD sync → 應用驗證）；CI/CD 故障診斷（Jenkins 未觸發、stage 失敗重跑、ArgoCD OutOfSync、Gitea webhook 除錯）；本地環境快速指令（`make dev-status` / `make dev-logs` / `make dev-restart` / `make dev-health`）；常見問題 Q&A（本地 namespace 版本，含 pod 在 pending / image pull fail / port conflict 等）；環境維護（密碼 rotate / image 清理 / namespace 重置）
   - **禁止**：不重覆 LOCAL_DEPLOY.md 的一次性設定步驟；不含生產 runbook 內容（生產事故處理歸 runbook.md）
   - **成功標準**：開發者熟悉 DEVELOPER_GUIDE.md 後，能獨立解決 90% 的日常問題，無需詢問架構師；新 team member 看此文件能在 30 分鐘內上手日常工作流

6c. **職責邊界明確化**：
   - LOCAL_DEPLOY.md ：一次性 / 環境準備 / 非開發者也能執行
   - DEVELOPER_GUIDE.md：重複操作 / 日常工作流 / 開發者日常查閱
   - Runbook.md：生產事故 / SRE on-call 角色 / 生產環境操作
   - 三文件無重複，各自聚焦一個職責
```

**影響範圍**：
- 直接影響：PRD 標準 #6 定義
- 下游依賴：LOCAL_DEPLOY.gen.md / DEVELOPER_GUIDE.gen.md 的生成規則將遵循此邊界
- 測試驗證項：
  1. 三個標準各自清晰、可操作
  2. 職責邊界明確無重複

**決策**：明確的職責邊界（6a / 6b / 6c）讓每份文件聚焦，避免混亂或重複。使用者可根據場景（初次搭建 vs 日常開發 vs 生產故障）快速定位正確文件。

---

### 修改項 3.2

**檔案路徑**：/Users/tobala/projects/gendoc/skills/gendoc-gen-dryrun/SKILL.md

**修改位置**：Step 3「生成各 step 的 .gendoc-rules/*.json」規則表（第 150-182 行），補充 D21-LOCAL_DEPLOY 和 D21b-DEVELOPER_GUIDE 兩行

**原內容**：
```
[第 174 行]
| LOCAL_DEPLOY | docs/LOCAL_DEPLOY.md | 5 | — | ["Prerequisites", "Setup Steps", "Verification"] |
[第 175 行]
| CICD | docs/CICD.md | 6 | — | ["Pipeline Overview", "Jenkinsfile", "PR Gate", "ArgoCD"] |
```

**修改原因**：
缺険陷 #3-R2：dryrun 規則表中 LOCAL_DEPLOY 行存在，但 DEVELOPER_GUIDE 缺失，導致 pipeline 生成規則時無法涵蓋此 step。

**修改後內容**（在第 175 行前新增 DEVELOPER_GUIDE 行）：
```
| LOCAL_DEPLOY | docs/LOCAL_DEPLOY.md | 5 | — | ["Prerequisites", "Setup Steps", "Verification"] |
| DEVELOPER_GUIDE | docs/DEVELOPER_GUIDE.md | 5 | — | ["Daily Scenarios", "CI/CD Diagnosis", "Quick Reference"] |
| CICD | docs/CICD.md | 6 | — | ["Pipeline Overview", "Jenkinsfile", "PR Gate", "ArgoCD"] |
```

**影響範圍**：
- 直接影響：dryrun Step 3 write rules.json 時會為 DEVELOPER_GUIDE 生成對應規則
- 下游依賴：pipeline.json 中的 D21b-DEVELOPER_GUIDE step 在 dryrun 後可獲得量化規則
- 測試驗證項：
  1. DEVELOPER_GUIDE-rules.json 成功生成
  2. min_h2_sections=5 正確
  3. required_sections 清單完整

**決策**：規則表應完整覆蓋 pipeline 中的所有 step，缺一不可。

---

### 修改項 3.3

**檔案路徑**：/Users/tobala/projects/gendoc/templates/LOCAL_DEPLOY.gen.md

**修改位置**：檔案開頭（當前無此內容），新增 § 0.1 職責界定

**原內容**（無，新增）

**修改原因**：
缺陷 #3-R3：LOCAL_DEPLOY.gen.md 生成規則中應明確說明此文件的職責邊界（初始化層、一次性、非開發者可用），避免生成的文件偷混涵蓋日常操作。

**修改後內容**（新增在檔案開頭，第 1 行之後）：
```
---

## §0.1 職責界定（生成時強制檢查）

本文件是 LOCAL_DEPLOY.md 的生成規則。生成的 LOCAL_DEPLOY.md **必須遵守以下邊界**：

### 職責範圍（✅ 應包含）
- Prerequisite 工具列表（Rancher Desktop、kubectl、helm、mkcert 等）
- Rancher Desktop 首次啟動設定（Memory / CPU / 容器引擎選項）
- k3s namespace 及 RBAC 初始化
- Kubernetes manifest 編寫範本（Deployment、Service、ConfigMap、Secret、Ingress、PersistentVolume）
- Docker image 構建或拉取指令
- 資料庫初始化（liquibase migration / seed data 載入）
- 一次性網路配置（mkcert 自簽憑證、/etc/hosts 修改）
- 所有服務的 `kubectl apply` 或 `helm install` 指令
- Verification checklist（pod 就緒 / port-forward 測試 / 健康檢查）
- Local Developer Platform（Gitea + Jenkins + ArgoCD）整套一鍵啟動（`make dev-tools-up`）
- 完整的 docker-compose.yaml 作為替代方案（兩種方式均可無礙建置）

### 禁止範圍（❌ 不應包含）
- 日常開發工作流（git push / CI 監控 / CD 驗證）→ 歸 DEVELOPER_GUIDE.md
- 生產故障診斷（pod crash / OOMKilled / DNS 解析失敗）→ 歸 runbook.md
- 環境維護（secret rotate / image 清理 / log 輪替）→ 歸 DEVELOPER_GUIDE.md
- 「開發者日常修改代碼後如何部署」→ 歸 DEVELOPER_GUIDE.md
- 「生產上線步驟」→ 歸 runbook.md / CICD.md

### 品質門檻
- [CRITICAL] 從零開始，完整執行此文件所有步驟後，應能啟動完整環境（`make k8s-apply` 後所有 pod running）
- [CRITICAL] 非開發者（例如 QA / PM）也應能執行此文件
- [HIGH] 不含任何 TBD / TODO / 缺漏步驟
- [HIGH] 所有工具版本明確指定（不允許 ">=1.0" 這類模糊版本）
- [HIGH] 每個步驟有驗證指令（例如 `kubectl get pods` / `helm list` / `curl http://localhost`）

---

```

**影響範圍**：
- 直接影響：LOCAL_DEPLOY.gen.md 生成規則
- 下游依賴：gendoc-gen-diagrams / reviewtemplate 讀取此職責界定，檢驗生成的文件是否遵守邊界
- 測試驗證項：
  1. 生成的 LOCAL_DEPLOY.md 不含日常操作步驟
  2. 生成的 LOCAL_DEPLOY.md 不含生產故障診斷
  3. 職責邊界檢查通過

**決策**：生成規則中明確職責邊界，讓 AI 和 review loop 可據此檢驗生成文件是否符合定義。

---

### 修改項 3.4

**檔案路徑**：/Users/tobala/projects/gendoc/templates/DEVELOPER_GUIDE.gen.md

**修改位置**：檔案開頭（當前無此內容），新增 § 0.1 職責界定

**原內容**（無，新增）

**修改原因**：
缺陷 #3-R3：DEVELOPER_GUIDE.gen.md 應明確界定此文件不重覆 LOCAL_DEPLOY.md 的一次性步驟，而是聚焦日常操作和故障診斷。

**修改後內容**（新增在檔案開頭，第 1 行之後）：
```
---

## §0.1 職責界定（生成時強制檢查）

本文件是 DEVELOPER_GUIDE.md 的生成規則。生成的 DEVELOPER_GUIDE.md **必須遵守以下邊界**：

### 職責範圍（✅ 應包含）
- 日常開發工作流 step-by-step（git push → Jenkins SCM trigger → 監控 pipeline → ArgoCD auto-sync → 應用驗證）
- CI/CD 故障診斷（Jenkins 未觸發 / stage 失敗重跑 / ArgoCD OutOfSync / Gitea webhook 除錯 / image pull 失敗）
- 本地環境快速指令集（`make dev-status` / `make dev-logs` / `make dev-restart` / `make dev-health` / `make dev-shell`）
- 常見問題 Q&A（本地環境特有，例如 Pod pending / image conflict / port 被佔用 / namespace 滿了 / storage 不足 / DNS 延遲）
- 環境維護（密碼/token rotate / image 清理 / namespace 重置 / 日誌檢查）
- 本機性能優化（CPU / Memory 限制調整、cache 策略、log level 設定）
- 開發工具平台使用（Gitea UI / Jenkins UI / ArgoCD UI 存取方式，各自的常見問題）

### 禁止範圍（❌ 不應包含）
- Prerequisite 工具安裝 → 歸 LOCAL_DEPLOY.md
- 一次性環境初始化（k3s 建立、namespace 初始建立、image 初始拉取）→ 歸 LOCAL_DEPLOY.md
- 生產環境故障處理 → 歸 runbook.md
- 「第一次如何建起本機環境」→ 歸 LOCAL_DEPLOY.md
- 「本地環境 100% 清除重來」→ LOCAL_DEPLOY.md 的驗證清單中

### 品質門檻
- [CRITICAL] 文件應為「開發者已完成 LOCAL_DEPLOY.md 後的參考手冊」
- [CRITICAL] 新 team member 看此文件，30 分鐘內應能獨立完成日常工作流（git push + 驗證 ArgoCD）
- [HIGH] 無重複的一次性步驟（all 一次性步驟應在 LOCAL_DEPLOY.md）
- [HIGH] 包含至少 10 個日常場景的 Q&A（pod crash / image pull / webhook / port conflict...）
- [HIGH] 所有指令可複製貼上直接執行，不含模糊描述

### 受眾明確區隔
| 文件 | 受眾 | 場景 |
|-----|------|------|
| LOCAL_DEPLOY.md | 任何人（含非開發者） | 第一次環境搭建 |
| DEVELOPER_GUIDE.md | 開發者 | 日常開發、故障診斷 |
| runbook.md | SRE / On-call | 生產故障應急 |
| CICD.md | DevOps / Platform | Pipeline 設計與維護 |

---

```

**影響範圍**：
- 直接影響：DEVELOPER_GUIDE.gen.md 生成規則
- 下游依賴：gendoc-gen-diagrams / reviewtemplate 據此檢驗
- 測試驗證項：
  1. 生成的文件不含一次性步驟
  2. 生成的文件包含 ≥10 Q&A
  3. 受眾和場景清晰

**決策**：DEVELOPER_GUIDE 應聚焦日常，不補 LOCAL_DEPLOY 的缺漏。職責界定讓生成質量可控。

---

### 修改項 3.5

**檔案路徑**：/Users/tobala/projects/gendoc/templates/LOCAL_DEPLOY.review.md

**修改位置**：Review Checklist 開頭，新增「職責邊界驗證（CRITICAL）」項（第 1 行之前）

**原內容**（當前 LOCAL_DEPLOY.review.md 內容不詳，但通常從檢查清單開始）

**修改原因**：
缺陷 #3-R5：LOCAL_DEPLOY.review.md 應在最高優先級檢查職責邊界（即確認文件未包含日常操作、生產故障等禁區）。

**修改後內容**（新增在 Review Checklist 最開頭，共 5 條 CRITICAL 項）：
```
## Review Checklist — LOCAL_DEPLOY.md

### 職責邊界驗證（CRITICAL）— 檢查清單最優先

> **此段落必須首先通過審查。若邊界違規，其他檢查無意義。**

- [CRITICAL-1] **文件不含日常操作相關內容**  
  掃描文件：搜尋 "git push", "CI", "CD", "deployment", "日常", "每天", "每次修改" 等關鍵詞。  
  預期結果：全部無匹配或僅在說明邊界時出現。  
  違規案例：「修改代碼後執行 git push 觸發 Jenkins」→ 應在 DEVELOPER_GUIDE.md

- [CRITICAL-2] **文件不含生產故障診斷**  
  掃描文件：搜尋 "생산", "production", "故障", "crash", "outage", "incident", "on-call" 等。  
  預期結果：全部無匹配或僅在說明邊界時出現。  
  違規案例：「生產環境 Pod CrashLoopBackOff 解決方法」→ 應在 runbook.md

- [CRITICAL-3] **文件不含環境維護相關步驟**  
  掃描文件：搜尋 "rotate", "清理", "cleanup", "清除", "重置", "reset", "日誌", "log rotation", "secret refresh" 等。  
  預期結果：全部無匹配或僅在說明邊界時出現。  
  違規案例：「定期清理舊 image」→ 應在 DEVELOPER_GUIDE.md

- [CRITICAL-4] **文件必須包含一次性初始化的完整步驟**  
  檢查以下段落是否均存在且完整：
  - Prerequisite 工具列表（版本明確指定）
  - Rancher Desktop / k3s 初始設定
  - Kubernetes manifest apply 完整指令
  - 資料庫初始化（liquibase / seed data）
  - 一次性網路設定（mkcert / /etc/hosts）
  - Local Developer Platform 一鍵啟動（`make dev-tools-up`）
  - docker-compose 替代方案（完整、可無礙執行）
  預期結果：以上全部段落均存在、內容完整、無 TBD。

- [CRITICAL-5] **驗證清單必須包含環境完整性檢查**  
  檢查以下項目是否均有驗證指令：
  - `kubectl get pods -n {{K8S_NAMESPACE}}-local` → 所有 pod running
  - `kubectl port-forward ...` 或 Ingress 訪問 → 應用可達
  - `helm list -n {{K8S_NAMESPACE}}-local` → 所有 helm release 就緒
  - `kubectl logs -f pod/...` → 應用日誌無錯誤
  - Database connectivity test（`psql` / `mysql` 連線成功）
  - Unit / Integration / E2E test 執行成功（`make test` 或 `npm test` 通過）
  預期結果：5 項驗證全通過後，環境完整性可認定。

---

[以下為原有的 Review Checklist...]
```

**影響範圍**：
- 直接影響：LOCAL_DEPLOY.review.md 審查清單
- 下游依賴：gendoc-flow review loop 第一輪即檢驗邊界
- 測試驗證項：
  1. CRITICAL-1 至 CRITICAL-5 全部通過
  2. 邊界違規被正確偵測

**決策**：職責邊界是文件品質的前提，應優先檢查，高於其他檢查項。

---

### 修改項 3.6

**檔案路徑**：/Users/tobala/projects/gendoc/templates/DEVELOPER_GUIDE.review.md

**修改位置**：Review Checklist 開頭，新增「職責邊界驗證（CRITICAL）」項 + 日常場景檢查（第 1 行之前）

**原內容**（當前 DEVELOPER_GUIDE.review.md 內容不詳）

**修改原因**：
缺陷 #3-R6：DEVELOPER_GUIDE.review.md 應在最高優先級檢查職責邊界（確認無一次性步驟、無生產故障內容），並驗證日常場景涵蓋充分。

**修改後內容**（新增在 Review Checklist 最開頭，共 10 條檢查項）：
```
## Review Checklist — DEVELOPER_GUIDE.md

### 職責邊界驗證（CRITICAL）— 檢查清單最優先

> **此段落必須首先通過審查。若邊界違規，其他檢查無意義。**

- [CRITICAL-1] **文件不含一次性環境初始化步驟**  
  掃描文件：搜尋 "安裝", "install", "setup", "初始化", "initialization", "第一次", "初始建立" 等。  
  預期結果：全部無匹配或僅在邊界說明時出現（「參考 LOCAL_DEPLOY.md」）。  
  違規案例：「執行 mkcert --install」或「kubectl create namespace」→ 應在 LOCAL_DEPLOY.md

- [CRITICAL-2] **文件不含生產環境內容**  
  掃描文件：搜尋 "production", "生產", "prod-", "staging", "上線", "release" 等。  
  預期結果：全部無匹配或僅在「區隔說明」時出現。  
  違規案例：「生產故障排查清單」→ 應在 runbook.md；「生產部署步驟」→ 應在 CICD.md

- [CRITICAL-3] **文件必須開頭明確標示前置條件**  
  檢查第一段落是否清晰說明：
  - 「前提：已完成 LOCAL_DEPLOY.md 初始建置」
  - 「本文件針對已搭建好的本地環境，日常開發操作指南」
  - 「若環境從未搭建過，請先執行 LOCAL_DEPLOY.md」
  預期結果：這三點均明確呈現。

- [CRITICAL-4] **文件必須包含日常工作流完整步驟**  
  檢查以下 section 是否均存在：
  - §1 日常開發工作流（git push → Jenkins trigger → 監控 pipeline → ArgoCD auto-sync → 應用驗證）
  - §2 CI/CD 故障診斷（至少 5 個常見問題 + 解決步驟）
  - §3 本地環境快速指令（`make dev-status` / `make dev-logs` / `make dev-restart` 等 ≥4 個）
  - §4 常見問題 Q&A（≥10 個本地環境特有問題）
  - §5 環境維護（密碼 rotate / image 清理 / 日誌檢查）
  預期結果：5 個 section 均存在、內容完整。

### 日常場景詳細檢查（HIGH）

- [HIGH-1] **日常工作流完整性**  
  驗證 §1 是否涵蓋完整的：git push → Jenkins log 監控 → Pipeline stage 列表 → ArgoCD UI 檢查同步狀態 → Pod 健康檢查。  
  預期結果：新 dev 只看此 section，應能獨立完成一次 commit → deploy 循環。

- [HIGH-2] **CI/CD 故障診斷詳細度**  
  檢查 §2 是否包含：
  - Jenkins 未觸發（Gitea webhook 配置）
  - Pipeline stage 失敗重跑（Blue Ocean UI 使用）
  - ArgoCD OutOfSync（manifest 差異檢查）
  - Image pull failed（Docker registry 驗證）
  - Pod pending / CrashLoopBackOff（本地環境特有的 resource limit 問題）
  預期結果：≥5 個常見問題，每個均有明確的故障現象 + 診斷指令 + 解決步驟。

- [HIGH-3] **快速指令的實用性**  
  檢查 §3 Makefile targets 或 shell script 是否可複製貼上直接執行（不含模糊變數 / 不需 manual substitution）。  
  預期結果：每個指令均可不加修改直接執行。例如 `make dev-logs pod-name=api` 而非「將 POD_NAME 替換為...」。

- [HIGH-4] **常見問題的代表性**  
  檢查 §4 Q&A 是否涵蓋：
  - Namespace 資源滿（Pod pending 因 CPU / Memory limit）
  - DNS 延遲（service 解析失敗）
  - Storage 不足（PVC pending）
  - Image conflict（image pull 卡住）
  - Database 連線失敗（SQL connection refused）
  - Port 被佔用（port-forward 衝突）
  - Cache 過期（node_modules / build cache 需清理）
  預期結果：≥10 個 Q&A，涵蓋本地環境的典型故障 signature。

- [HIGH-5] **環境維護的可操作性**  
  檢查 §5 是否明確指出：
  - 定期任務（多久一次）
  - 具體指令（可複製貼上）
  - 驗證方式（執行後如何確認成功）
  例如：「每月 rotate 密碼：`kubectl create secret ... --dry-run=client -o yaml | kubectl apply -f -`」  
  預期結果：無模糊描述，每項維護均有明確的指令和驗證。

---

[以下為原有的其他 Review Checklist...]
```

**影響範圍**：
- 直接影響：DEVELOPER_GUIDE.review.md 審查清單
- 下游依賴：gendoc-flow review loop 中檢驗邊界和日常場景
- 測試驗證項：
  1. CRITICAL-1 至 CRITICAL-4 全部通過
  2. HIGH-1 至 HIGH-5 全部通過
  3. 邊界違規被正確偵測

**決策**：日常場景檢查確保 DEVELOPER_GUIDE 真正有用，不只列清單。

---

### 修改項 3.7

**檔案路徑**：/Users/tobala/projects/gendoc/docs/PRD.md

**修改位置**：Change Log 表頂部，新增 v3.2.1 行（在 v3.2 上方），或建立 v3.3 版本行

**原內容**：
```
[第 27 行]
| v3.2 | 2026-05-03 | PM Agent | **UML Class Diagram...
```

**修改原因**：
缺陷 #3-R7：PRD 應記錄本輪修改（LOCAL_DEPLOY + DEVELOPER_GUIDE 分離、職責邊界、review checklist 擴充）。

**修改後內容**（在 v3.2 行前新增 v3.3 版本）：
```
| v3.3 | 2026-05-03 | PM Agent | **LOCAL_DEPLOY ↔ DEVELOPER_GUIDE 職責分離完整化**：(1) **PRD 標準 #6 拆分為 6a/6b/6c**：LOCAL_DEPLOY 專責初始化（一次性、非開發者可用）、DEVELOPER_GUIDE 專責日常操作（git push → CI/CD → 驗證，本地故障診斷，快速指令），職責邊界明確；(2) **dryrun 規則表補齊 DEVELOPER_GUIDE 行**：Step 3 now covers DEVELOPER_GUIDE-rules.json 生成；(3) **LOCAL_DEPLOY.gen.md 新增 §0.1 職責界定**：明確告知 AI 此文件的禁區（日常操作 / 生產故障 / 環境維護）；(4) **DEVELOPER_GUIDE.gen.md 新增 §0.1 職責界定**：明確告知 AI 此文件聚焦日常，不重複一次性步驟；(5) **LOCAL_DEPLOY.review.md CRITICAL-1~5 新增**：職責邊界驗證（5 條 CRITICAL 檢查）；(6) **DEVELOPER_GUIDE.review.md CRITICAL-1~4 + HIGH-1~5 新增**：職責邊界驗證 + 日常場景詳細檢查（9 條檢查）；(7) **受眾明確分離**：LOCAL_DEPLOY（任何人）/ DEVELOPER_GUIDE（開發者）/ runbook.md（SRE）/ CICD.md（DevOps）各有明確角色與場景。**硬性約束**：本版修改涵蓋 3 個 gen.md + 2 個 review.md + PRD + dryrun，共 7 項。 |
| v3.2 | 2026-05-03 | PM Agent | **UML Class Diagram...
```

**影響範圍**：
- 直接影響：PRD Change Log
- 下游依賴：release note / version tracking
- 測試驗證項：
  1. v3.3 版本號清晰
  2. 變更摘要覆蓋全部 7 項修改

**決策**：完整記錄此輪修改，供日後查證和版本管理。

---

## 摘要表

| 缺陷 | 項目 ID | 檔案 | 修改類型 | 狀態 |
|-----|---------|------|---------|------|
| #1 DRYRUN 三態 | 1.1 | gendoc-gen-dryrun/SKILL.md | Step 1.6 新增 | ✅ 詳列 |
| | 1.2 | gendoc-gen-dryrun/SKILL.md | Step 4 擴充 | ✅ 詳列 |
| | 1.3 | gendoc-repair/SKILL.md | Step 1.6 新增 | ✅ 詳列 |
| | 1.4 | gendoc-repair/SKILL.md | Step 3c 擴充 | ✅ 詳列 |
| | 1.5 | PRD.md | Change Log v3.2.1 新增 | ✅ 詳列 |
| #2 正則精度 | 2.1 | gendoc-gen-dryrun/SKILL.md | Step 1-2A 精化 | ✅ 詳列 |
| | 2.2 | gendoc-gen-dryrun/SKILL.md | Step 1-2B 精化 | ✅ 詳列 |
| | 2.3 | gendoc-gen-dryrun/SKILL.md | Step 1-2C 精化 | ✅ 詳列 |
| | 2.4 | gendoc-gen-dryrun/SKILL.md | Step 1-2D 精化 | ✅ 詳列 |
| | 2.5 | PRD.md | Appendix A 新增 | ✅ 詳列 |
| #3 職責分離 | 3.1 | PRD.md | 標準 #6 拆分 | ✅ 詳列 |
| | 3.2 | gendoc-gen-dryrun/SKILL.md | Step 3 表補齊 | ✅ 詳列 |
| | 3.3 | LOCAL_DEPLOY.gen.md | §0.1 新增 | ✅ 詳列 |
| | 3.4 | DEVELOPER_GUIDE.gen.md | §0.1 新增 | ✅ 詳列 |
| | 3.5 | LOCAL_DEPLOY.review.md | CRITICAL-1~5 新增 | ✅ 詳列 |
| | 3.6 | DEVELOPER_GUIDE.review.md | CRITICAL-1~4 + HIGH-1~5 新增 | ✅ 詳列 |
| | 3.7 | PRD.md | Change Log v3.3 新增 | ✅ 詳列 |

---

**總計**：17 項修改，全部詳列完成。

**下一步**：
1. 逐項檢查修改內容是否符合您的需求
2. 確認後可按序執行（Edit / Write 工具）
3. 完成後 commit + push + install/upgrade

