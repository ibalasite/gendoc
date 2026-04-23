---
doc-type: VDD
output-path: docs/VDD.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md    # 若存在
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md     # 若存在（UX 設計已完成時）
quality-bar: "§1 Design Mission 含明確視覺方向聲明（≥3 條原則）；§2 Art Direction 含情緒板關鍵字（≥5 個）+ 視覺參考來源；§3 品牌色盤（≥5 色含 hex + oklch + WCAG 對比度）；§4 Typography 含字型家族 + Scale（≥6 級）+ 行高；§5 Design Token 三層架構（Primitive / Semantic / Component）全部完整；§6 對遊戲類：角色設計表（主角 + ≥3 NPC）；對 SaaS/Mobile：UI 元件視覺規格表（≥8 元件）；§7 Asset Pipeline 含輸出格式 + 解析度 + 命名規範；§8 Screen 視覺規格覆蓋所有 PRD P0 畫面；§9 無障礙對比度比率已驗證；Dark Mode Token Mapping（≥13 tokens）；Motion Token 含 easing 函數；所有章節均有具體內容，不得留空或填 placeholder。"
---

# VDD 生成規則

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## 上游文件優先順序表

| 上游文件 | 必讀章節 | 用途 |
|---------|---------|------|
| `docs/IDEA.md`（若存在）| 全文 + Appendix C | 了解產品核心概念、目標用戶、市場定位——推斷視覺個性與品牌方向 |
| `docs/BRD.md` | 目標市場、競品分析、成功指標 | 競品視覺對比分析、品牌差異化策略依據 |
| `docs/PRD.md` | 產品類型指示詞、User Personas、P0/P1 功能清單、平台需求 | 偵測產品類型（game/saas-web/mobile）、推斷需哪些 VDD 章節、確認需涵蓋的畫面清單 |
| `docs/PDD.md`（若存在）| §5 Design System、§9 Design Token、§6 互動設計、§4 功能 UI 清單 | VDD 必須與 PDD Design Token 完全對齊；PDD 的 Component 清單決定 VDD §6 視覺規格涵蓋範圍 |
| `docs/req/*`（IDEA Appendix C 所列）| 全文 | 使用者原始輸入、業界視覺參考、美術風格素材——最原始的視覺上游資料 |

---

## IDEA Appendix C 特殊處理

若 `docs/IDEA.md` 存在且有 Appendix C，其中列出 `docs/req/` 目錄下所有參考檔案清單。
讀到 IDEA.md 時，**同時讀取** Appendix C 提及的所有 `docs/req/` 檔案：
- 這些檔案包含使用者原始輸入與業界參考資料，是最原始的上游資訊來源
- 對每個存在的 `docs/req/` 檔案，讀取全文，結合 Appendix C「應用於」欄位標有「VDD §」的段落
- 作為生成 VDD 對應章節的補充依據（視覺方向、設計美學、品牌參考）
- 優先採用素材原文描述，而非 AI 推斷
- 若無引用，靜默跳過

---

## Product Type Detection（產品類型偵測）

讀取 `docs/PRD.md`（輔以 `docs/IDEA.md` + `docs/BRD.md`），依以下優先順序偵測：

| 優先順序 | 偵測條件 | VDD Mode | 說明 |
|--------|---------|----------|------|
| 1 | PRD 明確提到 Unity / UnityEngine / Cocos Creator / cc.Node / Phaser / PixiJS / game engine / 角色設計 / NPC / 遊戲場景 | `game` | 啟用角色設計、美術風格、遊戲 UI 章節 |
| 2 | PRD 明確提到 iOS / Android / React Native / Flutter / 原生 App / SwiftUI / Jetpack Compose | `mobile` | 啟用平台視覺規範（iOS HIG / Material Design）+ Mobile Token 章節 |
| 3 | PRD 明確提到 SaaS / Web App / Dashboard / Admin / Portal / React / Vue / Next.js / SPA | `saas-web` | 啟用品牌系統、Design System、UI 元件視覺規格章節 |
| 4 | PRD 為純後端 API / CLI / 微服務，無任何 UI 描述 | `api-only` | **跳過 VDD 生成**，於文件最頂部聲明「本產品為純後端服務，無視覺設計需求，VDD 不適用」 |

**多類型並存**（如 mobile + saas-web）：以 PRD 主要描述的平台為主，次要平台補充說明；兩份 Section 均生成，以 `> 本節適用：[platform]` 標注。

