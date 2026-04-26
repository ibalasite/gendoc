# gendoc 品質審計報告

**審計日期：** 2026-04-26  
**審計人員：** Expert AI Auditor（以 slot 專案產出為實證基礎）  
**審計範圍：** gendoc 全流水線（D01–D19）產出品質、AI 可實作性、架構缺陷  
**決策欄：** ✅ 全部決策已確認（2026-04-27）  

---

## 執行摘要

gendoc 能夠自動化生成 19 個步驟、約 20 份技術文件，在輸出數量上表現亮眼。然而，以 slot 專案為實證，**目前產出物仍無法達到「AI 可無歧義實作」的標準**。根本原因有六類：

| 類別 | 嚴重度 | 問題數 |
|------|--------|--------|
| A. Pipeline 結構性缺失（步驟未接入） | CRITICAL | 3 |
| B. 版本漂移——輸出路徑/HTML 生成器不一致 | HIGH | 4 |
| C. State 管理失效（lang_stack 未持久化） | HIGH | 2 |
| D. 審查迴圈架構性缺陷（單文件視角盲點） | CRITICAL | 5 |
| E. 模板複雜度 vs. Context Window 超限 | HIGH | 3 |
| F. AI 可實作性標準未被強制閉環驗證 | CRITICAL | 4 |

---

## PART I — 分類詳細問題

---

### A. Pipeline 結構性缺失（步驟未接入）

#### A-01 ⛔ CRITICAL — prototype 步驟從未在 pipeline 中執行

**問題描述：**  
`gendoc-gen-prototype` skill 功能完整，能生成可點擊的 HTML prototype + API explorer，輸出至 `docs/pages/prototype/`。然而 `templates/pipeline.json` 中**完全沒有對應的 D-step**。

**槽位實證：**  
`slot` 專案 state 顯示 D01–D19 全部完成，但 `docs/pages/prototype/` 目錄從未被建立。`docs/pages/` 中只有 `generate_site.py`，無任何 prototype 相關檔案。

**目前行為（錯誤）：**  
`gendoc-gen-html`（D19）的 SKILL.md 第 1319 行有這段邏輯：
```
若 _HAS_FRONTEND=1 或 _HAS_API=1：呼叫 /gendoc-gen-prototype
```
但這只存在於當前版本 SKILL.md 的文字描述中，**slot 專案使用的舊版 `generate_site.py` 根本不包含此邏輯**。即使新版 gen_html.py 有此呼叫，它也是隱藏在 HTML 步驟內的子呼叫，缺乏獨立的步驟 ID、進度追蹤、review loop。

**影響範圍：** 所有使用 gendoc 的專案都沒有 prototype。開發者在實作 UI 時缺乏可點擊的視覺參考，只能依賴 PDD/VDD 文字描述。

**建議解決方案：**  
1. 在 `pipeline.json` 新增 `D20-PROTOTYPE` 步驟（condition: `client_type != api-only`）
2. 為 prototype 步驟設計 review loop
3. 移除 D19 內的隱藏 prototype 子呼叫，改為獨立步驟

**決策：** ✅ 執行 — pipeline.json 新增 D20-PROTOTYPE 步驟（condition: client_type != api-only），移除 D19-HTML 內的隱藏子呼叫，改為獨立步驟追蹤。

---

#### A-02 ⛔ CRITICAL — D17-CONTRACTS 和 D18-MOCK 無 review loop，以 special_completed 狀態靜默通過

**問題描述：**  
state file 中 contracts 和 mock 被標記在 `special_completed` 而非 `completed_steps`，且沒有 `review_progress` 記錄。這意味這兩個步驟**完全沒有品質閘門**。

**槽位實證：**
```json
"special_completed": {
  "D07b-UML": true,
  "D16-ALIGN": true,
  "D16-ALIGN-F": true,
  "D17-CONTRACTS": true,
  "D18-MOCK": true,
  "D19-HTML": true
}
```
無任何 `review_progress.D17-CONTRACTS` 記錄。

**contracts 品質問題（無 review 可能導致的）：**  
- openapi.yaml 的 path 數量是否與 API.md 完全一致？未驗證  
- JSON Schema 的 DTO 是否覆蓋 API.md 所有 RequestDTO/ResponseDTO？未驗證  
- Pact contract 的 consumer/provider pair 是否正確？未驗證

**影響範圍：** contracts/ 和 mock/ 的正確性全靠生成一次過、未經審查。AI 依賴這些合約實作時若有缺漏，只能靠人工比對發現。

**建議解決方案：**  
為 D17-CONTRACTS 加入 review subagent，驗證：(a) openapi path 數量 = API.md endpoint 數量；(b) 每個 DTO schema 有對應 JSON Schema 文件；(c) mock server 能夠啟動（`python main.py --check`）。

