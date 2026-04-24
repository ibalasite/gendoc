---
doc-type: ANIM
target-path: docs/ANIM.md
reviewer-roles:
  primary: "技術動畫師（Senior Technical Animator，10 年遊戲動畫，熟悉 Spine/DragonBones/Unity Animator/GSAP）"
  primary-scope: "§2 骨骼動畫狀態機完整性、§3 幀動畫規格、§4 Tween 設計合理性、§5 粒子特效可行性"
  secondary: "VFX 技術工程師（VFX Technical Engineer，精通 Cocos ParticleSystem / Unity VFX Graph / PixiJS / GLSL Shader）"
  secondary-scope: "§5 粒子技術規格、§6 Shader 代碼正確性、§7 引擎設定合理性、§8 資產規格"
  tertiary: "效能工程師（Performance Engineer，移動端 GPU 優化、Draw Call 合批、LOD 策略）"
  tertiary-scope: "§9 效能預算達成可行性、§9.1 LOD 策略完整性、§10 效能測試覆蓋"
quality-bar: "技術動畫師和 VFX 工程師可直接依此文件完成全部動畫與特效實作，不需再問任何技術決策問題。"
upstream-alignment:
  - field: 引擎版本與動畫 API
    source: FRONTEND.md §2
    check: §7 引擎設定代碼的 API 是否與 FRONTEND.md 引擎版本一致（如 Cocos 2.x cc.tween vs 3.x tween()）
  - field: P0 角色動畫覆蓋
    source: PRD.md User Stories
    check: §2 骨骼動畫是否為 PRD 所有 P0 角色/物件填寫完整狀態機
  - field: Motion Design 規格
    source: VDD.md §4
    check: §4 Tween Easing 函數和時長是否與 VDD Motion Design Token 一致
  - field: 最低目標裝置
    source: BRD.md
    check: §9 效能預算是否在 BRD 最低目標裝置上可達成
  - field: Spine 版本
    source: FRONTEND.md
    check: §2.2 Spine runtime 版本是否與 FRONTEND.md 引入的 Spine 版本一致
---

# ANIM Review Items

本檔案定義 `docs/ANIM.md` 的審查標準。由 `/reviewdoc ANIM` 讀取並遵循。
審查角色：三角聯合審查（技術動畫師 + VFX 技術工程師 + 效能工程師）
審查標準：「假設公司聘請一位 10 年以上技術動畫師，以可直接完成全部動畫特效實作為標準進行驗收。」

---

## Review Items

### Layer 1: 動畫設計目標（由技術動畫師主審）

#### [CRITICAL] 1 — §1 設計目標含裸 Placeholder
**Check**: §1.1 視覺回饋目標、品牌動態識別、效能目標是否有 `{{PLACEHOLDER}}` 未替換？目標 fps 是否填具體數值？
**Risk**: 動畫師不知道效能預算邊界，特效過度導致效能崩潰；或特效不足導致體驗平淡。
**Fix**: 填入具體的動畫風格描述（如「卡通誇張風格，使用 Back.Out Easing，強調回彈感」）和目標 fps。

#### [HIGH] 2 — §1.3 動畫分級未對應 PRD 優先級
**Check**: §1.3 P0/P1/P2 分級是否引用了具體的 PRD 功能（如「P0 = 主角戰鬥動畫（PRD US-001~US-010）」）？
**Risk**: 動畫師不知道哪些動畫是 MVP 必做，可能花時間在 P2 裝飾動效而耽誤 P0 核心動畫。
**Fix**: 補充 P0/P1/P2 具體對應 PRD 功能列表。

---

### Layer 2: 骨骼動畫完整性（由技術動畫師主審）

#### [CRITICAL] 3 — §2 骨骼動畫未覆蓋 P0 角色所有狀態
**Check**: 從 PRD.md 提取所有 P0 角色（玩家角色、主要敵人、關鍵 NPC）。§2 骨骼動畫清單是否為每個 P0 角色填寫了至少 idle + 主要行動 + 結束狀態（die/win/exit）三個動畫？是否有空白或 placeholder 的資產路徑？
**Risk**: P0 角色缺少狀態動畫，遊戲核心循環無法實現。
**Fix**: 補充缺漏的角色動畫記錄；替換裸 placeholder 路徑。

