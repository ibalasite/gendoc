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
| **決策** | |

---

## M-29

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/EDD.gen.md` §3.4 生成規則有「若有多服務」的條件保護，意即單體部署時 Bounded Context 圖可選填，與 Spring Modulith「Day 1 即需要 BC 邊界」原則相矛盾。Self-Check Checklist 無「每個 BC Schema 擁有權已明確」項目，無「模組依賴圖為 DAG」項目。 |
| **建議怎麼改** | (1) 移除 §3.4 生成規則中的「若有多服務」條件，改為「任何系統均必須生成 Bounded Context Map，並填入 Schema Ownership Table（每個 BC 擁有的具體表名）」。(2) §4.6 Domain Event 生成規則補充：每個事件必須填入 `event_schema_version`（初始值 `v1`）和 `topic_name`。(3) Self-Check Checklist 新增：`[ ] 每個 Bounded Context 的 Schema 擁有權已明確（具體表名，無跨 BC DB 直接存取）` 和 `[ ] 模組間依賴圖已驗證為 DAG（無循環依賴）`。 |
| **目標檔案** | `templates/EDD.gen.md`（§3.4 生成規則、§4.6 生成規則、Self-Check Checklist） |
| **影響範圍** | `templates/EDD.gen.md` |
| **決策** | |

---

## M-30

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/EDD.review.md` 審查項 #9「DDD Bounded Context 未定義」嚴重度僅 MEDIUM，且無 Schema 隔離審查項（HC-1 缺失）、無跨模組呼叫只透過公開介面審查項（HC-2 缺失）、無 DAG 驗證審查項（HC-5 缺失）、無跨模組 Shared Mutable State 審查項（HC-4 缺失）。 |
| **建議怎麼改** | 在現有審查項之後新增「Spring Modulith 微服務可拆解性」審查層（Layer N），含以下項目：(1) `[CRITICAL]` SM-01 — Schema 隔離：每個 BC 擁有且只擁有自己的 DB 表，§3.4 Schema Ownership Table 必須填寫具體表名，無兩個 BC 聲明擁有同一張表。Fix：補填 Schema Ownership Table，移除跨 BC FK。(2) `[HIGH]` SM-02 — 跨模組只透過 Public Interface：無直接跨 BC repository/DAO 呼叫路徑。Fix：改為透過目標 BC 的 API 端點或 Domain Event。(3) `[HIGH]` SM-03 — 依賴圖 DAG 驗證：模組間依賴已驗證無循環（附 Mermaid 圖或 DAG 聲明）。Fix：消除循環依賴，重新設計邊界。(4) `[HIGH]` SM-04 — Domain Event Schema 版本化：§4.6 所有 Event 均有 `event_schema_version` 和 `topic_name`。Fix：補齊版本欄位。(5) `[MEDIUM]` SM-05 — 無跨模組 Shared Mutable State：Redis key namespace 隔離，無跨 BC 全域可變物件。Fix：分配獨立 key prefix 給每個 BC。 |
| **目標檔案** | `templates/EDD.review.md`（新增 Spring Modulith 審查層） |
| **影響範圍** | `templates/EDD.review.md` |
| **決策** | |

---

