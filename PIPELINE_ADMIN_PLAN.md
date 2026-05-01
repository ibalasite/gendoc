# gendoc Pipeline 重構 + Admin 支援 — 執行計劃

> **狀態：草稿，待 Review**
> 日期：2026-05-01
> 本文件供 Review 後決定執行策略，尚未動任何程式碼。

---

## 一、背景與設計決策

### 1.1 Pipeline 架構改革的動機

目前 `pipeline.json` 的問題：
- Step ID 含數字前綴（D05-EDD），造成誤解「第5步一定是EDD」
- 插入新節點需要重新排序 ID，維護成本高
- 各 SKILL.md 有部分寫死的步驟名稱，pipeline 異動需同步多檔
- JSON 格式不易手動閱讀與 review

**決策：pipeline.json → pipeline.yml（YAML 格式，去除數字前綴）**
- 所有 skill 動態讀取 pipeline.yml，不寫死步驟清單
- 插入新節點只改 pipeline.yml，所有 skill 自動生效
- YAML 格式可加 comment，文件即代碼

### 1.2 CONSTANTS 整合的動機

目前 CONSTANTS 是獨立 pipeline step（D03.5-CONSTANTS），問題：
- Constants 本質上是「PRD 數字統一」，是制作 EDD 前必須和 PM 確認的數字
- 獨立一個 step 讓溝通成本提高（對 stakeholder 解釋多一份文件）
- EDD Pass-A 和 Pass-C 本來就已讀取 CONSTANTS.md，說明它是 EDD 前置工作

**決策：CONSTANTS 合併進 EDD Pass-0**
- EDD 由 3-pass 升為 4-pass（Pass-0 + Pass-A + Pass-B + Pass-C）
- Pass-0：從 PRD 提取業務數值，輸出 docs/constants.json（機器可讀）+ docs/CONSTANTS.md（人類可讀）
- pipeline.yml 移除 CONSTANTS 獨立節點
- `CONSTANTS.gen.md` 標記為 deprecated（保留作歷史參考，不再被 pipeline 呼叫）

### 1.3 Admin Backend 支援的動機

目前 gendoc 只有 client_type（none / web / game / api-only）控制分支，沒有 admin 後台概念：
- 大多數商業系統都有 admin portal
- admin 有獨特的 RBAC 架構、Component Library 選型、CRUD 模式
- 不加 admin 支援，PRD/EDD/API 等文件會漏掉 admin 相關需求

**決策：新增 `has_admin_backend` flag + `ADMIN_IMPL` pipeline 節點**
- Admin 預設技術棧：**Vue3 + Element Plus + Vite**（業界 admin 最成熟組合，RBAC+CRUD 有大量範例）
- 在 EDD §3.3 宣告 `_ADMIN_FRAMEWORK`（預設值 = Vue3+ElementPlus+Vite）
- 建立 ADMIN_IMPL 三件套模板（.md / .gen.md / .review.md）
- 相關文件（PRD/PDD/VDD/ARCH/API/SCHEMA/FRONTEND/RTM/runbook/LOCAL_DEPLOY/CONTRACTS/PROTOTYPE）條件性加入 admin 章節

### 1.4 ADMIN_IMPL vs CLIENT_IMPL 的邊界

| 面向 | CLIENT_IMPL | ADMIN_IMPL |
|------|-------------|------------|
| 處理對象 | 前台：Cocos/Unity/React/Vue/HTML5 | 後台：Vue3+ElementPlus Admin Portal |
| 架構模式 | 場景/遊戲/SPA | RBAC + CRUD Layout |
| 引擎偵測 | EDD §3.3 `_CLIENT_ENGINE` | EDD §3.3 `_ADMIN_FRAMEWORK` |
| 狀態管理 | 引擎原生 | Pinia + ElementPlus |
| 觸發條件 | client_type != none | has_admin_backend = true |

**關鍵**：CLIENT_IMPL 需加入明確排除說明：「若 EDD §3.3 Vue 應用為 admin 後台 → 請見 ADMIN_IMPL.md，不走本文件」

---

## 二、新 Pipeline 節點順序

### 完整流程（移除數字前綴後）

