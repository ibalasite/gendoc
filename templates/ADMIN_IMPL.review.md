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
  - "ARCH.md Admin Portal 容器：部署位置與技術棧與 §2 一致"
  - "CONSTANTS.md Token TTL 等常數：§5.4 Token 有效期數值引用一致"
---

# ADMIN_IMPL.review.md — Admin 後台實作規格審查標準

---

## §0 文件完整性審查

### HI-07：上游文件引用正確性

**Check**: §0 文件資訊表中的上游文件引用（EDD、API、SCHEMA）是否均存在且路徑正確？具體確認：
1. `EDD.md` 已存在且包含 §3.3 + §5.5-A 段落
2. `API.md` 已存在且包含 `/admin/*` 路由章節
3. `SCHEMA.md` 已存在且包含 RBAC 相關資料表章節
4. §0 表格中的引用連結路徑與實際檔案路徑一致（無相對路徑錯誤）

**Risk**: 上游文件缺失或路徑錯誤時，AI 讀取上游資料失敗，導致後續生成內容依據不足，產生幻覺填充。  
**Fix**: 確認三份上游文件均已生成，並修正 §0 中的引用路徑（統一使用 `docs/` 前綴）。

---

## §1 Admin Portal 概覽審查

### ME-06：§1.3 角色清單與 EDD §5.5-A 對齊

**Check**: §1.3 使用者角色表格中列出的角色（role_name + description + capabilities）是否與 EDD §5.5-A 角色定義完全對應？具體確認：
1. 角色數量與 EDD §5.5-A 一致（無遺漏、無多餘）
2. 角色 key（英文 code）與 EDD §5.5-A 命名一致（大小寫、底線格式）
3. 每個角色的 capabilities 描述覆蓋 EDD §5.5-A 中該角色的操作範圍

**Risk**: §1.3 與 EDD §5.5-A 不一致，後續 §5 RBAC 定義以 §1.3 為基礎時將引入偏差，導致整份文件 RBAC 系統性錯誤。  
**Fix**: 對照 EDD §5.5-A 補充或修正 §1.3 的角色清單，確保與 EDD 完全對應。

---

## CRITICAL 級別（阻斷性問題 — 必須修復才能使用）

### CR-01：RBAC PermissionGuard 缺失或不完整

**Check**: §5 是否有 `hasPermission()` 函數實作 + Vue 指令（v-permission）？  
**Risk**: 若無 PermissionGuard，任何用戶可存取所有 Admin 功能，產生嚴重安全漏洞。  
**Fix**: 補充 `composables/usePermission.ts` 中完整的 `hasPermission()` 實作 + `permissionDirective` 定義，並說明 mounted/updated 生命週期處理。

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

**Check**: §2 依賴版本表每行是否都有具體版本號（如 `3.4+`、`2.7.x`）？額外確認 Element Plus 版本匹配：
1. 所有依賴均有明確版本號，無 "latest" 或空白
2. Element Plus 版本需 ≥2.0（v1.x API 與 v2.x 有重大差異，如 `ElTable` vs `el-table` 命名慣例、`ElMessage` 呼叫方式）
3. Element Plus 版本與 Vue 版本相容（Element Plus 2.x 需搭配 Vue 3.x；若 Vue < 3.0 則不相容）
4. 若使用 Element Plus 2.4+，確認 §10 中的組件 API（如 `el-table` 的 `row-key`、`el-form` 的 `validate()` 返回 Promise）使用正確的 v2.x 語法，而非 v1.x 的舊版 callback 寫法

**Risk**: "latest" 版本導致不同時間安裝產生不一致；Element Plus 版本不明確時，AI 可能混用 v1.x 和 v2.x API，導致組件無法正確渲染或方法呼叫錯誤。  
**Fix**: 將所有 "latest" 替換為具體的最低支援版本號；明確標注 Element Plus ≥2.0 並確認與 Vue 版本相容性。

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