**決策：** ✅ 執行 — pipeline.json D17-CONTRACTS note 加入 openapi-spec-validator 驗證及 path 數量對齊檢查；D18-MOCK note 加入 python main.py --check 啟動驗證。

---

#### A-03 🔴 HIGH — D16-ALIGN-F（對齊修復）未更新 ALIGN_REPORT.md，報告與實際狀態脫節

**問題描述：**  
D16-ALIGN 生成了 ALIGN_REPORT.md（54 個問題），D16-ALIGN-F 宣稱已修復。但 ALIGN_REPORT.md **沒有被重新生成**，仍顯示 54 個問題。使用者和下游 AI 無法判斷哪些問題已修復、哪些仍存在。

**槽位實證：**  
`docs/ALIGN_REPORT.md` 仍顯示：
```
║  總計  5  15  22  12  54  ║
```
包含 CRITICAL 問題如「BDD-client features/client/coin_toss/coin_toss_panel.feature 與 PRD §5.5 衝突」。

**影響範圍：** 無法審計修復品質；報告作為「已完成」留在文件中具有誤導性。

**建議解決方案：**  
D16-ALIGN-F 完成後強制重新執行 D16-ALIGN，以更新 ALIGN_REPORT.md 到修復後狀態。

**決策：** ✅ 執行 — pipeline.json 新增 D16b-ALIGN-VERIFY 步驟（緊接 D16-ALIGN-F 之後），重跑 gendoc-align-check 並更新 ALIGN_REPORT.md。若仍有 CRITICAL/HIGH，繼續修復。

---

### B. 版本漂移——輸出路徑/HTML 生成器不一致

#### B-01 ⛔ CRITICAL — 舊版 HTML 生成器（generate_site.py）被保留，新版（gen_html.py）未替換

**問題描述：**  
`gendoc-gen-html` SKILL.md（v3.0.0）生成 `gen_html.py`，包含：
- `PAGE_META` 中有 `idea`（生成 IDEA.html）
- `req_section()` 在 index.html 底部列出 req/ 素材
- `has_bdd` 偵測並生成 bdd.html（彙整所有 .feature 檔）
- 掃描 `docs/diagrams/*.md` 生成各 UML diagram 頁面

**但 slot 專案使用的是舊版 `generate_site.py`，包含：**
- 固定的 `DOC_META` 字典，**沒有 `IDEA` 項目**（IDEA.html 從未生成）
- 無 req/ 素材列表
- 無 BDD feature file 彙整
- 無 UML diagrams 分類導覽

**槽位實證：**  
`docs/pages/` 目錄：
```
generate_site.py  ← 舊版
ALIGN_REPORT.html, ANIM.html, ARCH.html, AUDIO.html, BRD.html, 
EDD.html, FRONTEND.html, IDEA.html, LOCAL_DEPLOY.html, PDD.html,
PRD.html, RTM.html, SCHEMA.html, VDD.html, api.html, runbook.html,
test-plan.html, index.html
```
`IDEA.html` 雖然存在（可能是舊 generate_site.py 後來某次更新所生成），但 sidebar 中**沒有任何 IDEA.html 連結**（確認自 index.html grep 分析）。

**根本原因：** gendoc-gen-html 的 Step 4（`gen_html.py` 版本檢查）只有在版本號不匹配時才重寫腳本。但如果舊腳本叫 `generate_site.py`（不同檔名），版本檢查永遠不會觸發，舊腳本就永遠留著。

**影響範圍：** 所有用舊版 gendoc 生成的專案都有此問題。IDEA.html、req/ 連結、BDD 彙整、UML diagrams sidebar 全部缺失。

**建議解決方案：**  
- D19-HTML 步驟開始時，刪除 `generate_site.py`（若存在），強制使用 `gen_html.py`
- 在 gen_html.py 的 Step 4 中額外檢查舊版腳本是否存在並刪除

**決策：** ✅ 執行 — gendoc-gen-html Step 1-B 加入 B-01 邏輯：偵測 generate_site.py 存在時自動刪除，強制使用 gen_html.py。pipeline.json D19-HTML note 同步更新說明。

---

#### B-02 🔴 HIGH — contracts/ 和 mock/ 輸出路徑在不同版本間不一致

**問題描述：**  
當前 `gendoc-gen-contracts` SKILL.md 明確輸出至：
```
docs/blueprint/contracts/
docs/blueprint/infra/
docs/blueprint/scaffold/
```
當前 `gendoc-gen-mock` SKILL.md 明確輸出至：
```
docs/blueprint/mock/
```

