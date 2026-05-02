---
doc-type: ADMIN_IMPL
version: 1.0.0
condition: has_admin_backend
---

# Admin Portal 實作規格書

## §0 文件資訊

| 欄位 | 說明 |
|------|------|
| DOC-ID | ADMIN-`{{PROJECT_SLUG}}`-`{{YYYYMMDD}}` |
| Admin 技術棧 | `{{_ADMIN_FRAMEWORK}}`（來自 EDD §3.3） |
| 上游 EDD | [EDD.md](EDD.md) §3.3 + §5.5-A |
| 上游 API | [API.md](API.md) /admin/* 章節 |
| 上游 SCHEMA | [SCHEMA.md](SCHEMA.md) RBAC 資料表章節 |
| 上游 ARCH | [ARCH.md](ARCH.md) Admin Portal 容器（部署位置 + 技術棧） |
| 上游 CONSTANTS | [CONSTANTS.md](CONSTANTS.md) Token TTL + API Timeout + pageSize 等常數 |

---

## §1 Admin Portal 概覽

### §1.1 系統定位

`{{Admin Portal 的業務定位：給誰用、管理什麼、解決什麼運維問題}}`

### §1.2 設計原則

- **安全第一**：RBAC 最小權限原則；所有操作留稽核日誌
- **操作效率**：批量操作 + 快捷鍵 + 智慧搜尋
- **資料一致性**：與主系統同一資料庫；不建立另一套資料快取
- **可審計性**：所有 CUD 操作必須記錄至 AuditLog

### §1.3 使用者角色（來自 EDD §5.5-A）

| 角色 | 說明 | 可存取功能 |
|------|------|-----------|
| `{{role_name}}` | `{{description}}` | `{{capabilities}}` |

---

## §2 技術棧決策

### §2.1 框架選型

| 技術 | 選型 | 決策理由 |
|------|------|---------|
| 前端框架 | `{{e.g. Vue 3.4+}}` | `{{理由}}` |
| UI Component | `{{e.g. Element Plus 2.x}}` | `{{理由}}` |
| Build Tool | `{{e.g. Vite 5.x}}` | `{{理由}}` |
| 狀態管理 | `{{e.g. Pinia 2.x}}` | `{{理由}}` |
| 路由 | `{{e.g. Vue Router 4.x}}` | `{{理由}}` |
| HTTP Client | `{{e.g. axios 1.x}}` | `{{理由}}` |
| 圖表 | `{{e.g. ECharts 5.x / Chart.js}}` | `{{理由}}` |
| 國際化 | `{{e.g. vue-i18n 9.x}}` | `{{理由}}` |

### §2.2 依賴版本清單

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "element-plus": "^2.7.0",
    "vue-router": "^4.x.x",
    "pinia": "^2.x.x",
    "axios": "^1.x.x",
    "echarts": "^5.x.x",
    "vue-i18n": "^9.x.x"
  },
  "devDependencies": {
    "vite": "^5.x.x",
    "@vitejs/plugin-vue": "^5.x.x",
    "typescript": "^5.x.x"
  }
}
```

---

## §3 目錄結構

```
admin/                          ← Admin Portal 根目錄
├── src/
│   ├── api/                    ← API 呼叫封裝（對應 API.md /admin/* 路由）
│   │   ├── auth.ts
│   │   ├── users.ts
│   │   ├── roles.ts
│   │   ├── audit-log.ts
│   │   └── {{business}}.ts     ← 業務相關 API
│   ├── components/
│   │   ├── common/             ← 通用組件（Table/Form/Search）
│   │   └── business/           ← 業務組件
│   ├── composables/            ← 可重用邏輯（useTable, usePagination, usePermission）
│   ├── layouts/
│   │   └── AdminLayout.vue     ← Sidebar + Header + Content 主佈局
│   ├── router/
│   │   ├── index.ts            ← 路由定義
│   │   └── guards.ts           ← 路由守衛（RBAC 驗證）
│   ├── stores/                 ← Pinia stores
│   │   ├── auth.ts
│   │   ├── permission.ts
│   │   └── user.ts
│   ├── types/                  ← TypeScript 型別定義
│   ├── utils/                  ← 工具函式
│   └── views/
│       ├── auth/               ← 登入頁
│       ├── dashboard/          ← 首頁 Dashboard
│       ├── user-management/    ← 使用者管理
│       ├── role-management/    ← 角色管理
│       ├── audit-log/          ← 稽核日誌
│       └── {{business}}/       ← 業務功能頁
├── public/
├── .env.development
├── .env.production
├── vite.config.ts
└── package.json
```

---

## §4 路由設計

### §4.1 路由清單

| 路徑 | 組件 | 需求權限 | 說明 |
|------|------|---------|------|
| `/admin/login` | `LoginView` | 公開 | Admin 登入頁 |
| `/admin/dashboard` | `DashboardView` | `dashboard:view` | 首頁儀表板 |
| `/admin/users` | `UserListView` | `user:list` | 使用者列表 |
| `/admin/users/:id` | `UserDetailView` | `user:view` | 使用者詳情 |
| `/admin/roles` | `RoleListView` | `role:list` | 角色管理 |
| `/admin/audit-log` | `AuditLogView` | `audit_log:view` | 稽核日誌 |
| `/admin/{{resource}}` | `{{View}}` | `{{permission}}` | `{{說明}}` |

### §4.2 動態路由守衛

```typescript
// router/guards.ts
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const permStore = usePermissionStore()
  
  // 公開頁面直接放行
  if (to.meta.public) return next()
  
  // 未登入 → 重導登入頁
  if (!authStore.isAuthenticated) return next('/admin/login')
  
  // 驗證 Permission
  const required = to.meta.permission as string
  if (required && !permStore.hasPermission(required)) {
    return next('/admin/403')
  }
  
  next()
})
```

### §4.3 動態側邊欄生成規則

側邊欄依當前使用者的 Permission 動態過濾，無權限的選單項目不顯示（非僅 disabled）。

---

## §5 RBAC 實作規格

### §5.1 角色定義（對應 EDD §5.5-A）

| 角色 key | 顯示名稱 | 是否系統角色 | 預設 Permission |
|---------|---------|-----------|----------------|
| `super_admin` | 超級管理員 | ✅ 是 | 全部 |
| `{{role}}` | `{{name}}` | `{{yes/no}}` | `{{permissions}}` |

### §5.2 Permission Guard 實作

**路由層**（見 §4.2）+ **組件層**：

```typescript
// composables/usePermission.ts
export function usePermission() {
  const permStore = usePermissionStore()
  
  const hasPermission = (permission: string) => {
    return permStore.permissions.includes(permission)
  }
  
  return { hasPermission }
}
```

```vue
<!-- 按鈕層級 Permission 控制 -->
<template>
  <el-button v-if="hasPermission('user:delete')" type="danger">
    刪除
  </el-button>
</template>
```

### §5.3 動態選單生成

選單配置從 API 取回（server-driven），或本地按 Permission 過濾靜態配置。
選擇：`{{server-driven / client-filtered}}`，理由：`{{理由}}`

### §5.4 Token 管理

| 項目 | 規格 |
|------|------|
| Access Token TTL | `{{來自 CONSTANTS.md 的值}}` |
| Refresh Token TTL | `{{來自 CONSTANTS.md 的值}}` |
| Token 存儲位置 | `{{HttpOnly Cookie / Memory（不存 localStorage）}}` |
| Refresh 策略 | Axios Interceptor 自動 refresh，失敗 → 重導登入頁 |

---

## §6 Layout 系統

### §6.1 主 Layout 結構

```
┌──────────────────────────────────────┐
│  Top Header（Logo + 用戶選單 + 通知）  │
├─────────┬────────────────────────────┤
│ Sidebar │  Content Area              │
│ (260px) │  ┌──────────────────────┐  │
│ 選單    │  │  Breadcrumb          │  │
│ 動態展開 │  ├──────────────────────┤  │
│         │  │  Page Content        │  │
│         │  │                      │  │
│         │  └──────────────────────┘  │
└─────────┴────────────────────────────┘
```

### §6.2 Sidebar 規格

| 屬性 | 值 |
|------|-----|
| 寬度 | 260px（展開）/ 64px（收合） |
| 收合行為 | 僅顯示 icon，Tooltip 顯示名稱 |
| 選中樣式 | 左邊框 accent 色 + 背景淡色 |

---

## §7 主要頁面規格

### §7.1 登入頁（/admin/login）

- 表單欄位：Username + Password（不用 Email，避免暴露使用者存在與否）
- 失敗處理：連續 `{{來自 CONSTANTS.md: admin_login_max_attempts}}` 次失敗 → 鎖定帳號 + 通知管理員
- 2FA（若 PRD 要求）：`{{TOTP / SMS / 無}}`
- 成功後：重導 `/admin/dashboard`

### §7.2 Dashboard（/admin/dashboard）

統計卡（KPI Cards）：
| 卡片 | 資料來源 | 說明 | 更新策略 |
|------|---------|------|---------|
| `{{指標名}}` | `GET /admin/stats/{{endpoint}}` | `{{說明}}` | `{{輪詢/手動刷新/頁面載入}}` |

圖表：
| 圖表 | 類型 | 資料來源 |
|------|------|---------|
| `{{圖表名}}` | `{{折線/柱狀/圓餅}}` | `{{API endpoint}}` |

### §7.3 使用者管理（/admin/users）

**列表頁功能**：
- 搜尋：姓名 / Email / 狀態 / 角色
- 篩選：創建時間範圍 / 是否啟用
- 批量操作：批量啟用 / 停用（需 `user:update` 權限）
- 分頁：每頁 `{{20}}` 筆（來自 CONSTANTS.md）

**詳情/編輯頁功能**：
- 基本資料編輯
- 角色指派（需 `role:assign` 權限）
- 密碼重置（發送重置郵件，不直接改密碼）
- 帳號停用 / 啟用
- 登入歷史（最近 `{{N}}` 筆）

### §7.4 角色管理（/admin/roles）

- 角色列表（系統角色唯讀）
- 角色建立 / 編輯：名稱 + 描述 + Permission 勾選表格
- Permission 勾選表格：按資源分組顯示（users/roles/audit_log/{{business}}）
- 刪除保護：有用戶指派的角色不可刪除

### §7.5 稽核日誌（/admin/audit-log）

- 篩選：操作者 / 動作類型 / 資源 / 時間範圍
- 欄位顯示：時間 / 操作者 / 動作 / 資源 / 資源 ID / IP / 變更摘要
- 匯出：CSV 匯出（需 `audit_log:export` 權限）
- 唯讀：不可刪除、不可修改

### §7.x 業務功能頁（依 PRD 展開）

`{{依 PRD Admin 需求展開對應的業務管理頁面，每個頁面填入：路徑、功能清單、API endpoints、所需 Permission}}`

---

## §8 API 串接規格

### §8.1 Axios 配置

```typescript
// api/http.ts
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: {{ADMIN_API_TIMEOUT_MS}},  // 來自 CONSTANTS.md
})

// Request Interceptor：附加 Authorization header
http.interceptors.request.use(config => {
  const token = useAuthStore().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response Interceptor：Token refresh
http.interceptors.response.use(
  res => res,
  async error => {
    if (error.response?.status === 401) {
      await useAuthStore().refreshToken()
      return http(error.config)
    }
    return Promise.reject(error)
  }
)
```

### §8.2 API Endpoints 對應表（對應 API.md /admin/* 路由）

| 功能 | Method | Path | 所需 Permission | 對應頁面 |
|------|--------|------|----------------|---------|
| Admin 登入 | POST | `/admin/auth/login` | 公開 | `/admin/login` |
| Token Refresh | POST | `/admin/auth/refresh` | 公開 | — |
| 取得當前用戶 | GET | `/admin/me` | 已驗證 | — |
| 使用者列表 | GET | `/admin/users` | `user:list` | `/admin/users` |
| 建立使用者 | POST | `/admin/users` | `user:create` | `/admin/users` |
| 更新使用者 | PATCH | `/admin/users/:id` | `user:update` | `/admin/users/:id` |
| 角色列表 | GET | `/admin/roles` | `role:list` | `/admin/roles` |
| 建立角色 | POST | `/admin/roles` | `role:create` | `/admin/roles` |
| 指派角色 | POST | `/admin/users/:id/roles` | `role:assign` | `/admin/users/:id` |
| 稽核日誌 | GET | `/admin/audit-logs` | `audit_log:view` | `/admin/audit-log` |
| `{{功能}}` | `{{方法}}` | `{{路徑}}` | `{{權限}}` | `{{頁面}}` |

---

## §9 Pinia Store 架構

### §9.1 Store 清單

| Store | 職責 | 主要狀態 |
|-------|------|---------|
| `authStore` | 認證狀態 / Token 管理 | `user`, `accessToken`, `isAuthenticated` |
| `permissionStore` | 當前用戶 Permission 清單 | `permissions[]`, `roles[]` |
| `userStore` | 使用者管理業務狀態 | `userList`, `pagination`, `filters` |
| `{{storeName}}` | `{{職責}}` | `{{狀態}}` |

### §9.2 authStore 關鍵邏輯

> **Token 存儲方式對本節實作的影響（依 §5.4 選擇）：**
> - **HttpOnly Cookie**：`accessToken` 由瀏覽器自動附帶，此 store 不需存放 token 字串；`refreshToken()` 透過呼叫刷新端點完成，Cookie 由後端更新。
> - **Memory（預設範例）**：`accessToken` 存於 ref 中，頁面刷新後清空；需配合 silent refresh（頁面載入時呼叫 refresh endpoint 恢復 token）或導向登入頁。
> 請依 §5.4 的選擇調整下方程式碼邏輯，確保兩節保持一致。

```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<AdminUser | null>(null)
  const accessToken = ref<string | null>(null)
  
  const isAuthenticated = computed(() => !!accessToken.value)
  
  async function login(credentials: LoginRequest) {
    const res = await authApi.login(credentials)
    accessToken.value = res.access_token
    user.value = res.user
    await usePermissionStore().loadPermissions()
  }
  
  async function refreshToken() {
    const res = await authApi.refresh()
    accessToken.value = res.access_token
  }
  
  function logout() {
    user.value = null
    accessToken.value = null
    router.push('/admin/login')
  }
  
  return { user, accessToken, isAuthenticated, login, refreshToken, logout }
})
```

---

## §10 Element Plus 組件規範

### §10.1 Table 組件標準（通用）

所有 Admin Table 必須實作：
- Loading 狀態（`v-loading`）
- Empty 狀態（`el-empty` 加「新增第一筆資料」提示）
- Error 狀態（載入失敗時顯示錯誤訊息 + 重試按鈕）
- 響應式欄位（小螢幕隱藏低優先欄位）

### §10.2 Form 組件標準

- 使用 `el-form` 的 `rules` prop 進行前端驗證
- 提交前 `formRef.validate()` 阻擋無效提交
- Loading 狀態防止重複提交
- 成功後顯示 `ElMessage.success(...)` + 關閉 Dialog

### §10.3 確認危險操作

所有刪除 / 停用 / 批量操作：
```typescript
await ElMessageBox.confirm('確定要刪除此項目？', '警告', {
  type: 'warning',
  confirmButtonText: '確定刪除',
  cancelButtonText: '取消',
})
```

---

## §11 通用組件規格

### §11.1 SearchableTable 組件

```
Props：
  - columns: TableColumn[]     ← 欄位定義（含 sortable / hidden）
  - fetchFn: (params) => Promise<PagedResponse>  ← 資料取得函式
  - searchFields: SearchField[]  ← 搜尋欄位定義
  - defaultSort: SortConfig    ← 預設排序

Emits：
  - selection-change(rows)     ← 多選變更
  - row-click(row)             ← 行點擊

Features：
  - 分頁（el-pagination，pageSize 來自 CONSTANTS.md）
  - 搜尋（debounce 300ms）
  - 排序（server-side）
  - 匯出 CSV（可選）
```

```typescript
// SearchableTable Props（TypeScript interface）
interface TableColumn {
  prop: string
  label: string
  width?: number | string
  sortable?: boolean
  formatter?: (row: unknown) => string
}

interface SearchField {
  prop: string
  label: string
  type: 'input' | 'select' | 'date-range'
  options?: { label: string; value: string | number }[]
}

interface SortConfig {
  prop: string
  order: 'ascending' | 'descending'
}

interface SearchableTableProps {
  columns: TableColumn[]
  fetchFn: (params: QueryParams) => Promise<PagedResponse<unknown>>
  searchFields?: SearchField[]
  defaultSort?: SortConfig
  pageSize?: number      // 預設來自 CONSTANTS.md
  selectable?: boolean
}

// 使用方式：
// defineProps<SearchableTableProps>()
```

### §11.2 AuditLogDetail 組件

顯示 old_value / new_value JSON Diff，使用 highlight 標示變更欄位。

```typescript
interface AuditLogDetailProps {
  operatorId: string
  targetType: string   // 'user' | 'wallet' | 'game' | ...
  targetId: string
  startDate?: string   // ISO 8601
  endDate?: string
  visible: boolean     // 控制 drawer/dialog 開關
}
// defineProps<AuditLogDetailProps>()
```

---

## §12 圖表整合規格

| 圖表類型 | 元件 | 資料更新策略 |
|---------|------|------------|
| 折線圖 | `ECharts LineChart` | 輪詢（每 `{{N}}` 秒） |
| 柱狀圖 | `ECharts BarChart` | 手動刷新 |
| 圓餅圖 | `ECharts PieChart` | 頁面載入時 |

`{{若有其他圖表，依樣展開}}`

---

## §13 國際化（i18n）

| 語言 | 代碼 | 優先序 |
|------|------|--------|
| 繁體中文 | `zh-TW` | 預設 |
| `{{其他語言}}` | `{{code}}` | `{{N}}` |

Element Plus Locale 同步設定（見 `main.ts`）。

---

## §14 效能優化

### §14.1 Lazy Loading

```typescript
// router/index.ts
{
  path: '/admin/users',
  component: () => import('@/views/user-management/UserListView.vue'),
}
```

### §14.2 Bundle 分析

```bash
# 執行 bundle 分析
npx vite-bundle-visualizer
```

目標：主 bundle < `{{150}}` KB gzipped（來自 CONSTANTS.md 或專案約定）。

---

## §15 部署配置

### §15.1 Vite Build 設定

```typescript
// vite.config.ts
export default defineConfig({
  base: '/admin/',
  build: {
    outDir: 'dist/admin',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue': ['vue', 'vue-router', 'pinia'],
          'vendor-element': ['element-plus'],
          'vendor-charts': ['echarts'],
        }
      }
    }
  }
})
```

### §15.2 環境變數

| 變數 | Development | Production |
|------|-------------|-----------|
| `VITE_API_BASE_URL` | `http://localhost:{{PORT}}/api` | `/api`（Nginx 反代） |
| `VITE_ADMIN_PATH` | `/admin` | `/admin` |

### §15.3 Nginx 路由配置

```nginx
# Admin Portal SPA routing
location /admin/ {
  root /usr/share/nginx/html;
  try_files $uri $uri/ /admin/index.html;
}

# Admin API proxy
location /api/admin/ {
  proxy_pass http://backend:{{PORT}}/api/admin/;
  proxy_set_header Authorization $http_authorization;
}
```

---

## §16 Self-Check Checklist（生成後必須全部通過）

- [ ] §2 所有依賴版本號已填入具體版本（無 latest 或空版本，vue/element-plus/pinia/vue-router/axios 均已指定）
- [ ] §0 Admin 技術棧欄位已填入（_ADMIN_FRAMEWORK 來自 EDD §3.3，非 placeholder）
- [ ] §5.1 角色清單與 EDD §5.5-A 完全對應（無遺漏）
- [ ] §5.1 Permission 清單與 API.md /admin/* endpoint 一對一對應
- [ ] §7.1-7.5 所有頁面均有對應的 API endpoint
- [ ] §8.2 API Endpoints 數量與 API.md /admin/* 路由數量相符
- [ ] §9 所有 Pinia Store 已完整定義（無 placeholder）
- [ ] CONSTANTS.md 中的數值已被正確引用（timeout / pageSize 等）
- [ ] §15 環境變數（VITE_API_BASE_URL）與 Nginx /admin/ try_files 已正確配置（非 placeholder）
- [ ] 無殘留 `{{PLACEHOLDER}}` 格式的未填內容