#### [CRITICAL] 4 — §2.1 骨骼動畫狀態機不完整
**Check**: §2.1 是否為每個有多狀態的 P0 角色畫出了完整的狀態轉換圖（包含：每個狀態、所有可能的轉換路徑、不可打斷的特殊轉換）？是否有孤立狀態（只能進入、無法離開）？
**Risk**: 動畫師按狀態機實作後，發現邏輯無法閉環，需要回頭修改設計。
**Fix**: 補充所有缺漏的轉換路徑；標注不可打斷的轉換（如 `die` 不可被任何狀態打斷）。

#### [HIGH] 5 — §2.2 骨骼動畫技術規格未填具體值
**Check**: §2.2 骨骼節點數上限、圖集尺寸、動畫幀率是否都填具體數值？Premultiplied Alpha 是否標注選擇（開啟/關閉）？
**Risk**: 美術超過骨骼節點上限導致效能問題；圖集尺寸超出 GPU 紋理限制。
**Fix**: 填入具體值（Cocos 建議 ≤ 50 骨骼，Unity ≤ 100，圖集 ≤ 2048×2048）。

---

### Layer 3: Tween 動畫合理性（由技術動畫師主審）

#### [HIGH] 6 — §4 Tween 缺少 P0 UI 基礎動畫
**Check**: §4 是否包含以下 P0 UI 動畫（每個 P0 客戶端專案必備）：(1) 按鈕點擊縮放；(2) 主要面板出現/消失；(3) 數值跳動（如金幣/分數）？每條 Tween 是否填寫具體的起始值、結束值、時長（ms）和 Easing 函數？
**Risk**: UI 動畫缺失或配置不明，工程師自行發揮導致體驗不一致。
**Fix**: 補充缺漏的 P0 UI 動畫；所有 Tween 填具體數值。

#### [MEDIUM] 7 — §4 Easing 函數與 VDD 不一致
**Check**（若 VDD.md 存在）：§4 使用的 Easing 函數名稱是否與 VDD.md §4 Motion Design Token 一致？
**Risk**: VDD 定義的品牌動感被 ANIM 覆蓋，動畫感受不統一。
**Fix**: 對齊 VDD Motion Design Token 中的 Easing 定義。

---

### Layer 4: 粒子特效可行性（由 VFX 工程師主審）

#### [CRITICAL] 8 — §5 粒子特效最大粒子數含 Placeholder
**Check**: §5 清單中每條特效的「最大粒子數」是否填具體數值？全局粒子數上限（§5.1）是否填具體值？
**Risk**: 無預算限制，工程師可能設定過高粒子數，在低階裝置上嚴重掉幀。
**Fix**: 填入具體數值（命中/爆炸 ≤ 200，收集 ≤ 50，環境 ≤ 500）；全局上限依目標裝置填寫。

#### [HIGH] 9 — §5 粒子特效未覆蓋 P0 核心事件
**Check**: 從 PRD P0 User Story 提取需要粒子特效的核心事件（攻擊命中、技能釋放、獲得獎勵等）。§5 是否為每個 P0 核心事件填寫對應特效記錄？
**Risk**: P0 核心事件缺少視覺回饋，遊戲體驗大打折扣。
**Fix**: 補充缺漏的 P0 特效記錄。

---

### Layer 5: Shader 特效正確性（由 VFX 工程師主審）

#### [HIGH] 10 — §6 Shader 代碼含裸 Placeholder 或 API 錯誤
**Check**: §6 展開的 Shader 代碼（Cocos Effect / Unity Shader Graph / GLSL）是否有裸 placeholder？代碼是否與引擎版本的渲染管線一致（如 Unity URP 的 Shader Graph 與 Built-in Shader 語法不同）？
**Risk**: Shader 代碼無法直接使用，VFX 工程師需重寫。
**Fix**: 替換 placeholder，確認渲染管線一致性。

#### [MEDIUM] 11 — §6 缺少 Shader 資產路徑
**Check**: §6 每個 Shader 特效是否標注了具體的資產路徑（Cocos Effect 檔案 / Unity Shader Graph 資產 / GLSL 檔案）？
**Risk**: VFX 工程師不知道 Shader 資產放在哪裡，需要自行約定。
**Fix**: 補充每個 Shader 的具體資產路徑（依 §8.2 目錄結構）。

---

### Layer 6: 引擎設定正確性（由 VFX 工程師主審）

