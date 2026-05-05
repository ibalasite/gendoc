---
doc-type: VDD
target-path: docs/VDD.md
reviewer-roles:
  primary: "資深 Art Director（主審，共 12 項）"
  primary-scope: "視覺識別系統完整性、設計美學一致性、Art Direction 品質、品牌辨識度"
  secondary: "資深 Brand Strategist"
  secondary-scope: "品牌定位一致性、競品差異化、設計原則可落地性"
  tertiary: "資深 Frontend Architect"
  tertiary-scope: "Design Token 可工程實現性、Asset Pipeline 完整性、FRONTEND 交付清晰度"
quality-bar: "任何前端工程師依此 VDD，能直接取得所有 Design Token、資產規格、元件視覺標準，不需詢問設計師即可實作符合品牌的 FRONTEND 頁面。"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥17 個）均存在且有實質內容"
  - "所有視覺元件有具體規格（無模糊描述）"
upstream-alignment:
  - field: 品牌色彩 Token 命名
    source: PDD.md §9.3 Design Tokens
    check: VDD §3 Color Palette 的 Token 名稱（`color-action-primary` 等）是否與 PDD §9.3 Semantic Token 命名完全一致，無命名漂移
  - field: 目標平台
    source: PRD.md §1 Product Overview（平台範圍）
    check: VDD §1.2 Platform Visual Scope 是否涵蓋 PRD 所定義的所有目標平台（Web / Mobile / Game 等），無遺漏
  - field: UI 元件視覺規格
    source: PDD.md §5 Component Library
    check: VDD §6 Component Visual Standards 中每個元件的視覺規格（顏色、圓角、陰影）是否與 PDD §5 的結構定義相符，VDD 只加視覺層不重新定義結構
  - field: 動效 Token 緩動值
    source: PDD.md §6.1 Motion Design Spec
    check: VDD §5.3 Motion Tokens 的 easing function 數值是否與 PDD §6.1 完全一致（`ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)` 等），無矛盾
---

<!-- reviewer-roles.*-scope 欄位供 /reviewdoc 工具顯示角色範圍說明，不影響審查執行邏輯 -->

# VDD Review Items

本檔案定義 `docs/VDD.md` 的審查標準。由 `/reviewdoc VDD` 讀取並遵循。
審查角色：三角聯合審查（資深 Art Director + 資深 Brand Strategist + 資深 Frontend Architect）
審查標準：「假設公司聘請一位 10 年以上頂尖 Art Director，以最嚴格的業界標準進行視覺設計文件驗收審查。」

---

## Review Items

### Layer 1: 視覺識別核心（由 Art Director 主審，共 6 項（含 3 CRITICAL + 3 HIGH））

#### [CRITICAL] 1 — 色彩系統不完整或缺少色彩值
**Check**: §3 Color Palette 是否包含以下三層色彩定義？
- **Primitive**：基礎色階（`gray-100` 到 `gray-900`、品牌主色階 10 個以上層次）
- **Semantic**：語意色（`color-action-primary`、`color-feedback-error`、`color-feedback-warning`、`color-feedback-success`、`color-surface-default`、`color-text-primary`、`color-text-secondary` 等至少 8 個）
- **每個色彩值**：是否同時提供 HEX（`#1A2B3C`）和 HSL（`hsl(215, 43%, 17%)`）格式？
缺少任一層或有任何 `{{HEX}}` 未替換的裸 placeholder 視為 CRITICAL。
**Risk**: 色彩系統不完整，前端工程師各自硬編碼顏色值，品牌色彩碎片化，主題切換（Light/Dark）或品牌更新時需全面重構，且設計系統無法在程式碼層面被自動化驗證。
**Fix**: 補充三層色彩架構：Primitive scale（至少 10 個色階）→ Semantic Token（至少 8 個語意色）→ Component Token（各元件狀態的具體引用）；每個顏色同時提供 HEX + HSL；替換所有裸 placeholder 為真實色彩值。

