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
    - docs/EDD.md          # §3.3 _ADMIN_FRAMEWORK 技術棧 + §5.5 RBAC 模型 + §3.1 角色
    - docs/ARCH.md         # C4 Container 圖 + Admin Portal 服務部署位置
    - docs/API.md          # /admin/* endpoints 清單 + 認證方案
    - docs/SCHEMA.md       # RBAC 相關 tables (Role, Permission, AdminUser, AuditLog)
  recommended:
    - docs/PRD.md          # Admin 使用情境 + 業務功能模組
    - docs/PDD.md          # Admin 產品設計 section
    - docs/VDD.md          # Admin UI 設計原則 + 色彩系統
    - docs/CONSTANTS.md    # Token 有效期、Rate Limit 等常數
output-paths:
  - docs/ADMIN_IMPL.md
quality-bar:
  - "§3 目錄結構完整，包含 admin/ 子目錄 + views/layout/store/utils"
  - "§4 路由表涵蓋所有 admin 功能頁面（不含 placeholder）"
  - "§5 RBAC 完整：Role/Permission 定義 + PermissionGuard 實作 + Token 管理"
  - "§7 頁面規格：login/dashboard/user-mgmt/role-mgmt/audit-log 全部有欄位或操作說明"
  - "§8 API 整合：baseURL、interceptor、所有 /admin/* endpoint 對應表"
  - "§9 三個 Pinia Store（authStore/permissionStore/userStore）有完整 state + actions"
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
    "ui_library": "Element Plus 2.x",
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

---

## Step 1：生成 §0 文件資訊

```markdown
| 項目         | 內容                                  |
|------------|---------------------------------------|
| DOC-ID     | ADMIN_IMPL-001                        |
| 版本        | 1.0.0                                 |
| 技術棧      | Vue3 + Element Plus + Vite（Admin Portal）|
| 觸發條件    | has_admin_backend=true                |
| 上游文件    | EDD §3.3 §5.5 + ARCH + API + SCHEMA   |
| 覆蓋範圍    | Admin Portal 完整實作規格             |
```

---

## Step 2：生成 §1 Admin Portal 定位

讀取 `docs/PRD.md` 的 Admin 使用情境段落（若存在），提取：
- Admin Portal 目標用戶（Super Admin, Operator, Auditor...）
- 核心功能模組清單（用戶管理、角色管理、業務管理、稽核日誌等）
- 後台設計核心原則

若 PRD 無明確 Admin section，依 EDD §3.1 角色定義推導出合理的 Admin 功能集。

---

## Step 3：生成 §2 技術棧決策

完整列出依賴版本表（不得使用 "latest" 或空版本）：

```markdown
| 類別         | 技術        | 版本   | 用途                          |
|------------|-----------|------|-----------------------------|
| Framework  | Vue 3     | 3.4+ | Composition API + `<script setup>` |
| UI Library | Element Plus | 2.7+ | 企業組件庫                  |
| Build      | Vite      | 5.x  | HMR + 生產 bundle             |
| State      | Pinia     | 2.x  | 模組化 Store                 |
| Router     | Vue Router| 4.x  | History 模式 + 動態路由       |
| HTTP       | Axios     | 1.x  | 攔截器 + 自動 token 注入     |
| ...        | ...       | ...  | ...                          |
```

---

## Step 4：生成 §3 目錄結構

基於技術棧生成完整的 admin/ 目錄樹，必須包含：

```
admin/
├── src/
│   ├── views/           # 頁面（login/dashboard/users/roles/audit/...）
│   ├── layout/          # HeaderBar + SidebarMenu + MainContent
│   ├── router/          # index.ts + guards.ts + routes.ts
│   ├── store/           # authStore / permissionStore / userStore
│   ├── api/             # 對應 API.md /admin/* 各模組
│   ├── components/      # 共用組件（SearchableTable / ConfirmDialog / ...）
│   ├── utils/           # permission.ts / request.ts / format.ts
│   ├── hooks/           # usePermission / usePagination / useTable
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

### 6.1 角色定義表
完整列出每個 Role 的中文名稱、英文 code、可操作 Permissions 清單。

### 6.2 Permission Guard 實作

```typescript
// utils/permission.ts
export function hasPermission(userPermissions: string[], required: string): boolean {
  return userPermissions.includes(required) || userPermissions.includes('*')
}