#### [CRITICAL] 12 — §7 引擎設定代碼 API 版本不匹配
**Check**: §7 展開的引擎設定代碼是否與 FRONTEND.md 確認的引擎版本一致？
- Cocos Creator 2.x vs 3.x：`cc.tween()` vs `tween()`、`cc.Tween.stopAllByTarget()` vs `tween(node).stop()`
- Unity：Animator 的 Parameter 類型（bool/trigger/int）是否與狀態機設計匹配
- PixiJS v7 vs v8：API 有重大差異
**Risk**: 代碼複製後編譯失敗。
**Fix**: 確認引擎版本，更新代碼至對應版本的 API。

#### [HIGH] 13 — §7.1 Cocos 缺少 Tween 清理代碼
**Check**（Cocos 專案）：§7.1 是否包含 `onDestroy()` 中停止 Tween 的代碼？
**Risk**: 節點銷毀後 Tween 繼續執行訪問空指標，導致運行時崩潰。
**Fix**: 補充 `cc.Tween.stopAllByTarget(this.node)` 在 `onDestroy()` 的代碼範例。

---

### Layer 7: 資產規格（由 VFX 工程師主審）

#### [HIGH] 14 — §8 命名規範有裸 Placeholder 或不一致
**Check**: §8.1 命名範例是否使用了實際的專案模組名稱（非 `{{MODULE}}`）？§2/§3/§4/§5 清單中所有資產路徑是否符合 §8.1 命名規範？
**Risk**: 命名不一致，美術和程式之間交接出錯，資產讀取失敗。
**Fix**: 替換所有 placeholder 為實際模組名稱；統一所有 ID 的命名格式。

---

### Layer 8: 效能預算（由效能工程師主審）

#### [CRITICAL] 15 — §9 效能預算含裸 Placeholder
**Check**: §9 所有欄位（fps、Draw Call、粒子數、骨骼數、記憶體）是否填具體數值？是否有 `{{PLACEHOLDER}}` 未替換？
**Risk**: 無具體效能目標，QA 無法判斷效能是否達標，效能問題上線後才被發現。
**Fix**: 依引擎和 BRD 目標裝置填入具體數值。

#### [CRITICAL] 16 — §9.1 LOD 策略缺失或不完整
**Check**: §9.1 是否定義了三個裝置等級（高/中/低）的判斷條件和具體降級項目？降級項目是否精確到「關閉 §5 PTL-00X 特效」或「粒子數減半」？
**Risk**: 低階裝置效能崩潰；降級邏輯不明確，工程師自行判斷。
**Fix**: 補充三級 LOD 策略，精確到具體的降級操作。

#### [HIGH] 17 — §9 效能預算超出 BRD 最低目標裝置能力
**Check**: §9 的目標 Draw Call 和粒子數上限，在 BRD 最低目標裝置（如入門級 Android）是否可達成？（入門 Android 建議 Draw Call ≤ 50，粒子 ≤ 200）
**Risk**: 效能預算設定不合理，低階裝置必然無法達標。
**Fix**: 調整效能預算，或在 §9.1 LOD 中明確說明低階裝置的特效降級方案。

---

### Layer 9: 測試清單完整性（由效能工程師 + QA 主審）

#### [HIGH] 18 — §10 缺少目標裝置幀率測試
**Check**: §10 是否包含「在 BRD 最低規格裝置上執行完整場景的幀率測試」？最低通過 fps 是否填具體數值（非 placeholder）？
**Risk**: 效能問題在真機上才被發現，修改成本極高。
**Fix**: 補充 ANIM-T-FPS 測試，填入具體 fps 門檻值。

#### [HIGH] 19 — §10 缺少記憶體洩漏測試
**Check**: §10 是否包含「場景切換後無殘留 Tween / 粒子 / Spine 實例」的記憶體洩漏測試？
**Risk**: Tween/粒子未清理，反覆切換場景後記憶體持續增長，最終 OOM 崩潰。
**Fix**: 補充 ANIM-T-LEAK 測試（切換場景 10 次，用 Profiler 確認無記憶體增長）。

#### [MEDIUM] 20 — §10 缺少跨平台 Shader 視覺對比測試
**Check**（若 §6 有 Shader 特效）：§10 是否包含「在 iOS / Android / Web Chrome 分別截圖比對 Shader 效果」的測試？
**Risk**: Shader 在不同 GPU 廠商（ARM Mali / Qualcomm Adreno / Apple GPU / Intel）上渲染結果不同。
**Fix**: 補充 ANIM-T-SHADER 跨平台截圖對比測試。
