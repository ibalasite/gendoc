---
doc-type: ADMIN_IMPL
role: gen
version: "1.0"
expert-roles:
  gen:
    - name: Vue3 Admin Architect
      scope: §0-§5 RBAC + 路由 + 目錄結構
    - name: Element Plus UI Specialist
      scope: §6-§12 Layout + 頁面規格 + 組件規範
    - name: DevOps & Performance Specialist
      scope: §13-§16 i18n + 效能 + 部署配置
upstream-docs:
  required:
    - path: docs/EDD.md
      sections: "§3.3 + §5.5 + §3.1"
      purpose: "§3.3：_ADMIN_FRAMEWORK 技術棧；§5.5：Admin RBAC 角色與 Permission 定義（優先使用）；§3.1（備用）：若 §5.5 無角色定義時，從系統角色章節推導業務角色，注意 §3.1 描述的是技術角色（如 backend-service），不得將技術角色誤認為 Admin 使用者角色。"
    - path: docs/ARCH.md
      sections: "Admin Portal 容器"
      purpose: "C4 Container 圖 + Admin Portal 服務部署位置"
    - path: docs/API.md
      sections: "/admin/* 章節"
      purpose: "/admin/* endpoints 清單 + 認證方案"
    - path: docs/SCHEMA.md
      sections: "RBAC 資料表章節"
      purpose: "Role, Permission, AdminUser, AuditLog 表結構"
    - path: docs/CONSTANTS.md
      sections: "全文"
      purpose: "Token 有效期、API Timeout、pageSize 等常數"
  recommended:
    - path: docs/PRD.md
      sections: "Admin 功能段落"
      purpose: "Admin 使用情境 + 業務功能模組"
    - path: docs/PDD.md
      sections: "Admin 產品設計"
      purpose: "Admin 產品設計 section"
    - path: docs/VDD.md
      sections: "設計原則章節"
      purpose: "Admin UI 設計原則 + 色彩系統"
output-paths:
  - docs/ADMIN_IMPL.md
quality-bar:
  - "§0 DOC-ID 已填入 PROJECT_SLUG + 日期（非靜態值），Admin技術棧欄位已從 EDD §3.3 讀取（非 placeholder）"
  - "§1 Admin Portal 概覽：系統定位非 placeholder，§1.3 角色表格已依 EDD §5.5-A 完整填入（無 {{role_name}} 殘留）"
  - "§2 技術棧版本表：所有依賴有明確版本號，無 latest 或空版本（允許 X.x 格式表示大版本鎖定，但不接受 latest 或空版本）"
  - "§3 目錄結構完整，包含 admin/ 子目錄 + views/layout/store/utils"
  - "§4 路由表涵蓋所有 admin 功能頁面（不含 placeholder）"
  - "§5 RBAC 完整：Role/Permission 定義 + PermissionGuard 實作 + Token 管理"
  - "§6.1 主 Layout 結構：ASCII 框線圖維持三區（Header / Sidebar / Content Area）；§6.1 文字說明另行描述 HeaderBar / SidebarMenu / BreadCrumb / Content 四個功能子項（BreadCrumb 作為 Content Area 的子項），無殘留 placeholder。"
  - "§7 頁面規格：login/dashboard/user-mgmt/role-mgmt/audit-log 全部有欄位或操作說明"
  - "§8 API 整合：baseURL、interceptor、所有 /admin/* endpoint 對應表"
  - "§9 三個 Pinia Store（authStore/permissionStore/userStore）有完整 state + actions"
  - "§10 Element Plus 規範：Table 三狀態 + Form 驗證規則 + ElMessageBox 確認範例均存在"
  - "§11 共用組件：SearchableTable 和 AuditLogDetail 均有 Props TypeScript 型別定義"
  - "§14 效能目標：bundle size 有具體數值（如 150KB gzipped），首屏時間有明確毫秒數（如 2000ms），全文無任何 {{N}} 格式的未替換佔位符。"
  - "§12 圖表整合：若 PRD 有圖表需求，圖表類型表格已填入具體名稱和更新策略；若無需求，已填入「本專案 Dashboard 無圖表需求，略過此節」，無殘留 placeholder。"
  - "§13 國際化：若專案多語言，語言代碼表格已填入完整語言清單；若單語言，已填入「本專案單語言，略過此節」，無殘留 {{其他語言}} placeholder。"
  - "§15 部署配置：env 變數 + Nginx /admin 路由規則"
  - "禁止保留任何 {{PLACEHOLDER}} 或 TODO 空欄"
