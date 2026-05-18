---
name: gendoc-gen-prototype
description: |
  從工程文件自動生成互動式 HTML Prototype，輸出至 docs/pages/prototype/。支援兩種模式：
  UI Prototype（PRD/PDD/VDD/FRONTEND/AUDIO/ANIM → 可點擊畫面 + 動畫音效）
  API Explorer（API.md/SCHEMA.md → Postman 式試打介面，JavaScript 模擬回應，含 deep-link 分享）
  兩種文件同時存在時並行生成（full 模式）。含 gen→review→fix loop，commit，並自動更新 README.md。
  可獨立呼叫（/gendoc-gen-prototype）或由 gendoc-gen-html 自動呼叫。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
  - Skill
  - AskUserQuestion
---

# gendoc-gen-prototype — 互動式 HTML Prototype 生成

從工程文件自動生成可點擊的 HTML Prototype，放置於 `docs/pages/prototype/`。
效果等同於 Figma Demo Link —— 可展示所有畫面、點擊導覽、動畫、音效。

**支援專案類型：** SaaS / 服務後台 / 遊戲（Cocos / Unity / HTML5）/ 任何有 Frontend 需求的專案

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：讀取 State + 判斷 Frontend 需求

### Step 0-A：讀取執行設定

```bash
_CWD="$(pwd)"
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

_EXEC_MODE=$(python3 -c "
import json
try: print(json.load(open('$_STATE_FILE')).get('execution_mode','full-auto'))
except: print('full-auto')
" 2>/dev/null || echo "full-auto")

_MAX_ROUNDS=$(python3 -c "
import json
try: print(int(json.load(open('$_STATE_FILE')).get('max_rounds', 5)))
except: print(5)
" 2>/dev/null || echo "5")

_REVIEW_STRATEGY=$(python3 -c "
import json
try: print(json.load(open('$_STATE_FILE')).get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")

echo "[proto] EXEC_MODE=${_EXEC_MODE}  strategy=${_REVIEW_STRATEGY}  max_rounds=${_MAX_ROUNDS}"
```

### Step 0-B：Prototype 模式偵測

```bash
# 掃描現有文件，決定 Prototype 模式
_HAS_FRONTEND=0
_HAS_API=0
_HAS_AUDIO=0
_HAS_ANIM=0
_DOCS_FOUND=""

[ -f "docs/FRONTEND.md" ]  && _HAS_FRONTEND=1 && _DOCS_FOUND="$_DOCS_FOUND FRONTEND.md"
[ -f "docs/PDD.md" ]       && _HAS_FRONTEND=1 && _DOCS_FOUND="$_DOCS_FOUND PDD.md"
[ -f "docs/API.md" ]       && _HAS_API=1       && _DOCS_FOUND="$_DOCS_FOUND API.md"
[ -f "docs/VDD.md" ]       && _DOCS_FOUND="$_DOCS_FOUND VDD.md"
[ -f "docs/AUDIO.md" ]     && _HAS_AUDIO=1    && _DOCS_FOUND="$_DOCS_FOUND AUDIO.md"
[ -f "docs/ANIM.md" ]      && _HAS_ANIM=1     && _DOCS_FOUND="$_DOCS_FOUND ANIM.md"
[ -f "docs/PRD.md" ]       && _DOCS_FOUND="$_DOCS_FOUND PRD.md"
[ -f "docs/EDD.md" ]       && _DOCS_FOUND="$_DOCS_FOUND EDD.md"
[ -f "docs/SCHEMA.md" ]    && _DOCS_FOUND="$_DOCS_FOUND SCHEMA.md"
[ -f "docs/ADMIN_IMPL.md" ] && _DOCS_FOUND="$_DOCS_FOUND ADMIN_IMPL.md"

_HAS_ADMIN=$(python3 -c "import json; d=json.load(open('$_STATE_FILE')); print('1' if d.get('has_admin_backend', False) else '0')" 2>/dev/null || echo "0")

# 決定 Prototype 模式
if [ "$_HAS_FRONTEND" -eq 1 ] && [ "$_HAS_API" -eq 1 ]; then
  _PROTO_MODE="full"          # 全棧：UI Prototype + API Explorer
elif [ "$_HAS_FRONTEND" -eq 1 ]; then
  _PROTO_MODE="ui"            # 純前端：可點擊畫面 + 導覽流程
elif [ "$_HAS_API" -eq 1 ]; then
  _PROTO_MODE="api-explorer"  # 純後端：API 試打介面 + Mock 回應
else
  _PROTO_MODE="ui"            # 無文件，依 PRD + EDD 推斷畫面
fi

echo "[proto] 偵測到文件：${_DOCS_FOUND}"
echo "[proto] MODE=${_PROTO_MODE}  HAS_FRONTEND=${_HAS_FRONTEND}  HAS_API=${_HAS_API}  HAS_AUDIO=${_HAS_AUDIO}  HAS_ANIM=${_HAS_ANIM}  HAS_ADMIN=${_HAS_ADMIN}"

if [ "$_HAS_FRONTEND" -eq 0 ] && [ "$_HAS_API" -eq 0 ]; then
  echo ""
  echo "⚠️  未偵測到 Frontend 或 API 設計文件。"
  echo "   Frontend 專案：先執行 /gendoc pdd 或 /gendoc frontend"
  echo "   API 專案：先執行 /gendoc api"
fi
```

**若 `_EXEC_MODE=interactive` 且 `_HAS_FRONTEND=0` 且 `_HAS_API=0`**：用 `AskUserQuestion` 確認是否繼續。
**若 `_EXEC_MODE=full-auto` 且無任何設計文件**：仍繼續生成（依 PRD + EDD 推斷）。

---

## Step 1：文件掃描 — 畫面清單 & 設計規格提取

### Step 1-0：Codebase 實作掃描（優先執行）

**在讀設計文件之前，先掃描 `docs/req/` 中的實作參考資料。若找到，其內容優先於文件推算值。**

```bash
_REQ_DIR="$(pwd)/docs/req"
_HAS_CODEBASE_REF="no"

if [[ -d "$_REQ_DIR" ]]; then
  # 偵測實作參考檔案
  _CODEBASE_FILES=$(find "$_REQ_DIR" -maxdepth 1 -type f \( \
    -name "codebase-*.md" -o \
    -name "codebase-*.txt" -o \
    -name "*-EDD.md" -o \
    -name "engine_config.json" -o \
    -name "*.feature" \
  \) 2>/dev/null)

  if [[ -n "$_CODEBASE_FILES" ]]; then
    _HAS_CODEBASE_REF="yes"
    echo "[Step 1-0] ✅ 偵測到 codebase 實作參考："
    echo "$_CODEBASE_FILES" | sed 's/^/  /'
  else
    echo "[Step 1-0] ℹ️  docs/req/ 無 codebase 參考檔案，使用文件推算模式"
  fi
fi
```

**若 `_HAS_CODEBASE_REF=yes`**，先用 Agent subagent 讀取這些檔案，提取：

```
你是 Codebase Implementation Analyst。
任務：從 docs/req/ 的實作參考資料中提取真實 UI 規格，這些資料比設計文件更精確。

讀取所有 docs/req/codebase-*.md、docs/req/*-EDD.md、docs/req/engine_config.json（若存在）。

提取以下資訊（找到什麼提取什麼，找不到填 null）：

CODEBASE_SNAPSHOT:
  screens:
    # 從 codebase 中找到的真實畫面/場景清單（非文件推算）
    - id: "實際 ID 或 scene name"
      name: "真實名稱"
      entry_point: true|false
      components: ["實際元件/prefab 名稱"]
  design_tokens:
    # 從 codebase 找到的真實 CSS 變數 / 色彩值
    primary_color: null | "#實際色碼"
    background: null | "#實際色碼"
    font_family: null | "實際字型"
  render_mode: null | "dom | canvas | webgl"
    # 從 engine_config 或 codebase 結構推斷
  audio_events:
    # 真實 SFX 事件名稱（從 codebase 找到的）
    - id: "實際事件 ID"
      trigger: "實際觸發條件"
  anim_classes:
    # 真實動畫 CSS class 或函式名稱
    - name: "實際名稱"
      type: "css | js | spine | tween"
  notes: "其他從 codebase 觀察到的重要 UI 實作細節"
```

輸出的 `CODEBASE_SNAPSHOT` 會在 Step 1 文件掃描後合併：**codebase 的值覆蓋文件推算值**，null 表示讓文件值保留。

---

用 **Agent tool** 派送「文件掃描 Subagent」：

```
你是 UI/UX Specification Analyst（資深產品設計分析師）。
任務：從工程文件中提取所有畫面、導覽流程、設計規格，輸出結構化清單供後續 Prototype 生成使用。

**若主 Claude 已提供 CODEBASE_SNAPSHOT，必須將其中的非 null 值直接採用，不得用文件推算值覆蓋。**

**讀取步驟（不得跳過）：**
1. 若存在，讀取 docs/PRD.md → 提取：User Stories、功能模組、使用者角色
2. 若存在，讀取 docs/PDD.md → 提取：畫面清單（Screen List）、設計決策、UX 流程
3. 若存在，讀取 docs/VDD.md → 提取：色彩系統（主色/輔色/背景/文字）、字型規範、間距規範、品牌風格
4. 若存在，讀取 docs/FRONTEND.md → 提取：組件清單、頁面結構、導覽架構、互動規格
5. 若存在，讀取 docs/AUDIO.md → 提取：BGM 清單、P0 SFX 觸發點（事件名稱）、VO 關鍵點
6. 若存在，讀取 docs/ANIM.md → 提取：P0/P1 動畫清單（進場/轉場/強調）、粒子特效規格
7. 若存在，讀取 docs/SCHEMA.md → 提取：主要資料結構（用於生成 mock data）
8. 若存在，讀取 docs/EDD.md → 提取：引擎/技術棧（用於判斷 Canvas/WebGL/HTML5 渲染模式）
9. 若存在，讀取 docs/req/GDD_*.md → 提取：遊戲設計規格（畫面、流程、數值）

**輸出格式（必須輸出此結構）：**

PROTOTYPE_SPEC:
  project_type: "saas | game | service | hybrid"
  render_mode: "dom | canvas | webgl"

  screens:
    - id: "screen-01"
      name: "畫面名稱"
      role: "對應使用者角色"
      entry_point: true|false  # 是否為首頁/入口
      source: "PRD User Story N / PDD Screen List / FRONTEND §N"
      nav_from: []  # 哪些 screen 可以導覽到此處
      nav_to: []    # 此處可以導覽到哪些 screen
      components: ["Header", "DataTable", "Button"]
      mock_data_needed: true|false

  design_tokens:
    primary_color: "#XXXXXX"
    secondary_color: "#XXXXXX"
    background: "#XXXXXX"
    surface: "#XXXXXX"
    text_primary: "#XXXXXX"
    text_secondary: "#XXXXXX"
    accent: "#XXXXXX"
    error: "#XXXXXX"
    success: "#XXXXXX"
    font_family: "字型名稱或 system-ui fallback"
    font_size_base: "16px"
    border_radius: "8px"
    spacing_unit: "8px"

  animations:
    - id: "anim-01"
      trigger: "screen-enter | click | scroll | game-event"
      target: "畫面或元素"
      type: "fade | slide | scale | particle | shader"
      duration_ms: 300
      source: "ANIM.md §N"

  audio:
    bgm:
      - id: "BGM-001"
        trigger_screen: "screen-01"
        loop: true
    sfx:
      - id: "SFX-001"
        trigger_event: "onClick:btn-submit"

  mock_data:
    - entity: "User"
      sample: {"id": 1, "name": "示範使用者", ...}
```

Agent 執行完成後，主 Claude 解析輸出的 `PROTOTYPE_SPEC`，並執行合併：

```
若 CODEBASE_SNAPSHOT 存在：
  - screens：codebase 的 screen id/name/components 覆蓋文件推算值
  - design_tokens：codebase 的非 null 色碼/字型覆蓋文件推算值
  - render_mode：codebase 的非 null 值覆蓋文件推算值
  - audio.sfx：以 codebase audio_events 為準（追加文件清單中文件有但 codebase 沒有的）
  - animations：以 codebase anim_classes 補充文件清單
  保留原則：codebase 有的用 codebase，codebase 無的（null）才用文件推算
```

合併後的 `PROTOTYPE_SPEC` 供後續步驟使用。

> **若 `_PROTO_MODE=api-explorer`**：跳過本 Step，直接執行 Step 1-B。
> **若 `_PROTO_MODE=full`**：執行本 Step + Step 1-B，兩份規格並行使用。

---

## Step 1-B：API Explorer 規格提取（僅 api-explorer / full 模式）

**`_PROTO_MODE` 為 `api-explorer` 或 `full` 時執行。**

用 **Agent tool** 派送「API Specification Subagent」：