## M-31

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/ARCH.md` §15 Architecture Review Checklist 無 Microservice Decomposability 子節；§4 服務邊界表的「擁有資料」欄為自由文字，無強制填寫具體表名的規則，且無「禁止跨 BC 直接 DB 存取」的明確聲明。`templates/ARCH.gen.md` Self-Check Checklist 27 項無任何 Decomposability 項目；Quality Gate 6 行無 Schema 隔離閘。`templates/ARCH.review.md` 無 Schema 隔離審查項、無 DAG 審查項、無 Shared Mutable State 審查項。 |
| **建議怎麼改** | (A) **ARCH.md**：(1) §4 服務邊界表「擁有資料」欄下方加入明確聲明：「禁止跨服務直接存取他服務的 DB 表，所有跨服務資料存取必須透過 Public API 或 Domain Event（HC-1）」。(2) §15 Checklist 新增子節「微服務可拆解性（MD-01～MD-05）」：MD-01 每個服務 Schema 擁有權已明確（具體表名）、MD-02 跨服務通訊只透過 API 或 Event、MD-03 依賴圖已驗證為 DAG、MD-04 無跨服務 Shared Mutable State、MD-05 每個服務理論上可獨立部署（列出需要變更的接合點）。(B) **ARCH.gen.md**：Self-Check 新增 3 項（§4 Schema 擁有權具體表名、依賴圖 DAG 確認、§15 MD-01～MD-05 已生成）；Quality Gate 新增列：`BC 隔離 | §4 每服務具體擁有表名已填；§15 MD-01~05 均已回答 | 補充缺失項`。(C) **ARCH.review.md**：新增「Layer 5：微服務可拆解性」審查層，含：`[CRITICAL]` Schema 隔離、`[HIGH]` 跨服務只透過 Public Interface、`[HIGH]` 依賴圖 DAG、`[MEDIUM]` 無跨服務 Shared Mutable State（對應 HC-1～HC-4）。 |
| **目標檔案** | `templates/ARCH.md`、`templates/ARCH.gen.md`、`templates/ARCH.review.md` |
| **影響範圍** | ARCH 三件套 |
| **決策** | |

---

## M-32

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/SCHEMA.md` Document Control 無「Owning Bounded Context」欄位；§9 資料完整性約束無跨 BC FK 禁止規則；§16 Schema Review Checklist 無任何 BC 隔離審查項。`templates/SCHEMA.gen.md` 無「Step 0 — Bounded Context 識別」步驟；生成 FK 約束時無跨 BC FK 偵測與阻止規則；Self-Check 和 Quality Gate 無 BC 隔離項。 |
| **建議怎麼改** | (A) **SCHEMA.md**：(1) Document Control 表格新增欄位「Owning Bounded Context / Service」（必填，對應 ARCH §4）。(2) §1 Overview 新增「Schema Boundary Declaration」子節：本 Schema 的唯一擁有服務、外部不得直接 JOIN 的表清單。(3) §9 新增 §9.5「跨 BC FK 禁止」：明確規定 FK 不得引用其他 BC 的表，跨 BC 引用改為應用層管理的 ID-only 策略，加注：`-- Cross-BC reference: enforced at application layer, no DB FK.`。(4) §16 新增子節「Bounded Context 隔離」：本 Schema Owning BC 已標明、所有表屬同一 BC、無跨 BC DB-level FK、跨 BC 引用使用 ID-only。(B) **SCHEMA.gen.md**：生成規則第一步新增「Step 0 — Bounded Context 識別：讀取 EDD §3.4 和 ARCH §4，確認本 SCHEMA 的 Owning BC，填入 Document Control；列出不得被其他 Schema FK 引用的表清單」；Part 3 CREATE TABLE 生成規則補充「每條 FK 驗證引用表屬同一 BC，跨 BC 引用替換為 ID-only + 注釋」；Self-Check 新增 2 項；Quality Gate 新增「BC 隔離」列。 |
| **目標檔案** | `templates/SCHEMA.md`、`templates/SCHEMA.gen.md` |
| **影響範圍** | SCHEMA 兩件（review.md 若有也一併檢查） |
| **決策** | |

---

