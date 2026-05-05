# VDD — Visual Design Document (視覺設計文件)
<!-- SDLC Requirements Engineering — Layer 3.5：Visual Design -->
<!-- 對應學術標準：ISO 9241-210 §Visual；WCAG 2.1 §Perceivable；W3C Design Tokens CG Spec -->
<!-- 上游：PDD（UX / Interaction Design）→ 本文件 → 下游：EDD（Tech Spec）+ FRONTEND（實作） -->
<!-- 回答：產品的視覺語言是什麼？品牌識別如何表達？藝術風格與資產規格如何定義？ -->

---

<!-- ⚠️ Product Type Scope — 本文件適用範圍 -->
<!-- 勾選適用產品類型，不同類型有不同重點章節 -->

## Product Type Declaration（產品類型宣告）

- [ ] SaaS / Web App（重點：品牌識別系統、UI 視覺系統、Design Token）
- [ ] Game（重點：角色設計、世界美術風格、NPC 視覺規格）
- [ ] Mobile App（重點：平台視覺規範、圖示系統、視覺動效）
- [ ] Marketing Site / Landing Page（重點：視覺敘事、插畫風格、品牌表達）
- [ ] Desktop App（重點：視覺密度、深色模式、系統整合視覺）
- [ ] Game + SaaS Hybrid（如遊戲後台）

---

## Document Control

| 欄位 | 內容 |
|------|------|
| **專案名稱** | {{PROJECT_NAME}} |
| **文件版本** | v1.0 |
| **狀態** | DRAFT / IN_REVIEW / APPROVED |
| **作者（Visual / Art Designer）** | {{AUTHOR}} |
| **日期** | {{DATE}} |
| **上游 PDD** | [PDD.md](PDD.md)（UX / Interaction Design） |
| **下游 EDD** | [EDD.md](EDD.md)（Tech Spec） |
| **下游 FRONTEND** | [FRONTEND.md](FRONTEND.md)（前端實作） |
| **設計規格版本** | {{DESIGN_SPEC_VERSION}} |
| **品牌指南** | {{BRAND_GUIDE_LINK}} |
| **審閱者** | {{ART_DIRECTOR}}, {{PM}}, {{ENGINEERING_LEAD}} |
| **核准者** | {{DESIGN_LEAD}} |

---

## Change Log

| 版本 | 日期 | 作者 | 變更摘要 |
|------|------|------|---------|
| v1.0 | {{DATE}} | {{AUTHOR}} | 初稿 |

---

## 1. 設計使命與品牌定位 (Design Mission & Brand Positioning)

### 1.1 設計使命宣言

> 本產品的視覺設計要傳達什麼核心感受？設計完成後，用戶第一眼會有什麼印象？

{{DESIGN_MISSION_STATEMENT}}

### 1.2 品牌個性（Brand Personality）

| 維度 | 我們是 | 我們不是 |
|------|--------|---------|
| **語氣** | {{E.g. 專業、直接}} | {{E.g. 冷漠、過度正式}} |
| **視覺能量** | {{E.g. 精煉、高對比}} | {{E.g. 雜亂、低能量}} |
| **情感色調** | {{E.g. 值得信賴、沉穩}} | {{E.g. 俗氣、刺激}} |
| **複雜度** | {{E.g. 簡潔有力}} | {{E.g. 裝飾過度}} |

### 1.3 情緒板（Mood Board）關鍵字

> 視覺方向的核心參考詞彙，所有設計決策應能回應這些關鍵字。

**主要方向：** {{DIRECTION}}（e.g. Editorial Luxury / Neo-brutalism / Glassmorphism / Swiss International）

**情感關鍵字：**
1. {{KEYWORD_1}}（e.g. 力量感 Power）
2. {{KEYWORD_2}}（e.g. 簡練 Refined）
3. {{KEYWORD_3}}（e.g. 現代 Contemporary）

**Mood Board 連結：** {{MOODBOARD_LINK}}

### 1.4 競品視覺分析

| 競品 | 視覺風格 | 我們的差異化 |
|------|---------|------------|
| {{COMPETITOR_1}} | {{STYLE_DESCRIPTION}} | {{DIFFERENTIATION}} |
| {{COMPETITOR_2}} | {{STYLE_DESCRIPTION}} | {{DIFFERENTIATION}} |
| {{COMPETITOR_3}} | {{STYLE_DESCRIPTION}} | {{DIFFERENTIATION}} |

### 1.5 PDD 需求對應

| PDD 互動規格 | VDD 視覺回應 | VDD 章節 |
|-------------|------------|---------|
| {{UX_REQUIREMENT_1}} | {{VISUAL_DECISION_1}} | §4.1 |
| {{UX_REQUIREMENT_2}} | {{VISUAL_DECISION_2}} | §5.2 |

---

## 2. 藝術方向與視覺風格 (Art Direction & Visual Style)

### 2.1 核心視覺風格（Style Direction）

**風格定義：** {{STYLE_DIRECTION}}

> 描述本產品的整體視覺哲學，包括：層次感、材質感、光影處理、空間感知。

{{STYLE_PHILOSOPHY_DESCRIPTION}}

### 2.2 視覺風格規格

| 元素 | 規格 | 說明 |
|------|------|------|
| **材質感** | {{E.g. 磨砂玻璃 / 平面無材質 / 皮革紋理}} | {{RATIONALE}} |
| **光源方向** | {{E.g. 頂部 45° / 無光影（Flat）}} | {{RATIONALE}} |
| **陰影風格** | {{E.g. 柔和漫射 / 硬邊投影 / 無陰影}} | {{RATIONALE}} |
| **邊角處理** | {{E.g. 全圓角 / 方形直角 / 混合}} | {{RATIONALE}} |
| **視覺密度** | {{E.g. 高密度資訊流 / 呼吸感留白}} | {{RATIONALE}} |
| **圖像風格** | {{E.g. 真實攝影 / 插畫 / 3D 渲染 / 純圖標}} | {{RATIONALE}} |

### 2.3 視覺靈感參考（Visual References）

| 類別 | 參考來源 | 借鑑元素 |
|------|---------|---------|
| 色彩靈感 | {{REFERENCE_SOURCE}} | {{BORROWED_ELEMENT}} |
| 排版靈感 | {{REFERENCE_SOURCE}} | {{BORROWED_ELEMENT}} |
| 版面靈感 | {{REFERENCE_SOURCE}} | {{BORROWED_ELEMENT}} |
| 動效靈感 | {{REFERENCE_SOURCE}} | {{BORROWED_ELEMENT}} |

### 2.4 設計禁區（Anti-patterns）

> 以下視覺選擇在本產品中被明確禁止，所有設計審查依此評判。

- 禁止：{{ANTI_PATTERN_1}}（e.g. 使用 Tailwind 預設藍色作為主色）
- 禁止：{{ANTI_PATTERN_2}}（e.g. 無差異化的卡片網格版型）
- 禁止：{{ANTI_PATTERN_3}}（e.g. 所有元件使用相同的圓角和陰影）
- 禁止：{{ANTI_PATTERN_4}}（e.g. 裝飾性動畫多於功能性動畫）

---

## 3. 品牌識別系統 (Brand Identity System)

### 3.1 色彩體系（Color System）

#### 3.1.1 品牌主色盤（Brand Palette）

| 色彩名稱 | Hex | RGB | HSL | OKLCH | 使用場景 |
|---------|-----|-----|-----|-------|---------|
| **{{BRAND_PRIMARY_NAME}}** | `#{{HEX}}` | `rgb({{R}}, {{G}}, {{B}})` | `hsl({{H}}, {{S}}%, {{L}}%)` | `oklch({{L}} {{C}} {{H}})` | 主要 CTA、品牌標識 |
| **{{BRAND_SECONDARY_NAME}}** | `#{{HEX}}` | `rgb({{R}}, {{G}}, {{B}})` | `hsl({{H}}, {{S}}%, {{L}}%)` | `oklch({{L}} {{C}} {{H}})` | 輔助強調、次要元素 |
| **{{BRAND_ACCENT_NAME}}** | `#{{HEX}}` | `rgb({{R}}, {{G}}, {{B}})` | `hsl({{H}}, {{S}}%, {{L}}%)` | `oklch({{L}} {{C}} {{H}})` | 高亮點綴、互動回饋 |

#### 3.1.2 完整色階系統（Color Scale）

**主色色階（Primary Scale）：**

| Token | Hex | 使用場景 |
|-------|-----|---------|
| `primary-50` | `#{{HEX}}` | 超淺背景、懸停底色 |
| `primary-100` | `#{{HEX}}` | 淺色背景、選中狀態底色 |
| `primary-200` | `#{{HEX}}` | 邊框淺色 |
| `primary-300` | `#{{HEX}}` | 禁用態邊框 |
| `primary-400` | `#{{HEX}}` | 圖示次要色 |
| `primary-500` | `#{{HEX}}` | **主要品牌色（基準）** |
| `primary-600` | `#{{HEX}}` | Hover 態、按壓態 |
| `primary-700` | `#{{HEX}}` | 深色強調 |
| `primary-800` | `#{{HEX}}` | 文字連結深色 |
| `primary-900` | `#{{HEX}}` | 深色背景上的文字 |

**輔色色階（Secondary Scale）：**

| Token | Hex | 使用場景 |
|-------|-----|---------|
| `secondary-50` | `#{{HEX}}` | 超淺輔色背景 |
| `secondary-100` | `#{{HEX}}` | 輔色選中底色 |
| `secondary-200` | `#{{HEX}}` | 輔色邊框淺色 |
| `secondary-500` | `#{{HEX}}` | **輔色基準色** |
| `secondary-700` | `#{{HEX}}` | 輔色深色強調 |
| `secondary-900` | `#{{HEX}}` | 輔色最深（深色背景文字）|

> 架構說明：若輔色（Secondary）在產品中僅作為單一強調值使用，可將以上色階簡化為單一 Token `secondary-500`，並在 §6.1 Layer 1 Primitive Tokens 中以單值定義；若需支援完整互動狀態（Hover/Active/Disabled），則必須至少定義 50 / 500 / 700 三階。

