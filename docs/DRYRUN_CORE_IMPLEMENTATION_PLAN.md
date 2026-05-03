---
title: DRYRUN Core 實作計畫
date: 2026-05-04
version: 1.0
status: 規劃階段
---

# DRYRUN Core 實作計畫

## 核心設計原則（確認）

### 雙層獨立驗證架構

```
DRYRUN 前的文件
    ↓
[DRYRUN 推導層] → 期望規格（計劃）
    ↓
.gendoc-rules/*.json（DRYRUN 推導結果）
    ↓
DRYRUN 后的 step 各 STEP 實現
    ↓
[各 STEP template 實現層] → 實際生成（獨立實現）
    ↓
docs/<STEP>.md（實際生成結果）
    ↓
[審查工具] → 對比驗證
    ↓
期望 vs 實際 → ✅ 通過 / ❌ 失敗
```

**關鍵原則**：
- pipeline.json：只定義 `input[]` + `output[]`（無 metrics、無公式）
- DRYRUN：獨立推導邏輯（在 dryrun_core.py 中實現）
- 各 STEP：獨立實現邏輯（在 *.gen.md 中）
- 審查：對比兩條獨立路徑的結果

---

## DRYRUN 前的 step（上游分析）- DRYRUN 推導

### 需要提取的參數

| 參數 | 來源 | 含義 | 示例 |
|------|------|------|------|
| `entity_count` | EDD.md | 資料庫 entity 數 | 有 10 個 class → schema 應有 ≥10 個 table |
| `rest_endpoint_count` | PRD.md + EDD.md | REST API endpoint 數 | 有 5 個 endpoint → API.md 應有 ≥5 個 endpoint 章節 |
| `user_story_count` | PRD.md | User Story 數 | 有 20 個 US → test-plan 應 ≥22 章、BDD 應 ≥16 scenario |
| `arch_layer_count` | ARCH.md | 架構層數 | 有 4 層 → test-plan 應 ≥6 章（4+2） |
| `admin_feature_count` | EDD.md（若 has_admin_backend） | Admin 相關特性數 | 用於評估 ADMIN_IMPL 規模 |

### DRYRUN 推導的期望規格

**SCHEMA.md**：
- 期望：`min_table_count = max(entity_count, 3)`
- 存儲：`.gendoc-rules/SCHEMA-rules.json` → `{"min_table_count": <數字>}`

**API.md**：
- 期望：`min_endpoint_count = max(rest_endpoint_count, 5)`
- 存儲：`.gendoc-rules/API-rules.json` → `{"min_endpoint_count": <數字>}`

**test-plan.md**：
- 期望：`min_h2_sections = arch_layer_count + 2`
- 存儲：`.gendoc-rules/test-plan-rules.json` → `{"min_h2_sections": <數字>}`

**BDD-server**：
- 期望：`min_scenario_count = ceil(user_story_count * 0.8)`
- 存儲：`.gendoc-rules/BDD-server-rules.json` → `{"min_scenario_count": <數字>}`

（其他 DRYRUN 后的 step 類似推導）

---

## DRYRUN 后的 step（實現分析）- 各 STEP 獨立實現

### SCHEMA.gen.md 的實現邏輯

**獨立讀取**：EDD.md（entity 定義）、CONSTANTS.md、PDD.md
**獨立推導**：生成 table 定義
**實際結果**：`docs/SCHEMA.md` 中有 X 個 table

### API.gen.md 的實現邏輯

**獨立讀取**：PRD.md（User Story + AC）、EDD.md、CONSTANTS.md
**獨立推導**：生成 endpoint 定義
**實際結果**：`docs/API.md` 中有 Y 個 endpoint

（各 STEP 類似獨立實現）

---

## 審查層 - 機械式驗證

### review.sh 邏輯

```bash
# 對於每個 DRYRUN 后的 step：
1. 讀取 .gendoc-rules/<step>-rules.json（DRYRUN 期望）
2. 掃描 docs/<step>.md（實際生成）
3. 計算實際數量（table、endpoint、scenario 等）
4. 對比：期望 vs 實際
5. 輸出：PASS / FAIL + 詳細差異
```

**機械式檢查項目**（量化）：
- `min_table_count`：期望 10 table → 實際 10 table ✅
- `min_endpoint_count`：期望 5 endpoint → 實際 6 endpoint ✅
- `min_h2_sections`：期望 6 章 → 實際 6 章 ✅
- （不涉及 AI 的主觀判斷）