**Check**: §14 是否明確標注 bundle size 目標（< 150KB gzipped）和首屏時間目標（< 2s）？額外確認：
1. Bundle size 目標有明確數值（如 `< 150KB gzipped`），而非保留 `{{150}}` 這類未填充的 placeholder 格式
2. 若仍為 `{{150}}` placeholder，表示數值未從 `constants.json` 或專案約定取得，需補充具體數值
3. 首屏時間目標有明確毫秒數（如 `< 2000ms in 3G`），而非模糊描述

**Risk**: 無具體目標或保留 placeholder，效能優化無依據；`{{150}}` 等 placeholder 殘留也代表文件生成不完整。  
**Fix**: 補充具體的 bundle size 目標數值（推薦 `< 150KB gzipped`，Element Plus 按需引入）+ 路由懶加載配置範例，並確認無殘留 `{{N}}` 格式的未填充內容。

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
**Risk**: 視窗縮放後圖表無法自動 resize，圖表版面失真，影響 Dashboard 資料可讀性。  
**Fix**: 補充圖表 resize 事件綁定 + Vue 組件卸載時 removeEventListener 的說明。

---

### LO-02：§13 i18n 缺少 locale 自動偵測說明

**Check**: §13 是否說明如何自動偵測瀏覽器語言 fallback 到預設 locale？  
**Risk**: 無 locale 自動偵測，多語言用戶首次進入 Admin Portal 需手動切換語言，體驗不一致。  
**Fix**: 補充 `navigator.language` 偵測邏輯。

---

### LO-03：§5 Token 有效期未引用 CONSTANTS.md

**Check**: §5 Token 管理的有效期數值是否引用自 `docs/CONSTANTS.md` 的常數（如 `ACCESS_TOKEN_TTL`）？  
**Risk**: Token 有效期硬編碼，若業務調整後修改 CONSTANTS.md 但未同步更新 §5，文件與實際配置脫節。  
**Fix**: 將硬編碼的 Token 時間（如 "15 minutes"）替換為引用 CONSTANTS.md 中的對應常數名稱。

---

### LO-04：§16 Self-Check Checklist 不完整

**Check**: §16 的 Self-Check 是否包含至少 8 個可驗證項目？  
**Risk**: Self-Check 項目不足，生成後驗證不完整，可能遺漏關鍵缺陷。  
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

### ALN-05：與 ARCH.md Admin Portal 容器對齊

對照 `docs/ARCH.md` C4 Container 圖或 Admin Portal 部署描述，確認：
1. §2 技術棧選型與 ARCH.md 中 Admin Portal 容器標注的技術一致（如 ARCH 標注「Vue SPA」而 §2 選 React，則為衝突）
2. §15 部署配置（Nginx 路徑、環境變數）與 ARCH.md 中 Admin Portal 對外暴露的服務路徑一致
3. §8 API baseURL 設定與 ARCH.md 中 Admin Portal → Backend API 的連線路徑一致

若 ARCH.md 無 Admin Portal 相關描述，標注「ARCH.md 無 Admin Portal 容器描述，略過此對齊項」。

---

## 稽核日誌功能審查（強制項）

若 EDD §5.5 有定義 AuditLog 模型，必須確認：
- [ ] §7 稽核日誌頁面有完整的列表欄位說明（操作者/時間/操作類型/資源/IP）
- [ ] §5 或 §7 有說明哪些操作會寫入 AuditLog（如：用戶創建/刪除/角色變更）
- [ ] §8 有對應的 `GET /admin/audit-logs` endpoint 和查詢參數說明

若缺失上述任一項，評定為 HIGH 級別 Finding。

---

## 安全審查（強制項）

針對 Admin Portal 的特殊安全性要求，額外審查以下正式 Finding：

### CR-06：Token 存儲安全

**Check**: §5 Token 管理是否明確說明 token 存儲位置？推薦選項為 HttpOnly Cookie 或 Memory（不存 localStorage）。確認：
1. §5.4 Token 存儲位置欄位有明確值（非 placeholder）
2. 若使用 localStorage，必須有說明與 XSS 防護措施；若無說明，視為安全缺陷
3. Memory 存儲須說明頁面刷新後的 token 恢復策略

