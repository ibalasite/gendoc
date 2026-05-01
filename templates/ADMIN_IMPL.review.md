---
doc-type: ADMIN_IMPL
role: review
version: "1.0"
reviewer-roles:
  - name: RBAC Security Reviewer
    scope: §5 權限系統安全性、Token 管理、PermissionGuard 正確性
  - name: Vue3 Architecture Reviewer
    scope: §3-§4 目錄結構、路由設計、Pinia Store 架構合理性
  - name: Element Plus UX Reviewer
    scope: §6-§12 UI/UX 規範、組件使用、可用性
  - name: Deployment Reviewer
    scope: §15 部署配置、Nginx 規則、環境變數
quality-bar:
  - "§5 RBAC：Role 定義、Permission Guard、Token 管理均完整"
  - "§4 路由表：全部功能頁面有路由 + 權限 + 元件"
  - "§8 API 對應表：所有 /admin/* endpoint 均覆蓋"
  - "§9 三個 Pinia Store 有完整 state + actions"
  - "§15 部署：env 變數 + Nginx /admin/ 路由規則"
  - "全文無 {{PLACEHOLDER}} / TODO 空欄"
upstream-alignment:
  - "EDD §3.3 _ADMIN_FRAMEWORK：技術棧一致"
  - "EDD §5.5 RBAC 模型：Role/Permission 定義一致"
  - "API.md /admin/* endpoints：§8 對應表覆蓋"
  - "SCHEMA.md RBAC tables：§5 實作與 Schema 欄位一致"
---

# ADMIN_IMPL.review.md — Admin 後台實作規格審查標準

---

## CRITICAL 級別（阻斷性問題 — 必須修復才能使用）

### CR-01：RBAC PermissionGuard 缺失或不完整

**Check**: §5 是否有 `hasPermission()` 函數實作 + Vue 指令（v-permission）？  
**Risk**: 若無 PermissionGuard，任何用戶可存取所有 Admin 功能，產生嚴重安全漏洞。  
**Fix**: 補充 `utils/permission.ts` 中完整的 `hasPermission()` 實作 + `permissionDirective` 定義，並說明 mounted/updated 生命週期處理。

---

### CR-02：路由守衛邏輯缺失

**Check**: §4 是否有 `router.beforeEach` 守衛邏輯（JWT 驗證 + 403/401 處理）？  
**Risk**: 無路由守衛代表直接輸入 URL 可繞過登入，所有 Admin 頁面公開暴露。  
**Fix**: 在 `router/guards.ts` 補充：
1. 未登入 → 重定向 `/admin/login`  
2. 無所需 Permission → 重定向 `/admin/403`  
3. 已登入訪問 login → 重定向 dashboard

---

### CR-03：Axios 攔截器 Token 注入缺失

**Check**: §8 Axios 配置是否有 request interceptor 自動注入 `Authorization: Bearer <token>`？  
**Risk**: 若無 Token 注入，所有 Admin API 呼叫會被後端 401 拒絕，整個 Admin Portal 無法運作。  
**Fix**: 補充完整的 request interceptor code block，從 authStore 讀取 token 並注入 header。

---

### CR-04：所有必要頁面的路由缺失

**Check**: §4 路由表是否包含：login / dashboard / users / roles / audit-log 五個核心頁面？  
**Risk**: 缺少任一核心頁面路由，Admin Portal 功能不完整，無法交付。  
**Fix**: 逐一核對必要頁面清單，補充缺失路由（含 path + component + meta.permission）。

---

### CR-05：§9 Pinia Store 缺失或無 actions

**Check**: §9 是否有 authStore + permissionStore + userStore 三個 Store，每個都有 state 定義和主要 actions？  
**Risk**: 無 Store 定義代表狀態管理空白，AI 實作時無法生成正確的狀態邏輯。  
**Fix**: 補充三個 Store 的 TypeScript interface + 主要 actions 函式簽名（含 async API 呼叫描述）。

---

## HIGH 級別（重要缺陷 — 合併前應修復）

### HI-01：技術棧版本表有 "latest" 或空版本