```
你是 API Specification Analyst（資深 API 設計分析師）。
任務：從 docs/API.md 和 docs/SCHEMA.md 提取所有 API endpoint 規格，輸出結構化清單
供後續 API Explorer Prototype 生成使用。

**讀取步驟（不得跳過）：**
1. 讀取 docs/API.md → 提取所有 endpoint：method, path, description, parameters（path/query/header）,
   request_body schema, response codes（200/400/401/404/500）及 response schema
2. 若存在，讀取 docs/SCHEMA.md → 提取所有 Entity 定義和 example data，用於組裝 mock 回應
3. 若存在，讀取 docs/EDD.md → 提取：base_url、認證方式（Bearer Token / API Key / OAuth2 / none）
4. 若存在，讀取 docs/PRD.md → 提取：功能分組標籤（用於 endpoint 側欄分組）

**輸出格式（必須輸出此結構）：**

API_EXPLORER_SPEC:
  project_name: "..."
  base_url: "https://api.example.com/v1"   # 從 EDD 或 API.md 提取；若無則用此預設
  auth:
    type: "bearer | api_key | oauth2 | none"
    header: "Authorization"
    placeholder: "Bearer <your_token>"
  groups:
    - id: "users"
      name: "User Management"
      color: "#2d9ef5"   # 每組一個主色（用於 sidebar 色條）
      endpoints:
        - id: "list-users"
          method: "GET"          # GET / POST / PUT / PATCH / DELETE
          path: "/users"
          summary: "取得使用者列表"
          description: "回傳分頁使用者清單，支援關鍵字篩選"
          params:
            - name: "page"
              in: "query"          # path | query | header
              type: "integer"
              required: false
              default: "1"
              description: "頁碼（從 1 開始）"
            - name: "q"
              in: "query"
              type: "string"
              required: false
              default: ""
              description: "關鍵字搜尋"
          request_body: null       # 或 schema JSON string（POST/PUT 時使用）
          responses:
            - code: 200
              description: "成功"
              example: |
                {
                  "data": [
                    {"id": 1, "name": "Alice", "email": "alice@example.com"},
                    {"id": 2, "name": "Bob",   "email": "bob@example.com"}
                  ],
                  "total": 42,
                  "page": 1,
                  "per_page": 20
                }
            - code: 401
              description: "未授權"
              example: |
                {"error": "unauthorized", "message": "Token invalid or expired"}
          mock_entity: "User"    # 對應 SCHEMA.md 的 Entity 名稱，用於填充 example data
        - id: "create-user"
          method: "POST"
          path: "/users"
          summary: "建立使用者"
          description: "建立新使用者帳號"
          params: []
          request_body: |
            {
              "name": "string",
              "email": "string",
              "role": "admin | member"
            }
          responses:
            - code: 201
              description: "建立成功"
              example: |
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
            - code: 400
              description: "參數錯誤"
              example: |
                {"error": "validation_failed", "fields": {"email": "already exists"}}
          mock_entity: "User"
```

Agent 執行完成後，主 Claude 解析輸出的 `API_EXPLORER_SPEC` 供後續 Step 2-B 使用。

---

## Step 2：Prototype 生成 — 多專家並行實作

用 **Agent tool** 派送「Prototype Generation Subagent」，包含以下 5 個內建專家角色：

### Prototype Generation Subagent Prompt

```
你是 Prototype Engineering Team，由以下 5 位專家協作：

1. **UX Flow Architect（使用者流程架構師）**
   職責：設計導覽結構、路由邏輯、畫面間的過渡關係
   
2. **UI Visual Engineer（介面視覺工程師）**
   職責：實作設計 token（色彩/字型/間距）、組件樣式、視覺層次
   
3. **Frontend Interaction Engineer（前端互動工程師）**
   職責：表單互動、按鈕狀態、動態列表、模態框、載入狀態
   
4. **Animation & VFX Engineer（動畫特效工程師）**
   職責：CSS/JS 動畫、Canvas 粒子效果、Shader 視覺效果、轉場動畫
   
5. **Audio Implementation Engineer（音效實作工程師）**
   職責：Web Audio API、BGM 管理、SFX 觸發、iOS 解鎖機制

**輸入規格：**
{PROTOTYPE_SPEC}  ← Step 1 輸出的完整規格

**輸出目標：** docs/pages/prototype/ 目錄下的完整可運行 Prototype

**實作標準（Iron Law — 不得違反）：**
- 所有 Screen 必須覆蓋 PROTOTYPE_SPEC.screens 中的每一個
- 設計 token 必須使用 PROTOTYPE_SPEC.design_tokens 中的確切值
- 所有 P0/P1 動畫必須實作（不得省略為靜態）
- 音效必須在指定事件上觸發（不得靜默）
- 導覽必須可點擊（不得有死結畫面）
- Mock data 必須擬真（不得使用 Lorem ipsum 或空表格）

---

### 執行步驟

**Step G-1: 建立目錄結構**

```bash
mkdir -p docs/pages/prototype/assets
```

**Step G-2: 寫入 prototype.css（設計系統）**

使用 Write 工具寫入 `docs/pages/prototype/assets/prototype.css`：

- CSS custom properties 對應 PROTOTYPE_SPEC.design_tokens
- 基礎重設（*, box-sizing）
- Typography scale（h1~h6, p, code）
- 元件樣式（Button variants: primary/secondary/danger/ghost）
- 表單元件（input/select/checkbox/radio）
- Card 組件
- Modal/Dialog 組件
- Navigation 組件（側欄/頂欄）
- Loading/Skeleton 狀態
- 動畫 keyframes（fade-in, slide-up, slide-in-right, scale-pop, shake）
- 遊戲專用樣式（若 render_mode=canvas/webgl）
- RWD breakpoints（依 EDD 目標平台）

**Step G-3: 寫入 mock-data.js**

使用 Write 工具寫入 `docs/pages/prototype/assets/mock-data.js`：
- 基於 PROTOTYPE_SPEC.mock_data，生成擬真的示範資料
- 每個 entity 至少 5~10 筆記錄
- 資料符合 SCHEMA.md 結構（如有）

**Step G-4: 寫入 audio-engine.js（若有 AUDIO 規格）**

若 PROTOTYPE_SPEC.audio 非空，使用 Write 工具寫入 `docs/pages/prototype/assets/audio-engine.js`：

```javascript
// audio-engine.js — Web Audio API 引擎
// 基於 AUDIO.md 實作

class AudioEngine {
  constructor() {
    this.ctx = null;
    this.buffers = {};
    this.bgmSource = null;
    this.bgmGain = null;
    this.sfxGain = null;
    this.unlocked = false;
  }

  // iOS/Chrome 首次點擊解鎖（AUD-T-005 必備）
  async unlock() { ... }

  // BGM 管理
  async playBGM(id, { loop = true, fadeIn = 500 } = {}) { ... }
  stopBGM({ fadeOut = 500 } = {}) { ... }
  
  // SFX 觸發
  async playSFX(id, { volume = 1.0 } = {}) { ... }

  // 從 PROTOTYPE_SPEC 中的 BGM/SFX 清單生成事件綁定
  bindEvents(screenId) { ... }
}

// 依 AUDIO.md 規格生成所有 BGM/SFX 觸發對應表
const AUDIO_MAP = {
  bgm: { /* BGM-001: 觸發畫面 */ },
  sfx: { /* SFX-001: onClick:btn-submit */ }
};

export const audioEngine = new AudioEngine();
```

**Step G-5: 寫入 fx-engine.js（若有 ANIM 規格）**

若 PROTOTYPE_SPEC.animations 非空，使用 Write 工具寫入 `docs/pages/prototype/assets/fx-engine.js`：

```javascript
// fx-engine.js — 動畫特效引擎
// 基於 ANIM.md P0/P1 動畫規格實作

class FXEngine {
  // 畫面進場動畫
  animateScreenEnter(screenEl, animSpec) { ... }

  // 粒子效果（Canvas-based，依 ANIM.md §5 規格）
  createParticleEffect(config) { ... }

  // Tween 動畫（依 ANIM.md §4 緩動規格）
  tween(target, from, to, { duration, easing } = {}) { ... }

  // 骨骼/幀動畫模擬（CSS sprite 或 Canvas）
  playFrameAnimation(element, frames, fps) { ... }

  // 轉場效果
  transition(fromScreen, toScreen, type = 'fade') { ... }
}

export const fxEngine = new FXEngine();
```

**Step G-6: 寫入 prototype.js（路由 + 互動核心）**

使用 Write 工具寫入 `docs/pages/prototype/assets/prototype.js`：

```javascript
// prototype.js — 客戶端路由 + 互動邏輯
// 畫面清單來自 PROTOTYPE_SPEC.screens

class PrototypeRouter {
  constructor() {
    this.screens = {};     // { id: HTMLElement }
    this.current = null;
    this.history = [];
  }

  register(id, renderFn) { ... }
  navigate(id, { replace = false } = {}) { ... }
  back() { ... }
  init() { ... }  // 讀取 URL hash 決定初始畫面
}

// === 畫面渲染函式（每個 Screen 一個 renderXxx() 函式）===
// 依 PROTOTYPE_SPEC.screens 逐一生成

function renderScreen01() {
  return `
    <div class="screen" id="screen-01">
      <!-- 100% 擬真的 HTML 結構，對應 PRD User Story N -->
      <!-- 含真實的 mock data 從 mock-data.js 取用 -->
      <!-- 所有 click handler 綁定到 router.navigate() -->
    </div>
  `;
}

// ...依此類推，每個畫面一個函式

// === 初始化 ===
const router = new PrototypeRouter();
// 依 PROTOTYPE_SPEC.screens 注冊所有畫面
router.init();
```

**Step G-7: 寫入 index.html（主殼層）**

使用 Write 工具寫入 `docs/pages/prototype/index.html`：

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{APP_NAME}} — Interactive Prototype</title>
  <link rel="stylesheet" href="assets/prototype.css">
  <!-- Mermaid（若需要流程圖） -->
</head>
<body>

<!-- Prototype Shell -->
<div id="proto-shell">
  <!-- 頂部導覽列：含 文件站回首頁、"流程地圖" + 目前畫面 breadcrumb + 返回按鈕 -->
  <nav id="proto-nav">
    <a href="../index.html" class="proto-back-docs">← 文件站</a>
    <button onclick="router.back()">← 返回</button>
    <span id="proto-breadcrumb"></span>
    <button onclick="showFlowMap()">📍 流程地圖</button>
  </nav>

  <!-- 畫面容器 -->
  <main id="proto-content"></main>

  <!-- 流程地圖 Modal（展示所有 Screen 的 DAG） -->
  <div id="flow-map-modal" class="modal" style="display:none">
    <div class="modal-content">
      <h2>使用者流程地圖</h2>
      <!-- 所有 Screen 的網格，可點擊直接跳轉 -->
      <div id="screen-grid"></div>
    </div>
  </div>

  <!-- Audio Unlock 浮動按鈕（iOS 相容） -->
  <button id="audio-unlock-btn" style="display:none" onclick="audioEngine.unlock()">
    🔊 開啟音效
  </button>

  <!-- FX Canvas（粒子效果，fixed 定位） -->
  <canvas id="fx-canvas" style="position:fixed;top:0;left:0;pointer-events:none;z-index:999"></canvas>
</div>

<script type="module">
  import { audioEngine } from './assets/audio-engine.js';
  import { fxEngine } from './assets/fx-engine.js';
  import mockData from './assets/mock-data.js';
  // prototype.js 包含所有 Screen 渲染函式 + Router
</script>
<script src="assets/prototype.js"></script>
</body>
</html>
```

**品質要求（生成後自我驗證）：**
- [ ] docs/pages/prototype/index.html 存在且可在 file:// 開啟
- [ ] docs/pages/prototype/assets/prototype.css 含所有 PROTOTYPE_SPEC.design_tokens 的 CSS 變數
- [ ] 每個 PROTOTYPE_SPEC.screens 都有對應的 render 函式
- [ ] 所有 nav_to 連結都有對應的 router.navigate() 呼叫
- [ ] 無任何 Lorem ipsum 或空的 mock 資料表格
- [ ] 若有 AUDIO 規格，audio-engine.js 已建立且 SFX 事件已綁定
- [ ] 若有 ANIM 規格，fx-engine.js 已建立且 P0 動畫已實作
- [ ] 流程地圖 Modal 可開啟，顯示所有 Screen 名稱並可點擊

完成後輸出：
PROTOTYPE_GEN_RESULT:
  screens_generated: N
  has_audio: true|false
  has_animations: true|false
  render_mode: "dom|canvas|webgl"
  files:
    - docs/pages/prototype/index.html
    - docs/pages/prototype/assets/prototype.css
    - docs/pages/prototype/assets/prototype.js
    - docs/pages/prototype/assets/mock-data.js
    - docs/pages/prototype/assets/audio-engine.js  # 若有
    - docs/pages/prototype/assets/fx-engine.js      # 若有
  summary: "生成了 N 個畫面的 Prototype，涵蓋 M 個使用者流程..."