**但 slot 專案的實際輸出在：**
```
contracts/       ← 根目錄
mock/            ← 根目錄
```

**影響：** HTML 文件網站無法從 `docs/` 下找到 contracts/mock 連結；gendoc 新版本重跑時會在 `docs/blueprint/` 建立新的輸出，與根目錄的舊版並存，形成雙份輸出。

**建議解決方案：**  
在 D17/D18 步驟開始時，偵測根目錄是否有 `contracts/` 和 `mock/`，若有則先遷移到 `docs/blueprint/`，再生成新版。

**決策：** ✅ 已執行 — gendoc-gen-contracts / gendoc-gen-mock Step 0 加入 B-02 遷移邏輯：偵測根目錄 contracts/ 或 mock/ 存在時，先 cp -rn 至 docs/blueprint/ 再將原目錄重命名（帶時間戳）後繼續生成。

---

#### B-03 🔴 HIGH — sidebar 導覽列不含 IDEA.html 和 req/ 來源素材連結

**問題描述（適用當前 gen_html.py）：**  
即使在最新版 gen_html.py 中，sidebar 只顯示 `docs/` 下的 md 檔案。`req/` 素材（PDF、額外 md）只在 index.html 底部 `req_section()` 顯示，sidebar 沒有導覽到 req/ 的任何連結。

進入任何非首頁的文件（如 EDD.html），根本找不到指向 req/ 素材的導覽路徑。

**影響：** 使用者在查閱技術文件時，無法從 sidebar 直接跳轉到原始需求素材；AI 代理瀏覽文件網站時也無法自動找到 req/ 連結。

**建議解決方案：**  
在 sidebar 新增「原始素材 (req/)」section，列出 `docs/req/` 下所有文件。

**決策：** ✅ 已執行 — gen_html.py make_sidebar() 加入「原始素材」section（has_req=True 時顯示），連結至新增的 req.html 頁面；main() 偵測 REQ_DIR 有檔案時自動生成 req.html。

---

#### B-04 🟡 MEDIUM — BDD-client HTML 頁面只有 server BDD 彙整，client features 分類缺失

**問題描述：**  
gen_html.py 的 bdd.html 彙整 `features/*.feature`（server BDD）。但 client BDD 在 `features/client/` 子目錄，目前的 `FEATURES_DIR.rglob("*.feature")` 雖然可以掃到，但 sidebar 只顯示一個「BDD Scenarios」入口，所有 feature 檔全部合併成一頁，沒有分類（server / client）。

**影響：** 對於 game 類型（有 client BDD），開發者無法區分哪些 scenario 是 server 側、哪些是 client 側。

**決策：** ✅ 已執行 — gen_html.py 拆分 BDD：server_bdd_features（features/*.feature）→ bdd-server.html；client_bdd_features（features/client/**/*.feature）→ bdd-client.html；sidebar 各自獨立入口 🧪。

---

### C. State 管理失效

#### C-01 ⛔ CRITICAL — lang_stack 未持久化到 state file，下游步驟無法讀取

**問題描述：**  
`EDD.gen.md` Quality Gate 明確要求：
> `lang_stack 明確宣告` — 依 PRD 需求推薦後填入，並**寫入 state**

但 gendoc-auto 的 D06-EDD 步驟完成後，**slot state file 中沒有 `lang_stack` 欄位**（確認自 `.gendoc-state-tobala-main.json`）。

**槽位實證：**  
```json
{
  "version": "2.0",
  "project_dir": "/Users/tobala/projects/slot",
  "start_step": "COMPLETE",
  "execution_mode": "full-auto",
  "review_strategy": "tiered",
  // ... lang_stack 欄位完全不存在
}
```

EDD.md §1.1 中明確寫明「TypeScript/Node.js using Fastify」，但這從未被任何機制寫入 state。

**連鎖影響：**  
`test-plan.gen.md`、`BDD-server.gen.md`、`runbook.gen.md`、`LOCAL_DEPLOY.gen.md` 都聲明「從 state.lang_stack 讀取工具選型」。lang_stack 缺失時，這些文件的生成 agent 只能從 EDD.md 文字推斷，容易出現工具選擇不一致。

**根本原因：**  
gendoc-auto 的 D06-EDD 步驟呼叫 skill 完成後，沒有執行任何 Bash 命令將 EDD §語言/框架 的值寫回 state file。lang_stack 的寫入是 EDD gen agent 的「建議行為」，不是 pipeline 的「強制機制」。

**建議解決方案：**  
D06-EDD 步驟完成後，強制執行：
```python
lang_stack = extract_from_edd_section_3_3(edd_content)
state['lang_stack'] = lang_stack
write_state(state)
```

