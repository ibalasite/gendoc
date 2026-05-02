# HA/SPOF 違規修改計劃

> **原則**：所有 gendoc 生成的系統文件，架構設計必須以 HA + SCALE + BCP 為前提，無「小/中/大規模」選擇，成本計算以消除所有 SPOF 的最小 Server 數為準。
>
> **狀態說明**：`決策` 欄位留空，請使用者填入 ✅批准 / ❌拒絕 / ✏️修改後批准

---

## M-01

| 欄位 | 內容 |
|------|------|
| **違規事由** | V1+V6：IDEA.md Q4 讓使用者選小/中/大規模，且將「人數」當規模分類依據，違反「架構只有一種，差別只在最小 server 數」原則 |
| **建議怎麼改** | 將 Q4 改為「PM Expert 研究推估」展示區塊（非使用者填寫），由 gendoc-auto Step 1.7 PM Expert 依競品研究推估 DAU + 同時在線峰值後寫入 state，IDEA.md 直接顯示推估結果，不再詢問使用者 |
| **目標檔案** | `templates/IDEA.md` 行 276–282 |
| **原段落** | `### Q4 — 預期使用規模`<br>`\| **回答** \| {{Q4_SCALE}} \|`<br>`\| **選項** \| 小規模（1–100 人）／ 中規模（100–10,000 人）／ 大規模（10,000 人以上）\|`<br>`\| **影響範疇** \| ARCH 可擴展性設計、SCHEMA 分表策略、EDD 容量規劃 \|` |
| **預計改成** | `### Q4 — 預估流量規模（PM Expert 研究推估）`<br>`\| **日活用戶（DAU）** \| {{Q4_DAU}} \|`<br>`\| **同時在線峰值（PCU）** \| {{Q4_PEAK_CCU}} \|`<br>`\| **推估依據** \| {{Q4_ESTIMATE_BASIS}} \|`<br>`\| **影響範疇** \| EDD 容量規劃數值、ARCH HPA 觸發閾值、DB 連線池大小 \|`<br><br>> 以上數值由 PM Expert 依競品研究與行業基準自動推估，僅供容量規劃使用，不影響架構選型（架構均採 HA 設計，≥ 2 replica）。 |
| **影響範圍** | IDEA.md（行 329 的 Q4_SCALE 引用也需同步改）、IDEA.gen.md（生成規則需說明 Q4 欄位來自 state）、gendoc-auto SKILL.md（M-10 同步） |
| **決策** | IDEA.md, IDEA.gen.md, IDEA.review.md 都要有相對應的相關細節|

---

## M-02

| 欄位 | 內容 |
|------|------|
| **違規事由** | V1+V6：IDEA.md 行 329 `*技術建議基於 Q3（{{Q3_TECH}}）與 Q4（{{Q4_SCALE}}）。*` 殘留 Q4_SCALE 引用 |
| **建議怎麼改** | 改為引用 PM Expert 推估的 DAU + PCU 欄位 |
| **目標檔案** | `templates/IDEA.md` 行 329 |
| **原段落** | `*技術建議基於 Q3（{{Q3_TECH}}）與 Q4（{{Q4_SCALE}}）。*` |
| **預計改成** | `*技術建議基於 Q3（{{Q3_TECH}}）；容量規劃基於 PM Expert 推估 — DAU {{Q4_DAU}}、同時在線峰值 {{Q4_PEAK_CCU}}。*` |
| **影響範圍** | IDEA.md 單行 |
| **決策** | 可以|

---

## M-03

| 欄位 | 內容 |
|------|------|
| **違規事由** | V1+V3：ARCH.md Phase 演進路徑「Phase 1 單體服務 → Phase 2 微服務 → Phase 3 Multi-Region」暗示早期架構允許 SPOF（Phase 1 無 HA） |
| **建議怎麼改** | 移除 Phase 演進作為「選擇哪種架構」的邏輯，改為「任何規模都從 HA 基線出發，Phase 差別只在水平擴展的程度」 |
| **目標檔案** | `templates/ARCH.md` §10.2 行 781–788 |
| **原段落** | `Phase 1（0–{{P1_USERS}} 用戶）：單區單體服務 + 托管 DB`<br>`Phase 2（{{P1_USERS}}–{{P2_USERS}}）：微服務拆分 + Read Replica + PgBouncer`<br>`Phase 3（{{P2_USERS}}–{{P3_USERS}}）：Multi-Region + CQRS + Event Sourcing`<br>`Phase 4（{{P3_USERS}}+）：全球分佈 + 資料分片 + 專用搜尋引擎` |
| **預計改成** | > 架構從啟動第一天即採 HA 設計（API ≥ 2 replica，DB Primary+Standby，Redis Sentinel），零 SPOF。<br>> 以下為水平擴展里程碑，不代表架構切換，只代表擴展程度：<br><br>`Phase 1（< {{P1_USERS}} 並發）：HA 基線 + 單 Region，HPA 自動擴展`<br>`Phase 2（{{P1_USERS}}–{{P2_USERS}} 並發）：Read Replica 擴展讀取吞吐，PgBouncer 連線池`<br>`Phase 3（{{P2_USERS}}+ 並發）：Multi-Region Active-Passive，CQRS 分離讀寫`<br>`Phase 4（{{P3_USERS}}+ 並發）：全球分佈，資料分片，專用搜尋引擎` |
| **影響範圍** | ARCH.md §10.2、ARCH.gen.md（生成規則是否有同樣邏輯） |
| **決策** | ARCH.md, ARCH.gen.md ARCH.review.md 都要有相對應的相關細節|

---

## M-04

| 欄位 | 內容 |
|------|------|
| **違規事由** | V3：ARCH.md §7 服務副本數最小值使用 `{{GW_MIN_REPLICAS}}` 等純佔位符，允許生成者填入 1，未強制 ≥ 2 |
| **建議怎麼改** | 在每個 Min Replicas 欄位加入 ≥ 2（硬性要求），佔位符只用來填入實際規劃數字，但加上 SPOF 消除說明 |
| **目標檔案** | `templates/ARCH.md` §7 行 460–467 |
| **原段落** | `\| API Gateway \| {{GW_MIN_REPLICAS}} \| {{GW_MAX_REPLICAS}} \| minAvailable: {{GW_PDB}} \|`<br>`\| {{SERVICE_A}} \| {{SVC_A_MIN}} \| {{SVC_A_MAX}} \| minAvailable: {{SVC_A_PDB}} \|` |
| **預計改成** | `\| API Gateway \| {{GW_MIN_REPLICAS}}（≥ 2，消除 SPOF）\| {{GW_MAX_REPLICAS}} \| minAvailable: {{GW_PDB}} \|`<br>`\| {{SERVICE_A}} \| {{SVC_A_MIN}}（≥ 2，消除 SPOF）\| {{SVC_A_MAX}} \| minAvailable: {{SVC_A_PDB}} \|`<br><br>並在表格上方加：<br>> **強制要求**：所有服務 Min Replicas ≥ 2，任何低於 2 的設計視為 SPOF，必須修正。 |
| **影響範圍** | ARCH.md §7、ARCH.review.md（審查規則是否有對應強制項） |
| **決策** | ARCH.md, ARCH.gen.md ARCH.review.md 都要有相對應的相關細節|

---

## M-05

| 欄位 | 內容 |
|------|------|
| **違規事由** | V6：ARCH.md §16.3 成本優化策略列出「非生產環境排程停機 40-60% 節省」，允許非生產環境 downtime，與 HA 設計原則衝突 |
| **建議怎麼改** | 加入說明：非生產環境（dev/staging）允許排程縮減副本數以節省成本，但仍不得縮減至 0（即仍需 ≥ 1 可用），且此策略不適用於 production |
| **目標檔案** | `templates/ARCH.md` §16.3 行 1157 |
| **原段落** | `\| RDS \| 非生產環境排程停機（週末、深夜）\| 40-60% \| 低 \|` |
| **預計改成** | `\| RDS \| 非生產環境縮減副本（週末/深夜 scale to 1，非 scale to 0）\| 20-40% \| 低 \|`<br><br>並加注：<br>> ⚠️ 注意：Production 環境不得排程停機或縮副本，HA 要求全天候有效。 |
| **影響範圍** | ARCH.md §16.3 單行 |
| **決策** | 可以|

---

## M-06

| 欄位 | 內容 |
|------|------|
| **違規事由** | V2+V5：EDD.md 環境矩陣 Local 欄 API 副本數 = 1，Local 單副本無法測試 HA 程式邏輯（session、distributed lock、pub/sub） |
| **建議怎麼改** | Local API 副本數改為 ≥ 2，並加說明為何需要多副本 |
| **目標檔案** | `templates/EDD.md` 行 229（環境矩陣） |
| **原段落** | `\| **API 副本數（Replicas）** \| 1 \| {{DEV_API_REPLICAS}} \| {{STAGING_API_REPLICAS}} \| {{PROD_API_REPLICAS}}（HPA min–max）\|` |
| **預計改成** | `\| **API 副本數（Replicas）** \| 2（HA 測試最低要求）\| {{DEV_API_REPLICAS}} \| {{STAGING_API_REPLICAS}} \| {{PROD_API_REPLICAS}}（HPA min–max）\|` |
| **影響範圍** | EDD.md 單行、LOCAL_DEPLOY.md 需同步（M-08） |
| **決策** | 可以，但EDD.md, EDD.gen.md EDD.review.md LOCAL_DEPLOY.md, LOCAL_DEPLOY.gen.md LOCAL_DEPLOY.review.md 都要有相對應的相關細節|

---

## M-07

| 欄位 | 內容 |
|------|------|
| **違規事由** | V2+V5：EDD.md 環境矩陣 Local 欄 Worker 副本數 = 1，單副本 Worker 無法測試冪等處理、競爭條件等 HA 場景 |
| **建議怎麼改** | Local Worker 副本數改為 ≥ 2 |
| **目標檔案** | `templates/EDD.md` 行 230（環境矩陣） |
| **原段落** | `\| **Worker 副本數** \| 1 \| {{DEV_WORKER_REPLICAS}} \| {{STAGING_WORKER_REPLICAS}} \| {{PROD_WORKER_REPLICAS}}（HPA min–max）\|` |
| **預計改成** | `\| **Worker 副本數** \| 2（冪等/競爭條件測試最低要求）\| {{DEV_WORKER_REPLICAS}} \| {{STAGING_WORKER_REPLICAS}} \| {{PROD_WORKER_REPLICAS}}（HPA min–max）\|` |
| **影響範圍** | EDD.md 單行 |
| **決策** | |

---

## M-08

| 欄位 | 內容 |
|------|------|
| **違規事由** | V5：LOCAL_DEPLOY.md 預期 Pod 狀態清單全部為單 pod（api-server-\<hash\> 1/1），與 M-06 EDD 修正後矛盾，且無法測試 HA |
| **建議怎麼改** | 預期 Pod 清單改為顯示 2 個 api-server pod，並加說明「≥ 2 為 HA 測試基線」 |
| **目標檔案** | `templates/LOCAL_DEPLOY.md` 行 275–285 |
| **原段落** | `api-server-<hash>             1/1     Running   0          60s`（單行） |
| **預計改成** | `api-server-<hash1>            1/1     Running   0          60s`<br>`api-server-<hash2>            1/1     Running   0          60s`<br><br>並在段落前加：<br>> Local 環境 API Server 維持 ≥ 2 replica，用以測試 HA 程式邏輯（共享 Session、distributed lock、pub/sub 等）。 |
| **影響範圍** | LOCAL_DEPLOY.md、LOCAL_DEPLOY.gen.md（生成規則需同步） |
| **決策** | 可以 |

---

## M-09

| 欄位 | 內容 |
|------|------|
| **違規事由** | V2：runbook.md `{{MIN_POD_COUNT}}` 和 `{{MIN_WORKER_COUNT}}` 純佔位符，無 ≥ 2 硬性要求，生成者可能填入 1 |
| **建議怎麼改** | 在 placeholder 說明中加入「≥ 2，SPOF 消除要求」 |
| **目標檔案** | `templates/runbook.md` 行 1135、1140、1228、1247 |
| **原段落** | `# Expected: N pods Running and Ready (N = {{MIN_POD_COUNT}})`<br>`kubectl scale ... --replicas={{MIN_POD_COUNT}}` |
| **預計改成** | `# Expected: N pods Running and Ready (N = {{MIN_POD_COUNT}}，最小值 2，消除 SPOF)`<br>`kubectl scale ... --replicas={{MIN_POD_COUNT}}  # MIN_POD_COUNT ≥ 2` |
| **影響範圍** | runbook.md 4 處、runbook.gen.md（生成規則需加強制要求） |
| **決策** | 可以|

---

## M-10

| 欄位 | 內容 |
|------|------|
| **違規事由** | V1：gendoc-auto SKILL.md 仍存在 `_SUGGEST_SCALE` 推斷區塊（小/中/大規模）、Step 1.8 規模確認問題、q4_scale 讀寫（共 10 處） |
| **建議怎麼改** | 刪除整個 `_SUGGEST_SCALE` 推斷區塊；刪除 Step 1.8 中規模確認問題；刪除所有 q4_scale 讀寫；由 PM Expert（Step 1.7）從 Step 3 web 研究結果推估 DAU + 同時在線峰值，寫入 state |
| **目標檔案** | `skills/gendoc-auto/SKILL.md` 行 634–650、667、683–688、729–757、787、889 |
| **原段落** | 行 634–650：`_SUGGEST_SCALE=$(python3 ...)` 計算小/中/大/MVP<br>行 729–757：「問題 2 — 規模確認」AskUserQuestion<br>行 754：`d['q4_scale'] = '${_CONFIRMED_SCALE}'`<br>行 787：`_Q4_SCALE=$(python3 ... d.get('q4_scale','小規模...'))`<br>行 889：`d['q4_scale'] = '${_Q4_SCALE}'` |
| **預計改成** | 刪除所有 q4_scale / _SUGGEST_SCALE 相關邏輯。Step 1.8 改為純自動推斷 client_type + has_admin_backend，無規模相關邏輯。<br><br>**新增**：在 PM Expert（Step 1.7）角色的任務清單中加入容量推估步驟：依 Step 3 web 研究結果（競品 DAU、市場規模、行業基準），推估本專案啟動期預期 DAU 與同時在線峰值（PCU），以及推估依據，寫入 state：<br>`d['q4_dau']            = '<推估 DAU，如 50,000/day>'`<br>`d['q4_peak_ccu']       = '<推估同時在線峰值，如 3,000 人>'`<br>`d['q4_estimate_basis'] = '<推估依據，如 競品 A 月活 100 萬，類似產品 DAU/MAU 比約 5%>'` |
| **影響範圍** | gendoc-auto SKILL.md（集中修改），state schema 同步（M-11） |
| **決策** | client_type + has_admin_backend 是state沒有才在這推估，shared 要能判斷state 讀不到這兩個其中一個值就叫config出來問，統一問的地方，然後寫進state|

---

## M-11

| 欄位 | 內容 |
|------|------|
| **違規事由** | V1：gendoc-shared SKILL.md 行 1019 state schema 仍定義 q4_scale 欄位 |
| **建議怎麼改** | 刪除 q4_scale 行，新增三個 PM Expert 推估欄位 |
| **目標檔案** | `skills/gendoc-shared/SKILL.md` 行 1019 |
| **原段落** | `\| \`q4_scale\` \| string \| Q4 使用規模澄清結果 \|` |
| **預計改成** | 刪除 `q4_scale` 行，替換為：<br>`\| \`q4_dau\` \| string \| DAU 推估值（PM Expert 從研究推估，如 "50,000/day"）\|`<br>`\| \`q4_peak_ccu\` \| string \| 同時在線峰值推估值（如 "3,000 人"）\|`<br>`\| \`q4_estimate_basis\` \| string \| 推估依據來源（競品比較、行業基準等）\|` |
| **影響範圍** | gendoc-shared 單行刪除 + 三行新增，下游 IDEA.md 生成時由 state 填入 |
| **決策** | client_type + has_admin_backend 是state沒有才在這推估，但shared 要能判斷state 讀不到這兩個其中一個值就叫config出來問，統一問的地方，然後寫進state, 再回到呼叫端||

---

## M-12

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4：API.review.md 完全沒有 HA/SPOF 相關審查項目（Timeout/Retry/Circuit Breaker/Rate Limit） |
| **建議怎麼改** | 新增 Layer 審查項：API 設計是否支援 HA 部署（Timeout、Retry、幂等性、Circuit Breaker、Rate Limit） |
| **目標檔案** | `templates/API.review.md`（在最後一個 Layer 後新增） |
| **原段落** | 無（缺漏） |
| **預計改成** | 新增：<br>`#### [HIGH] — API HA 設計缺漏`<br>`**Check**: 每個非冪等 endpoint 是否有 idempotency key 設計？是否定義 Timeout、Retry 策略？是否有 Rate Limit（429）？`<br>`**Risk**: 多副本部署下重複請求導致資料不一致；無限重試導致雪崩。`<br>`**Fix**: 補充 idempotency key、Retry policy、Rate limit header 定義。` |
| **影響範圍** | API.review.md 新增段落 |
| **決策** | API.md, API.gen.md API.review.md 都要有相對應的相關細節|

---

## M-13

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4：SCHEMA.review.md 完全沒有 Replication/讀寫分離/分片策略的審查項目 |
| **建議怎麼改** | 新增 Layer 審查項：DB Schema 設計是否支援 Read Replica、分片、HA failover |
| **目標檔案** | `templates/SCHEMA.review.md`（在最後一個 Layer 後新增） |
| **原段落** | 無（缺漏） |
| **預計改成** | 新增：<br>`#### [HIGH] — Schema HA 擴展性缺漏`<br>`**Check**: 高頻寫入 table 是否有分片鍵設計（或說明不需要的理由）？是否有 Read Replica 路由設計（讀寫分離）？主鍵是否避免 Sequential ID 造成的熱點寫入？`<br>`**Risk**: 單節點寫入瓶頸，SPOF 無法 Failover。`<br>`**Fix**: 補充分片策略說明或確認 PgBouncer + Read Replica 路由設計。` |
| **影響範圍** | SCHEMA.review.md 新增段落 |
| **決策** | SCHEMA.md, SCHEMA.gen.md SCHEMA.review.md 都要有相對應的相關細節|

---

## M-14

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4：test-plan.review.md 沒有 HA 測試覆蓋審查項目（Chaos Engineering、Failover 測試、多副本負載均衡驗證） |
| **建議怎麼改** | 新增 Layer 審查項：測試計畫是否包含 HA 場景測試 |
| **目標檔案** | `templates/test-plan.review.md`（在最後一個 Layer 後新增） |
| **原段落** | 無（缺漏） |
| **預計改成** | 新增：<br>`#### [HIGH] — HA / SPOF 測試場景缺漏`<br>`**Check**: 測試計畫是否包含：(1) 多副本下請求分配驗證；(2) 單副本 kill 後服務不中斷；(3) DB Failover 期間 API 行為；(4) Redis 不可用時的降級行為？`<br>`**Risk**: HA 程式邏輯未被測試，生產故障時才發現設計缺陷。`<br>`**Fix**: 在 §12 Chaos / Failover 章節補充上述四類測試場景。` |
| **影響範圍** | test-plan.review.md 新增段落 |
| **決策** | test-plan.md, test-plan.gen.md test-plan.review.md 都要有相對應的相關細節|

---