condition: has_admin_backend
---

# ADMIN_IMPL.gen.md — Admin 後台實作規格生成規則

## Iron Law

**生成任何 ADMIN_IMPL.md 之前，必須先讀取 `ADMIN_IMPL.md`（結構骨架）和 `ADMIN_IMPL.gen.md`（本規則）。**

**條件觸發**：只有 `.gendoc-state.json` 中 `has_admin_backend=true` 才執行本步驟。若為 false，輸出訊息後跳過：
```
[Skip] ADMIN_IMPL：has_admin_backend=false，本專案無 Admin 後台需求，跳過。
```

---

## Step 0：條件與技術棧偵測

### Step 0-A：讀取 EDD §3.3

必須讀取 `docs/EDD.md` §3.3，提取：

```
_ADMIN_FRAMEWORK = EDD §3.3 中 _ADMIN_FRAMEWORK 欄位值
# 預設：Vue3 + Element Plus + Vite
# 若欄位為空或不存在 → 使用預設值
```

### Step 0-B：確認 ADMIN_IMPL 技術棧

```python
TECH_DEFAULTS = {
    "frontend_framework": "Vue 3 (Composition API)",
    "ui_library": "Element Plus 2.7+",
    "build_tool": "Vite 5.x",
    "state_management": "Pinia 2.x",
    "router": "Vue Router 4.x",
    "http_client": "Axios 1.x",
    "chart_library": "ECharts 5.x（可選，依 PRD 需求）",
    "i18n": "Vue I18n 9.x（若多語言需求）",
}
```

若 EDD `_ADMIN_FRAMEWORK` 有明確指定其他框架，以 EDD 為準；否則使用上述預設值。

### Step 0-C：讀取 RBAC 模型

從 `docs/EDD.md` §5.5 讀取：
- Admin 角色定義（Role 清單 + 每個 Role 的操作範圍）
- Permission 體系（module.action 格式）
- AuditLog 觸發場景

從 `docs/SCHEMA.md` 讀取：
- Role / Permission / RolePermission / AdminUser / AuditLog 表結構
- 若表不存在，則在 §5 中自行設計並說明「依 EDD §5.5 擴展 Schema」

### Step 0-D：非預設框架時的調整說明

當 EDD `_ADMIN_FRAMEWORK` 指定的框架**非** Vue3 + Element Plus 時，以下步驟需對應調整：

| Step | 預設（Vue3 + Element Plus） | 非預設框架時的調整方向 |
|------|-----------------------------|----------------------|
| Step 4 | 使用 `composables/` + `stores/` | 依目標框架慣用目錄命名（如 React 用 `hooks/` + `store/`） |
| Step 5 | Vue Router 4.x 路由守衛 | 替換為目標框架的路由解決方案（如 React Router 6.x、Next.js App Router） |
| Step 6.2 | `composables/usePermission.ts`（Vue Composition API 風格） | 依目標框架調整（如 React 用 `hooks/usePermission.ts`） |
| Step 11 | Element Plus 組件規範（el-table / el-form / ElMessageBox） | 替換為目標 UI 庫對應組件（如 Ant Design / MUI / Naive UI）及其使用慣例 |
| Step 12 | SearchableTable 以 Element Plus el-table 為基礎 | 包裝目標框架對應的 Table 組件 |

> 非預設框架時，TECH_DEFAULTS 中所有 Element Plus 特定內容均需替換，但 RBAC 模型、路由守衛邏輯、Token 管理策略保持不變。

