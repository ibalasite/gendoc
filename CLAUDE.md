# gendoc 專案 — Claude Code 必讀原則

## Session 開始時必須執行

每次進入此專案的 session，**必須立即執行**：

將以下原則寫入 memory（`~/.claude/projects/-Users-tobala-projects-gendoc/memory/project_gendoc_architecture_principles.md`）：
- Remote-first 分發原則
- Runtime 完全獨立原則
- 目標專案邊界原則
- 修改流程（edit → commit → push 才能生效）
- 禁止直接修改 runtime
- 任何動作前必須先告知使用者

---

## 架構原則

### 1. Single Source of Truth
`~/projects/gendoc/`（git repo）是唯一真相來源。所有修改只在這裡發生，commit 後 push 到 remote。

### 2. 分發路徑：只從 remote，不讀本地
```
~/projects/gendoc/ → push → remote (GitHub)
                                ↓
                         install / setup / update
                                ↓
                          ~/.claude/（runtime）
```
- install、setup、update **只從 remote 拉**
- **不得讀取**本地 `~/projects/gendoc/` 的任何內容來安裝
- 本地 gendoc 專案目錄不能是任何人 runtime 的依賴

### 3. Runtime 完全獨立
`~/.claude/` 安裝完後自給自足：
- `~/.claude/skills/` — skill 指令
- `~/.claude/gendoc/bin/` — 執行腳本
- `~/.claude/gendoc/templates/` — 模板

Runtime 不依賴、不引用 `~/projects/gendoc/` 的任何路徑。

### 4. 目標專案邊界
任何目標專案執行 skill 時：
- 只呼叫 `~/.claude/gendoc/bin/gen_html.py`
- **不讀** `~/projects/gendoc/` 的任何內容
- **不讀**目標專案自己目錄下的任何同名腳本

### 5. 修改流程（必須依序）
```
1. 修改 ~/projects/gendoc/skills/ 或 bin/
2. commit
3. push 到 remote        ← 不做這步，修改永遠不會生效
4. 告知使用者 run update  ← 不要自己跑
```
禁止跳過 push 直接 install，否則 SessionStart hook git pull 後會覆蓋回舊版。

### 6. 禁止直接修改 Runtime
永遠不得直接 Edit/Write `~/.claude/skills/` 或 `~/.claude/gendoc/`。
PreToolUse hook 已封鎖此行為。

### 7. 任何動作前必須問
改完告訴使用者，讓使用者決定下一步。不得自行 push、install、upgrade。

---

## 目標系統架構原則（gendoc 生成的所有文件必須遵守）

gendoc 生成的文件描述的目標系統，**從設計第一天起就只有一種架構**：可橫向擴展、零單點故障、支援 BCP。

### 核心原則

1. **沒有「小中大規模」選項**  
   架構只有一種，差別只在最小啟動 server 數。不得在任何文件或 skill 中出現小規模/中規模/大規模的選項或分支邏輯。

2. **成本 = 消除 SPOF 的最小 server 數**  
   成本估算的起點是「每個元件消除 SPOF 所需的最少副本數」，例如：  
   - API Server：≥ 2 replica  
   - DB：Primary + Standby  
   - Redis：Sentinel 或 Cluster（≥ 3 nodes）  
   流量增加時以水平 scale 解決，不是換規模。

3. **HA/SCALE/SPOF/BCP 是設計前提，不是選項**  
   這四項是架構設計的前提條件，不需要使用者選擇。任何讓使用者「選擇是否需要 HA」的設計都是錯的。

4. **Local 環境必須支援小 HA**  
   本地開發環境（LOCAL_DEPLOY）也必須能跑 ≥ 2 replica API server，因為 HA 的程式寫法與單台不同（shared state、pub/sub、distributed lock、session 存放位置等），local 有 SPOF 就無法測試 HA 程式是否正確。

5. **所有下游文件必須 follow EDD 的 HA 設計**  
   EDD 定義 HA/SCALE/SPOF 設計原則後，ARCH、runbook、LOCAL_DEPLOY、test-plan、API、SCHEMA 等所有文件都必須遵循，且 review checklist 必須包含 HA/SCALE/SPOF 驗證項目。