**Risk**: token 存儲於 localStorage 時，任何 XSS 漏洞均可竊取 token，攻擊者獲得 Admin Portal 完整存取權限。  
**Fix**: 在 §5.4 明確標注存儲位置並說明防護策略：推薦「HttpOnly Cookie（後端設置，不可 JS 存取）」或「Memory（頁面生命週期內有效，配合 silent refresh）」。

---

### HI-08：密碼欄位不得在列表頁顯示

**Check**: §7 使用者管理列表頁的欄位說明中，是否明確排除密碼（password/password_hash）欄位？確認：
1. §7.3 使用者列表欄位清單中無 password / password_hash 項目
2. 詳情/編輯頁說明中，密碼操作使用「發送重置郵件」而非「直接顯示或修改明文密碼」

**Risk**: 若列表或詳情頁意外顯示密碼相關欄位，即使是雜湊值也會洩露安全資訊，且可能誤導前端工程師實作直接顯示密碼。  
**Fix**: 在 §7.3 列表欄位說明末尾明確標注「密碼欄位不得在任何頁面顯示，重置密碼應透過發送重置郵件實作」。

---

### HI-09：危險操作必須有二次確認

**Check**: §10 Element Plus 規範或各頁面規格中，是否明確要求刪除、批量停用、角色移除等危險操作需要 `ElMessageBox.confirm` 二次確認？確認：
1. §10.3 有明確的二次確認規範（含 ElMessageBox 程式碼範例）
2. §7 使用者管理、角色管理的刪除/停用操作均引用此規範
3. 二次確認文字應說明具體操作（如「確定要刪除使用者 {name}？」）而非通用「確定？」

**Risk**: 缺少二次確認的危險操作容易造成誤操作，Admin 誤刪用戶或批量停用帳號無法快速還原，影響業務連續性。  
**Fix**: 確認 §10.3 有 `ElMessageBox.confirm` 範例，並在 §7 各頁面操作說明中標注哪些操作需二次確認。

---

### ME-07：Axios 配置應包含 CSRF Token Header

**Check**: §8 Axios 配置（request interceptor）是否說明 CSRF token 的注入策略？確認：
1. 若後端採用 CSRF 防護（如 Django、Laravel、Spring Security），Axios 的 request interceptor 需從 Cookie 讀取 CSRF token 並注入至 `X-CSRFToken` 或 `X-XSRF-TOKEN` header
2. 若後端使用無狀態 JWT（不需 CSRF），應在 §8 說明「使用 JWT Bearer Token 認證，無需額外 CSRF token」

**Risk**: 後端有 CSRF 防護但前端未注入 token 時，所有 POST/PATCH/DELETE 請求將被 403 拒絕，Admin 無法執行任何寫入操作。  
**Fix**: 在 §8.1 Axios 配置說明末尾補充 CSRF 策略選擇：「若後端有 CSRF 防護，在 request interceptor 加入 CSRF token 注入；若純 JWT 則無需此步驟」。

---

### ME-08：用戶輸入應說明 XSS Sanitize 需求

**Check**: §7 頁面規格（特別是包含富文字或自由輸入欄位的頁面）是否提及 XSS sanitize 策略？確認：
1. 若有顯示用戶生成內容（如備註、描述欄位），§7 說明中需提及使用 sanitize 函式（如 DOMPurify）處理後再渲染
2. 若使用 `v-html` 渲染任何動態內容，必須說明先做 sanitize
3. 純文字欄位使用 `{{ }}` 插值（Vue 自動 escape），不需額外說明

**Risk**: 未說明 sanitize 需求，前端工程師可能使用 `v-html` 直接渲染用戶輸入，造成 Stored XSS 攻擊，Admin Portal 被植入惡意腳本。  
**Fix**: 在 §7 相關頁面規格中補充「含動態 HTML 渲染的欄位需使用 DOMPurify 或同等 sanitize 函式處理後再使用 `v-html`」。

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