### Step 0-E：上游一致性驗證

在開始生成前，執行以下衝突偵測，任一衝突需停止並告知用戶：

**場景 1：技術棧衝突**  
若 EDD `_ADMIN_FRAMEWORK` 指定的框架與 ARCH.md 中 Admin Portal 容器描述不一致（例如 EDD 說 Vue3，ARCH.md 說 React），輸出警告：
```
[Conflict] ADMIN_IMPL 技術棧衝突：EDD §3.3 = {EDD值}，ARCH.md Admin 容器 = {ARCH值}。
請先對齊兩份文件後再生成。
```

**場景 2：RBAC 角色衝突**  
若 EDD §5.5 定義的 Role 清單與 SCHEMA.md Role 表的 `code` 欄位值不完全一致（有遺漏或命名差異），輸出警告：
```
[Conflict] RBAC Role 不一致：EDD 定義了 {N} 個 Role，SCHEMA Role 表有 {M} 個 code。
差異：{列出差異項}。建議先修正 SCHEMA 或 EDD 後再生成。
```

**場景 3：API Endpoint 缺失**  
若 API.md 中 `/admin/*` 路徑數量少於 EDD §5.5 Admin 功能模組數量（每個模組至少需要 1 個 CRUD endpoint），輸出警告：
```
[Conflict] API endpoint 不足：API.md /admin/* 共 {N} 個路徑，但 EDD 定義了 {M} 個 Admin 功能模組。
可能遺漏：{列出未對應的模組}。
```

---

## Step 1：生成 §0 文件資訊

依骨架 §0 欄位結構，生成七列表格（欄名為「欄位｜說明」）：

```markdown
| 欄位 | 說明 |
|------|------|
| DOC-ID | ADMIN-`{PROJECT_SLUG}`-`{YYYYMMDD}` |
| Admin 技術棧 | `{_ADMIN_FRAMEWORK}`（來自 EDD §3.3） |
| 上游 EDD | [EDD.md](EDD.md) §3.3 + §5.5-A |
| 上游 API | [API.md](API.md) /admin/* 章節 |
| 上游 SCHEMA | [SCHEMA.md](SCHEMA.md) RBAC 資料表章節 |
| 上游 ARCH | [ARCH.md](ARCH.md) Admin Portal 容器（部署位置 + 技術棧） |
| 上游 CONSTANTS | [CONSTANTS.md](CONSTANTS.md) Token TTL + API Timeout + pageSize 等常數 |
```

> **注意**：DOC-ID 格式為 `ADMIN-{PROJECT_SLUG}-{YYYYMMDD}`，其中 PROJECT_SLUG 和 YYYYMMDD 須替換為實際值（非靜態字串 `ADMIN_IMPL-001`）。Admin 技術棧從 Step 0-A 讀取的 `_ADMIN_FRAMEWORK` 填入。

---

## Step 2：生成 §1 Admin Portal 概覽

讀取 `docs/PRD.md` 的 Admin 使用情境段落（若存在），提取：
- Admin Portal 目標用戶（Super Admin, Operator, Auditor...）
- 核心功能模組清單（用戶管理、角色管理、業務管理、稽核日誌等）
- 後台設計核心原則

Admin 業務角色優先從 EDD §5.5 讀取。若 PRD 無明確 Admin section，且 EDD §5.5 亦無角色定義，方可依 EDD §3.1 推導，但需注意 EDD §3.1 描述的是技術角色（如 backend-service、worker），**不得**將技術角色誤認為 Admin 使用者角色（如 super_admin、operator）。

---

## Step 3：生成 §2 技術棧決策

### §2.1 框架選型表（3 欄格式）

§2.1 需維持骨架的 3 欄格式（技術 / 選型 / 決策理由），依下列骨架格式填入，不得使用 4 欄或其他欄位佈局：