## M-15

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4+V5：LOCAL_DEPLOY.review.md 完全沒有 HA 本地驗證項目（多副本、負載均衡、HA 程式邏輯測試） |
| **建議怎麼改** | 新增 Layer 審查項：Local 環境是否支援 ≥ 2 replica HA 測試 |
| **目標檔案** | `templates/LOCAL_DEPLOY.review.md`（在 Layer 2 最後新增） |
| **原段落** | 無（缺漏） |
| **預計改成** | 新增：<br>`#### [CRITICAL] — Local 環境無法測試 HA 程式邏輯`<br>`**Check**: LOCAL_DEPLOY 的 API Server 是否部署 ≥ 2 replica？是否有驗證步驟確認多副本下請求正確分配（session、shared state、WebSocket）？`<br>`**Risk**: 開發者在本地用單副本開發，HA 相關程式邏輯（共享狀態、distributed lock）未被測試，到 staging/production 才爆。`<br>`**Fix**: 確認 api-server replicas ≥ 2，補充多副本驗證步驟（如 kubectl get pods、curl 多次確認 pod hostname 分散）。` |
| **影響範圍** | LOCAL_DEPLOY.review.md 新增段落 |
| **決策** | LOCAL_DEPLOY.gen.md LOCAL_DEPLOY.review.md 都要有相對應的相關細節|

---

---

## M-16

| 欄位 | 內容 |
|------|------|
| **違規事由** | V3+V5：EDD.md 缺乏獨立的 HA/SPOF 架構規格章節。HA 相關設計散落在 §3.5（環境矩陣）、§8（Resilience）、§12.3（Chaos）、§13.5（DR），沒有任何一處明確宣告：哪些元件必須 ≥ 2 replica、Anti-affinity 規則、Pod Disruption Budget、Distributed Lock 設計、BCP 啟動條件。工程師拿到 EDD 時 HA 要求是隱性的，容易被各自解讀。 |
| **建議怎麼改** | 在 §3 Architecture Design 下新增 §3.6 HA/SPOF Architecture Specification，集中宣告所有 HA 非協商要求；同時在 §12.1 Testing Strategy 表新增「HA 驗證」測試類型、§12.2 測試重點場景加入多副本行為場景 |
| **目標檔案** | `templates/EDD.md`（§3 下新增 §3.6、§12.1 表格新增行、§12.2 場景清單新增項目） |
| **原段落** | §3.6 不存在（缺漏）<br>§12.1 表：`\| Unit Test \| ... \|`、`\| Integration Test \| ... \|`、`\| E2E Test \| ... \|`（無 HA 驗證行）<br>§12.2：`- [ ] {{TEST_SCENARIO_4}}（外部服務失敗 → Circuit Breaker 觸發）`（無多副本場景） |
| **預計改成** | **新增 §3.6 HA/SPOF Architecture Specification**，包含：<br>（1）SPOF 消除矩陣表（元件 → Min Replicas → Anti-affinity 規則 → PDB 設定）<br>（2）Session/State 處理聲明（Stateless 原則、禁止 Sticky Session、Redis 共享 Session 設計）<br>（3）Distributed Lock 設計（用於 Background Job 等競爭場景）<br>（4）BCP 啟動條件與手動切換 SOP 摘要（詳細見 runbook）<br>（5）Health Check / Readiness Probe 設計<br><br>**§12.1 新增行**：`\| HA 驗證 \| chaoskube / toxiproxy \| 多副本行為、Failover 恢復 \| Pre-release / 每季 \|`<br><br>**§12.2 新增項目**：`- [ ] Pod kill 測試：Kill 1 of N api-server pods，驗證 30s 內服務恢復、用戶請求無 5xx`<br>`- [ ] DB Failover 測試：模擬 Primary DB 不可用，驗證切換至 Standby 後 API 可寫入` |
| **影響範圍** | EDD.md（§3 新增章節、§12.1 表格、§12.2 清單）、EDD.gen.md（生成規則需同步說明如何填入 §3.6）、EDD.review.md（需新增 §3.6 對應審查項） |
| **決策** | 可以|

---

## M-17

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4：BDD.md 完全缺乏 HA/SPOF 行為測試情境。Tag Taxonomy（§10.1）沒有 `@ha`、`@failover`、`@chaos` 標籤；Error Scenario Catalog（§8）和 Example Feature File（§11）無任何 HA 相關場景。這意味著 QA 驗收流程中 HA 行為從未被確認：Pod 重啟用戶是否感知、DB Failover 期間寫入是否安全、Redis 不可用時降級是否正確 — 全部缺席。 |
| **建議怎麼改** | 在 §10.1 Tag 分類表新增 HA 相關 tag；在文件末尾新增 §16 HA/SPOF BDD Scenario Patterns，提供四類標準 HA 場景範本，供各專案的 BDD 生成時套用 |
| **目標檔案** | `templates/BDD.md`（§10.1 表格新增行、文件末新增 §16） |
| **原段落** | §10.1 Tag 表末行：`\| \`@security\` \| 安全測試 \| 越權、注入、速率限制等場景 \| 安全回歸 \|`（之後無 HA tag）<br>§16 不存在（缺漏） |
| **預計改成** | **§10.1 新增三個 tag**：<br>`\| \`@ha\` \| 高可用驗證 \| 多副本行為、Failover 恢復、Session 跨 Pod 持久 \| Pre-release / 每季 \|`<br>`\| \`@failover\` \| 故障切換 \| DB/Cache/Pod Failover 場景 \| Pre-release \|`<br>`\| \`@chaos\` \| 混沌工程 \| 故障注入驗證（需 staging 環境授權）\| 每季 \|`<br><br>**新增 §16 HA/SPOF BDD Scenario Patterns**，包含四類標準範本：<br>（1）Pod Kill Recovery：`Given 系統有 2 個 api-server pod 運行 / When 其中 1 個 pod 被強制終止 / Then 30 秒內服務恢復 / And 進行中的請求得到正確回應或可重試的錯誤碼`<br>（2）DB Primary Failover：`Given DB Primary 發生故障 / When 切換至 Standby / Then API 寫入在 RTO 時間內恢復 / And 無資料遺失超過 RPO`<br>（3）Redis 不可用降級：`Given Redis 連線失敗 / When 用戶發起需要快取的請求 / Then 系統降級走 DB 直讀 / And 回應時間 < SLO × 2 倍閾值`<br>（4）Distributed Lock 競爭：`Given 2 個 Worker pod 同時處理同一 Job / Then 只有 1 個執行成功 / And 結果冪等（無重複副作用）` |
| **影響範圍** | BDD.md（§10.1 + 新增 §16）、BDD.gen.md（生成規則需說明：專案有 HA 設計時必須生成對應的 @ha 場景） |
| **決策** | 可以|

---

## M-18

| 欄位 | 內容 |
|------|------|
| **違規事由** | **V4（最嚴重）**：test-plan.md §2.3 Future Scope 第 151 行明確將 HA 測試列為「後續版本」：`\| 高可用性驗證（HA Failover） \| v{{HA_VERSION}} \| 需 Chaos Engineering 場景 \|`。這是對 HA-First 原則的正面衝突 — 架構設計從 Day 1 是 HA，但測試計劃明文宣告「第一版上線不測 HA」。 |
| **建議怎麼改** | 將 HA Failover 測試從 §2.3 Future Scope 移除；在 §2.1 In-Scope 非功能性測試（NFR）中明確列入；在 §3 Test Types 中新增 §3.6 HA/Failover Testing 子章節 |
| **目標檔案** | `templates/test-plan.md`（§2.1 NFR 表、§2.3 刪除該行、新增 §3.6） |
| **原段落** | §2.3 行：`\| 高可用性驗證（HA Failover）\| v{{HA_VERSION}} \| 需 Chaos Engineering 場景（如 Chaos Monkey）\|`<br>§2.1 NFR 只有：效能測試、安全測試、UAT（缺 HA 驗證） |
| **預計改成** | **§2.3 刪除該行**（HA 測試不得列為 Future Scope）<br><br>**§2.1 NFR 新增**：`- HA / Failover 測試：所有有狀態元件（DB、Cache、Message Queue）的 Failover 場景、多副本負載驗證`<br><br>**新增 §3.6 HA / Failover Testing**：<br>`**目標**：驗證系統在元件失敗時能在 RTO 內自動恢復，用戶無感知或收到可重試的錯誤碼。`<br>（1）HA 測試場景矩陣表（場景 → 觸發方式 → 預期行為 → 驗收標準 → 工具）<br>（2）標準 HA 測試場景：Pod Kill、DB Failover、Redis Unavailable、網路分區<br>（3）執行前提：Staging 環境 + SRE Approval，Production 需 Game Day 形式<br>（4）驗收標準：在 RTO 內服務恢復 + 無資料遺失超過 RPO + Error rate 回到基線 |
| **影響範圍** | test-plan.md（§2.1、§2.3 修改 + 新增 §3.6）、test-plan.review.md（M-14 已涵蓋 review.md，此項聚焦 template 主體） |
| **決策** | 可以|

---

## M-19

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4：test-plan.md §3.2 Integration Tests 測試範圍表（Service Boundary、DB Layer、Cache Layer）完全缺乏 HA 相關整合測試場景：並發寫入冪等性、Distributed Lock 競爭、Redis 不可用降級路徑、DB 連線池耗盡回復、Message Queue 重試與 Dead Letter Queue 驗證 — 這些在多副本部署下才會出現的行為，無法靠 Unit Test 覆蓋，必須在 Integration Test 層驗證。 |
| **建議怎麼改** | 在 §3.2 Integration Tests 的測試範圍表中新增「HA 行為」層次；在 Test Database 策略後新增「HA Integration Test 標準場景」子節 |
| **目標檔案** | `templates/test-plan.md`（§3.2 Integration Tests 範圍表新增行、新增子節） |
| **原段落** | §3.2 測試範圍表末行：`\| Cache Layer \| Cache hit/miss、TTL、invalidation \| testcontainers (Redis) / in-memory fake \|`（之後無 HA 行） |
| **預計改成** | **§3.2 表格新增行**：`\| HA 行為 \| 並發冪等性、Distributed Lock 競爭、Redis 不可用降級、DB Failover 切換 \| toxiproxy + testcontainers \|`<br><br>**新增「HA Integration Test 標準場景」子節**：<br>`// 場景 1：並發寫入冪等性（多副本下同一請求到達兩個 Pod）`<br>`// 場景 2：Distributed Lock — 兩個 Worker 同時搶鎖，只有一個執行`<br>`// 場景 3：Redis 不可用時 API 降級走 DB，回應時間 < N ms`<br>`// 場景 4：DB 連線池耗盡 → Circuit Breaker 觸發 → 503 → 10s 後自動恢復`<br>每個場景包含：前置條件（toxiproxy 設定）→ 執行動作 → 驗收 assertion |
| **影響範圍** | test-plan.md §3.2（新增行 + 子節）、test-plan.gen.md（生成規則需要求 HA Integration Test 場景必填） |
| **決策** | 可以|

---

## M-20

| 欄位 | 內容 |
|------|------|
| **違規事由** | V4：test-plan.md §3.3 E2E Tests 的 Critical User Flows 清單完全沒有 HA Failover 相關流程。用戶在交易過程中若 Pod 重啟或 DB Failover，現有 E2E 流程看不出系統如何回應 — 是 5xx 中斷、透明重試、還是提示用戶重試 — 這些行為在驗收時從未被確認。 |
| **建議怎麼改** | 在 §3.3 E2E Tests 的 Critical User Flows 表中新增 HA 相關 Flow；在 Browser Matrix 後新增「HA E2E 場景」子節，說明在多副本環境下執行 E2E 的特殊要求 |
| **目標檔案** | `templates/test-plan.md`（§3.3 Critical User Flows 表新增行、新增子節） |
| **原段落** | §3.3 Critical User Flows 表末行：`\| 錯誤輸入 → 驗證錯誤顯示 \| P2 \| No \| < 10 sec \| AC-UX-001 \|`（之後無 HA Flow） |
| **預計改成** | **§3.3 Critical User Flows 表新增行**：<br>`\| Pod Kill 期間進行中的表單提交 → 驗證結果正確或收到可重試錯誤 \| P0 \| Yes \| < 60 sec \| HA-001 \|`<br>`\| DB Failover 期間讀取操作 → 驗證降級至 Read Replica 仍可查詢 \| P0 \| No \| < 120 sec \| HA-002 \|`<br>`\| 多副本下 Session 跨 Pod 持久 → 同一 Session 在不同 Pod 均可讀取 \| P0 \| Yes \| < 30 sec \| HA-003 \|`<br><br>**新增「HA E2E 場景執行要求」子節**：<br>`- 前提：測試環境部署 ≥ 2 api-server pod`<br>`- 使用 kubectl delete pod 或 chaoskube 注入故障`<br>`- E2E runner 需設定 retry policy（可重試的 5xx / 連線錯誤）`<br>`- 驗收：故障注入後 30s 內，後續請求全部正常` |
| **影響範圍** | test-plan.md §3.3（新增行 + 子節）、test-plan.gen.md（生成規則需要求 HA E2E Flow 必填） |
| **決策** |可以 |

---

---

## M-21

| 欄位 | 內容 |
|------|------|
| **違規事由** | 缺漏：EDD.md 沒有「最小完整度架構圖」。目前 EDD 的部署相關內容（§13.1 部署架構、UML §4.5 Deployment Diagram）僅描述單 Region 或未明確 HA-HA 拓撲。任何人生成 EDD 後，無法直接讀到「我們系統長什麼樣子才算合格」，工程師只能自行推斷。 |
| **建議怎麼改** | 在 §3 Architecture Design 下新增 **§3.7 Minimum Complete Architecture（最小完整度架構）**，包含兩張 Mermaid `graph TB` 部署圖（Graph TB 與現有 EDD 圖風格一致，Mermaid 渲染穩定）：圖 A 正式環境 HA-HA、圖 B Local Dev 簡化版。並同步更新 EDD.gen.md（生成規則）和 EDD.review.md（審查項）。 |
| **目標檔案** | `templates/EDD.md`（新增 §3.7）、`templates/EDD.gen.md`（生成規則同步）、`templates/EDD.review.md`（審查項同步） |
| **原段落** | §3.7 不存在（缺漏）。EDD.md §13.1 部署架構有一張單 Region 的 Mermaid 圖，未標注 SPOF 消除、未涵蓋跨 Region。 |
| **預計改成** | 新增 §3.7，內容如下：<br><br>**§3.7 Minimum Complete Architecture（最小完整度架構）**<br><br>> **架構決策**<br>> - **Active-Active 模式：讀 Active-Active，寫 Active-Primary（選項 B）**<br>>   - 兩個 Region 均對外提供讀取服務（Global LB 路由至就近 Region）<br>>   - 寫入永遠路由至 Primary Region（Region A），非同步複製至 Region B<br>>   - Region A Primary DB 故障時，Region B 提升為新 Primary（RTO ≤ {{RTO_INTER_REGION}} 分鐘）<br>>   - 此設計消除衝突解決複雜度，同時提供跨 Region 讀取高可用<br>> - **異地**：Region A、Region B 位於不同地理 Region（非同一 Region 的不同 AZ）<br>> - **最小 Server 數定義**：每個 Region 內消除所有 SPOF 的最少元件數；兩個 Region 共同消除單機房 SPOF<br><br>---<br><br>**圖 A — 正式環境：HA-HA Active-Active（Read AA / Write AP）最小完整度**<br><br>```mermaid<br>graph TB<br>    User["👤 Global Users"]<br>    GLB["🌐 Global Load Balancer<br>(GeoDNS / Anycast)<br>✅ SPOF消除：單一入口點"]<br><br>    subgraph RA["☁️ Region A — Primary Write Region（{{REGION_A_NAME}}）"]<br>        direction TB<br>        LB_A["Regional LB ≥ 2 nodes<br>✅ SPOF消除：LB層"]<br>        subgraph API_A["API Tier"]<br>            A1["api-server-1"]<br>            A2["api-server-2"]<br>        end<br>        subgraph DATA_A["Data Tier"]<br>            DB_AP["DB Primary 🖊<br>（{{DB_SPEC}}）<br>✅ 消除DB-SPOF"]<br>            DB_AS["DB Standby<br>（Failover Ready）"]<br>            REDIS_A["Redis Sentinel<br>3 nodes<br>✅ 消除Cache-SPOF"]<br>            MQ_A["Message Queue<br>≥ 2 brokers"]<br>        end<br>    end<br><br>    subgraph RB["☁️ Region B — Read Region / Standby Write（{{REGION_B_NAME}}）"]<br>        direction TB<br>        LB_B["Regional LB ≥ 2 nodes<br>✅ SPOF消除：LB層"]<br>        subgraph API_B["API Tier"]<br>            B1["api-server-1"]<br>            B2["api-server-2"]<br>        end<br>        subgraph DATA_B["Data Tier"]<br>            DB_BP["DB Read Replica<br>（平時）/ Promoted Primary（故障時）<br>✅ 消除機房-SPOF"]<br>            DB_BS["DB Standby"]<br>            REDIS_B["Redis Sentinel<br>3 nodes"]<br>            MQ_B["Message Queue<br>≥ 2 brokers"]<br>        end<br>    end<br><br>    User --> GLB<br>    GLB -->|"Reads: 就近路由<br>Writes: 固定路由 Region A"| LB_A<br>    GLB -->|"Reads: 就近路由"| LB_B<br>    LB_A --> A1 & A2<br>    LB_B --> B1 & B2<br>    A1 & A2 --> DB_AP & REDIS_A & MQ_A<br>    B1 & B2 --> DB_BP & REDIS_B & MQ_B<br>    DB_AS -.-|"Failover"| DB_AP<br>    DB_BS -.-|"Failover"| DB_BP<br>    DB_AP -->|"Async Streaming Replication<br>RPO = {{RPO_INTER_REGION}}"| DB_BP<br>    DB_AP -.->|"Region Failover: Region B 升級為 Primary<br>RTO ≤ {{RTO_INTER_REGION}} min"| DB_BP<br>```<br><br>**最小 Server 數摘要（正式環境，每 Region）：**<br><br>\| 元件 \| 最小數量 \| 說明 \|<br>\|------|---------|------\|<br>\| API Server \| ≥ 2 pods \| 消除應用層 SPOF，HPA auto-scale \|<br>\| DB Primary \| 1（Region A）\| 唯一寫入節點 \|<br>\| DB Standby \| 1（per region）\| 本 Region 故障切換 \|<br>\| DB Read Replica \| 1（Region B）\| 跨 Region 讀取 + 待機 Primary \|<br>\| Redis Sentinel \| 3 nodes（per region）\| Quorum 需 ≥ 3 \|<br>\| Message Queue \| ≥ 2 brokers \| 消除佇列 SPOF \|<br>\| Regional LB \| ≥ 2 nodes \| 消除 LB 層 SPOF \|<br>\| Global LB \| 1 服務（雲端 managed，本身 HA）\| 雲端 managed 服務內建 HA \|<br><br>---<br><br>**圖 B — Local Dev：單 Region 簡化版（HA 程式邏輯測試用）**<br><br>> ⚠️ **本圖為 Local Dev 簡化版**：單 Region、無跨 Region 複製、Redis standalone。<br>> 程式碼必須設計為支援 Active-Active（Session 不依賴本地記憶體、State 存 Redis、分散式鎖使用 Redis Redlock），使正式環境可無縫切換至圖 A。<br><br>```mermaid<br>graph TB<br>    Dev["👤 Developer / CI Runner"]<br>    Ingress["Local Ingress<br>（Nginx / Traefik）"]<br><br>    subgraph Local["🖥️ Local Cluster — Single Region（Rancher Desktop / kind）"]<br>        direction TB<br>        A1["api-server-1<br>（pod 1）"]<br>        A2["api-server-2<br>（pod 2）<br>✅ ≥ 2 replica：HA 程式邏輯測試"]<br>        DB_P["DB Primary<br>（postgres-0）"]<br>        DB_S["DB Standby<br>（postgres-1）<br>✅ Failover 程式邏輯測試"]<br>        Redis["Redis<br>（standalone，Local 允許）"]<br>        MQ["Message Queue<br>（single broker，Local 允許）"]<br>    end<br><br>    Dev --> Ingress<br>    Ingress --> A1 & A2<br>    A1 & A2 --> DB_P & Redis & MQ<br>    DB_P -.-|"Local streaming replication<br>（模擬 Failover 測試）"| DB_S<br>```<br><br>**Local 與正式環境的對應關係：**<br><br>\| 元件 \| Local（圖 B）\| 正式（圖 A）\| 差異說明 \|<br>\|------|------------|-----------|----------\|<br>\| API Server \| 2 pods \| ≥ 2 pods / region \| 數量相同，消除 HA 程式差異 \|<br>\| DB \| 1 Primary + 1 Standby \| 1 Primary + 1 Standby + 1 Replica \| 無跨 Region Replica \|<br>\| Redis \| Standalone \| Sentinel 3 nodes \| Local 不測試 Sentinel 故障切換 \|<br>\| 跨 Region \| 無 \| Async Streaming \| Local 明確省略 \|<br>\| Global LB \| 無 \| GeoDNS / Anycast \| Local 明確省略 \| |
| **影響範圍** | `EDD.md`（新增 §3.7）、`EDD.gen.md`（新增規則：①必須依 `cloud_provider` state 欄位替換圖中雲端服務名稱；②圖中 server 數量不得低於最小值；③禁止生成 single-pod 或 single-region 正式架構圖）、`EDD.review.md`（新增 CRITICAL 審查項：§3.7 是否存在、圖 A 是否有雙 Region、圖 B 是否保留 ≥ 2 API replica）、`LOCAL_DEPLOY.md`（在部署規格說明中引用「詳見 EDD §3.7 圖 B」）、`LOCAL_DEPLOY.gen.md`（生成規則確認 replica count ≥ 2） |
| **決策** |可以 |