```
需求層
  IDEA        → docs/IDEA.md
  BRD         → docs/BRD.md
  PRD         → docs/PRD.md

設計層
  PDD         → docs/PDD.md          [condition: client_type != none]
  VDD         → docs/VDD.md          [condition: client_type != none]
  EDD         → docs/EDD.md          ← Pass-0 新增（含 constants.json 輸出）
  ARCH        → docs/ARCH.md
  UML         → docs/diagrams/       [special_skill: gendoc-gen-diagrams]
  API         → docs/API.md
  SCHEMA      → docs/SCHEMA.md
  FRONTEND    → docs/FRONTEND.md     [condition: client_type != none]
  AUDIO       → docs/AUDIO.md        [condition: client_type == game]
  ANIM        → docs/ANIM.md         [condition: client_type == game]
  ADMIN_IMPL  → docs/ADMIN_IMPL.md   [condition: has_admin_backend = true]  ← NEW
  CLIENT_IMPL → docs/CLIENT_IMPL.md  [condition: client_type != none]

品質層
  test-plan   → docs/test-plan.md
  BDD-server  → features/*.feature
  BDD-client  → features/client/*.feature  [condition: client_type != none]
  RTM         → docs/RTM.md

運維層
  runbook         → docs/runbook.md
  LOCAL_DEPLOY    → docs/LOCAL_DEPLOY.md

稽核層
  ALIGN           → docs/ALIGN_REPORT.md    [special_skill: gendoc-align-check]
  ALIGN-F         → docs/ALIGN_REPORT.md    [special_skill: gendoc-align-fix]
  ALIGN-VERIFY    → docs/ALIGN_REPORT.md    [special_skill: gendoc-align-check]

實作層
  CONTRACTS   → docs/blueprint/contracts/   [special_skill: gendoc-gen-contracts]
  MOCK        → docs/blueprint/mock/        [special_skill: gendoc-gen-mock, condition: client_type != api-only]
  PROTOTYPE   → docs/pages/prototype/       [special_skill: gendoc-gen-prototype, condition: client_type != api-only]

發布層
  HTML        → docs/pages/                 [special_skill: gendoc-gen-html]
```

### ID 對應表（舊 → 新）

| 舊 ID | 新 ID | 變更說明 |
|-------|-------|---------|
| D01-IDEA | IDEA | 去除數字前綴 |
| D02-BRD | BRD | 去除數字前綴 |
| D03-PRD | PRD | 去除數字前綴 |
| D03.5-CONSTANTS | **（已移除）** | 合併進 EDD Pass-0 |
| D04-PDD | PDD | 去除數字前綴 |
| D05-VDD | VDD | 去除數字前綴 |
| D06-EDD | EDD | 去除數字前綴；升為 4-pass |
| D07-ARCH | ARCH | 去除數字前綴 |
| D07b-UML | UML | 去除數字前綴 |
| D08-API | API | 去除數字前綴 |
| D09-SCHEMA | SCHEMA | 去除數字前綴 |
| D10-FRONTEND | FRONTEND | 去除數字前綴 |
| D10b-AUDIO | AUDIO | 去除數字前綴 |
| D10c-ANIM | ANIM | 去除數字前綴 |
| **（新增）** | **ADMIN_IMPL** | Admin 後台實作規格，條件 has_admin_backend |
| D10d-CLIENT_IMPL | CLIENT_IMPL | 去除數字前綴 |
| D11-test-plan | test-plan | 去除數字前綴 |
| D12-BDD-server | BDD-server | 去除數字前綴 |
| D12b-BDD-client | BDD-client | 去除數字前綴 |
| D13-RTM | RTM | 去除數字前綴 |
| D14-runbook | runbook | 去除數字前綴 |
| D15-LOCAL_DEPLOY | LOCAL_DEPLOY | 去除數字前綴 |
| D16-ALIGN | ALIGN | 去除數字前綴 |
| D16-ALIGN-F | ALIGN-F | 去除數字前綴 |
| D16b-ALIGN-VERIFY | ALIGN-VERIFY | 去除數字前綴 |
| D17-CONTRACTS | CONTRACTS | 去除數字前綴 |
| D18-MOCK | MOCK | 去除數字前綴 |
| D20-PROTOTYPE | PROTOTYPE | 去除數字前綴 |
| D19-HTML | HTML | 去除數字前綴 |

---

## 三、執行分階（Phase Plan）

### Phase 1 — Pipeline 結構重組
**目標：** 建立新 pipeline.yml，確保所有 skill 能讀取

