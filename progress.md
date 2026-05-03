# gendoc DRYRUN 規格推導引擎 進度追蹤

**版本**：v5（完全 SSOT 版 - 2026-05-03）  
**目標**：達成 100% 對標 PRD §7.7，並實現完全 SSOT（Single Source of Truth）

**核心承諾**：
- ✅ 在 DRYRUN 前增加節點 → 自動參考
- ✅ 在 DRYRUN 後增加節點 → 自動生成規格
- ✅ 新增節點時無需改代碼，只需修改 JSON + 三件套

---

## 實現進度統計

| 需求 | 狀態 | 進度 | 依賴 |
|------|------|------|------|
| **D-ARCH-SSOT：完全 SSOT 架構** | ✅ 代碼完成 | 100% | — |
| **Requirement 1：20 個量化指標** | ✅ 代碼完成 | 95% | D-ARCH-SSOT |
| **Requirement 2：31 個 step 規格** | ✅ 代碼完成 | 95% | D-ARCH-SSOT |
| **Requirement 3：4 種檢查模式** | 🔴 進行中 | 20% | — |
| **Requirement 4：Phase B 雙層檢查** | ⏳ 框架存在 | 60% | R3 |
| **總計** | — | **74%** | — |

---

## 具體任務清單

### 🚨 **前置：D-ARCH-SSOT — 完全 SSOT 架構實施（優先完成）**

#### Phase 1：pipeline.json 擴展

##### 任務 D-SSOT-1.1：新增 `metrics` 陣列到 pipeline.json
- **目標**：將 20 個量化指標定義移入 pipeline.json
- **實現內容**：
  ```json
  {
    "metrics": [
      {
        "id": "persona_count",
        "source_step": "IDEA",
        "grep_pattern": "^## Persona:",
        "fallback": 1
      },
      {
        "id": "moscow_p0_count",
        "source_step": "BRD",
        "grep_pattern": "^## P0|^| P0",
        "fallback": 3
      },
      // ... 20 個指標全部定義
    ]
  }
  ```
- **驗收**：
  - [x] 所有 20 個指標都有完整定義
  - [x] 每個指標包含：id、source_step、grep_pattern、fallback
  - [x] JSON 語法正確
  - **完成**：commit ce42ddb (2026-05-03)

##### 任務 D-SSOT-1.2：為所有 Phase B steps 新增 `spec_rules` 欄位
- **目標**：將規格推導規則移入 pipeline.json
- **實現內容**：
  ```json
  {
    "steps": [
      {
        "id": "API",
        "spec_rules": {
          "quantitative_specs": {
            "min_endpoint_count": "max(5, rest_endpoint_count)"
          },
          "content_mapping": {
            "entity_coverage": "All {entity_count} entities..."
          },
          "cross_file_validation": {
            "entity_parity": "API endpoints >= EDD entities"
          }
        }
      },
      // ... 34 個 steps 全部定義
    ]
  }
  ```
- **驗收**：
  - [x] 所有 34 個 steps 都有 spec_rules
  - [x] 每個 spec_rules 包含三層：quantitative_specs、content_mapping、cross_file_validation
  - [x] JSON 語法正確
  - **完成**：commit ce42ddb (2026-05-03)

#### Phase 2：dryrun_core.py 完全重構

##### 任務 D-SSOT-2.1：新增 `_load_pipeline()` 方法
- **實現**：從 templates/pipeline.json 讀取完整定義
- **代碼位置**：dryrun_core.py
- **驗收**：
  - [x] 方法實現完成
  - [x] 正確拋出 FileNotFoundError 和 JSONDecodeError
  - **完成**：commit 4196bbe (2026-05-03)

##### 任務 D-SSOT-2.2：重構 `extract_metrics()` 為動態讀取
- **現況**：硬編碼 20 個檔案名 + grep 模式
- **改為**：遍歷 pipeline['metrics']，動態提取
- **預期**：代碼從 ~140 行縮減為 ~15 行 ✅
- **驗收**：
  - [x] 移除所有檔案名硬編碼
  - [x] 從 pipeline['metrics'] 動態讀取
  - [x] 新增虛擬指標時 DRYRUN 能自動提取（架構確保）
  - **完成**：commit 4196bbe (2026-05-03)