#### [CRITICAL] 2 — 字體排印系統不完整
**Check**: §4 Typography System 是否完整定義以下內容？
- **Font Family**：主字體、輔助字體（含 Fallback Stack，如 `"Inter", system-ui, sans-serif`）
- **Type Scale**：至少 6 個層次（`text-xs / sm / base / lg / xl / 2xl`，含具體 px 或 rem 值）
- **Font Weight**：每個 Weight 層次（Regular 400 / Medium 500 / Semibold 600 / Bold 700）
- **Line Height**：每個 Type Scale 對應的 line-height 值
- **Letter Spacing**：標題與正文的 tracking 規格
缺少任一類別、或有 `{{FONT}}` 裸 placeholder 視為 CRITICAL。
**Risk**: 字體系統不完整，前端工程師隨意設定字重和行高，產品各頁面的字體節奏不統一，視覺品質降低，且難以在 CI 中自動驗證排版一致性。
**Fix**: 補充完整的 Typography System，確保每個 Type Scale 都有 font-size、line-height、letter-spacing、font-weight 四個維度；提供 CSS Custom Properties 實作範例（`--text-base: clamp(1rem, 0.92rem + 0.4vw, 1.125rem)`）。

#### [CRITICAL] 3 — Art Direction 無視覺參考或 Moodboard
**Check**: §2 Art Direction 是否包含以下任一類型的視覺參考？
- Moodboard（至少 4 張參考圖，含出處）
- 風格方向明確指定（如「Editorial / Neo-brutalism / Swiss International」中的某一類）
- 競品或業界標竿的視覺截圖與分析（說明「借鑒什麼 / 刻意差異化什麼」）
完全缺少視覺參考（只有文字描述）視為 CRITICAL。
**Risk**: 沒有視覺參考，設計師和前端工程師對「風格方向」的理解完全主觀，執行期間反覆來回確認，設計稿偏離期望後需大幅返工，延誤交付週期。
**Fix**: 補充 §2.1 Visual Moodboard，提供至少 4 張具體的參考圖（連結 + 說明「參考這張圖的 XX 特質」）；明確指定風格方向類型，並說明與競品的視覺差異點。

#### [HIGH] 4 — 設計原則少於 3 條或缺乏具體示例
**Check**: §1.3 Design Principles 是否列出至少 3 條設計原則？每條原則是否附有具體的「符合示例」和「違反示例」？原則是否可衡量（避免「美觀」「友善」等無法操作的空泛描述）？
**Risk**: 設計原則缺失或過於抽象，設計決策缺乏依據，設計師在新增元件或頁面時無法自我審查，品牌一致性靠個人感覺而非系統化標準維護。
**Fix**: 補充至少 3 條具體且可衡量的設計原則，每條附「Do / Don't」示例；原則應針對本產品的具體挑戰（如「遊戲：視覺回饋優先於資訊密度」或「SaaS：資料可讀性高於視覺裝飾」）。

#### [HIGH] 5 — 視覺層次規則未定義
**Check**: §1.4 Visual Hierarchy 是否定義以下內容？
- Scale Contrast 規則（標題 vs 正文 vs 說明文字的最小尺寸比例，如「標題至少是正文的 1.5×」）
- Weight Contrast 規則（關鍵資訊使用 Bold，何時使用 Medium）
- Color Emphasis 規則（哪些元素使用 `color-action-primary` 強調，哪些使用 `color-text-secondary` 降調）
- Whitespace Rhythm 規則（Spacing Token 的節奏使用原則）
缺少任一維度視為 HIGH。
**Risk**: 視覺層次規則缺失，前端工程師實作新頁面時無法自主判斷資訊優先序，各頁面的視覺重量分佈不一致，用戶閱讀體驗差，關鍵 CTA 淹沒在頁面噪音中。
**Fix**: 補充 §1.4 Visual Hierarchy Rules，為 Scale、Weight、Color、Spacing 四個維度各定義至少一條操作性規則，附具體 Token 引用（如「主要 CTA 使用 `color-action-primary` + `font-weight-bold`」）。

#### [HIGH] 6 — Dark Mode 視覺規格缺失或 Token 映射不完整
**Check**: §3.3 Dark Mode Color Mapping 是否存在且涵蓋至少 13 個 Semantic Token 的 Light/Dark 雙組值？是否提供 WCAG 對比度驗證值（正文 ≥ 4.5:1，大字 ≥ 3:1）？若 PRD/PDD 明確要求 Dark Mode 但 VDD 完全無此章節，視為 HIGH。
**Risk**: Dark Mode Token 映射缺失，前端工程師各自決定 Dark Mode 顏色，造成 Dark Mode 下的品牌識別度喪失；對比度未驗證可能在 Dark Mode 下違反 WCAG AA，影響可及性合規。
**Fix**: 補充 §3.3 Dark Mode Color Mapping 表格，為每個 Semantic Color Token 定義 Light 值和 Dark 值；使用 WCAG Contrast Checker 驗算並填入對比度數值；不符合 AA 標準的值必須調整。