```

> **若 `_PROTO_MODE=ui`**：完成後跳至 Step 3（Review）。
> **若 `_PROTO_MODE=api-explorer`**：跳過本 Step，執行 Step 2-B。
> **若 `_PROTO_MODE=full`**：本 Step 完成後繼續執行 Step 2-B，兩者都生成。

---

## Step 2-B：API Explorer 生成（僅 api-explorer / full 模式）

**`_PROTO_MODE` 為 `api-explorer` 或 `full` 時執行。**

**Step 2-B 前置：主 Claude 計算 API.md endpoint 總數（派送 subagent 前必須執行）**

```bash
_TOTAL_EP=$(python3 - <<'PYEOF'
import re, sys
try:
    content = open('docs/API.md', encoding='utf-8').read()
    # 掃描各種 API.md 常見格式：
    #   `GET /path`  /  **GET** /path  /  行首 GET /path  /  table | GET |
    endpoints = set()
    for m in re.finditer(
        r'`(GET|POST|PUT|PATCH|DELETE)\s+(/[^`\s\n]+)',
        content
    ):
        endpoints.add((m.group(1), m.group(2).rstrip('`').rstrip(',')))
    for m in re.finditer(
        r'\*\*(GET|POST|PUT|PATCH|DELETE)\*\*\s+`?(/[^\s`\n,]+)',
        content
    ):
        endpoints.add((m.group(1), m.group(2)))
    for m in re.finditer(
        r'(?m)^(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s\n]+)',
        content
    ):
        endpoints.add((m.group(1), m.group(2)))
    print(len(endpoints) if endpoints else 'unknown')
except Exception as e:
    print('unknown')
PYEOF
)
echo "[Step 2-B] API.md endpoint 計數：${_TOTAL_EP}"
```

**主 Claude 將 `${_TOTAL_EP}` 嵌入以下 subagent prompt 中的 `{_TOTAL_EP}` 佔位符，再派送。**

用 **Agent tool** 派送「API Explorer Generation Subagent」：

```
你是 API Explorer Engineer，任務是從 docs/API.md 生成一個完整可使用的
API Explorer HTML，儲存至 docs/pages/prototype/api-explorer/index.html。
這是一個自給自足的單一 HTML 檔案（inline CSS + JS），不依賴任何本地框架，
用 JavaScript 模擬 API 回應——使用者試打時不需要真實 server。

**⚠️ 覆蓋率強制要求：docs/API.md 共有 {_TOTAL_EP} 個 HTTP endpoint。
SPEC.groups[].endpoints 必須包含全部 {_TOTAL_EP} 個，一個不得省略（含管理後台 /admin/* 路由）。
生成前先完整讀取 API.md 確認 endpoint 清單，再開始寫 SPEC。**

**生成步驟（不得跳過）：**

Step G-0：讀取規格來源（必須全部讀完，不得略過任何章節）
  - 讀取 docs/API.md（全文）→ 提取全部 HTTP endpoint：method、path、params、request_body、responses
  - 若存在，讀取 docs/SCHEMA.md → 提取 Entity 定義（用於 MOCK_DB 擬真資料）
  - 若存在，讀取 docs/EDD.md → 提取 base_url + 認證方式
  - 讀完後統計找到的 endpoint 總數；若 < {_TOTAL_EP} 則繼續讀取直到找齊

Step G-1：建立目錄
  mkdir -p docs/pages/prototype/api-explorer/

Step G-2：生成 docs/pages/prototype/api-explorer/index.html

HTML 結構規範（★ Iron Law G：Postman 風格）：

```
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{project_name} — API Explorer</title>
  <style>
    /* 必須包含：
       - CSS 變數（--primary, --success, --error, --warning, --bg, --surface, --border）
       - .sidebar（固定寬度，endpoint 列表）
       - .method-badge（GET/POST/PUT/PATCH/DELETE 各自顏色）
       - .postman-bar（method badge + URL preview + Send 按鈕；水平 flex 排列）
       - .req-tabs（tab bar；.tab-btn.active 有底線或背景高亮）
       - .req-tab-content（預設 display:block；.hidden 時 display:none）
       - .param-grid（四欄表格：KEY / VALUE / TYPE / DESC；VALUE 欄有 input）
       - .headers-grid（三欄表格：checkbox / KEY / VALUE）
       - .auth-section（Bearer token input + 顯示/隱藏按鈕）
       - .body-editor（可編輯 textarea；monospace；.invalid 時紅色 border）
       - .resp-panel（response 面板；Send 前 display:none）
       - .resp-topbar（status badge + elapsed ms + Pretty/Raw 切換 + Copy 按鈕）
       - .resp-body（pre 格式化 JSON；深色背景）
       - .resp-status-badge（200-299=綠/400-499=橙/401=紅/500-599=深紅）
       - .possible-responses（<details> 折疊；.resp-item 展開顯示完整 JSON）
       - .enum-chips（可點擊 chips；點擊填入 input + 觸發 URL 預覽）
    */
  </style>