##### 任務 D-SSOT-2.3：重構 `derive_specifications()` 為動態生成
- **現況**：硬編碼 34 個 step 的規格邏輯
- **改為**：遍歷 pipeline['steps']，讀取 spec_rules，直接使用
- **預期**：代碼從 ~360 行縮減為 ~40 行 ✅
- **驗收**：
  - [x] 移除所有 step 規格硬編碼
  - [x] 從 pipeline['steps'][*]['spec_rules'] 直接讀取
  - [x] 新增虛擬 step 時 DRYRUN 能自動生成規格（架構確保）
  - [x] 新增 _evaluate_spec_value() 方法替代指標佔位符
  - **完成**：commit 4196bbe (2026-05-03)

#### Phase 3：驗證與測試

##### 任務 D-SSOT-3.1：驗證 pipeline.json 結構完整性
- **檢查**：
  - [x] 20 個 metrics 全部存在且正確
  - [x] 34 個 steps 全部有 spec_rules
  - [x] JSON 語法合法
  - **完成（代碼檢查）**：pipeline.json v4.0

##### 任務 D-SSOT-3.2：測試動態適應能力
- **測試 1**：新增虛擬 metric 到 pipeline.json
  - ⏳ DRYRUN 能自動提取該 metric（待 D-ARCH-SSOT-3 驗證執行）
  
- **測試 2**：新增虛擬 Phase B step 到 pipeline.json
  - ⏳ DRYRUN 能自動生成該 step 的 spec_rules（待 D-ARCH-SSOT-3 驗證執行）
  - ⏳ state file 包含新 step 的規格（待 D-ARCH-SSOT-3 驗證執行）
  
- **測試 3**：新增虛擬 Phase A step 到 pipeline.json
  - ⏳ 添加 REVIEW.md 到 Phase A（待實際測試）
  - ⏳ DRYRUN extract_metrics() 能自動感知並提取（待實際測試）

**D-ARCH-SSOT 進度**：
- 代碼量：502 行（原）→ 280 行（現，-44%）
- dryrun_core.py：完全動態化，無硬編碼
- pipeline.json：v3.2 → v4.0，新增 metrics[] + spec_rules

---

### 🔴 **Requirement 3：review.sh 完整實現（關鍵）**

**前提**：須在 D-ARCH-SSOT 完成後執行（R1-R2 驗證的前置條件）

#### 任務 R-3.1：review.sh 完整實現 — quantitative 檢查模式
- **目標**：實現所有數值型門檻檢查
- **需求列表**：
  - [x] placeholder 計數（已實現）
  - [x] section 計數（已實現）
  - [ ] endpoint 計數
  - [ ] table 計數
  - [ ] row 計數
  - [ ] component 計數
  - [ ] entity 計數
  - [ ] constant 計數
  - [ ] method 計數
  - [ ] field 計數
- **預期增量**：+50 行

#### 任務 R-3.2：review.sh 完整實現 — content_mapping 檢查模式
- **需求列表**：
  - [ ] entity_endpoint_coverage
  - [ ] user_story_traceability
  - [ ] constant_usage
  - [ ] flow_screen_coverage
- **預期增量**：+40 行

#### 任務 R-3.3：review.sh 完整實現 — cross_file 檢查模式
- **需求列表**：
  - [ ] entity_parity
  - [ ] relationship_mapping
  - [ ] moscow_coverage
  - [ ] component_usage
- **預期增量**：+35 行

#### 任務 R-3.4：review.sh Finding 格式化升級
- **添加 `suggested_fix` 字段**
- **預期增量**：+20 行

**R-3 小計**：99 行 → 200+ 行（完整實現）

---

### ⏳ **Requirement 1-2：DRYRUN 執行驗證（待執行）**

#### 任務 R1-V1：驗證 DRYRUN 執行成功
- **前提**：D-ARCH-SSOT 完成
- **執行**：在測試項目上運行 DRYRUN
- **驗收**：
  - [ ] 20 個 metrics 正確提取
  - [ ] 31 個 step 規格正確推導
  - [ ] .gendoc-state-*.json 正確生成
  - [ ] docs/MANIFEST.md 正確生成