---

## Platform Scope Declaration

在 VDD 文件最開頭（Document Control 後）寫入：

```markdown
<!-- ⚠️ VDD Platform Scope — 本文件視覺設計適用範圍 -->
- [ ] Web App / SaaS（Browser）
- [ ] iOS Native
- [ ] Android Native
- [ ] Game（Unity / Cocos / HTML5）
- [ ] 跨平台 App
```

依偵測結果勾選對應平台。

---

## Key Fields（欄位提取表）

| 欄位 | 來源上游 | 推斷規則 |
|------|---------|---------|
| 產品名稱 | IDEA.md §1 / PRD §1 | 直接提取，格式化為 Title Case |
| 目標市場 / 用戶 | BRD.md §2 / PRD Personas | 提取用戶年齡層、文化背景——影響色彩、字型風格選擇 |
| 競品列表 | BRD.md §3 / IDEA.md 競品 | 用於競品視覺差異化分析（§1.3） |
| 產品個性關鍵字 | IDEA.md / req/* 素材 | 若存在，直接引用；若無，依產品類型 AI 推斷（至少 5 個形容詞） |
| 主要功能清單（P0）| PRD.md P0 User Stories | 決定哪些畫面需要 §8 Screen 視覺規格 |
| 現有 Design Token | PDD.md §9 | 若 PDD 已定義 Token，VDD 必須繼承並擴展；不得自行另起一套 |
| 遊戲類型 / 世界觀 | PRD / IDEA / req/* | 僅 `game` mode：決定角色設計風格、藝術方向 |
| 平台 UI 規範 | PRD 平台指示 | `mobile` mode：iOS HIG 或 Material Design 3 版本；`game` mode：引擎 UI 規範 |

---

## Section Rules

以下為 VDD 每個章節的生成規則。依 Product Type Detection 結果，部分章節僅適用特定 mode，以 `[game]` / `[saas-web]` / `[mobile]` / `[all]` 標注。

---

### §0 Document Control [all]

- DOC-ID 格式：`VDD-<PROJECT_SLUG 大寫>-<YYYYMMDD>`
- 上游文件連結：IDEA.md / BRD.md / PRD.md / PDD.md（若存在）
- 版本歷程表（Version / Date / Author / Change Summary）
- 下游文件聲明：「本文件輸出供 EDD.md（技術規格）與 FRONTEND.md（前端實作）參照」

---

### §1 Design Mission（設計使命）[all]

**必填項目**：

1. **產品視覺定位宣言**（1–2 句）：說明視覺設計要在競品中實現什麼差異化。依 BRD 競品分析推斷。

2. **設計原則**（≥3 條，格式：原則名 + 一句說明）：

   | 原則 | 說明 |
   |------|------|
   | <原則 1> | <基於 IDEA/BRD 的具體說明，非泛論> |
   | <原則 2> | <具體說明> |
   | <原則 3> | <具體說明> |

3. **視覺方向選擇**（必須從以下選擇並明確聲明，不得留空）：

   - Editorial / Magazine
   - Neo-Brutalism
   - Glassmorphism（含真實深度）
   - Dark Luxury / Light Luxury
   - Bento Layout
   - Swiss / International
   - Retro-Futurism
   - Game UI（Diegetic / Non-Diegetic / Meta）
   - Material Design 3 / iOS HIG
   - 自定義（需在 §1 完整描述）

   **Anti-Template 警告**：禁止選擇「乾淨簡約（Clean Minimal）」作為最終答案——必須具體到特定方向。

4. **§1.3 競品視覺差異化分析**：

   | 競品 | 視覺風格描述 | 我方差異化點 |
   |------|------------|------------|
   | <競品 1（來自 BRD）> | <色彩 + 字型 + 風格關鍵字> | <我方如何不同> |
   | <競品 2> | <描述> | <差異> |

---

### §2 Art Direction（藝術方向）[all]

**必填項目**：

1. **情緒板關鍵字**（≥5 個形容詞，構成視覺語言詞彙表）：

   ```
   <Keyword 1> · <Keyword 2> · <Keyword 3> · <Keyword 4> · <Keyword 5>
   ```

   來源：優先引用 `docs/req/*` 素材原文；若無，依產品定位 AI 推斷。

2. **視覺參考來源**（Moodboard References）：

   | 類型 | 參考來源 / 描述 |
   |------|--------------|
   | 色彩靈感 | <調色板參考（如：Bauhaus 主色系 / 日式 wabi-sabi 大地色）> |
   | 排版靈感 | <字型風格參考（如：Neue Haas Grotesk 極簡系統 / 哥德式裝飾字）> |
   | 構圖靈感 | <佈局風格參考（如：editorial magazine / bento grid）> |
   | 插圖 / 圖標靈感 | <視覺元素風格（如：flat icons / hand-drawn / 3D render）> |
   | 動態靈感 | <動效參考（如：Framer Motion showcase / iOS 彈性動畫）> |

3. **光線與材質方向**：

   - 材質風格（Flat / Skeuomorphism / Glassmorphism / Claymorphism / Neumorphism / Brutalism / 其他）
   - 光源方向（統一從左上方 / 環境光 / 無陰影）
   - 陰影使用原則（用於層次感 / 僅 hover 狀態 / 完全不用）

4. **[game] 世界觀與美術風格聲明**：

   - 美術風格（寫實主義 / 卡通渲染 / 像素藝術 / 水彩插畫 / 賽博龐克 / 東方水墨 / 其他）
   - 視覺時代感（古代 / 現代 / 未來 / 架空）
   - 色彩情緒目標（溫暖歡快 / 神秘緊張 / 清爽治癒 / 史詩宏偉）
   - 光影技術要求（Toon Shading / PBR / 2D Sprite 光源模擬）

---

### §3 Brand Identity（品牌識別）[all]

**注意**：若 PDD.md §5 已定義 Design System 色彩，本節必須繼承並擴展（不得另起一套）。

> **[game]** 定義 HUD color palette（overlay-bg、hud-text、hud-accent）、game logo safe-zone、UI overlay 色彩語義（health=紅、energy=藍、XP=金）。

**必填項目**：

1. **主色盤（Primary Palette）**（≥5 色，每色必填以下欄位）：

   | 名稱 | Hex | oklch | RGB | 用途 | WCAG AA 對比度（白底）| WCAG AA 對比度（黑底）|
   |------|-----|-------|-----|------|---------------------|---------------------|
   | Primary-500 | `#XXXXXX` | `oklch(XX% X.XX XXX)` | `rgb(X,X,X)` | 主按鈕、主要連結 | X.X:1 | X.X:1 |
   | Primary-700 | | | | hover 狀態 | | |
   | Secondary-500 | | | | 輔助元素、強調 | | |
   | Neutral-100 | | | | 背景、卡片底色 | | |
   | Neutral-900 | | | | 主文字 | | |

2. **功能色（Semantic Colors）**：

   | 功能 | Light Mode Hex | Dark Mode Hex | 用途 |
   |------|--------------|--------------|------|
   | Success | `#XXXXXX` | `#XXXXXX` | 成功提示、正向狀態 |
   | Warning | | | 警告、需注意狀態 |
   | Error | | | 錯誤、危險操作 |
   | Info | | | 資訊提示 |

3. **Logo 使用規範**（若 PRD/IDEA 有 Logo 需求）：

   - 最小尺寸（螢幕：XXpx，印刷：XXmm）
   - 安全間距（Logo 高度的 X 倍）
   - 可用背景（白底 / 深底 / 彩色底規則）
   - 禁止用法（不得拉伸、不得旋轉、禁止色彩覆蓋）

4. **[mobile] 平台品牌適配**：

   - iOS：遵守 iOS HIG 色彩語意（`systemBlue`、`systemRed` 等系統色對應我方品牌色的映射）
   - Android：定義 Material Theme Color Scheme（`primary`、`secondary`、`tertiary`、`surface` 對應我方品牌色）

---

### §4 Typography System（字型系統）[all]

**必填項目**：

1. **字型家族選擇**：

   | 角色 | 字型名稱 | 備用字型 | 用途 | 授權 |
   |------|---------|---------|------|------|
   | Display / Heading | <字型名> | serif / sans-serif | 標題、大型文字 | <Google Fonts / Adobe Fonts / 商業授權> |
   | Body | <字型名> | system-ui, sans-serif | 內文、UI 標籤 | |
   | Mono（若需要）| <字型名> | monospace | 程式碼、數字顯示 | |
   | [game] 遊戲字型 | <字型名> | | 遊戲 UI、對話框、計分板 | |

   字型最多 2 個家族（Display + Body），除非有明確設計理由；game mode 可額外 1 個遊戲字型。

2. **Type Scale（字型比例）**（≥6 個層級）：

   | Token 名稱 | 尺寸 | 行高 | 字重 | 字距 | 用途 |
   |-----------|------|------|------|------|------|
   | `--text-display` | `clamp(3rem, 1rem + 7vw, 8rem)` | 1.1 | 700 | -0.02em | Hero 主標題 |
   | `--text-h1` | `clamp(2rem, 1.5rem + 3vw, 4rem)` | 1.2 | 700 | -0.01em | 頁面主標題 |
   | `--text-h2` | `clamp(1.5rem, 1.2rem + 1.5vw, 2.5rem)` | 1.3 | 600 | 0 | 章節標題 |
   | `--text-h3` | `clamp(1.25rem, 1rem + 0.8vw, 1.75rem)` | 1.4 | 600 | 0 | 子標題 |
   | `--text-body` | `clamp(1rem, 0.92rem + 0.4vw, 1.125rem)` | 1.6 | 400 | 0 | 內文 |
   | `--text-small` | `0.875rem` | 1.5 | 400 | 0.01em | 說明文字、標籤 |
   | `--text-caption` | `0.75rem` | 1.4 | 400 | 0.02em | 圖說、Metadata |

3. **字型載入策略**：

   - `font-display: swap`
   - Preload 僅 Critical Weight/Style（主 Body 字型的 Regular 400）
   - Subset 策略（若有中文：繁體中文 Unicode Range 或 Google Fonts `&subset=chinese-traditional`）

---

### §5 Design Tokens（設計代幣）[all]

**必填項目**（三層架構，必須全部完整，不得留 placeholder）：

**Layer 1 — Primitive（原始值）**

```css
/* 色彩原始值 */
--color-blue-50:  oklch(97% 0.02 250);
--color-blue-500: oklch(55% 0.21 250);
--color-blue-900: oklch(25% 0.15 250);