6. **微服務可拆解性（Microservice Decomposability）是架構設計前提**  
   採用 **Spring Modulith** 架構模式：各子系統（例如 member / wallet / deposit / lobby / game）從 Day 1 即以 Bounded Context 為邊界設計，可合部署（最小 HA 成本）、也可獨立拆出 SCALE（最大擴展彈性）。  
   五條硬約束（缺一不可）：  
   - **無跨模組 DB 直接存取**：每個 BC 擁有且只擁有自己的 DB Schema；跨 BC 資料存取只能透過對方的 Public API 或 Domain Event。  
   - **跨模組只透過 Public Interface 通訊**：禁止直接呼叫其他模組的內部 class / function / repository。  
   - **跨模組通訊事件驅動（Async）**：Domain Event 在合部署時走 in-process bus，拆出後改 Kafka/RabbitMQ，程式碼不需改變。  
   - **無跨模組 Shared Mutable State**：Redis key namespace 隔離；Session/Cache 不跨模組共享可變物件。  
   - **模組依賴圖為 DAG（有向無環圖）**：任何循環依賴（A→B→A）均不可拆分，設計時必須消除。  
   文獻依據：Martin Fowler "MonolithFirst"（2015）、Sam Newman《Monolith to Microservices》（O'Reilly 2019）、Spring Modulith（2022）。

### Claude 執行 gendoc 時的強制行為

- **不得**在任何 skill 中詢問使用者「要不要 HA」或「選擇規模大小」
- **不得**生成單副本部署設計（MIN_POD_COUNT < 2）
- **必須**在所有 review checklist 中包含 HA/SCALE/SPOF 驗證項目
- **必須**確認 LOCAL_DEPLOY 支援 ≥ 2 API replica

---

## gendoc-repair 設計原則

### 目標定義
`gendoc-repair` 的目標是：**把任何不完整的目標專案，補到與 gendoc-auto + gendoc-flow 從頭執行完全一致的狀態**。

不只是「補缺漏步驟」，而是確保：
- 所有應執行的步驟均完成
- 已完成步驟的輸出通過 `.gendoc-rules/` 的品質門檻
- DRYRUN 的量化基線是根據真實的 EDD/PRD/ARCH 計算，而非使用預設值

### DRYRUN 是相位邊界，不是普通步驟

Pipeline 有兩個相位：
```
Phase A（內容層）              Gate          Phase B（技術文件層）
IDEA BRD PRD CONSTANTS ... ARCH → DRYRUN → API SCHEMA FRONTEND ... HTML
                                      ↑
                         讀 EDD/PRD/ARCH 計算量化基線
                         寫出 .gendoc-rules/*.json
```

- Phase B 所有步驟的 gate-check 依賴 `.gendoc-rules/*.json`
- 未跑 DRYRUN 直接補 Phase B = 沒有品質閘門
- repair 必須感知這個邊界，並引導使用者先完成 Phase A → DRYRUN → Phase B

### repair 的修改邊界

**只能修改 `skills/gendoc-repair/SKILL.md`。**

嚴格禁止：
- 修改任何其他 skill 檔案（包括 gendoc-flow、gendoc-gen-dryrun、gendoc-shared）
- 直接修改 `~/.claude/skills/`（PreToolUse hook 已封鎖）
- 在 repair 內重新實作其他 skill 的邏輯

repair 只能**呼叫**其他 skill，不能**複製**其邏輯。

### 七項需求摘要

| # | 需求 | 改動位置 |
|---|------|---------|
| R1 | Phase 邊界識別：diff 分三區 | Step 1 |
| R2 | DRYRUN 三態偵測（none/defaults/ok） | Step 1.6（新增） |
| R3 | DRYRUN 上游就緒度預檢 | Step 1.6 延伸 |
| R4 | DRYRUN 基線過時偵測（git 時間戳比對） | Step 1.6 延伸 |
| R5 | Step 1.5 品質門檻驗證（rules.json） | Step 1.5 升級 |
| R6 | Phase-aware Step 3 提示（三條件分支） | Step 3 重構 |
| R7 | 兩階段補跑模式 | Step 3/4 擴充 |

---

## 這個工具是給所有人用的

gendoc 的目標是讓任何人 clone + setup 後就能用，不依賴作者本機的任何狀態。
任何只在作者本機生效的修改都是錯的。