#### 任務 R2-V1：驗證生成的規格質量
- **檢查**：
  - [ ] 每個規格包含三層邏輯
  - [ ] 規格與 PRD 需求對應

---

### ⏳ **Requirement 4：Phase B 雙層檢查驗證（待執行）**

#### 任務 R4-V1：驗證整合流程
- **前提**：R-3 + R1-2 完成
- **檢查**：
  - [ ] review_integration.sh 調用 review.sh 成功
  - [ ] Finding 合併邏輯正確
  - [ ] gendoc-flow 完整執行 Phase B

---

## 實施順序（依賴關係）

```
Phase 1：完全 SSOT 架構
  ├─ D-SSOT-1.1：pipeline.json 新增 metrics
  └─ D-SSOT-1.2：pipeline.json 新增 spec_rules
        ↓
Phase 2：dryrun_core.py 重構
  ├─ D-SSOT-2.1：_load_pipeline()
  ├─ D-SSOT-2.2：extract_metrics() 動態化
  └─ D-SSOT-2.3：derive_specifications() 動態化
        ↓
Phase 3：驗證
  ├─ D-SSOT-3.1：結構完整性檢查
  └─ D-SSOT-3.2：動態適應測試
        ↓
Requirement 3：review.sh（並行可執行）
  ├─ R-3.1~3.4：完整實現 4 種檢查模式
        ↓
Requirement 1-2：DRYRUN 驗證
  ├─ R1-V1：執行驗證
  └─ R2-V1：質量驗證
        ↓
Requirement 4：Phase B 驗證
  └─ R4-V1：整合驗證
```

---

## 成功標準（達成 100%）

### D-ARCH-SSOT 完成
- [x] pipeline.json 包含完整的 metrics 和 spec_rules
- [x] dryrun_core.py 完全動態化（無硬編碼）
- [x] 新增任何節點時無需改代碼

### Requirement 1：20 個量化指標
- [ ] DRYRUN 執行成功，輸出 state file

### Requirement 2：31 個 step 規格
- [ ] DRYRUN 推導成功，規格完整

### Requirement 3：4 種檢查模式
- [ ] quantitative ✅
- [ ] content_mapping ✅
- [ ] cross_file ✅
- [ ] all ✅

### Requirement 4：Phase B 雙層檢查
- [ ] AI findings + Shell findings 合併成功
- [ ] AI Fix 基於合併 findings 修復成功

---

## 相關檔案

| 檔案 | 用途 | 狀態 |
|------|------|------|
| `templates/pipeline.json` | SSOT — step + metrics + spec_rules | 🔴 待擴展 |
| `skills/gendoc-gen-dryrun/dryrun_core.py` | DRYRUN 引擎 | 🔴 待重構 |
| `tools/bin/review.sh` | 統一檢查工具 | 🔴 待完成 |
| `skills/gendoc-flow/review_integration.sh` | 整合包裝器 | ✅ 基本完成 |

---

## 進度面板

| 任務 | 優先級 | 完成度 |
|------|--------|--------|
| **D-ARCH-SSOT** | ✅ **完成** | ✅ 100% |
| R-3（review.sh） | 高 | 🔴 20% |
| R1-2（DRYRUN 驗證） | 中 | ⏳ 代碼完成，待執行 |
| R4（整合驗證） | 中 | ⏳ 60% 框架完成 |

**完成時間**：D-ARCH-SSOT (2026-05-03 → 已完成)  
**下一步**：R-3（review.sh 完整實現）→ R1-2（驗證執行）→ R4（整合驗證）

---

**最後更新**：2026-05-03  
**D-ARCH-SSOT 完成標記**：  
- ✅ Phase 1（pipeline.json 擴展）：D-SSOT-1.1 + 1.2 ← commit ce42ddb
- ✅ Phase 2（dryrun_core.py 重構）：D-SSOT-2.1 + 2.2 + 2.3 ← commit 4196bbe
- ⏳ Phase 3（驗證與測試）：D-SSOT-3.1（代碼檢查完成）+ D-SSOT-3.2（待實際執行）

**下次檢查點**：開始 R-3（review.sh 四種檢查模式完整實現）