---

---

## M-22

| 欄位 | 內容 |
|------|------|
| **違規事由** | 缺漏 + 風險誤判：(1) BDD.md admin 相關情境幾乎空白，唯一出現（行 361）是「非 admin 用戶呼叫 admin API 得到 403」的負向場景，完全沒有正向 admin 操作的 BDD 範本（RBAC 層級驗證、批次操作、稽核日誌確認、Impersonation）；(2) test-plan.md 行 744 將 Admin Dashboard 定為 P2 + Unit ≥ 70%，嚴重低估風險 — admin 操作影響系統層級（可刪所有用戶、匯出全量資料），RBAC 錯誤等同安全漏洞，理應 P0（Security）。 |
| **建議怎麼改** | BDD.md：新增 `@admin`/`@rbac`/`@audit` Tag、Admin Background 樣板、Admin Feature File 範例（涵蓋 4 類場景）；test-plan.md：修正 Admin 風險分級，在 §3.2 Integration Tests 新增 Admin RBAC Boundary Test 子節 |
| **目標檔案** | `templates/BDD.md`（§10.1 Tag 表 + 新增 §17 Admin BDD Patterns）、`templates/test-plan.md`（§2.1 NFR 表 + §3.1 Unit 覆蓋率修正 + §3.2 Integration 新增子節） |
| **原段落** | BDD.md §10.1 Tag 表末行：`\| \`@security\` \| 安全測試 \| 越權、注入、速率限制等場景 \| 安全回歸 \|`（之後無 admin/rbac tag）<br>BDD.md §8.1 唯一 admin 場景（行 361）：`Given 使用者已以一般帳號 role="user" 登入 / When 使用者呼叫 DELETE /api/v1/admin/users/123 / Then 403`<br>test-plan.md 行 744：`\| Admin Dashboard \| L \| 僅內部使用，影響範圍小 \| P2 \| Unit ≥ 70% \|` |
| **預計改成** | **BDD.md §10.1 新增三個 tag**：<br>`\| \`@admin\` \| 管理介面操作 \| 所有需要 admin 角色才能執行的 Scenario \| 安全回歸 + pre-release \|`<br>`\| \`@rbac\` \| 角色權限邊界 \| 驗證不同角色是否只能執行被授權的操作 \| 安全回歸 \|`<br>`\| \`@audit\` \| 稽核日誌 \| 驗證高風險操作是否被正確記錄到 Audit Log \| 安全回歸 \|`<br><br>**BDD.md 新增 §17 Admin BDD Patterns**，含四類場景範本：<br>（1）Admin Background 樣板：`Given 系統中有以下角色的管理員帳號 / And 我已以 "{{ADMIN_ROLE}}" 角色（如 super_admin / operator / viewer）登入管理後台`<br>（2）RBAC 邊界驗證：`Scenario Outline: <role> 只能存取被授權的功能 / Given 我以 "<role>" 登入 / When 我嘗試執行 "<action>" / Then 回應應為 "<expected>"` + Examples 表（涵蓋所有角色 × 操作組合）<br>（3）批次操作 + 稽核日誌：`When 我選取 N 筆用戶並執行批次停用 / Then 所有用戶狀態變為 inactive / And Audit Log 記錄本次操作（操作者、時間、影響筆數）`<br>（4）Impersonation（若支援）：`Given 我以 super_admin 身份進入用戶 "{{TARGET_USER}}" 的 Impersonation 模式 / Then 我看到的介面與該用戶一致 / And Audit Log 記錄 Impersonation 開始事件`<br><br>**test-plan.md 行 744 修正**：<br>原：`\| Admin Dashboard \| L \| 僅內部使用，影響範圍小 \| P2 \| Unit ≥ 70% \|`<br>改為三行拆分：<br>`\| Admin RBAC / 越權驗證 \| **H**（高） \| 誤授權等同安全漏洞，影響全體用戶資料 \| **P0 + Security** \| Security + Integration ≥ 90% \|`<br>`\| Admin 批次操作（bulk delete / export）\| M \| 操作不可逆，影響大量資料 \| **P1** \| Integration ≥ 80% \|`<br>`\| Admin Dashboard UI 功能 \| L \| 僅內部使用 \| P2 \| Unit ≥ 70% \|`<br><br>**test-plan.md §3.2 新增「Admin RBAC Boundary Test」子節**：<br>`// 測試矩陣：role × action → expected_status`<br>`// super_admin → 任何操作 → 200`<br>`// operator → 讀寫 → 200；刪除 → 403`<br>`// viewer → 只讀 → 200；寫入/刪除 → 403`<br>`// 所有 admin API endpoint 均需驗證水平越權（admin A 不能操作 admin B 的私有資源）` |
| **影響範圍** | `BDD.md`（§10.1 + 新增 §17）、`BDD.gen.md`（生成規則：專案有 `has_admin_backend=true` 時必須生成 §17 對應場景）、`test-plan.md`（行 744 修正 + §3.2 新增子節）、`test-plan.gen.md`（生成規則：has_admin_backend=true 時必須生成 Admin RBAC test matrix） |
| **決策** | 可以|

---

## M-23

| 欄位 | 內容 |
|------|------|
| **違規事由** | 缺漏：gendoc 現有 VDD.md、ANIM.md、AUDIO.md 三個模板解決的是「設計規格」，但沒有任何模板解決「**資產生產訂單**」問題 — 即「要生成哪些具體檔案、用什麼 AI 工具、Prompt 是什麼、尺寸與效能預算多少、目前狀態為何」。這導致資產規劃隱性、Prompt 無版本控制、設計師與工程師對接無依據。 |
| **建議怎麼改** | 新增 `RESOURCE` 三件套（`RESOURCE.md` + `RESOURCE.gen.md` + `RESOURCE.review.md`）。gen.md 的上游為 VDD.md + ANIM.md + AUDIO.md，由 AI 推導出需要哪些資產並產出結構化清單，使用者補填 Prompt 後即可餵給生成式 AI 工具（Midjourney、DALL-E、Suno、Udio 等）執行生產。輸出為 `docs/RESOURCE.md`，HTML 由 `/gendoc-gen-html` 負責，不在此 skill 範圍。 |
| **目標檔案** | 新建 `templates/RESOURCE.md`、`templates/RESOURCE.gen.md`、`templates/RESOURCE.review.md`；更新 `skills/gendoc-auto/SKILL.md` 中的 type alias 對照表（新增 `resource → RESOURCE`）；更新 `skills/gendoc/SKILL.md`（同上） |
| **原段落** | 三個模板均不存在（全新建立）；SKILL.md type alias 表末段（新增一行） |
| **預計改成** | **RESOURCE.md 結構（骨架）**：<br><br>文件包含三個分類表格，分類對應 VDD / ANIM / AUDIO 的來源：<br><br>（1）視覺資產清單（圖片 / 圖示 / 插畫）— 上游 VDD.md<br>（2）動態資產清單（動畫 / 粒子 / Shader）— 上游 ANIM.md<br>（3）音效資產清單（BGM / SFX / VO）— 上游 AUDIO.md<br><br>每個分類表格欄位如下：<br>`\| ID \| 檔名 \| type \| source_tool \| prompt \| dimensions \| file_size_budget \| status \| output_path \| description \|`<br><br>欄位說明：<br>`ID` — 資產唯一識別碼（RES-IMG-001、RES-ANIM-001、RES-SFX-001）<br>`檔名` — 最終交付檔案名稱（如 hero_idle.png）<br>`type` — image / animation / particle / shader / bgm / sfx / vo / video / font<br>`source_tool` — 生成工具（Midjourney v6 / DALL-E 3 / Stable Diffusion XL / Suno v3 / Udio / ElevenLabs / 手繪委外 / 購買授權）<br>`prompt` — 直接可用的生成提示詞（語言依 source_tool 決定）<br>`dimensions` — 圖片用 WxH px；音效用秒數；動畫用幀數×fps<br>`file_size_budget` — 效能預算上限（如 ≤ 200 KB、≤ 2 MB）<br>`status` — needed / prompt_ready / generating / generated / approved / rejected<br>`output_path` — 資產在 repo 中的最終路徑（如 `assets/images/hero/hero_idle.png`）<br>`description` — 用途說明與設計注意事項<br><br>**RESOURCE.gen.md 上游推導規則**：<br>upstream-docs：`docs/VDD.md`（必讀）、`docs/ANIM.md`（若存在）、`docs/AUDIO.md`（若存在）<br>推導邏輯：<br>① 讀 VDD.md §4 角色設計 → 推斷需要哪些角色 image（hero、NPC）<br>② 讀 VDD.md §5 UI 視覺系統 → 推斷 UI asset（icons、backgrounds、buttons）<br>③ 讀 ANIM.md §2 骨骼動畫清單 → 每個 SKEL-xxx 對應一個 animation 資產行<br>④ 讀 ANIM.md §5 粒子特效清單 → 每個 VFX-xxx 對應一個 particle 資產行<br>⑤ 讀 AUDIO.md §2 BGM 清單 → 每個 BGM-xxx 對應一個 bgm 資產行<br>⑥ 讀 AUDIO.md §3 SFX 清單 → 每個 SFX-xxx 對應一個 sfx 資產行<br>AI 自動填入：ID、檔名、type、output_path、dimensions（從 ANIM/AUDIO 規格推算）<br>AI 自動推測：prompt（依 VDD 風格描述生成第一版 prompt，待人工調整）<br>人工補填：source_tool（選擇工具）、file_size_budget（依效能需求）、status（初始為 needed）<br><br>**RESOURCE.review.md 審查項（3 個 CRITICAL，2 個 HIGH）**：<br>[CRITICAL] 所有 VDD §4 角色設計是否都有對應的 RES-IMG 行<br>[CRITICAL] 所有 ANIM.md SKEL/VFX 項目是否都有對應的 RES-ANIM 行<br>[CRITICAL] 所有 file_size_budget 是否符合平台效能預算（手遊 ≤ 2MB per texture、Web ≤ 200KB per image）<br>[HIGH] 所有 prompt 欄位是否非空（needed status 除外）<br>[HIGH] output_path 是否與實際 repo 目錄結構一致 |
| **影響範圍** | 新建 `templates/RESOURCE.md` + `RESOURCE.gen.md` + `RESOURCE.review.md`；`skills/gendoc/SKILL.md` 的 type alias 對照表新增 `resource → RESOURCE`；`templates/pipeline.json` 可選擇是否將 RESOURCE 加入自動 pipeline（建議加在 VDD/ANIM/AUDIO 之後，D15 位置） |
| **決策** | 可以|

---

共 23 項修改（M-01 至 M-23），跨 18 個檔案。請逐項在「決策」欄標注，確認後依指示動手。

*版本：2026-05-02 v4（新增 M-22：BDD Admin 覆蓋 + test-plan 風險修正；M-23：RESOURCE 三件套新建）*

---

## 計劃外發現（M-24 至 M-27）

> 以下四項為 M-01~M-23 全面審查後發現的額外違規，尚未納入原計劃。請審查後標注決策。

---

## M-24

| 欄位 | 內容 |
|------|------|
| **違規事由** | runbook.gen.md 未設定 MIN_POD_COUNT ≥ 2 的強制生成約束。現行生成規則只在「完成後自我檢核清單」末行提到「所有服務最小 replica ≥ 2」，但沒有在逐步驟的生成規則中明確禁止 AI 生成 replica=1 的 runbook 段落，導致 AI 仍可能在 §4 On-Call SOP 或 §6 Capacity Scaling 中給出 `replicas: 1` 的指令範例。 |
| **建議怎麼改** | 在 runbook.gen.md 的 Step 4（On-Call SOP 生成）與 Step 6（Capacity Scaling 生成）中，各新增一條 **Iron Constraint**，明確寫：「任何 kubectl scale / replicas 指令，數值不得低於 2；若上游 EDD §3.7 有定義最小副本數，以 EDD 為準但不得低於 2」。同步在 Quality Gate 表格新增一行：`All replicas ≥ 2｜runbook 中所有 replicas 數值 ≥ 2｜掃描全文，任何 replicas=1 視為不合格` |
| **目標檔案** | `templates/runbook.gen.md`（Step 4 + Step 6 + Quality Gate 表格） |
| **影響範圍** | `templates/runbook.gen.md` |
| **決策** |可以 |

---

## M-25

| 欄位 | 內容 |
|------|------|
| **違規事由** | EDD.md §12.2（混沌工程場景清單）所有場景列均為 `{{SCENARIO_N}}` 裸 placeholder，未提供任何具體的 HA 故障場景範例。生成時 AI 若缺乏參考，容易填入無意義的通用描述，導致混沌工程測試無法涵蓋關鍵 SPOF 切換路徑（Pod crash、DB Failover、Region Failover）。 |
| **建議怎麼改** | 在 EDD.md §12.2 的表格中，保留 placeholder 欄位（允許專案自訂），但在其前方增加「標準最小場景集」示範行（以 HTML 注釋或斜體標注為「範例，請依專案調整」），涵蓋：(1) API Pod kill（chaoskube）、(2) DB Primary Failover（pg_ctl stop / failover trigger）、(3) Redis Sentinel 主節點斷線、(4) 單 Region 全斷（Regional Failover 模擬）。同步在 EDD.gen.md 的 §12 生成步驟中，要求 AI 至少填入上述 4 個場景（可從 EDD §3.6 BCP 設計推導 RTO/RPO 對應的混沌場景）。 |
| **目標檔案** | `templates/EDD.md`（§12.2 表格前新增示範行）、`templates/EDD.gen.md`（§12 生成規則新增「至少填 4 個場景」要求） |
| **影響範圍** | `templates/EDD.md`、`templates/EDD.gen.md` |
| **決策** | 可以|

---

## M-26

| 欄位 | 內容 |
|------|------|
| **違規事由** | LOCAL_DEPLOY.gen.md 的「HA ≥ 2 replicas」規則只出現在完成後的自我檢核清單，沒有嵌入各 Step 的生成指令中。這表示 AI 在執行 Step 2（Kubernetes YAML 生成）或 Step 3（docker-compose 生成）時，沒有被明確告知「API Server 與 Worker 的 replicas 必須 ≥ 2」，仍可能輸出 `replicas: 1`。 |
| **建議怎麼改** | 在 LOCAL_DEPLOY.gen.md Step 2（K8s Deployment 生成）與 Step 3（docker-compose 生成）中，各新增明確約束：「api-server Deployment 的 spec.replicas 不得低於 2；worker Deployment 的 spec.replicas 不得低於 2；若生成 docker-compose，services.api.deploy.replicas 不得低於 2」。同時在 Step 2/3 後新增「副本數驗證指令」範例（`kubectl get pods` 或 `docker compose ps`），讓 LOCAL_DEPLOY 文件本身就包含驗證步驟。 |
| **目標檔案** | `templates/LOCAL_DEPLOY.gen.md`（Step 2 + Step 3 各新增 Iron Constraint） |
| **影響範圍** | `templates/LOCAL_DEPLOY.gen.md` |
| **決策** | 可以|

---

## M-27

| 欄位 | 內容 |
|------|------|
| **違規事由** | ARCH.review.md 審查項 #14「架構演進路徑未定義」的審查描述仍寫「Phase 1 模組化單體 → Phase 2 微服務拆分」，這與 M-03 計劃修改後的 ARCH.md §10.2（HA 基線出發，差別只在水平擴展程度）相矛盾。若 M-03 執行後未同步更新 review.md，審查者會用舊標準（允許 Phase 1 單體）去審查新版 ARCH.md，導致本應通過的 HA 基線文件被誤判為「Phase 1 缺少 HA」。 |
| **建議怎麼改** | 將 ARCH.review.md #14 的 Check 描述改為：「§10.2 Phase 演進路徑是否以 HA 基線為起點（Phase 1 即已 ≥ 2 replica + DB Primary+Standby），而非從單體或單副本出發？若 Phase 1 描述為 Modular Monolith 或 single pod，視為 HIGH 違規。」同時升級此審查項的嚴重度為 HIGH（原為 MEDIUM），並在 Fix 指引中明確引導修改者參考 M-03 的 Phase 演進表改法。 |
| **目標檔案** | `templates/ARCH.review.md`（審查項 #14） |
| **影響範圍** | `templates/ARCH.review.md` |
| **決策** |可以 |

---

共 27 項修改（M-01 至 M-27），跨 20+ 個檔案。

*版本：2026-05-02 v5（新增 M-24~M-27：計劃外發現 — runbook.gen.md 副本約束、EDD §12.2 場景範例、LOCAL_DEPLOY.gen.md Step 層級約束、ARCH.review.md #14 矛盾修正）*

---

## 新需求：Spring Modulith — 微服務可拆解性（M-28 至 M-36）

**背景**：使用者確認採用 Spring Modulith 架構模式。各子系統（member / wallet / deposit / lobby / game 等）從 Day 1 以 Bounded Context 為邊界設計，可合部署（最小 HA 成本），也可獨立拆出 Scale（最大擴展彈性）。五條硬約束（HC-1～HC-5）已寫入 CLAUDE.md、docs/PRD.md §7.6、README.md。以下 M-28～M-36 為 template 層面的對應修改，待決策後執行。

**已完成（不需決策）**：
- CLAUDE.md：已加入第 6 條核心原則（Spring Modulith 五條硬約束）
- docs/PRD.md：已在 §7.6 加入 Spring Modulith 原則區塊與影響清單
- README.md：已加入 Design Principles 段落

---

