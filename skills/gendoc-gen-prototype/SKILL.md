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
2. 若存在，讀取 docs/PDD.md → 提取：畫面清單（Screen List）、設計決策、UX 流程；★ **特別重要**：從每個 Screen §5 的 `Key Components:` 區塊逐行複製 component 名稱 + States + Props（含 `maxCidrs`/`maxChars`/`count` 等數量限制），原文原樣填入 components 欄位，不得省略、不得歸納
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
      components:
        # ★ 直接從 PDD §5（或 FRONTEND §N）的 Key Components 複製，含 States 與重要 Props
        # 格式：每個 component 必須記錄 name + layout_type + states（若有）+ props_constraints（若有）
        # 例：
        # - { name: "TokenTable", layout_type: "table", states: ["loading","empty","populated"],
        #     columns: ["Token 說明","前綴","Scope","子站","狀態","到期日","Quota","操作"] }
        # - { name: "ExpiryWarningBanner", states: ["hidden","visible"], trigger: "tokens.filter(expiring)" }
        # - { name: "IPWhitelistManager", states: ["view","editing"], props: {maxCidrs: 5} }
        # - { name: "ApplyTokenModal", states: ["step1_purpose","step2_scope","step3_confirm","submitting","success"] }
        # - { name: "RejectModal", props: {maxChars: 200, reason_required: true} }
        # - { name: "MetricCard", props: {count: 4, fields: ["label","value","unit","status"]} }
        - name: "ComponentName"
          layout_type: "table|card|list|modal|form|chart|badge"
          states: []  # 從 PDD Key Components States 欄位複製
          props: {}   # maxCidrs, maxChars, columns 等重要約束
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

**Step 1-B 前置：主 Claude 計算 PATH_LIST 和 _TOTAL_EP（派送 subagent 前必須執行）**