**Check**: §2 依賴版本表每行是否都有具體版本號（如 `3.4+`、`2.7.x`）？  
**Risk**: "latest" 版本導致不同時間安裝產生不一致，AI 生成 package.json 時無法確定版本。  
**Fix**: 將所有 "latest" 替換為具體的最低支援版本號。

---

### HI-02：API 對應表未涵蓋所有 /admin/* endpoint

**Check**: 對照 `docs/API.md` 中所有 `/admin/` 開頭的路徑，是否在 §8 對應表中全部列出？  
**Risk**: 遺漏 endpoint 導致前端工程師實作時漏掉 API 呼叫，功能不完整。  
**Fix**: 重新掃描 API.md，補充所有 /admin/* 路徑的對應表行。

---

### HI-03：§5 RBAC Role 定義與 EDD §5.5 不一致

**Check**: §5 中定義的 Role 清單（code 名稱 + 中文名稱 + Permission 範圍）是否與 EDD §5.5 完全一致？  
**Risk**: Role 定義不一致，導致後端 RBAC 和前端顯示行為不同，引發生產 Bug。  
**Fix**: 對照 EDD §5.5 修正 §5 的 Role 定義表，確保 code 名稱精確匹配。

---

### HI-04：§3 目錄結構缺少關鍵資料夾

**Check**: §3 目錄樹是否包含 views / layout / router / store / api / components / utils / types 所有子目錄？  
**Risk**: 缺少 types/ 或 utils/ 導致 AI 生成代碼時無明確存放位置，引發代碼散落。  
**Fix**: 補充缺失的目錄節點並附加一行說明。

---

### HI-05：§15 部署缺少 Nginx /admin/ try_files

**Check**: §15 是否有 Nginx location /admin/ 的 `try_files $uri $uri/ /admin/index.html` 配置？  
**Risk**: SPA 路由刷新頁面時，Nginx 會返回 404 而非讓 Vue Router 處理，所有子路由刷新失效。  
**Fix**: 補充完整 Nginx server block 包含 `try_files` 規則。

---

### HI-06：§7 頁面規格缺少操作按鈕或表單欄位說明

**Check**: 每個頁面規格是否列出：主要表格欄位 / 操作按鈕（含所需 Permission） / 表單欄位（新增/編輯）？  
**Risk**: 規格不完整，AI 實作時會自行猜測欄位，導致與需求不一致。  
**Fix**: 為每個頁面補充具體的欄位清單和操作說明。

---

## MEDIUM 級別（品質問題 — 建議修復）

### ME-01：§10 Element Plus 規範不完整

**Check**: §10 是否涵蓋 Table 三狀態 + Form 驗證 + ElMessageBox 二次確認 + 全局 message 格式？  
**Risk**: 規範不完整導致各頁面 UI 行為不一致，影響使用者體驗。  
**Fix**: 補充缺失的規範項目，每項附一個 code 範例。

---

### ME-02：§11 共用組件缺少 Props 定義

**Check**: `SearchableTable` 和 `AuditLogDetail` 組件是否有完整的 Props TypeScript interface？  
**Risk**: 無 Props 定義，AI 生成組件時接口設計不一致，難以複用。  
**Fix**: 為每個共用組件添加 `defineProps<{...}>()` 的型別定義。

---

### ME-03：§14 效能目標缺乏具體數值

**Check**: §14 是否明確標注 bundle size 目標（< 150KB gzipped）和首屏時間目標（< 2s）？  
**Risk**: 無具體目標，效能優化無依據，代碼審查時無法判斷是否達標。  
**Fix**: 補充具體的 bundle size 目標 + 路由懶加載配置範例。

---

### ME-04：§8 未說明 401/403 攔截器行為

**Check**: §8 response interceptor 是否說明 401（token 失效 → 重新導向 login）和 403（無權限 → toast 提示）的處理邏輯？  
**Risk**: 不同開發者對錯誤處理有不同理解，導致行為不一致。  
**Fix**: 在 Axios response interceptor 區塊補充 401/403 的具體處理說明。

---

### ME-05：§6 Layout 缺少響應式說明

**Check**: §6 Layout 規範是否說明 Admin Portal 的響應式斷點策略（Admin 通常以桌面為主，是否支援平板？）？  
**Risk**: 無明確說明，各頁面響應式行為不一致。  
**Fix**: 補充說明響應式策略（如「1024px 以下顯示 Hamburger Menu，不支援手機）。

---

## LOW 級別（建議改善 — 可選）

### LO-01：§12 圖表整合缺少響應式 resize 說明

**Check**: §12 ECharts 圖表是否有 `window.addEventListener('resize', chart.resize)` 的響應式說明？  
**Fix**: 補充圖表 resize 事件綁定 + Vue 組件卸載時 removeEventListener 的說明。

---

### LO-02：§13 i18n 缺少 locale 自動偵測說明

**Check**: §13 是否說明如何自動偵測瀏覽器語言 fallback 到預設 locale？  
**Fix**: 補充 `navigator.language` 偵測邏輯。

---

### LO-03：§5 Token 有效期未引用 CONSTANTS.md

**Check**: §5 Token 管理的有效期數值是否引用自 `docs/CONSTANTS.md` 的常數（如 `ACCESS_TOKEN_TTL`）？  
**Fix**: 將硬編碼的 Token 時間（如 "15 minutes"）替換為引用 CONSTANTS.md 中的對應常數名稱。

---

### LO-04：§16 Self-Check Checklist 不完整

**Check**: §16 的 Self-Check 是否包含至少 8 個可驗證項目？  
**Fix**: 確認清單完整覆蓋：目錄結構 / 路由 / RBAC / 頁面規格 / API / Store / 效能 / placeholder。

---

## 上游對齊審查

在完成基本審查後，額外執行以下上游對齊檢查：

### ALN-01：與 EDD §3.3 技術棧對齊

對照 `docs/EDD.md` §3.3 `_ADMIN_FRAMEWORK` 欄位值，確認 §2 技術棧選擇一致。

### ALN-02：與 API.md /admin/* 對齊

統計 API.md 中 /admin/ 前綴的路徑數量，確認 §8 對應表行數相符（±1 容錯）。

### ALN-03：與 SCHEMA.md RBAC Tables 對齊

確認 §5 的 TypeScript interface 中的欄位名稱與 SCHEMA.md 中 Role/Permission/AdminUser table 的欄位名稱一致。

### ALN-04：與 PRD Admin 功能模組對齊

確認 §7 頁面規格涵蓋 PRD 中所有提及的 Admin 功能模組（逐一對照）。

---

## 稽核日誌功能審查（強制項）

若 EDD §5.5 有定義 AuditLog 模型，必須確認：
- [ ] §7 稽核日誌頁面有完整的列表欄位說明（操作者/時間/操作類型/資源/IP）
- [ ] §5 或 §7 有說明哪些操作會寫入 AuditLog（如：用戶創建/刪除/角色變更）
- [ ] §8 有對應的 `GET /admin/audit-logs` endpoint 和查詢參數說明

若缺失上述任一項，評定為 HIGH 級別 Finding。

---

## 安全審查（強制項）

針對 Admin Portal 的特殊安全性要求，額外審查：

| 安全點 | 檢查內容 | 嚴重度 |
|--------|---------|-------|
| XSS | §7 說明中是否提及用戶輸入應做 sanitize | MEDIUM |
| CSRF | §8 Axios 配置是否包含 CSRF token header | MEDIUM |
| 敏感操作確認 | §10 是否要求刪除/批量操作需 ElMessageBox 二次確認 | HIGH |
| 密碼欄位 | §7 用戶管理是否說明密碼欄位不得在列表顯示 | HIGH |
| Token 存儲 | §5 是否說明 token 存儲位置（推薦 httpOnly cookie 或 memory，避免 localStorage XSS）| CRITICAL |

---

## 審查完成輸出格式

```yaml
ADMIN_IMPL_REVIEW_RESULT:
  round: N
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  upstream_alignment:
    EDD_admin_framework: aligned|mismatched|not_found
    API_admin_endpoints: aligned|mismatched|partial
    SCHEMA_rbac_tables: aligned|mismatched|not_found
  security_check:
    token_storage: pass|fail
    permission_guard: pass|fail
    router_guard: pass|fail
  findings:
    - id: AR-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      section: "§N.N"
      check_ref: "CR-0N / HI-0N / ME-0N / LO-0N / ALN-0N"
      issue: "具體問題描述"
      fix_guide: "具體修復指引"
```