// 指令（v-permission）
export const permissionDirective = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    if (!hasPermission(store.permissions, value)) {
      el.parentNode?.removeChild(el)
    }
  }
}
```

### 6.3 Token 管理

從 CONSTANTS.md 讀取 Token 有效期常數（若不存在則使用合理預設：access=15min, refresh=7days）。

---

## Step 7：生成 §6 Layout 系統

生成完整的 Layout 結構說明：
- HeaderBar：用戶資訊 + 通知 + 登出
- SidebarMenu：動態路由 + 折疊功能 + 高亮當前路由
- BreadCrumb：根據路由自動生成
- Content 區域：max-width + padding 規範

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

---

## Step 9：生成 §8 API 整合

### 9.1 Axios 配置

```typescript
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})
// request interceptor: 自動注入 Authorization Bearer Token
// response interceptor: 401→重新導向 login；403→顯示無權限；500→統一 toast 錯誤
```

### 9.2 Admin Endpoint 對應表

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
- 關鍵頁面首屏時間目標（< 2s in 3G）

---

## Step 16：生成 §15 部署配置

### 16.1 Vite 生產配置

必須包含：
- `base: '/admin/'`（若部署在子路徑）
- `build.outDir: 'dist/admin'`
- `server.proxy` 配置（開發時代理 /admin/api → backend）

### 16.2 環境變數

必須包含（`.env.example` 格式）：
```
VITE_API_BASE_URL=https://api.example.com
VITE_ADMIN_BASE_PATH=/admin
```

### 16.3 Nginx 路由規則

```nginx
location /admin/ {
  root /var/www;
  try_files $uri $uri/ /admin/index.html;
}
location /admin/api/ {
  proxy_pass http://backend:8080/;
}
```

---

## Step 17：生成 §16 Self-Check Checklist

生成後必須對照以下清單確認，所有項目需明確通過（✅）才算完成：

```markdown
| # | 檢查項目                                    | 狀態 |
|---|-------------------------------------------|------|
| 1 | §3 目錄結構完整，含 views/store/router/api  | ✅/❌ |
| 2 | §4 路由表覆蓋所有頁面，含權限欄位          | ✅/❌ |
| 3 | §5 RBAC：Role+Permission 定義 + Guard 程式碼 | ✅/❌ |
| 4 | §7 頁面規格：必要頁面全部有欄位說明        | ✅/❌ |
| 5 | §8 /admin/* endpoint 對應表完整            | ✅/❌ |
| 6 | §9 三個 Pinia Store 有 state+actions       | ✅/❌ |
| 7 | §15 部署：env 變數 + Nginx 配置            | ✅/❌ |
| 8 | 全文無 {{PLACEHOLDER}} / TODO 空欄         | ✅/❌ |
```

若有 ❌，必須返回相應 Step 補完後再輸出。

---

## Quality Gate（生成完成後自我驗證）

```
✅ Pass-0 條件：has_admin_backend=true 已確認（否則整個 STEP 跳過）
✅ _ADMIN_FRAMEWORK 已從 EDD §3.3 讀取（或使用預設值 Vue3+ElementPlus+Vite）
✅ 技術棧版本表無 "latest" 或空版本
✅ 路由表：每個路由有 path + component + 權限 + 說明
✅ RBAC：Role 定義 + Permission Guard 程式碼 + Token 管理
✅ API 對應表：所有 /admin/* endpoint 均已列出
✅ Pinia：authStore + permissionStore + userStore 三個 Store 完整
✅ 部署：Nginx /admin/ try_files + env 變數清單
✅ Self-Check Checklist 全部通過（8/8）
```

---

## 完成後 Commit

```bash
git add docs/ADMIN_IMPL.md
git commit -m "docs(gendoc)[ADMIN_IMPL]: 生成 Admin 後台實作規格"
```