---

### Layer 2: Art Direction 品質（由 Art Director + Brand Strategist 聯合審查，共 5 項）

#### [HIGH] 7 — 遊戲角色 / 吉祥物視覺規格缺失（遊戲類必審）
**Check**: 若 PRD 類型為遊戲或包含品牌角色：§7 Character Design 是否包含以下內容？
- 角色一覽表（主角 + 至少 3 個 NPC，含正面/側面參考圖或連結）
- 每個角色的色彩歸屬（使用 §3 Color Palette 中的哪些顏色）
- 角色視覺關係說明（主角 vs 對立角色的視覺對比邏輯）
- 禁止事項（禁止的姿勢 / 表情 / 配色組合）
若為遊戲類但完全缺少 §7 章節，視為 HIGH。若非遊戲類產品，此項標注為 N/A 並跳過。
**Risk**: 角色視覺規格缺失，外包美術或不同設計師在不同模組實作角色時風格不統一，造成品牌角色的視覺一致性崩解，尤其在動畫和多媒體素材中難以補救。
**Fix**: 補充 §7 Character Design Spec，為每個角色提供至少一張正面參考圖 + 使用色彩歸屬 + 視覺禁止事項；若角色尚未確定，補充「角色視覺方向簡述」作為中間版本。

#### [HIGH] 8 — SaaS / Web 應用插圖與圖示風格未定義（非遊戲類必審）
**Check**: 若 PRD 類型為 SaaS 或 Web 應用：§7 Illustration & Icon Style 是否定義以下內容？
- 插圖風格方向（Line Art / Flat / Isometric / 3D Render 擇一，附參考圖）
- 圖示風格規格（Stroke 寬度、圓角規則、`24×24` 或 `20×20` 基礎 Grid）
- 插圖使用場景規範（何時使用插圖、何時使用圖示、何時使用照片）
- 圖示庫來源（自製 / 採用 Phosphor / Heroicons 等，附版本）
若非遊戲類但完全缺少此章節視為 HIGH。若為遊戲類，此項標注為 N/A 並跳過。
**Risk**: 插圖和圖示風格未定義，設計師和前端工程師在各頁面混用不同風格的圖示（有些線條粗細 1px、有些 2px；有些 Sharp Corner、有些 Round），造成介面視覺噪音，品牌精緻感下降。
**Fix**: 補充 §7 Illustration & Icon Style 規格，明確指定圖示庫（附版本號）和圖示 Grid 規格；若使用自製圖示，附設計 Grid 原型（Figma 連結）。

#### [MEDIUM] 9 — 情感色調映射缺失
**Check**: §2.3 Emotional Tone Mapping 是否存在？是否為主要品牌情感（如「信任感 / 活力 / 精確性」）映射出對應的視覺決策（顏色選擇邏輯、形狀圓角決策、字體選擇理由）？完全缺失此章節視為 MEDIUM。
**Risk**: 沒有情感色調映射，設計決策依賴個人審美而非品牌策略，不同設計師在不同頁面做出截然不同的視覺選擇，品牌情感一致性難以維持；在向利害關係人說明設計決策時缺乏論據。
**Fix**: 補充 §2.3 Emotional Tone Mapping，列出 2-3 個核心品牌情感，為每個情感說明對應的視覺決策（如「信任感 → 深藍主色 + 大圓角 + 充裕留白 + Geometric Sans Serif 字體」）。

#### [MEDIUM] 10 — 競品視覺差異化未文件化
**Check**: §1.2 Competitive Visual Differentiation 是否列出至少 2 個直接競品的視覺特徵分析（競品使用的主色、字體風格、UI 密度），並說明本品牌選擇哪些視覺元素來區別自身？完全缺少競品視覺分析視為 MEDIUM。
**Risk**: 競品差異化未分析，設計方向可能不自覺地趨同於競品（尤其是 SaaS 類別中大量藍色 + Rounded Sans-Serif 的「預設 SaaS 外觀」），失去品牌獨特識別，在市場中難以被記憶。
**Fix**: 補充 §1.2，列出 2-3 個主要競品的視覺快照分析（截圖 + 3 個視覺特徵摘要）；說明本品牌在哪 2 個以上視覺維度刻意與競品做出差異。