**強調色色階（Accent Scale）：**

| Token | Hex | 使用場景 |
|-------|-----|---------|
| `accent-50` | `#{{HEX}}` | 強調色超淺背景 |
| `accent-100` | `#{{HEX}}` | 強調色淺色背景 |
| `accent-200` | `#{{HEX}}` | 強調色邊框淺色 |
| `accent-500` | `#{{HEX}}` | **強調色基準色（高亮點綴）**|
| `accent-700` | `#{{HEX}}` | 強調色深色 |
| `accent-900` | `#{{HEX}}` | 強調色最深 |

> 架構說明：若 Accent 色在產品中為純裝飾用單點強調（如徽章、標籤高亮），可簡化為單一 Token `accent-500`；若 Accent 色用於可互動元件，則同 Secondary 需定義完整色階。

**中性灰階（Neutral Scale）：**

| Token | Hex | 使用場景 |
|-------|-----|---------|
| `neutral-0` | `#FFFFFF` | 純白背景 |
| `neutral-50` | `#{{HEX}}` | 頁面背景 |
| `neutral-100` | `#{{HEX}}` | 卡片背景 |
| `neutral-200` | `#{{HEX}}` | 分隔線、邊框 |
| `neutral-300` | `#{{HEX}}` | 禁用色 |
| `neutral-400` | `#{{HEX}}` | 佔位文字（Placeholder）|
| `neutral-500` | `#{{HEX}}` | 輔助說明文字 |
| `neutral-600` | `#{{HEX}}` | 次要文字 |
| `neutral-700` | `#{{HEX}}` | 內文文字 |
| `neutral-800` | `#{{HEX}}` | 標題文字 |
| `neutral-900` | `#{{HEX}}` | 主要文字（最高對比）|
| `neutral-1000` | `#000000` | 純黑 |

**語意色彩（Semantic Colors）：**

| 類別 | Light | Dark | 用途 |
|------|-------|------|------|
| `success-500` | `#{{HEX}}` | `#{{HEX}}` | 成功狀態、正向回饋 |
| `warning-500` | `#{{HEX}}` | `#{{HEX}}` | 警告提示、需注意項目 |
| `error-500` | `#{{HEX}}` | `#{{HEX}}` | 錯誤狀態、驗證失敗 |
| `info-500` | `#{{HEX}}` | `#{{HEX}}` | 資訊提示、說明文字 |

#### 3.1.3 色彩可及性驗證（WCAG Contrast Matrix）

| 前景色 | 背景色 | 對比度 | WCAG 等級 | 適用場景 |
|--------|--------|--------|----------|---------|
| `neutral-900` on `neutral-0` | — | {{RATIO}}:1 | AAA | 主要內文 |
| `neutral-700` on `neutral-50` | — | {{RATIO}}:1 | AA | 次要文字 |
| `primary-500` on `neutral-0` | — | {{RATIO}}:1 | AA | 互動連結 |
| `neutral-0` on `primary-500` | — | {{RATIO}}:1 | AA | 主要按鈕文字 |
| `error-500` on `neutral-0` | — | {{RATIO}}:1 | AA | 錯誤提示文字 |

### 3.2 字體系統（Typography System）

#### 3.2.1 字型選用

| 角色 | 字型名稱 | 用途 | 載入方式 |
|------|---------|------|---------|
| **Display Font** | `{{DISPLAY_FONT}}` | 大標題、英雄區塊 | Google Fonts / Self-hosted |
| **Primary Font** | `{{PRIMARY_FONT}}` | 介面文字、UI 元件 | Google Fonts / Self-hosted |
| **Mono Font** | `{{MONO_FONT}}` | 程式碼、資料欄位 | Google Fonts / Self-hosted |
| **Fallback Stack** | `system-ui, -apple-system, sans-serif` | 字型未載入時 | 系統內建 |

**選用理由：** {{FONT_SELECTION_RATIONALE}}

**Pairing Rationale（字型配對理由）：** {{FONT_PAIRING_RATIONALE}}（描述 Display Font 與 Primary Font 之間的排版對比，例如：Display 使用高對比襯線體製造視覺張力，Primary 使用幾何無襯線體確保介面可讀性，二者在字重和筆畫粗細上形成清晰的階層對比。）

**Required Glyph Ranges（必要字元範圍）：**
- Latin Basic / Latin-1 Supplement（英文、數字、基本標點）
- {{CJK_RANGE}}（如適用：CJK Unified Ideographs U+4E00–U+9FFF 繁體中文 / 簡體中文 / 日文漢字）
- {{EXTENDED_RANGES}}（如適用：Greek、Cyrillic、越南文、泰文等）
- 數學符號 / 貨幣符號（按實際內容需求填寫）

**Licensed Weights / Styles（授權字重與樣式）：**

| 字型角色 | 字重（Weight）| 樣式（Style）| 授權方式 |
|---------|-------------|------------|---------|
| Display Font | {{DISPLAY_WEIGHTS}}（e.g. 700, 900）| Normal | {{LICENSE}}（e.g. SIL OFL / 商業授權）|
| Primary Font | {{PRIMARY_WEIGHTS}}（e.g. 400, 500, 600, 700）| Normal, Italic | {{LICENSE}} |
| Mono Font | {{MONO_WEIGHTS}}（e.g. 400, 700）| Normal | {{LICENSE}} |

#### 3.2.2 字型比例系統（Type Scale）

| Token | 大小 | Line Height | Letter Spacing | Font Weight | 使用場景 |
|-------|------|-------------|---------------|-------------|---------|
| `text-display-2xl` | `clamp(3rem, 1rem + 7vw, 8rem)` | 1.1 | -0.02em | 700 | 首頁英雄標題 |
| `text-display-xl` | `clamp(2.25rem, 1.5rem + 4vw, 4.5rem)` | 1.15 | -0.02em | 700 | 主要 H1 標題 |
| `text-display-lg` | `clamp(1.875rem, 1.25rem + 3vw, 3rem)` | 1.2 | -0.01em | 700 | H2 標題 |
| `text-xl` | `1.25rem` / `20px` | 1.4 | 0em | 600 | H3 標題、卡片標題 |
| `text-lg` | `1.125rem` / `18px` | 1.5 | 0em | 500 | 小標題、強調文字 |
| `text-base` | `1rem` / `16px` | 1.6 | 0em | 400 | 主要內文 |
| `text-sm` | `0.875rem` / `14px` | 1.5 | 0.01em | 400 | 輔助說明、標籤 |
| `text-xs` | `0.75rem` / `12px` | 1.4 | 0.02em | 400 | 提示文字、版權聲明 |
| `text-mono` | `0.875rem` / `14px` | 1.6 | 0em | 400 | 程式碼、資料欄位 |

#### 3.2.3 字體載入規範

```css
/* 字體預載（僅針對關鍵字重） */
<link rel="preload" href="/fonts/{{FONT_FILE}}.woff2" as="font" type="font/woff2" crossorigin>

/* font-face 宣告 */
@font-face {
  font-family: '{{FONT_NAME}}';
  src: url('/fonts/{{FONT_FILE}}.woff2') format('woff2');
  font-weight: {{WEIGHT_RANGE}};
  font-style: normal;
  font-display: swap; /* 防止 FOIT */
}
```

**規範：**
- 最多載入 2 種字族（Display + Body）
- 僅預載首屏所需字重（通常 400 + 700）
- 字型子集化（Subsetting）至實際使用字元
- 使用 `font-display: swap` 防止不可見文字閃爍

### 3.3 標誌與圖示規格（Logo & Icon Specification）

#### 3.3.1 品牌標誌規格

| 版本 | 用途 | 最小尺寸 | 清除空間 | 格式 |
|------|------|---------|---------|------|
| 主標誌（含文字）| 首頁 Header、對外文件 | 120px 寬 | 標誌高度 × 0.5 | SVG / PNG |
| 標誌符號（僅圖標）| Favicon、App Icon | 32px | 符號尺寸 × 0.25 | SVG / ICO |
| 深色背景版 | 深色 Header、Dark Mode | 120px 寬 | 同上 | SVG / PNG |

**禁用規則：**
- 禁止拉伸或壓縮標誌比例
- 禁止在低對比背景上使用標誌（需確保 ≥ 3:1 對比度）
- 禁止旋轉、加陰影或添加特效
- 禁止修改品牌色彩

#### 3.3.2 圖示系統（Icon System）

| 欄位 | 規格 |
|------|------|
| **圖示庫** | {{ICON_LIBRARY}}（e.g. Lucide / Phosphor / Heroicons / 自建） |
| **繪製規格** | {{CANVAS_SIZE}}px 畫布，{{STROKE_WIDTH}}px 線寬，{{CORNER_RADIUS}}px 圓角 |
| **尺寸規格** | 16px / 20px / 24px / 32px |
| **輸出格式** | SVG（線上）/ PNG 2x（相容）|
| **色彩模式** | 繼承 `currentColor`，單色可著色 |
| **無障礙** | 裝飾性圖示 `aria-hidden="true"`；功能性圖示搭配 `aria-label` |

---

## 4. 角色與世界設計 (Character & World Design)
<!-- 遊戲產品必填；SaaS 產品填寫吉祥物 / 插畫風格即可 -->

### 4.1 美術風格定義（Art Style Definition）

| 維度 | 規格 | 說明 |
|------|------|------|
| **整體風格** | {{E.g. 2D 手繪卡通 / 3D 低多邊形 / 像素藝術 / 寫實渲染}} | {{RATIONALE}} |
| **視覺複雜度** | {{E.g. 簡潔（Minimal）/ 豐富（Detailed）}} | {{RATIONALE}} |
| **色彩飽和度** | {{E.g. 高飽和（Vivid）/ 低飽和（Muted）/ 去飽和（Desaturated）}} | {{RATIONALE}} |
| **輪廓風格** | {{E.g. 粗黑邊線 / 無邊線 / 細線}} | {{RATIONALE}} |
| **光影處理** | {{E.g. 卡通平塗 / 賽璐珞 / 體積光}} | {{RATIONALE}} |