/* 間距原始值（4px 基準格線）*/
--space-1: 4px;
--space-2: 8px;
--space-4: 16px;
--space-8: 32px;
--space-16: 64px;

/* 字型尺寸原始值 */
--font-size-12: 0.75rem;
--font-size-16: 1rem;
--font-size-24: 1.5rem;

/* 圓角原始值 */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 16px;
--radius-full: 9999px;

/* 動效原始值 */
--duration-instant: 50ms;
--duration-fast:    150ms;
--duration-normal:  300ms;
--duration-slow:    500ms;
--ease-out-expo:    cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out:      cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring:      cubic-bezier(0.34, 1.56, 0.64, 1);
```

**Layer 2 — Semantic（語意，引用 Primitive）**

```css
/* 色彩語意 */
--color-action-primary:    var(--color-blue-500);
--color-action-primary-hover: var(--color-blue-700);
--color-feedback-success:  var(--color-green-500);
--color-feedback-error:    var(--color-red-500);
--color-feedback-warning:  var(--color-amber-500);
--color-feedback-info:     var(--color-blue-400);
--color-surface-base:      var(--color-neutral-50);
--color-surface-elevated:  var(--color-neutral-0);
--color-text-primary:      var(--color-neutral-900);
--color-text-secondary:    var(--color-neutral-500);
--color-text-disabled:     var(--color-neutral-300);
--color-border-default:    var(--color-neutral-200);
--color-border-focus:      var(--color-blue-500);