---

## 實作 STEP 分解

### STEP 1：DRYRUN 參數提取邏輯設計
**目標**：定義如何從上游文件提取參數
- 設計 entity_count、rest_endpoint_count、user_story_count、arch_layer_count 的提取規則
- 根據實際 EDD/PRD/ARCH 結構決定 grep 模式或 parse 邏輯
- 確認 fallback 值（若參數無法提取）

**輸出**：`docs/DRYRUN_PARAMETER_EXTRACTION.md`（定義每個參數的提取方法）

### STEP 2：DRYRUN 規格推導公式設計
**目標**：定義每個 DRYRUN 后的 step 的期望規格公式
- SCHEMA：`min_table_count = max(entity_count, 3)`
- API：`min_endpoint_count = max(rest_endpoint_count, 5)`
- test-plan：`min_h2_sections = arch_layer_count + 2`
- （類似定義其他 ~20 個 steps）

**輸出**：`docs/DRYRUN_SPEC_FORMULAS.md`（所有公式清單）

### STEP 3：實現 dryrun_core.py
**目標**：完成 DRYRUNEngine 類的實現
1. `_load_upstream()`：調用 get-upstream 讀取 DRYRUN step 定義的上游文件
2. `extract_parameters()`：根據 STEP 1 的規則提取 4 個核心參數
3. `derive_specifications()`：根據 STEP 2 的公式計算每個 step 的期望規格
4. `generate_rules_json()`：輸出 `.gendoc-rules/<step-id>-rules.json`
5. `generate_manifest()`：輸出 `docs/MANIFEST.md`（量化基線報告）

**輸出**：更新的 `tools/bin/dryrun_core.py`

### STEP 4：全專案掃描 - 找出 hardcoded 規格
**目標**：掃描所有 skill 和 template，找出不依賴 pipeline 的規格定義
```bash
# 搜索 hardcoded 規格
grep -r "min_.*count\|min_.*section" skills/ templates/ --include="*.md" --include="*.py"

# 搜索 hardcoded 公式
grep -r "= max(\|= min(\|= ceil(" tools/ --include="*.py"

# 搜索 hardcoded metrics
grep -r "entity_count\|endpoint_count\|user_story" skills/ templates/ --include="*.md" --exclude-dir=.git
```

**輸出**：`docs/HARDCODED_SPECS_AUDIT.md`（清單 + 改正方案）

### STEP 5：修正 hardcoded 規格
**目標**：將所有 hardcoded 規格改為依賴 DRYRUN 輸出
- 各 STEP template（SCHEMA.gen.md、API.gen.md 等）：不硬編碼最小值，改由 review.sh 讀 .gendoc-rules/ 驗證
- skills（gendoc-align-check 等）：若涉及量化檢查，改讀 pipeline.json 或 .gendoc-rules/

**輸出**：修正後的各檔案 + commit

### STEP 6：實現審查工具 review.sh
**目標**：機械式對比 DRYRUN 期望 vs 實際生成
1. 讀取 .gendoc-rules/*.json（DRYRUN 期望）
2. 掃描 docs/*.md（實際生成），計算實際數量
3. 對比並輸出 PASS / FAIL

**輸出**：`tools/bin/review.sh`（或 Python 版本）

---

## 檢查清單

- [ ] STEP 1：參數提取規則文件
- [ ] STEP 2：規格推導公式文件  
- [ ] STEP 3：dryrun_core.py 實現完成
- [ ] STEP 4：hardcoded 規格掃描報告
- [ ] STEP 5：所有 hardcoded 規格已修正
- [ ] STEP 6：審查工具 review.sh 實現完成
- [ ] 全迴歸測試：用一個實際專案跑完整 DRYRUN → DRYRUN 后的 step → review 流程

---

## 預期時間表

| STEP | 工作 | 預估 |
|------|------|------|
| 1 | 參數提取規則設計 | 1 小時 |
| 2 | 規格公式設計 | 2 小時 |
| 3 | dryrun_core.py 實現 | 3 小時 |
| 4 | hardcoded 掃描 | 1 小時 |
| 5 | 修正所有 hardcoded | 2 小時 |
| 6 | review.sh 實現 | 2 小時 |
| 驗證 | 實際專案測試 | 1 小時 |
| **總計** | | **12 小時** |

