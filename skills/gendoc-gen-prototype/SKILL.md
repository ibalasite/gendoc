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
echo "[proto] MODE=${_PROTO_MODE}  HAS_FRONTEND=${_HAS_FRONTEND}  HAS_API=${_HAS_API}  HAS_AUDIO=${_HAS_AUDIO}  HAS_ANIM=${_HAS_ANIM}"

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
  <!-- 頂部導覽列：含 "流程地圖" + 目前畫面 breadcrumb + 返回按鈕 -->
  <nav id="proto-nav">
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

用 **Agent tool** 派送「API Explorer Generation Subagent」：

```
你是 API Explorer Engineer，任務是依照 API_EXPLORER_SPEC 生成一個完整可使用的
API Explorer HTML，儲存至 docs/pages/prototype/api-explorer/index.html。
這是一個自給自足的單一 HTML 檔案（inline CSS + JS），不依賴任何本地框架，
用 JavaScript 模擬 API 回應——使用者試打時不需要真實 server。

**輸入**：已解析的 API_EXPLORER_SPEC（包含所有 endpoint、mock responses、SCHEMA entities）

**生成步驟（不得跳過）：**

Step G-1：建立目錄
  mkdir -p docs/pages/prototype/api-explorer/

Step G-2：生成 docs/pages/prototype/api-explorer/index.html

HTML 結構規範：

```
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{project_name} — API Explorer</title>
  <style>
    /* 完整 CSS inline，必須包含：
       - CSS 變數（--primary, --success, --error, --warning, --bg, --surface, --border）
       - .sidebar（固定寬度，endpoint 列表）
       - .main-panel（endpoint 詳情 + Try It 面板）
       - .method-badge（GET/POST/PUT/PATCH/DELETE 各自顏色）
       - .response-panel（程式碼顯示區，深色背景）
       - .param-row（參數列）
       - .status-badge（200=綠/400=橙/401=紅/500=深紅）
       - .spinner（試打時的載入動畫）
    */
  </style>
</head>
<body>
  <!-- Top Nav -->
  <header class="top-nav">
    <span class="brand">{project_name} API Explorer</span>
    <div class="auth-section">
      <input id="auth-token" type="text" placeholder="{auth.placeholder}" 
             oninput="saveAuth(this.value)">
      <label><input type="checkbox" id="auth-enabled" checked> 自動帶入 Auth Header</label>
    </div>
    <a class="nav-link" href="../index.html">← 文件站</a>
  </header>

  <div class="layout">
    <!-- Sidebar：endpoint 列表 -->
    <nav class="sidebar">
      <input class="search-input" placeholder="搜尋 endpoint..." oninput="filterEndpoints(this.value)">
      <!-- 依 API_EXPLORER_SPEC.groups 動態生成 -->
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
  // 依 API_EXPLORER_SPEC 生成完整 JS 資料物件，包含：
  // - groups[]（endpoint 分組）
  // - 每個 endpoint 的 id, method, path, summary, params, request_body, responses[]
  // - MOCK_DB：{ entity_name: example_array }（從 SCHEMA entity examples 組裝，≥3 筆）

  const SPEC = { /* 完整 API_EXPLORER_SPEC 資料 */ };

  const MOCK_DB = {
    // 每個 Entity 至少 3 筆擬真範例資料（非 lorem ipsum）
  };

  // ─── Mock Engine ─────────────────────────────────────
  // 依 endpoint id + 使用者填入的參數模擬 API 回應
  function mockRequest(endpointId, params, body) {
    const ep = findEndpoint(endpointId);
    // 模擬 200ms 延遲
    // 若有 auth-enabled 且 auth-token 為空 → 回傳 401
    // 根據 params/body 內容決定回傳哪個 response code
    // 使用 MOCK_DB 填充真實資料（列表加分頁、單筆 by id 等）
    return new Promise(resolve => {
      setTimeout(() => resolve(buildMockResponse(ep, params, body)), 200);
    });
  }

  // ─── 參數表單渲染 ──────────────────────────────────
  // 每個參數渲染成一個 .param-row，含：
  // [必填標記] [參數名] [說明] [輸入控制項]
  //
  // 輸入控制項設計（雙模式）：
  //   若 param.enum 存在（或從 SCHEMA 推斷出枚舉值）：
  //     <datalist id="param-{name}-opts"> + <input list="...">
  //     同時顯示快選 Chips（點擊直接填入）
  //   否則：
  //     單純 <input type="text|number"> + default value 預填
  //
  // Request Body 區塊：
  //   若 endpoint 有 request_body：
  //     顯示 Presets 下拉選單（從 spec 的 request_body examples 組裝）
  //     + 可編輯的 <textarea>（JSON 格式，預設填入第一個 preset）
  //     選 preset 後自動填入 textarea，使用者可繼續修改

  function renderEndpoint(epId) {
    // 更新 URL hash：#endpoint-{epId}（deep link）
    location.hash = 'endpoint-' + epId;
    // 渲染 endpoint 詳情 + 參數表單 + Try It 按鈕 + response 面板
  }

  // ─── Try It ───────────────────────────────────────
  async function tryIt(endpointId) {
    showSpinner();
    const params = collectParams(endpointId);
    const body   = collectBody(endpointId);
    const result = await mockRequest(endpointId, params, body);
    hideSpinner();
    renderResponse(result);
    renderCurlCommand(endpointId, params, body);  // "Copy as cURL" 區塊
  }

  // ─── Deep Link（hash routing）────────────────────
  // 頁面載入時解析 #endpoint-{id} → 自動開啟對應 endpoint
  function initHash() {
    const hash = location.hash.slice(1);
    if (hash.startsWith('endpoint-')) renderEndpoint(hash.replace('endpoint-', ''));
  }

  // ─── Auth 持久化 ─────────────────────────────────
  function saveAuth(token) { localStorage.setItem('api-explorer-token', token); }
  function loadAuth() {
    const t = localStorage.getItem('api-explorer-token');
    if (t) document.getElementById('auth-token').value = t;
  }

  // ─── Endpoint 篩選 ────────────────────────────────
  function filterEndpoints(q) {
    // 過濾 sidebar 中的 endpoint 列表（method + path + summary）
  }

  // ─── Init ────────────────────────────────────────
  renderSidebar();
  loadAuth();
  initHash();
  </script>