**決策：** ✅ 確認已實作 — gendoc-flow P-15 在 D06-EDD 完成後提取 §語言/框架 並寫入 state.lang_stack。slot 專案舊版未包含此邏輯，新版已修正。

---

#### C-02 🔴 HIGH — state file 存在兩種不相容的 schema 版本，均標記 version=2.0

**問題描述：**  
`gendoc-shared` SKILL.md 定義的 state schema（v2.0）包含：
```json
{"version": "2.0", "current_step": "...", "brd_path": "...", "auto_mode": "..."}
```

`gendoc-auto` 實際寫入的 state schema（也自稱 v2.0）包含：
```json
{"version": "2.0", "start_step": "...", "completed_steps": [...], "special_completed": {...}}
```

**兩者 version 相同但結構不同**，任何讀取 `state.current_step` 的舊邏輯都會失敗（應讀 `start_step`）。

**影響：** 若用戶同時使用舊版 skill（如 `gendoc-config`）和新版 pipeline，讀取到的欄位名稱不一致，導致靜默錯誤（變數為空但不報錯）。

**決策：** ✅ 已執行 — gendoc-shared §-1 加入 C-02 schema 版本檢查：偵測到 current_step 欄位（舊格式）時立即停止並提示執行 /gendoc-config → 清除全部設定後重新設定。

---

### D. 審查迴圈架構性缺陷

#### D-01 ⛔ CRITICAL — 單文件 review 無法偵測跨文件語意錯誤

**問題描述：**  
每個 review loop 只審查一份文件，review agent 的 prompt 是「對照本文件的 template 審查標準審查本文件」。這種設計在以下情境**系統性失效**：

**最嚴重實例（已發生）：**  
D12b-BDD-client review loop 跑了 7 輪，最終以「tiered round 7: CRITICAL+HIGH+MEDIUM=0」終止。

但 D16-ALIGN 隨後發現以下 CRITICAL 錯誤：
```
[CRITICAL] features/client/coin_toss/coin_toss_panel.feature：
  TC-E2E-COIN-005 寫的是「×3, ×5, ×10, ×25, ×50, ×100」(6 個節點)
  PRD §5.5 定義：×3→×7→×17→×27→×77 (5 個節點，最大 ×77)

[CRITICAL] features/client/thunder_blessing/thunder_blessing_trigger.feature：
  TB-001 描述「Coin Toss overlay appears over the reel grid」
  PRD §5.3：Thunder Blessing 是 SC 觸發 Lightning Mark 升級，與 Coin Toss 完全無關
```

**為什麼 review 沒抓到：**  
BDD-client review template 的審查標準是 Gherkin 格式、scenario 結構、Given/When/Then 完整性、AC 編號對照。**它沒有要求 review agent 對照 PRD §5.5 原文驗證每個數值**。Review agent 看到「6 個倍率節點」覺得「格式正確，有倍率」就通過了，沒有對照 PRD 的「5 個節點」。

**影響範圍：** 任何需要跨文件語意一致性的問題，都可能被單文件 review 漏過。

**建議解決方案：**
1. 為每個 review agent 的 prompt 增加「必讀上游文件」清單（強制讀取後才能審查）
2. 在 D12-BDD review 中強制比對 PRD 所有 AC 的數值（不只是格式）
3. 將 D16-ALIGN 的「D1 — Doc→Doc 對齊檢查」提前到每個步驟的 review 中執行（局部對齊 vs 全局對齊）

**決策：** ✅ 已執行 — gendoc-flow Review subagent prompt 加入：(1) 必讀上游文件步驟（讀取 review.md upstream-alignment 中的上游文件，比對數值）；(2) 品質強調聲明（公司資深專家稽核，每輪需高品質 finding）。

---

#### D-02 ⛔ CRITICAL — review 迴圈可以在 LOW findings 殘留時終止，不保證零問題

**問題描述：**  
`tiered` 策略的終止條件：「前 5 輪 finding=0；第 6 輪起 CRITICAL+HIGH+MEDIUM=0 即停」。

這意味 LOW findings 可以殘留。ANIM 步驟：
```json
"D10c-ANIM": {
  "rounds_done": 14,
  "terminate_reason": "tiered round 14: CRITICAL+HIGH+MEDIUM=0",
  "findings_per_round": [6,5,4,5,5,5,5,6,6,4,4,3,1,1]
}
```
最後兩輪各有 1 個 finding（未確認是 LOW），但在第 14 輪就終止了。