```bash
_PATH_LIST=$(python3 - <<'PYEOF'
import re
try:
    content = open('docs/API.md', encoding='utf-8').read()
    seen = set()
    paths = []
    # 格式1：`GET /path`（backtick heading 格式）
    for m in re.finditer(r'`(GET|POST|PUT|PATCH|DELETE)\s+(/[^`\s\n]+)', content):
        key = (m.group(1), m.group(2).rstrip('`').rstrip(','))
        if key not in seen:
            seen.add(key)
            paths.append(f"{m.group(1)} {m.group(2).rstrip('`').rstrip(',')}")
    # 格式2：**GET** /path（bold 格式）
    for m in re.finditer(r'\*\*(GET|POST|PUT|PATCH|DELETE)\*\*\s+`?(/[^\s`\n,]+)', content):
        key = (m.group(1), m.group(2))
        if key not in seen:
            seen.add(key)
            paths.append(f"{m.group(1)} {m.group(2)}")
    # 格式3：行首 GET /path
    for m in re.finditer(r'(?m)^(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s\n]+)', content):
        key = (m.group(1), m.group(2))
        if key not in seen:
            seen.add(key)
            paths.append(f"{m.group(1)} {m.group(2)}")
    # 格式4：H1-H4 heading 格式（#### GET /path 或 ## POST /path 等）
    for m in re.finditer(r'^#{1,4}\s+(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s\n]+)', content, re.MULTILINE):
        key = (m.group(1), m.group(2).rstrip('`').rstrip(','))
        if key not in seen:
            seen.add(key)
            paths.append(f"{m.group(1)} {m.group(2).rstrip('`').rstrip(',')}")
    print('\n'.join(paths))
except Exception as e:
    print('')
PYEOF
)
_TOTAL_EP=$(echo "$_PATH_LIST" | grep -c '^' 2>/dev/null || echo 'unknown')
echo "[Step 1-B] Python 機械提取完整 endpoint 清單（共 ${_TOTAL_EP} 個）：
${_PATH_LIST}"
```

**主 Claude 將 `${_PATH_LIST}` 和 `${_TOTAL_EP}` 嵌入以下 subagent prompt 中的佔位符，再派送。**

用 **Agent tool** 派送「API Specification Subagent」：

```
你是 API Specification Analyst（資深 API 設計分析師）。
任務：為以下 {_TOTAL_EP} 個 endpoint 補充語義細節，輸出結構化規格
供後續 API Explorer Prototype 生成使用。

**⚠️ endpoint 清單已由主 Claude 預先從 API.md 機械提取，不得新增或刪除任何 endpoint：**
{PATH_LIST}

**讀取步驟（不得跳過）：**
1. 逐一對應上方每個 endpoint，在 docs/API.md 中找到對應段落，提取：
   - params（path/query/header 參數名稱、型別、required、default、enum 值）
   - request_body schema
   - response codes + example JSON（至少 200/成功碼 + 4xx 錯誤碼）
2. 若存在，讀取 docs/SCHEMA.md → 提取 Entity 定義（用於 mock_entity + response examples）
3. 若存在，讀取 docs/EDD.md → 提取：base_url、認證方式（Bearer Token / API Key / OAuth2 / none）
4. 若存在，讀取 docs/PRD.md → 提取：功能分組標籤（用於 endpoint 側欄分組）

**⚠️ 輸出驗證：輸出前計算 endpoint 數量，必須 = {_TOTAL_EP}；不足時補齊上方清單中的遺漏項**

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

Agent 執行完成後，主 Claude 將 Step 1-B 輸出的 `API_EXPLORER_SPEC` 連同 `${_PATH_LIST}` 和 `${_TOTAL_EP}` 一起嵌入 Step 2-B subagent prompt。

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

> **★ 重要前置動作（禁止跳過）**：在開始寫程式碼前，必須逐一確認 PROTOTYPE_SPEC.screens 中每個 screen 的 `components` 欄位，重新閱讀每個 component 的 `layout_type`、`states`、`props`。寫每個 `renderXxx()` 函式時，先列出該 screen 的 Key Components 清單，確認每一個都被實作後再繼續。「沒時間全部做」不是理由 — Iron Law R 全部違反。

> **★ 若 prototype.js 已存在**：先讀取現有實作，評估每個 screen 的實作品質。若已正確實作所有 Key Components，只補充缺漏部分（最小修改），不得整個覆寫後反而變得更簡化。

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
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'none'; img-src 'self' data:; object-src 'none'; base-uri 'self';">
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

**Iron Law Q — Portal 禁止偷賴（6 條硬約束，全部違反 = 必須修復後重新輸出）：**
- [ ] **[Q-1] 禁止硬編碼動態內容**：告警文字、Token 名稱、剩餘天數必須從 mockData 計算動態生成。錯誤示範：`'「物流追蹤監控」Token 將於 <strong>4 天後</strong>到期'`；正確示範：`` `${t.name}` 將於 `${t.expiresInDays}` 天後到期 ``（t 從 tokens.filter(t=>t.expiresInDays<=7) 取）。凡是出現姓名/數字/狀態被硬編碼進模板字串的，一律視為違反。
- [ ] **[Q-2] 禁止 Toast-Only 互動**：filter/sort 選單必須實際過濾資料並重新渲染 DOM（`renderXxx(data.filter(...))` 而非 `showToast('篩選條件已套用')`）；匯出按鈕必須用 `new Blob([csv], {type:'text/csv'})` + `URL.createObjectURL` 觸發真實下載；凡是功能按鈕只 `showToast(...)` 而不操作資料的，一律視為違反。
- [ ] **[Q-3] Method Badge 必須動態計算**：`badge-method-{method}` class 必須由 endpoint 的 method 欄位動態決定（如 `` `badge-method-${ep.method.toLowerCase()}` ``）；禁止硬編碼 `badge-method-get`。
- [ ] **[Q-4] 設定頁面必須有實際功能**：設定畫面（P7 或等效）必須包含 ≥2 個可修改並以 `localStorage` 持久化的設定項目（語言偏好/通知設定/API 預設值等）；禁止設定頁只顯示頭像+Email+登出而無可操作設定。
- [ ] **[Q-5] 輸入欄位必須有驗證**：IP 白名單格式必須驗證 CIDR（`/^\d{1,3}(\.\d{1,3}){3}\/\d{1,2}$/`）；IP 筆數上限必須 enforce（超出上限 → 顯示錯誤，禁止繼續新增）；表單送出前必須驗 required 欄位，禁止無驗證直接 `showToast('已送出')` 假成功。
- [ ] **[Q-6] 多步驟表單必須動態讀 mockData**：Substation 選項必須從 `mockData.substationDefs`（或等效資料源）動態生成 `<option>`，禁止硬編碼選項文字；有效期下拉必須對應 spec 允許的選項（如 30天/60天/90天），禁止無依據硬編碼。

**Iron Law R — 畫面 Key Components 1:1 實作（禁止省略/壓縮）：**

> **★ 重要執行步驟**：在生成每個 `renderXxx()` 函式前，必須重新閱讀 PROTOTYPE_SPEC.screens[N].components，確認所有 Key Components 均被實作。不得依賴記憶跳過此步驟。

- [ ] **[R-1] 佈局型態嚴格照 PROTOTYPE_SPEC.layout_type**：Step 1 從文件讀取並填入 `layout_type` 欄位；生成 renderXxx() 時**只看 layout_type，禁止依 component 名稱猜測**：
  - `layout_type='card'` → 使用 card-grid（`<div class="xxx-card">` 等）；禁止改成 `<table>`
  - `layout_type='table'` → 使用 `<table><thead><tbody>` 結構；columns 欄位列出的每一欄都必須生成 `<th>`/`<td>`；禁止省略任何 column
  - `layout_type='list'` → 使用 `<ul>/<li>` 或等效有序清單結構
  - 若 PROTOTYPE_SPEC 未設定 layout_type：以文件（FRONTEND.md/PDD/PRD）的 Components Used 清單為準 — 名稱含 `Card/Tile` → card；含 `Table/Grid/List` → table/list

- [ ] **[R-2] States 必須實作**：component 有 `states: ["loading","empty","populated"]` 時，render 函式中至少實作 `empty`（空狀態提示）和 `populated`（有資料的完整 HTML）兩個分支；有 `loading` 時需有 spinner 或 skeleton；`states: ["view","editing"]` 的 component（如 IPWhitelistManager）必須有 edit mode 的 HTML + 觸發邏輯。

- [ ] **[R-3] Modal 多步驟分函式**：component `states` 含 `step1_xxx|step2_xxx|...` 格式者，必須為每個 step 建立獨立 render 函式（如 `renderApplyStep1()`、`renderApplyStep2()` 等），由 `wizardState.step` 驅動；禁止把所有 step HTML 塞進一個 renderXxx() 函式用 if-else 切換。

- [ ] **[R-4] IPWhitelistManager 必須可操作**：若任何 screen 包含 `IPWhitelistManager` component，render 函式必須包含：(a) 現有 CIDR 的 `<code>` 顯示列表；(b) `+ 新增 IP` 按鈕；(c) 新增 CIDR 的 `<input>` + CIDR 格式驗證（`/^\d{1,3}(\.\d{1,3}){3}\/\d{1,2}$/`）；(d) 超過 maxCidrs 限制時禁止新增並顯示錯誤。禁止只讀展示。

- [ ] **[R-5] RejectModal 必須有字元計數器**：若任何 screen 包含帶 `maxChars` 的 RejectModal（或等效審批拒絕 Modal），render 函式必須包含：`<textarea maxlength="N" required>`；`<span id="char-count">0/N</span>`；`oninput` 更新計數；提交前 `required` 驗證（reason 為空 → 禁止送出）。

- [ ] **[R-6] MetricCard 陣列：數量與欄位完整**：若 PROTOTYPE_SPEC 某 screen 的 components 包含 MetricCard（或等效的 StatCard/KpiCard）陣列，必須生成與 spec 中列出的**相同數量**的獨立卡片，每張卡片包含 label/value/unit/status 四個欄位；每個 status 對應不同顏色（normal/warning/critical = 綠/橙/紅）；值從 mockData 動態計算，禁止全部硬編碼為相同固定值。

- [ ] **[R-7] 匯出 CSV + JSON 各獨立函式**：若 screen spec 要求 `ExportButton format:'csv'|'json'`，兩種格式必須各有獨立的 Blob 下載函式（`exportAuditCsv()` + `exportAuditJson()`），分別綁定對應按鈕；禁止只實作 CSV 省略 JSON。

- [ ] **[R-8] prototype.js 行數下限**：整個 prototype.js 行數 ≥ 80 × screen_count（最低下限）；每個非空 renderXxx() 函式 ≥ 30 行；含 multi-step modal 時各 step 函式合計 ≥ 100 行；含 filter+pagination table 時相關函式合計 ≥ 80 行。

- [ ] **[R-9] Detail screen 全欄位實作**：若 PROTOTYPE_SPEC 某 screen 為資源詳情頁（token detail / user detail / order detail 等），render 函式必須實作 PROTOTYPE_SPEC.components 中**所有列出的欄位**（包含 status badge、reference ID、timestamp 欄位、badge 陣列如 scope/tag、關聯欄位如 approval method）；禁止只顯示 4 個「最基本」欄位而省略 spec 中的其他欄位。

- [ ] **[R-10] 多層 Quota/Rate 進度條：每層獨立**：若 PROTOTYPE_SPEC 某 component 的 `tiers` 或 `rates` 欄位定義了多個速率上限（例如 per-minute/per-hour/per-day，或 tier-1/tier-2/tier-3），必須為**每個 tier 各生成一條獨立進度條**，每條各自計算百分比並顯示「已用 N / 上限 M」；禁止把所有 tier 壓縮成一行 `N / M (P%)`。

- [ ] **[R-11] Chart component 必須是圖形實作**：若 PROTOTYPE_SPEC 某 component 名稱含 `Chart/Graph/Trend/Usage` 或 type 為 `chart`，render 函式必須使用 SVG 或 HTML5 Canvas 實作可視化圖表（點數 ≥ spec 中 `days` 或 `points` 欄位指定值）；禁止以純文字「近 N 天 XXX 次」替代圖形。

- [ ] **[R-12] Profile/Settings screen 完整使用者資訊**：若 PROTOTYPE_SPEC 某 screen 為 profile/settings，render 函式必須包含 components 中所有列出的使用者屬性（陣列型屬性如 substations/roles/tags 顯示為 badge/tag 列表；時間型屬性如 session expiry 顯示為倒數或格式化時間）；禁止只顯示 email + name 兩欄。

- [ ] **[R-13] Log/History screen：預設 filter + 全欄位 + 全匯出格式**：若 PROTOTYPE_SPEC 某 screen 為 log/audit/history，render 函式必須：(a) 實作 spec 中 `default_filter` 定義的預設篩選條件（如 last_7_days）；(b) `<table>` 包含 spec 中 `columns[]` 的**每一個**欄位，禁止省略；(c) 對 spec 中 `export_formats[]` 列出的每種格式（如 csv/json）各生成獨立的下載函式和按鈕；缺任何一欄或格式 → HIGH。

Iron Law R 任何一項違反 = CRITICAL，必須修復後重新輸出。

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
你是 API Explorer Engineer，任務是從 Step 1-B 提供的規格生成一個完整可使用的
API Explorer HTML，儲存至 docs/pages/prototype/api-explorer/index.html。
這是一個自給自足的單一 HTML 檔案（inline CSS + JS），不依賴任何本地框架，
用 JavaScript 模擬 API 回應——使用者試打時不需要真實 server。

**⚠️ 覆蓋率強制要求（PATH_LIST 硬約束）：**
以下 {_TOTAL_EP} 個 endpoint 必須全部出現在 SPEC.groups[].endpoints 中，一個不得省略：
{PATH_LIST}

**生成步驟（不得跳過）：**

Step G-0：驗證規格完整性並補充細節
  - Step 1-B 已提供完整 API_EXPLORER_SPEC（{_TOTAL_EP} 個 endpoint）
  - 對照上方 PATH_LIST，逐一確認 SPEC 中每個 endpoint 均存在；若有遺漏則讀取 docs/API.md 補齊
  - 若存在，讀取 docs/SCHEMA.md → 補充 MOCK_DB entity 擬真資料
  - 若存在，讀取 docs/EDD.md → 確認 base_url + 認證方式
  - 驗證完成後統計 endpoint 總數；必須等於 {_TOTAL_EP}，不足則補齊後繼續

Step G-1：建立目錄
  mkdir -p docs/pages/prototype/api-explorer/

Step G-2：生成 docs/pages/prototype/api-explorer/index.html

HTML 結構規範（★ Iron Law G：Postman 風格）：

> **⚠️ 強制架構：Single-Workbench（嚴禁 per-endpoint-panel 模式）**
> - 全域唯一一個 `#workbench`；切換 endpoint 時呼叫 `selectEndpoint(id)` 重新渲染 `#req-content`
> - **嚴禁** 為每個 endpoint 生成個別回應 DOM（如 `resp-panel-login`、`resp-body-get-user`）
> - `#resp-panel` 是全域共用的 — Send 前顯示空狀態，Send 後顯示 `#resp-loaded` 內容
> - 此架構已在 `tools/api-explorer/postman-skeleton.html`（骨架）中驗證
> - **生成時必須以 `tools/api-explorer/postman-skeleton.html` 為基底**，替換 `/* INJECT_SPEC_HERE */` 和 `/* INJECT_MOCK_HERE */` 標記區塊

**執行步驟（必須依序，禁止跳過任何一步）：**

```
Step G-2a：Read 骨架（必做，禁止跳過）
  Read ~/.claude/skills/gendoc/tools/api-explorer/postman-skeleton.html
  （本地開發時為 ~/projects/gendoc/tools/api-explorer/postman-skeleton.html）
  ⚠️ 不得從記憶或任何 code block 直接生成 — 必須真正 Read 骨架檔案

Step G-2b：從 API.md 建構 SPEC 物件（用於注入 INJECT_SPEC_HERE）

  ★ 強制前置步驟（禁止跳過）：計算 API.md endpoint 總數
    grep -c "^#### " API.md   → 記為 N_EP_TOTAL
    此數字即為 SPEC.groups[].eps[] 的 element 總和下限
    ⚠️ 禁止「選代表性的 endpoint」— API.md 定義的每一個 endpoint 都必須進 SPEC
    ⚠️ 若 API.md 有 ≥ 30 個 endpoint，必須分多個 groups 組織，每 group 不超過 15 個 ep
    建構完成後驗算：sum(SPEC.groups[].eps[].length) 必須 == N_EP_TOTAL，否則補齊後才繼續

  格式規範：
  - SPEC.groups[]：每個 group 需有 id / name / eps[]
  - SPEC.groups[].eps[]（⚠️ 不是 endpoints[]）
  - 每個 ep 的欄位名稱使用縮寫（骨架 renderSidebar 讀取縮寫欄位）：
    id      → endpoint 唯一識別 ID（字串，用於 selectEndpoint / mockExec switch）
    m       → HTTP method（'GET'/'POST'/'PUT'/'PATCH'/'DELETE'）
    p       → path（'/api/v1/xxx'）
    s       → name / summary（顯示於 sidebar 和 Documentation panel）
    auth    → 驗證格式（見下）
    params  → 參數陣列，每個 param：{ n, in, def, d, required, enum[] }
                n=欄位名稱, in='path'|'query', def=預設值, d=說明
    body    → request body 範例字串（JSON 格式，選填）
    responses → [{ code, description, example }]
  - auth 欄位格式（⚠️ 禁止 auth_required: true/false 舊格式）：
    auth: false                           // 公開端點
    auth: true                            // 需 Bearer Token（簡寫）
    auth: {type:'bearer'}                 // 需 Bearer Token（明確）
    auth: {type:'cookie',cookieName:'x'}  // 需特定 Cookie
    auth: {type:'any'}                    // Bearer 或 Cookie 任一皆可

Step G-2c：從 API.md 建構 mockExec + checkAuth（用於注入 INJECT_MOCK_HERE）
  函式簽名（必須）：
    async function mockExec(ep, up, bodyObj, token, cookieJar = {})
  - 依 ep.id switch 分支實作每個 endpoint 的 mock 邏輯
  - login endpoint：回傳 Set-Cookie（Max-Age>0），renderer 自動存入 cookieJar
  - logout endpoint：回傳 Set-Cookie（Max-Age=0），renderer 自動清除 cookieJar
  - refresh endpoint：auth {type:'cookie',cookieName:'refresh_token'}，驗 jar 中的 refresh_token
  - checkAuth(ep, token, cookieJar) 依 ep.auth 型別驗證 bearer / cookie / any

Step G-2d：字串替換（⚠️ 這是「替換」不是「重寫」）
  取骨架的完整文字內容，執行 **兩次字串替換**：
    替換 1：找到 `/* INJECT_SPEC_HERE */` 到 `/* END_INJECT_SPEC */` 之間的所有內容（含預設空 SPEC）
            → 換成 Step G-2b 建構的 SPEC 宣告（保留首尾 INJECT 標記行）
    替換 2：找到 `/* INJECT_MOCK_HERE */` 到 `/* END_INJECT_MOCK */` 之間的所有內容（含預設 mockExec stub）
            → 換成 Step G-2c 建構的 mockExec 函式（保留首尾 INJECT 標記行）
  ★ 這兩個區塊以外的所有內容（HTML、CSS、JS 函式）必須與骨架完全一致，一個字元都不能改

Step G-2e：Write 輸出
  路徑：docs/pages/prototype/api-explorer/index.html
  ⚠️ 禁止重新生成骨架：輸出內容 = 骨架原文 + 兩處 INJECT 替換，僅此而已
  ⚠️ 禁止將骨架中的 Unicode 字元（▶ ⏳ ⚙ 🍪 等）轉換為 HTML entity（&#9654; 等）
  ⚠️ 禁止重寫 doSend()、renderBodyTab()、initFromHash() 等骨架函式
  驗證：寫入前確認 `btn.textContent = '▶ Send'` 存在（原 Unicode，非 &#9654;）
```

<!--
★ [Iron Law P] 骨架禁止重寫（最高優先級）

╔══════════════════════════════════════════════════════════════════════╗
║ Iron Law P：生成 api-explorer/index.html 必須是字串替換，           ║
║             禁止重新生成整個骨架                                     ║
╚══════════════════════════════════════════════════════════════════════╝

違反表現（以下任一出現即 CRITICAL violation）：
  ✗ doSend()、renderBodyTab()、renderHeadersTab() 等骨架函式被重寫
  ✗ `btn.textContent = '&#9654; Send'`（HTML entity 進入 textContent）
  ✗ `btn.textContent = 'Sending...'`（emoji 被刪除，文字被簡化）
  ✗ renderTestResults() 函式缺失
  ✗ _initFromHash() 函式缺失
  ✗ S._testResults 欄位缺失
  ✗ 6th param reqHeaders = {} 在 mockExec 簽名中缺失
  ✗ endpoint 總數少於 API.md 定義的數量

正確做法（僞代碼）：
  skeleton_content = Read("~/.claude/skills/gendoc/tools/api-explorer/postman-skeleton.html")
  spec_block = build_spec_from_api_md()
  mock_block = build_mockexec_from_api_md()
  output = skeleton_content
    .replace(between("/* INJECT_SPEC_HERE */", "/* END_INJECT_SPEC */"), spec_block)
    .replace(between("/* INJECT_MOCK_HERE */", "/* END_INJECT_MOCK */"), mock_block)
  Write("docs/pages/prototype/api-explorer/index.html", output)
-->

<!--REMOVED: 舊 HTML 模板 code block（原 762-1184 行）已刪除。
AI 執行時必須 Read 骨架檔案，不得使用任何內嵌模板。-->


**Params Tab 控制項規格：**

| 情境 | 控制項 | 說明 |
|------|--------|------|
| 有枚舉值（status: active/inactive/pending）| 快選 Chips + 可輸入 input | chips 點擊 → 填入 input + 觸發 URL 預覽（★ Iron Law E）|
| 有明確格式（email, url, uuid）| input + placeholder 格式提示 | |
| 數值範圍（page ≥ 1）| number input + min 屬性 | |
| 一般字串 | text input + default 預填 | |
| Request Body | Body tab 的可編輯 textarea（★ Iron Law C）| 可修改後點 ▶ Send |

**品質要求（生成後自我驗證）：**
- [ ] docs/pages/prototype/api-explorer/index.html 存在且可在 file:// 開啟
- [ ] **[Iron Law A] 資料模型**：`SPEC.groups[].eps[].responses[]` 存 JSON 物件（禁 HTML 字串）；params 有限制時含 `enum[]`；**每個 param 必須有 `default` 欄位**；每個 ep 的 `auth` 欄位使用物件格式（`false / true / {type:'bearer'} / {type:'cookie',cookieName} / {type:'any'}`，禁止舊格式 `auth_required: true/false`）
- [ ] **[Iron Law B] Possible Responses 靜態可見**：每個 response code 用 `<details>/<summary>` 渲染 — 不展開可見 code+description，展開可見完整 example JSON + 複製按鈕 — **禁止只顯示 code+description**
- [ ] **[Iron Law C] Request Body 可編輯**：Body tab 有可編輯 `<textarea class="body-editor">`（非唯讀 code block）；Beautify 按鈕；JSON 格式驗證
- [ ] **[Iron Law D] URL 預覽**：填入 path/query param 後，`#url-preview` 即時顯示 resolved URL
- [ ] **[Iron Law E] Enum Chips**：`params[].enum` 存在 → Params tab value input 下方渲染可點擊 chips，點擊填入 + 觸發 URL 預覽
- [ ] **[Iron Law F] MOCK_DB 覆蓋度**：每個 entity ≥ 3 筆，涵蓋不同狀態；path param 找不到 → 404；列表 endpoint 支援 query param 過濾
- [ ] **[Iron Law G] Postman Single-Workbench 架構**：
      - **⚠️ 禁止 per-endpoint panels**：不得存在 `resp-panel-{epId}`、`resp-body-{epId}` 等 per-endpoint DOM ID
      - 全域唯一 `#workbench` + `#req-pane` + `#resp-panel`；切換 endpoint 時 `selectEndpoint()` 重新渲染 `#req-content`
      - `#resp-empty` 在 Send 前顯示；`#resp-loaded` 在 Send 後顯示（display:none ↔ flex 切換）
      - **CSP meta tag 必須存在**（見 HTML 結構規範 `<head>` 區段）
      - **SPEC 初始值 `groups: []`**；整個 SPEC 宣告包在 `/* INJECT_SPEC_HERE */` … `/* END_INJECT_SPEC */` 標記中
      - **SPEC endpoint auth 欄位**必須使用 `{type,cookieName}` 物件格式（禁止舊 `auth_required: true/false`）
      - **State 必須包含 `cookieJar: {}`**；`Set-Cookie Max-Age>0` 存入，`Max-Age=0` 刪除
      - **`mockExec` 簽名**：`async function mockExec(ep, up, bodyObj, token, cookieJar = {}, reqHeaders = {})`（必須接受第 6 個參數；`reqHeaders` 為使用者在 Headers tab 手動新增的 key-value 對）
      - **`checkAuth(ep, token, cookieJar)`** 依 `ep.auth` 型別驗證 bearer / cookie / any
      - **Cookie auto-header**：Headers tab Auto-Generated section，jar 非空時自動出現 `Cookie: k=v; ...`
      - **🍪 badge**：app header 顯示 jar 中 cookie 數量，空時隱藏
      - **整個 mockExec 包在 `/* INJECT_MOCK_HERE */` … `/* END_INJECT_MOCK */` 標記中**
      - **Request tab bar**（#req-tabs）：Params | Authorization | Headers | Body | Scripts — 5 個固定 tab
      - **Params tab**：Path Variables 固定列（不可刪）+ Query Params 可新增刪除；每列 checkbox/key/value/desc 四欄可編輯
      - **Authorization tab**：type select（No Auth / Bearer Token / Basic Auth / API Key）+ 對應 input
      - **Headers tab**：user-editable rows + 下方 Auto-Generated section（Content-Type/Authorization/Cookie）
      - **Body tab**（**所有 method 均顯示**，包含 GET/HEAD/OPTIONS）：body type toggle（none/raw/form-data/urlencoded/binary）+ raw → `<textarea class="body-editor">` + Beautify 按鈕；**禁止用 method 白名單（如 `['POST','PUT','PATCH','DELETE']`）在 renderBodyTab() 頭部 early-return 截斷 GET 的渲染** — bodyType='none' 預設值 + "This request does not have a body." 空狀態已足夠；使用者可手動切換到 raw 為任何 method 加 body
      - **Response panel**（`#resp-loaded`）：resp-topbar（status badge + ⏱ elapsed + 📦 size + Copy/Download/Clear/Wrap）
      - **Response tab bar**（#resp-tabs）：Body | Headers (N) | Cookies (N) | Test Results — 4 個固定 tab
      - **Body tab**（response）：Pretty/Raw/Preview/Visualize 四向切換；Pretty → syntax-highlighted JSON；Visualize → JSON-to-table
      - **Headers tab**（response）：Key/Value 兩欄表格，顯示所有 response headers
      - **Cookies tab**（response，★ 必須實作）：Name/Value/Domain/Path/Expires/HttpOnly/Secure/SameSite 八欄表格；HttpOnly/Secure 顯示 ✓（綠色）或 —
      - **Environment Panel**：可編輯 `{{base_url}}`、`{{auth_token}}` 等環境變數；login 成功後自動更新 `auth_token`
      - **Draggable divider**：`#divider` 可上下拖曳調整 req-pane/resp-panel 高度
- [ ] ▶ Send 按鈕可執行，顯示 ≥60ms 模擬延遲 + mock 回應
- [ ] `mockExec()` 回傳值必須包含 `headers`（物件）+ `cookies`（陣列）+ `elapsed`（ms）+ `size`（bytes）
- [ ] `doSend()` 從 `S.params`（url params）+ `S.auth`（token）+ `S.cookieJar`（cookies）+ `S.bodyRaw`（body textarea）讀取輸入；**禁止只回傳硬編碼 example**
- [ ] `ep.auth` 不通過 `checkAuth()` → mockExec 回傳 401
- [ ] sidebar 搜尋可過濾 endpoint 列表（method + path + summary 模糊比對）
- [ ] **[Iron Law M] Body tab 所有 method 均渲染 mode toggles**：`renderBodyTab()` 不得以 method 白名單（如 `!['POST','PUT','PATCH','DELETE'].includes(ep.m)`）在頭部 early-return；模式切換按鈕（none/raw/form-data/urlencoded/binary）必須對所有 method 均渲染；GET/HEAD/OPTIONS 預設 `bodyType='none'` 即可，使用者須能切換到 raw 自行加 body
- [ ] **[Iron Law H] Endpoint 覆蓋率 = 100%**：`SPEC.groups[].endpoints` 總數必須等於 API.md 中 HTTP endpoint 數量（主 Claude 在派送前已用 Python 計算並嵌入提示，數量為 `{_TOTAL_EP}` 個）；**禁止省略任何 endpoint，包含管理後台 `/admin/*` 路由、GDPR endpoint、health check**；完成後輸出的 `endpoints_generated` 必須等於 `{_TOTAL_EP}`
- [ ] **[Iron Law J] Scripts Tab 必須真正執行**：
      - Pre-request script（`S.preScript`）在 `doSend()` 呼叫 `mockExec` 之前，使用 sandboxed `new Function('pm', S.preScript)(pmPreContext)` 執行；執行出錯 → Test Results tab 顯示 `PRE-SCRIPT ERROR: {msg}`
      - Post-response script（`S.postScript`）在 `mockExec` 回傳後立即執行，傳入 `pmPostContext`（含 `response.status`、`response.json()`、`response.headers`、`pm.test(name, fn)`、`pm.expect(val)` 等 Chai-style API）；執行結果累積至 `S._testResults[]`（每筆：`{name, passed, error}`）
      - **禁止** Scripts tab 只是純文字 textarea、`S.preScript`/`S.postScript` 從未真正執行
      - 即使當前 endpoint 的 script 為空，`doSend()` 也必須依序執行「pre-script → mockExec → post-script」三段邏輯，空 script 直接跳過即可
- [ ] **[Iron Law K] Test Results Tab 必須顯示實際執行結果**：
      - 有 post-response script 執行後，Test Results tab 必須顯示每條 `pm.test` 的 Pass（✓ 綠色）/ Fail（✗ 紅色 + 錯誤訊息）結果
      - tab label 顯示計數：`Test Results (2/3)`（passed/total）
      - 無 script 或 script 未執行時才顯示「No test scripts defined.」；**禁止 Test Results 不論 script 是否有內容都顯示此訊息**
- [ ] **[Iron Law L] addEnvVar 必須使用 inline 行編輯，禁止 prompt()**：
      - 新增環境變數使用 inline `<tr>` 插入（`<input>` 或 contenteditable），禁止呼叫 `window.prompt()` 或 `window.confirm()`
      - 每行末尾有刪除按鈕（`<button class="env-del-btn">`），點擊後從 `S.envVars[]` 移除並 re-render
      - 修改環境變數值必須即時觸發 URL 預覽更新（`{{base_url}}` 等變數替換）
- [ ] **[Iron Law N] mockExec 過濾參數必須生效**：
      - 列表型 endpoint（`/admin/tokens`、`/admin/audit-log` 等）的 `mockExec` 分支必須讀取 `up`（URL params）中的過濾參數（如 `status`、`user_id`、`scope`、`page`、`start_date`、`end_date`）並實際過濾 mock 資料，**禁止永遠回傳固定 3 筆資料無視任何參數**
      - 路徑參數（如 `/tokens/{id}/revoke`）在 `up.id`（或對應 key）為空時必須回傳 `404 Not Found`，**禁止用 `up.id || 'default-id'` fallback 靜默接受空 id**
      - 批次操作（approve/reject）對不存在的 entity 必須回傳 `404`；重複操作（對已 active token 再 approve）必須回傳 `409 Conflict`
- [ ] **[Iron Law O] mockExec 必須純函式，副作用走正規管道**：
      - `mockExec` 本身是 `async function`，禁止在其內直接呼叫 `showToast()`、`renderEnvPanel()`、直接修改全域 DOM
      - 需要儲存 auth token：回傳 bResp 的 body 包含 token，**由 post-response script（`S.postScript`）** 使用 `pm.environment.set('auth_token', ...)` 完成；或 mockExec 僅修改 `S.env`（純 state 變更），由 `renderResponse()` 統一觸發 UI 更新
      - Cookie 生命週期（login Set-Cookie / logout Max-Age=0）仍透過 `bResp` 的第 5 個 `cookies` 參數傳回，由 `renderResponse()` 統一寫入/清除 `S.cookieJar`，mockExec 不直接操作 `S.cookieJar`

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

Step A-2.5（Step C-0）：讀取 API.md Entity Schema（寫入 admin-mock.js 前必須執行）

在生成 admin-mock.js 之前，主 Claude 必須先完整讀取 docs/API.md 中所有 Entity 的 response schema：
- 提取每個 Entity 的精確欄位名稱（camelCase）、型別、enum 值（exact casing）
- 記錄下列 Iron Law I 關鍵欄位名稱作為 admin-mock.js 生成的強制約束

**⚠️ Iron Law I — admin-mock.js 欄位必須嚴格對齊 API.md 的 Entity Schema：**
1. **欄位名稱使用 API.md 的 camelCase**：例如 API.md 定義 `petName` → mock 用 `petName`（NOT `name`）；`matchId`（NOT `id`）；`isBanned`（NOT `status`）；`isFlagged`（NOT `flagged`）；`petAId`/`petBId`/`winnerId`（NOT `pet_a`/`pet_b`/`winner`）
2. **Enum 大小寫與 API.md 完全一致**：若 API.md 定義 `LEGENDARY`/`EPIC`/`RARE`/`COMMON` → mock 用 UPPERCASE（NOT `Legendary`/`Epic`）
3. **數值型別 decimal vs 整數**：`winRate`、`deliverySuccessRate` 等 API.md 定義為 decimal (0.0–1.0) 的欄位，mock 必須用 decimal（NOT 整數百分比：0.91 NOT 91）
4. **UUID 格式 ID**：API.md 若使用 UUID 格式 → mock id 欄位用 UUID 格式字串（`"a1b2c3d4-e5f6-7890-abcd-ef1234567890"` NOT `"pet-0001"`）
5. **admin HTML 頁面讀取 ADMIN_MOCK 的欄位名稱，必須與 admin-mock.js 定義一致**（不得在 HTML 裡用 `pet.name` 若 mock 定義為 `pet.petName`）

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
- [ ] **[Iron Law I] admin-mock.js 欄位對齊 API.md Entity Schema（Step C-0 執行後方可生成）：**
  - 欄位名稱使用 API.md camelCase（例：`petName` NOT `name`；`matchId` NOT `id`；`isBanned` NOT `status`；`isFlagged` NOT `flagged`）
  - Enum 大小寫與 API.md 完全一致（例：`LEGENDARY` NOT `Legendary`）
  - decimal 型別欄位（winRate、deliverySuccessRate 等）使用 0.0–1.0（NOT 整數百分比）
  - API.md 使用 UUID 的 entity，mock id 欄位必須使用 UUID 格式字串
  - admin HTML 頁面存取 ADMIN_MOCK 的欄位名稱與 admin-mock.js 定義一致

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

**Iron Law Q — Portal 偷賴審查（與生成側 Q-1~Q-6 一一對應）：**
- [ ] Q-1: **無硬編碼動態內容** — 告警訊息（Token 到期通知等）是否從 mockData 動態計算？是否存在把 Token 名稱或天數直接硬編碼在模板字串裡的程式碼？（搜尋 `<strong>N 天</strong>` 或類似 hardcoded 數字+文字）
- [ ] Q-2: **無 Toast-Only 互動** — filter/sort 選單是否真的過濾資料並重新渲染 DOM？匯出按鈕是否產生真實 Blob 下載？（搜尋 `onchange="showToast` 或 `onclick="showToast`，凡是業務功能只做 showToast 的均為違反）
- [ ] Q-3: **Method Badge 動態** — 是否存在硬編碼 `class="badge-method-get"` 而非動態計算？（搜尋 `badge-method-get`，若出現在靜態模板字串而非動態運算，即違反）
- [ ] Q-4: **設定頁面有實際功能** — 設定畫面是否包含 ≥2 個可修改且用 localStorage 持久化的設定項目？還是只有頭像+Email+登出？
- [ ] Q-5: **輸入有驗證** — IP 白名單是否驗證 CIDR 格式？IP 筆數上限是否實際 enforce？表單是否驗 required 欄位後才 submit？
- [ ] Q-6: **多步驟表單動態讀 mockData** — Substation 選項是否從 `mockData.substationDefs` 動態生成？是否存在硬編碼 `TW_NORTH（台灣北區）` 選項文字？

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
- [ ] A-11: **[Iron Law A] 資料模型** — `SPEC.groups[].eps[].responses[]` 是否存 JSON 物件（禁 HTML 字串）？每個 ep 的 `auth` 欄位是否使用物件格式（`false / true / {type:'bearer'} / {type:'cookie',cookieName} / {type:'any'}`），禁止舊格式 `auth_required: true/false`？params 有限制時是否含 `enum[]`？**每個 param 是否有 `default` 欄位**（缺少 `default` → `runTry()` 替換失效）？
- [ ] A-12: **[Iron Law B] Possible Responses 靜態可見** — 每個 response code 是否用 `<details>/<summary>` 渲染？不展開可見 code+desc，展開可見完整 example JSON + 複製按鈕？**禁止只顯示 code+description 無 example**
- [ ] A-13: **[Iron Law D] URL 預覽** — 填入 path/query param 後 URL preview 是否即時更新？顯示完整 `METHOD base_url/path?qs=val`？
- [ ] A-14: **[Iron Law J] Scripts 真正執行** — `doSend()` 是否在呼叫 `mockExec` 前執行 `S.preScript`（用 `new Function` sandbox）？是否在 `mockExec` 回傳後執行 `S.postScript`？（搜尋 `preScript`/`postScript` — 若只 assign 不執行即違反）`pm.test()` 結果是否累積至 `S._testResults[]`？
- [ ] A-15: **[Iron Law K] Test Results 顯示執行結果** — 有 script 執行後，Test Results tab 是否顯示每條 `pm.test` 的 Pass/Fail？tab label 是否含計數（如 `Test Results (2/3)`）？是否禁止了「永遠顯示 No test scripts defined.」的狀況？
- [ ] A-16: **[Iron Law L] addEnvVar 無 prompt()** — 環境變數新增/編輯是否使用 inline `<input>` 行（而非 `window.prompt()`）？每行是否有刪除按鈕？修改值是否即時更新 URL 預覽？（搜尋 `window.prompt`，出現即違反）
- [ ] A-17: **[Iron Law M] Body tab 所有 method 均有 mode toggles** — GET/HEAD/OPTIONS endpoint 切換到 Body tab 是否能看到 none/raw/form-data/urlencoded/binary 的切換按鈕？還是直接顯示「No body for GET requests」而無任何切換？（搜尋 `renderBodyTab` 內是否存在 `ms.includes` 或 `['POST','PUT','PATCH','DELETE']` 白名單早返，出現即違反）
- [ ] A-18: **[Iron Law N] mockExec 過濾參數生效** — 列表型 endpoint 的 mockExec 分支是否真正讀取 `up.status`/`up.user_id`/`up.page` 等過濾參數？（搜尋對應 switch/if 分支 — 若分支只讀 `up.status` 而忽略其他 8 個過濾 param 即違反）路徑參數空值是否回傳 404 而非 fallback 到 `up.id || 'default-id'`？批次操作重複執行是否回傳 409？
- [ ] A-19: **[Iron Law O] mockExec 純函式** — `mockExec` 函式體內是否存在直接呼叫 `showToast()`/`renderEnvPanel()`/直接寫 DOM？（出現即違反）auth token 儲存是否透過 post-response script 的 `pm.environment.set()` 或僅修改 `S.env`（無 DOM 操作）？Cookie 生命週期是否只透過 `bResp` 第 5 參數傳回？
- [ ] A-20: **[Iron Law P] 骨架未被重寫** — `btn.textContent = '&#9654;` 是否出現在 JS 中？（出現即 CRITICAL：textContent 不解析 HTML entity，導致顯示亂碼）搜尋 `renderTestResults`、`_initFromHash`、`S._testResults`、`reqHeaders = {}` — 四者缺失任一即表示骨架被重新生成而非字串替換；endpoint 總數是否等於 API.md 定義的數量？

**Iron Law R — Key Components 完整性審查（_PROTO_MODE = ui / full）：**
- [ ] R-1: **[Iron Law R-1] 佈局型態照 PROTOTYPE_SPEC.layout_type** — 每個 screen 的 render 函式是否嚴格照 `layout_type` 欄位？`card` → card-grid；`table` → `<table><thead><tbody>` 且所有 `columns[]` 欄位都有對應 `<th>`/`<td>`？（搜尋各 render 函式的 DOM 結構對照 PROTOTYPE_SPEC — 若 layout_type=card 卻生成 `<table>` → CRITICAL；若 layout_type=table 但缺 columns 欄位 → HIGH）
- [ ] R-2: **[Iron Law R-2] States 完整** — 每個有 `states: ["empty","populated"]` 的 component，render 函式中是否有空狀態 HTML（空表格提示或 empty-state div）和有資料狀態 HTML 兩個分支？（搜尋對應 render 函式中是否有 `length === 0` 分支）
- [ ] R-3: **[Iron Law R-3] 多步驟 Modal 分函式** — 若 PROTOTYPE_SPEC 包含含 `step1_xxx|step2_xxx` States 的 modal component，prototype.js 是否有對應的獨立 step 函式（renderApplyStep1/2/3...）？（搜尋 `renderApplyStep` 或等效命名 — 若只有一個大 renderApplyModal 塞所有 step HTML → HIGH）
- [ ] R-4: **[Iron Law R-4] IPWhitelistManager 可操作** — 若 screen 包含 IPWhitelistManager，prototype.js 是否有：「+ 新增 IP」按鈕、新增 input 欄位、CIDR 正規表達式驗證（`/\d+\.\d+\.\d+\.\d+\/\d+/`）、超過 maxCidrs 的錯誤提示？（若只有靜態 IP 列表無任何新增邏輯 → HIGH）
- [ ] R-5: **[Iron Law R-5] RejectModal 字元計數** — 若 screen 包含帶 maxChars 的 RejectModal，prototype.js 中是否有 `<textarea maxlength="N" required>`、字元計數 span、及 `oninput` 更新計數的邏輯？（搜尋 `maxlength` + `char-count` — 缺一 → HIGH）
- [ ] R-6: **[Iron Law R-6] MetricCard 數量與欄位** — 若 PROTOTYPE_SPEC 某 screen 有 MetricCard 陣列，生成的 MetricCard 數量是否與 spec 一致？每張是否含 label/value/unit/status 四欄？值是否從 mockData 動態計算？（搜尋 metric-card class 出現次數對比 spec 定義數量 — 數量不符 → HIGH；全部硬編碼 → MEDIUM）
- [ ] R-7: **[Iron Law R-7] 匯出 CSV + JSON 各獨立** — 若 screen spec 要求兩種格式匯出，prototype.js 是否各有獨立 exportXxx() 函式 + Blob download？（搜尋 export 函式 — 只有一個 → MEDIUM）
- [ ] R-8: **[Iron Law R-8] 行數下限** — prototype.js 行數是否 ≥ 80 × screen_count？（用 wc -l 計算 — 若低於 80 × N → CRITICAL）
- [ ] R-9: **[Iron Law R-9] Detail screen 全欄位** — 詳情頁 render 函式是否包含 PROTOTYPE_SPEC.components 中所有欄位（badge 陣列、時間欄位、關聯屬性）？（對照 PROTOTYPE_SPEC 逐一勾選 — 任何 SPEC 中有但 render 沒有的欄位 → HIGH）
- [ ] R-10: **[Iron Law R-10] 多層速率各獨立進度條** — 若 PROTOTYPE_SPEC 有多 tier quota/rate component，render 是否為**每個 tier 各一條進度條**（含個別 N/M 顯示）？（搜尋 progress bar 數量對比 spec tiers 數量 — 壓縮成一行 → CRITICAL）
- [ ] R-11: **[Iron Law R-11] Chart component 是圖形** — 若 PROTOTYPE_SPEC 有 chart 類型 component，render 是否包含 `<svg` 或 `<canvas`？（搜尋對應 render 函式 — 只有文字無圖形 → CRITICAL）
- [ ] R-12: **[Iron Law R-12] Profile screen 完整使用者屬性** — Profile/Settings render 是否包含 spec 中所有使用者屬性（陣列 → badge list，時間 → 倒數/格式化）？（對照 PROTOTYPE_SPEC.components — 任何缺失 → HIGH）
- [ ] R-13: **[Iron Law R-13] Log screen：filter + 全欄位 + 全匯出格式** — Log/Audit render 是否實作 spec 的 default_filter？`<table>` 是否含 columns[] 每一欄？是否每個 export_format 各有獨立函式 + 按鈕？（任何缺失 → HIGH）

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