</head>
<body>
  <!-- Top Nav（僅品牌名 + 文件站連結；auth 移至各 endpoint 的 Authorization tab）-->
  <header class="top-nav">
    <span class="brand">{project_name} API Explorer</span>
    <a class="nav-link" href="../../index.html">← 文件站</a>
  </header>

  <div class="layout">
    <!-- Sidebar：endpoint 列表 -->
    <nav class="sidebar">
      <input class="search-input" placeholder="搜尋 endpoint..." oninput="filterEndpoints(this.value)">
      <div id="endpoint-list"></div>
    </nav>

    <!-- Main Panel -->
    <main class="main-panel" id="main-panel">
      <div class="welcome-state">
        <h2>選擇左側 Endpoint 開始試打</h2>
        <p>所有回應均為 JavaScript Mock — 無需啟動後端服務</p>
      </div>
    </main>
  </div>

  <script>
  // ─── API_EXPLORER_SPEC（內嵌）────────────────────────
  // ★ Iron Law A：統一資料模型（禁止 HTML 字串型 responses）
  // responses[] 一律存 JSON 物件；params 有限制時必填 enum[]；
  // 每個 endpoint 標 auth_required（boolean）+ mock_entity（對應 MOCK_DB key）
  //
  // 必須採用此結構：
  // const SPEC = {
  //   base_url: "https://api.example.com",
  //   auth: { type: "bearer", header: "Authorization", placeholder: "Bearer <token>" },
  //   groups: [{
  //     id: "group-id", name: "分組名", color: "#HEX",
  //     endpoints: [{
  //       id: "ep-id", method: "GET|POST|PUT|PATCH|DELETE",
  //       path: "/resource/{id}", summary: "簡述", description: "詳述",
  //       auth_required: true,        // ← 必填
  //       mock_entity: "entityName",  // ← 對應 MOCK_DB key（無實體填 null）
  //       params: [{
  //         name: "id", in: "path|query|header",
  //         type: "string|number|boolean", required: true,
  //         description: "說明",
  //         default: "預設值",  // ← 必填；runTry() 用此值替換 mock response 中的佔位符
  //         enum: ["a","b"]  // ← 有值限制時必填，否則省略
  //       }],
  //       request_body: { /* 典型請求 JSON 物件，非字串 */ },
  //       responses: [{
  //         code: 200, description: "成功",
  //         example: { /* 完整 JSON 物件，禁止 HTML 字串 */ }
  //       }]
  //     }]
  //   }]
  // };

  const SPEC = { /* 依上述結構填入完整資料 */ };

  const MOCK_DB = {
    // ★ Iron Law F：每個 entity ≥ 3 筆擬真資料，涵蓋不同狀態（active/inactive/banned…）
    // mockRequest() 必須：path param 在 MOCK_DB 找不到 → 404
    //                    列表 endpoint 支援 query param 過濾（status/type/rarity…）
  };

  // ─── Mock Engine ─────────────────────────────────────
  function mockRequest(endpointId, params, body, token) {
    const ep = findEndpoint(endpointId);
    // 模擬 250ms 延遲；記錄起始時間以計算 elapsed ms
    // 若 ep.auth_required && !token → 回傳 { code:401, description:'Unauthorized', body:{error:'missing token'} }
    // 根據 params/body 內容決定回傳哪個 response code
    // 使用 MOCK_DB 填充真實資料（列表加分頁、單筆 by id 等）
    return new Promise(resolve => {
      const start = Date.now();
      setTimeout(() => resolve({ response: buildMockResponse(ep, params, body, token), elapsed: Date.now()-start }), 250);
    });
  }

  // ─── Tab 切換 ─────────────────────────────────────────
  function switchTab(epId, tab, btn) {
    // 1. 隱藏所有 id 符合 "tab-*-{epId}" 的 .req-tab-content（加 hidden class）
    // 2. 移除所有同 endpoint 的 .tab-btn 的 active class
    // 3. 顯示 id="tab-{tab}-{epId}" 的 content（移除 hidden）
    // 4. 為 btn 加上 active class
  }

  // ─── URL Preview 即時更新（★ Iron Law D）─────────────
  // 每個 param input 的 keyup / onchange 均觸發 updateUrlPreview(epId)
  //   let url = (SPEC.base_url||'') + ep.path;
  //   ep.params.filter(p=>p.in==='path').forEach(p=>{
  //     const v=document.getElementById(`param-${ep.id}-${p.name}`)?.value;
  //     if(v) url=url.replace(`{${p.name}}`,v);
  //   });
  //   const qs=ep.params.filter(p=>p.in==='query')
  //     .map(p=>{const v=document.getElementById(`param-${ep.id}-${p.name}`)?.value;
  //              return v?`${p.name}=${encodeURIComponent(v)}`:null})
  //     .filter(Boolean).join('&');
  //   if(qs) url+='?'+qs;
  //   document.getElementById(`url-preview-${ep.id}`).textContent=url;
  function updateUrlPreview(epId) { /* 依上述邏輯實作 */ }

  // ─── Enum Chips（★ Iron Law E）──────────────────────
  // params[].enum 存在 → 渲染可點擊 chips：
  //   <div class="enum-chips">
  //     {enum.map(v=>`<span class="chip" onclick="fillParam('${epId}','${p.name}','${v}')">${v}</span>`)}
  //   </div>
  // fillParam(epId, name, val) → 填入 input + updateUrlPreview(epId)

  // ─── renderEndpoint（★ Iron Law G：Postman 風格）─────
  function renderEndpoint(epId) {
    location.hash = 'endpoint-' + epId;

    // 渲染每個 endpoint panel，結構依序如下：
    //
    // ① ep-header：method badge + path + summary + auth badge
    // ② ep-desc：description 描述文字
    //
    // ③ ── Postman Request Bar ─────────────────────────────
    //    <div class="postman-bar">
    //      <span class="method-badge method-{METHOD}">{METHOD}</span>
    //      <div class="url-preview" id="url-preview-{epId}">{SPEC.base_url}{path}</div>
    //      <button class="send-btn" onclick="runTry('{epId}', this)">▶ Send</button>
    //    </div>
    //
    // ④ ── Request Tab Bar ─────────────────────────────────
    //    <div class="req-tabs">
    //      <button class="tab-btn active" onclick="switchTab('{epId}','params',this)">
    //        Params {params.length ? `(${params.length})` : ''}
    //      </button>
    //      <button class="tab-btn" onclick="switchTab('{epId}','auth',this)">Authorization</button>
    //      <button class="tab-btn" onclick="switchTab('{epId}','headers',this)">Headers</button>
    //      {method in ['POST','PUT','PATCH','DELETE'] ?
    //        <button class="tab-btn" onclick="switchTab('{epId}','body',this)">Body</button> : ''}
    //    </div>
    //
    // ⑤ ── Params Tab（預設 active）───────────────────────
    //    <div class="req-tab-content" id="tab-params-{epId}">
    //      <table class="param-grid">
    //        <thead><tr><th>KEY</th><th>VALUE</th><th>TYPE</th><th>DESC</th></tr></thead>
    //        <tbody>
    //          {params.map(p => `
    //            <tr class="${p.required?'required':'optional'}">
    //              <td><span class="pname">${p.name}</span>${p.required?'<span class="req-star">*</span>':''}</td>
    //              <td>
    //                <input id="param-${epId}-${p.name}"
    //                       value="${p.default||''}"
    //                       placeholder="${p.default||p.description||''}"
    //                       onkeyup="updateUrlPreview('${epId}')">
    //                ${p.enum ? enumChipsHtml(epId, p) : ''}   ← ★ Iron Law E
    //              </td>
    //              <td><code class="ptype">${p.in}</code></td>
    //              <td class="pdesc">${p.description||''}</td>
    //            </tr>`
    //          )}
    //        </tbody>
    //      </table>
    //    </div>
    //
    // ⑥ ── Authorization Tab ──────────────────────────────
    //    <div class="req-tab-content hidden" id="tab-auth-{epId}">
    //      <div class="auth-section">
    //        <label>Type: Bearer Token</label>
    //        <div class="auth-row">
    //          <input id="auth-token-{epId}" type="password"
    //                 placeholder="${SPEC.auth.placeholder||'Bearer <token>'}"
    //                 value="${loadAuth()}"
    //                 oninput="saveAuth(this.value)">
    //          <button onclick="toggleAuthVis('${epId}')">👁</button>
    //        </div>
    //        ${!ep.auth_required ? '<p class="auth-note">此端點為公開端點，無需 Token</p>' : ''}
    //      </div>
    //    </div>
    //
    // ⑦ ── Headers Tab ─────────────────────────────────────
    //    <div class="req-tab-content hidden" id="tab-headers-{epId}">
    //      <table class="headers-grid">
    //        <thead><tr><th></th><th>KEY</th><th>VALUE</th></tr></thead>
    //        <tbody id="headers-body-{epId}">
    //          <tr>
    //            <td><input type="checkbox" checked></td>
    //            <td><input value="Content-Type"></td>
    //            <td><input value="application/json"></td>
    //          </tr>
    //          ${ep.auth_required ? `
    //          <tr>
    //            <td><input type="checkbox" checked></td>
    //            <td><input value="Authorization" readonly></td>
    //            <td><input id="auth-header-${epId}"
    //                       placeholder="Bearer <token>"
    //                       value="${loadAuth() ? 'Bearer '+loadAuth() : ''}"></td>
    //          </tr>` : ''}
    //        </tbody>
    //      </table>
    //      <button onclick="addHeaderRow('${epId}')">+ Add</button>
    //    </div>
    //
    // ⑧ ── Body Tab（POST/PUT/PATCH/DELETE 才渲染）────── ★ Iron Law C
    //    <div class="req-tab-content hidden" id="tab-body-{epId}">
    //      <div class="body-toolbar">
    //        <span class="body-type-badge">raw JSON</span>
    //        <button onclick="formatBody('${epId}')">Format</button>
    //        <button onclick="resetBody('${epId}')">Reset</button>
    //      </div>
    //      <textarea class="body-editor" id="body-textarea-{epId}"
    //                spellcheck="false"
    //                oninput="validateJson(this)"
    //                >${JSON.stringify(ep.request_body||{}, null, 2)}</textarea>
    //      <div class="json-error hidden" id="body-error-{epId}"></div>
    //    </div>
    //
    // ⑨ ── Response Panel（▶ Send 前 display:none）─────── ★ Iron Law G
    //    <div class="resp-panel" id="resp-panel-{epId}" style="display:none">
    //      <div class="resp-topbar">
    //        <span class="resp-status-badge" id="resp-status-{epId}"></span>
    //        <span class="resp-time" id="resp-time-{epId}"></span>
    //        <div class="resp-view-toggle">
    //          <button class="active" onclick="setRespView('${epId}','pretty',this)">Pretty</button>
    //          <button onclick="setRespView('${epId}','raw',this)">Raw</button>
    //        </div>
    //        <button class="copy-resp-btn" onclick="copyResp('${epId}')">Copy</button>
    //      </div>
    //      <pre class="resp-body" id="resp-body-{epId}"></pre>
    //    </div>
    //
    // ⑩ ── Possible Responses（靜態，<details> 折疊）──── ★ Iron Law B
    //    <details class="possible-responses">
    //      <summary>Possible Responses</summary>
    //      ${ep.responses.map(r => {
    //        const plain = JSON.stringify(r.example||{}, null, 2);
    //        return `<details class="resp-item">
    //          <summary>
    //            <span class="status-badge">${r.code}</span> ${escapeHtml(r.description||'')}
    //          </summary>
    //          <div class="resp-example-block">
    //            <div class="resp-example-header">
    //              <span>JSON</span>
    //              <button data-copy="${plain.replace(/"/g,'&quot;')}"
    //                      onclick="copyCode(this,this.dataset.copy)">複製</button>
    //            </div>
    //            <pre>${jsonHighlight(plain)}</pre>
    //          </div>
    //        </details>`;
    //      }).join('')}
    //    </details>
  }

  // ─── ▶ Send（★ Iron Law G：從三個 tab 讀取輸入）──────
  // 讀取 Params tab 輸入值、Authorization tab token、Body tab textarea → mockRequest()
  function runTry(epId, btn) {
    const ep = findEndpoint(epId);
    if (!ep) return;
    btn.disabled = true;
    btn.textContent = '⏳ 執行中…';

    // Step 1：從 Params tab 讀取輸入值（id="param-{epId}-{paramName}"）
    const inputVals = {};
    ep.params.forEach(p => {
      const el = document.getElementById(`param-${epId}-${p.name}`);
      inputVals[p.name] = el ? el.value : (p.default ?? '');
    });

    // Step 2：從 Authorization tab 讀取 Bearer token
    const tokenEl = document.getElementById(`auth-token-${epId}`);
    const token = (tokenEl ? tokenEl.value.trim() : '') || loadAuth();

    // Step 3：從 Body tab 讀取 textarea（POST/PUT/PATCH/DELETE）
    let body = null;
    const bodyEl = document.getElementById(`body-textarea-${epId}`);
    if (bodyEl) { try { body = JSON.parse(bodyEl.value); } catch(e) {} }

    // Step 4：呼叫 mockRequest（auth gate：auth_required && !token → 401）
    mockRequest(epId, inputVals, body, token).then(({ response, elapsed }) => {
      btn.disabled = false;
      btn.textContent = '▶ Send';

      // Step 5：更新 Response Panel（顯示 status badge + elapsed ms + formatted JSON）
      const panel = document.getElementById(`resp-panel-${epId}`);
      if (panel) panel.style.display = 'block';
      const statusEl = document.getElementById(`resp-status-${epId}`);
      if (statusEl) {
        statusEl.textContent = `${response.code} ${response.description || ''}`;
        statusEl.className = `resp-status-badge status-${Math.floor(response.code/100)}xx`;
      }
      const timeEl = document.getElementById(`resp-time-${epId}`);
      if (timeEl) timeEl.textContent = `${elapsed}ms`;
      const bodyOutEl = document.getElementById(`resp-body-${epId}`);
      if (bodyOutEl) bodyOutEl.textContent = JSON.stringify(response.body, null, 2);

      renderCurlCommand(epId, inputVals, token);
    });
  }

  // ─── 輔助函式 ─────────────────────────────────────────
  function toggleAuthVis(epId) {
    const el = document.getElementById(`auth-token-${epId}`);
    if (el) el.type = el.type === 'password' ? 'text' : 'password';
  }
  function setRespView(epId, view, btn) {
    // pretty: JSON.stringify(data, null, 2)；raw: JSON.stringify(data)
  }
  function copyResp(epId) {
    const pre = document.getElementById(`resp-body-${epId}`);
    if (pre) navigator.clipboard.writeText(pre.textContent);
  }
  function addHeaderRow(epId) {
    const tbody = document.getElementById(`headers-body-${epId}`);
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.innerHTML = '<td><input type="checkbox" checked></td><td><input placeholder="Key"></td><td><input placeholder="Value"></td>';
    tbody.appendChild(tr);
  }
  function formatBody(epId) {
    const el = document.getElementById(`body-textarea-${epId}`);
    if (!el) return;
    try { el.value = JSON.stringify(JSON.parse(el.value), null, 2); el.classList.remove('invalid'); }
    catch(e) { el.classList.add('invalid'); }
  }
  function resetBody(epId) {
    const ep = findEndpoint(epId);
    const el = document.getElementById(`body-textarea-${epId}`);
    if (ep && el) el.value = JSON.stringify(ep.request_body || {}, null, 2);
  }
  function validateJson(textarea) {
    const errEl = textarea.nextElementSibling;
    try {
      JSON.parse(textarea.value);
      textarea.classList.remove('invalid');
      if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }
    } catch(e) {
      textarea.classList.add('invalid');
      if (errEl) { errEl.textContent = `JSON Error: ${e.message}`; errEl.classList.remove('hidden'); }
    }
  }
  function renderCurlCommand(epId, inputVals, token) {
    // 組建 curl 命令：curl -X {METHOD} '{url}' [-H 'Authorization: Bearer {token}'] [-d '{body}']
    // ★ Copy 按鈕使用 data-copy attribute，禁止 JSON 直接嵌入 onclick attribute
  }

  // ─── Deep Link（hash routing）────────────────────────
  function initHash() {
    const hash = location.hash.slice(1);
    if (hash.startsWith('endpoint-')) renderEndpoint(hash.replace('endpoint-', ''));
  }

  // ─── Auth 持久化 ──────────────────────────────────────
  // 所有 endpoint 的 Authorization tab 共用同一 token（localStorage key: api-explorer-token）
  function saveAuth(token) { localStorage.setItem('api-explorer-token', token); }
  function loadAuth() { return localStorage.getItem('api-explorer-token') || ''; }

  // ─── Endpoint 篩選 ─────────────────────────────────────
  function filterEndpoints(q) {
    // 過濾 sidebar 中的 endpoint 列表（method + path + summary 模糊比對）
  }

  // ─── Init ────────────────────────────────────────────
  renderSidebar();
  initHash();
  </script>