**修改/建立的檔案：**

#### A. `templates/pipeline.yml`（新建，取代 pipeline.json）
- 格式：YAML，含 comment 說明每個節點
- 移除 CONSTANTS 節點
- 新增 ADMIN_IMPL 節點（ANIM 後、CLIENT_IMPL 前）
- 所有 ID 去除數字前綴
- 新增欄位：`condition_admin: has_admin_backend`（用於 ADMIN_IMPL 節點）
- 節點結構範例：
  ```yaml
  steps:
    - id: IDEA
      type: IDEA
      layer: 需求層
      output: [docs/IDEA.md]
      multi_file: false
      condition: always
      handled_by: gendoc-auto
      commit_prefix: "docs(gendoc)[IDEA]"

    - id: EDD
      type: EDD
      layer: 設計層
      output: [docs/EDD.md]
      multi_file: false
      condition: always
      handled_by: gendoc-flow
      commit_prefix: "docs(gendoc)[EDD]"
      note: "EDD 採用四 pass 架構：Pass-0 提取 constants（輸出 constants.json），Pass-A 生成 §0-§8，Pass-B 生成 §4.5 UML，Pass-C 生成 §9-§21。"

    - id: ADMIN_IMPL
      type: ADMIN_IMPL
      layer: 設計層
      output: [docs/ADMIN_IMPL.md]
      multi_file: false
      condition: has_admin_backend
      handled_by: gendoc-flow
      commit_prefix: "docs(gendoc)[ADMIN_IMPL]"
      note: "Admin 後台實作規格（Vue3+ElementPlus+Vite 預設）：RBAC 架構、Component 規範、API 串接。上游：EDD + ARCH + API + SCHEMA。"
  ```

#### B. `templates/pipeline.json`（保留，標記 deprecated）
- 在 description 欄位加入警告：`"DEPRECATED: 請改用 pipeline.yml。此檔保留作向後相容，下版本將移除。"`

---

### Phase 2 — Skills 動態讀取 Pipeline

**目標：** gendoc-auto、gendoc-flow、gendoc-config 改從 pipeline.yml 動態讀取步驟清單

#### A. `skills/gendoc-auto/SKILL.md`
修改內容：
1. **Step 0：Session Config 讀取** 新增 `has_admin_backend` 問題：
   ```
   問：「此專案是否需要 Admin 後台？」
   選項：[1] 是（has_admin_backend=true，預設 Vue3+ElementPlus+Vite）
         [2] 否（has_admin_backend=false）
   寫入 .gendoc-state.json 的 has_admin_backend 欄位
   ```
2. **pipeline 讀取**：Step 讀取 pipeline.yml（優先）或 pipeline.json（fallback）
3. **ID 參照**：所有 IDEA/BRD/PRD... 參照改用新 ID

#### B. `skills/gendoc-flow/SKILL.md`
修改內容：
1. 步驟執行邏輯改為從 pipeline.yml 動態讀取 steps 清單
2. condition 評估：`has_admin_backend` 條件判斷
3. ADMIN_IMPL 步驟分派：呼叫對應 gen/review template

#### C. `skills/gendoc-config/SKILL.md`
修改內容：
1. **STEP 選單**：對應新 ID（IDEA / BRD / PRD / EDD / ... / ADMIN_IMPL / CLIENT_IMPL ...）
2. 移除 CONSTANTS 選項（已合併入 EDD）
3. 新增 ADMIN_IMPL 選項

---

### Phase 3 — EDD 四 Pass 架構 + Admin 欄位

**修改檔案：** `templates/EDD.gen.md`

修改內容：

#### A. 新增 Pass-0（Constants 提取）
在 Pass-A 之前插入：
```
Pass-0：業務數值提取（Constants Extraction）
- 輸入：docs/req/*, docs/PRD.md, docs/BRD.md
- 任務：掃描 PRD 中所有數字（倍率/閾值/SLO/RTP/rate-limit/timeout/retry 等）
- 輸出 1：docs/CONSTANTS.md（Markdown 格式，人類可讀）
- 輸出 2：docs/constants.json（JSON 格式，機器可讀，供下游 CI 驗證）
- 格式要求：每個常數必須有 name / value / unit / source（PRD 章節）/ note
```