/* 間距語意 */
--spacing-component-gap:   var(--space-2);
--spacing-section-gap:     var(--space-16);
--spacing-page-padding:    var(--space-8);

/* 動效語意 */
--duration-interaction:    var(--duration-fast);
--duration-transition:     var(--duration-normal);
--ease-interaction:        var(--ease-out-expo);
```

**Layer 3 — Component（元件，引用 Semantic）**

```css
/* 按鈕 */
--button-primary-bg:       var(--color-action-primary);
--button-primary-bg-hover: var(--color-action-primary-hover);
--button-primary-text:     var(--color-neutral-0);
--button-padding-x:        var(--space-4);
--button-padding-y:        var(--space-2);
--button-radius:           var(--radius-md);
--button-transition:       var(--duration-interaction) var(--ease-interaction);

/* 輸入欄位 */
--input-border:            var(--color-border-default);
--input-border-focus:      var(--color-border-focus);
--input-bg:                var(--color-surface-elevated);
--input-text:              var(--color-text-primary);
--input-placeholder:       var(--color-text-secondary);
--input-radius:            var(--radius-md);
```

#### §5.1 Dark Mode Token Mapping（至少 13 個 semantic token）

| Semantic Token | Light Mode 值 | Dark Mode 值 | WCAG 對比度（dark 底）|
|---------------|-------------|-------------|-------------------|
| `--color-surface-base` | `oklch(98% 0 0)` | `oklch(12% 0 0)` | N/A（背景）|
| `--color-surface-elevated` | `oklch(100% 0 0)` | `oklch(18% 0 0)` | N/A |
| `--color-text-primary` | `oklch(18% 0 0)` | `oklch(95% 0 0)` | 15.8:1 ✓ |
| `--color-text-secondary` | `oklch(45% 0 0)` | `oklch(65% 0 0)` | 4.6:1 ✓ |
| `--color-text-disabled` | `oklch(70% 0 0)` | `oklch(40% 0 0)` | 2.8:1（禁用，豁免）|
| `--color-action-primary` | `oklch(55% 0.21 250)` | `oklch(65% 0.18 250)` | 4.6:1 ✓ |
| `--color-action-primary-hover` | `oklch(45% 0.22 250)` | `oklch(75% 0.15 250)` | 8.1:1 ✓ |
| `--color-border-default` | `oklch(88% 0 0)` | `oklch(28% 0 0)` | N/A（分隔線）|
| `--color-border-focus` | `oklch(55% 0.21 250)` | `oklch(65% 0.18 250)` | N/A（焦點環）|
| `--color-feedback-success` | `oklch(55% 0.18 150)` | `oklch(65% 0.15 150)` | 4.5:1 ✓ |
| `--color-feedback-error` | `oklch(55% 0.22 25)` | `oklch(65% 0.18 25)` | 4.5:1 ✓ |
| `--color-feedback-warning` | `oklch(65% 0.18 80)` | `oklch(72% 0.16 80)` | 4.5:1 ✓ |
| `--color-feedback-info` | `oklch(60% 0.19 250)` | `oklch(68% 0.16 250)` | 4.5:1 ✓ |

#### §5.2 Motion Tokens（動效代幣）

| Token | 值 | 用途 |
|-------|---|------|
| `--duration-fast` | `150ms` | 按鈕 hover / focus / tap |
| `--duration-normal` | `300ms` | 面板展開 / 頁面轉換 / Modal 開關 |
| `--duration-slow` | `500ms` | Hero 進場 / 複雜動畫序列 |
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | 元素滑入、彈出（自然退出）|
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 開心的彈跳感（卡片、Toast 進場）|
| `--ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)` | 頁面轉換、抽屜展開 |
| `--motion-reduced-duration` | `1ms` | `prefers-reduced-motion: reduce` 時覆蓋所有 duration |

**prefers-reduced-motion 規則**：所有動效 CSS 必須包含：
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: var(--motion-reduced-duration) !important;
    transition-duration: var(--motion-reduced-duration) !important;
  }
}
```

