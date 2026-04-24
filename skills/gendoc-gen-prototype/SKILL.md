---
name: gendoc-gen-prototype
description: |
  從工程文件（PRD/PDD/VDD/FRONTEND/AUDIO/ANIM/SCHEMA）自動生成完整可點擊的 HTML Prototype，
  輸出至 docs/pages/prototype/。100% 擬真還原：前端畫面、導覽流程、動畫特效、音效觸發、色彩配置。
  含 gen→review→fix loop（依 state file 設定），commit，並自動更新 README.md 和 pages/index.html。
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

### Step 0-B：Frontend 需求偵測

```bash
# 掃描現有文件判斷是否有 Frontend 需求
_HAS_FRONTEND=0
_HAS_AUDIO=0
_HAS_ANIM=0
_DOCS_FOUND=""

[ -f "docs/FRONTEND.md" ]  && _HAS_FRONTEND=1 && _DOCS_FOUND="$_DOCS_FOUND FRONTEND.md"
[ -f "docs/PDD.md" ]       && _HAS_FRONTEND=1 && _DOCS_FOUND="$_DOCS_FOUND PDD.md"
[ -f "docs/VDD.md" ]       && _DOCS_FOUND="$_DOCS_FOUND VDD.md"
[ -f "docs/AUDIO.md" ]     && _HAS_AUDIO=1    && _DOCS_FOUND="$_DOCS_FOUND AUDIO.md"
[ -f "docs/ANIM.md" ]      && _HAS_ANIM=1     && _DOCS_FOUND="$_DOCS_FOUND ANIM.md"
[ -f "docs/PRD.md" ]       && _DOCS_FOUND="$_DOCS_FOUND PRD.md"
[ -f "docs/EDD.md" ]       && _DOCS_FOUND="$_DOCS_FOUND EDD.md"
[ -f "docs/SCHEMA.md" ]    && _DOCS_FOUND="$_DOCS_FOUND SCHEMA.md"

echo "[proto] 偵測到文件：${_DOCS_FOUND}"
echo "[proto] HAS_FRONTEND=${_HAS_FRONTEND}  HAS_AUDIO=${_HAS_AUDIO}  HAS_ANIM=${_HAS_ANIM}"

if [ "$_HAS_FRONTEND" -eq 0 ]; then
  echo ""
  echo "⚠️  未偵測到 Frontend 設計文件（docs/FRONTEND.md 或 docs/PDD.md）。"
  echo "   若確定有 Frontend 需求，請先執行 /gendoc frontend 或 /gendoc pdd 生成相關文件。"
  echo "   或在 interactive 模式下手動確認繼續。"
fi
```

**若 `_EXEC_MODE=interactive` 且 `_HAS_FRONTEND=0`**：用 `AskUserQuestion` 確認是否繼續。
**若 `_EXEC_MODE=full-auto` 且 `_HAS_FRONTEND=0`**：仍繼續生成（依 PRD + EDD 推斷）。

---

## Step 1：文件掃描 — 畫面清單 & 設計規格提取

用 **Agent tool** 派送「文件掃描 Subagent」：

```
你是 UI/UX Specification Analyst（資深產品設計分析師）。
任務：從工程文件中提取所有畫面、導覽流程、設計規格，輸出結構化清單供後續 Prototype 生成使用。

**讀取步驟（不得跳過）：**
1. 若存在，讀取 docs/PRD.md → 提取：User Stories、功能模組、使用者角色
2. 若存在，讀取 docs/PDD.md → 提取：畫面清單（Screen List）、設計決策、UX 流程
3. 若存在，讀取 docs/VDD.md → 提取：色彩系統（主色/輔色/背景/文字）、字型規範、間距規範、品牌風格
4. 若存在，讀取 docs/FRONTEND.md → 提取：組件清單、頁面結構、導覽架構、互動規格
5. 若存在，讀取 docs/AUDIO.md → 提取：BGM 清單、P0 SFX 觸發點（事件名稱）、VO 關鍵點
6. 若存在，讀取 docs/ANIM.md → 提取：P0/P1 動畫清單（進場/轉場/強調）、粒子特效規格
7. 若存在，讀取 docs/SCHEMA.md → 提取：主要資料結構（用於生成 mock data）
8. 若存在，讀取 docs/EDD.md → 提取：引擎/技術棧（用於判斷 Canvas/WebGL/HTML5 渲染模式）

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

Agent 執行完成後，主 Claude 解析輸出的 `PROTOTYPE_SPEC` 供後續步驟使用。

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

**審查目標：**
  docs/pages/prototype/index.html
  docs/pages/prototype/assets/prototype.css
  docs/pages/prototype/assets/prototype.js
  docs/pages/prototype/assets/audio-engine.js（若存在）
  docs/pages/prototype/assets/fx-engine.js（若存在）

**審查清單（共 10 項）：**

### P. Prototype 品質審查

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

## Step 4：整合 — 更新 README 和 pages/index.html

生成完成後，更新以下兩個檔案：

### Step 4-A：更新 README.md

搜尋 README.md 中的 `## Demo` 或 `## 文件站` 區塊，插入 Prototype 連結：

```markdown
## Interactive Prototype

| 連結 | 說明 |
|------|------|
| [📱 Interactive Prototype](docs/pages/prototype/index.html) | 可點擊的前端原型展示（{N} 個畫面，含動畫音效） |
| [📚 文件站](docs/pages/index.html) | 完整工程文件 |
```

若找不到合適區塊，在 README.md 的 `## Quick Start` 之前插入。

### Step 4-B：更新 docs/pages/index.html

在 `index-grid` 卡片群組中，插入 Prototype 卡片（置於最前）：

```html
<a class="index-card" href="prototype/index.html" style="border-color: var(--accent); background: linear-gradient(135deg, #eff8ff 0%, #fff 100%);">
  <div class="index-card__icon">🎮</div>
  <div class="index-card__title">Interactive Prototype</div>
  <div class="index-card__desc">{N} 個畫面 · 可點擊體驗 · 含動畫音效</div>
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

git add docs/pages/prototype/ README.md docs/pages/index.html

git commit -m "feat(gendoc)[prototype]: 生成互動式 HTML Prototype（${_PROTO_SCREENS} 畫面）

- 基於 PRD/PDD/VDD/FRONTEND/AUDIO/ANIM 生成完整可點擊原型
- 包含導覽路由、Mock Data、動畫特效、音效觸發
- 流程地圖 Modal 可全覽所有畫面
- 連結已更新至 README.md 和 docs/pages/index.html

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