### 4.2 主角設計規格（Protagonist Design Spec）
<!-- SaaS 產品此節改為「品牌吉祥物 / Mascot 設計規格」 -->

| 欄位 | 規格 |
|------|------|
| **角色名稱** | {{CHARACTER_NAME}} |
| **視覺原型** | {{VISUAL_ARCHETYPE}}（e.g. 青年探索者 / 機械戰士）|
| **身形比例** | {{PROPORTION}}（e.g. 7 頭身寫實 / 4 頭身 Q 版）|
| **主色調** | {{PRIMARY_COLOR}}（對應品牌色 `primary-500`）|
| **輔色調** | {{SECONDARY_COLOR}} |
| **服裝 / 外觀特徵** | {{APPEARANCE_DESCRIPTION}} |
| **表情組數** | {{EXPRESSION_COUNT}} 種（e.g. 開心 / 憤怒 / 驚訝 / 疲憊 / 專注）|
| **動作狀態** | {{ANIMATION_STATES}}（e.g. 閒置 / 跑步 / 攻擊 / 受傷 / 勝利）|
| **參考風格** | {{STYLE_REFERENCE}} |

**精靈圖（Sprite Sheet）規格：**

| 動畫狀態 | 單格寬度（px）| 單格高度（px）| 幀數 | FPS | Atlas 排列（欄×列）| 幀間距（px）| Origin Point（x, y）|
|---------|------------|------------|-----|-----|-----------------|------------|-------------------|
| Idle（閒置）| {{FRAME_W}} | {{FRAME_H}} | {{COUNT}} | {{FPS}} | {{COLS}}×{{ROWS}} | {{PAD}} | {{ORIGIN_X}}, {{ORIGIN_Y}} |
| Run（跑步）| {{FRAME_W}} | {{FRAME_H}} | {{COUNT}} | {{FPS}} | {{COLS}}×{{ROWS}} | {{PAD}} | {{ORIGIN_X}}, {{ORIGIN_Y}} |
| Attack（攻擊）| {{FRAME_W}} | {{FRAME_H}} | {{COUNT}} | {{FPS}} | {{COLS}}×{{ROWS}} | {{PAD}} | {{ORIGIN_X}}, {{ORIGIN_Y}} |
| Hurt（受傷）| {{FRAME_W}} | {{FRAME_H}} | {{COUNT}} | {{FPS}} | {{COLS}}×{{ROWS}} | {{PAD}} | {{ORIGIN_X}}, {{ORIGIN_Y}} |
| Victory（勝利）| {{FRAME_W}} | {{FRAME_H}} | {{COUNT}} | {{FPS}} | {{COLS}}×{{ROWS}} | {{PAD}} | {{ORIGIN_X}}, {{ORIGIN_Y}} |
| Death（死亡）| {{FRAME_W}} | {{FRAME_H}} | {{COUNT}} | {{FPS}} | {{COLS}}×{{ROWS}} | {{PAD}} | {{ORIGIN_X}}, {{ORIGIN_Y}} |

> 說明：Origin Point 為角色的邏輯錨點（腳底或重心），以像素座標表示，用於引擎碰撞盒對齊與場景定位。幀間距（inter-frame padding）防止 GPU 紋理抗鋸齒造成的幀溢色（Bleeding）。Atlas 排列格式為「欄數 × 列數」，讀取順序為從左到右、從上到下。

### 4.3 NPC 視覺規格（NPC Visual Spec）

| NPC 名稱 | 角色功能 | 視覺特徵 | 顏色代碼 | 表情組數 |
|---------|---------|---------|---------|---------|
| {{NPC_1_NAME}} | {{FUNCTION_1}} | {{VISUAL_TRAITS}} | `#{{HEX}}` | {{COUNT}} |
| {{NPC_2_NAME}} | {{FUNCTION_2}} | {{VISUAL_TRAITS}} | `#{{HEX}}` | {{COUNT}} |
| {{NPC_3_NAME}} | {{FUNCTION_3}} | {{VISUAL_TRAITS}} | `#{{HEX}}` | {{COUNT}} |

**NPC 視覺差異化規則：**
- 每個 NPC 必須有獨特的輪廓剪影，可在縮圖大小下辨認
- 主要 NPC 與背景 NPC 在細節精度上應有差異
- 敵對 / 友善 / 中立 NPC 需有明確的色彩語義差異

### 4.4 環境與場景美術（Environment & Scene Art）

| 場景名稱 | 視覺主題 | 主色調 | 時間段 / 光線 | 特殊視覺效果 |
|---------|---------|--------|-------------|------------|
| {{SCENE_1}} | {{THEME}} | `#{{HEX}}` | {{LIGHTING}} | {{EFFECT}} |
| {{SCENE_2}} | {{THEME}} | `#{{HEX}}` | {{LIGHTING}} | {{EFFECT}} |

> **[Game Products] Game HUD Color Safety（遊戲 HUD 色彩安全規範）：**
> HUD（抬頭顯示器）元素疊加於場景背景之上，必須在所有場景主色調環境下保持可讀性。
>
> | HUD 元素 | 前景色 | 建議背景處理 | 最低對比度要求 | 備注 |
> |---------|--------|------------|-------------|------|
> | 血量 / 生命值文字 | `neutral-0`（白）| 半透明黑色遮罩（`rgba(0,0,0,0.5)`）| ≥ 4.5:1 on 遮罩 | WCAG AA 正常文字 |
> | 技能冷卻計時 | `neutral-0` | 同上 | ≥ 4.5:1 | |
> | 小地圖圖示 | 語意色（紅/綠/藍）| 深色遮罩（`rgba(0,0,0,0.65)`）| ≥ 3:1（UI 元件）| 色盲友善需加形狀區分 |
> | 提示文字（Quest）| `neutral-0` 或 `warning-500` | 深色遮罩 | ≥ 4.5:1 | |
> | Boss 血量條 | `error-500` 前景 | `neutral-900` 背景條 | ≥ 3:1 | 大型 UI 元件 |
>
> **驗證要求：** 對每個場景截圖（最亮場景 + 最暗場景），使用 Colour Contrast Analyser 對 HUD 元素進行抽樣驗證，確保全場景通過對比度要求。

### 4.5 插畫風格（Illustration Style）
<!-- SaaS / Web App 適用；描述空狀態插畫、Onboarding 插畫、功能說明插畫的風格 -->

| 欄位 | 規格 |
|------|------|
| **插畫風格** | {{E.g. 幾何抽象 / 輕量等距 3D / 手繪線稿 + 水彩}} |
| **人物描繪方式** | {{E.g. 多元膚色 / 抽象無特徵 / 職場場景}} |
| **使用場景** | 空狀態 / Onboarding / 錯誤頁 / 功能說明 |
| **插畫規格** | SVG 向量，最大尺寸 {{MAX_SIZE}}px |
| **色彩限制** | 使用品牌主色盤（§3.1），最多 **5 種色彩**（含黑、白、透明背景）|

**插畫色彩限制詳細規則：**
- **預設上限：5 種填色**（不含透明 / `none` 填色）。計算方式：確認插畫中唯一填色數量 ≤ 5。
- **漸層計算：** 單一線性或放射漸層算作 **1 種色彩**，漸層的起止色必須來自 §3.1 品牌主色盤 Token（不得使用任意色）。
- **品牌色盤對齊：** 所有填色必須完全對應 §3.1 定義的 Token 值（Hex 精確匹配）；禁止使用主色盤以外的自由色。
- **驗證方式：** 確認插畫所有色票均對應 §3.1 定義的 Token 名稱（kebab-case 命名，Hex 精確匹配）。

---

## 5. UI 視覺系統 (UI Visual System)

### 5.1 元件視覺美學（Component Visual Aesthetics）

#### 5.1.1 按鈕（Button）視覺規格

| 變體 | 背景色 | 文字色 | 邊框 | 圓角 | Hover 效果 | Focus 樣式 |
|------|--------|--------|------|------|-----------|-----------|
| Primary | `primary-500` | `neutral-0` | 無 | `button-radius` | `primary-600` + `translateY(-1px)` | `2px solid primary-300` |
| Secondary | `neutral-0` | `primary-500` | `1px solid primary-500` | `button-radius` | `primary-50` 背景 | `2px solid primary-300` |
| Destructive | `error-500` | `neutral-0` | 無 | `button-radius` | `error-600` + shadow | `2px solid error-300` |
| Ghost | transparent | `neutral-700` | 無 | `button-radius` | `neutral-100` 背景 | `2px solid neutral-400` |
| Disabled（所有變體）| — | — | — | — | 不響應（`opacity: 0.4`，`cursor: not-allowed`）| 無 |

**尺寸規格：**

| 尺寸 | 高度 | 水平 Padding | 字體大小 | 圖示尺寸 |
|------|------|------------|---------|---------|
| XS | 28px | 12px | 12px | 14px |
| SM | 32px | 16px | 14px | 16px |
| MD（預設）| 40px | 20px | 16px | 18px |
| LG | 48px | 24px | 18px | 20px |
| XL | 56px | 32px | 20px | 24px |

#### 5.1.2 表單元件（Form Components）視覺規格

| 狀態 | 邊框色 | 邊框寬度 | 背景色 | 說明文字色 |
|------|--------|---------|--------|----------|
| Default | `neutral-300` | 1px | `neutral-0` | `neutral-500` |
| Focused | `primary-500` | 2px | `neutral-0` | `neutral-500` |
| Filled | `neutral-400` | 1px | `neutral-0` | `neutral-700` |
| Error | `error-500` | 2px | `error-50` | `error-600` |
| Disabled | `neutral-200` | 1px | `neutral-100` | `neutral-400` |
| Read-only | `neutral-200` | 1px | `neutral-50` | `neutral-700` |

#### 5.1.3 卡片（Card）視覺規格