#### [LOW] 11 — 季節性 / 活動視覺變體策略缺失
**Check**: §8 Visual Variation Strategy 是否說明品牌在節慶活動、限時行銷或版本迭代時如何調整視覺元素（哪些可以變、哪些屬於核心識別不可動）？完全缺失此章節視為 LOW。
**Risk**: 無視覺變體策略，行銷團隊在活動期間自行為品牌「加工」視覺（如在標誌上加聖誕帽），侵蝕品牌識別的完整性；每次活動設計師都需臨時決策，無法規模化執行。
**Fix**: 補充 §8.1，定義「可變元素」（配色方案 / 輔助插圖 / 活動 Banner 風格）和「核心不可變元素」（標誌 / 主字體 / 主色系），提供至少一個活動視覺變體規則範例。

---

### Layer 3: 設計到工程橋接（由 Frontend Architect 主審，共 6 項）

#### [CRITICAL] 12 — Design Token 三層架構缺失或不完整
**Check**: §5 Design Tokens 是否實作三層架構？
- **Primitive Tokens**：原始值（`color-blue-500: #3B82F6`、`space-4: 1rem`）
- **Semantic Tokens**：語意引用 Primitive（`color-action-primary: {color-blue-500}`）
- **Component Tokens**：元件級引用 Semantic（`button-background-default: {color-action-primary}`）
是否提供 CSS Custom Properties 完整輸出格式（`:root { --color-action-primary: ... }`）？
缺少任一層或三層之間的引用關係不清晰視為 CRITICAL。
**Risk**: Design Token 架構不完整，前端工程師無法建立可維護的 CSS 系統；當品牌色彩更新時，必須手動修改散落在整個程式碼庫的硬編碼值，而非修改單一 Primitive Token 即可級聯更新。
**Fix**: 補充完整三層 Token 架構；提供 CSS Custom Properties 輸出範例，含所有 Semantic 和 Component Token；說明 Token 更新的級聯規則（修改 Primitive → 自動影響所有引用的 Semantic 和 Component Token）。

#### [HIGH] 13 — 資產匯出規格不完整
**Check**: §9 Asset Pipeline 是否為以下每類資產定義匯出規格？
- **圖示（Icons）**：格式（SVG）、命名規則（`icon-arrow-right`）、尺寸基準（`24×24`）、優化工具（SVGO）
- **插圖（Illustrations）**：格式（SVG / PNG / WebP 擇一，附理由）、解析度（1x/2x/3x 或 AVIF+WebP 組合）
- **品牌 Logo**：格式（SVG 主版 + PNG 備用）、各用途尺寸規格、背景版本（深色版 / 淺色版 / 單色版）
- **紋理 / 背景圖片**：格式（WebP 或 AVIF）、最大檔案大小上限
缺少任一類資產的匯出規格視為 HIGH。
**Risk**: 資產匯出規格缺失，前端工程師和設計師各自決定格式（混用 PNG / SVG / JPEG），導致檔案過大或解析度不足；圖示未統一尺寸造成對齊問題；無命名規則使 Asset 管理混亂。
**Fix**: 補充 §9.1 Asset Export Specifications，為每類資產定義格式、解析度、命名規則、優化工具和最大檔案大小上限；提供 Figma Export 設定截圖或說明。

#### [HIGH] 14 — Figma → Code 交付清單缺失
**Check**: §10 Design Handoff 是否包含以下清單？
- Figma 設計稿連結（File URL + 各 Frame / Component 的直連 Link）
- Auto Layout 使用狀態確認（所有元件是否已使用 Auto Layout，防止 fixed 尺寸問題）
- Component Properties 設定說明（Variants、Interactive Components 配置）
- Redline 規格確認方法（Figma Dev Mode 或 Zeplin 等工具的交付方式）
- 已知偏差說明（設計稿與最終實作的已知差異點）
完全缺少 §10 章節視為 HIGH。
**Risk**: 交付清單缺失，前端工程師在實作過程中不知從哪個 Figma 版本取用規格，可能引用過舊的設計稿導致實作偏差；Auto Layout 未設定造成前端測量尺寸錯誤，反覆對稿浪費時間。
**Fix**: 補充 §10 Design Handoff Checklist，提供 Figma File URL 和所有 P0 元件的 Frame 直連 Link；確認 Auto Layout 狀態並在文件中明確標注。