**更嚴重的問題：** D12-BDD-server 出現**退步**：
```json
"findings_per_round": [20,10,11,6,24,4,2]
```
第 5 輪 finding 從 6 跳到 24（增加了 18 個問題）。這說明 fix agent 在修復一個問題時引入了新問題，而 pipeline 繼續跑，最終以「CRITICAL+HIGH+MEDIUM=0」終止——但不保證 fix agent 的每次修改都沒有引入語意錯誤。

**影響範圍：** 所有以 tiered 策略生成的文件，終止時可能仍有 LOW 問題存在，且每次修復都有引入新問題的風險（無 regression 檢測）。

**決策：** ✅ 接受現狀 — tiered 策略允許 LOW findings 殘留為設計選擇，由 token 消耗與品質之間的平衡決定。不同嚴格程度有其合理性。無需改動。

---

#### D-03 🔴 HIGH — 部分 review 迴圈前幾輪 finding=0 後突然爆增（AUDIO 現象）

**問題描述：**  
AUDIO review 的 findings 序列：
```json
"findings_per_round": [0,0,0,0,0,5,6,6,4,3,1,3,1,0]
```
前 5 輪連續 finding=0，但第 6 輪突然出現 5 個問題。

**可能原因：**
1. Review agent 的前 5 輪使用了不同（更寬鬆）的標準或上下文
2. Review template 被更新或 review agent 在第 6 輪讀了更多上游文件
3. 隨機性：AI 每次 review 的嚴格程度不一致

這種行為表明 **review 的結果不可複現、不可預測**，無法保證「通過」代表真正達標。

**影響範圍：** 用戶看到「finding=0」以為文件達標，但下次 review 可能又出現問題。

**決策：** ✅ 已執行 — AUDIO 現象確認為舊版 bug（finding=0 未立即終止）。gendoc-flow termination 邏輯已正確（任一輪 finding=0 立即終止）。gendoc-shared tiered 描述已修正。Review subagent 加入品質強調聲明（每輪需嚴格、高品質 finding）。

---

#### D-04 🔴 HIGH — 超高輪次終止（FRONTEND 20 輪，ANIM 14 輪）耗盡資源但品質仍不確定

**問題描述：**  
```
D10-FRONTEND: 20 輪 tiered review
D10c-ANIM:   14 輪 tiered review
D10b-AUDIO:  14 輪（其中前 5 輪無效）
D07-ARCH:     9 輪
D08-API:      8 輪
```

在 tiered 策略下，部分文件需要 14-20 輪才能達到「CRITICAL+HIGH+MEDIUM=0」，**消耗大量 API token 和時間**，且不保證 LOW findings 為零。

**根本原因：**  
- Fix agent 的修復品質不穩定（有時引入退步）
- Review 標準在不同輪次之間不一致（AUDIO 前 5 輪零問題）
- 沒有 fix quality gate（fix 後必須驗證修復正確性）

**決策：** ✅ 已執行 — gendoc-flow Fix subagent prompt 加入品質強調聲明：每次修復須根本解決問題（不得表面修補）；涉及數值必須與上游文件核對；修復後重讀確認。

---

#### D-05 🟡 MEDIUM — D16-ALIGN-F 修復後未重跑 ALIGN 驗證，54 個問題報告未更新

詳見 A-03。ALIGN 修復完成後 ALIGN_REPORT.md 未更新，無法確認修復效果。

**決策：** ✅ 已執行 — 同 A-03。pipeline.json 新增 D16b-ALIGN-VERIFY，D16-ALIGN-F 完成後強制重跑 gendoc-align-check 並更新 ALIGN_REPORT.md。

---

### E. 模板複雜度 vs. Context Window 超限

#### E-01 🔴 HIGH — EDD.gen.md 要求 AI 在單次生成中完成「讀取 6 份上游文件 + 生成 9 種 UML 圖 + 20+ 個章節」

**問題描述：**  
`EDD.gen.md` 要求生成 agent：
- 讀取：`docs/req/*`, `IDEA.md`, `BRD.md`, `PRD.md`, `PDD.md`, `VDD.md`（5-6 份文件，累計可達 10,000+ 字）
- 生成：§4.5 的 9 種 UML 圖（Use Case, Class×3, Object, Sequence, Communication, State Machine, Activity, Component, Deployment）
- 填寫：§0-§21 共 21+ 個章節，每章有嚴格規格（OWASP 表、STRIDE 表、SLO 表、Chaos Engineering 表等）

**slot EDD.md 最終達到 2,292 行**。在單次生成中，AI 的 context window 被上游文件佔用大量空間，後半段生成時「前面讀過的細節」已超出有效上下文範圍，導致：
- 後半段章節的數值與前半段不一致（已在 ALIGN 中發現）
- 部分 UML 圖的覆蓋完整性下降（API endpoint → Sequence 的 1:1 對應在高 endpoint 數時易遺漏）