| 類型 | 背景 | 邊框 | 陰影 | 圓角 | Hover 效果 |
|------|------|------|------|------|-----------|
| Surface Card | `neutral-0` | `1px solid neutral-200` | `shadow-sm` | `card-radius` | `shadow-md` + `translateY(-2px)` |
| Elevated Card | `neutral-0` | 無 | `shadow-md` | `card-radius` | `shadow-lg` |
| Outlined Card | `neutral-0` | `2px solid neutral-300` | 無 | `card-radius` | `border-color: primary-500` |
| Ghost Card | `neutral-50` | 無 | 無 | `card-radius` | `neutral-100` 背景 |

### 5.2 視覺層次系統（Visual Hierarchy System）

#### 5.2.1 陰影與海拔（Shadow & Elevation）

| 層級 | Token | CSS 值 | 使用場景 |
|------|-------|--------|---------|
| Level 0（無陰影）| `shadow-none` | `none` | 內嵌元素、背景層 |
| Level 1（微陰影）| `shadow-xs` | `0 1px 2px rgb(0 0 0 / 0.05)` | 輸入框、靜態卡片 |
| Level 2（小陰影）| `shadow-sm` | `0 2px 4px rgb(0 0 0 / 0.08)` | 懸停卡片、Tooltip |
| Level 3（中陰影）| `shadow-md` | `0 4px 12px rgb(0 0 0 / 0.12)` | 下拉選單、Popover |
| Level 4（大陰影）| `shadow-lg` | `0 8px 24px rgb(0 0 0 / 0.15)` | Modal、側邊欄 |
| Level 5（最大）| `shadow-xl` | `0 16px 48px rgb(0 0 0 / 0.2)` | 全域遮罩、Dialog |

#### 5.2.2 間距系統（Spatial System）

**基礎單位：4px（0.25rem）**

| Token | 值 | 使用場景 |
|-------|---|---------|
| `space-1` | 4px | 圖示與文字間距 |
| `space-2` | 8px | 元件內部小間距 |
| `space-3` | 12px | 表單元素間距 |
| `space-4` | 16px | 元件標準間距 |
| `space-5` | 20px | 元件寬鬆間距 |
| `space-6` | 24px | 卡片內部間距 |
| `space-8` | 32px | 區塊間距 |
| `space-10` | 40px | 頁面區域間距 |
| `space-12` | 48px | 大區塊間距 |
| `space-16` | 64px | 頁面段落間距 |
| `space-20` | 80px | Section 間距（Desktop）|
| `space-section` | `clamp(4rem, 3rem + 5vw, 10rem)` | 響應式 Section 間距 |

### 5.3 響應式視覺規格（Responsive Visual Spec）

> 字體尺寸欄位顯示各斷點下的實際解析值（px），直接從 §3.2.2 clamp 表達式計算得出，不使用百分比縮放係數。間距縮放以 §5.2.2 Token 為基準說明增減原則。

| Breakpoint | 視覺密度 | `text-display-2xl` 實際值 | `text-display-xl` 實際值 | `text-base` 實際值 | 間距縮放原則 | 版面欄數 |
|-----------|---------|------------------------|------------------------|-------------------|------------|---------|
| Mobile（320px）| 緊湊 | 48px（clamp 下限）| 36px（clamp 下限）| 16px | 使用 `space-4`–`space-8` 為主，`space-section` clamp 下限 64px | 1 欄 |
| Mobile（≤ 639px）| 緊湊 | 48–72px（線性插值）| 36–54px（線性插值）| 16px | 同上 | 1 欄 |
| Tablet（640–1023px）| 標準 | 72–104px（線性插值）| 54–72px（線性插值）| 16px | 使用 `space-6`–`space-12`，`space-section` 約 80–112px | 2 欄 |
| Desktop（1024–1279px）| 標準 | 104–120px（線性插值）| 72px | 16px | 使用完整間距 Token，`space-section` 約 112–144px | 3–4 欄 |
| Large Desktop（≥ 1280px）| 寬鬆 | 128px（clamp 上限）| 72px（clamp 上限）| 16px | `space-section` 上限 160px（clamp 10rem）| 4–6 欄 |