## M-28

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/EDD.md` §3.4 Bounded Context 表格無 Schema 擁有權欄位，無跨 BC 存取禁止宣告；§4 模組設計無跨模組依賴 DAG 驗證欄位；§4.6 Domain Event 表格無 `event_schema_version`、`topic_name` 欄位。根據 HC-1（跨 BC 禁止直接 DB 存取）和 HC-5（依賴圖為 DAG）的要求，EDD.md 結構上缺少承載這些約束的欄位。 |
| **建議怎麼改** | (1) §3.4 Bounded Context 表格新增「Schema 擁有權」欄：列出每個 BC 擁有的具體 DB 表/Schema 名稱，並加入聲明：「任何其他 BC 不得直接存取本 BC 的 DB 表；跨 BC 資料存取只能透過 Public API 或 Domain Event」。(2) §4 模組設計章節新增「跨模組依賴 DAG 驗證」小節：要求填入所有模組間依賴箭頭並確認圖為 DAG（無循環），提供一個 Mermaid graph 範例框架。(3) §4.6 Domain Event 表格新增欄位：`event_schema_version`（格式 `v{N}`）、`topic_name`（Kafka/Bus topic 名稱）。 |
| **目標檔案** | `templates/EDD.md`（§3.4、§4、§4.6） |
| **影響範圍** | `templates/EDD.md` |
| **決策** | 可以|

---

## M-29

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/EDD.gen.md` §3.4 生成規則有「若有多服務」的條件保護，意即單體部署時 Bounded Context 圖可選填，與 Spring Modulith「Day 1 即需要 BC 邊界」原則相矛盾。Self-Check Checklist 無「每個 BC Schema 擁有權已明確」項目，無「模組依賴圖為 DAG」項目。 |
| **建議怎麼改** | (1) 移除 §3.4 生成規則中的「若有多服務」條件，改為「任何系統均必須生成 Bounded Context Map，並填入 Schema Ownership Table（每個 BC 擁有的具體表名）」。(2) §4.6 Domain Event 生成規則補充：每個事件必須填入 `event_schema_version`（初始值 `v1`）和 `topic_name`。(3) Self-Check Checklist 新增：`[ ] 每個 Bounded Context 的 Schema 擁有權已明確（具體表名，無跨 BC DB 直接存取）` 和 `[ ] 模組間依賴圖已驗證為 DAG（無循環依賴）`。 |
| **目標檔案** | `templates/EDD.gen.md`（§3.4 生成規則、§4.6 生成規則、Self-Check Checklist） |
| **影響範圍** | `templates/EDD.gen.md` |
| **決策** |可以|

---

## M-30

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/EDD.review.md` 審查項 #9「DDD Bounded Context 未定義」嚴重度僅 MEDIUM，且無 Schema 隔離審查項（HC-1 缺失）、無跨模組呼叫只透過公開介面審查項（HC-2 缺失）、無 DAG 驗證審查項（HC-5 缺失）、無跨模組 Shared Mutable State 審查項（HC-4 缺失）。 |
| **建議怎麼改** | 在現有審查項之後新增「Spring Modulith 微服務可拆解性」審查層（Layer N），含以下項目：(1) `[CRITICAL]` SM-01 — Schema 隔離：每個 BC 擁有且只擁有自己的 DB 表，§3.4 Schema Ownership Table 必須填寫具體表名，無兩個 BC 聲明擁有同一張表。Fix：補填 Schema Ownership Table，移除跨 BC FK。(2) `[HIGH]` SM-02 — 跨模組只透過 Public Interface：無直接跨 BC repository/DAO 呼叫路徑。Fix：改為透過目標 BC 的 API 端點或 Domain Event。(3) `[HIGH]` SM-03 — 依賴圖 DAG 驗證：模組間依賴已驗證無循環（附 Mermaid 圖或 DAG 聲明）。Fix：消除循環依賴，重新設計邊界。(4) `[HIGH]` SM-04 — Domain Event Schema 版本化：§4.6 所有 Event 均有 `event_schema_version` 和 `topic_name`。Fix：補齊版本欄位。(5) `[MEDIUM]` SM-05 — 無跨模組 Shared Mutable State：Redis key namespace 隔離，無跨 BC 全域可變物件。Fix：分配獨立 key prefix 給每個 BC。 |
| **目標檔案** | `templates/EDD.review.md`（新增 Spring Modulith 審查層） |
| **影響範圍** | `templates/EDD.review.md` |
| **決策** | 可以|

---

## M-31

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/ARCH.md` §15 Architecture Review Checklist 無 Microservice Decomposability 子節；§4 服務邊界表的「擁有資料」欄為自由文字，無強制填寫具體表名的規則，且無「禁止跨 BC 直接 DB 存取」的明確聲明。`templates/ARCH.gen.md` Self-Check Checklist 27 項無任何 Decomposability 項目；Quality Gate 6 行無 Schema 隔離閘。`templates/ARCH.review.md` 無 Schema 隔離審查項、無 DAG 審查項、無 Shared Mutable State 審查項。 |
| **建議怎麼改** | (A) **ARCH.md**：(1) §4 服務邊界表「擁有資料」欄下方加入明確聲明：「禁止跨服務直接存取他服務的 DB 表，所有跨服務資料存取必須透過 Public API 或 Domain Event（HC-1）」。(2) §15 Checklist 新增子節「微服務可拆解性（MD-01～MD-05）」：MD-01 每個服務 Schema 擁有權已明確（具體表名）、MD-02 跨服務通訊只透過 API 或 Event、MD-03 依賴圖已驗證為 DAG、MD-04 無跨服務 Shared Mutable State、MD-05 每個服務理論上可獨立部署（列出需要變更的接合點）。(B) **ARCH.gen.md**：Self-Check 新增 3 項（§4 Schema 擁有權具體表名、依賴圖 DAG 確認、§15 MD-01～MD-05 已生成）；Quality Gate 新增列：`BC 隔離 | §4 每服務具體擁有表名已填；§15 MD-01~05 均已回答 | 補充缺失項`。(C) **ARCH.review.md**：新增「Layer 5：微服務可拆解性」審查層，含：`[CRITICAL]` Schema 隔離、`[HIGH]` 跨服務只透過 Public Interface、`[HIGH]` 依賴圖 DAG、`[MEDIUM]` 無跨服務 Shared Mutable State（對應 HC-1～HC-4）。 |
| **目標檔案** | `templates/ARCH.md`、`templates/ARCH.gen.md`、`templates/ARCH.review.md` |
| **影響範圍** | ARCH 三件套 |
| **決策** | 可以|

---

## M-32

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/SCHEMA.md` Document Control 無「Owning Bounded Context」欄位；§9 資料完整性約束無跨 BC FK 禁止規則；§16 Schema Review Checklist 無任何 BC 隔離審查項。`templates/SCHEMA.gen.md` 無「Step 0 — Bounded Context 識別」步驟；生成 FK 約束時無跨 BC FK 偵測與阻止規則；Self-Check 和 Quality Gate 無 BC 隔離項。 |
| **建議怎麼改** | (A) **SCHEMA.md**：(1) Document Control 表格新增欄位「Owning Bounded Context / Service」（必填，對應 ARCH §4）。(2) §1 Overview 新增「Schema Boundary Declaration」子節：本 Schema 的唯一擁有服務、外部不得直接 JOIN 的表清單。(3) §9 新增 §9.5「跨 BC FK 禁止」：明確規定 FK 不得引用其他 BC 的表，跨 BC 引用改為應用層管理的 ID-only 策略，加注：`-- Cross-BC reference: enforced at application layer, no DB FK.`。(4) §16 新增子節「Bounded Context 隔離」：本 Schema Owning BC 已標明、所有表屬同一 BC、無跨 BC DB-level FK、跨 BC 引用使用 ID-only。(B) **SCHEMA.gen.md**：生成規則第一步新增「Step 0 — Bounded Context 識別：讀取 EDD §3.4 和 ARCH §4，確認本 SCHEMA 的 Owning BC，填入 Document Control；列出不得被其他 Schema FK 引用的表清單」；Part 3 CREATE TABLE 生成規則補充「每條 FK 驗證引用表屬同一 BC，跨 BC 引用替換為 ID-only + 注釋」；Self-Check 新增 2 項；Quality Gate 新增「BC 隔離」列。 |
| **目標檔案** | `templates/SCHEMA.md`、`templates/SCHEMA.gen.md` |
| **影響範圍** | SCHEMA 兩件（review.md 若有也一併檢查） |
| **決策** |可以 |

---

## M-33

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/API.md` Document Control 無「Owning Bounded Context」欄位；§1.1 設計原則無「Service Encapsulation」原則（禁止 API Response 直接暴露 DB 欄位名）；§14 API Review Checklist 無任何 BC 封裝審查項。若各子系統（member / wallet 等）的 API 文件不宣告歸屬 BC，審查者無法確認 API 是否真正封裝了邊界。 |
| **建議怎麼改** | (1) Document Control 表格新增「Owning Bounded Context / Service」欄位（必填）。(2) §1.1 設計原則新增「Service Encapsulation」：本 API 是其 Bounded Context 的唯一對外介面；其他服務不得直接存取本 BC 的 DB Schema；API Response 不得直接暴露 DB 欄位名稱作為穩定合約（必須有 DTO/View Model 層）。(3) §14 Checklist 新增子節「Bounded Context 封裝」：本 API 已標注 Owning BC、API Response 不直接暴露 DB 欄位、無端點依賴其他 BC 的 DB 表、若本服務獨立部署所有端點仍可正常運作。 |
| **目標檔案** | `templates/API.md`（Document Control、§1.1、§14） |
| **影響範圍** | `templates/API.md` |
| **決策** | 可以|

---

## M-34

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/BRD.md` §5「Proposed Solution」為平坦清單，無子系統（Bounded Context）業務邊界定義；§8.3「技術約束」無 HC-1～HC-5 硬約束的業務層聲明；RTM §3.4 無「Owning Subsystem」欄位，無法將業務目標追溯到具體子系統。 |
| **建議怎麼改** | (1) 新增 §5.5「子系統分解（Bounded Context）」：表格欄位包含「子系統名 | 業務領域 | 擁有的業務規則 | 不擁有的業務規則 | 業務不變量（Invariant）」，要求填入所有子系統（如 member / wallet / deposit / lobby / game）及其業務邊界。(2) §8.3「技術約束」新增必填列：「子系統可拆解性（Spring Modulith HC-1～HC-5）」，說明業務層的跨子系統邊界原則。(3) §3.4 RTM 新增「Owning Subsystem」欄，確保每個業務目標對應一個具體子系統。 |
| **目標檔案** | `templates/BRD.md`（§5.5 新增、§8.3 補充、§3.4 RTM 欄位） |
| **影響範圍** | `templates/BRD.md` |
| **決策** | 可以|

---

## M-35

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/test-plan.md` §3.2 Integration Tests 僅有一行「Service Boundary」描述，Contract Testing（Pact）為可選項而非必要閘；無 Schema 隔離測試、無 DAG 驗證測試、無單一子系統冷啟動測試、無 Async Event Contract 測試。§1.4 Quality Gates 無「合約測試通過率 100%」或「跨 Schema SQL 違規 0」的條件。 |
| **建議怎麼改** | (1) §3.2 Integration Tests 新增必填子節「Module Decomposability Tests」，含以下場景表格：(a) Schema 隔離測試 — 驗證子系統 A 的程式碼不執行子系統 B 的 Schema 的 SQL；(b) Consumer-Driven Contract Tests（Pact，**必要**，非可選）— 每個跨子系統 API pair 均有 Pact 合約測試；(c) Async Event Contract Tests — 每個 Domain Event 的 Producer/Consumer Schema 版本兼容性測試；(d) 單一子系統冷啟動測試 — 僅啟動一個子系統，驗證其全部端點可正常運作（其他子系統以 stub 取代）。(2) §1.4 Quality Gates 新增列：「Contract Test 通過率 100%（Merge 前必要）」和「跨 Schema SQL 違規 0」。(3) §2.1 In-Scope 新增「Module 可拆解性驗證」為必填 NFR 測試項。 |
| **目標檔案** | `templates/test-plan.md`（§3.2 新增子節、§1.4 Quality Gates、§2.1） |
| **影響範圍** | `templates/test-plan.md` |
| **決策** | 可以|

---

## M-36

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/runbook.md` 從單一服務視角撰寫，無子系統邊界定義（每個 K8s Deployment 歸屬哪個 BC）；§4 Deployment Procedures 無「子系統提取程序」（從合部署到獨立部署的操作步驟）；§3.2 SLOs 無子系統層級的可觀測性指引；§7 Troubleshooting 無「跨子系統 API 呼叫失敗」場景。 |
| **建議怎麼改** | (1) 新增 §1.3「子系統邊界參考（Subsystem Boundary Reference）」：表格欄位包含「Bounded Context | K8s Deployment | Owning DB Schema | Public API Prefix | Event Topics」，列出所有子系統的操作邊界。(2) 新增 §4.X「子系統提取程序（Subsystem Extraction Procedure）」：從合部署切換到獨立部署的 step-by-step，含：新建 Namespace、部署子系統及其獨立 DB Schema、設定新 Ingress、更新 Service Discovery、對新端點執行合約測試、流量切換、從原部署移除。(3) §3.2 SLOs 補充：各子系統 Prometheus label 設計指引（`subsystem="member"` 等），使 SLO 可按子系統切片。(4) §7 Troubleshooting 新增場景「跨子系統 API 呼叫失敗」：症狀識別、診斷步驟、修復指引。 |
| **目標檔案** | `templates/runbook.md`（§1.3 新增、§4.X 新增、§3.2 補充、§7 補充） |
| **影響範圍** | `templates/runbook.md` |
| **決策** | 可以|

---

## M-37

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/LOCAL_DEPLOY.md` 假設所有子系統一起啟動（`make k8s-apply` 套用全部 overlay），無「單一子系統啟動」模式；無子系統分解地圖（哪些 K8s 資源屬於哪個 BC）；無各子系統的 Kustomize overlay 設計；§14 Mock Services 只覆蓋第三方外部服務，無對「缺席子系統」的 stub 指引。 |
| **建議怎麼改** | (1) 新增 §2.X「子系統分解地圖（Subsystem Decomposition Map）」：表格和圖，說明每個 K8s Deployment/Service 歸屬哪個 BC、其 Owning Schema、對外 API Prefix、Event Topics。(2) 新增 §4.X「單一子系統啟動（Single Subsystem Startup）」：說明如何只啟動單個 BC（例如 `make k8s-apply-wallet`），對應 `k8s/overlays/local-{subsystem}/` 的 Kustomize overlay 結構；其他子系統以 WireMock/msw stub 取代。(3) §6 Development Commands 新增每個子系統的 make target（`k8s-apply-{subsystem}`、`health-check-{subsystem}`、`logs-{subsystem}`）。(4) §14 Mock Services 新增「內部子系統 Stub」子節：當進行單一子系統開發時，如何用 WireMock 模擬其他子系統的 Public API。 |
| **目標檔案** | `templates/LOCAL_DEPLOY.md`（§2.X 新增、§4.X 新增、§6 補充、§14 補充） |
| **影響範圍** | `templates/LOCAL_DEPLOY.md` |
| **決策** |可以 |

---

---

## M-38

| 欄位 | 內容 |
|------|------|
| **違規事由** | **BDD 九件套全部缺少 Spring Modulith 覆蓋。** 專家讀檔確認（2026-05-02）：`BDD.md`、`BDD-server.md`、`BDD-client.md` 及其對應 gen.md / review.md 共 9 個檔案，對 HC-1～HC-5 五條硬約束的覆蓋為零。具體缺失：(1) `BDD.md` §2 Feature File 命名規範以 domain 目錄組織，但沒有 Bounded Context 概念，無跨 BC 整合場景、無 Domain Event 合約測試場景；(2) `BDD-server.md` §5 Contract Testing 只覆蓋 HTTP 合約，無模組邊界驗證（HC-2）、無跨 BC 呼叫只透過 Public Interface 的場景；(3) `BDD.gen.md` Self-Check 22 項、`BDD-server.gen.md` Self-Check 16 項，均無 HC-1～HC-5 任何項目；(4) `BDD-server.review.md` Layer 3 Item 11 觸及 async operation（HC-3 邊緣）但只關心測試 Flaky，不驗證 Domain Event 合約；(5) 無任何「單一子系統冷啟動 BDD 情境」（僅啟動一個 BC 驗證其行為）；(6) 無 `@cross-module`、`@event-contract`、`@modulith` 等 tag，無對應生成規則。 |
| **建議怎麼改** | **(A) BDD.md**：(1) §2 Feature File 命名規範新增「Spring Modulith 模組組織」：`features/{bounded-context}/{domain}/` 結構，每個 BC 有獨立目錄，從 ARCH §4 或 EDD §3.4 推導 BC 名稱。(2) §10 Tag Strategy 新增 tag 族群：`@modulith`（全部 BC 整合場景）、`@cross-module`（跨 BC 呼叫只透過 Public Interface 驗證）、`@event-contract`（Domain Event 生產者/消費者合約）、`@module-isolation`（單一子系統冷啟動）。(3) 新增 §18「Spring Modulith BDD 場景模板」：提供 Domain Event 合約場景的標準 Given/When/Then 格式：`Given [Module A] 狀態滿足觸發條件 / When [Event Name] 事件已發布 / Then [Module B] 的可觀測行為符合預期`；提供 HC-2 Public Interface 場景：`Given 模組 A 需要模組 B 的資料 / When 呼叫模組 B 的公開 API / Then 回傳符合合約的資料（無直接 DB cross-access）`。(4) §16 HA BDD Scenario Patterns 仿照格式，新增 §16.5「Module Decomposability Scenarios」。**(B) BDD-server.md**：(1) §3 Standard Feature File Template 新增 Cross-Module Contract 標記格式。(2) §5 Contract Testing 擴充為兩層：HTTP Contract（Pact，現有）+ Domain Event Contract（schema version 兼容性測試）。**(C) BDD.gen.md**：(1) 生成規則新增：從 ARCH §4 服務邊界表推導所有跨 BC dependency pair，每個 pair 至少生成一個 `@event-contract` 場景；(2) Self-Check 新增：`[ ] 每個跨 BC 依賴有對應的 @event-contract 場景`、`[ ] 每個 Bounded Context 有至少一個 @module-isolation 冷啟動場景`、`[ ] 無場景在模組 A 的 step 中直接操作模組 B 的 DB 資料（HC-1）`。**(D) BDD-server.gen.md**：(1) F-03 Step Definition Skeleton 新增 Event Contract test stub（Kafka consumer mock + schema validation）；(2) Self-Check 新增：`[ ] 跨模組呼叫場景驗證 step 指向 Public Service Interface（HC-2）`。**(E) BDD-server.review.md**：(1) Layer 3 新增審查項「Domain Event Contract — 有跨 BC 依賴時，是否有 @event-contract 場景覆蓋 Event Schema 版本（MEDIUM）」；(2) Layer 5 Upstream Alignment 新增「Bounded Context 覆蓋 — features/ 目錄結構是否對應 ARCH §4 的每個 BC（HIGH）」。 |
| **目標檔案** | `templates/BDD.md`（§2、§10、新增 §18）、`templates/BDD-server.md`（§5）、`templates/BDD.gen.md`（生成規則、Self-Check）、`templates/BDD-server.gen.md`（F-03 skeleton、Self-Check）、`templates/BDD-server.review.md`（Layer 3、Layer 5） |
| **影響範圍** | BDD 五件（BDD-client 三件為 UI 範疇，不需改動） |
| **決策** | 可以|

---

## M-39