---

### §6 Character & UI Visual Specs（角色與 UI 視覺規格）

#### §6a [game] Character Design（角色設計）

**必填項目**：

1. **整體美術風格宣言**（1 段，含比較參考作品）

2. **角色設計規格表**（主角 + ≥3 NPC）：

   | 角色名稱 | 角色類型 | 體型比例 | 主色系 | 輔色系 | 服裝風格 | 面部特徵 | 個性視覺語言 | 特殊視覺標誌 |
   |---------|---------|---------|-------|-------|---------|---------|------------|------------|
   | <主角名（來自 PRD/IDEA）> | Protagonist | <X 頭身（如 6 頭身）> | <主色 hex> | <輔色 hex> | <風格描述> | <臉型/眼型特徵> | <活潑/神秘/正直/調皮等> | <招牌元素，如武器/頭飾> |
   | <NPC 1> | <類型（Ally/Enemy/NPC）> | | | | | | | |
   | <NPC 2> | | | | | | | | |
   | <NPC 3> | | | | | | | | |

3. **角色動態狀態規格**：

   | 狀態 | 動作描述 | 幀數 | 速度 | 循環 |
   |------|---------|------|------|------|
   | Idle | <靜止自然呼吸動作> | <N> 幀 | <N> fps | 是 |
   | Walk | <走路循環> | | | 是 |
   | Run | <跑步循環> | | | 是 |
   | Attack | <攻擊動作> | | | 否（一次性）|
   | Hurt | <受傷反應> | | | 否 |
   | Die | <死亡動畫> | | | 否 |
   | <產品特有狀態> | | | | |