#### [HIGH] 15 — 響應式視覺行為規則未定義
**Check**: §6.3 Responsive Visual Behavior 是否定義以下內容？
- 各 Breakpoint（320 / 768 / 1024 / 1440px）的視覺密度策略（Mobile: 低密度 / Desktop: 高密度）
- 字體 Scale 的流體縮放規格（`clamp()` 值或各斷點的具體字體大小）
- 間距 Token 在不同 Breakpoint 的縮放規則（Mobile: 使用 `--space-section: 3rem`，Desktop: `--space-section: 8rem`）
- 圖片視覺焦點適配規則（不同螢幕比例下圖片的焦點保留策略）
完全缺少此章節視為 HIGH。
**Risk**: 響應式視覺規則缺失，前端工程師在不同斷點各自決定縮放策略，造成 Mobile 版和 Desktop 版的視覺節奏差異過大；字體在小螢幕過大或過小，破壞可讀性和品牌感。
**Fix**: 補充 §6.3，為所有主要 Type Scale 提供 `clamp()` 值（至少 Hero、Heading、Body 三個層次）；定義各 Breakpoint 的 Spacing Token 對應值；提供圖片焦點適配規則（Object-fit / Object-position 策略）。

#### [HIGH] 16 — 動效 Token 未定義或與 PDD 矛盾
**Check**: §5.3 Motion Tokens 是否定義以下內容？
- Duration Token（`--duration-fast: 150ms`、`--duration-normal: 300ms`、`--duration-slow: 500ms`）
- Easing Token（`--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1)`、`--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1)`）
- `prefers-reduced-motion` 替代值（將 duration 設為 `0ms` 或使用 opacity-only 替代）
是否與 PDD §6.1 Motion Design Spec 的數值完全一致？若不一致，列出矛盾項目。
**Risk**: Motion Token 缺失或與 PDD 矛盾，導致 CSS 和 JS Animation Library 使用不一致的緩動值，動畫節奏感不統一；`prefers-reduced-motion` 缺失直接違反 WCAG 2.3.3。
**Fix**: 補充完整的 Motion Token 定義（含 Duration / Easing / Reduced-motion 替代值）；對照 PDD §6.1 逐一確認數值一致性，修正所有矛盾項目。注意：若 `prefers-reduced-motion` override 完全缺失，本項自動升級為 HIGH，無論其他 Motion Token 完整性。

#### [MEDIUM] 17 — 元件視覺規格缺乏 State 覆蓋
**Check**: §6 Component Visual Standards 中每個核心互動元件（Button、Input、Dropdown、Card）是否定義以下所有 State 的視覺規格？
- default / hover / active / focus / disabled / error
每個 State 的規格是否引用 Design Token（`background: var(--color-action-primary)`）而非寫死顏色值？缺少任何必要 State 或使用硬編碼值視為 MEDIUM。
**Risk**: 元件 State 視覺規格不完整，前端工程師在 hover、focus、disabled 狀態下各自決定視覺表現，跨頁面元件狀態不一致；使用硬編碼值使主題切換（Dark Mode）時需全面修改。
**Fix**: 為每個核心元件補充完整的 State 視覺矩陣，全部使用 Design Token 引用而非硬編碼值；Focus State 必須包含 2px 以上可見外框（WCAG 2.4.7）。

---

### Layer 4: 品牌完整性（由 Brand Strategist 主審，共 5 項）

#### [HIGH] 18 — 品牌定位宣言缺失或過於空泛
**Check**: §1.1 Brand Positioning Statement 是否存在且包含以下要素？
- Target Audience（目標受眾定義）
- Unique Differentiator（與競品的核心差異點）
- Brand Promise（品牌承諾，1 句話可操作的陳述）
- 視覺主張（Brand Positioning 如何轉化為視覺決策）
僅有「我們是一個 XX 品牌」的空泛陳述視為 HIGH finding（等同於缺失）。
**Risk**: 品牌定位宣言缺失，視覺設計方向缺乏業務錨點，設計師和 Stakeholder 對「設計對不對」的判斷各自依賴個人偏好，導致設計評審反覆、設計稿難以收斂。
**Fix**: 補充 §1.1 Brand Positioning Statement，使用「For [target audience] who [need], [Product Name] is [category] that [differentiator], unlike [competitor] who [alternative]」框架，並補充視覺主張（Positioning 如何影響色彩、字體、版式的選擇決策）。