**建議解決方案：**  
將 EDD 生成拆分為多個子步驟：
- D06a-EDD-core（§0-§6：系統設計、技術選型、模組設計）
- D06b-EDD-uml（§4.5：9 大 UML 圖，獨立 subagent，每種圖各一個 subagent）
- D06c-EDD-security（§8-§12：安全、可觀測性、效能、測試策略）

**決策：** ✅ 已執行 — EDD.gen.md 加入三 Pass 多 subagent 架構：Pass-A（§1-§8，讀 PRD/BRD/IDEA/PDD/VDD）→ Pass-B（§4.5 UML，讀已生成 EDD.md + PRD AC 清單）→ Pass-C（§9-§21 安全/運維，讀已生成 EDD.md + PRD 安全需求）。所有 pass 輸出至同一份 docs/EDD.md，Review Loop 在三個 pass 完成後執行。

---

#### E-02 🔴 HIGH — SCHEMA.gen.md 要求上游讀取 5 份文件，但 lang_stack=None 時 SQL dialect 不確定

**問題描述：**  
SCHEMA 生成需要讀取 EDD.md（資料模型）、ARCH.md（技術棧）、API.md（DTO）等。由於 `lang_stack` 未寫入 state，SCHEMA 生成 agent 需自行從 EDD.md §3.3 推斷資料庫選型（`Supabase PostgreSQL`），但這種推斷不保證與 EDD/LOCAL_DEPLOY 一致。

**槽位結果：** SCHEMA.md 最終用了 Supabase PostgreSQL（正確），但這是 agent 從文字推斷的，不是從 state 讀取的確定性值。

**決策：** ✅ 確認已實作 — lang_stack 由 D06-EDD 完成後的 gendoc-flow P-15 提取（從 EDD.md §語言/框架 章節）並寫入 state。此機制確保下游步驟從 state 讀取確定性值而非文字推斷。

---

#### E-03 🟡 MEDIUM — BDD feature files 超大（server + client 共 8 個 .feature 檔），單次 review 全部讀取困難

**問題描述：**  
D12-BDD-server review 有 20 個問題且出現退步（round 5: 24 findings），表明生成或修復時 agent 沒有完整讀取所有 feature 文件，只修復部分場景，引入了其他場景的問題。

**決策：** ✅ 已執行 — 同 D-03。gendoc-flow Review subagent 加入品質強調聲明（每輪須嚴格、高品質 finding），適用於所有文件類型包含多文件 BDD review。

---

### F. AI 可實作性標準未被強制閉環驗證

#### F-01 ⛔ CRITICAL — 無任何機制驗證數值在所有文件間的一致性

**問題描述（最核心的 AI 可實作性問題）：**  
一個 AI 工程師閱讀 slot 文件套件實作時，必須確認同一數值在所有文件中一致：

| 數值 | 出現位置 | 是否一致？ |
|------|----------|-----------|
| FG 倍率序列 ×3→×7→×17→×27→×77 | PRD §5.5, EDD §5.6, BDD-server, BDD-client | ❌ BDD-client 寫了 ×100 |
| Rate limit 5 req/s | EDD §8.4 | 未確認是否出現在 runbook, LOCAL_DEPLOY |
| Max bet level 320 | EDD §1.1 | 未確認是否與 API.md request validation 一致 |
| RTP 97.5% | BRD, IDEA | 未確認是否出現在 test-plan 的驗收標準中 |
| DB: Supabase PostgreSQL | EDD §3.3 | 未確認是否與 SCHEMA, LOCAL_DEPLOY, runbook 一致 |

這些一致性驗證依賴 D16-ALIGN（在流水線末尾），**但 ALIGN 只掃描「已知的對齊維度」，不掃描「所有重要業務數值」的跨文件一致性**。

**根本問題：** gendoc 沒有「業務數值清單（Canonical Values Registry）」機制。重要的業務數值（倍率、限制、RTP、閾值）應在 PRD 定義後，被所有下游文件強制引用，而非各自重新寫入。

**建議解決方案：**  
建立 `docs/constants.json`（或 `docs/canonical-values.md`），在 PRD 生成後提取所有關鍵數值，下游文件生成時必須從此文件讀取並引用，review 時強制驗證引用一致性。

**決策：** ✅ 已執行 — pipeline.json 新增 D03.5-CONSTANTS 步驟（PRD 後，PDD 前）；建立 templates/CONSTANTS.md + CONSTANTS.gen.md + CONSTANTS.review.md 三件套；下游文件生成規則加入必讀 docs/CONSTANTS.md 要求。

---