4. **場景美術規格**：

   | 場景 | 主色調 | 光源方向 | 氣候 / 時間 | 特殊視覺元素 |
   |------|-------|---------|-----------|------------|
   | <場景 1（來自 PRD）> | <色調描述> | <左上 / 頂部 / 逆光> | <晴天 / 夜晚 / 雨天> | <霧氣 / 粒子效果 / 動態背景> |

#### §6b [saas-web] [mobile] UI Component Visual Specs（UI 元件視覺規格）

**必填項目**（≥8 個元件，每個元件涵蓋所有 States）：

| 元件 | Default | Hover | Focus | Active | Disabled | Error | Empty | Loading |
|-----|---------|-------|-------|--------|----------|-------|-------|---------|
| Button Primary | bg: `--button-primary-bg`；文字白色；radius `--radius-md` | bg 加深 8%；transition `--duration-fast` | ring 2px `--color-border-focus`；ring-offset 2px | scale(0.97)；bg 加深 12% | opacity 0.4；cursor not-allowed | N/A | N/A | Spinner 替換文字 |
| Button Secondary | border 1px `--color-border-default`；bg transparent | bg `--color-surface-base` | ring 2px focus | scale(0.97) | opacity 0.4 | N/A | N/A | Spinner |
| Input Field | border `--input-border`；bg `--input-bg` | border 加深 | border `--input-border-focus`；ring 2px | 同 Focus | opacity 0.5 | border red；error text 下方 | placeholder 顯示 | N/A |
| Card | bg `--color-surface-elevated`；shadow-sm | shadow-md；translateY(-2px) | ring 2px（若可互動）| shadow-sm | opacity 0.6 | Skeleton 閃爍 | Empty State 插圖 + CTA | Skeleton Screen |
| Navigation Item | color `--color-text-secondary` | color `--color-text-primary` | underline + ring | bg highlight | opacity 0.4 | N/A | N/A | N/A |
| Checkbox | border 1px；bg white | border 加深 | ring 2px | 同 Hover | opacity 0.4 | N/A | N/A | N/A |
| Modal | bg `--color-surface-elevated`；backdrop blur(8px) | N/A | Trap focus 在 Modal 內 | N/A | N/A | N/A | N/A | 內容 Skeleton |
| Toast / Snackbar | bg `--color-neutral-900`；text white；radius `--radius-lg` | N/A | N/A | Dismiss on click | N/A | bg `--color-feedback-error` | N/A | N/A |
| <依 PRD 特有元件補充> | | | | | | | | |

---

### §7 Asset Pipeline（素材管線）[all]

**必填項目**：

1. **素材分類與輸出規格**：

   | 素材類型 | 輸出格式 | 解析度 / 尺寸 | 色彩模式 | 備注 |
   |---------|---------|-------------|---------|------|
   | 圖示（Icon）| SVG（主）+ PNG 備用 | 24×24px（1x），48×48px（2x） | RGBA | 提供 Sprite Sheet |
   | 插圖（Illustration）| SVG / AVIF / WebP | 依使用場景，最大 1920px wide | RGB | 必須有 PNG fallback |
   | 照片 / 截圖 | AVIF（主）+ WebP + JPEG fallback | 最大 2000px wide；渲染尺寸 2× | RGB | `loading="lazy"` 除 Hero |
   | Hero 媒體 | AVIF + WebP | 1920px wide + Mobile 768px | RGB | `fetchpriority="high"` |
   | [game] 精靈圖（Sprite）| PNG（透明）+ Texture Atlas | 2× 倍率原始尺寸；最大 4096×4096 | RGBA | Cocos/Unity Sprite Packer |
   | [game] 背景圖 | AVIF / JPEG | 1080p / 2K 依平台 | RGB | 支援多解析度版本 |
   | 字型檔案 | WOFF2（主）+ WOFF fallback | N/A | N/A | Subset 僅用到的字元 |