> clamp 計算方式：`text-display-2xl = clamp(3rem, 1rem + 7vw, 8rem)` → 在 320px viewport 時為 max(48px, 1rem + 7vw×320px) = 48px（取下限）；在 1280px 時為 min(128px, 1rem + 89.6px) ≈ 105.6px，達上限 128px 前。各斷點值可使用 [CSS clamp() calculator](https://www.marcbacon.com/tools/clamp-calculator/) 驗算。

### 5.4 版面網格系統（Layout Grid System）

> 本節定義產品的欄位網格規範，所有頁面版型必須依此系統對齊。Gutter 和 Outer Margin 引用 §5.2.2 間距 Token。

**基礎欄位配置：**

| 規格 | 值 | 說明 |
|------|---|------|
| **基礎欄數** | 12 欄 | 所有版型以 12 欄為基礎，根據斷點折疊 |
| **最大容器寬度** | 1280px | 超過此寬度後兩側 Outer Margin 等比延伸 |
| **欄位寬度** | 彈性（Fluid）| 欄寬隨 Viewport 縮放，Gutter 和 Outer Margin 固定 |

**響應式網格規格：**

| Breakpoint | 欄數 | Gutter Token | Gutter 實際值 | Outer Margin Token | Outer Margin 實際值 | 最大容器寬度 |
|-----------|------|-------------|-------------|------------------|-------------------|------------|
| Mobile（≤ 639px）| 4 欄 | `space-4` | 16px | `space-4` | 16px | 100% |
| Tablet（640–1023px）| 8 欄 | `space-6` | 24px | `space-6` | 24px | 100% |
| Desktop（1024–1279px）| 12 欄 | `space-8` | 32px | `space-8` | 32px | 1024px |
| Large Desktop（≥ 1280px）| 12 欄 | `space-8` | 32px | `space-12` | 48px | 1280px |

**版面置放規則：**
- 所有內容元件必須對齊欄位邊緣，不得跨出 Outer Margin 範圍（除全出血 Full-bleed 設計有明確標注外）
- 全出血（Full-bleed）背景區塊：背景色可延伸至 Viewport 邊緣，但內容仍限制在容器欄位內
- 元件橫跨欄數：主要內容區塊佔 8/12 欄（桌面），側邊欄 / 補充資訊佔 4/12 欄；行動版退化為 4/4 欄全寬
- 卡片網格間距統一使用 Gutter Token（對應斷點），不得使用硬編碼值

### 5.5 載入與回饋狀態視覺規格（Loading & Feedback States Visual Spec）

#### 5.5.1 Skeleton 骨架屏

| 規格 | 值 | 說明 |
|------|---|------|
| **圓角** | `input-radius`（`radius.sm` = 4px）| 所有 Skeleton 區塊統一使用小圓角 |
| **背景色（Light）** | `neutral-200`（`#E5E7EB`）| 基底灰色 |
| **背景色（Dark）** | `neutral-700`（`#374151`）| Dark Mode 基底色 |
| **Shimmer 漸層** | `linear-gradient(90deg, transparent 0%, neutral-100 50%, transparent 100%)` | 由左至右掃過的光澤效果 |
| **Shimmer 動畫** | `anim-skeleton-shimmer`（見 §6.3.1）| 1500ms 線性無限循環 |
| **`prefers-reduced-motion` 替代** | 靜態顯示，移除 Shimmer 動畫 | 僅顯示靜態背景色 |

**Skeleton 使用場景：**
- 卡片列表首次載入（高度與實際內容一致）
- 使用者個人資訊區塊
- 圖片佔位（維持 `aspect-ratio` 防止 CLS）

#### 5.5.2 Spinner 旋轉指示器

| 尺寸 | 直徑 | 線寬 | 使用場景 |
|------|------|------|---------|
| XS | 16px | 2px | 按鈕內嵌 Loading 狀態 |
| SM | 20px | 2px | 小型元件、Inline 載入 |
| MD（預設）| 24px | 3px | 區塊載入指示 |
| LG | 32px | 3px | 頁面 / Dialog 全螢幕載入 |

- 色彩：前景使用 `color-action-primary`，背景軌道使用 `neutral-200`（Light）/ `neutral-700`（Dark）
- 動畫：360° 旋轉，`duration-loading`（1500ms），`ease-linear`，無限循環

#### 5.5.3 進度條（Progress Bar）

| 規格 | 值 |
|------|---|
| **高度** | 4px（緊湊）/ 8px（標準）|
| **圓角** | `radius.full`（9999px，膠囊形）|
| **前景色** | `color-action-primary` |
| **背景色** | `neutral-200`（Light）/ `neutral-700`（Dark）|
| **動態進度** | CSS `width` 從 0% 過渡至目標值，`transition: width duration-normal ease-standard` |
| **不確定態（Indeterminate）** | Shimmer 效果同 Skeleton，或前景塊左右往返動畫 |

#### 5.5.4 Toast / Notification 提示

| 規格 | 值 | 說明 |
|------|---|------|
| **尺寸** | 最小寬度 280px，最大寬度 480px | 響應式自適應 |
| **圓角** | `card-radius`（`radius.md` = 8px）| 與卡片一致 |
| **陰影** | `shadow-lg` | 確保浮於頁面內容之上 |
| **出現動畫** | `anim-toast-enter`（見 §6.3.1）| 從底部滑入 |
| **消失動畫** | `anim-toast-exit`（見 §6.3.1）| 向底部滑出 |
| **自動關閉** | 4000ms（資訊 / 成功）/ 不自動關閉（錯誤）| |
| **語意顏色** | Success: `color-feedback-success` / Error: `color-feedback-error` / Warning: `color-feedback-warning` / Info: `color-action-primary` | 左側色條寬度 4px |
| **圖示** | 各語意類型對應圖示（24px），來自 §3.3.2 圖示系統 | |

---

## 6. Design Token → 工程交付 (Design Tokens → Engineering)

### 6.1 Token 分類架構（Token Taxonomy）

> 遵循 W3C Design Tokens Community Group 規範與三層架構。

**Layer 1 — Primitive Tokens（原始值層）**
> 定義系統中所有原子值，不帶語意含義，不直接用於元件

```json
{
  "color": {
    "blue": {
      "50":  { "value": "#eff6ff" },
      "500": { "value": "#3b82f6" },
      "900": { "value": "#1e3a8a" }
    },
    "neutral": {
      "0":   { "value": "#ffffff" },
      "900": { "value": "#111827" }
    }
  },
  "font-size": {
    "12": { "value": "0.75rem" },
    "16": { "value": "1rem" },
    "24": { "value": "1.5rem" }
  },
  "spacing": {
    "4":  { "value": "0.25rem" },
    "16": { "value": "1rem" },
    "64": { "value": "4rem" }
  },
  "radius": {
    "sm": { "value": "4px" },
    "md": { "value": "8px" },
    "lg": { "value": "12px" },
    "full": { "value": "9999px" }
  }
}
```

**Layer 2 — Semantic Tokens（語意層）**
> 定義「用在哪裡」，賦予設計意圖，支援主題切換

| Token | Light 引用 | Dark 引用 | 語意說明 |
|-------|-----------|----------|---------|
| `color-action-primary` | `color.blue.500` | `color.blue.400` | 主要互動色 |
| `color-action-primary-hover` | `color.blue.600` | `color.blue.300` | 主要互動懸停 |
| `color-text-primary` | `color.neutral.900` | `color.neutral.50` | 主要文字 |
| `color-text-secondary` | `color.neutral.600` | `color.neutral.400` | 次要文字 |
| `color-surface-default` | `color.neutral.0` | `color.neutral.900` | 預設表面背景 |
| `color-surface-raised` | `color.neutral.50` | `color.neutral.800` | 凸起表面背景 |
| `color-border-default` | `color.neutral.200` | `color.neutral.700` | 預設邊框 |
| `color-feedback-error` | `color.red.500` | `color.red.400` | 錯誤回饋 |
| `color-feedback-success` | `color.green.500` | `color.green.400` | 成功回饋 |
| `spacing-component-inner` | `spacing.16` | — | 元件內部間距 |
| `spacing-section` | `spacing.64` | — | 頁面區塊間距 |
| `radius-component` | `radius.md` | — | 元件通用圓角 |

**Layer 3 — Component Tokens（元件層）**
> 最終 Token 名稱與元件強綁定

| Token | 引用 Semantic Token | 元件位置 |
|-------|-------------------|---------|
| `button-primary-bg` | `color-action-primary` | Primary Button 背景 |
| `button-primary-bg-hover` | `color-action-primary-hover` | Primary Button 懸停背景 |
| `button-primary-text` | `color.neutral.0` | Primary Button 文字 |
| `input-border-default` | `color-border-default` | 輸入框預設邊框 |
| `input-border-focus` | `color-action-primary` | 輸入框聚焦邊框 |
| `input-border-error` | `color-feedback-error` | 輸入框錯誤邊框 |
| `button-radius` | `radius.md` | 按鈕圓角（所有尺寸變體共用）|
| `input-radius` | `radius.sm` | 輸入框、下拉選單、Textarea 圓角 |
| `card-bg` | `color-surface-default` | 卡片背景 |
| `card-radius` | `radius-component` | 卡片圓角 |
| `card-shadow` | `shadow-sm` | 卡片陰影 |

### 6.2 Dark / Light Mode Token Mapping（主題切換對照）

<!-- 適用範圍：SaaS / Web App、Desktop App、Mobile App。遊戲產品的深色場景視覺規格由 §4.4 Environment & Scene Art 管理；遊戲 HUD 對比度規範見 §4.4 Game HUD Color Safety。 -->

| Semantic Token | Light Mode | Dark Mode | WCAG 對比度（on surface）| 說明 |
|---------------|-----------|----------|:----------------------:|------|
| `color-text-primary` | `#111827` | `#F9FAFB` | 16.9:1 AAA | 主要文字 |
| `color-text-secondary` | `#6B7280` | `#9CA3AF` | 4.6:1 AA | 輔助說明文字 |
| `color-text-disabled` | `#D1D5DB` | `#4B5563` | — | 禁用（非內容）|
| `color-surface-default` | `#FFFFFF` | `#111827` | — | 頁面主背景 |
| `color-surface-raised` | `#F9FAFB` | `#1F2937` | — | 卡片 / 面板背景 |
| `color-surface-elevated` | `#FFFFFF` | `#374151` | — | 浮層 / Dropdown |
| `color-action-primary` | `#3B82F6` | `#60A5FA` | 4.5:1 AA | 主要 CTA |
| `color-border-default` | `#E5E7EB` | `#374151` | — | 分隔線 / 邊框 |
| `color-border-focus` | `#3B82F6` | `#60A5FA` | 3:1 UI Component | 焦點環 |
| `color-feedback-error` | `#EF4444` | `#FCA5A5` | 4.5:1 AA | 錯誤提示 |
| `color-feedback-success` | `#10B981` | `#6EE7B7` | 4.5:1 AA | 成功提示 |
| `color-feedback-warning` | `#F59E0B` | `#FCD34D` | 4.5:1 AA | 警告提示 |

**主題切換實作規範：**

```css
/* CSS Custom Properties 實作 */
:root {
  --color-text-primary: #111827;
  --color-surface-default: #ffffff;
  --color-action-primary: #3b82f6;
  /* ... 其餘 token ... */
}

[data-theme="dark"] {
  --color-text-primary: #f9fafb;
  --color-surface-default: #111827;
  --color-action-primary: #60a5fa;
  /* ... 其餘 token ... */
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    /* 跟隨系統且無手動設定時生效 */
    --color-text-primary: #f9fafb;
    /* ... */
  }
}
```

**禁止事項：**
- 禁止在元件 CSS 中直接使用 `#hex` 顏色值
- 禁止只定義單一主題 Token（Light 與 Dark 必須同時定義）
- 禁止 Token 命名使用具體色彩（如 `--blue-button`），應使用語意名稱

### 6.3 動效 Token（Motion Tokens）

| Token | 值 | 使用場景 |
|-------|---|---------|
| `duration-instant` | `50ms` | 游標跟隨、滑入指示 |
| `duration-fast` | `150ms` | 按鈕按壓、Hover 切換 |
| `duration-normal` | `300ms` | 元件進場、Dropdown 開啟 |
| `duration-slow` | `500ms` | 頁面轉場、Modal 出現 |
| `duration-loading` | `1500ms` | Skeleton Shimmer 循環 |
| `ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | 元件進場、彈出 |
| `ease-in-expo` | `cubic-bezier(0.55, 0, 1, 0.45)` | 元件退場、消失 |
| `ease-standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | 一般狀態切換 |
| `ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 彈性進場、收藏動畫 |
| `ease-linear` | `linear` | Spinner、進度條 |

**`prefers-reduced-motion` 規範：**

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

#### 6.3.1 Composite Animation Recipes（複合動畫配方）

> 定義由多個動畫屬性組合而成的標準動畫配方，供設計師與工程師共同引用。Duration 和 Easing 欄位引用 §6.3 動效 Token 名稱。

| 動畫名稱 | 動畫屬性 | 起始值（From）| 結束值（To）| Duration Token | Easing Token | 序列方式 | Transform Origin |
|---------|---------|------------|-----------|---------------|-------------|---------|----------------|
| `anim-modal-enter` | `opacity`, `transform` | `opacity: 0; transform: scale(0.95)` | `opacity: 1; transform: scale(1)` | `duration-normal` | `ease-out-expo` | parallel | `center center` |
| `anim-modal-exit` | `opacity`, `transform` | `opacity: 1; transform: scale(1)` | `opacity: 0; transform: scale(0.95)` | `duration-fast` | `ease-in-expo` | parallel | `center center` |
| `anim-dropdown-enter` | `opacity`, `transform` | `opacity: 0; transform: translateY(-8px)` | `opacity: 1; transform: translateY(0)` | `duration-normal` | `ease-out-expo` | parallel | `top center` |
| `anim-dropdown-exit` | `opacity`, `transform` | `opacity: 1; transform: translateY(0)` | `opacity: 0; transform: translateY(-8px)` | `duration-fast` | `ease-in-expo` | parallel | `top center` |
| `anim-toast-enter` | `opacity`, `transform` | `opacity: 0; transform: translateY(16px)` | `opacity: 1; transform: translateY(0)` | `duration-normal` | `ease-out-expo` | parallel | `bottom center` |
| `anim-toast-exit` | `opacity`, `transform` | `opacity: 1; transform: translateY(0)` | `opacity: 0; transform: translateY(16px)` | `duration-fast` | `ease-in-expo` | parallel | `bottom center` |
| `anim-page-transition` | `opacity`, `transform` | `opacity: 0; transform: translateX(24px)` | `opacity: 1; transform: translateX(0)` | `duration-slow` | `ease-out-expo` | parallel | `center center` |
| `anim-card-list-stagger` | `opacity`, `transform` | `opacity: 0; transform: translateY(12px)` | `opacity: 1; transform: translateY(0)` | `duration-normal` | `ease-out-expo` | staggered（每項 +50ms delay）| `top center` |
| `anim-button-press` | `transform` | `transform: scale(1)` | `transform: scale(0.97)` | `duration-fast` | `ease-standard` | parallel | `center center` |
| `anim-skeleton-shimmer` | `background-position` | `background-position: -200% 0` | `background-position: 200% 0` | `duration-loading` | `ease-linear` | loop（infinite）| — |

**使用說明：**
- Staggered 動畫：列表元件中每個子元素的 `animation-delay` 累加，公式為 `base-delay + (index × stagger-step)`，stagger-step 預設 50ms。
- 所有 Composite Recipe 在 `prefers-reduced-motion: reduce` 環境下應退化為純 `opacity` 淡入淡出，移除所有 `transform` 動畫。
- Transform Origin 應在 CSS 中明確宣告，避免瀏覽器預設值造成非預期的縮放中心。

### 6.4 Token 輸出格式與交付

| 格式 | 用途 | 產出位置 |
|------|------|---------|
| CSS Custom Properties | Web 前端 | `src/styles/tokens.css` |
| JavaScript / TypeScript | JS 邏輯層 | `src/lib/tokens.ts` |
| JSON（W3C DTCG 格式）| Token Studio / Style Dictionary | `tokens/tokens.json` |
| Android XML | Android 原生 | `res/values/design_tokens.xml` |
| iOS Swift | iOS 原生 | `DesignTokens.swift` |

**Token 管理工具：** {{TOKEN_TOOL}}（e.g. Style Dictionary / Amazon Style Dictionary / custom scripts）

**Style Dictionary 最小配置（`config.json`）：**

```json
{
  "source": ["tokens/**/*.json"],
  "platforms": {
    "css": {
      "transformGroup": "css",
      "buildPath": "src/styles/",
      "files": [
        {
          "destination": "tokens.css",
          "format": "css/variables",
          "options": {
            "outputReferences": true,
            "selector": ":root"
          }
        }
      ]
    },
    "css-dark": {
      "transformGroup": "css",
      "buildPath": "src/styles/",
      "files": [
        {
          "destination": "tokens-dark.css",
          "format": "css/variables",
          "filter": "isDarkToken",
          "options": {
            "outputReferences": true,
            "selector": "[data-theme=\"dark\"]"
          }
        }
      ]
    },
    "js": {
      "transformGroup": "js",
      "buildPath": "src/lib/",
      "files": [
        {
          "destination": "tokens.ts",
          "format": "javascript/es6"
        }
      ]
    },
    "json": {
      "transformGroup": "js",
      "buildPath": "tokens/",
      "files": [
        {
          "destination": "tokens.w3c.json",
          "format": "json/nested"
        }
      ]
    },
    "android": {
      "transformGroup": "android",
      "buildPath": "android/app/src/main/res/values/",
      "files": [
        {
          "destination": "design_tokens.xml",
          "format": "android/resources"
        }
      ]
    },
    "ios-swift": {
      "transformGroup": "ios-swift",
      "buildPath": "ios/",
      "files": [
        {
          "destination": "DesignTokens.swift",
          "format": "ios-swift/class.swift",
          "options": {
            "className": "DesignTokens"
          }
        }
      ]
    }
  }
}
```

**預期輸出檔案：**
- `src/styles/tokens.css` — CSS Custom Properties（Light Mode）
- `src/styles/tokens-dark.css` — CSS Custom Properties（Dark Mode，`[data-theme="dark"]` 選擇器）
- `src/lib/tokens.ts` — TypeScript ES6 模組匯出
- `tokens/tokens.w3c.json` — W3C DTCG 格式 JSON
- `android/app/src/main/res/values/design_tokens.xml` — Android XML 資源
- `ios/DesignTokens.swift` — iOS Swift 類別

---

## 7. 資產管線規格 (Asset Pipeline Specification)

### 7.1 資產類型與格式規範

| 資產類型 | 主要格式 | 備用格式 | 最大尺寸 | 命名規則 |
|---------|---------|---------|---------|---------|
| UI 圖示 | SVG | PNG 2x | 單圖示 ≤ 5KB | `icon-{name}-{size}.svg` |
| 插畫 | SVG | WebP | ≤ 100KB | `illus-{scene}-{variant}.svg` |
| 角色精靈圖（遊戲）| PNG（Sprite Sheet）| WebP | ≤ 512KB | `char-{name}-{action}.png` |
| 背景場景（遊戲）| WebP | AVIF | ≤ 2MB | `bg-{scene}-{resolution}.webp` |
| 品牌 Logo | SVG | PNG 3x | SVG ≤ 10KB | `logo-{variant}-{color}.svg` |
| Hero 圖像 | AVIF | WebP / JPEG | ≤ 300KB | `hero-{page}-{breakpoint}.avif` |
| 一般圖片 | WebP | JPEG | ≤ 150KB | `img-{context}-{descriptor}.webp` |
| 縮圖 | WebP | JPEG | ≤ 30KB | `thumb-{context}-{id}.webp` |

### 7.2 命名規範（Naming Conventions）

```
{category}-{descriptor}-{variant}-{size}@{density}.{format}

範例：
  icon-arrow-right-24.svg
  btn-primary-hover.png
  char-protagonist-idle-128@2x.png
  bg-forest-day-1920.webp
  logo-primary-white.svg
  illus-empty-state-search.svg
```

**命名規則：**
- 全小寫，單字間用 `-` 連接
- 禁止空格、中文、特殊字元
- 尺寸後綴使用 `@2x`、`@3x` 標記解析度倍數
- 深色版資產加 `-dark` 後綴

### 7.3 圖片規格詳細說明

| 使用場景 | 最大寬度 | 格式優先序 | `loading` 屬性 | `fetchpriority` |
|---------|---------|----------|--------------|----------------|
| Hero / 首屏主視覺 | 1920px | AVIF > WebP > JPEG | `eager` | `high` |
| 卡片縮圖 | 600px | WebP > JPEG | `lazy` | — |
| 角色插圖 | 800px | WebP > PNG | `lazy` | — |
| 背景場景 | 2560px | WebP > JPEG | `lazy` | — |
| 圖示 | 向量 | SVG（優先）> PNG | — | — |
| 頭像 / Avatar | 256px | WebP > JPEG | `lazy` | — |

**圖片最佳化規範：**
- 所有 `<img>` 必須指定明確的 `width` 和 `height`（防止 CLS）
- Hero 圖片必須提供 `srcset`（320w / 768w / 1280w / 1920w）
- 使用 `<picture>` 元素提供 AVIF + WebP + JPEG 多格式降級

### 7.4 Design Token → Code 交付規範（Design-to-Code Handoff）

**交付流程：**

1. VDD 中所有 Design Token 已定義至 `src/tokens/` 目錄下的 JSON/YAML（Style Dictionary 格式）
2. 執行 Style Dictionary build，生成 `src/styles/tokens.css`（CSS 自訂屬性）和 `src/lib/tokens.ts`（TypeScript 型別）
3. 可匯出資產已輸出至 `public/assets/`，並在 §7.1-7.3 中標注路徑和格式要求
4. CI 驗證 Token JSON → CSS 的一致性，發現漂移即阻塞 PR

**資產命名規範：**

```
Token 名稱：  kebab-case（e.g. color-primary-500, shadow-card-default）
CSS 變數：    --{token-name}（e.g. --color-primary-500）
Icon 檔案：   {icon-name}.svg（e.g. arrow-right.svg）
插畫檔案：    {illustration-name}.svg（e.g. empty-state-search.svg）
圖片資產：    {asset-name}@{density}.{ext}（e.g. hero-banner@2x.webp）
```

**交付檢查清單：**

- [ ] 所有元件均有完整的互動狀態（Default / Hover / Focus / Active / Disabled）
- [ ] 所有 Design Token 已定義在 `src/tokens/` 並通過 Style Dictionary build
- [ ] 圖示已匯出至 `src/assets/icons/` 並設定 SVG Export 格式
- [ ] 所有圖片已標注尺寸規格和格式要求（§7.3）
- [ ] 動效規格（timing / easing）已在 §6.3 動效 Token 中標注
- [ ] 無障礙注釋（Accessibility Annotation）已完成（§9）
- [ ] 響應式規格已涵蓋所有需要的 Breakpoint（§5.3）

---

## 8. 畫面視覺規格 (Screen Visual Specifications)

### 8.1 {{SCREEN_NAME_1}}（{{SCREEN_FUNCTION_1}}）

**視覺目標：** {{VISUAL_OBJECTIVE}}（對應 PDD §5.{{N}}）

**關鍵視覺決策：**
- {{VISUAL_DECISION_1}}（e.g. 使用大字重標題 + 留白製造呼吸感）
- {{VISUAL_DECISION_2}}（e.g. 主要 CTA 使用品牌主色，視覺重量最重）
- {{VISUAL_DECISION_3}}（e.g. 背景使用材質或漸層增加層次）

**版面視覺結構：**
```
┌─────────────────────────────────────────┐
│  [Header] logo + nav（neutral-0 bg）      │
│  border-bottom: 1px neutral-200          │
├─────────────────────────────────────────┤
│  [Hero] text-display-xl                  │
│  background: {{HERO_BG_SPEC}}            │
│  padding: space-20 vertical              │
├─────────────────────────────────────────┤
│  [Content Grid] {{COLUMN_SPEC}}          │
│  gap: space-6 / space-8 on desktop       │
│  ├── [Card] shadow-sm + radius-md        │
│  ├── [Card] shadow-sm + radius-md        │
│  └── [Card] shadow-sm + radius-md        │
├─────────────────────────────────────────┤
│  [CTA Section] primary-500 背景          │
│  color: neutral-0 / padding: space-16    │
└─────────────────────────────────────────┘
```

**視覺注釋：**

| 元素 | 視覺規格 | Token 引用 | 說明 |
|------|---------|-----------|------|
| 頁面背景 | `#F9FAFB` | `color-surface-raised` | 低飽和背景製造層次 |
| 標題字 | 36px / 700 / -0.02em | `text-display-lg` | 大字重製造視覺衝擊 |
| 主要 CTA | 40px 高 / primary-500 背景 | `button-primary-bg` | 視覺重量最高 |
| 卡片 | 12px 圓角 / shadow-sm | `card-radius`, `card-shadow` | 柔和邊角符合品牌調性 |

---

### 8.2 {{SCREEN_NAME_2}}（{{SCREEN_FUNCTION_2}}）

**視覺目標：** {{VISUAL_OBJECTIVE_2}}（對應 PDD §5.{{N}}）

**關鍵視覺決策：**
- {{VISUAL_DECISION_1}}（e.g. 使用分欄版型清楚區分主內容與側邊操作區）
- {{VISUAL_DECISION_2}}（e.g. 表單元件使用 input-radius + focused 邊框色製造清晰焦點感）
- {{VISUAL_DECISION_3}}（e.g. 空狀態使用插畫搭配品牌色引導使用者行動）

**版面視覺結構：**
```
┌─────────────────────────────────────────┐
│  [Header] logo + nav（neutral-0 bg）      │
│  border-bottom: 1px neutral-200          │
├─────────────────────────────────────────┤
│  [Page Title] text-display-lg            │
│  background: {{PAGE_BG_SPEC}}            │
│  padding: space-8 vertical               │
├──────────────────────┬──────────────────┤
│  [Main Content]      │  [Sidebar]        │
│  8/12 欄             │  4/12 欄          │
│  ├── {{CONTENT_1}}   │  ├── {{WIDGET_1}} │
│  ├── {{CONTENT_2}}   │  └── {{WIDGET_2}} │
│  └── {{CONTENT_3}}   │                   │
├─────────────────────────────────────────┤
│  [Footer] neutral-100 背景               │
│  color: neutral-600 / padding: space-8   │
└─────────────────────────────────────────┘
```

**視覺注釋：**

| 元素 | 視覺規格 | Token 引用 | 說明 |
|------|---------|-----------|------|
| 頁面背景 | `#F9FAFB` | `color-surface-raised` | 與卡片 `neutral-0` 形成層次 |
| 頁面標題 | 30px / 700 / -0.01em | `text-display-lg` | 清晰的層次錨點 |
| 主內容區域 | neutral-0 背景 / shadow-sm | `card-bg`, `card-shadow` | 白卡浮在頁面底色上 |
| 側邊欄背景 | neutral-50 | `color-surface-raised` | 低對比區分功能區 |
| 互動按鈕 | 40px 高 / primary-500 | `button-primary-bg`, `button-radius` | 主要操作視覺重量最高 |
| 輸入框 | 1px neutral-300 邊框 / input-radius | `input-border-default`, `input-radius` | 收斂的表單視覺風格 |

---

## 9. 無障礙與包容性設計 (Accessibility & Inclusive Design)

### 9.1 色彩無障礙

| 檢查項目 | 標準 | 驗證工具 |
|---------|------|---------|
| 正文色彩對比度 | ≥ 4.5:1（WCAG AA）| Colour Contrast Analyser / axe |
| 大字（≥ 18px 或 ≥ 14px 粗體）對比度 | ≥ 3:1 | axe-core |
| UI 元件邊框 / 圖示對比度 | ≥ 3:1 | axe-core |
| 色盲友善（不依賴單一色彩傳遞資訊）| 加圖示 / 文字標籤 | Sim Daltonism |
| Dark Mode 下所有 Token 對比度 | 全部 ≥ AA | 手動逐一驗證 |

### 9.2 排版無障礙

| 檢查項目 | 規格 |
|---------|------|
| 最小字體大小 | 12px（建議 14px+）|
| 行距 | ≥ 1.5 倍字體大小 |
| 段落間距 | ≥ 2 倍字體大小 |
| 字距（Letter Spacing）| 不小於 -0.05em |
| 瀏覽器縮放至 200% | 不得水平溢出，不得遮蓋功能 |
| 使用相對單位（rem / em）| 禁止 px 鎖定字體大小 |

### 9.3 動效無障礙

| 場景 | 標準行為 | `prefers-reduced-motion` 替代 |
|------|---------|------------------------------|
| 頁面轉場 | Slide + Fade 300ms | Fade only 150ms |
| 元件進場 | Scale + Fade | Fade only |
| Skeleton Shimmer | 1.5s 循環動畫 | 靜態顯示（無動畫）|
| Parallax 效果 | 捲動差速位移 | 完全禁用（`transform: none`）|
| Auto-play 影片 / GIF | 播放 | 暫停（`prefers-reduced-motion: reduce`）|

### 9.4 包容性設計考量

| 面向 | 設計規範 |
|------|---------|
| **多元文化** | 插畫人物涵蓋多元膚色；避免地區性歧視圖示 |
| **性別中立** | 人物圖示不預設性別；文案使用中性稱謂 |
| **年齡友善** | 關鍵文字 ≥ 14px；觸控目標 ≥ 44×44px |
| **認知負荷** | 單頁最多 3 個主要動作；避免閃爍和過多動畫 |
| **低頻寬環境** | 圖片提供低解析度替代；Progressive loading |
| **單手操作** | 手機關鍵操作區域集中於拇指可達範圍 |

### 9.5 WCAG 2.1 AA 視覺設計合規矩陣

| WCAG 準則 | 等級 | 視覺設計要求 | 執行方式 | 優先 |
|----------|:---:|------------|---------|:---:|
| 1.1.1 非文字內容 | AA | 圖示 / 插畫有替代文字 | `alt` / `aria-label` | M |
| 1.4.1 色彩使用 | A | 不以顏色為唯一資訊媒介 | 加圖示 + 文字標籤 | M |
| 1.4.3 對比度（正常文字）| AA | ≥ 4.5:1 | Design Token 驗證 | M |
| 1.4.4 調整文字大小 | AA | 200% 縮放不失功能 | 使用 rem / em 單位 | M |
| 1.4.10 重新排版 | AA | 320px 寬度不橫向捲動 | Mobile-first 設計 | M |
| 1.4.11 非文字對比度 | AA | UI 元件邊框 ≥ 3:1 | Token 設計時驗證 | M |
| 1.4.12 文字間距 | AA | 行距 / 段距可調整 | 相對單位 | R |
| 1.4.13 游標懸停內容 | AA | Tooltip 可被關閉 | 設計 Dismiss 機制 | R |
| 2.3.1 三次閃爍 | A | 不超過每秒 3 次閃爍 | 動效設計審查 | M |

*M = 強制（上線前必須通過）；R = 建議（最佳實踐）*

---

## 10. 開放問題 (Open Questions)

| # | 問題 | 影響範圍 | 負責人 | 截止日 | 狀態 |
|---|------|---------|--------|--------|------|
| Q1 | {{VISUAL_QUESTION_1}}（e.g. 是否採用深色模式作為預設？）| Token 系統、全部畫面 | {{OWNER}} | {{DATE}} | OPEN |
| Q2 | {{VISUAL_QUESTION_2}}（e.g. 品牌主色最終選用哪個色號？）| 色彩系統 | {{OWNER}} | {{DATE}} | RESOLVED：{{ANSWER}} |
| Q3 | {{VISUAL_QUESTION_3}}（e.g. 圖示庫選用自建或採購？）| 資產管線 | {{OWNER}} | {{DATE}} | OPEN |

---

## 11. 工程交付規格 (Engineering Handoff Specification)

### 11.1 視覺 QA 流程

| 階段 | 工具 | 標準 | 時機 |
|------|------|------|------|
| 像素比對 | Playwright 截圖 / Percy | 關鍵畫面無視覺回歸 | 每次 PR |
| Design Token 驗證 | Style Dictionary CI | Token JSON 與生成的 CSS 100% 一致 | 每次 Token 更新 |
| 色彩對比度 | axe-core / Lighthouse | 全部 AA 合規 | 每次 PR |
| 響應式驗證 | Playwright 多 Viewport | 320 / 768 / 1024 / 1440 截圖 | 每次 PR |
| 動效驗證 | 手動 + `prefers-reduced-motion` | 所有動畫有降級方案 | Sprint Review |

### 11.2 資產交付清單

- [ ] Logo SVG（主版、深色版、符號版）已交付
- [ ] 圖示庫 SVG 已匯出至 `src/assets/icons/`
- [ ] 插畫 SVG / WebP 已匯出至 `src/assets/illustrations/`
- [ ] 所有 Design Token 已同步至程式碼（CSS / JSON / TS），Style Dictionary build 通過
- [ ] 字型檔案（`.woff2`）已放置至 `public/fonts/`
- [ ] 資產命名符合 §7.4 交付規範（kebab-case）
- [ ] §7.4 Engineering Handoff Checklist 所有項目已完成

### 11.3 設計→工程溝通協議

- 視覺設計變更在進入 Sprint 後需 Art Director + PM 雙重確認
- 工程師若發現視覺偏差，開 issue 標注問題並 @{{VISUAL_DESIGNER}}，於 {{N}} 個工作日內回應
- 新增 / 修改 Design Token 必須同時更新 `src/tokens/` 的 Token 定義和執行 Style Dictionary build
- 資產命名不符規範時，工程師有權退回並要求重新命名

### 11.4 VDD → FRONTEND.md 交叉對照（VDD → FRONTEND Cross-Reference）

> 本表列出 VDD 各章節所定義的視覺規格，及其對應的 FRONTEND.md 實作章節，確保設計意圖完整傳遞至前端工程交付。

| VDD 章節 | VDD 主題 | 對應 FRONTEND.md 章節 |
|---------|---------|---------------------|
| §3.1 | 色彩體系（Brand Palette、Color Scale、Semantic Colors）| FRONTEND §2（Design Tokens / CSS Custom Properties）|
| §3.2 | 字體系統（Type Scale、Font Loading）| FRONTEND §3（Typography / Font Loading Strategy）|
| §3.3 | 圖示系統（Icon System）| FRONTEND §7（Asset Pipeline / Icon Usage）|
| §5.1 | 元件視覺美學（Button、Form、Card 視覺規格）| FRONTEND §4（Component Library / UI Components）|
| §5.2.1 | 陰影與海拔（Shadow & Elevation）| FRONTEND §2（Design Tokens — Shadow Tokens）|
| §5.2.2 | 間距系統（Spatial System）| FRONTEND §2（Design Tokens — Spacing Tokens）|
| §5.3 | 響應式視覺規格（Breakpoints、字體實際值）| FRONTEND §5（Responsive Layout / Breakpoint System）|
| §5.4 | 版面網格系統（Grid System、Container、Gutter）| FRONTEND §5（Responsive Layout / Grid Implementation）|
| §5.5 | 載入與回饋狀態視覺規格（Skeleton、Spinner、Toast）| FRONTEND §6（Loading States / Feedback Components）|
| §6.1 | Design Token 三層架構（Primitive / Semantic / Component）| FRONTEND §2（Design Tokens — Token Architecture）|
| §6.2 | Dark / Light Mode Token Mapping | FRONTEND §2（Design Tokens — Theme Switching）|
| §6.3 | 動效 Token（Duration、Easing）| FRONTEND §8（Animation / Motion Implementation）|
| §6.3.1 | Composite Animation Recipes | FRONTEND §8（Animation Recipes / Keyframe Definitions）|
| §6.4 | Token 輸出格式（CSS / JSON / TS、Style Dictionary）| FRONTEND §2（Build Pipeline / Token Generation）|
| §7.1 | 資產類型與格式規範 | FRONTEND §7（Asset Formats / Image Optimization）|
| §7.3 | 圖片規格（loading、fetchpriority、srcset）| FRONTEND §7（Image Component / Performance）|
| §7.4 | Design Token → Code 交付規範 | FRONTEND §1（Project Setup / Design Handoff Process）|
| §9 | 無障礙與包容性設計（WCAG 合規矩陣）| FRONTEND §9（Accessibility Implementation）|
| §11.1 | 視覺 QA 流程 | FRONTEND §10（QA / Testing — Visual Regression）|

---

## 12. 參考文件 (References)

- PDD（UX / Interaction Design）：[PDD.md](PDD.md)
- PRD（產品需求）：[PRD.md](PRD.md)
- EDD（工程設計）：[EDD.md](EDD.md)
- FRONTEND（前端實作）：[FRONTEND.md](FRONTEND.md)
- 品牌指南：{{BRAND_GUIDE_LINK}}
- Mood Board：{{MOODBOARD_LINK}}
- W3C Design Tokens 規範：https://www.w3.org/community/design-tokens/
- WCAG 2.1 Guidelines：https://www.w3.org/TR/WCAG21/
- W3C OKLCH 色彩模型：https://www.w3.org/TR/css-color-4/#ok-lab

---

## 13. Admin UI 設計規範（condition: has_admin_backend=true）

> **條件章節**：僅在 `has_admin_backend = true` 時填寫。若無 Admin 後台，標記「不適用」即可。

### 13.1 Admin 配色方案

Admin Portal 採 Professional / Neutral 方向，與前台品牌色彩刻意區隔，減少使用者對前後台的混淆。

| Token 名稱 | 用途 | 預設值（可依品牌調整） |
|-----------|------|----------------------|
| `--admin-sidebar-bg` | Sidebar 背景 | `#111827`（Tailwind gray-900） |
| `--admin-nav-text` | Sidebar 文字 | `#f9fafb`（gray-50） |
| `--admin-nav-accent` | Sidebar active/hover 強調色 | `#2d9ef5`（與主題 accent 同色或相近） |
| `--admin-content-bg` | 主內容區背景 | `#f6f8fa`（淺灰） |
| `--admin-surface` | 卡片 / 表格背景 | `#ffffff` |
| `--admin-border` | 分隔線、表格邊框 | `#e1e4e8` |
| `--admin-text` | 主要文字 | `#24292e` |
| `--admin-text-muted` | 次要文字（標籤、說明） | `#586069` |
| `--admin-accent` | CTA 按鈕、連結、active 狀態 | `#2d9ef5` |
| `--admin-success` | 狀態 Badge：成功 / 啟用 | `#22c55e` |
| `--admin-warning` | 狀態 Badge：警告 / 待確認 | `#f59e0b` |
| `--admin-error` | 狀態 Badge：錯誤 / 鎖定 | `#ef4444` |
| `--admin-table-stripe` | 表格偶數行背景 | `#fafbfc` |

**WCAG 對比度驗證（必達 AA）：**

| 前景 | 背景 | 對比度 | 合規 |
|------|------|--------|------|
| `--admin-nav-text` `#f9fafb` | `--admin-sidebar-bg` `#111827` | ≥ 15:1 | ✅ AAA |
| `--admin-text` `#24292e` | `--admin-surface` `#ffffff` | ≥ 12:1 | ✅ AAA |
| `--admin-accent` `#2d9ef5` | `--admin-surface` `#ffffff` | ≥ 4.5:1 | ✅ AA |

---

### 13.2 Admin Layout 規範

| 元素 | 規格 | 說明 |
|------|------|------|
| **Top Nav** 高度 | 56px | 固定，含 Logo + 用戶名 + 登出 |
| **Sidebar** 寬度 | 240px（預設）/ 64px（收合） | 可 toggle 收合，收合時僅顯示 icon |
| **Content Area** padding | 24px（左右）/ 20px（上下） | 主內容區四邊 padding |
| **Card** 圓角 | 8px | 統計卡、表格容器 |
| **Card** 陰影 | `0 1px 3px rgba(0,0,0,0.08)` | 輕微陰影，區隔背景 |
| **Table** 行高 | 48px | 資料行高（含 8px 上下 padding） |
| **Table** header 高度 | 44px | 含灰色背景 |
| **Button** 高度 | 32px（small）/ 36px（default） | Element Plus 標準 |
| **Modal** 最大寬度 | 520px（表單 Modal）| 一般 CRUD Modal |
| **Form Label** 對齊 | 右對齊（label-width: 100px）| 與 Element Plus Form 一致 |
| **Pagination** 位置 | 表格右下方 | 含「共 N 條」文字 |

---

### 13.3 Element Plus 主題客製化變數

Admin Portal 採 Element Plus，以下 CSS 變數覆蓋預設主題，統一視覺風格：

```css
/* src/admin/styles/element-override.css */
:root {
  /* Primary Color（對應 --admin-accent） */
  --el-color-primary: #2d9ef5;
  --el-color-primary-light-3: #6cbdf7;
  --el-color-primary-light-5: #96d0f9;
  --el-color-primary-light-7: #c0e4fb;
  --el-color-primary-light-8: #d5edfc;
  --el-color-primary-light-9: #eaf6fe;
  --el-color-primary-dark-2: #1a8ae0;

  /* Border Radius */
  --el-border-radius-base: 6px;
  --el-border-radius-small: 4px;
  --el-border-radius-round: 20px;

  /* Table */
  --el-table-header-bg-color: #f6f8fa;
  --el-table-header-text-color: #586069;
  --el-table-row-hover-bg-color: #f0f7ff;
  --el-table-border-color: #e1e4e8;

  /* Menu（Sidebar） */
  --el-menu-bg-color: #111827;
  --el-menu-text-color: #d1d5db;
  --el-menu-active-color: #2d9ef5;
  --el-menu-hover-bg-color: #1f2937;
  --el-menu-item-height: 48px;

  /* Form */
  --el-font-size-base: 14px;
  --el-form-label-font-size: 14px;
}
```

---

### 13.4 Admin 表格 / 表單 設計規範

#### 表格（El-Table）規範

| 場景 | 規格 |
|------|------|
| **多選** | 首欄 checkbox，批量操作限非破壞性行為（如：匯出、批量停用） |
| **排序** | 重要欄位支援點擊排序（如：時間、ID） |
| **空狀態** | El-Empty 元件，含說明文字和 CTA（如「+ 新增第一個用戶」） |
| **Loading** | El-Table 的 `v-loading` directive，遮罩含 spinner |
| **操作欄** | 固定最右欄（`fixed="right"`），含 Edit / Delete / 其他 icon button |
| **刪除確認** | El-Popconfirm，非 window.confirm；確認文字：「確定要刪除「{name}」嗎？此操作不可復原。」 |
| **分頁** | El-Pagination，`layout="total, sizes, prev, pager, next"`；預設每頁 20 筆 |

#### 表單（El-Form）規範

| 場景 | 規格 |
|------|------|
| **驗證觸發** | `trigger: "blur"` + 提交時全欄驗證 |
| **必填標記** | 紅色星號 `*`，置於 label 左側（El 預設行為） |
| **錯誤提示** | 欄位下方紅色文字（El 預設），不使用 Toast 替代 |
| **成功回饋** | El-Message（`type: 'success'`），3 秒自動消失 |
| **密碼欄位** | 含 show/hide toggle icon；不支援 autocomplete |
| **提交 Loading** | Button `loading` 屬性，防止重複提交 |

#### 角色 / 狀態 Tag 配色

| 值 | 顏色 | El-Tag type |
|----|------|-------------|
| `super_admin` | 紫色 `#7c3aed` | `type="danger"` + 覆蓋色 |
| `operator` | 藍色 `#2d9ef5` | `type="primary"` |
| `auditor` | 灰色 `#586069` | `type="info"` |
| `active` | 綠色 `#22c55e` | `type="success"` |
| `inactive` | 灰色 `#9ca3af` | `type="info"` |
| `locked` | 紅色 `#ef4444` | `type="danger"` |

---

## 14. 審核簽核 (Approval Sign-off)

| 角色 | 姓名 | 簽核日期 | 職責範圍 | 意見 |
|------|------|---------|---------|------|
| Visual / Art Designer | {{NAME}} | {{DATE}} | 視覺設計整體完整性 | |
| Art Director | {{NAME}} | {{DATE}} | 藝術方向與品牌一致性 | |
| Product Manager | {{NAME}} | {{DATE}} | 需求符合性與優先級 | |
| Engineering Lead | {{NAME}} | {{DATE}} | 技術可行性評估 | |
| Visual QA Lead | {{NAME}} | {{DATE}} | §11.1 QA 流程驗證：像素比對、設計 Token 一致性、色彩對比度、響應式驗證 | |
| Design System / Token Engineer | {{NAME}} | {{DATE}} | §6 Token 體系完整性：Layer 1–3 Token 定義、Light / Dark 對照、Style Dictionary 輸出格式正確性 | |
| Accessibility Review | {{NAME}} | {{DATE}} | WCAG 2.1 AA 合規（§9）| |
| Brand / Marketing | {{NAME}} | {{DATE}} | 品牌識別一致性（§3、§7）| |