#### B. EDD §3.3 新增 Admin 框架欄位
```
§3.3 技術決策
  _CLIENT_ENGINE: Cocos Creator | Unity WebGL | React | Vue | HTML5 | none
  _ADMIN_FRAMEWORK: Vue3+ElementPlus+Vite（預設）| 其他（需說明）| none
  
  若 has_admin_backend=true 且 _ADMIN_FRAMEWORK 未指定 → 預設填入 Vue3+ElementPlus+Vite
```

#### C. EDD §5.5 Admin RBAC 資料模型（條件性章節）
```
§5.5 Admin RBAC 資料模型（has_admin_backend=true 時必填）
  - 角色清單（Role）
  - 權限清單（Permission）
  - 角色-權限對應（RolePermission）
  - 使用者-角色對應（UserRole）
  - 稽核日誌（AuditLog）
  Mermaid erDiagram 格式輸出，供 SCHEMA.md §12 繼承
```

---

### Phase 4 — 建立 ADMIN_IMPL 三件套

**新建三個檔案：**

#### A. `templates/ADMIN_IMPL.md`（文件結構骨架）

章節結構：
```
§1  Admin Portal 概覽
§2  技術棧決策（_ADMIN_FRAMEWORK）
§3  目錄結構與 Monorepo 配置
§4  路由設計（vue-router，動態路由 + 角色守衛）
§5  RBAC 實作規格
    §5.1 角色定義（對應 EDD §5.5）
    §5.2 Permission Guard（組件級 + 路由級）
    §5.3 動態選單生成
§6  Layout 系統（Sidebar + Header + Breadcrumb）
§7  主要頁面規格
    §7.1 登入頁（含 token refresh 邏輯）
    §7.2 Dashboard（統計卡 + 圖表）
    §7.3 使用者管理（CRUD + 分頁）
    §7.4 角色管理（CRUD + 權限勾選）
    §7.5 稽核日誌（篩選 + 匯出）
    §7.x 業務功能頁（依 PRD 展開）
§8  API 串接規格（對應 API.md /admin/* 路由）
§9  狀態管理（Pinia Store 架構）
§10 Element Plus 組件使用規範
§11 Table + Pagination 通用組件
§12 Form + Validation 通用組件
§13 圖表整合（ECharts / Chart.js）
§14 國際化（i18n）配置
§15 效能優化（Lazy Loading + Bundle Split）
§16 部署配置（Vite build + 環境變數）
```

#### B. `templates/ADMIN_IMPL.gen.md`（AI 生成規則）