2. **命名規範**：

   ```
   格式：<category>-<name>-<variant>-<size>.<ext>
   範例：
     icon-chevron-right-24.svg
     illus-empty-state-search-400.webp
     hero-banner-homepage-1920.avif
     [game] sprite-player-idle-2x.png
     [game] bg-forest-day-1080.jpg
   ```

   - 全小寫 + kebab-case
   - 禁止空格、特殊字元（除連字符）
   - 版本號不放在檔名（改用 Content Hash 或 CDN 快取控制）

3. **Figma → Code 交付規格**：

   | 步驟 | 說明 |
   |------|------|
   | Export 設定 | 圖示：SVG；插圖：SVG + PNG @2x；照片：AVIF + WebP @2x |
   | 命名對齊 | Figma Component 名稱 = Token 名稱 = CSS class 名稱（kebab-case）|
   | Design Token 同步 | 使用 Style Dictionary / Theo 從 Figma Token 匯出至 CSS / JSON |
   | 交付物 | Figma Link + Storybook Link + Token JSON 檔 |
   | 更新頻率 | 每個 Sprint 結束，QA 進入前完成 Figma → Code 同步 |

---

### §8 Screen Visual Specs（畫面視覺規格）[all]

**必填規則**：覆蓋所有 PRD P0 功能對應的畫面（依 PDD §4 Screen 清單或 PRD User Stories 推斷）。

每個 Screen 包含以下結構：

```
#### SCR-XXX <畫面名稱>（對應 PRD US-XXX）

**視覺層次（Visual Hierarchy）**：
- Primary Focus（最吸引視線的元素）：<元素名 + 視覺手法>
- Secondary（引導操作的元素）：<元素名>
- Tertiary（輔助資訊）：<元素名>

**Grid / 佈局**：
- Desktop：<欄數>欄 / <gutter> gap / max-width <Xpx>
- Mobile：單欄 / <gutter> gap

**色彩使用**：
- 背景：<Token 名>
- 主內容區：<Token 名>
- 強調色使用位置：<說明>

**Typography 使用**：
- 主標題：<Token 名> `--text-h1`
- 副標題：<Token 名>
- 內文：<Token 名>

**空狀態（Empty State）設計**：
- 插圖：<描述>
- 標題：「<文案>」
- 說明：「<文案>」
- CTA：「<按鈕文字>」

**Loading State**：
- 採用 Skeleton Screen（非 Spinner），模擬頁面骨架
```

---

### §9 Accessibility Visual Standards（無障礙視覺標準）[all]

**必填項目**：

1. **對比度驗證表**：

   | 文字 / 元素 | 前景色 | 背景色 | 對比度 | WCAG AA（4.5:1 / 3:1 大文字）| 狀態 |
   |-----------|--------|-------|--------|---------------------------|------|
   | 主文字（`--color-text-primary`）| `oklch(18% 0 0)` | `oklch(98% 0 0)` | 16.1:1 | ✓ 通過 | Light Mode |
   | 主文字（Dark）| `oklch(95% 0 0)` | `oklch(12% 0 0)` | 15.8:1 | ✓ 通過 | Dark Mode |
   | 次要文字 | `oklch(45% 0 0)` | `oklch(98% 0 0)` | 4.7:1 | ✓ 通過 | Light Mode |
   | 主要按鈕文字 | `oklch(100% 0 0)` | `oklch(55% 0.21 250)` | 4.6:1 | ✓ 通過 | Default |
   | Error 訊息 | `oklch(55% 0.22 25)` | `oklch(98% 0 0)` | 4.5:1 | ✓ 通過 | Light Mode |
   | Placeholder 文字 | `oklch(60% 0 0)` | `oklch(100% 0 0)` | 3.8:1 | ✗ 未達 AA（Placeholder 豁免）| — |

2. **焦點樣式規範**：

   - 焦點環寬度：≥ 2px
   - 焦點環顏色：`--color-border-focus`（對比度 ≥ 3:1 對所有相鄰色）
   - 焦點環偏移：`ring-offset: 2px`（確保環與元素間有間距）
   - 禁止：`outline: none` 不搭配自定義焦點樣式

3. **色盲無障礙檢核**：

   - 不以純色彩區分狀態（Always 搭配圖示或文字標籤）
   - 紅色 Error 必須搭配 ✕ 圖示
   - 綠色 Success 必須搭配 ✓ 圖示
   - 測試工具：Colour Contrast Analyser / Figma A11y Plugin / Stark