## M-33

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/API.md` Document Control 無「Owning Bounded Context」欄位；§1.1 設計原則無「Service Encapsulation」原則（禁止 API Response 直接暴露 DB 欄位名）；§14 API Review Checklist 無任何 BC 封裝審查項。若各子系統（member / wallet 等）的 API 文件不宣告歸屬 BC，審查者無法確認 API 是否真正封裝了邊界。 |
| **建議怎麼改** | (1) Document Control 表格新增「Owning Bounded Context / Service」欄位（必填）。(2) §1.1 設計原則新增「Service Encapsulation」：本 API 是其 Bounded Context 的唯一對外介面；其他服務不得直接存取本 BC 的 DB Schema；API Response 不得直接暴露 DB 欄位名稱作為穩定合約（必須有 DTO/View Model 層）。(3) §14 Checklist 新增子節「Bounded Context 封裝」：本 API 已標注 Owning BC、API Response 不直接暴露 DB 欄位、無端點依賴其他 BC 的 DB 表、若本服務獨立部署所有端點仍可正常運作。 |
| **目標檔案** | `templates/API.md`（Document Control、§1.1、§14） |
| **影響範圍** | `templates/API.md` |
| **決策** | |

---

## M-34

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/BRD.md` §5「Proposed Solution」為平坦清單，無子系統（Bounded Context）業務邊界定義；§8.3「技術約束」無 HC-1～HC-5 硬約束的業務層聲明；RTM §3.4 無「Owning Subsystem」欄位，無法將業務目標追溯到具體子系統。 |
| **建議怎麼改** | (1) 新增 §5.5「子系統分解（Bounded Context）」：表格欄位包含「子系統名 | 業務領域 | 擁有的業務規則 | 不擁有的業務規則 | 業務不變量（Invariant）」，要求填入所有子系統（如 member / wallet / deposit / lobby / game）及其業務邊界。(2) §8.3「技術約束」新增必填列：「子系統可拆解性（Spring Modulith HC-1～HC-5）」，說明業務層的跨子系統邊界原則。(3) §3.4 RTM 新增「Owning Subsystem」欄，確保每個業務目標對應一個具體子系統。 |
| **目標檔案** | `templates/BRD.md`（§5.5 新增、§8.3 補充、§3.4 RTM 欄位） |
| **影響範圍** | `templates/BRD.md` |
| **決策** | |

---

## M-35

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/test-plan.md` §3.2 Integration Tests 僅有一行「Service Boundary」描述，Contract Testing（Pact）為可選項而非必要閘；無 Schema 隔離測試、無 DAG 驗證測試、無單一子系統冷啟動測試、無 Async Event Contract 測試。§1.4 Quality Gates 無「合約測試通過率 100%」或「跨 Schema SQL 違規 0」的條件。 |
| **建議怎麼改** | (1) §3.2 Integration Tests 新增必填子節「Module Decomposability Tests」，含以下場景表格：(a) Schema 隔離測試 — 驗證子系統 A 的程式碼不執行子系統 B 的 Schema 的 SQL；(b) Consumer-Driven Contract Tests（Pact，**必要**，非可選）— 每個跨子系統 API pair 均有 Pact 合約測試；(c) Async Event Contract Tests — 每個 Domain Event 的 Producer/Consumer Schema 版本兼容性測試；(d) 單一子系統冷啟動測試 — 僅啟動一個子系統，驗證其全部端點可正常運作（其他子系統以 stub 取代）。(2) §1.4 Quality Gates 新增列：「Contract Test 通過率 100%（Merge 前必要）」和「跨 Schema SQL 違規 0」。(3) §2.1 In-Scope 新增「Module 可拆解性驗證」為必填 NFR 測試項。 |
| **目標檔案** | `templates/test-plan.md`（§3.2 新增子節、§1.4 Quality Gates、§2.1） |
| **影響範圍** | `templates/test-plan.md` |
| **決策** | |

---

## M-36

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/runbook.md` 從單一服務視角撰寫，無子系統邊界定義（每個 K8s Deployment 歸屬哪個 BC）；§4 Deployment Procedures 無「子系統提取程序」（從合部署到獨立部署的操作步驟）；§3.2 SLOs 無子系統層級的可觀測性指引；§7 Troubleshooting 無「跨子系統 API 呼叫失敗」場景。 |
| **建議怎麼改** | (1) 新增 §1.3「子系統邊界參考（Subsystem Boundary Reference）」：表格欄位包含「Bounded Context | K8s Deployment | Owning DB Schema | Public API Prefix | Event Topics」，列出所有子系統的操作邊界。(2) 新增 §4.X「子系統提取程序（Subsystem Extraction Procedure）」：從合部署切換到獨立部署的 step-by-step，含：新建 Namespace、部署子系統及其獨立 DB Schema、設定新 Ingress、更新 Service Discovery、對新端點執行合約測試、流量切換、從原部署移除。(3) §3.2 SLOs 補充：各子系統 Prometheus label 設計指引（`subsystem="member"` 等），使 SLO 可按子系統切片。(4) §7 Troubleshooting 新增場景「跨子系統 API 呼叫失敗」：症狀識別、診斷步驟、修復指引。 |
| **目標檔案** | `templates/runbook.md`（§1.3 新增、§4.X 新增、§3.2 補充、§7 補充） |
| **影響範圍** | `templates/runbook.md` |
| **決策** | |