| 欄位 | 內容 |
|------|------|
| **違規事由** | **新需求**：LOCAL_DEPLOY 未整合 client（前端 UI）和 admin（後台管理介面）到同一個 k8s Ingress 對外 Port，導致無法用「一個 URL 分享測試環境」。專家讀檔確認：(1) `LOCAL_DEPLOY.md` §5 Service Reference 已有 `http://{{PROJECT_SLUG}}.local/` → web-app 和 `/api` → api-server，但 `admin-service` 不在 Ingress 規則中（`has_admin_backend=true` 條件區塊缺少 Ingress patch）；(2) §19 Docker Compose 明確標注「docker-compose 模式無 Ingress，各服務各自對外暴露 port，與 K8s 單一 port 80 不同」— 與單一 port 目標矛盾；(3) 無 admin SPA 路由的 nginx fallback 說明（admin 部署在 `/admin/` 路徑時，前端 router basename 和 vite build base 須一致設定，否則靜態資源全部 404）；(4) 無 admin 建置時 `base: '/admin/'` 的強制要求；(5) 無 single-port routing 驗證指令。**架構理由**：Ingress path-based routing（Traefik / k3s built-in）已是 k8s local dev 的標準模式，不需額外元件；docker-compose 側以 nginx reverse proxy container 達到同等效果，消除兩種啟動方式的 URL 差異，QA / 分享測試只需一個 URL。 |
| **建議怎麼改** | **(A) templates/LOCAL_DEPLOY.md 骨架**：(1) §2 Architecture Overview 的 Ingress 圖加入 admin 路徑：`/admin → admin-service:80`（`has_admin_backend=true` 時）；(2) §5 Service Reference 表格加入 admin 行：`http://{{PROJECT_SLUG}}.local/admin/` 管理介面；(3) §10 Common Issues 加入兩個 admin 常見問題：「admin 靜態資源 404（未設 `base: '/admin/'`）」和「admin 頁面 refresh 404（nginx SPA fallback 未設定 `/admin/index.html`）」；(4) §12 Port Reference 的 Ingress 路徑表加入 admin 行。**(B) templates/LOCAL_DEPLOY.gen.md 生成規則**：(1) `has_admin_backend=true` 條件區塊新增 Ingress patch 段落，包含完整 Traefik Ingress YAML（`/admin` Prefix 規則）及 Traefik Middleware（如需 strip prefix 則生成，如 API server 自帶 `/api` prefix 則不需要）；(2) §4.4 Build Image 生成規則的 admin 段落加入建置約束：「admin 前端 image 必須以 `base: '/admin/'`（Vite）或等效框架設定建置，並加入驗證指令 `grep -q 'src="/admin/' ... index.html`」；(3) §4.5 Deployment 驗證步驟加入 admin 驗證：`curl http://{{PROJECT_SLUG}}.local/admin/` 回 200 且 SPA deep-link `curl http://{{PROJECT_SLUG}}.local/admin/login` 亦回 200；(4) §18 AI Quick Start Script 的驗證段落加入 admin 條件驗證；(5) §19 Docker Compose 生成規則重寫單一 Port 模式：移除「各服務各自對外暴露 port」敘述，改為「nginx proxy container 在 Port 80 提供統一入口」，生成 `docker/proxy/nginx.conf`（含 `/api`、`/admin`、`/` 三段 proxy_pass）；(6) §19 Docker Compose Iron Constraint 同步更新：`proxy` service 對外 ports 只有 `80:80`，各 backend service 不暴露 nodePort。**(C) 路由設計原則（寫入 gen.md 生成說明）**：推薦 Option B（API server 路由含 `/api` prefix，無需 Traefik stripPrefix middleware），原因：`kubectl port-forward` 直連時路徑一致，調試更直觀；admin nginx container 需要 SPA fallback 設定：`try_files $uri $uri/ /admin/index.html`，所有 `/admin/*` 請求返回 admin 的 `index.html`，由 client-side router 處理路由；admin 前端的 API 呼叫必須使用絕對路徑 `/api/...`（不得使用相對路徑）。 |
| **目標檔案** | `templates/LOCAL_DEPLOY.md`（§2、§5、§10、§12）、`templates/LOCAL_DEPLOY.gen.md`（Ingress 生成規則、§4.4/§4.5/§18/§19） |
| **影響範圍** | LOCAL_DEPLOY 兩件；間接影響 docker/admin/nginx.conf 的生成說明 |
| **決策** |可以 |

---

共 39 項修改（M-01 至 M-39），跨 28+ 個檔案。

**M-28～M-39 修改優先順序建議（依依賴關係）**：
1. M-28、M-29、M-30（EDD 三件套）— 最上游，其他文件依賴 EDD 的 BC 定義
2. M-31（ARCH 三件套）— 依賴 EDD BC Map
3. M-32（SCHEMA 兩件）— 依賴 EDD §3.4 Schema Ownership
4. M-33（API.md）— 依賴 ARCH §4 服務邊界
5. M-34（BRD.md）— 業務層定義，可與 M-28 並行
6. M-35（test-plan.md）— 依賴 EDD Domain Event + ARCH 邊界
7. M-36（runbook.md）— 依賴 ARCH §4 + EDD §3.4
8. M-37（LOCAL_DEPLOY.md）— 依賴 ARCH §4 + Subsystem Boundary Reference
9. M-38（BDD 五件）— 依賴 ARCH §4 服務邊界（推導跨 BC dependency pair）
10. M-39（LOCAL_DEPLOY Single-Port）— 可與 M-37 合併執行，依賴 has_admin_backend flag

*版本：2026-05-02 v7（新增 M-38：BDD 九件套 Spring Modulith 覆蓋；M-39：LOCAL_DEPLOY Single-Port client+admin+API 統一 Port 80）*

---

## M-40

| 欄位 | 內容 |
|------|------|
| **需求來源** | 新功能需求（2026-05-02）：CI/CD 工具選型 + 本地 Pipeline 模擬能力 |
| **問題描述** | 目前 gendoc 所有 templates（EDD、ARCH、runbook、LOCAL_DEPLOY）均未涵蓋 CI/CD pipeline 工具設計與本地模擬。企業開發者在 PR 前無法在 local 環境執行完整 CI/CD pipeline dry-run，導致 pipeline 問題只能在 CI server 上才被發現，PR reject 率高、反饋週期長。具體缺失：(1) 無 CI/CD 工具選型指引（Jenkins / Tekton / ArgoCD）；(2) LOCAL_DEPLOY.md 無 Jenkins-on-k3s 安裝章節；(3) 無 `jenkinsfile-runner` 本地 dry-run 說明；(4) 無 Makefile 共享腳本模式（讓 local 和 CI 執行相同指令）；(5) 無獨立 CICD.md template。 |
| **專家評估** | **需求完全合理，是企業工程文化的正確方向。** Survey 結果：Jenkins 仍是企業最大裝機量，`jenkinsfile-runner`（官方專案）可在本地單次執行 Jenkinsfile 無需啟動完整 server；Kubernetes plugin 讓 Jenkins on k3s 成為支援的模式（`ungerts/k3s-jenkins`、`deors/workshop-pipelines` 有 working reference）。現代替代方案 Tekton + ArgoCD 是 Kubernetes-native 方向，但 Jenkins 對企業遷移路徑友好。Screwdriver CD 僅 Yahoo/Verizon 系統使用，不適合本專案。業界最佳實踐：CI 和 local 使用「相同 Make targets」作為共享介面，避免 CI-as-snowflake 問題。 |
| **建議怎麼改** | **(A) 新增 `templates/CICD.md`**（新 template）：(1) Document Control（CI 工具 `{{CI_TOOL}}`，預設 Jenkins；CD 工具 `{{CD_TOOL}}`，預設 ArgoCD）；(2) §1 Pipeline Architecture（Jenkins-on-k3s 架構圖：Jenkins server + Kubernetes Plugin + ephemeral agent pod）；(3) §2 Jenkinsfile 骨架（stages: Checkout → Build → Unit Test → Integration Test → Image Build → Deploy to Local K8s → Smoke Test）；(4) §3 Local Pipeline Dry-Run（`jenkinsfile-runner` 安裝 + `docker run jenkinsfile-runner` 指令）；(5) §4 Shared Make Targets（`make ci-build`、`make ci-test`、`make ci-deploy` — CI 和 local 共用，消除「本地 OK CI 炸掉」）；(6) §5 PR Gate（PR merge 前必跑的 pipeline stage 清單）。**(B) 新增 `templates/CICD.gen.md` + `templates/CICD.review.md`**（三件套）。**(C) `templates/LOCAL_DEPLOY.md` 新增 §20 CI/CD 本地模擬**：(1) Jenkins on k3s 安裝（Helm chart `jenkins/jenkins` + Kubernetes Plugin 設定）；(2) `jenkinsfile-runner` 安裝 + 本地 dry-run 指令；(3) 本地 pipeline 驗證指令（確認 agent pod 正常建立/銷毀）。**(D) `templates/EDD.md`**：CI/CD 工具欄位補充 `{{CI_TOOL}}`（Jenkins / Tekton）+ `{{CD_TOOL}}`（ArgoCD / Helm）及架構說明。**(E) `templates/LOCAL_DEPLOY.gen.md`**：§20 CI/CD 生成規則（根據 state.ci_tool 選擇 Jenkins 或 Tekton 的安裝說明）。 |
| **目標檔案** | 新增：`templates/CICD.md`、`templates/CICD.gen.md`、`templates/CICD.review.md`；修改：`templates/LOCAL_DEPLOY.md`（新增 §20）、`templates/LOCAL_DEPLOY.gen.md`（§20 生成規則）、`templates/EDD.md`（CI/CD 工具欄位） |
| **影響範圍** | 新增 3 個 template；修改 3 個現有 template；gendoc-auto SKILL.md 需加入 CICD step |
| **工作量評估** | 大（需設計新 CICD 三件套） |
| **決策** | 可以|

---

## M-41

| 欄位 | 內容 |
|------|------|
| **需求來源** | 新功能需求（2026-05-02）：本地 K8s 密碼安全管理 — 不進 git、不用 .env、OS-level 安全存儲 + 每次重啟重生成 |
| **問題描述** | 目前 LOCAL_DEPLOY.md 的 secret 處理方式存在安全隱患：(1) `k8s/overlays/local/secrets.env` 檔案若未加入 .gitignore 有進 git 風險；(2) 靜態密碼（如 DB password `secret`）在文件中明文標注，開發者容易複製到其他環境；(3) 無「每次重啟重生成密碼」機制，靜態密碼模式有規律可猜；(4) 不支援 macOS Keychain / Windows Credential Manager 存放固定憑證（如 registry token、OAuth secret）；(5) 雙平台（macOS / Windows）無對應的 bootstrap script。 |
| **專家評估** | **需求完全合理，符合企業安全標準。** Survey 結果整理為三層設計：**層 1（Ephemeral 密碼，每次重生成）**：`openssl rand -hex 32 \| kubectl create secret --from-literal` 是業界最廣泛做法；`mittwald/kubernetes-secret-generator` 是最優雅的 in-cluster 方案（annotation 標記，controller 自動生成，無需 bootstrap script）。**層 2（固定憑證，OS Keychain 存儲）**：macOS `security` CLI + Windows PowerShell `CredentialManager` 可在 bootstrap script 中讀取，適合不能重生成的憑證（Docker Hub token、npm private registry token）。**層 3（企業 Password Manager）**：1Password `op inject` 或 Bitwarden Secrets Manager Operator 是有 password manager 的團隊的首選，1Password Kubernetes Operator 有第一方支援。注意：OS Keychain → K8s Secret 無成熟橋接工具，需要 DIY bootstrap script，onboarding 成本略高但可接受。每次重啟重生成的密碼讓靜態密碼模式消失，安全性顯著提升。 |
| **建議怎麼改** | **(A) `templates/LOCAL_DEPLOY.md` 新增 §X Secret Bootstrap**（建議放在 §3 Prerequisites 後，§4 之前）：(1) 三層 secret 策略說明（Ephemeral / OS Keychain / Password Manager）；(2) 層 1 Ephemeral：`scripts/bootstrap-secrets.sh`（macOS/Linux）模板，使用 `openssl rand` 生成 DB_PASSWORD / REDIS_AUTH / JWT_SECRET / ADMIN_INIT_PASSWORD 並 `kubectl create secret`；`scripts/bootstrap-secrets.ps1`（Windows）等效 PowerShell 版本；(3) 層 2 OS Keychain：macOS Keychain 讀取指令（`security find-generic-password -w -s "{{PROJECT_SLUG}}-registry" -a "dev"`）+ Windows Credential Manager 讀取（`(Get-StoredCredential -Target "{{PROJECT_SLUG}}-registry").GetNetworkCredential().Password`）；適用場景：Docker Hub login、private npm/Maven registry token；(4) 重啟重生成規則：每次 `make k8s-clean`（namespace 刪除）或 `make secrets-rotate` 後必須重跑 bootstrap script；(5) mittwald/secret-generator 選項說明（in-cluster 自動生成，無需手動跑 script）；(6) 禁止規則：禁止 `.env` 進 git（`.gitignore` 必須包含 `*.env`, `secrets.env`, `.env.*`）。**(B) `templates/LOCAL_DEPLOY.gen.md`**：(1) Secret Bootstrap 生成規則（雙平台 bootstrap script 內容）；(2) Self-Check 加入：`[ ] 無 .env 檔案進 git（.gitignore 已包含 *.env 規則）`；(3) Quality Gate 加入：`Ephemeral 密碼 | bootstrap script 存在且使用 openssl rand（非靜態值）`。**(C) `templates/LOCAL_DEPLOY.review.md`**：(1) 加入 CRITICAL 審查項：「.env 或 secrets.env 進 git — Risk：密碼洩漏」；(2) 加入 HIGH 審查項：「靜態密碼（DB password = 'secret'）無重生成機制」。**(D) 新增 `scripts/bootstrap-secrets.sh` + `scripts/bootstrap-secrets.ps1` 模板說明**（不是真實 script，是 template 中說明 gen agent 應生成的 script 格式）。 |
| **目標檔案** | 修改：`templates/LOCAL_DEPLOY.md`（新增 §X Secret Bootstrap）、`templates/LOCAL_DEPLOY.gen.md`（生成規則 + Self-Check + Quality Gate）、`templates/LOCAL_DEPLOY.review.md`（CRITICAL/HIGH 審查項）；間接：gen agent 應在目標專案生成 `scripts/bootstrap-secrets.sh` 和 `scripts/bootstrap-secrets.ps1` |
| **影響範圍** | LOCAL_DEPLOY 三件套；間接影響所有使用 local K8s 的目標專案 |
| **工作量評估** | 中（雙平台 bootstrap script 模板設計有細節） |
| **決策** | 可以|

---

## M-42

| 欄位 | 內容 |
|------|------|
| **需求來源** | 新功能需求（2026-05-02）：k9s 安裝納入 LOCAL_DEPLOY Prerequisites + Runbook 補充 k9s 操作指引 |
| **問題描述** | 目前 LOCAL_DEPLOY.md §1 Prerequisites 和 runbook.md §7 Troubleshooting 均只提供 `kubectl` 指令，沒有 k9s 相關內容：(1) `make k9s` 指令已在 §6 Development Commands 出現（`k9s -n {{K8S_NAMESPACE}}-local`），但 §1 Prerequisites 沒有 k9s 安裝說明；(2) runbook.md §7 各診斷場景只有 `kubectl` 指令，無 k9s 等效操作；(3) 無 k9s 快速鍵參考章節供 on-call 工程師使用。 |
| **專家評估** | **需求合理，工作量小，建議採用「kubectl 為主、k9s 為補充」模式。** Survey 結果：k9s 有 ~33,500 GitHub stars，廣泛使用於 SRE / 平台工程師，是事實上的標準互動式 K8s 工具。業界共識：kubectl 是 canonical（可腳本化、CI 環境、任何 terminal 均可用），k9s 是 power user 效率層（互動式 triage、on-call 快速診斷）。建議模式：runbook §7 各場景**保留 kubectl 指令為主**，每個場景末尾加入 k9s 等效快捷鍵作為「Quick Reference」方塊，不取代 kubectl 主指令。原因：kubectl 指令可直接 copy-paste 進腳本和 CI；k9s 操作依賴本地 terminal session 和特定按鍵綁定，不適合作為 runbook 唯一指令。 |
| **建議怎麼改** | **(A) `templates/LOCAL_DEPLOY.md` §1 Prerequisites**：(1) 在工具清單加入 k9s：`k9s`（`brew install derailed/k9s/k9s` / `choco install k9s` / `scoop install k9s`）+ 版本要求（`≥ v0.32`）；(2) `make k9s` 指令已存在，確認 §6 指令說明保持一致。**(B) `templates/LOCAL_DEPLOY.md` 新增 §X k9s 快速操作參考**（建議放在 §11 Logs & Debugging 後）：常用操作對照表：進入特定 namespace（`:ns` 選擇）、過濾 Pod（`/` 搜尋）、查看 logs（`l`）、exec 進 container（`s`）、port-forward（`shift-f`）、查看資源（`:deploy`、`:pod`、`:svc`、`:cm`、`:secret`）、刪除資源（`ctrl-d`）、描述資源（`d`）、編輯資源（`e`）；附加 k9s skin / config 說明（`~/.config/k9s/`）。**(C) `templates/runbook.md` §7 各 troubleshooting 場景**：在每個 §7.X 場景的診斷指令段落末尾，加入固定格式的 k9s 等效方塊：`> **k9s 等效操作（互動式）**`，列出對應按鍵順序（例如 §7.1 API Server 5xx：`:pod` → `/{{API_APP_LABEL}}` 篩選 → `l` 查看 logs）。格式固定、簡短，不取代 kubectl 主指令。 |
| **目標檔案** | 修改：`templates/LOCAL_DEPLOY.md`（§1 Prerequisites + 新增 k9s Quick Reference 章節）、`templates/runbook.md`（§7.1～§7.11 各場景加 k9s 等效方塊） |
| **影響範圍** | LOCAL_DEPLOY.md、runbook.md；不影響 gen.md / review.md（k9s 是使用層，不影響生成規則） |
| **工作量評估** | 小（格式固定，工作量可控） |
| **決策** | 可以|

---

共 42 項修改（M-01 至 M-42），跨 30+ 個檔案。

**M-40～M-42 修改優先順序建議（依依賴關係）**：
1. M-42（k9s）— 最小，可獨立執行，不依賴其他 M 項
2. M-41（Secret Bootstrap）— 中量，依賴 LOCAL_DEPLOY 現有結構，可在 M-42 後執行
3. M-40（CI/CD）— 最大，需設計新 CICD 三件套，建議在 M-41/M-42 完成後執行

*版本：2026-05-02 v8（新增 M-40：CI/CD Jenkins on k3s + 本地 Pipeline 模擬；M-41：Secret Bootstrap 雙平台 OS Keychain + Ephemeral 密碼；M-42：k9s 安裝 + Runbook k9s 操作指引）*

---

## M-43