</body>
</html>
```

**參數雙模式 UX 規格（必須實作）：**

| 情境 | 控制項 | 說明 |
|------|--------|------|
| 有枚舉值（status: active/inactive/pending）| 快選 Chips + 可輸入 input | chips 點擊 → 填入 input；input 仍可自由打值 |
| 有明確格式（email, url, uuid）| input + placeholder 格式提示 | |
| 數值範圍（page ≥ 1）| number input + min 屬性 | |
| 一般字串 | text input + default 預填 | |
| Request Body | Presets 下拉 + 可編輯 textarea | 選 preset 填入 textarea，可繼續修改後送出 |

**品質要求（生成後自我驗證）：**
- [ ] docs/pages/prototype/api-explorer/index.html 存在且可在 file:// 開啟
- [ ] MOCK_DB 每個 entity 有 ≥ 3 筆擬真資料（非 lorem ipsum）
- [ ] 所有 endpoint 的 params 均有對應輸入欄位
- [ ] 枚舉型參數有 Chips 快選 + 可自由輸入
- [ ] Request Body 有 Presets 下拉 + 可編輯 textarea
- [ ] "Try It" 按鈕可執行，顯示 ≥200ms 模擬延遲 + mock 回應
- [ ] 回應面板顯示 status code badge + formatted JSON
- [ ] "Copy as cURL" 按鈕可用，複製後命令包含 auth header
- [ ] Hash routing 可用：`#endpoint-{id}` 直接開啟對應 endpoint
- [ ] Auth token 持久化（localStorage）：重新整理後保留
- [ ] 無 401 mock（auth 啟用時帶入 token）
- [ ] sidebar 搜尋可過濾 endpoint 列表

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

### A. API Explorer 品質審查（_PROTO_MODE = api-explorer / full）

- [ ] A-1: **Endpoint 覆蓋** — API_EXPLORER_SPEC 所有 endpoint 是否都在 sidebar 列出且可點擊？
- [ ] A-2: **Mock 擬真** — MOCK_DB 每個 entity 是否有 ≥ 3 筆擬真資料（非 lorem ipsum / placeholder）？
- [ ] A-3: **雙模式參數輸入** — 枚舉型參數是否有 Chips 快選 + 可自由打值的 input？非枚舉是否有 default 預填？
- [ ] A-4: **Request Body Presets** — POST/PUT endpoint 是否有 Presets 下拉 + 可編輯 textarea？選 preset 後 textarea 是否自動填入？
- [ ] A-5: **Try It 可用** — 點擊 Try It 是否顯示 ≥200ms spinner + 顯示 mock response（JSON）？
- [ ] A-6: **Status Code Badge** — response panel 是否顯示正確顏色的 status badge（200=綠/400=橙/401=紅/500=深紅）？
- [ ] A-7: **cURL 複製** — "Copy as cURL" 按鈕是否可用，命令是否包含 auth header（auth 啟用時）？
- [ ] A-8: **Hash Deep Link** — `#endpoint-{id}` 是否可直接開啟對應 endpoint？分享連結是否有效？
- [ ] A-9: **Auth 持久化** — Auth token 是否透過 localStorage 持久化（重新整理後保留）？
- [ ] A-10: **無 JS 語法錯誤** — index.html inline script 是否無明顯語法錯誤？

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

if [[ "$_PROTO_MODE" == "api-explorer" ]]; then
  _MSG="feat(gendoc)[prototype]: 生成 API Explorer（${_PROTO_SCREENS} endpoints）

- 基於 API.md/SCHEMA.md 生成互動式 API 試打介面
- JavaScript Mock 回應：無需啟動後端
- 雙模式參數輸入：Chips 快選 + 自由打值
- Request Body Presets + 可編輯 textarea
- Copy as cURL、Hash Deep Link、Auth 持久化
- 連結已更新至 README.md 和 docs/pages/index.html"
elif [[ "$_PROTO_MODE" == "full" ]]; then
  _MSG="feat(gendoc)[prototype]: 生成 UI Prototype + API Explorer

- UI：${_PROTO_SCREENS} 個畫面，含導覽路由、Mock Data、動畫音效
- API Explorer：基於 API.md 生成可試打介面，JavaScript Mock 回應
- 連結已更新至 README.md 和 docs/pages/index.html"
else
  _MSG="feat(gendoc)[prototype]: 生成互動式 HTML Prototype（${_PROTO_SCREENS} 畫面）

- 基於 PRD/PDD/VDD/FRONTEND/AUDIO/ANIM 生成完整可點擊原型
- 包含導覽路由、Mock Data、動畫特效、音效觸發
- 流程地圖 Modal 可全覽所有畫面
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
║  Review：{rounds} 輪（{strategy}策略，最多 {max_rounds} 輪）     ║
║  終止原因：{terminate_reason}                                    ║
╠══════════════════════════════════════════════════════════════════╣
║  輸出位置：docs/pages/prototype/index.html                        ║
║  README 連結：✅ 已更新                                           ║
║  文件站首頁：✅ 已插入 Prototype 卡片                             ║
╚══════════════════════════════════════════════════════════════════╝

🚀 開啟 Prototype：
   file://$(pwd)/docs/pages/prototype/index.html

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