---

## M-37

| 欄位 | 內容 |
|------|------|
| **違規事由** | `templates/LOCAL_DEPLOY.md` 假設所有子系統一起啟動（`make k8s-apply` 套用全部 overlay），無「單一子系統啟動」模式；無子系統分解地圖（哪些 K8s 資源屬於哪個 BC）；無各子系統的 Kustomize overlay 設計；§14 Mock Services 只覆蓋第三方外部服務，無對「缺席子系統」的 stub 指引。 |
| **建議怎麼改** | (1) 新增 §2.X「子系統分解地圖（Subsystem Decomposition Map）」：表格和圖，說明每個 K8s Deployment/Service 歸屬哪個 BC、其 Owning Schema、對外 API Prefix、Event Topics。(2) 新增 §4.X「單一子系統啟動（Single Subsystem Startup）」：說明如何只啟動單個 BC（例如 `make k8s-apply-wallet`），對應 `k8s/overlays/local-{subsystem}/` 的 Kustomize overlay 結構；其他子系統以 WireMock/msw stub 取代。(3) §6 Development Commands 新增每個子系統的 make target（`k8s-apply-{subsystem}`、`health-check-{subsystem}`、`logs-{subsystem}`）。(4) §14 Mock Services 新增「內部子系統 Stub」子節：當進行單一子系統開發時，如何用 WireMock 模擬其他子系統的 Public API。 |
| **目標檔案** | `templates/LOCAL_DEPLOY.md`（§2.X 新增、§4.X 新增、§6 補充、§14 補充） |
| **影響範圍** | `templates/LOCAL_DEPLOY.md` |
| **決策** | |

---

共 37 項修改（M-01 至 M-37），跨 25+ 個檔案。

**M-28～M-37 修改優先順序建議（依依賴關係）**：
1. M-28、M-29、M-30（EDD 三件套）— 最上游，其他文件依賴 EDD 的 BC 定義
2. M-31（ARCH 三件套）— 依賴 EDD BC Map
3. M-32（SCHEMA 兩件）— 依賴 EDD §3.4 Schema Ownership
4. M-33（API.md）— 依賴 ARCH §4 服務邊界
5. M-34（BRD.md）— 業務層定義，可與 M-28 並行
6. M-35（test-plan.md）— 依賴 EDD Domain Event + ARCH 邊界
7. M-36（runbook.md）— 依賴 ARCH §4 + EDD §3.4
8. M-37（LOCAL_DEPLOY.md）— 依賴 ARCH §4 + Subsystem Boundary Reference

*版本：2026-05-02 v6（新增 M-28～M-37：Spring Modulith 微服務可拆解性 — 五條硬約束寫入 EDD/ARCH/SCHEMA/API/BRD/test-plan/runbook/LOCAL_DEPLOY template 層）*