</body>
</html>
```

**Params Tab 控制項規格：**

| 情境 | 控制項 | 說明 |
|------|--------|------|
| 有枚舉值（status: active/inactive/pending）| 快選 Chips + 可輸入 input | chips 點擊 → 填入 input + 觸發 URL 預覽 |
| 有明確格式（email, url, uuid）| input + placeholder 格式提示 | |
| 數值範圍（page ≥ 1）| number input + min 屬性 | |
| 一般字串 | text input + default 預填 | |
| Request Body | Body tab 的可編輯 textarea | 可修改 JSON 後點 ▶ Send 送出 |

**品質要求（生成後自我驗證）：**
- [ ] docs/pages/prototype/api-explorer/index.html 存在且可在 file:// 開啟
- [ ] **[Iron Law A] 資料模型**：`SPEC.groups[].endpoints[].responses[]` 存 JSON 物件（禁 HTML 字串）；params 有限制時含 `enum[]`；**每個 param 必須有 `default` 欄位**（`runTry()` 替換邏輯依賴此值）；每個 endpoint 標 `auth_required` + `mock_entity`
- [ ] **[Iron Law B] Possible Responses 靜態可見**：每個 response code 用 `<details>/<summary>` 渲染 — 不展開可見 code+description，展開可見完整 example JSON + 複製按鈕 — **禁止只顯示 code+description**
- [ ] **[Iron Law C] Request Body 可編輯**：Body tab 有可編輯 `<textarea>`（非唯讀 code block）；JSON keyup 驗證：invalid → red border + 錯誤訊息；Format 按鈕可格式化 JSON
- [ ] **[Iron Law D] URL 預覽**：填入 path/query param 後，Postman Request Bar 中的 URL preview 即時更新
- [ ] **[Iron Law E] Enum Chips**：`params[].enum` 存在 → 在 Params tab 渲染可點擊 chips，點擊填入 input + 觸發 URL 預覽
- [ ] **[Iron Law F] MOCK_DB 覆蓋度**：每個 entity ≥ 3 筆，涵蓋不同狀態；path param 找不到 → 404；列表 endpoint 支援 query param 過濾
- [ ] **[Iron Law G] Postman Layout**：
      - 每個 endpoint panel 有 Postman-style request bar（method badge + URL preview div + ▶ Send 按鈕）
      - Request tab bar：Params | Authorization | Headers | Body（有 request_body 才顯示 Body tab）
      - Params tab：KEY/VALUE/TYPE/DESC 四欄可編輯表格（VALUE 欄有 input，非靜態文字）
      - Authorization tab：id="auth-token-{epId}" password input + 顯示/隱藏切換按鈕 + localStorage 持久化
      - Headers tab：checkbox/KEY/VALUE 三欄表格（Content-Type 預填）+ Add Row 按鈕
      - Body tab（POST/PUT/PATCH/DELETE）：可編輯 textarea + JSON 即時驗證 + Format 按鈕
      - Response panel（id="resp-panel-{epId}"）：Send 前 display:none；Send 後顯示 status badge + elapsed ms + Pretty/Raw 切換 + Copy 按鈕 + formatted JSON
- [ ] 頂部 top-nav **不包含** auth input（auth 在各 endpoint 的 Authorization tab）
- [ ] 所有 endpoint 的 params 均有對應輸入欄位（Params tab 四欄表格中）
- [ ] ▶ Send 按鈕可執行，顯示 ≥200ms 模擬延遲 + mock 回應
- [ ] **`runTry()` 從 Params tab 讀取輸入值（id="param-{epId}-{name}"）、從 Authorization tab 讀取 Bearer token（id="auth-token-{epId}"）、從 Body tab 讀取 textarea** — 禁止只回傳硬編碼 example，使用者改了 input 看到的回應必須反映變更
- [ ] `auth_required: true` endpoint 無 token → mockRequest 回傳 401（auth gate 透過 Authorization tab token 判斷）
- [ ] Response panel 顯示 status code badge（依色：2xx=綠/4xx=橙/5xx=深紅）+ elapsed ms + Pretty/Raw 切換 + formatted JSON
- [ ] **所有 Copy 按鈕使用 `data-copy` attribute 傳遞複製內容，`onclick="copyCode(this, this.dataset.copy)"` 觸發** — **禁止**將 JSON 直接嵌入 `onclick` 屬性；`data-copy` 值需做 `replace(/"/g, '&quot;')` HTML 轉義
- [ ] "Copy" 按鈕複製 response JSON；cURL 指令含 auth header（`-H 'Authorization: Bearer {token}'`）
- [ ] Hash routing 可用：`#endpoint-{id}` 直接開啟對應 endpoint
- [ ] Auth token 持久化（localStorage key: `api-explorer-token`）：重新整理後保留；各 Authorization tab 共用同一 token
- [ ] sidebar 搜尋可過濾 endpoint 列表
- [ ] **[Iron Law H] Endpoint 覆蓋率 = 100%**：`SPEC.groups[].endpoints` 總數必須等於 API.md 中 HTTP endpoint 數量（主 Claude 在派送前已用 Python 計算並嵌入提示，數量為 `{_TOTAL_EP}` 個）；**禁止省略任何 endpoint，包含管理後台 `/admin/*` 路由、GDPR endpoint、health check**；完成後輸出的 `endpoints_generated` 必須等於 `{_TOTAL_EP}`

完成後輸出：
API_EXPLORER_GEN_RESULT:
  endpoints_generated: N
  groups: N
  mock_entities: N
  files:
    - docs/pages/prototype/api-explorer/index.html
  summary: "生成了 N 個 endpoint 的 API Explorer，涵蓋 M 個資源分組..."
```

---

## Step 2-C：Admin Portal Prototype 生成（僅 has_admin_backend=true 時執行）

**`_HAS_ADMIN == "1"` 時執行。**

用 **Agent tool** 派送「Admin Portal Prototype Generation Subagent」：

```
你是 Admin Portal Prototype Engineer，任務是依照 ADMIN_IMPL.md + ARCH.md + API.md（§18 Admin API）
生成 Admin 後台的 HTML Prototype 頁面，儲存至 docs/pages/prototype/admin/ 目錄。

**讀取步驟（不得跳過）：**
1. 讀取 docs/ADMIN_IMPL.md → 提取：
   - RBAC 角色清單（super_admin / operator / auditor 等）
   - 功能模組清單（用戶管理/角色管理/審計日誌/業務管理等）
   - Admin Portal 技術棧（Vue3 + ElementPlus + Vite 預設）
   - 色彩系統（若有 VDD，讀取 Admin 色彩主題）
2. 若存在，讀取 docs/ARCH.md §18 Admin Portal Architecture → 提取：C4 架構、RBAC 設計
3. 若存在，讀取 docs/API.md §18 Admin API → 提取：所有 admin endpoint（用於 sidebar 選單 + mock data 對應）
4. 若存在，讀取 docs/PRD.md §19 Admin Backend Requirements → 提取：業務管理模組清單
5. 若存在，讀取 docs/SCHEMA.md → 提取：AdminUser、Role、Permission、AuditLog entity 結構

**生成目標：** docs/pages/prototype/admin/ 目錄下 5 個完整可運行的 Admin Portal HTML 頁面

**執行步驟（不得跳過）：**

Step A-1：建立目錄
```bash
mkdir -p docs/pages/prototype/admin/assets
```

Step A-2：寫入 docs/pages/prototype/admin/assets/admin-style.css
使用 Write 工具寫入完整 CSS（必須包含）：
- CSS 變數（深色 sidebar：--admin-sidebar-bg: #111827；淺色 content；--admin-accent: #2d9ef5）
- Top nav：固定高度 56px，深色背景，含 Logo + 使用者下拉
- Sidebar：固定寬 240px，深色背景，nav items（含 icon slot、active 狀態、hover 效果）
- Content area：使用 `.admin-layout { display: grid; grid-template-columns: var(--sidebar-w) 1fr; }` + `.admin-main { grid-column: 2; }` — **⚠️ 禁止用 `margin-left: var(--sidebar-w)` 替代**。原因：sidebar 使用 `position: fixed` 脫離 grid flow，main 自動占第 1 欄（240px），再加 `margin-left: 240px` 使 computed width = 0，版形完全崩壞。必須用 `grid-column: 2` 明確佔第 2 欄
- Stats card：白色卡片，含標題/數值/趨勢 badge
- Card header heading：`.card-header h2, .card-header h3 { font-size: 14px; font-weight: 600; color: var(--text); }` — **必須同時覆蓋 h2 和 h3**，因為頁面 card header 使用 `<h2>` 語意標籤
- Data table：含 thead（灰底）、tbody zebra stripe、action 列（Edit/Delete 按鈕）
- Permission matrix：grid 佈局，Permission chip（enabled=藍底/disabled=灰底）
- Status badge：active=綠/inactive=灰/locked=紅
- 搜尋列：input + 篩選 select + 清除 button
- Modal overlay：半透明遮罩 + 居中卡片
- Form elements：ElInput 風格 input/select/radio
- Pagination：prev/page numbers/next
- Tag chip：小型 badge，含 role 顏色（super_admin=紫/operator=藍/auditor=灰）

Step A-3：寫入 docs/pages/prototype/admin/assets/admin-mock.js
使用 Write 工具寫入 mock data（不得用 Lorem ipsum）：

```javascript
// admin-mock.js — Admin Portal Mock Data
// 依 ADMIN_IMPL.md 的 RBAC 設計 + SCHEMA.md entity 結構

const ADMIN_MOCK = {
  // 當前登入使用者（super_admin 示範）
  currentUser: {
    id: 1, username: "admin", name: "系統管理員",
    role: "super_admin", mfa_enabled: true, last_login: "2026-05-01 09:23:11"
  },

  // AdminUser 清單（≥8 筆，含不同角色 + 狀態）
  users: [
    { id: 1, username: "admin",    name: "系統管理員", email: "admin@example.com",    role: "super_admin", status: "active",   last_login: "2026-05-01 09:23" },
    { id: 2, username: "alice",    name: "Alice Chen", email: "alice@example.com",    role: "operator",   status: "active",   last_login: "2026-05-01 08:45" },
    { id: 3, username: "bob",      name: "Bob Wang",   email: "bob@example.com",      role: "operator",   status: "active",   last_login: "2026-04-30 17:32" },
    { id: 4, username: "carol",    name: "Carol Liu",  email: "carol@example.com",    role: "auditor",    status: "active",   last_login: "2026-04-29 11:15" },
    { id: 5, username: "dave",     name: "Dave Lee",   email: "dave@example.com",     role: "operator",   status: "inactive", last_login: "2026-04-20 14:00" },
    { id: 6, username: "eve",      name: "Eve Huang",  email: "eve@example.com",      role: "auditor",    status: "active",   last_login: "2026-04-28 10:30" },
    { id: 7, username: "frank",    name: "Frank Zhao", email: "frank@example.com",    role: "operator",   status: "locked",   last_login: "2026-04-15 09:00" },
    { id: 8, username: "grace",    name: "Grace Wu",   email: "grace@example.com",    role: "operator",   status: "active",   last_login: "2026-05-01 07:55" },
  ],

  // Role 清單（含 permissions）
  roles: [
    { id: 1, name: "super_admin", display: "超級管理員", user_count: 1,
      permissions: ["user.list","user.create","user.edit","user.delete","user.lock",
                    "role.list","role.create","role.edit","role.delete","role.assign",
                    "audit.view","audit.export","business.*"] },
    { id: 2, name: "operator",   display: "操作員",     user_count: 5,
      permissions: ["user.list","user.create","user.edit","role.list","business.read","business.write"] },
    { id: 3, name: "auditor",    display: "審計員",     user_count: 2,
      permissions: ["audit.view","audit.export","user.list","role.list"] },
  ],

  // All permissions（module.action 格式）
  permissions: [
    { module: "user",     action: "list",    desc: "查看用戶列表" },
    { module: "user",     action: "create",  desc: "建立用戶" },
    { module: "user",     action: "edit",    desc: "編輯用戶" },
    { module: "user",     action: "delete",  desc: "刪除用戶" },
    { module: "user",     action: "lock",    desc: "鎖定/解鎖用戶" },
    { module: "role",     action: "list",    desc: "查看角色列表" },
    { module: "role",     action: "create",  desc: "建立角色" },
    { module: "role",     action: "edit",    desc: "編輯角色" },
    { module: "role",     action: "delete",  desc: "刪除角色" },
    { module: "role",     action: "assign",  desc: "指派角色給用戶" },
    { module: "audit",    action: "view",    desc: "查看審計日誌" },
    { module: "audit",    action: "export",  desc: "匯出審計日誌 CSV" },
    { module: "business", action: "read",    desc: "查看業務資料" },
    { module: "business", action: "write",   desc: "修改業務資料" },
  ],

  // AuditLog 清單（≥15 筆，含不同操作類型）
  auditLogs: [
    { id: 1,  operator: "admin",  action: "user.create",  target: "grace(id=8)",   ip: "192.168.1.10", ts: "2026-05-01 07:50:22", result: "success" },
    { id: 2,  operator: "admin",  action: "user.lock",    target: "frank(id=7)",   ip: "192.168.1.10", ts: "2026-05-01 07:52:01", result: "success" },
    { id: 3,  operator: "alice",  action: "business.write", target: "order#2341",  ip: "10.0.0.15",   ts: "2026-05-01 08:20:33", result: "success" },
    { id: 4,  operator: "alice",  action: "user.edit",    target: "dave(id=5)",    ip: "10.0.0.15",   ts: "2026-05-01 08:45:12", result: "success" },
    { id: 5,  operator: "admin",  action: "role.assign",  target: "carol→auditor", ip: "192.168.1.10", ts: "2026-05-01 09:01:44", result: "success" },
    { id: 6,  operator: "bob",    action: "user.create",  target: "tmp_user",      ip: "10.0.0.22",   ts: "2026-04-30 16:10:05", result: "failed" },
    { id: 7,  operator: "carol",  action: "audit.export", target: "2026-04 log",   ip: "172.16.0.5",  ts: "2026-04-30 17:00:00", result: "success" },
    { id: 8,  operator: "admin",  action: "user.delete",  target: "tmp_user",      ip: "192.168.1.10", ts: "2026-04-30 18:30:21", result: "success" },
    { id: 9,  operator: "eve",    action: "audit.view",   target: "user audit",    ip: "172.16.0.8",  ts: "2026-04-29 10:15:33", result: "success" },
    { id: 10, operator: "alice",  action: "business.read", target: "report Q1",   ip: "10.0.0.15",   ts: "2026-04-29 11:00:00", result: "success" },
    { id: 11, operator: "admin",  action: "role.create",  target: "reporter",      ip: "192.168.1.10", ts: "2026-04-28 09:30:00", result: "success" },
    { id: 12, operator: "bob",    action: "user.edit",    target: "grace(id=8)",   ip: "10.0.0.22",   ts: "2026-04-28 14:22:11", result: "success" },
    { id: 13, operator: "admin",  action: "role.delete",  target: "reporter",      ip: "192.168.1.10", ts: "2026-04-28 15:00:00", result: "success" },
    { id: 14, operator: "carol",  action: "audit.export", target: "2026-03 log",   ip: "172.16.0.5",  ts: "2026-04-27 16:45:00", result: "success" },
    { id: 15, operator: "alice",  action: "user.create",  target: "new_member",    ip: "10.0.0.15",   ts: "2026-04-27 09:10:00", result: "success" },
  ],

  // Dashboard 統計（用於 admin-dashboard.html）
  stats: {
    total_users: 8, active_users: 6, locked_users: 1,
    total_roles: 3,
    audit_today: 5, audit_month: 47,
    last_refresh: "2026-05-01 09:30"
  },

  // 時序圖表資料（用於 admin-dashboard.html Analytics Charts）
  // 最近 7 天日期標籤（由新到舊）
  chartLabels: ["04-25","04-26","04-27","04-28","04-29","04-30","05-01"],
  // 新增用戶趨勢（每日新增數）
  chartNewUsers:   [1, 0, 2, 3, 1, 0, 1],
  // 操作活躍度（每日 audit log 筆數）
  chartAuditActivity: [2, 1, 4, 5, 3, 2, 5],
  // 【⚠️ 業務指標：子代理讀取 PRD 後替換為實際業務 KPI 名稱與模擬數值】
  // 例如：pet 專案 → 寵物領取數；e-commerce → 訂單量；SaaS → 活躍訂閱數
  chartBizLabel:   "業務活動量",
  chartBizData:    [5, 8, 12, 9, 15, 11, 7],
};
```

★ **Sidebar 共用模板（所有頁面必須逐字複用，禁止自行設計）**

每個 admin 頁面（含任何額外生成的模組頁面）的 sidebar 必須使用以下固定結構，
**class 名稱不得更改**（admin-style.css 只認識這套選擇器）：

```html
<!-- ★ 所有 admin 頁共用 sidebar —— 複製此結構，僅改 active 位置 -->
<nav class="admin-sidebar">
  <div class="sidebar-brand">🛡️ Admin Portal</div>
  <ul class="sidebar-nav">
    <li class="nav-item"><a href="admin-dashboard.html">📊 Dashboard</a></li>
    <li class="nav-item"><a href="admin-users.html">👥 Users</a></li>
    <li class="nav-item"><a href="admin-roles.html">🗝️ Roles</a></li>
    <li class="nav-item"><a href="admin-audit-log.html">📜 Audit Log</a></li>
    <!-- 動態依 ADMIN_IMPL.md 業務模組插入已完成模組；未完成標 disabled -->
    <li class="nav-item disabled" title="Coming Soon"><span>📈 Analytics</span></li>
  </ul>
  <div class="sidebar-footer">
    <div class="sidebar-user">👤 系統管理員</div>
    <button class="logout-btn" onclick="location.href='admin-login.html'">登出</button>
  </div>
</nav>
```

當前頁對應的 `<li>` 加 `active` class：`<li class="nav-item active">`

**絕對禁止的替代寫法（生成即 FAIL）：**
- ❌ `<a class="sidebar-link">` — 扁平連結，admin-style.css 無此選擇器
- ❌ `<div class="admin-logo">` — 錯誤 class，必須是 `sidebar-brand`
- ❌ `<link href="admin.css">` — 檔案不存在；CSS 一律 `href="assets/admin-style.css"`
- ❌ `<link href="../admin-style.css">` — 相對路徑錯誤；必須 `assets/admin-style.css`
- ❌ Dashboard 連結指向 `../../index.html`（docs hub）；必須 `admin-dashboard.html`（同層）

Step A-4：生成 5 個 Admin HTML 頁面（使用 Write 工具分別寫入）

**頁面 1：docs/pages/prototype/admin/admin-login.html**

登入頁：
- 頁面置中卡片（min-height:100vh，深色漸層背景）
- 系統名稱 Logo（大字）
- 帳號欄位（type=text）+ 密碼欄位（type=password，可 toggle 顯示）
- 「記住帳號」checkbox
- 登入按鈕（loading 狀態：點擊後顯示 spinner 300ms → 跳轉至 admin-dashboard.html）
- MFA TOTP 輸入框（6位數字，自動 focus 下一格）
- 錯誤提示文字（紅色，預設隱藏）
- 底部版本資訊（Admin Portal v1.0）
- 示範帳號提示（demo 使用：admin / Admin@2026）
- **頂部固定**：`<a href="../../index.html" class="back-link">← 文件站</a>`（depth=2 from `pages/prototype/admin/`，回 docs hub；登入後也保留此 link 在後續頁面）

**頁面 2：docs/pages/prototype/admin/admin-dashboard.html**

控制台主頁（含 sidebar + 頂部 nav）：
- 頂部 nav：左側 `<a href="../../index.html" class="back-link">← 文件站</a>` + Logo + 右側「系統管理員 (super_admin)」下拉（含「登出」選項 → 返回 admin-login.html）
- 左側 sidebar（固定，含導覽項目 + active 樣式）：
  - 控制台（active）
  - 用戶管理 → admin-users.html
  - 角色管理 → admin-roles.html
  - 審計日誌 → admin-audit-log.html
  - （依 PRD §19.3 業務模組動態插入）
- 主內容區（依序排列）：
  - 標題「控制台」 + 副標「最後更新：{stats.last_refresh}」
  - **Section 1：KPI 統計卡片（grid 2×2，4 張）**
    - 用戶總數 8，↑ 活躍 6 / 鎖定 1
    - 角色數 3
    - 今日操作 5 筆
    - 本月審計 47 筆
  - **Section 2：Analytics Charts（必須生成，不可省略）**
    - `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>` 載入 Chart.js（CDN，file:// 可用）
    - 圖表 row（CSS grid，2 欄，在小螢幕堆疊）：
      - **左：折線圖「新增用戶趨勢（近 7 天）」**
        - x 軸：ADMIN_MOCK.chartLabels（7 個日期）
        - dataset：新增用戶數（ADMIN_MOCK.chartNewUsers）
        - 顏色：#4f46e5（indigo）；fill=true，透明 fillColor
        - Chart.js config：`{ type:'line', options: { responsive:true, plugins:{ legend:{display:false} } } }`
        - `<canvas id="chartNewUsers">`
      - **右：長條圖「操作活躍度（近 7 天）」**
        - x 軸：ADMIN_MOCK.chartLabels
        - dataset：每日審計筆數（ADMIN_MOCK.chartAuditActivity）
        - 顏色：#2d9ef5（blue）
        - Chart.js config：`{ type:'bar', options:{ responsive:true, plugins:{legend:{display:false}} } }`
        - `<canvas id="chartAudit">`
    - **第三張圖（全寬）：「{ADMIN_MOCK.chartBizLabel}（近 7 天）」**
      - ⚠️ 子代理生成前先讀取 docs/PRD.md，找出本專案最重要的業務 KPI（例如：pet 領取數、訂單量、活躍訂閱數等）
      - 將 ADMIN_MOCK.chartBizLabel 替換為實際 KPI 名稱；ADMIN_MOCK.chartBizData 替換為符合業務邏輯的模擬數值
      - 圖表類型：折線圖（顏色 #10b981 綠色）
      - `<canvas id="chartBiz">`
    - ⚠️ Chart.js 必須在 DOMContentLoaded 或頁面 `<body>` 底部初始化（避免 canvas 尚未 render 就取 context）
    - 每張 canvas 包裹在 `.chart-card`（white bg, border-radius, padding, box-shadow）
  - **Section 3：快速操作區**：新增用戶、查看角色、匯出審計日誌（各自 button → 對應頁面）
  - **Section 4：最近操作記錄**（取 auditLogs 前 5 筆）：操作員 / 動作 / 目標 / 時間 / 狀態

**頁面 3：docs/pages/prototype/admin/admin-users.html**

用戶管理（含 sidebar + 頂部 nav）：
- 頁面標題「用戶管理」+ 右側「+ 新增用戶」按鈕（點擊彈出 Modal）
- 搜尋列：關鍵字搜尋 input + 角色篩選 select（全部/super_admin/operator/auditor）+ 狀態篩選（全部/active/inactive/locked）
- 資料表格（來自 ADMIN_MOCK.users，8 筆）：
  - 欄位：ID / 使用者名稱 / 姓名 / Email / 角色（tag chip，各角色不同顏色）/ 狀態 badge / 最後登入 / 操作
  - 操作列：編輯（icon btn）/ 鎖定|解鎖（依狀態）/ 刪除（紅色，二次確認）
- 分頁（1/1，共 8 筆）
- 新增用戶 Modal：
  - 欄位：使用者名稱 / 姓名 / Email / 角色（下拉）/ 初始密碼
  - 確認 / 取消按鈕（確認後 toast「✅ 新增成功」並關閉）

**頁面 4：docs/pages/prototype/admin/admin-roles.html**

角色管理（含 sidebar + 頂部 nav）：
- 頁面標題「角色管理」+ 右側「+ 新增角色」按鈕
- 角色卡片清單（來自 ADMIN_MOCK.roles，3 個角色）：
  - 每張卡片：角色名 / 顯示名 / 用戶數 / 「編輯權限」按鈕
- 權限配置 Panel（點擊「編輯權限」展開）：
  - 依 module 分組（user / role / audit / business）
  - 每個 permission 顯示為 chip（module.action）
  - chip 狀態：當前角色有此權限 → 藍底；無 → 灰底
  - 可 toggle（點擊切換），toggle 後顯示「儲存變更」按鈕
  - 儲存後 toast「✅ 角色權限已更新」
- 新增角色 Modal：角色識別碼 / 顯示名稱 / 描述

**頁面 5：docs/pages/prototype/admin/admin-audit-log.html**

審計日誌（含 sidebar + 頂部 nav）：
- 頁面標題「審計日誌」
- 篩選列：
  - 日期範圍選擇（From / To，input type=date）
  - 操作員篩選 input（關鍵字）
  - 操作類型 select（全部 / user操作 / role操作 / audit操作 / business操作）
  - 查詢按鈕 + 重置按鈕
- 「匯出 CSV」按鈕（點擊後 blob download，含表頭 + 所有 auditLogs 資料）
- 資料表格（來自 ADMIN_MOCK.auditLogs，15 筆）：
  - 欄位：ID / 操作員 / 動作（monospace font）/ 目標 / IP 位址 / 時間 / 結果（success=綠badge/failed=紅badge）
- 分頁（顯示 1-10 筆，第 2 頁含剩餘 5 筆）
- 注意：審計日誌不可刪除、不可修改（無操作欄）

**Sidebar 共用元件規格（所有頁面必須一致 — 3 個 section）：**

所有 5 個 Admin Portal 頁面必須使用**完全相同的** `renderSidebar(active)` 函式，產生固定的 **3 section 結構：主要功能 | 待辦事項 | 工具**。

⚠️ **嚴禁**把「申請審核」放入「主要功能」section（這會造成各頁面 sidebar 結構不一致）：
```
❌ 錯誤：  主要功能（儀表板 / 使用者管理 / 角色權限 / 稽核日誌 / 申請審核）| 工具
✅ 正確：  主要功能（儀表板 / 使用者管理 / 角色權限 / 稽核日誌）| 待辦事項（申請審核 + pending badge）| 工具
```

正確的 `renderSidebar` 骨架（每頁 script 頂層宣告 `const m = ADMIN_MOCK`，函式從 outer scope 取用 `m`）：
```javascript
function renderSidebar(active) {
  const pendingCount = m.applications.filter(a => a.status === 'pending_review').length;
  const items = [
    { id:'dashboard', icon:'📊', label:'儀表板',    href:'admin-dashboard.html' },
    { id:'users',     icon:'👥', label:'使用者管理', href:'admin-users.html' },
    { id:'roles',     icon:'🛡', label:'角色權限',   href:'admin-roles.html' },
    { id:'audit',     icon:'📋', label:'稽核日誌',   href:'admin-audit-log.html' },
  ];
  return `
    ...
    <div class="sidebar-section">
      <div class="sidebar-section-label">主要功能</div>
      ${items.map(i => `<a class="sidebar-item${i.id===active?' active':''}" ...>`).join('')}
    </div>
    <div class="sidebar-section">
      <div class="sidebar-section-label">待辦事項</div>
      <a class="sidebar-item" href="admin-users.html#applications">
        申請審核 ${pendingCount > 0 ? `+ badge(${pendingCount})` : ''}
      </a>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-section-label">工具</div>
      <a href="../index.html" target="_blank">開發者門戶</a>
      <a href="../api-explorer/index.html" target="_blank">API Explorer</a>
    </div>
    ...`;
}
```

**Top Nav 共用元件規格（所有頁面都要用）：**
```html
<header class="admin-topnav">
  <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>
  <span class="topnav-title">Admin Portal</span>
  <div class="topnav-right">
    <span class="current-user">系統管理員 (super_admin)</span>
    <button class="logout-btn" onclick="location.href='admin-login.html'">登出</button>
  </div>
</header>
```

**Iron Law（品質要求 — 生成後自我驗證）：**
- [ ] 5 個 HTML 檔案均存在於 docs/pages/prototype/admin/
- [ ] 所有頁面 sidebar 中當前頁面有 active 樣式
- [ ] 所有 sidebar 連結指向正確相對路徑
- [ ] **所有 4 個非登入頁面的 sidebar 結構完全一致（3 section：主要功能 | 待辦事項 | 工具）**
- [ ] **「申請審核」出現在「待辦事項」section，而非「主要功能」section**
- [ ] **admin-style.css 使用 `.card-header h2, .card-header h3`（不得只有 h3）**
- [ ] admin-login.html 點擊登入 → 跳轉至 admin-dashboard.html
- [ ] admin-dashboard.html 「登出」→ 返回 admin-login.html
- [ ] **admin-dashboard.html 包含 Analytics Charts 區塊**：`<script src="https://cdn.jsdelivr.net/npm/chart.js">` 已載入；3 張 Chart.js 圖表均存在（`id="chartNewUsers"`、`id="chartAudit"`、`id="chartBiz"`）；圖表在 DOMContentLoaded 後初始化；`chartBizLabel` 為業務相關 KPI 名稱（非 placeholder「業務活動量」）
- [ ] admin-users.html 表格有 8 筆擬真資料（非空表格）
- [ ] admin-roles.html 角色卡片有 3 個角色 + 權限 chips 可 toggle
- [ ] admin-audit-log.html 有 15 筆日誌 + CSV 匯出可用
- [ ] 無 Lorem ipsum、無空的 placeholder 欄位
- [ ] 無 JS 語法錯誤（未閉合括號、未定義變數）
- [ ] **所有 `const`/`let` 宣告必須置於立即執行的初始化呼叫（`initTabs()`、`renderPage()` 等）之前** — `const` 不像 `function` 宣告，不會完整 hoist，在呼叫 chain 提前存取 `const` 變數會觸發 Temporal Dead Zone ReferenceError，造成頁面白屏
- [ ] **docs/pages/prototype/admin/index.html 存在**，打開後會 redirect 至 admin-login.html（gen_html.py sidebar 掃描依賴此檔案）
- [ ] **所有 admin HTML 的 `<link>` 必須指向 `assets/admin-style.css`** — 禁止 `admin.css`、`../admin-style.css` 或其他路徑；CSS 不存在 = 整頁無樣式
- [ ] **所有 admin 頁面 sidebar 使用 `.sidebar-brand` + `<ul class="sidebar-nav">` + `<li class="nav-item">` 結構** — 禁止扁平 `<a class="sidebar-link">` 或 `<div class="admin-logo">`；若存在 `class="sidebar-link"` → 立即重生成該頁
- [ ] **Dashboard nav-item 連結指向 `admin-dashboard.html`（同層）**，非 `../../index.html`（docs hub）

Step A-6：生成 docs/pages/prototype/admin/index.html（sidebar 入口）

用 Write 工具寫入以下內容（meta-redirect，不依賴 JS）：
```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="0;url=admin-login.html">
  <title>Admin Portal</title>
</head>
<body>
  <p>Redirecting… <a href="admin-login.html">Admin Portal 登入頁</a></p>
</body>
</html>
```
目的：gen_html.py 掃描 `prototype/<sub>/index.html` 以生成 sidebar Admin 連結；
      內部所有頁面連結（登出 → admin-login.html 等）無需修改。

完成後輸出：
ADMIN_PROTO_GEN_RESULT:
  pages_generated: 5
  files:
    - docs/pages/prototype/admin/index.html
    - docs/pages/prototype/admin/admin-login.html
    - docs/pages/prototype/admin/admin-dashboard.html
    - docs/pages/prototype/admin/admin-users.html
    - docs/pages/prototype/admin/admin-roles.html
    - docs/pages/prototype/admin/admin-audit-log.html
    - docs/pages/prototype/admin/assets/admin-style.css
    - docs/pages/prototype/admin/assets/admin-mock.js
  summary: "生成了 Admin Portal 5 個頁面 Prototype：登入/控制台/用戶管理/角色管理/審計日誌"
```

> **若 `_HAS_ADMIN == "0"`**：跳過本 Step，直接進入 Step 3（Review）。

---

## Step 3：Review → Fix Loop

主 Claude 執行以下 loop（最多 `_MAX_ROUNDS` 輪）：

### Review Subagent Prompt

```
你是 Prototype Quality Auditor，由以下 3 位審查專家組成：

1. **UX Flow Reviewer（使用者流程審查員）**
   — 驗證所有 Screen 均已生成、所有導覽路徑可用

2. **Visual Fidelity Reviewer（視覺保真審查員）**
   — 驗證設計 token 正確套用、無 placeholder 色彩

3. **Technical Quality Reviewer（技術品質審查員）**
   — 驗證 JS 無語法錯誤、音效/動畫邏輯正確

**審查目標（依 _PROTO_MODE 決定）：**

UI Prototype（_PROTO_MODE = ui / full）：
  docs/pages/prototype/index.html
  docs/pages/prototype/assets/prototype.css
  docs/pages/prototype/assets/prototype.js
  docs/pages/prototype/assets/audio-engine.js（若存在）
  docs/pages/prototype/assets/fx-engine.js（若存在）

API Explorer（_PROTO_MODE = api-explorer / full）：
  docs/pages/prototype/api-explorer/index.html

**審查清單：**

### P. UI Prototype 品質審查（_PROTO_MODE = ui / full）

- [ ] P-1: **畫面覆蓋** — 所有 PROTOTYPE_SPEC.screens 的 id 是否都有對應的 render 函式？（UX Flow）
- [ ] P-2: **導覽完整** — 是否所有 nav_to 連結都可點擊且有 router.navigate() 綁定？無死結畫面？（UX Flow）
- [ ] P-3: **流程地圖** — 流程地圖 Modal 是否可開啟，顯示所有 Screen？（UX Flow）
- [ ] P-4: **設計 Token** — prototype.css 是否包含 PROTOTYPE_SPEC.design_tokens 中所有 CSS 變數，且值正確？（Visual）
- [ ] P-5: **Mock Data 擬真** — 所有資料驅動畫面是否顯示擬真資料（≥3 筆），無 Lorem ipsum 或空表格？（Visual）
- [ ] P-6: **互動狀態** — 按鈕/輸入框是否有 :hover、:active、:disabled 視覺狀態？（Visual）
- [ ] P-7: **P0 動畫** — PROTOTYPE_SPEC.animations 中 P0 動畫是否全部實作（不得為靜態）？（Technical）
- [ ] P-8: **音效觸發** — 若有 audio-engine.js，BGM 進入首頁時是否觸發？P0 SFX 事件是否綁定？（Technical）
- [ ] P-9: **iOS 音效解鎖** — 是否有 audio-unlock-btn 或等效的首次點擊解鎖機制？（Technical）
- [ ] P-10: **無 JS 語法錯誤** — prototype.js 和 audio-engine.js 是否無明顯語法錯誤（未閉合的 {}/[]/"，缺少分號，未定義變數）？（Technical）
- [ ] P-11: **回 docs link** — 每個 prototype HTML（含 `prototype/index.html`、`prototype/admin/*.html`、`prototype/api-explorer/index.html`）必須含可解析到 docs index 的 back-link `<a>...← 文件站</a>`，href 由 depth 決定（depth=1 用 `../index.html`，depth=2 用 `../../index.html`）。確認 label 跟 href 對應正確（不可 label 寫文件站但 href 只到 prototype shell）。（UX Flow）

### A. API Explorer 品質審查（_PROTO_MODE = api-explorer / full）

- [ ] A-0.5: **[Admin] index.html 入口** — docs/pages/prototype/admin/index.html 是否存在且 meta-refresh redirect 至 admin-login.html？（gen_html.py sidebar 掃描依賴此檔案）
- [ ] A-0.8: **[Admin Charts] Dashboard 圖表** — admin-dashboard.html 是否包含 Chart.js 折線圖（#chartNewUsers）、長條圖（#chartAudit）、業務 KPI 折線圖（#chartBiz）？chartBizLabel 是否為業務相關 KPI 名稱（非「業務活動量」placeholder）？
- [ ] A-1: **[Iron Law H] Endpoint 覆蓋 = 100%** — SPEC endpoint 總數是否等於 API.md HTTP endpoint 數量？sidebar 是否列出全部 endpoint（含 /admin/* 路由）？可透過 `grep -oP '(GET|POST|PUT|PATCH|DELETE)\s+/[^\s`]+' docs/API.md | wc -l` 驗證；若數量不符，列出缺失的 endpoint path 清單
- [ ] A-2: **[Iron Law F] Mock 擬真** — MOCK_DB 每個 entity 是否有 ≥ 3 筆擬真資料（非 lorem ipsum / placeholder）？path param 找不到 → 是否回傳 404？列表 endpoint 是否支援 query param 過濾？
- [ ] A-3: **[Iron Law E] Enum Chips** — `params[].enum` 存在時是否渲染可點擊 chips？點擊後是否自動填入 input 並更新 URL 預覽？
- [ ] A-4: **[Iron Law C] Request Body 可編輯** — POST/PUT endpoint 的 request body 是否為可編輯 `<textarea>`（非唯讀 code block）？輸入非法 JSON 時是否顯示 red border + 錯誤訊息？
- [ ] A-5: **Try It 可用** — 點擊 Try It 是否顯示 ≥200ms spinner + 顯示 mock response（JSON）？
- [ ] A-6: **Status Code Badge** — response panel 是否顯示正確顏色的 status badge（200=綠/400=橙/401=紅/500=深紅）？
- [ ] A-7: **cURL 複製** — "Copy as cURL" 按鈕是否可用，命令是否包含 auth header（auth 啟用時）？
- [ ] A-8: **Hash Deep Link** — `#endpoint-{id}` 是否可直接開啟對應 endpoint？分享連結是否有效？
- [ ] A-9: **Auth 持久化** — Auth token 是否透過 localStorage 持久化（重新整理後保留）？
- [ ] A-10: **無 JS 語法錯誤** — index.html inline script 是否無明顯語法錯誤？
- [ ] A-11: **[Iron Law A] 資料模型** — `SPEC.responses[]` 是否存 JSON 物件（禁 HTML 字串）？每個 endpoint 是否標 `auth_required` + `mock_entity`？params 有限制時是否含 `enum[]`？**每個 param 是否有 `default` 欄位**（缺少 `default` → `runTry()` 替換失效）？
- [ ] A-12: **[Iron Law B] Possible Responses 靜態可見** — 每個 response code 是否用 `<details>/<summary>` 渲染？不展開可見 code+desc，展開可見完整 example JSON + 複製按鈕？**禁止只顯示 code+description 無 example**
- [ ] A-13: **[Iron Law D] URL 預覽** — 填入 path/query param 後 URL preview 是否即時更新？顯示完整 `METHOD base_url/path?qs=val`？

**完成後輸出（格式嚴格）：**
PROTOTYPE_REVIEW_RESULT:
  round: {N}
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  findings:
    - id: PF-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      file: "docs/pages/prototype/..."
      check_ref: "P-N"
      issue: "具體問題描述"
      fix_guide: "如何修復"
```

### Fix Subagent Prompt

```
你是 Prototype Fix Engineer（Prototype 修復工程師）。

任務：依照 findings 精準修復 Prototype 文件。

本輪 Findings（Round {N}）：
{findings_text}

被修復的文件：
  docs/pages/prototype/index.html
  docs/pages/prototype/assets/prototype.css
  docs/pages/prototype/assets/prototype.js
  docs/pages/prototype/assets/audio-engine.js（若存在）
  docs/pages/prototype/assets/fx-engine.js（若存在）

執行步驟：
1. 讀取每個 finding 對應的 file
2. 精準修復（最小修改原則，只改 finding 指出的位置）
3. CRITICAL + HIGH 必須修復；MEDIUM + LOW 盡力修復
4. 修復後重讀確認

完成後輸出：
PROTOTYPE_FIX_RESULT:
  round: {N}
  fixed:
    - id: PF-{N:02d}
      file: "..."
      action: "具體修復說明"
  unfixed:
    - id: PF-{N:02d}
      reason: "無法修復原因"
  summary: "本輪修復了 N 個 findings..."
```

### Loop 核心邏輯

```python
for round in range(1, max_rounds + 1):
    review_result = spawn_review_agent(round)

    terminate = False
    if review_result.finding_total == 0:
        terminate = True
        terminate_reason = "PASSED — finding = 0"
    elif review_strategy == "tiered" and round >= 6 and \
         (review_result.critical + review_result.high + review_result.medium) == 0:
        terminate = True
        terminate_reason = "PASSED — tiered: CRITICAL+HIGH+MEDIUM = 0"
    elif round >= max_rounds:
        terminate = True
        terminate_reason = f"MAX_ROUNDS = {max_rounds} 已達"

    if review_result.finding_total > 0:
        fix_result = spawn_fix_agent(round, review_result.findings)
    
    # Round summary
    status = "✅ PASS" if review_result.finding_total == 0 else \
             ("⚠️  MAX" if terminate else "🔄 CONT")
    print(f"""
┌─── Prototype Review Round {round}/{max_rounds} ──────────────────────────┐
│  CRITICAL={critical} HIGH={high} MEDIUM={medium} LOW={low}  Total={total}
│  Fix：修復 {fixed} 個 / 殘留 {unfixed} 個
│  {status}  {terminate_reason or '繼續下一輪'}
└────────────────────────────────────────────────────────────────┘""")

    if terminate:
        break
```

---

## Step 3.5：Playwright 實際執行驗證

Review Loop 通過後，用真實瀏覽器驗證 prototype 可運行。**此步驟發現的問題必須修復後才能進入 Step 4。**

### Step 3.5-A：啟動 HTTP Server + 截圖驗證

```bash
_PROTO_PORT=18765
_PROTO_DIR="$(pwd)/docs/pages/prototype"
_SCREENSHOT_DIR="$(pwd)/docs/pages/prototype/assets/screenshots"
mkdir -p "$_SCREENSHOT_DIR"

# 啟動 local HTTP server
python3 -m http.server $_PROTO_PORT --directory "$(pwd)/docs/pages" &
_HTTP_PID=$!
sleep 1

echo "[Playwright] Server started on port $_PROTO_PORT (PID: $_HTTP_PID)"
echo "[Playwright] 開始瀏覽器驗證..."
```

用 **mcp__playwright** 工具執行以下驗證序列：

**1. 開啟首頁，收集 Console Errors**
```
navigate → http://localhost:18765/prototype/index.html
wait 2s（等待 JS 初始化）
取得 console messages → 過濾 type=error 的項目
截圖 → docs/pages/prototype/assets/screenshots/01-home.png
```

**2. 驗證主要導覽（點擊每個 nav 連結）**
```
取得 .nav-item 或 .sidebar__link 或等效導覽元素清單
對每個可見連結：
  click → 等待 500ms → 截圖（02-nav-{n}.png）
  記錄：URL hash 是否改變 + 頁面是否空白
```

**3. 若有 API Explorer（_PROTO_MODE = api-explorer / full）**
```
navigate → http://localhost:18765/prototype/api-explorer/index.html
wait 1s → 截圖（03-api-explorer.png）
點擊第一個 endpoint → wait 500ms → 點擊 Try It 按鈕
wait 1500ms（mock delay）→ 截圖（04-api-try-it.png）
驗證 response panel 是否出現 JSON
```

**4. 關閉 server**
```bash
kill $_HTTP_PID 2>/dev/null || true
```

### Step 3.5-B：判定與修復

收集所有驗證結果，輸出：

```
PLAYWRIGHT_VERIFY_RESULT:
  home_loaded: true|false
  console_errors: N 個（列出每個 error 訊息）
  nav_tested: N 個連結
  nav_broken: N 個（列出哪些 hash 點擊後頁面空白）
  api_explorer_ok: true|false|skipped
  screenshots: [01-home.png, 02-nav-*.png, ...]
  verdict: PASS|FAIL
  issues:
    - severity: CRITICAL|HIGH
      description: "具體問題（如：JS error 'TypeError: router is not defined'）"
      fix_guide: "如何修復"
```

**若 `verdict=FAIL`**：立即派送 Fix subagent 修復所有 CRITICAL/HIGH issue，修復後重跑 Step 3.5-A 驗證，直到 `verdict=PASS` 或修復 3 輪仍失敗（輸出 BLOCKED 並說明殘留問題）。

**若 `verdict=PASS`**：繼續 Step 4。

---

## Step 4：整合 — 更新 README 和 pages/index.html

生成完成後，更新以下兩個檔案：

### Step 4-A：更新 README.md

搜尋 README.md 中的 `## Demo` 或 `## 文件站` 區塊，依 `_PROTO_MODE` 插入對應連結：

**`_PROTO_MODE=ui`**：
```markdown
## Interactive Prototype

| 連結 | 說明 |
|------|------|
| [📱 Interactive Prototype](docs/pages/prototype/index.html) | 可點擊的前端原型（{N} 個畫面，含動畫音效） |
| [📚 文件站](docs/pages/index.html) | 完整工程文件 |
```

**`_PROTO_MODE=api-explorer`**：
```markdown
## API Explorer

| 連結 | 說明 |
|------|------|
| [🔌 API Explorer](docs/pages/prototype/api-explorer/index.html) | 互動式 API 試打介面（{N} 個 endpoint，JavaScript Mock） |
| [📚 文件站](docs/pages/index.html) | 完整工程文件 |
```

**`_PROTO_MODE=full`**：
```markdown
## Interactive Demos

| 連結 | 說明 |
|------|------|
| [📱 UI Prototype](docs/pages/prototype/index.html) | 可點擊的前端原型（{N} 個畫面，含動畫音效） |
| [🔌 API Explorer](docs/pages/prototype/api-explorer/index.html) | 互動式 API 試打介面（{M} 個 endpoint，JavaScript Mock） |
| [📚 文件站](docs/pages/index.html) | 完整工程文件 |
```

若找不到合適區塊，在 README.md 的 `## Quick Start` 之前插入。

### Step 4-B：更新 docs/pages/index.html

在 `index-grid` 卡片群組中，依 `_PROTO_MODE` 插入卡片（置於最前）：

**UI Prototype 卡片（_PROTO_MODE = ui / full）：**
```html
<a class="index-card" href="prototype/index.html" style="border-color: var(--accent); background: linear-gradient(135deg, #eff8ff 0%, #fff 100%);">
  <div class="index-card__icon">📱</div>
  <div class="index-card__title">Interactive Prototype</div>
  <div class="index-card__desc">{N} 個畫面 · 可點擊體驗 · 含動畫音效</div>
</a>
```

**API Explorer 卡片（_PROTO_MODE = api-explorer / full）：**
```html
<a class="index-card" href="prototype/api-explorer/index.html" style="border-color: #10b981; background: linear-gradient(135deg, #ecfdf5 0%, #fff 100%);">
  <div class="index-card__icon">🔌</div>
  <div class="index-card__title">API Explorer</div>
  <div class="index-card__desc">{M} 個 Endpoint · JavaScript Mock · 可試打體驗</div>
</a>
```

**Admin Portal 卡片（_HAS_ADMIN == "1" 時插入）：**
```html
<a class="index-card" href="prototype/admin/index.html" style="border-color: #7c3aed; background: linear-gradient(135deg, #f5f3ff 0%, #fff 100%);">
  <div class="index-card__icon">🛡️</div>
  <div class="index-card__title">Admin Portal Prototype</div>
  <div class="index-card__desc">5 頁面 · RBAC 角色管理 · 審計日誌 · Vue3+ElementPlus 規格</div>
</a>
```

---

## Step 4.8：輸出存在性確認 + 自身補救

```bash
# [R4-C] P-1~P-10 review loop 通過後，git commit 前確認三件套存在
_MISSING_FILES=""
[[ ! -f "docs/pages/prototype/index.html"     ]] && _MISSING_FILES="$_MISSING_FILES index.html"
[[ ! -f "docs/pages/prototype/prototype.css"  ]] && _MISSING_FILES="$_MISSING_FILES prototype.css"
[[ ! -f "docs/pages/prototype/prototype.js"   ]] && _MISSING_FILES="$_MISSING_FILES prototype.js"

if [[ -n "$_MISSING_FILES" ]]; then
  echo "[Step 4.8] 首次確認：缺失檔案：$_MISSING_FILES"
  echo "[Action] 回到 Step 2 重新執行 SPA 生成（第 1 次補救）..."
  # → 重新執行 Step 2（PROTOTYPE_SPEC → SPA 完整輸出）
  _MISSING_V2=""
  [[ ! -f "docs/pages/prototype/index.html"     ]] && _MISSING_V2="$_MISSING_V2 index.html"
  [[ ! -f "docs/pages/prototype/prototype.css"  ]] && _MISSING_V2="$_MISSING_V2 prototype.css"
  [[ ! -f "docs/pages/prototype/prototype.js"   ]] && _MISSING_V2="$_MISSING_V2 prototype.js"
  if [[ -n "$_MISSING_V2" ]]; then
    echo "[FAIL] 補救後仍缺失：$_MISSING_V2"
    echo "       不執行 git commit；不寫入 special_completed['PROTOTYPE']"
    echo "       請手動確認 PRD/PDD 是否含足夠的畫面規格後重試"
    exit 1
  else
    echo "[Step 4.8] ✅ 補救成功，三件套均存在"
  fi
else
  echo "[Step 4.8] ✅ 三件套確認存在（index.html / prototype.css / prototype.js）"
fi
```

---

## Step 5：Git Commit

```bash
_PROTO_SCREENS=$(python3 -c "
import os, glob
count = len([f for f in glob.glob('docs/pages/prototype/*.html')])
print(count)
" 2>/dev/null || echo "?")

_HAS_API_EXPLORER=$([[ -f "docs/pages/prototype/api-explorer/index.html" ]] && echo "1" || echo "0")

git add docs/pages/prototype/ README.md docs/pages/index.html

_ADMIN_SUFFIX=""
[[ "$_HAS_ADMIN" == "1" ]] && _ADMIN_SUFFIX=" + Admin Portal（5 頁面）"

if [[ "$_PROTO_MODE" == "api-explorer" ]]; then
  _MSG="feat(gendoc)[prototype]: 生成 API Explorer（${_PROTO_SCREENS} endpoints）${_ADMIN_SUFFIX}

- 基於 API.md/SCHEMA.md 生成互動式 API 試打介面
- JavaScript Mock 回應：無需啟動後端
- 雙模式參數輸入：Chips 快選 + 自由打值
- Request Body Presets + 可編輯 textarea
- Copy as cURL、Hash Deep Link、Auth 持久化$([ "$_HAS_ADMIN" = "1" ] && echo "
- Admin Portal：登入/控制台/用戶管理/角色管理/審計日誌（含 RBAC + Mock Data）")
- 連結已更新至 README.md 和 docs/pages/index.html"
elif [[ "$_PROTO_MODE" == "full" ]]; then
  _MSG="feat(gendoc)[prototype]: 生成 UI Prototype + API Explorer${_ADMIN_SUFFIX}

- UI：${_PROTO_SCREENS} 個畫面，含導覽路由、Mock Data、動畫音效
- API Explorer：基於 API.md 生成可試打介面，JavaScript Mock 回應$([ "$_HAS_ADMIN" = "1" ] && echo "
- Admin Portal：登入/控制台/用戶管理/角色管理/審計日誌（含 RBAC + Mock Data）")
- 連結已更新至 README.md 和 docs/pages/index.html"
else
  _MSG="feat(gendoc)[prototype]: 生成互動式 HTML Prototype（${_PROTO_SCREENS} 畫面）${_ADMIN_SUFFIX}

- 基於 PRD/PDD/VDD/FRONTEND/AUDIO/ANIM 生成完整可點擊原型
- 包含導覽路由、Mock Data、動畫特效、音效觸發
- 流程地圖 Modal 可全覽所有畫面$([ "$_HAS_ADMIN" = "1" ] && echo "
- Admin Portal：登入/控制台/用戶管理/角色管理/審計日誌（含 RBAC + Mock Data）")
- 連結已更新至 README.md 和 docs/pages/index.html"
fi

git commit -m "${_MSG}

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Step 6：Total Summary

```
╔══════════════════════════════════════════════════════════════════╗
║  gendoc-gen-prototype — Prototype 生成完成                        ║
╠══════════════════════════════════════════════════════════════════╣
║  畫面數量：{N} 個 Screen                                         ║
║  動畫特效：{HAS_ANIM}（P0 動畫 {M} 個）                         ║
║  音效實作：{HAS_AUDIO}（BGM {B} 條 + SFX {S} 個觸發點）         ║
║  Admin Portal：{HAS_ADMIN}（5 頁面：登入/控制台/用戶/角色/審計） ║
║  Review：{rounds} 輪（{strategy}策略，最多 {max_rounds} 輪）     ║
║  終止原因：{terminate_reason}                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  輸出位置：docs/pages/prototype/index.html                        ║
║  Admin Portal：docs/pages/prototype/admin/admin-login.html        ║
║  README 連結：✅ 已更新                                           ║
║  文件站首頁：✅ 已插入 Prototype 卡片                             ║
╚══════════════════════════════════════════════════════════════════╝

🚀 開啟 Prototype：
   file://$(pwd)/docs/pages/prototype/index.html

🛡️  開啟 Admin Portal Prototype：
   file://$(pwd)/docs/pages/prototype/admin/admin-login.html

或在 gendoc-gen-html 生成後透過文件站首頁進入。
```

---

## 附錄 A：各專案類型實作重點

### SaaS / 服務後台
- **Layout**: 側欄 + 頂欄 + 主內容區（三欄 Grid）
- **屏幕**: Dashboard/列表/詳情/表單/設定（5 類典型）
- **互動**: 表格排序/分頁模擬、表單驗證、Modal CRUD
- **動畫**: 側欄收合、頁面載入 Skeleton、Toast 通知

### 遊戲 UI（Cocos / Unity / HTML5）
- **Layout**: 全螢幕 Canvas + HUD 覆蓋層
- **屏幕**: 主選單/遊戲畫面/暫停/結算/商店（典型遊戲流程）
- **互動**: 按鈕點擊音效+震動效果、進場動畫、粒子爆炸
- **渲染**: canvas 元素 + requestAnimationFrame 遊戲迴圈模擬
- **音效**: BGM 即時切換（選單/戰鬥/勝利）、即時 SFX

### 行動 App
- **Layout**: 375px 手機尺寸視窗（含 safe-area）
- **導覽**: Bottom Tab Bar 或 Top Tab
- **互動**: Swipe 手勢模擬（touch events）、Pull-to-refresh 動畫
- **動畫**: iOS/Android 風格轉場（slide-in-right / cross-fade）

---

## 附錄 B：被 gendoc-gen-html 呼叫的整合方式

**gendoc-gen-html Step 5 之後（HTML 生成完成後）**，自動呼叫本 skill：

```
偵測條件：_HAS_FRONTEND = 1（docs/FRONTEND.md 或 docs/PDD.md 存在）
呼叫方式：Skill tool → "/gendoc-gen-prototype"
時機說明：HTML 文件站生成後呼叫，prototype 連結才能正確插入 index.html
```

---

## 附錄 C：常見問題

| 問題 | 原因 | 解決 |
|------|------|------|
| 音效無聲（iOS Safari） | Web Audio Context 未解鎖 | 確認 audio-unlock-btn 存在且 unlock() 在首次點擊後呼叫 |
| 畫面空白 | router.init() 未找到初始 hash | 確認 entry_point=true 的 screen 已正確注冊 |
| 動畫不流暢 | 同時大量 DOM 操作 | 使用 requestAnimationFrame 批次更新，或改用 CSS transform |
| Mock 資料遺失 | mock-data.js 未正確引入 | 確認 `<script src="...">` 順序在 prototype.js 之前 |
| Canvas 模糊 | devicePixelRatio 未處理 | canvas.width = el.clientWidth * window.devicePixelRatio |