關鍵內容：
- Iron Law：生成前必讀 ADMIN_IMPL.md + EDD.md + API.md + SCHEMA.md
- 專家角色：Vue3 Admin Architect、RBAC Security Expert、Element Plus UI Specialist
- 上游文件鏈（必讀）：EDD（§3.3 _ADMIN_FRAMEWORK, §5.5 RBAC 模型）、ARCH、API（/admin/* 路由）、SCHEMA（RBAC 表結構）
- 上游文件鏈（選讀）：PRD（業務需求）、PDD（Product Design）、VDD（視覺設計）
- Engine 偵測：讀取 EDD §3.3 `_ADMIN_FRAMEWORK`，若為 none 則跳過本文件
- 條件偵測：has_admin_backend = true 才執行本步驟
- Quality Gate（生成後自我檢查）：
  - §5 RBAC 實作與 EDD §5.5 完全對應（無遺漏角色/權限）
  - §7 每個頁面規格有對應 API endpoint（來自 API.md）
  - §8 API 串接使用 constants.json 中的數值（timeout/retry 等）
  - 禁止含有 `{{PLACEHOLDER}}` 的最終輸出

#### C. `templates/ADMIN_IMPL.review.md`（審查標準）

關鍵審查項：
- CRITICAL：RBAC 規格是否覆蓋 EDD §5.5 所有角色（遺漏 = 安全漏洞）
- CRITICAL：每個 /admin/* API endpoint 是否有對應頁面規格
- HIGH：RBAC Permission Guard 是否有路由級和組件級雙重防護
- HIGH：稽核日誌頁面規格是否完整（可篩選 + 可匯出）
- HIGH：constants.json 數值是否被正確引用（timeout/retry 等）
- MEDIUM：Pinia Store 設計是否覆蓋所有主要業務狀態
- MEDIUM：Element Plus Table 是否有 loading/empty/error 三態規格

---

### Phase 5 — 更新既有 Templates（Admin 條件章節）

#### A. `templates/PRD.md` + `templates/PRD.gen.md`
新增條件章節（has_admin_backend=true 時展開）：
```
§X Admin 後台需求
  §X.1 Admin 使用者角色定義（角色名稱 + 職責 + 可存取功能）
  §X.2 RBAC 需求（哪些操作需要哪些權限）
  §X.3 稽核需求（哪些操作需要記錄稽核日誌）
  §X.4 Admin Portal 業務功能清單（對應前台功能的後台管理面）
```

#### B. `templates/PDD.md` + `templates/PDD.gen.md`
新增（has_admin_backend=true 時）：
```
§X Admin Portal 產品設計
  §X.1 Admin 使用情境（User Story 形式）
  §X.2 Admin Information Architecture（導覽結構）
  §X.3 Admin 核心頁面 wireframe 描述
```

#### C. `templates/VDD.md` + `templates/VDD.gen.md`
新增（has_admin_backend=true 時）：
```
§X Admin UI 設計規範
  §X.1 Admin 配色方案（通常與前台不同，偏 neutral/professional）
  §X.2 Admin Layout 規範（Sidebar width / Header height / Content padding）
  §X.3 Element Plus 主題客製化變數
  §X.4 Admin 表格/表單 設計規範
```

#### D. `templates/ARCH.md` + `templates/ARCH.gen.md`
新增（has_admin_backend=true 時）：
```
§3.2 C4 Container Diagram（修改）
  新增 Admin Portal container（Vue3+Vite SPA）
  新增 Admin → API Server 連線（/admin/* 路由）
  Auth Service 連線同時服務 Client App 和 Admin Portal

§X Admin 架構決策
  §X.1 Admin Portal 部署方式（獨立 container 或與 frontend 共 nginx）
  §X.2 Admin Auth 策略（共用 token service 或獨立 session）
  §X.3 Admin API 隔離策略（/admin/* 路由隔離 + RBAC middleware）
```

#### E. `templates/API.md` + `templates/API.gen.md`
新增（has_admin_backend=true 時）：
```
§X Admin API 規格
  §X.1 Admin Auth Endpoints（/admin/auth/login, /admin/auth/refresh）
  §X.2 User Management Endpoints（CRUD /admin/users/）
  §X.3 Role Management Endpoints（CRUD /admin/roles/）
  §X.4 Audit Log Endpoints（GET /admin/audit-logs/ + 篩選參數）
  §X.5 業務管理 Endpoints（依 PRD 展開）
  全部 Endpoints 需標記：所需權限（Permission）
```

#### F. `templates/FRONTEND.md` + `templates/FRONTEND.gen.md`
新增（has_admin_backend=true 時）：
```
§X Admin Frontend 架構補充
  注意：Admin Portal（Vue3+ElementPlus）是獨立前端應用，
  本節僅記錄與前台共用的部分（如 Auth Token 格式）。
  詳見 docs/ADMIN_IMPL.md。
```

#### G. `templates/CLIENT_IMPL.md` + `templates/CLIENT_IMPL.gen.md`
修改排除說明：
```
⚠️ 範圍說明：
本文件（CLIENT_IMPL）處理前台/遊戲客戶端實作：
  Cocos Creator / Unity WebGL / React / Vue SPA / HTML5

若 EDD §3.3 中 Vue 應用為 Admin 後台（_ADMIN_FRAMEWORK 已設定），
→ 請見 docs/ADMIN_IMPL.md，Admin Portal 不走本文件流程。
```

---

### Phase 6 — 品質層 Templates（admin 上游 + 章節）

#### A. `templates/test-plan.md` + `templates/test-plan.gen.md`
- 上游文件新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增測試章節：
  ```
  §X Admin 測試計劃
    §X.1 RBAC 測試矩陣（角色 × 功能 × 期望結果）
    §X.2 Admin UI 功能測試清單
    §X.3 Admin API 測試清單（對應 API.md /admin/* 路由）
    §X.4 稽核日誌正確性測試
    §X.5 Admin 效能測試（大量資料 Table 分頁）
  ```

#### B. `templates/BDD-client.gen.md`
- 上游文件新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增 Admin BDD scenarios：
  ```
  Feature: Admin RBAC Access Control
    Scenario: 超級管理員可存取所有頁面
    Scenario: 一般管理員無法存取角色管理頁
    Scenario: 未登入用戶被重導至登入頁
  
  Feature: Admin User Management
    Scenario: 成功建立新使用者
    Scenario: 編輯使用者角色
    Scenario: 停用使用者帳號
  ```

#### C. `templates/RTM.md` + `templates/RTM.gen.md`
- 上游文件新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增追蹤矩陣章節：
  ```
  §X Admin 需求追蹤矩陣
    PRD §X Admin 需求 → API.md /admin/* → ADMIN_IMPL.md §X → test-plan §X
    RBAC 需求 → EDD §5.5 → ADMIN_IMPL §5 → test-plan §X.1
  ```

---

### Phase 7 — 運維層 Templates（admin 上游 + 章節）

#### A. `templates/runbook.md` + `templates/runbook.gen.md`
- 上游文件新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增 Admin 運維章節：
  ```
  §X Admin 後台運維手冊
    §X.1 Admin 服務啟動/停止（Vite dev server / production build）
    §X.2 RBAC 管理程序（新增角色/調整權限的 SOP）
    §X.3 超級管理員緊急存取（emergency access 程序）
    §X.4 稽核日誌查詢指令（常用 SQL / API 查詢範例）
    §X.5 Admin 帳號管理（重置密碼/停用帳號 SOP）
    §X.6 Admin Session 管理（強制登出/清除 token）
  ```

#### B. `templates/LOCAL_DEPLOY.md` + `templates/LOCAL_DEPLOY.gen.md`
- 上游文件新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增 Admin 本地部署章節：
  ```
  §X Admin Portal 本地部署
    §X.1 Vite dev server 啟動（npm run dev:admin 或 docker compose admin）
    §X.2 Admin Ingress routing（nginx 配置：/admin/ → admin container）
    §X.3 Seed 初始管理員帳號（super-admin 種子資料）
    §X.4 RBAC 初始角色/權限種子資料
    §X.5 Admin 服務健康檢查
  ```

---

### Phase 8 — 特殊 Skills（admin 章節）

#### A. `skills/gendoc-gen-contracts/SKILL.md`
- 讀取上游新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增 Contract 輸出：
  ```
  docs/blueprint/contracts/admin-api.yaml（OpenAPI YAML，/admin/* 路由完整規格）
  docs/blueprint/contracts/rbac-seed.json（初始角色/權限種子資料）
  docs/blueprint/contracts/admin-seed.json（初始超級管理員帳號）
  ```
- 驗證：admin-api.yaml path 數量必須與 API.md /admin/* endpoint 數量對齊

#### B. `skills/gendoc-gen-prototype/SKILL.md`
- 讀取上游新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增 Admin Prototype 頁面：
  ```
  docs/pages/prototype/admin-login.html（Admin 登入頁）
  docs/pages/prototype/admin-dashboard.html（Dashboard 統計卡）
  docs/pages/prototype/admin-user-list.html（使用者管理列表）
  docs/pages/prototype/admin-role-management.html（角色管理）
  docs/pages/prototype/admin-audit-log.html（稽核日誌）
  ```

#### C. `skills/gendoc-gen-diagrams/SKILL.md`
- 讀取上游新增：`docs/ADMIN_IMPL.md`（has_admin_backend=true 時）
- 新增 Admin 相關圖（has_admin_backend=true 時條件生成）：
  ```
  docs/diagrams/admin-rbac-entity.md（RBAC 實體關係圖，Mermaid erDiagram）
  docs/diagrams/admin-login-sequence.md（Admin 登入 Sequence Diagram）
  docs/diagrams/admin-server-c4.md（Admin-Server C4 Component Diagram）
  ```

---

### Phase 9 — Deprecation

#### A. `templates/CONSTANTS.gen.md`
- 在檔案頂部加入 deprecated header：
  ```
  ---
  DEPRECATED: 此 template 已被合併至 EDD Pass-0。
  pipeline.yml 不再呼叫此步驟。
  保留作歷史參考，下版本將移除。
  ---
  ```

#### B. `templates/CONSTANTS.md`
- 同樣加入 deprecated header

---

## 四、各文件的累積上游鏈（更新後）

| 文件 | 必讀上游（更新後） |
|------|------------------|
| EDD | req/, IDEA, BRD, PRD → 自產 constants.json |
| ARCH | IDEA, BRD, PRD, PDD, VDD, EDD |
| API | IDEA, BRD, PRD, PDD, EDD, ARCH |
| SCHEMA | IDEA, BRD, PRD, PDD, EDD, ARCH, API |
| FRONTEND | IDEA, BRD, PRD, PDD, VDD, EDD, ARCH, API, SCHEMA |
| ADMIN_IMPL | EDD, ARCH, API, SCHEMA（PRD/PDD/VDD 選讀） |
| CLIENT_IMPL | EDD, ARCH, API, SCHEMA, FRONTEND, AUDIO, ANIM |
| test-plan | PRD, EDD, ARCH, API, SCHEMA, FRONTEND, ADMIN_IMPL*, AUDIO, ANIM |
| BDD-server | PRD, EDD, API, SCHEMA, CONSTANTS.json |
| BDD-client | PRD, PDD, EDD, API, FRONTEND, ADMIN_IMPL*, CONSTANTS.json |
| RTM | 所有設計層文件 + ADMIN_IMPL* + test-plan + features/ |
| runbook | EDD, ARCH, API, SCHEMA, ADMIN_IMPL*, FRONTEND, test-plan |
| LOCAL_DEPLOY | EDD, ARCH, API, SCHEMA, ADMIN_IMPL*, FRONTEND |
| CONTRACTS | EDD, ARCH, API, SCHEMA, ADMIN_IMPL* |
| PROTOTYPE | PRD, PDD, EDD, API, FRONTEND, ADMIN_IMPL* |

> `*` = 僅 has_admin_backend=true 時讀取

---

## 五、風險與注意事項

### 5.1 向後相容性
- pipeline.json 保留並標記 deprecated，確保舊版 skill 不會 break
- 各 skill 讀取 pipeline 時應先找 pipeline.yml，fallback 到 pipeline.json
- CONSTANTS.md 文件若已存在目標專案中，EDD Pass-0 跳過生成（不覆蓋）

### 5.2 has_admin_backend 的影響範圍
- 只有 gendoc-auto Step 0 詢問此問題（一次性）
- 所有條件章節應在對應 template 的 gen.md 中加入明確的 `if has_admin_backend` 偵測規則
- 此 flag 不影響 client_type 邏輯（可以同時有 client_type=web + has_admin_backend=true）

### 5.3 CONSTANTS 合併的注意事項
- EDD Pass-0 輸出的 constants.json 格式須與原 CONSTANTS.gen.md 輸出相同
- 下游所有引用 constants.json 的文件（BDD-server.gen.md、BDD-client.gen.md）無需修改（路徑不變）
- 若目標專案已有舊版 CONSTANTS.md，Pass-0 應讀取而非重新生成

### 5.4 實作優先順序建議
若資源有限，建議執行順序：
1. **必做**：Phase 1（pipeline.yml）+ Phase 2（skills 讀取更新）
2. **必做**：Phase 3（EDD 四 pass）+ Phase 4（ADMIN_IMPL 三件套）
3. **重要**：Phase 5 C/D/E（CLIENT_IMPL 排除 + ARCH/API admin 章節）
4. **重要**：Phase 7 A/B（runbook/LOCAL_DEPLOY admin 章節）
5. **完整**：Phase 5 A/B/F + Phase 6 + Phase 8（完整 admin 支援）
6. **最後**：Phase 9（deprecation 標記）

---

## 六、完成標準（Definition of Done）

- [ ] pipeline.yml 建立完成，包含所有 28（原）+ 1（ADMIN_IMPL）- 1（CONSTANTS）= 28 個節點
- [ ] gendoc-auto 新增 has_admin_backend 問題，寫入 state file
- [ ] EDD.gen.md 包含 Pass-0 常數提取邏輯
- [ ] ADMIN_IMPL 三件套建立完成（.md / .gen.md / .review.md）
- [ ] CLIENT_IMPL.gen.md 有明確 admin 排除說明
- [ ] 所有下游文件（RTM/runbook/LOCAL_DEPLOY/CONTRACTS/PROTOTYPE）上游鏈含 ADMIN_IMPL
- [ ] `templates/CONSTANTS.gen.md` 標記為 deprecated
- [ ] `/reviewtemplate ADMIN_IMPL` 通過（finding = 0 或 CRITICAL/HIGH = 0）

---

*計劃版本 v1.0 — 待 Review*