#### F-02 ⛔ CRITICAL — contracts 和 mock 未驗證可執行性，AI 無法確認合約可用

**問題描述：**  
D17-CONTRACTS 生成 `openapi.yaml` 和 `contracts/` 下的 JSON Schema，D18-MOCK 生成 `mock/main.py`。但整個流水線**沒有任何步驟驗證**：
- `openapi.yaml` 是否通過 `openapi-spec-validator` 驗證
- `mock/main.py` 是否可以 `python main.py` 啟動
- openapi.yaml 的 path 數量是否與 API.md endpoint 數量一致

**AI 可實作性影響：** AI 工程師依賴 openapi.yaml 生成 client SDK 或 server stub 時，若 YAML 有語法錯誤或 path 缺失，代碼生成工具直接報錯，完全無法使用。

**建議解決方案：**  
D17/D18 完成後加入 validation 子步驟：
```bash
# openapi validation
docker run --rm -v $(pwd)/contracts:/contracts openapitools/openapi-generator-cli validate \
  -i /contracts/openapi.yaml

# mock startup check  
cd mock && pip install -r requirements.txt -q && python main.py --check
```

**決策：** ✅ 已執行 — pipeline.json D17-CONTRACTS note 加入 openapi-spec-validator 驗證；D18-MOCK note 加入 python main.py --check 啟動驗證要求。

---

#### F-03 🔴 HIGH — BDD feature files 未被驗證可執行（無 step definitions skeleton）

**問題描述：**  
D12-BDD-server 和 D12b-BDD-client 生成了 `.feature` 文件。但：
1. 沒有對應的 step definitions 骨架（`steps/` 目錄）
2. 沒有執行 `behave --dry-run` 或類似命令驗證語法
3. AI 工程師拿到 feature files 後，需要自己推斷每個 step 對應的代碼，缺少直接可跑的 test skeleton

**槽位影響：** BDD-client 的 `coin_toss_panel.feature` 有根本性業務錯誤（CRITICAL），若有 step definitions 並嘗試跑 dry-run，可能提早在 D12b 就被發現。

**建議解決方案：**  
D12/D12b 完成後，用 AI 生成對應的 step definitions skeleton（空方法體，帶正確的 step 匹配），並執行 `behave --dry-run` 確認 step 全部可解析。

**決策：** ✅ 已執行 — 在 BDD-server.gen.md 和 BDD-client.gen.md 加入 F-03 step definitions skeleton 生成要求（不在 flow 中寫特例）。包含依 lang_stack 偵測語言副檔名、skeleton 格式規範、GENERATED_FILE 紀錄。

---

#### F-04 🟡 MEDIUM — LOCAL_DEPLOY.md 未被實際執行驗證，startup 流程可能有遺漏

**問題描述：**  
LOCAL_DEPLOY.md 描述本地環境啟動步驟。由於 lang_stack=None 且沒有實際執行驗證，文件中的命令（如 `npm install`, `docker-compose up`, 環境變數清單）可能不完整。

AI 工程師（或真實開發者）按照 LOCAL_DEPLOY.md 操作時，若有步驟缺失，需要自己排查，降低「開箱即用」品質。

**建議解決方案：**  
在 CI 或 sandbox 環境中，執行 LOCAL_DEPLOY.md 的每個步驟，確認無錯誤退出碼。

**決策：** ✅ 已執行 — 在 LOCAL_DEPLOY.gen.md 加入 F-04 執行驗證要求（docker/sandbox dry-run，不在 flow 中寫特例）。包含環境依賴確認、docker-compose.yml 語法驗證、指令格式驗證流程。

---

## PART II — 系統性根因分析

### 根因 1：審查架構為「文件品質審查」而非「系統正確性審查」

gendoc 的每個 review loop 被設計為「審查本文件是否符合其 template 的格式和完整性要求」。這是一個合理的品質門，但**不等同於「系統設計正確性審查」**。

一份 BDD-client feature 文件可以：
- Gherkin 語法完全正確 ✓
- Given/When/Then 結構完整 ✓
- 覆蓋所有 AC 編號 ✓
- 但業務數值（×100 而非 ×77）根本錯誤 ✗

在 template 的審查標準下，這份文件會通過。要抓到數值錯誤，必須讀 PRD §5.5 並比對。

**結論：** 要達到「AI 可實作標準」，需要在每個 review 中強制引入上游文件對照閱讀。