4. **圖示無障礙**：

   - 裝飾性圖示：`aria-hidden="true"`
   - 功能性圖示（無文字標籤）：`aria-label="<描述>"`
   - 最小觸控目標：44×44px（iOS HIG）/ 48×48dp（Material Design）

---

## Inference Rules（推導規則）

若上游文件缺少特定欄位，依以下規則推斷：

| 缺失欄位 | 推斷依據 | 推斷方法 |
|---------|---------|---------|
| 品牌主色 | IDEA.md 產品描述 + BRD 目標市場 | 依產業慣例（SaaS 科技類 → 藍色系；金融 → 深藍/深綠；健康 → 綠色；創意 → 多彩）；標注 `[AI 推斷]` |
| 字型選擇 | 視覺方向（§2）+ 產品個性 | Editorial → 有襯線 Display；SaaS → Inter / Geist；Game → 依美術風格；標注 `[AI 推斷]` |
| 角色名稱 | IDEA.md / PRD / req/* | 若無明確名稱，使用 `[待定]` 並說明期待角色類型 |
| Screen 清單 | PRD P0 User Stories | 依每個 P0 US 推斷對應 Screen；標注 `[依 PRD US-XXX 推斷]` |
| 競品視覺 | BRD 競品分析 | 依競品名稱推斷業界通用視覺語言；標注 `[AI 推斷，待確認]` |

**推斷標注規則**：所有非直接引用上游的推斷值，在行末加 `[AI 推斷]`，並在文件末尾 Open Questions 章節說明待確認事項。

---

## Self-Check Checklist（生成前自我核查，≥10 項）

- [ ] Product Type 已偵測正確（game / saas-web / mobile / api-only）；若 api-only，文件已聲明跳過
- [ ] Platform Scope Declaration 已勾選正確平台
- [ ] §1 Design Mission：設計原則 ≥3 條；視覺方向已明確選定（非「clean minimal」泛論）
- [ ] §1.3 競品視覺差異化分析：至少涵蓋 BRD 提及的所有競品
- [ ] §2 Art Direction：情緒板關鍵字 ≥5 個；視覺參考來源已填寫所有 5 個類型
- [ ] §3 品牌色盤：≥5 個色票，每色含 hex + oklch + 用途 + WCAG 對比度驗證
- [ ] §4 Typography：字型家族 ≤2 個（game 可 +1）；Type Scale ≥6 個層級；行高已定義
- [ ] §5 Design Token 三層架構（Primitive / Semantic / Component）全部完整，無裸 placeholder
- [ ] §5.1 Dark Mode Token Mapping：≥13 個 semantic token，每個有 Light + Dark 兩組 oklch 值 + WCAG 對比度
- [ ] §5.2 Motion Token：easing 函數已定義（≥3 個 cubic-bezier）；duration 已定義；prefers-reduced-motion 規則已包含
- [ ] §6 [game mode]：角色設計表覆蓋主角 + ≥3 NPC；角色動態狀態表已完成（≥6 個狀態）
- [ ] §6 [saas-web / mobile mode]：UI 元件視覺規格表 ≥8 個元件；每個元件有 Default / Hover / Focus / Active / Disabled / Error / Empty / Loading 8 種狀態
- [ ] §7 Asset Pipeline：素材分類規格表已填寫（圖示 / 插圖 / 照片 / Hero / 字型）；命名規範已定義；Figma → Code 交付規格已填寫
- [ ] §8 Screen Visual Specs：覆蓋所有 PRD P0 功能對應畫面（或依 PDD §4 Screen 清單）；每個 Screen 含視覺層次 + 佈局 + 色彩 + 空狀態設計
- [ ] §9 Accessibility：WCAG AA 對比度驗證表已完成；焦點樣式規範已定義；色盲無障礙檢核已說明
- [ ] 若 PDD.md 存在：VDD Design Token 與 PDD §9 Token 完全對齊，無衝突
- [ ] 所有 AI 推斷欄位已標注 `[AI 推斷]`，Open Questions 章節已列出待確認事項
- [ ] 無未替換的 `{{PLACEHOLDER}}` 格式佔位符
- [ ] 所有章節均有具體內容，無留空或「待補充」說明

若有遺漏，自行補齊後再寫入檔案。