| 欄位 | 內容 |
|------|------|
| **需求來源** | 新功能需求（2026-05-02）：Local Developer Platform — Gitea 本地 git server + Production Parity + 非開發者可用的完整 CI/CD flow |
| **問題描述** | M-40 實作的 CICD.md / LOCAL_DEPLOY.md §21 假設遠端 git server（GitHub / GitLab）存在，導致以下缺口：(1) **無遠端 source 無法使用 Jenkins**：開發者若無 GitHub 帳號或無法存取 remote，Jenkins Multibranch Pipeline 無 SCM source 可配置，整個 CI 流程無法啟動；(2) **jenkinsfile-runner dry-run 只能驗證語法邏輯**，無法測試 Kubernetes agent pod 的實際執行（因為 dry-run 不啟動 Jenkins server），無法驗證 ephemeral pod 建立/銷毀；(3) **無標準化 dev tools UI 存取方式**：Jenkins（Port 8080）、ArgoCD（Port 8443）已有，但無 Gitea（Port 3000），且三者均無 Makefile 統一入口（`make jenkins-ui` 等），非開發者無法使用；(4) **開發工具 port 與應用 port 80 的域分離未明確文件化**，新進人員不清楚為何 Port 3000/8080/8443 與 Port 80 可同時開著；(5) **Production Parity 原則未落地**：CICD.md 未明確說明「本地與生產使用相同工具鏈」，導致文件使用者誤以為本地是「簡化版」而非「縮小版」。 |
| **專家評估** | **需求完全合理，對齊業界最高標準。** 評估依據：(A) **12-Factor App #10 Dev/Prod Parity**（Heroku，2011）：本地環境與生產環境越相似，部署失敗率越低。本設計：本地 = k3s + Jenkins + ArgoCD + Gitea；生產 = EKS/GKE + Jenkins + ArgoCD + GitHub/Gitea，差異只有規模和 TLS，完全符合 Parity 原則。(B) **Platform Engineering / Internal Developer Platform（IDP）設計目標**（Spotify Backstage 2020、Google Paved Road、Netflix DevProd）：把 CI/CD 複雜性封裝在 `make` targets 裡，開發者只需知道指令名稱，不需了解底層工具。本設計的 `make dev-tools-up` / `make gitea-ui` 等正是 IDP 的本地實現。(C) **Gitea 技術可行性**：Gitea 單 pod，< 200MB RAM，helm chart 成熟，Jenkins Git plugin 支援 `http://gitea.dev-tools.svc.cluster.local:3000` URL，Webhook 支援（Jenkins 收到 push event 自動觸發），完全可在 k3s 執行。(D) **Port 域分離設計正確性**：應用域（Port 80，Traefik Ingress，面向使用者/QA/AI 測試）vs 開發工具域（Port 3000/8080/8443，`kubectl port-forward`，面向開發者），兩者生命週期不同、受眾不同、設計目的不同，分開是正確的 Separation of Concerns。業界從未見過把 Jenkins 塞進 `/jenkins` path 的企業實作。(E) **非開發者可用性**：Makefile target 是公認的「最小門檻抽象層」，任何懂 terminal 的人都能執行 `make dev-tools-up`，不需要懂 Helm、k8s、Jenkins。 |
| **建議怎麼改** | **(A) `templates/CICD.md` 新增兩個章節（插入現有 §8 Security 之前，重新編號）**：**新 §8 Local Developer Platform**：(1) 架構圖（`dev-tools` namespace 包含 Gitea pod + Jenkins pod；`argocd` namespace 包含 ArgoCD；`{{K8S_NAMESPACE}}-local` 包含應用服務；Port 域對照表：應用域 Port 80 vs 開發工具域 Port 3000/8080/8443）；(2) Gitea 安裝（`helm install gitea gitea-charts/gitea -n dev-tools`，含 `gitea-values.yaml`：adminUser/adminPassword、service ClusterIP、persistence 256Mi、resources request 100m/128Mi limit 500m/512Mi）；(3) Gitea → Jenkins Webhook 設定步驟（Gitea: Settings → Webhooks → Jenkins URL `http://jenkins.ci.svc.cluster.local:8080/gitea-webhook/post`；Jenkins: Gitea plugin 設定 SCM URL 指向本地 Gitea）；(4) ArgoCD 以本地 Gitea 為 source（`spec.source.repoURL: http://gitea.dev-tools.svc.cluster.local:3000/dev/{{PROJECT_SLUG}}.git`）；(5) **Gitea 首次推送 workflow**（`git remote add local http://localhost:3000/dev/{{PROJECT_SLUG}}.git` → `git push local main`）；**新 §9 Makefile dev-tools targets**：完整 Makefile 實作（`dev-tools-up`：helm install gitea + jenkins + argocd，等待所有 pod ready；`dev-tools-status`：`kubectl get pods -n dev-tools -n argocd`；`gitea-ui`：port-forward + 印出 URL；`jenkins-ui`：port-forward + 印出 URL；`argocd-ui`：port-forward + 印出 URL + 取得初始密碼；`dev-tools-down`：helm uninstall；`dev-tools-logs`：stern -n dev-tools）；**(B) `templates/CICD.gen.md` 新增 Step 8-9 生成規則**：(1) §8 Gitea values 中的 `adminPassword` 必須從 `LOCAL_DEPLOY.md §3.5` bootstrap-secrets.sh 取得（ephemeral 生成，`openssl rand -hex 16`）；(2) Gitea SCM URL 格式：`http://gitea.dev-tools.svc.cluster.local:3000/dev/{{PROJECT_SLUG}}.git`；(3) §9 Make targets 的 `dev-tools-up` 必須包含 readiness wait（`kubectl rollout status -n dev-tools`）；(4) `gitea-ui` / `jenkins-ui` / `argocd-ui` 各自必須印出 URL 和預設帳號提示；**(C) `templates/CICD.review.md` 新增審查項**（Layer 2）：(1) **[CRITICAL] R-X：§8 Gitea SCM URL 使用 `localhost` 而非 cluster DNS** — Risk：Jenkins pod 內無法解析 localhost → CI pipeline 每次 checkout 失敗；Fix：改為 `http://gitea.dev-tools.svc.cluster.local:3000`；(2) **[HIGH] R-X：§9 `dev-tools-up` 缺少 readiness wait** — Risk：後續指令在 pod 未 ready 時執行 → 隨機失敗；Fix：加入 `kubectl rollout status`；(3) **[MEDIUM] R-X：`argocd-ui` target 未印出初始密碼取得方式** — Risk：第一次登入找不到密碼；Fix：補 `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=...`；**(D) `templates/LOCAL_DEPLOY.md §21` 擴充（在現有 §21.1 Jenkins 之前插入）**：**新 §21.0 Local Developer Platform 架構**：(1) 全平台架構圖（ASCII art 版，含四個 namespace：dev-tools / argocd / myapp-local / kube-system；Port 對照表：80/3000/8080/8443 各自的用途和受眾）；(2) Port 域說明（為何應用 Port 80 和開發工具 Port 3000/8080/8443 可同時開著、不衝突）；(3) **非開發者 4 步 onboarding**：`make dev-tools-up`（啟動所有工具）→ `git remote add local http://localhost:3000/dev/{{PROJECT_SLUG}}.git` + `git push local main`（推送到本地 Gitea）→ 開瀏覽器 http://localhost:8080（看 Jenkins 自動觸發）→ 開瀏覽器 https://localhost:8443（看 ArgoCD sync）；(4) Production 對照表（本地 vs 生產的工具對應，差異只有 scale 和 TLS）；**(E) `templates/LOCAL_DEPLOY.gen.md §21` 更新**：新增 §21.0 生成規則（Gitea adminPassword 從 §3.5 bootstrap-secrets.sh 取；Gitea SCM URL 用 cluster DNS；非開發者 onboarding 步驟必須 < 5 行指令）；**(F) `templates/pipeline.json` 新增 D20-CICD step**：在 D19-HTML 之後加入 `{"id": "D20-CICD", "name": "CICD", "template": "templates/CICD.md", "gen_md": "templates/CICD.gen.md", "review_md": "templates/CICD.review.md"}`；**(G) `templates/EDD.md` §3.4 Gitea 欄位**：在 CI 工具 / CD 工具之後加入「本地 Git Server」欄位：`{{LOCAL_GIT_SERVER}}`（預設 Gitea，alt: none 若有 remote）；**(H) `docs/PRD.md` v2.8 changelog + LOCAL_DEPLOY 標準 #6 擴充（已完成）**；**(I) `README.md` 更新**：新增 `cicd` 至 Supported Document Types；新增 Local Developer Platform 至 Key capabilities（已完成）。 |
| **目標檔案** | 修改：`templates/CICD.md`（新增 §8 Local Developer Platform + §9 Makefile targets，舊 §8/§9 重新編號）、`templates/CICD.gen.md`（Step 8-9 生成規則）、`templates/CICD.review.md`（新增 3 項審查）、`templates/LOCAL_DEPLOY.md`（§21.0 Local Developer Platform 架構）、`templates/LOCAL_DEPLOY.gen.md`（§21.0 生成規則）；新增/修改：`templates/pipeline.json`（D20-CICD step）、`templates/EDD.md`（§3.4 本地 Git Server 欄位）；已更新：`docs/PRD.md`（v2.8 changelog + 標準 #6）、`README.md`（capabilities + 文件類型）。 |
| **影響範圍** | CICD 三件套（修改現有 M-40 產出）；LOCAL_DEPLOY 兩件（修改現有 M-39/M-41/M-42 產出）；pipeline.json；EDD.md；PRD.md；README.md |
| **工作量評估** | 中（主要是在 M-40 基礎上擴充，設計已確定） |
| **依賴關係** | 依賴 M-40（CICD 三件套已存在）；M-41（§3.5 Secret Bootstrap 提供 Gitea password 來源）；M-39（§21 LOCAL_DEPLOY CI/CD 節基礎結構）|
| **決策** | |

---

共 43 項修改（M-01 至 M-43），跨 32+ 個檔案。

**M-43 執行優先順序建議**：
1. 先確認 M-40 已完成（CICD 三件套已存在）✅
2. 修改 CICD.md（新增 §8 Local Developer Platform + §9 Makefile targets）
3. 更新 CICD.gen.md + CICD.review.md（對應生成規則 + 審查項）
4. 更新 LOCAL_DEPLOY.md §21.0 + LOCAL_DEPLOY.gen.md §21.0
5. 更新 pipeline.json（D20-CICD）
6. 更新 EDD.md（§3.4 本地 Git Server 欄位）

*版本：2026-05-02 v9（新增 M-43：Local Developer Platform — Gitea + Production Parity + 非開發者可用 CI/CD + Port 域分離設計文件化）*

---

## M-44

| 欄位 | 內容 |
|------|------|
| **需求來源** | 新功能需求（2026-05-02）：開發者日常操作手冊 — DEVELOPER_GUIDE.md 三件套，填補「建置之後的每日操作層」空白 |
| **問題描述** | 目前三份主要文件均未覆蓋「建置完成後，開發者每天如何操作」：(1) `LOCAL_DEPLOY.md` 負責第一次建置（1,973 行，一次性使用），建好後開發者不會每天翻它；(2) `runbook.md` 負責生產事故（namespace 是 `{{K8S_NAMESPACE}}`，不是 local 的 `{{K8S_NAMESPACE}}-local`），且目標讀者是 SRE / on-call 工程師，開發者用錯 namespace 會出事；(3) `CICD.md` 是 pipeline 設計文件，描述架構，不是操作手冊；(4) 實際缺少的場景：「我 git push 了，Jenkins 沒有觸發，怎麼辦？」「Pipeline 第 3 個 stage 失敗了，要去哪裡看 log？怎麼只重跑那個 stage？」「ArgoCD 一直顯示 OutOfSync，原因是什麼？」「密碼要換，要跑哪個指令？」—— 這些問題三份文件都沒有完整的 step-by-step 答案。 |
| **專家評估** | **需求真實存在，填補的是實際開發者體驗的空白，不是理論上的文件完整性。** 評估依據：(A) **受眾分離是設計原則，不是文件數量問題**：On-call 工程師凌晨收到告警打開 runbook.md，不應看到「如何設定 Gitea webhook」；開發者遇到 Jenkins 未觸發打開 runbook.md，找到的指令 namespace 是生產環境 → 誤操作風險。混合受眾的文件兩邊都爛掉。(B) **LOCAL_DEPLOY.md 已達合理上限（1,973 行）**：繼續在 LOCAL_DEPLOY.md 裡加「日常操作」章節，文件定位模糊（建置 + 操作混合），且開發者找東西找不到。(C) **業界對應實踐**：GitHub Engineering 有獨立的 「Developer Guide」；Stripe Engineering 有獨立的「Local Development Handbook」；AWS 有「Getting Started」vs「Day 2 Operations」分開文件。這是業界慣例，不是過度設計。(D) **DEVELOPER_GUIDE.md 的具體內容有明確邊界**：覆蓋「環境建好之後，到生產事故之前」的這段操作空間；不重複 LOCAL_DEPLOY.md 的建置步驟；不重複 runbook.md 的生產事故處理；不重複 CICD.md 的 pipeline 架構說明。 |
| **建議怎麼改** | **(A) 新增 `templates/DEVELOPER_GUIDE.md`（骨架）**，章節結構：(1) **Document Control**（doc-type: DEVELOPER_GUIDE；前提：LOCAL_DEPLOY.md §21 CI/CD 環境已建置完成；適用對象：開發者，非 SRE）；(2) **§1 每日開發工作流程**：完整 step-by-step 涵蓋 6 個場景 —— ①新功能開發（feature branch push → CI → deploy → verify）；②Hotfix（直接 main branch，緊急流程）；③只改前端（跳過 integration test？說明 Make target 邏輯）；④只改 schema（migration 如何在 CI 裡執行）；⑤多人協作（同一 Gitea repo，branch 保護規則，PR 合併後 ArgoCD 自動部署）；⑥Dry-Run 驗證（jenkinsfile-runner，push 前先本地跑）；(3) **§2 CI/CD 診斷與修復（Jenkins / ArgoCD / Gitea）**：逐場景 step-by-step —— ①Jenkins 未收到 Webhook（Gitea webhook 設定驗證 3 步驟）；②Pipeline stage 失敗（去哪裡看 log：Console Output path；怎麼只重跑一個 stage：Replay 功能 + 限制；怎麼完整重跑：Rebuild）；③ArgoCD OutOfSync（3 種原因分類：git 有改動但未 push 到 Gitea / helm values 漂移 / manifest 語法錯誤；各自解法）；④Image pull 失敗（registry credentials 過期的排查 3 步驟）；⑤Agent Pod 起不來（k3s 資源不足 / image pull policy / RBAC 問題）；(4) **§3 本地環境快速指令（Quick Reference）**：表格格式，Make target + 說明 + 何時用 ——`make dev-status`（所有 pod 狀態）、`make dev-logs service=api`（特定服務 log）、`make dev-restart service=api`（重啟特定服務，不重建 image）、`make dev-health`（curl 所有 health endpoint，含 Jenkins / ArgoCD / Gitea / App）、`make gitea-ui / jenkins-ui / argocd-ui`（開 browser + port-forward）、`make dev-tools-status`（CI/CD 工具 pod 狀態）、`make k9s`（互動式 k8s 管理）；(5) **§4 常見問題 + 解法（本地環境版）**：與 runbook.md §7 明確區隔（runbook = 生產 namespace；本節 = local namespace），條目：①Pod CrashLoopBackOff（本地版，排查 4 步驟）；②Port 衝突（哪個 process 佔用，kill 方式）；③密碼 / secret 失效（重跑 bootstrap-secrets.sh 的時機和方式）；④Namespace 狀態混亂（make k8s-clean 的執行條件，防止誤刪）；⑤Local image 未更新（build cache 問題，`--no-cache` 時機）；⑥Gitea push 被 reject（credentials 或 repo 不存在，3 種原因）；⑦Jenkins 初始密碼忘記（重新取得指令）；(6) **§5 環境維護（排程建議）**：每日（無需動作，自動監控）；每週（清理舊 image：`make dev-cleanup`；確認所有 pod healthy：`make dev-health`）；每月（helm repo update；確認 Gitea / Jenkins / ArgoCD 版本）；secret rotate（`make secrets-rotate`，觸發條件說明）；完全重置（`make dev-tools-down && make k8s-clean && make dev-setup`，步驟和預期耗時）；(7) **§6 與其他文件的邊界**：明確表格說明本文件 vs LOCAL_DEPLOY.md vs runbook.md vs CICD.md 各自負責的範圍，防止未來章節混淆。**(B) 新增 `templates/DEVELOPER_GUIDE.gen.md`（生成規則）**：(1) Iron Law：生成前必須讀取 `LOCAL_DEPLOY.md`（確認 §21 CI/CD 工具安裝指令）、`CICD.md`（確認 Make targets 名稱、Jenkinsfile stages）、`runbook.md`（確認 §7 各診斷場景，避免重複）；(2) 兩個專家角色：Developer Experience Engineer（§1/§3/§4 工作流程與快速指令）+ DevOps Diagnostics Expert（§2/§5 CI/CD 診斷與維護）；(3) 逐章節生成規則：§1 工作流程必須從 `CICD.md §4 Shared Make Targets` 取得正確 target 名稱；§2 Jenkins 診斷 log path 必須與 `CICD.md §2 Jenkinsfile` 的 stage 名稱一致；§3 Make targets 必須驗證 `LOCAL_DEPLOY.md §6` 所有 target 均存在；§4 本地 namespace 必須使用 `{{K8S_NAMESPACE}}-local`（不得使用生產 namespace）；(4) Quality Gate：無 `{{PLACEHOLDER}}` 殘留；§2 Jenkins log path 與 CICD.md 一致；§3 所有 Make target 均可在 LOCAL_DEPLOY.md §6 找到對應；§4 所有指令的 namespace 均含 `-local` 後綴；**(C) 新增 `templates/DEVELOPER_GUIDE.review.md`（審查標準）**，4 層共 10 項：Layer 1 工作流程完整性（CRITICAL：§1 是否涵蓋 6 個開發場景；HIGH：step-by-step 指令中 Make target 名稱是否與 LOCAL_DEPLOY.md §6 一致）；Layer 2 CI/CD 診斷可操作性（CRITICAL：§2 是否有 Jenkins 未觸發的排查步驟；HIGH：Jenkins log path 是否與 CICD.md Jenkinsfile 一致）；Layer 3 本地環境隔離（CRITICAL：§4 所有指令 namespace 是否含 `-local`，與生產隔離；MEDIUM：§6 邊界表格是否列出與 runbook.md 的區隔）；Layer 4 維護可操作性（HIGH：§5 完全重置步驟是否有預期耗時說明；MEDIUM：secret rotate 觸發條件是否明確）；**(D) `templates/pipeline.json` 新增 D21-DEVELOPER_GUIDE step**：`{"id": "D21-DEVELOPER_GUIDE", "name": "DEVELOPER_GUIDE", "template": "templates/DEVELOPER_GUIDE.md", "condition": "always"}`（無條件生成，所有專案都需要）；**(E) `docs/PRD.md` v2.9 changelog + LOCAL_DEPLOY 標準 #6 擴充（已完成）**；**(F) `README.md` 更新（已完成）**：新增 `developer-guide` 至 Supported Document Types；新增 Developer Daily Operations Manual 至 Key capabilities。 |
| **目標檔案** | 新增：`templates/DEVELOPER_GUIDE.md`、`templates/DEVELOPER_GUIDE.gen.md`、`templates/DEVELOPER_GUIDE.review.md`；修改：`templates/pipeline.json`（D21-DEVELOPER_GUIDE）；已更新：`docs/PRD.md`（v2.9 changelog + 標準 #6）、`README.md`（capabilities + 文件類型）。 |
| **影響範圍** | 新增 3 個 template（DEVELOPER_GUIDE 三件套）；pipeline.json 新增 D21 step；PRD / README 已更新 |
| **工作量評估** | 中（三件套設計明確，§1~§6 章節邊界清晰，主要工作是生成規則與審查標準的細節設計） |
| **依賴關係** | 依賴 LOCAL_DEPLOY.md（§6 Make targets、§21 CI/CD 工具）；依賴 CICD.md（§2 Jenkinsfile stages、§4 Shared Make Targets、§8/§9 Local Developer Platform）；依賴 runbook.md（§7 各診斷場景，避免內容重複）；建議在 M-43 完成後執行（確認 Gitea / Make targets 設計定案） |
| **決策** | |

---

共 44 項修改（M-01 至 M-44），跨 33+ 個檔案。

**M-44 執行優先順序建議**：
1. 確認 M-43 決策（DEVELOPER_GUIDE §2 的 Gitea webhook 診斷依賴 M-43 的 Gitea 設計）
2. 建立 DEVELOPER_GUIDE.md 骨架（§1~§6）
3. 建立 DEVELOPER_GUIDE.gen.md（生成規則，含 upstream 讀取清單）
4. 建立 DEVELOPER_GUIDE.review.md（4 層 10 項審查標準）
5. 更新 pipeline.json（D21-DEVELOPER_GUIDE）

*版本：2026-05-02 v10（新增 M-44：DEVELOPER_GUIDE.md 三件套 — 開發者日常操作手冊，填補 LOCAL_DEPLOY 建置後的每日操作空白）*

---

## M-45