#### [MEDIUM] 19 — Logo 使用規範不完整
**Check**: §2.2 Logo Usage Guidelines 是否定義以下內容？
- Safe Zone（最小留白距離，以 Logo 高度的百分比表示）
- Minimum Size（最小可識別尺寸：Print / Digital 各一個值）
- 允許版本（全彩版 / 深色版 / 淺色版 / 單色版，各附圖例）
- 禁止使用方式（禁止拉伸 / 扭曲 / 修改顏色 / 添加效果，附禁止示例）
缺少任一維度視為 MEDIUM。
**Risk**: Logo 使用規範不完整，外部設計師或行銷人員在社群素材、投影片、廣告中各自修改 Logo（調整顏色、加陰影、壓縮比例），累積性地侵蝕品牌識別完整性。
**Fix**: 補充 §2.2 完整 Logo Usage Guidelines，提供 SVG 主版 + PNG 備用版 + 各顏色版本的 Figma 連結；明確標注 Safe Zone 尺寸和最小使用尺寸。

#### [MEDIUM] 20 — 文件控制資訊不完整
**Check**: VDD 的 Document Control 區塊是否填寫以下所有欄位？
- Version（具體版本號，如 `v1.2.0`，非 `{{VERSION}}`）
- Author（具體姓名或團隊名，非 `{{AUTHOR}}`）
- Date（具體日期，非 `{{DATE}}`）
- Reviewers（Art Director / Brand Strategist / Frontend Architect 三角審查者具體姓名）
- Status（`DRAFT / IN REVIEW / APPROVED` 其中之一）
- Change Log（至少一條版本記錄，含日期 + 改動摘要）
任何欄位含裸 `{{PLACEHOLDER}}` 視為 MEDIUM。
**Risk**: 文件控制資訊不完整，無法追蹤 VDD 的版本歷程，設計師和工程師不清楚目前使用的是哪個版本，容易在設計評審中引用過舊版本的 Token 或規格，造成溝通錯位。
**Fix**: 填入所有 Document Control 欄位的真實值；建立 Change Log 紀錄所有版本的主要改動；Status 必須反映真實審查狀態。若審查提交時 Status 仍為 `DRAFT`，記錄為 MEDIUM finding，要求更新為 `IN REVIEW` 後重新提交審查。

#### [LOW] 21 — 品牌延伸指南缺失
**Check**: §11 Brand Extension Guidelines 是否說明品牌系統在未來應用場景的延伸規則？至少覆蓋以下 2 個場景：
- 新產品線 / 子品牌的視覺命名規則（如「允許使用副標 + 品牌 Logo 組合」）
- 第三方合作或 Co-branding 場景的品牌展示規則
完全缺少此章節視為 LOW。
**Risk**: 品牌延伸指南缺失，產品線擴展或合作行銷時各自決定品牌呈現方式，子品牌或合作視覺可能與主品牌視覺系統不相容，長期積累造成品牌家族的視覺混亂。
**Fix**: 補充 §11 Brand Extension 基本規則，至少定義 2 個未來延伸場景的視覺規則；若目前無子品牌計畫，標注「未來擴展時需更新此章節」並提供空白框架。

#### [LOW] 22 — 裸 Placeholder 掃描（全文）
**Check**: 掃描 VDD 全文中所有 `{{PLACEHOLDER}}` 格式的未替換字串。重點掃描章節：§1.1（Brand Positioning）、§2.1（Moodboard 連結）、§3（色彩 HEX 值）、§4（字體名稱）、§5（Token 值）、§9（Figma Asset 連結）、Document Control（版本 / 作者 / 日期）。列出所有裸 placeholder 的位置（章節 + 欄位名稱）和數量。
**Risk**: 含裸 placeholder 的 VDD 無法作為工程實作依據，前端工程師需人工追問設計師每個空白欄位的真實值，失去文件作為「單一事實來源」的核心價值；VDD 的可信度在工程團隊中下降，未來更新難以推動。
**Fix**: 對每個裸 placeholder，依上游文件（PRD / PDD / BRD）推斷並填入真實值；若確實無法確定，改為 `（待確認：[說明待確認的原因]）` 格式，不得保留機器格式的 `{{PLACEHOLDER}}`。若裸 placeholder 發現於 §3 色彩值或 §5 Token 值，該 placeholder 應同時標注為 CRITICAL（觸發 Item 1 或 Item 12），不得僅記錄為 LOW。