```markdown
| 技術 | 選型 | 決策理由 |
|------|------|---------|
| 前端框架 | Vue 3.4+ | Composition API + `<script setup>`，與 Element Plus 2.x 完整相容 |
| UI Component | Element Plus 2.7+ | 企業組件庫，提供完整 Admin 所需的 Table / Form / Dialog 組件 |
| Build Tool | Vite 5.x | HMR 快速 + 生產 bundle 優化 |
| 狀態管理 | Pinia 2.x | 模組化 Store，型別友善 |
| 路由 | Vue Router 4.x | History 模式 + 動態路由 + 路由守衛 |
| HTTP Client | Axios 1.x | 攔截器 + 自動 token 注入 |
| ...  | ...  | ... |
```

> **格式說明**：§2.1 固定為「技術 / 選型 / 決策理由」3 欄，與骨架一致。決策理由欄必須填入具體理由（非 `{{理由}}` placeholder）。

### §2.2 依賴版本清單

完整列出 package.json 依賴版本（不得使用 "latest" 或空版本）：

---

## Step 4：生成 §3 目錄結構

基於技術棧生成完整的 admin/ 目錄樹，必須包含：

```
admin/
├── src/
│   ├── views/           # 頁面（login/dashboard/users/roles/audit/...）
│   ├── layouts/         # AdminLayout.vue（HeaderBar + SidebarMenu + MainContent）
│   ├── router/          # index.ts + guards.ts + routes.ts
│   ├── stores/          # authStore / permissionStore / userStore（Pinia stores）
│   ├── api/             # 對應 API.md /admin/* 各模組
│   ├── components/      # 共用組件（SearchableTable / ConfirmDialog / ...）
│   ├── composables/     # usePermission / usePagination / useTable（Vue Composition API）
│   ├── utils/           # request.ts / format.ts（工具函式）
│   ├── styles/          # variables.scss / global.scss
│   └── types/           # 與 API response 對應的 TypeScript types
├── public/
├── vite.config.ts
├── tsconfig.json
└── package.json
```

每個資料夾附一行說明。

---

## Step 5：生成 §4 路由設計

依 PRD Admin 功能模組生成路由表，必須包含：

| 路由路徑 | 組件 | 權限 | 說明 |
|---------|------|------|------|
| /admin/login | Login.vue | 無需驗證 | 登入頁 |
| /admin/dashboard | Dashboard.vue | admin:view | 控制台 |
| /admin/users | UserList.vue | user:list | 用戶管理 |
| ... | ... | ... | ... |

必須包含：
- 路由守衛邏輯（JWT 驗證 + Permission 驗證流程）
- 動態側邊欄生成邏輯（根據用戶 Role 過濾路由）
- 404 + 403 頁面路由

---

## Step 6：生成 §5 RBAC 實作

依 EDD §5.5 和 SCHEMA 的 Role/Permission 表生成：

### Step 6.A：生成骨架 §5.1
完整列出每個 Role 的中文名稱、英文 code、可操作 Permissions 清單。

### Step 6.B：生成骨架 §5.2 Permission Guard 實作

```typescript
// composables/usePermission.ts（Vue Composition API 慣用風格，與骨架 §5.2 一致）
export function usePermission() {
  const permStore = usePermissionStore()

  const hasPermission = (permission: string): boolean => {
    return permStore.permissions.includes(permission) || permStore.permissions.includes('*')
  }

  return { hasPermission }
}

// 指令（v-permission），掛載在 main.ts
export const permissionDirective = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    const permStore = usePermissionStore()
    if (!permStore.permissions.includes(value) && !permStore.permissions.includes('*')) {
      el.parentNode?.removeChild(el)
    }
  }
}
```

### Step 6.C：生成骨架 §5.3 動態選單策略

依據 PRD.md 或 EDD §5.5 判斷 Admin 角色結構，選擇 §5.3 的選單生成方式：

- **client-filtered（首選）**：Admin 角色定義固定（Role 清單在部署時確定，不動態新增），前端依用戶 Permission 清單過濾靜態路由配置。選擇條件：EDD §5.5-A 角色數量固定，無需後端動態下發選單。
- **server-driven**：Admin 角色可由後台動態配置（如多租戶、自定義角色），選單結構需從 API 取回。選擇條件：PRD 要求支援動態角色或多層級組織結構。