| 欄位 | 內容 |
|------|------|
| **需求來源** | 新功能需求（2026-05-02）：gendoc-gen-diagrams skill 缺乏 CI/CD Pipeline + 本地基礎設施 UML 圖，無法支援「讀文件即可建置系統」目標 |
| **問題描述** | M-40 至 M-44 新增了 3 個新子系統（CI/CD Pipeline、Local Developer Platform、Developer Workflow），但 `/gendoc-gen-diagrams` skill 完全沒有對應的視覺化輸出：(1) **CI/CD 流程無序列圖**：CICD.md §2 Jenkinsfile 有 7 個 stages 的文字描述，但沒有「Developer push → Gitea webhook → Jenkins Agent Pod 建立 → ci-build/test/image → Kaniko 推 image → ci-deploy → ArgoCD sync → ci-smoke」的端對端序列圖；讀文件的 AI 或人類無法直觀理解整個流程的觸發鏈；(2) **本地基礎設施無拓撲圖**：LOCAL_DEPLOY §21 描述 k3s 有 3 個 namespace（`dev-tools` / `{{K8S_NAMESPACE}}-local` / `argocd`）+ 4 個 port（80 / 3000 / 8080 / 8443），但沒有視覺化拓撲圖說明哪些服務在哪個 namespace、哪個 port、Traefik Ingress 的邊界在哪裡、port-forward 的路徑；這是最難用文字描述的「網狀關係」，缺圖導致開發者在建置時頻繁混淆；(3) **PR Gate 流程無活動圖**：CICD.md §5 的 branch protection rules 是 YAML 格式，required-status-checks 是清單，但沒有「什麼時候 block、什麼條件 pass、merge 後 CD 如何接手」的活動流程圖；(4) **Secret 三層流動路徑無視覺化**：LOCAL_DEPLOY §3.5 定義了 Ephemeral / OS Keychain / mittwald 三層 Secret 策略，CICD.md §8 描述 CI 中的 Secret 管理，但沒有「Secret 從哪裡生成、流到哪個 namespace 的 k8s Secret、最終如何注入到 pod env」的流動圖；Secret 管理是安全設計中最容易出錯的環節，缺圖導致按文件建置的人看不出層次；(5) **現有 deployment.md 未標注 CD 層**：Step 2.11 的 Deployment Diagram 只從 EDD §4.5.9 + ARCH.md 讀取，沒有讀 CICD.md §7 ArgoCD Application，導致部署圖上看不到「代碼如何到達 k8s」的 CD 路徑標注。 |
| **專家評估** | **需求真實且緊迫，是「文件能建置系統」目標的最後一塊拼圖。** 評估依據：(A) **UML 圖的核心價值是表達「無法用線性文字表達的網狀/時序關係」**：Sequence Diagram = 跨系統時序（誰先誰後、誰等誰）；Deployment Diagram = 空間拓撲（誰在哪、連到誰）；Activity Diagram = 條件分支流程（什麼時候 block、什麼時候 pass）；這三種關係用文字描述效率極低，CI/CD + Local Infra 正好是典型案例。(B) **第一性原則檢驗**：目標是「AI 或人類讀文件，按步驟能建置出同等系統」。測試問題：「只讀 CICD.md，能畫出 CI/CD 流程圖嗎？」現在的答案是「不能」—— 因為 Jenkinsfile 有 stages，但誰觸發 Jenkins、Jenkins 如何建立 Agent Pod、Kaniko image 推到哪裡、ArgoCD 如何 sync，這個完整鏈路沒有視覺化。有圖之後的答案是「能」。(C) **方案選型**：Option A（新建 `gendoc-gen-cicd-diagrams` skill）：缺點是使用者需記憶兩個 skill，邏輯分裂，State 讀取重複；Option B（在現有 skill 新增 Step 2D，條件觸發）：完全符合現有 Step 2B（Frontend）/ Step 2C（Admin）的條件觸發模式，單一入口，使用者只呼叫 `/gendoc-gen-diagrams`。**選 Option B**，理由：使用者問的正是「/gendoc-gen-diagrams 是不是要更新」，確認入口不要分裂。(D) **現有 skill 規模可行性**：目前 1,220 行，新增 Step 2D 約 +150 行，最終 ~1,370 行，在合理範圍內（2B Frontend 段本身就有 ~240 行）。(E) **5 張圖的必要性分析**：每一張對應一個「只靠文字無法清楚表達的關係」，無冗餘；其中 infra-local-topology.md 是開發者建置時最常查的拓撲參考，優先級最高。 |
| **建議怎麼改** | **只修改 `skills/gendoc-gen-diagrams/SKILL.md`，不新增 skill**。具體變更：**(A) 新增 Step 2D（條件觸發：`docs/CICD.md` 存在）**，共 5 張新圖，輸出至 `docs/diagrams/cicd/`：**2D-1 `cicd-pipeline-sequence.md`**（sequenceDiagram）— CI/CD 端對端序列圖；Participants：Developer / Gitea / Jenkins Controller / Jenkins Agent Pod / Container Registry / k3s / ArgoCD；覆蓋：git push → webhook → Agent Pod 建立（kubernetes plugin）→ ci-build（make） → ci-test-unit → ci-test-integration → Kaniko image build + push → ci-deploy → pod rollout → ArgoCD sync → ci-smoke → Pipeline 成功/失敗 → Agent Pod 銷毀；alt 分支：ci-test 失敗 → ci-rollback → Pipeline FAILED；來源：CICD.md §2 Jenkinsfile + §7 ArgoCD；**2D-2 `cicd-pr-gate-activity.md`**（flowchart TD）— PR Gate + 分支保護流程活動圖；覆蓋：feature branch commit → local dry-run（jenkinsfile-runner）→ git push → PR 建立 → required-status-checks 觸發（Build / Unit Test / Integration Test / Image Build）→ 全部 pass → Code Review → Approve → Merge → CD 接手（ArgoCD 偵測 main 分支變更 → 自動 sync）；decision 節點：「dry-run 失敗？」→ 修 Jenkinsfile；「CI check 未全 pass？」→ PR blocked；來源：CICD.md §3 + §5；**2D-3 `infra-local-topology.md`**（graph TD，C4-style）— 本地 k3s 基礎設施拓撲圖；涵蓋：4 個 namespace 邊界框（kube-system / dev-tools / argocd / {{K8S_NAMESPACE}}-local）；每個 namespace 內的 Service 節點（標注 ClusterIP + port）；對外存取路徑（Port 80 via Traefik Ingress、Port 3000/8080/8443 via kubectl port-forward）；Gitea → Jenkins webhook 內部路徑；ArgoCD → Gitea SCM URL 內部路徑；應用服務內部通訊路徑（API → DB / Redis）；Port 域標色區分（應用域 Port 80：綠色；開發工具域 Port 3000/8080/8443：橙色）；來源：LOCAL_DEPLOY.md §21.0 + CICD.md §8；**2D-4 `developer-workflow-activity.md`**（flowchart TD，swimlane）— 開發者每日工作流程活動圖（**條件**：`docs/DEVELOPER_GUIDE.md` 存在，否則從 CICD.md §3 + §5 推斷基本工作流）；swimlane：`Developer | Local CI | Gitea | Jenkins | ArgoCD`；覆蓋：git pull → feature branch → code → make dev-test → local dry-run（jenkinsfile-runner）→ git push → PR → Jenkins CI → review → merge → ArgoCD sync → verify；每個 swimlane actor 的行動標注對應 Make target；來源：DEVELOPER_GUIDE.md §1（若存在）/ CICD.md §3+§5（fallback）；**2D-5 `cicd-secret-flow.md`**（graph LR）— Secret 三層流動路徑圖；Layer 1：Secret 來源（開發者 macOS Keychain / Linux openssl rand / mittwald secret-generator annotation）→ Layer 2：CI Secret（Jenkins credentials store：REGISTRY_TOKEN / DB_PASSWORD / REDIS_AUTH / JWT_SECRET，對應 CICD.md §8 Secret Location table）→ Layer 3：k8s Secret 注入（`ci` namespace 的 `registry-credentials` / `app-secrets`）→ Layer 4：Pod env injection（Jenkinsfile `credentials()` + `kubectl create secret`）→ 應用 Pod 讀取 env；標注每個 Secret 的類型（Ephemeral / Fixed / in-cluster）；來源：CICD.md §8 + LOCAL_DEPLOY.md §3.5；**(B) 更新 Step 2.11 `deployment.md` 生成規則**：在現有「讀取 EDD §4.5.9 + ARCH.md」之後，新增「若 `docs/CICD.md` 存在，讀取 §7 ArgoCD Application YAML，在 Deployment Diagram 中補充 CD 層標注：GitOps source（Gitea/GitHub repo）→ ArgoCD Controller → k8s Apply → Pod Rollout」；**(C) 更新 Step 0 環境偵測**：新增 `_HAS_CICD=$([ -f "${_DOCS_DIR}/CICD.md" ] && echo "yes" || echo "no")` + 在環境摘要印出 CI/CD UML 觸發狀態；**(D) 更新 Step 2D 完整度驗證**（類比 Step 2B-17）：5 張圖各自的驗證項目（sequence participant 數、activity decision 節點數、topology namespace 框數等）；**(E) 更新 frontmatter description**：新增「CI/CD-: pipeline-sequence / pr-gate-activity / infra-local-topology / developer-workflow / secret-flow」到描述中；**(F) 更新 Step 4 輸出摘要**：新增 Step 2D 的 ✓/✗/skip 清單。 |
| **目標檔案** | 修改：`skills/gendoc-gen-diagrams/SKILL.md`（新增 Step 2D + 更新 Step 2.11 + 更新 Step 0 + 更新 Step 4 + 更新 frontmatter）；不新增任何 template 檔案，不修改任何 template 檔案 |
| **影響範圍** | 只影響 `/gendoc-gen-diagrams` skill 執行結果（新增 5 張圖至 `docs/diagrams/cicd/`）；不影響其他 skill；不影響任何 template |
| **工作量評估** | 中（主要是撰寫 5 個圖的強制完整度標準，約 +150 行） |
| **依賴關係** | 依賴 M-40（CICD.md 存在，2D 才觸發）；依賴 M-41（LOCAL_DEPLOY §3.5 Secret Bootstrap 是 cicd-secret-flow.md 的 Layer 1 來源）；依賴 M-43（§21.0 Local Developer Platform 架構是 infra-local-topology.md 的主要來源）；M-44 非必要依賴（developer-workflow-activity.md 有 DEVELOPER_GUIDE.md 時取最完整來源，否則從 CICD.md 推斷，不 block） |
| **決策** | |

---

共 45 項修改（M-01 至 M-45），跨 33+ 個檔案。

*版本：2026-05-02 v11（新增 M-45：gendoc-gen-diagrams 新增 Step 2D — CI/CD + 本地基礎設施 UML 5 張圖，填補 M-40~M-44 新子系統的視覺化缺口）*

---

## M-46

| 欄位 | 內容 |
|------|------|
| **需求來源** | 結構性缺陷評估（2026-05-02）：`templates/pipeline.json` 在 M-40~M-45 連續新增需求後，存在 5 個確認 bug，導致「按 pipeline 順序執行即可建置完整系統」的目標無法達成 |
| **問題描述** | 以下 5 個問題均由 `python3` 分析 `pipeline.json` 原始碼 + grep 各 `.gen.md` 確認，非推斷：**(1) D07b-UML 位置錯誤（最嚴重 bug）**：目前 D07b-UML 排在 D07-ARCH 之後、D08-API 之前（第 16 位）。但 `skills/gendoc-gen-diagrams/SKILL.md` Step 1 的 upstream-docs 明確列出：EDD.md、ARCH.md、**API.md**、**SCHEMA.md**、FRONTEND.md、PDD.md、VDD.md。API.md（D08，第 17 位）、SCHEMA.md（D09，第 19 位）、FRONTEND.md（D10，第 21 位）在 D07b-UML 執行時均**尚未生成**，導致：(a) `class-inventory.md` 只能從 EDD §4.5.2 classDiagram 提取（fallback 模式），遺漏 API layer 和 SCHEMA 的所有 entity；(b) Step 2B（Frontend UML）條件是 `HAS_FRONTEND`，但 FRONTEND.md 不存在，**Step 2B 永遠被跳過**；(c) `test-plan.gen.md` 和 `RTM.gen.md` 消費 `class-inventory.md`（兩個 .gen.md 均已確認讀取此檔），但拿到的是殘缺 class 清單；(d) UML 圖（class diagram / deployment diagram / sequence diagram）缺少 API endpoints 和 DB schema entity，輸出圖的覆蓋率不到設計層的 40%；**(2) CICD.md 無 pipeline step（M-40 遺漏）**：`python3` 確認：`CICD step 存在: False`。M-40 建立了 CICD 三件套（templates/CICD.md + CICD.gen.md + CICD.review.md），但忘記在 `pipeline.json` 中新增對應 step。效果：執行 `/gendoc-auto` 時，CICD.md 永遠不會被自動生成，使用者必須手動呼叫 `/gendoc CICD`，違背「按 pipeline 順序即可完整建置」的核心目標。CICD.gen.md frontmatter 要求 EDD.md、ARCH.md、LOCAL_DEPLOY.md 三個 upstream，確認必須排在 D15-LOCAL_DEPLOY 之後；**(3) DEVELOPER_GUIDE.md 無 pipeline step（M-44 提案遺漏預告）**：`python3` 確認：`DEVELOPER_GUIDE step 存在: False`。M-44 提案指出需新增 `templates/DEVELOPER_GUIDE.md` 三件套，但 pipeline.json 中亦無對應 step（M-44 提案文字有提到「D21-DEVELOPER_GUIDE」但該 step 尚未加入 pipeline.json）。依賴關係：DEVELOPER_GUIDE.gen.md 需讀 LOCAL_DEPLOY.md §6（Make targets）、CICD.md §2+§4（Jenkinsfile stages + Shared Make Targets）、runbook.md §7（避免重複），確認必須排在 CICD.md 之後；**(4) D20-PROTOTYPE 編號混亂（邏輯 bug）**：pipeline.json 陣列中，D20-PROTOTYPE 排在 D19-HTML **之前**執行（陣列順序才是執行順序，step id 的數字大小不代表執行順序）。但 step id「D20」比「D19」大，造成：(a) 人類讀 pipeline 時誤認為 D20 在 D19 之後；(b) 未來維護者插入新 step 時，容易把 step 插入 D19 和 D20 之間（邏輯上以為 D19 是倒數第二），實際上破壞執行順序；(c) `gendoc-config` 選單顯示 step id 時，D20-PROTOTYPE 排在 D19-HTML 後面，與實際執行順序相反；**(5) D16-ALIGN 覆蓋範圍落後**：D16-ALIGN 排在 D15-LOCAL_DEPLOY 之後執行（對齊現有 pipeline 設計）。但在 M-46 修復後，D15b-CICD 和 D15c-DEVELOPER_GUIDE 會新增到 D15-LOCAL_DEPLOY 之後、D16-ALIGN 之前，D16-ALIGN **可以且應該**審查這兩個新文件與上游的對齊關係（例如：CICD.md §4 Make targets 是否與 LOCAL_DEPLOY.md §6 一致；DEVELOPER_GUIDE.md §2 Jenkins log path 是否與 CICD.md §2 Jenkinsfile stage 名稱一致）。若 pipeline.json 不在 D16-ALIGN 的注釋中補充說明，gendoc-align-check SKILL 可能不知道要稽核這兩個新文件。 |
| **專家評估** | **5 個問題全部必須修復，無一可以接受「暫緩」。** 核心論據：(A) **D07b-UML 位置錯誤的連鎖影響最大**：`class-inventory.md` 是 `test-plan.gen.md` 和 `RTM.gen.md` 的 upstream input，錯誤的 class-inventory 會導致 Unit Test RTM §15.2 的 class→test coverage 不完整，品質層文件的正確性依賴設計層文件的完整性，這是「下游文件污染」，修復優先級為 P0。同時 Step 2B（Frontend UML）永遠跳過，讓 frontend 子系統缺少所有視覺化，與 M-45 的新增目標直接衝突。(B) **CICD.md 無 pipeline step 違背工具的核心承諾**：gendoc 的核心價值命題是「執行 `/gendoc-auto` 即可完整生成所有文件」。CICD.md 是 M-40 明確新增的文件類型，缺少 pipeline step 等同「功能上線但未接入主幹流程」，這是 M-40 的遺漏，必須補充。(C) **D20-PROTOTYPE 編號混亂是維護性定時炸彈**：gendoc 是給所有人用的工具，pipeline.json 必須是可維護、可讀的。ID 比 D19 大卻排在 D19 之前，違背最小驚訝原則（Principle of Least Astonishment），必須修正。(D) **D15d-UML-CICD 的必要性**：M-45 的 Step 2D 是「條件觸發：`docs/CICD.md` 存在」。若 CICD.md 在 pipeline 中排在 D07b-UML 之後（即 D15b），則 D07b-UML 執行時 CICD.md 尚未生成，Step 2D 永遠 skip。解法是在 pipeline 中，CICD.md 生成後，新增一個 D15d-UML-CICD step，專門執行 gendoc-gen-diagrams 的 Step 2D（5 張 CI/CD 相關圖）。這樣 infra-local-topology.md 等圖才能被生成並被 D19-HTML 收錄。 |
| **建議怎麼改** | **只修改 `templates/pipeline.json`（單一檔案，所有 5 個 bug 集中修復）**。具體變更清單：**(Fix-1) 將 D07b-UML 從位置 16 移至位置 27（D10f-RESOURCE 之後，D11-test-plan 之前），重命名為 D10g-UML**：移動後，UML step 執行時所有 upstream docs（API.md / SCHEMA.md / FRONTEND.md / AUDIO / ANIM / CLIENT_IMPL / ADMIN_IMPL / RESOURCE）均已存在；class-inventory.md 可從完整設計層提取 entity；Step 2B（Frontend UML）條件觸發正常運作；test-plan 和 RTM 消費到正確的 class-inventory。**此為高影響修復，不涉及任何 skill 修改**；**(Fix-2) 在 D15-LOCAL_DEPLOY 之後新增 D15b-CICD step**（補 M-40 遺漏）：`{"id": "D15b-CICD", "name": "CICD", "phase": "運維層", "condition": "always", "template": "templates/CICD.md", "gen_skill": "gendoc-gen-cicd", "review_skill": "reviewdoc", "gen_md": "templates/CICD.gen.md", "review_md": "templates/CICD.review.md", "output": "docs/CICD.md"}`；**(Fix-3) 在 D15b-CICD 之後新增 D15c-DEVELOPER_GUIDE step**（補 M-44 遺漏）：`{"id": "D15c-DEVELOPER_GUIDE", "name": "DEVELOPER_GUIDE", "phase": "運維層", "condition": "always", "template": "templates/DEVELOPER_GUIDE.md", "gen_skill": "gendoc-gen-developer-guide", "review_skill": "reviewdoc", "gen_md": "templates/DEVELOPER_GUIDE.gen.md", "review_md": "templates/DEVELOPER_GUIDE.review.md", "output": "docs/DEVELOPER_GUIDE.md"}`；**(Fix-4) 在 D15c-DEVELOPER_GUIDE 之後新增 D15d-UML-CICD step**（M-45 Step 2D）：`{"id": "D15d-UML-CICD", "name": "UML-CICD Diagrams", "phase": "運維層", "condition": "docs/CICD.md exists", "skill": "gendoc-gen-diagrams", "args": "--step 2D", "output": "docs/diagrams/cicd/"}`；此 step 確保 infra-local-topology.md 等 5 張圖在 CICD.md 和 LOCAL_DEPLOY.md 均生成後才執行，且在 D16-ALIGN 之前完成，讓 D16 能稽核圖的內容；**(Fix-5) 將 D20-PROTOTYPE 重命名為 D18b-PROTOTYPE 並移至 D18-MOCK 之後、D19-HTML 之前**：ID 從 D20 改為 D18b，使執行順序（D17→D18→D18b→D19）與 ID 排序（D17<D18<D18b<D19）一致，消除維護性混亂；**(Fix-6) 在 D16-ALIGN step 的 `notes` 欄位新增說明**：`"alignment_scope_note": "包含稽核 CICD.md（§4 Make targets vs LOCAL_DEPLOY.md §6）、DEVELOPER_GUIDE.md（§2 Jenkins log path vs CICD.md §2 Jenkinsfile stage name）、diagrams/cicd/（infra-local-topology namespace 數量 vs LOCAL_DEPLOY §21.0）"`。**修復後完整 pipeline 執行順序**（共 35 steps，含 4 個新 step + 1 個重命名）：需求層（D01-IDEA → D01-IDEA-R → D02-BRD → D02-BRD-R → D03-PRD → D03-PRD-R → D03.5-CONSTANTS → D04-PDD → D04-PDD-R）→ 設計層（D05-VDD → D05-VDD-R → D06-EDD → D06-EDD-R → D07-ARCH → D07-ARCH-R → D08-API → D08-API-R → D09-SCHEMA → D09-SCHEMA-R → D10-FRONTEND → D10-FRONTEND-R → D10b-AUDIO → D10c-ANIM → D10d-CLIENT_IMPL → D10e-ADMIN_IMPL → D10f-RESOURCE → **D10g-UML**）→ 品質層（D11-test-plan → D12-BDD-server → D12b-BDD-client → D13-RTM）→ 運維層（D14-runbook → D15-LOCAL_DEPLOY → **D15b-CICD** → **D15c-DEVELOPER_GUIDE** → **D15d-UML-CICD**）→ 稽核層（D16-ALIGN → D16-ALIGN-F → D16b-ALIGN-VERIFY）→ 實作層（D17-CONTRACTS → D18-MOCK → **D18b-PROTOTYPE**）→ 發布層（D19-HTML）。 |
| **目標檔案** | 修改：`templates/pipeline.json`（唯一修改檔案）：(1) 移動 D07b-UML → D10g-UML；(2) 新增 D15b-CICD；(3) 新增 D15c-DEVELOPER_GUIDE；(4) 新增 D15d-UML-CICD；(5) 重命名 D20-PROTOTYPE → D18b-PROTOTYPE；(6) 更新 D16-ALIGN notes |
| **影響範圍** | 直接：pipeline.json 排程與步驟定義；間接：`/gendoc-auto` 執行結果（D07b 移位後 class-inventory.md 正確；CICD/DEVELOPER_GUIDE 自動生成；CI/CD UML 圖在 CICD 後觸發）；`gendoc-config` 選單顯示（D18b/D19 順序正確）；`gendoc-align-check`（CICD + DEVELOPER_GUIDE 進入稽核範圍） |
| **工作量評估** | 小（pipeline.json 是純 JSON 設定，只需精確編輯陣列順序和新增節點，無邏輯程式碼） |
| **依賴關係** | 依賴 M-40（CICD 三件套存在，Fix-2 才有意義）；依賴 M-44（DEVELOPER_GUIDE 三件套存在，Fix-3 才能執行）；依賴 M-45（gendoc-gen-diagrams Step 2D 存在，Fix-4 才能執行）；**不依賴** M-43（pipeline 修復可獨立執行，M-43 Gitea 設計只影響 CICD.md 內容，不影響 pipeline 結構） |
| **決策** | |