---

## Escalation Protocol

| 嚴重度 | 自動升級條件 | 處理方式 |
|--------|-------------|---------|
| CRITICAL（有任一項） | 色彩系統缺失（Item 1 / §3 Color Palette）/ Typography 不完整（Item 2 / §4 Typography System）/ 無 Art Direction 視覺參考（Item 3 / §2 Art Direction）/ Design Token 三層架構缺失（Item 12 / §6 Design Tokens） | **封鎖 VDD APPROVED**：必須修正後重新進入審查流程，不得進入 EDD 或 FRONTEND 階段 |
| HIGH（≥ 3 項未解決） | 視覺規格不足以支撐前端獨立實作 | **警示**：Art Director 與 Frontend Architect 召開同步會議，確認是否可帶 Issue 進入下一階段並設定補充 deadline |
| MEDIUM（≥ 5 項未解決） | 品牌完整性存在系統性缺漏 | **記錄**：建立 Design Backlog，在 Sprint 1 中安排補充，不封鎖進入工程階段 |
| LOW | 任何數量 | **選擇性修正**：由 Art Director 判斷是否納入本版本或推遲到下一版本 |

> **注意**：N/A 項目（產品類型條件性 Item 7 和 Item 8）不計入 HIGH 問題數量，不影響升級門檻計算。

---

## Completion Criteria

VDD 通過審查並獲得 `APPROVED` 狀態，需同時滿足以下全部條件：

### 必要條件（全部必須滿足）
- [ ] **0 個 CRITICAL 項目**：所有 CRITICAL 項目（Item 1、2、3、12）均已解決，無任何 CRITICAL 項目殘留，不限所在 Layer ✅
- [ ] **Design Token 可工程化**：§5 Design Tokens 三層架構完整，Frontend Architect 確認可直接轉換為 CSS Custom Properties
- [ ] **資產規格完整**：§9 Asset Pipeline 涵蓋所有資產類型的格式、解析度、命名規則，Frontend 工程師無需追問即可執行匯出
- [ ] **無裸 Placeholder**：全文零個 `{{PLACEHOLDER}}` 格式的未替換佔位符
- [ ] **Art Direction 有視覺參考**：§2 Moodboard 或風格參考存在且含具體圖片連結
- [ ] **Document Control 完整**：版本、作者、日期、審查者、Change Log 全部填寫真實值
- [ ] **upstream-alignment 四項交叉核對全部通過**：Token 命名（PDD §9.3）、平台範圍（PRD §1）、元件視覺（PDD §5）、動效緩動（PDD §6.1）均無矛盾，或矛盾已記錄並獲設計負責人簽核豁免 ✅

### 品質條件（由三角審查者確認）
- [ ] **Art Director 簽核**：視覺識別系統完整性、Art Direction 品質符合品牌定位
- [ ] **Brand Strategist 簽核**：品牌定位宣言、競品差異化、設計原則可落地
- [ ] **Frontend Architect 簽核**：Design Token 架構正確、交付清單完整、任何前端工程師依此文件可獨立實作符合品牌的 UI

### 最終驗收標準
> 隨機選取一位未參與 VDD 撰寫的前端工程師，給予此 VDD 文件，他/她應能在不詢問設計師的情況下：
> 1. 從 §5 Design Tokens 直接建立完整的 CSS Custom Properties 系統
> 2. 從 §9 Asset Pipeline 規格匯出所有品牌資產至正確格式和尺寸
> 3. 從 §6 Component Visual Standards 實作至少一個元件的所有視覺 State
> 4. 判斷一個新設計的元件是否符合 §1 Brand Principles 和 §2 Art Direction 精神
>
> 以上四點若均能達到，VDD 通過驗收。

---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/VDD.md`，提取所有 `^## ` heading（含條件章節），共約 17 個
2. 讀取 `docs/VDD.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