**填入 §5.3 的方式**：
1. 確認選擇值：`server-driven` 或 `client-filtered`
2. 填入選擇理由（一句話，說明依據）
3. 若選 `server-driven`，確認 §8 對應表中存在 `GET /admin/menu`（或同功能端點），若缺失須補充

### Step 6.D：生成骨架 §5.4 Token 管理

從 CONSTANTS.md 讀取 Token 有效期常數（若不存在則使用合理預設：access=15min, refresh=7days）。

---

## Step 7：生成 §6 Layout 系統

§6.1 必須包含 ASCII 或 Markdown 框線圖，**維持三區結構**（Header / Sidebar / Content Area）的視覺佈局，格式參考骨架 §6.1。**不得**在 ASCII 圖中強行新增第四個視覺區塊；BreadCrumb 屬於 Content Area 的子元素，在 ASCII 圖中以 Content Area 的內部標示體現即可。

接著，**在 §6.1 的文字說明部分**（ASCII 圖下方）對以下四個功能子項分別提供具體規格說明：
- HeaderBar：用戶資訊 + 通知 + 登出
- SidebarMenu：動態路由 + 折疊功能 + 高亮當前路由
- BreadCrumb：根據路由自動生成（Content Area 子元素）
- Content 區域：max-width + padding 規範

§6.2 Sidebar 規格：記錄展開寬度（預設 260px）/ 收合寬度（64px）/ 收合後行為（icon + Tooltip 顯示選單名稱）/ 選中樣式（從 VDD 或 PDD 讀取色彩方案；若無，使用預設 accent 色左邊框 + 淡背景）。

---

## Step 8：生成 §7 頁面規格

對每個 Admin 功能頁面，必須列出：
- 頁面用途（一句話）
- 主要元素（表格欄位 / 表單欄位 / 動作按鈕）
- 交互規則（如：刪除需二次確認、表格支持排序/篩選）
- 所需 API endpoints（對應 API.md）
- 所需 Permission（對應 §5 RBAC）

**必須涵蓋的頁面：**
- 登入頁
- 控制台（Dashboard 統計指標）
- 用戶管理（列表 + 新增 + 編輯 + 停用）
- 角色管理（角色 CRUD + 權限分配）
- 稽核日誌（列表 + 詳情 + 導出）
- （依 PRD 業務功能補充其他頁面）

**§7.2 Dashboard KPI Cards 與圖表填充規則（防止 placeholder 殘留）：**

掃描 PRD.md 的 Admin 統計/監控需求段落，依序填入：
1. **統計卡（KPI Cards）**：列出每張卡片的名稱、對應 `GET /admin/stats/*` endpoint（若端點在 API.md 有定義則引用，否則依 REST 命名設計）、更新策略（輪詢間隔 / 手動刷新按鈕 / 頁面載入時）。每個統計卡需有具體名稱（如「今日新增用戶數」「當前在線人數」），不得保留 `{{指標名}}` placeholder。
2. **圖表**：依 PRD 中 Admin 圖表需求填入圖表名稱和類型（折線 / 柱狀 / 圓餅）。若 PRD 無明確圖表需求，於圖表區塊填入「本專案 Dashboard 無圖表需求，略過此欄」。
3. 若 PRD 無 Admin 統計需求，整個 §7.2 統計卡表格填入「本專案 Dashboard 無 KPI 指標需求，略過此節」。

**§7.x 業務功能頁生成規則：**