---

共 46 項修改（M-01 至 M-46），跨 34+ 個檔案。

---

## M-47

| 欄位 | 內容 |
|------|------|
| **需求來源** | 架構原則違反（2026-05-02）：`pipeline.json` 步驟 ID 使用 `D01-IDEA`、`D07b-UML`、`D16-ALIGN` 等數字前綴格式，違反「pipeline 陣列順序才是執行順序，ID 只是語義識別符」的設計原則，並已蔓延到 9 個 SKILL 和 1 個 template 的靜態文字引用中 |
| **問題描述** | **(1) 核心問題：數字前綴暗示順序，與「陣列位置才是執行順序」的設計衝突**：`pipeline.json` 的 steps 陣列順序（index 0、1、2...）才是執行順序，step `id` 只是識別符。但現有 `D01-IDEA`、`D07b-UML`、`D16-ALIGN` 等 ID 攜帶數字，讀者（人類和 AI）自然會用數字推斷執行順序，導致：(a) `D20-PROTOTYPE` 排在 `D19-HTML` 之前執行，但 ID 數字 20 > 19 → 讀者誤認 PROTOTYPE 後執行（M-46 Bug-4 的根源）；(b) M-46 提案的修復方案本身就重複了同個錯誤：新增 `D10g-UML`、`D15b-CICD`、`D15c-DEVELOPER_GUIDE`、`D15d-UML-CICD`，這些 ID 仍用數字 + 字母後綴暗示位置，將來步驟再重排時又會出現同樣的歧義；(c) 子步驟的字母後綴（`D07b`、`D10b`、`D10c`、`D10d`）暗示「主步驟的附屬項」，但實際上 `D10b-AUDIO` 和 `D10-FRONTEND` 是平等的 pipeline 步驟；(2) **文字污染：共 11 個檔案 ~55 處靜態引用**，實測數字如下（python3 + grep 確認）：`gendoc-shared/SKILL.md`：17 處（含 `STEP ID 格式規範` 定義行 660，明文寫「D-prefix 格式，如 D01-IDEA、D07b-UML」，是所有 skill 的規範來源）；`gendoc-flow/SKILL.md`：17 處（含可執行程式碼 L492 `step["id"] in ("PRD", "D03-PRD")` 和 L665 `if [[ "${step_id}" == "UML" \|\| "${step_id}" == "D07b-UML" ]]`，這兩行是 legacy compatibility 殘留，若 pipeline.json 統一改為 semantic ID，這些 `"D03-PRD"` 字串永遠不會被命中，造成靜默的邏輯 bug）；`gendoc-gen-mock/SKILL.md`：8 處（STEP_COMPLETE 信號輸出含 `D18-MOCK`，若 pipeline.json 改名為 `MOCK`，gendoc-flow 收到 `STEP_COMPLETE: D18-MOCK` 但查找 `id=MOCK` → 找不到 → step 進度記錄失敗）；`gendoc-repair/SKILL.md`：4 處（hardcoded `"D19-HTML" in completed` → pipeline 改名後 completed 清單記錄的是 `HTML`，`"D19-HTML" in completed` 永遠 False → repair 邏輯失效）；`gendoc-shared/SKILL.md`：L660 定義「STEP ID 格式為 D-prefix」，這是所有 skill 的共同規範基礎，此處不改，其他 skill 的 D-prefix 引用就無法從源頭消除；其餘：`gendoc-gen-contracts` 1 處、`gendoc-gen-client-bdd` 1 處、`gendoc-rebuild-templates` 1 處、`gendoc-align-check` 1 處、`templates/RTM.gen.md` 2 處，均為 informational 字串，不影響執行邏輯，但會誤導維護者；(3) **commit_prefix 同樣攜帶 D-prefix**：`pipeline.json` 的 `commit_prefix` 欄位格式為 `"docs(gendoc)[D01-IDEA]"`，這些前綴用於 git commit message。若 step ID 改名，commit_prefix 必須同步改名，否則 git log 出現混用格式（新 commits 用 `[IDEA]`，舊 commits 用 `[D01-IDEA]`），造成 git log 查詢的一致性問題。 |
| **專家評估** | **問題確認，必須在所有上述問題被執行之前完成此修復，否則每次新增 step 都會重複製造相同的命名混亂。** 評估依據：(A) **Single Source of Truth 原則**：`pipeline.json` 是執行順序的唯一真相來源，其 `id` 字段應只是無語義附帶的識別符。最低驚訝原則（POLA）要求 ID 不攜帶順序暗示。(B) **陣列位置是唯一的執行順序標準**：任何 gendoc-flow 的步驟迭代都是 `for step in pipe["steps"]`，不是按 ID 數字排序。ID 上的數字永遠是多餘且容易誤導的資訊。(C) **最小可行識別符原則**：步驟 ID 的最小可行格式是匹配 output 文件類型的語義名稱：`IDEA`（生成 IDEA.md）、`EDD`（生成 EDD.md）、`UML`（生成 diagrams/）、`ALIGN`（生成 ALIGN_REPORT.md）。這比 `D06-EDD`、`D07b-UML`、`D16-ALIGN` 更易讀、更不易出錯。(D) **SKILL 程式碼中的 legacy compatibility 殘留是 Bug**：`gendoc-flow` L492 `step["id"] in ("PRD", "D03-PRD")` 原意是同時支援新舊 ID 格式，但若 ID 已統一為 `PRD`，`"D03-PRD"` 這個分支永遠不會命中，是死代碼（dead code），必須清除。同理 L665。(E) **M-46 的新增 step 命名已重蹈覆轍**：D10g-UML、D15b-CICD、D15c-DEVELOPER_GUIDE、D15d-UML-CICD — 這些 M-46 提案的 ID 繼續使用數字前綴，一旦新 steps 插入，這些 g/b/c/d 後綴又會錯位。M-47 必須先於 M-46 執行，或 M-46 與 M-47 合併執行，統一用 semantic ID（UML、CICD、DEVELOPER_GUIDE、UML-CICD）。 |
| **建議怎麼改** | **完整命名對照表（30 → 語義 ID）**：D01-IDEA → `IDEA`；D02-BRD → `BRD`；D03-PRD → `PRD`；D03.5-CONSTANTS → `CONSTANTS`；D04-PDD → `PDD`；D05-VDD → `VDD`；D06-EDD → `EDD`；D07-ARCH → `ARCH`；D07b-UML → `UML`（同時按 M-46 Fix-1 移位至設計層末尾）；D08-API → `API`；D09-SCHEMA → `SCHEMA`；D10-FRONTEND → `FRONTEND`；D10b-AUDIO → `AUDIO`；D10c-ANIM → `ANIM`；D10d-CLIENT_IMPL → `CLIENT_IMPL`；D10e-ADMIN_IMPL → `ADMIN_IMPL`；D10f-RESOURCE → `RESOURCE`；D11-test-plan → `test-plan`；D12-BDD-server → `BDD-server`；D12b-BDD-client → `BDD-client`；D13-RTM → `RTM`；D14-runbook → `runbook`；D15-LOCAL_DEPLOY → `LOCAL_DEPLOY`；D16-ALIGN → `ALIGN`；D16-ALIGN-F → `ALIGN-FIX`；D16b-ALIGN-VERIFY → `ALIGN-VERIFY`；D17-CONTRACTS → `CONTRACTS`；D18-MOCK → `MOCK`；D20-PROTOTYPE → `PROTOTYPE`（同時按 M-46 Fix-5 移至 MOCK 之後）；D19-HTML → `HTML`。**M-46 新增步驟同步採用語義 ID**：D15b-CICD → `CICD`；D15c-DEVELOPER_GUIDE → `DEVELOPER_GUIDE`；D15d-UML-CICD → `UML-CICD`（M-46 Fix-2/3/4 合併到 M-47 執行時直接使用語義 ID，不再需要 D15b/D15c/D15d 前綴）。**修改清單（11 個檔案，共 ~120 處）**：**(A) `templates/pipeline.json`**（根本修復）：(1) 30 個 step `id` 欄位按上方對照表重命名；(2) 30 個 `commit_prefix` 欄位同步更新（格式 `"docs(gendoc)[IDEA]"` 等，保留 commit type 前綴 docs/test/feat）；(3) 5 個 `note` 欄位中的 D-prefix 引用更新（L105 `D11-test-plan → test-plan, D13-RTM → RTM`；L279 `D16-ALIGN → ALIGN`；L291 `D16-ALIGN-F → ALIGN-FIX, D16b-ALIGN-VERIFY → ALIGN-VERIFY`；L329 `D19-HTML → HTML`）；(4) 同步合併 M-46 的所有 pipeline 結構修復（Fix-1～Fix-6），使用語義 ID；**(B) `skills/gendoc-shared/SKILL.md`**（最高優先，此處是規範定義）：(1) L660 規範行：刪除「D-prefix 格式」說法，改為「semantic ID（無數字前綴），如 `IDEA`、`EDD`、`UML`、`ALIGN`、`CONTRACTS`，格式與 pipeline.json 的 `id` 欄位完全一致」；(2) L416 `D11-test-plan` → `test-plan`；(3) L463-465 進度示例：`D01-IDEA～D09-SCHEMA → IDEA～SCHEMA`；`D10-FRONTEND → FRONTEND`；`D10b-AUDIO～D19-HTML → AUDIO～HTML`；(4) L613 `D03-PRD` → `PRD`；L620 `STEP_COMPLETE: D03-PRD` → `STEP_COMPLETE: PRD`；L632 `STEP_FAILED: D11-test-plan` → `STEP_FAILED: test-plan`；L634 `D07b-UML` → `UML`；(5) L710 `"D07-ARCH"` → `"ARCH"`；(6) L840-844 commit 範例：`[D03-PRD]→[PRD]`、`[D06-EDD]→[EDD]`、`[D12-BDD-server]→[BDD-server]`、`[D16-ALIGN]→[ALIGN]`、`[D17-CONTRACTS]→[CONTRACTS]`；(7) L922 `格式 D01-IDEA 至 D19-HTML` → `格式 IDEA 至 HTML（語義 ID，無數字前綴）`；(8) L1015 同 L922；**(C) `skills/gendoc-flow/SKILL.md`**：(1) L492 `step["id"] in ("PRD", "D03-PRD")` → `step["id"] == "PRD"`（移除 D-prefix legacy fallback，dead code）；(2) L588 `step["id"] in ("EDD", "D06-EDD")` → `step["id"] == "EDD"`（2 處）；(3) L665 `"${step_id}" == "UML" || "${step_id}" == "D07b-UML"` → `"${step_id}" == "UML"`；(4) L369 舊格式相容注解 `"D06-EDD" → 舊格式，仍相容` → 刪除（不再有舊格式）；(5) L661-677 所有 `D07b-UML` 文字 → `UML`；(6) L224, L311, L582 注解 `D03-PRD` → `PRD`；(7) L584, L607 注解 `D06-EDD` → `EDD`；(8) L1445 commit 前綴 `test(gendoc)[D12-BDD-server]` → `test(gendoc)[BDD-server]`；(9) L1450 `test(gendoc)[D12b-BDD-client]` → `test(gendoc)[BDD-client]`；**(D) `skills/gendoc-gen-mock/SKILL.md`**（有執行邏輯，最需精準修復）：(1) L66 `STEP_COMPLETE: D18-MOCK` → `STEP_COMPLETE: MOCK`（信號輸出，影響 pipeline 進度記錄）；(2) L583 `STEP_COMPLETE: D18-MOCK` → `STEP_COMPLETE: MOCK`（同上，確認兩處都改）；(3) L541 commit 前綴 `feat(gendoc)[D18-MOCK]` → `feat(gendoc)[MOCK]`；(4) L71 錯誤提示 `D08-API` → `API`；(5) L8, L549, L558, L579 informational 文字 `D18-MOCK → MOCK`, `D19-HTML → HTML`；**(E) `skills/gendoc-repair/SKILL.md`**（有執行邏輯，最需精準修復）：(1) L255 `if "D19-HTML" in completed:` → `if "HTML" in completed:`；(2) L260 `if not any(x["id"] == "D19-HTML" for x in incomplete):` → `if not any(x["id"] == "HTML" for x in incomplete):`；(3) L262 `"id": "D19-HTML"` → `"id": "HTML"`；(4) L254 注解 `D19-HTML` → `HTML`；**(F) `skills/gendoc-align-check/SKILL.md`**：L283 `step=D12-BDD-server` → `step=BDD-server`；**(G) `skills/gendoc-gen-contracts/SKILL.md`**：L10 `D17-CONTRACTS` → `CONTRACTS`；**(H) `skills/gendoc-gen-client-bdd/SKILL.md`**：L111 `D12b-BDD-client` → `BDD-client`；**(I) `skills/gendoc-rebuild-templates/SKILL.md`**：L358 `D01-IDEA` → `IDEA`；**(J) `templates/RTM.gen.md`**：L219 `D13-RTM` → `RTM`；L234 `D13-RTM` → `RTM`；**(K) `docs/ha-spof-modification-plan.md`（本文件）**：M-46 的「建議怎麼改」章節中使用 D10g-UML / D15b-CICD / D15c-DEVELOPER_GUIDE / D15d-UML-CICD 的段落需更新為語義 ID（UML / CICD / DEVELOPER_GUIDE / UML-CICD）；此修正為文件一致性，不影響 M-46 的技術內容。 |
| **目標檔案** | 主要修改：`templates/pipeline.json`（30 個 id + 30 個 commit_prefix + 5 個 note = ~65 處）；`skills/gendoc-shared/SKILL.md`（17 處，含 L660 規範定義 — 最重要）；`skills/gendoc-flow/SKILL.md`（17 處，含 L492/L588/L665 執行邏輯）；`skills/gendoc-gen-mock/SKILL.md`（8 處，含 L66/L583 STEP_COMPLETE 信號）；`skills/gendoc-repair/SKILL.md`（4 處，含 L255/L260/L262 執行邏輯）；次要修改：`skills/gendoc-align-check/SKILL.md`（1 處）、`skills/gendoc-gen-contracts/SKILL.md`（1 處）、`skills/gendoc-gen-client-bdd/SKILL.md`（1 處）、`skills/gendoc-rebuild-templates/SKILL.md`（1 處）、`templates/RTM.gen.md`（2 處）；文件一致性：`docs/ha-spof-modification-plan.md` M-46 段落（D-prefix 新增 step ID 更新） |
| **影響範圍** | 所有 `/gendoc-auto` / `/gendoc-flow` 的 STEP_COMPLETE 信號匹配；`gendoc-config` 選單動態輸出（自動修復，因其讀 pipeline.json `id` 欄位）；`gendoc-repair` 的 D19-HTML hardcode 邏輯；`gendoc-flow` 的 legacy D-prefix fallback（清除死代碼）；git commit message 格式（commit_prefix）；state file `start_step` 欄位說明 |
| **工作量評估** | 中（~120 處精準字串替換，最大風險是 gendoc-gen-mock 的 STEP_COMPLETE 信號和 gendoc-repair 的 Python 邏輯，需逐行確認替換正確）；完全可機械化（sed / python replace），無邏輯變更 |
| **依賴關係** | **M-47 應與 M-46 合併執行（同一 PR）**：M-46 新增的 step ID（D15b-CICD 等）在 M-47 中直接使用語義 ID（CICD 等），避免 D-prefix 污染繼續；若分開執行必須先 M-47 後 M-46；不依賴 M-43/M-44/M-45 |
| **決策** | |

---

共 47 項修改（M-01 至 M-47），跨 35+ 個檔案。

**M-47 執行優先順序建議**：
1. `templates/pipeline.json`（根本改動，先改 ID 再改 commit_prefix）— 與 M-46 合併執行
2. `skills/gendoc-shared/SKILL.md` L660（規範定義行，改後其他 skill 有依據）
3. `skills/gendoc-gen-mock/SKILL.md` L66+L583（STEP_COMPLETE 信號 — 影響執行邏輯）
4. `skills/gendoc-repair/SKILL.md` L255+L260+L262（Python 邏輯 — 影響執行邏輯）
5. `skills/gendoc-flow/SKILL.md` L492+L588+L665（dead code 清除）
6. 其餘 informational 文字（gendoc-shared 範例、RTM.gen.md 等）

*版本：2026-05-02 v12（新增 M-46：pipeline.json 結構修復 — 5 個確認 bug：D07b-UML 位置錯誤、CICD 無 pipeline step、DEVELOPER_GUIDE 無 pipeline step、D20 編號混亂、D16-ALIGN 覆蓋範圍落後）*

**M-46 執行優先順序建議**：
1. Fix-1（D07b-UML → D10g-UML 位置修正）— P0，影響最大，獨立可執行
2. Fix-2（新增 D15b-CICD）— 需 M-40 已完成，確認 CICD 三件套存在
3. Fix-5（D20-PROTOTYPE → D18b-PROTOTYPE）— 純命名修正，獨立可執行
4. Fix-3（新增 D15c-DEVELOPER_GUIDE）— 需 M-44 決策後執行
5. Fix-4（新增 D15d-UML-CICD）— 需 M-45 決策後執行
6. Fix-6（ALIGN notes 更新）— 最後執行，確認前面 fix 都定案

> **注意**：M-46 的所有新增 step 應使用語義 ID（CICD / DEVELOPER_GUIDE / UML-CICD），不使用 D15b/D15c/D15d 前綴，與 M-47 合併執行。

*版本：2026-05-02 v13（新增 M-47：pipeline.json + 9 個 SKILL + 1 個 template 的 D-prefix 命名全面清除 — 共 11 個檔案 ~120 處，消除「數字暗示執行順序」的系統性誤導；M-46 與 M-47 建議合併執行）*