**決策：** ✅ 已執行 — 採用局部上游章節參照方式：Review subagent 讀取 review.md 的 upstream-alignment 欄位，依此清單讀取對應 docs/*.md 中的相關章節（非全文），重點比對量化數值、API path、DB schema 欄位名稱。

---

### 根因 2：Pipeline 假設「串行正確性」——前面通過就不再驗證

gendoc pipeline 的設計邏輯是：每個步驟通過 review loop 後就進入 `completed_steps`，後續步驟不再回頭驗證。

但現實中：
- D12b-BDD-client 通過 7 輪 review 後，D16-ALIGN 發現其有 CRITICAL 錯誤
- D12b 的錯誤來源是「混淆了 Thunder Blessing 機制和 Coin Toss 機制」
- 這個混淆在 PRD §5.3/§5.5 中有明確區分，但 BDD-client review 沒有要求讀 PRD

**結論：** 已完成的步驟在後續步驟中發現問題時，pipeline 需要能回溯並重跑（目前 D16-ALIGN-F 只修復文件但不重跑相關的 review loop）。

**決策：** ✅ 確認 — 由 review fix loop 機制保障各步驟品質；D16-ALIGN 作為跨文件驗證補充，D16-ALIGN-F → D16b-ALIGN-VERIFY 確認修復效果。更深層的回溯機制列為未來優化項。

---

### 根因 3：語言模型的隨機性導致審查結果不可複現

AUDIO 步驟前 5 輪 finding=0（通過），第 6 輪突然 finding=5。這種不一致性意味著：
- 「review 通過」是當前這個 AI 實例在當前 context 下的判斷，不是確定性的結論
- 下一次跑 review 可能得到不同結果

**結論：** Review loop 不能作為品質的最終判定機制，必須輔以確定性的自動化測試（格式驗證、語法檢查、數值一致性腳本）。

**決策：** ✅ 確認 — AUDIO 現象確認為舊版 bug（finding=0 後 loop 未立即終止）。gendoc-flow 當前程式碼已正確實作 `if finding_total == 0: terminate immediately`。tiered 策略描述已修正避免誤解。D03.5-CONSTANTS 提供確定性數值一致性機制作為補充。

---

## PART III — 優先修復路線圖

根據影響範圍和修復難度，建議以下優先序：

| 優先級 | 問題 ID | 描述 | 預估工作量 |
|--------|---------|------|-----------|
| P0（立即） | C-01 | lang_stack 寫入 state | 小（pipeline D06 後加 3 行 bash） |
| P0（立即） | D-01 | BDD review 強制讀上游 PRD | 中（修改 BDD review prompt） |
| P0（立即） | F-01 | Canonical Values Registry | 中（新增 D03.5 步驟，提取 PRD 數值） |
| P1（本週） | A-01 | prototype 加入 pipeline | 中（新增 D20-PROTOTYPE 步驟） |
| P1（本週） | B-01 | 廢棄 generate_site.py，強制 gen_html.py | 小（D19 加入舊版清理） |
| P1（本週） | A-02 | contracts/mock review loop | 中（加 validation subagent） |
| P1（本週） | F-02 | openapi/mock 可執行性驗證 | 小（加 bash 驗證步驟） |
| P2（本月） | E-01 | EDD 拆分子步驟 | 大（需重設計 EDD pipeline） |
| P2（本月） | D-02 | 修復 regression 偵測 | 中（fix agent 加 diff 驗證） |
| P3（季度） | B-03 | req/ sidebar 連結 | 小（HTML 模板修改） |
| P3（季度） | F-03 | BDD step definitions skeleton | 中（新增 D12.5 步驟） |

---

## PART IV — 對 AI 可實作性的量化差距評估

以 slot 文件套件為基準，評估目前的 AI 可實作性：

| 維度 | 現況得分（/10） | 目標 | 主要缺口 |
|------|--------------|------|---------|
| 數值一致性 | 6 | 10 | BDD-client 有 CRITICAL 錯誤；ALIGN 報告仍有 54 問題 |
| 文件完整性 | 7 | 10 | IDEA.html/prototype 缺失；contracts 無 validation |
| 可執行性 | 5 | 10 | mock 未驗證啟動；BDD 無 step definitions；LOCAL_DEPLOY 未驗證 |
| 跨文件一致性 | 6 | 10 | lang_stack 未持久化；倍率數值出現跨文件矛盾 |
| 導覽可及性 | 6 | 10 | sidebar 缺 IDEA/req/prototype；BDD 無分類 |
| **綜合** | **6.0** | **10** | — |

**結論：** 目前 gendoc 的輸出在「讓 AI 工程師無歧義實作」的標準上約達 60 分。要達到 90 分（可接受標準），必須解決 P0/P1 問題。
我需要合部都能解決，我的目標是完成度最大化
---

*本報告基於 slot 專案（2026-04-26 生成）的實證分析，所有問題均有具體文件路徑或狀態文件作為依據。*