掃描 PRD.md 的 Admin 功能模組段落，對每個業務功能頁面，依序提取並填入：
1. **路徑**：`/admin/{{resource}}`（依 PRD 命名決定）
2. **頁面用途**：一句話說明此頁管理何種業務資源
3. **列表欄位**：從 PRD 和 SCHEMA.md 提取主要顯示欄位（至少 3 個，排除密碼類敏感欄位）
4. **操作按鈕**：新增 / 編輯 / 刪除 / 狀態切換（標注每個按鈕所需的 Permission）
5. **表單欄位**：新增/編輯 Dialog 的輸入欄位（欄位名稱、類型、是否必填）
6. **所需 API endpoints**：對應 API.md 中的 `/admin/{{resource}}` CRUD 路徑
7. **所需 Permission**：對應 §5 RBAC 的 `{{resource}}:list / create / update / delete`

若 PRD 無 Admin 業務功能頁，於 §7.x 節標注「本專案 Admin 無額外業務功能頁，略過此節」。

---

## Step 9：生成 §8 API 整合

### Step 9.A：Axios 配置

```typescript
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: ADMIN_API_TIMEOUT_MS, // 來自 CONSTANTS.md，預設 10000ms
})
// request interceptor: 自動注入 Authorization Bearer Token
// response interceptor: 401→重新導向 login；403→顯示無權限；500→統一 toast 錯誤
```

> **CONSTANTS.md 讀取指引**：`timeout` 值應從 `docs/CONSTANTS.md` 讀取 `ADMIN_API_TIMEOUT_MS` 常數（若存在）。若 CONSTANTS.md 無此欄位，使用預設值 `10000`（10 秒），並在生成的 §8.1 程式碼中以行內註解說明來源（如 `// ADMIN_API_TIMEOUT_MS，來自 CONSTANTS.md，預設 10000ms`）。生成的程式碼中，`ADMIN_API_TIMEOUT_MS` 應以 `const ADMIN_API_TIMEOUT_MS = {值} // 來自 CONSTANTS.md` 的形式在 `api/http.ts` 頂部宣告，不得直接使用未宣告的識別符。

### Step 9.B：Admin Endpoint 對應表

掃描 `docs/API.md` 所有 `/admin/*` 路徑，生成對應表：

| 功能 | Method | Path | 所需 Permission | 對應頁面 |
|------|--------|------|----------------|---------|
| ... | ... | ... | ... | ... |

若 API.md 無 /admin/* 端點，輸出警告並設計合理的 RESTful admin endpoints。

---

## Step 10：生成 §9 Pinia Store

每個 Store 必須包含：
- state 型別定義（TypeScript interface）
- getters（計算屬性）
- actions（含 async API 呼叫 + error handling）

**必須生成：**
- `authStore`：token / adminUser / login() / logout() / refreshToken()
- `permissionStore`：permissions / menuTree / loadPermissions() / hasPermission()
- `userStore`：userList / totalCount / fetchUsers() / updateUser() / deleteUser()

> **authStore Token 存儲方式必須與 §5.4 一致（重要）：**
> - 若 §5.4 選擇 **HttpOnly Cookie**：`authStore` 不應設置 `accessToken` ref 用於存放 token 字串；`isAuthenticated` 可依後端返回的用戶資訊判斷，不依賴 token 字串是否存在；`refreshToken()` 透過呼叫刷新端點完成，Cookie 由後端自動更新（瀏覽器自動附帶）。
> - 若 §5.4 選擇 **Memory**：`accessToken` 存於 ref 中，頁面刷新後清空；需在 `main.ts` 初始化時呼叫 silent refresh（透過 refresh endpoint 恢復 token）或直接導向登入頁；在 §9.2 代碼範例中加入 silent refresh 策略說明。
>
> 生成 §9.2 程式碼時，依 §5.4 的選擇動態調整 `accessToken` ref 的使用方式，確保兩節保持一致，不得出現 §5.4 選 HttpOnly Cookie 但 §9.2 仍有 `accessToken.value = res.access_token` 的矛盾。

---

## Step 11：生成 §10 Element Plus 使用規範

必須包含：
- Table 三狀態規範（loading / empty / data）
- Form 驗證規則（必填、格式、長度限制）
- 危險操作二次確認（ElMessageBox）
- 全局 message 提示（操作成功/失敗標準格式）
- Pagination 統一配置

---

## Step 12：生成 §11 共用組件

必須設計：
- `SearchableTable`：整合 Table + Pagination + 搜尋欄 + 操作按鈕的複合組件
- `AuditLogDetail`：稽核日誌詳情抽屜組件

每個組件需提供：Props 定義 + 使用範例（code block）

---

## Step 13：生成 §12 圖表整合（可選）

§12 的圖表初始化範例必須涵蓋 §7.2 中所有已定義的圖表類型；若 §7.2 標注為「本專案 Dashboard 無圖表需求，略過此欄」，§12 同樣標注「本專案 Dashboard 無圖表需求，略過此節」。

若 PRD Dashboard 需要數據圖表：
- ECharts 5.x 按需引入配置
- 常用圖表類型（折線圖/柱狀圖/餅圖）的初始化範例
- 響應式尺寸配置

若無圖表需求，標注「本專案 Dashboard 無圖表需求，略過此節」。

---

## Step 14：生成 §13 i18n 配置

若專案需多語言（從 PRD 判斷）：
- Vue I18n 9.x 配置
- zh-TW / en-US locale 結構
- 組件中使用範例

若無多語言需求，標注「本專案單語言，略過此節」。

---

## Step 15：生成 §14 效能

必須明確：
- Bundle size 目標（< 150KB gzipped，Element Plus 按需引入）
- 路由懶加載配置：
  ```typescript
  { path: '/admin/users', component: () => import('@/views/UserList.vue') }
  ```
- Vite bundle 分析命令：`npm run build -- --report`
- 關鍵頁面首屏時間目標：從 CONSTANTS.md 讀取 ADMIN_FCP_TARGET_MS 常數（若存在）；若 CONSTANTS.md 無此欄位，使用預設值 2000（2 秒），並在生成的 §14 中以行內註解說明來源（如 `// 首屏目標：< 2000ms in 3G，預設值`）

---

## Step 16：生成 §15 部署配置

### Step 16.A：Vite 生產配置

必須包含：
- `base: '/admin/'`（若部署在子路徑）
- `build.outDir: 'dist/admin'`
- `build.rollupOptions.output.manualChunks` vendor 切割設定（如 vendor-vue / vendor-element）
- `server.proxy` 配置（開發時代理 /api → backend）

### Step 16.B：環境變數

依骨架 §15.2 格式，生成三欄表格（變數名 | Development 值 | Production 值），列出 VITE_API_BASE_URL 和 VITE_ADMIN_PATH，Development 填 localhost 值，Production 填對應的生產值或說明：

| 變數 | Development | Production |
|------|-------------|-----------|
| `VITE_API_BASE_URL` | `http://localhost:{PORT}/api` | `/api`（Nginx 反代） |
| `VITE_ADMIN_PATH` | `/admin` | `/admin` |

### Step 16.C：Nginx 路由規則

```nginx
location /admin/ {
  root /usr/share/nginx/html;
  try_files $uri $uri/ /admin/index.html;
}
location /api/admin/ {
  proxy_pass http://backend:{{PORT}}/api/admin/;
  proxy_set_header Authorization $http_authorization;
  proxy_set_header Host $host;
}
```

> **注意**：API proxy 路徑須與 ARCH.md 中 Admin Portal → Backend 的連線路徑一致，如有差異以 ARCH.md 為準。

---

## Step 17：生成 §16 Self-Check Checklist

生成後必須對照以下清單確認，所有項目需明確通過（✅）才算完成：

> **分層說明**：Step 17 為生成時自查（AI 執行），§16 為交付驗收自查（開發者執行），兩者分層定義不同職責。Step 17 重點驗證生成完整性，§16 重點驗證可交付性。

```markdown
| # | 檢查項目                                    | 狀態 |
|---|-------------------------------------------|------|
| 1 | §3 目錄結構完整，含 views/store/router/api  | ✅/❌ |
| 2 | §4 路由表覆蓋所有頁面，含權限欄位          | ✅/❌ |
| 3 | §5 RBAC：Role+Permission 定義 + Guard 程式碼 | ✅/❌ |
| 4 | §5.2 Permission Guard：hasPermission() 實作 + routes/buttons 對應說明 | ✅/❌ |
| 5 | §7 頁面規格：必要頁面全部有欄位說明        | ✅/❌ |
| 6 | §8 Axios 配置有 baseURL + request interceptor（Token 注入）+ response interceptor（401/403 處理）說明 | ✅/❌ |
| 7 | §8 /admin/* endpoint 對應表完整            | ✅/❌ |
| 8 | §9 三個 Pinia Store 有 state+actions       | ✅/❌ |
| 9a | §15.1 Vite Build：base='/admin/'、outDir 已填入、manualChunks vendor 切割已設定、server.proxy 代理 /api 已設定（非 placeholder） | ✅/❌ |
| 9b | §15.2/§15.3 環境變數 + Nginx：VITE_API_BASE_URL 已填入；Nginx /admin/ try_files 已設定 | ✅/❌ |
| 10 | 全文無 {{PLACEHOLDER}} / TODO 空欄        | ✅/❌ |
| 11 | §1 Admin Portal 概覽：系統定位 + 使用者角色已依 EDD §5.5-A 填入，無 placeholder | ✅/❌ |
| 12 | §6.1 主 Layout 結構：ASCII 框線圖維持三區（Header / Sidebar / Content Area）；§6.1 文字說明涵蓋 HeaderBar / SidebarMenu / BreadCrumb / Content 四個功能子項（BreadCrumb 為 Content Area 子元素），無 placeholder | ✅/❌ |
| 13 | §5.1 Permission 清單與 API.md /admin/* endpoint 一對一對應 | ✅/❌ |
```

若有 ❌，必須返回相應 Step 補完後再輸出。

---

## Quality Gate（生成完成後自我驗證）

```
✅ Pass-0 條件：has_admin_backend=true 已確認（否則整個 STEP 跳過）
✅ _ADMIN_FRAMEWORK 已從 EDD §3.3 讀取（或使用預設值 Vue3+ElementPlus+Vite）
✅ 技術棧版本表無 "latest" 或空版本
✅ §1 Admin Portal 概覽：系統定位 + 使用者角色已依 EDD §5.5-A 填入，無 placeholder
✅ 路由表：每個路由有 path + component + 權限 + 說明
✅ RBAC：Role 定義 + Permission Guard 程式碼 + Token 管理
✅ §6.1 主 Layout 結構：ASCII 框線圖維持三區（Header / Sidebar / Content Area）；§6.1 文字說明部分涵蓋 HeaderBar / SidebarMenu / BreadCrumb / Content 四個功能子項（BreadCrumb 為 Content Area 子元素），均無 placeholder
✅ API 對應表：所有 /admin/* endpoint 均已列出
✅ Pinia：authStore + permissionStore + userStore 三個 Store 完整
✅ 部署：Nginx /admin/ try_files + env 變數清單 + Vite build base/outDir/manualChunks 已設定 + server.proxy /api 代理已設定
✅ §12 圖表整合：若 PRD 有圖表需求，圖表類型表格已填入具體名稱和更新策略；若無需求，已填入「本專案 Dashboard 無圖表需求，略過此節」，無殘留 placeholder
✅ §13 國際化：若專案多語言，語言代碼表格已填入完整語言清單；若單語言，已填入「本專案單語言，略過此節」，無殘留 {{其他語言}} placeholder
✅ §14 效能目標：bundle size 有具體數值（< 150KB gzipped）+ 首屏時間（< 2s）+ 無殘留 {{N}} placeholder
✅ Self-Check Checklist 全部通過（14/14）（Step 17 = AI 生成時自查（14 項，#9 拆分為 9a/9b）；骨架 §16 = 開發者交付前驗收自查（13 項））
```

---

## 完成後 Commit

```bash
git add docs/ADMIN_IMPL.md
git commit -m "docs(gendoc)[ADMIN_IMPL]: 生成 Admin 後台實作規格"
```
