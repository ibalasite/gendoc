---
doc-type: ARCH
target-path: docs/ARCH.md
reviewer-roles:
  primary: "資深 Solutions Architect（ARCH 審查者）"
  primary-scope: "元件拆解合理性、分層架構清晰度、Mermaid 圖表正確性、依賴方向、擴展性設計"
  secondary: "資深 Backend Engineer"
  secondary-scope: "服務邊界定義、API 設計對齊、資料流正確性、技術實作可行性"
  tertiary: "資深 DevOps Expert"
  tertiary-scope: "部署拓撲、服務發現、負載均衡、監控埋點位置"
quality-bar: "工程師看完 ARCH 文件，能立即畫出系統的部署圖與資料流圖，不需詢問任何架構師。"
upstream-alignment:
  - field: 技術選型一致性
    source: EDD.md §3.3 技術棧總覽
    check: ARCH 元件圖中使用的技術（框架、資料庫、訊息佇列）是否與 EDD §3.3 完全一致
  - field: SLO 設計支撐
    source: EDD.md §SLO/SLI
    check: ARCH 架構選擇（HA 方案、副本數、多 AZ）是否能支撐 EDD 定義的 Availability 和 Latency SLO
  - field: PRD P0 功能覆蓋
    source: PRD.md §功能清單
    check: ARCH 中是否所有 PRD P0 功能模組都有對應的系統元件或服務
---

# ARCH Review Items

本檔案定義 `docs/ARCH.md` 的審查標準。由 `/reviewdoc ARCH` 讀取並遵循。
審查角色：三角聯合審查（資深 Solutions Architect + 資深 Backend Engineer + 資深 DevOps Expert）
審查標準：「假設公司聘請一位 15 年系統架構資深顧問，以最嚴格的業界標準進行 ARCH 驗收審查。」

---

## Review Items

### Layer 1: 元件定義完整性（由 Solutions Architect 主審，共 5 項）

#### [CRITICAL] 1 — C4 Level 1（System Context）缺失
**Check**: ARCH 是否包含 C4 Level 1 System Context 圖，清楚展示本系統的邊界、外部用戶（Actor）、外部系統（External System）、各關係的通訊方式？缺失 Level 1 無法理解系統邊界。
**Risk**: 無 System Context 圖，利害關係人和新加入工程師無法快速理解系統的外部依賴和用戶角色，需要閱讀大量文件才能建立全局觀。
**Fix**: 補充 C4 Level 1 圖（Mermaid C4Context 或 graph TB），標注：系統名稱、外部用戶（Actor）、外部系統（External System）、各關係的通訊方式（HTTPS / gRPC / AMQP）。

#### [CRITICAL] 2 — C4 Level 2（Container）缺失
**Check**: ARCH 是否包含 C4 Level 2 Container Diagram，展示應用程式、資料庫、Message Queue、Cache 等 Container 及其通訊關係？每個 Container 是否標注技術（如 Spring Boot / PostgreSQL / Redis）和通訊協定與端口？
**Risk**: 無 Container Diagram，DevOps 工程師不清楚需要部署哪些容器、使用什麼技術、彼此如何通訊，IaC（Terraform / Helm Chart）無從下手。
**Fix**: 補充 C4 Level 2 圖，為每個 Container 標注：名稱、技術選型（與 EDD §3.3 一致）、通訊協定（HTTP/gRPC/AMQP）、端口。

#### [HIGH] 3 — EDD 元件與 ARCH 不一致
**Check**: ARCH 中的系統元件（Services / Containers / Databases）是否與 EDD Container 圖完全一致？ARCH 新增或遺漏的元件是否有說明原因？對照 EDD §2.2 逐一核查。
**Risk**: ARCH 與 EDD 元件不一致，工程師在兩份文件之間產生混淆，不知道哪份是最終設計依據，可能造成實作偏差。
**Fix**: 對照 EDD Container 圖逐一核對 ARCH 元件清單；補充說明新增或刪除元件的原因；若 ARCH 為更新版本，需同步更新 EDD 並記錄在 Change Log。

#### [HIGH] 4 — 元件職責未清楚定義
**Check**: ARCH 中每個主要元件（Service / Module）是否有明確的單一職責說明（Single Responsibility）？是否有元件的職責描述包含多個業務域，或職責說明使用「負責處理所有 XX 相關」等模糊表述？
**Risk**: 元件職責不清，服務邊界模糊，功能在開發過程中持續滑向錯誤的模組，造成架構腐化。
**Fix**: 為每個主要元件補充一句明確的職責說明（格式：「XX Service 負責 YY 業務邏輯，不包含 ZZ」）；若有職責重疊，明確劃定邊界。

#### [MEDIUM] 5 — C4 Level 3（Component）若存在必正確
**Check**: 若 ARCH 包含 C4 Level 3 Component Diagram，元件間的依賴關係是否與 EDD 模組介面定義一致？依賴箭頭方向是否遵循架構分層規則（不可由低層指向高層）？
**Risk**: Level 3 與 EDD 不一致，或違反分層規則，文件矛盾導致工程師不確定哪份為準，架構師意圖在實作中被誤解。
**Fix**: 對照 EDD 模組介面修正 Level 3 Component Diagram；確保依賴方向遵循 ARCH §2 選定的架構模式規則；或明確說明「以 EDD 模組設計為準」。

---

### Layer 2: Mermaid 圖表品質（由 Solutions Architect + DevOps Expert 聯合審查，共 5 項）

#### [CRITICAL] 6 — 關鍵基礎設施元件缺失於圖表
**Check**: ARCH 圖表中是否展示所有實際使用的基礎設施元件？必含元件清單（若系統使用）：Load Balancer、API Gateway、Application Server(s)、Database Primary + Replica、Cache（Redis）、Message Queue（若有）、CDN（若有靜態資源）。缺少任一已使用的元件視為 CRITICAL。
**Risk**: 關鍵元件未在 ARCH 中呈現，DevOps 工程師建立 Infrastructure 時遺漏元件，上線前才發現需要緊急補充，延誤交付。
**Fix**: 對照系統所有使用的中間件和基礎設施服務，逐一確認是否出現在 ARCH 圖中；補充缺失元件及其連接關係和配置說明。

#### [HIGH] 7 — 圖表箭頭無方向或含義標注
**Check**: ARCH 圖表中每條連線是否都有：箭頭方向（→ 表示呼叫方向）、操作類型標注（如 HTTPS、gRPC、READ/WRITE、PUBLISH/SUBSCRIBE）？無方向標注的雙向線段視為 HIGH。
**Risk**: 資料流向不清，工程師不確定各元件的讀寫責任，容易設計出競態條件或資料不一致；也無法判斷哪些連線是同步呼叫、哪些是非同步事件。
**Fix**: 為每條元件間連線補充：方向箭頭 + 操作類型（HTTP GET/POST / gRPC / PUBLISH TOPIC_NAME / SUBSCRIBE）+ 傳輸的資料描述（選填）。

#### [HIGH] 8 — Mermaid 語法錯誤
**Check**: ARCH 中的 Mermaid 程式碼塊是否語法正確？常見錯誤：缺少 graph 類型宣告、subgraph 缺少 end、節點 ID 含保留字、箭頭語法不符（`-->` vs `-->`）。列出所有疑似語法錯誤位置。
**Risk**: Mermaid 語法錯誤無法渲染，GitHub / GitLab / Confluence 中顯示原始碼而非圖表，ARCH 文件喪失視覺溝通效果。
**Fix**: 逐一修正語法錯誤；建議加入 CI 步驟使用 `mmdc` 驗證 Mermaid 語法，防止後續引入新錯誤。

#### [MEDIUM] 9 — 網路分區（Subnet / VPC）未在圖中標注
**Check**: 各元件所在的網路區域（Public Subnet / Private Subnet / DMZ）是否在 ARCH 圖中以視覺邊框或標注呈現？資料庫和內部服務是否在 Private Subnet 中？
**Risk**: 網路分區未定義，Security Group 和 Firewall 規則無從制定，資料庫可能被誤配置為公開存取，造成安全風險。
**Fix**: 在 ARCH 圖中以 subgraph 邊框或顏色標注網路區域（Public / Private Subnet / DMZ），說明各區域的存取控制原則（如 DB 僅允許 App Server 存取）。

#### [MEDIUM] 10 — CDN / 靜態資源架構缺失
**Check**: 若系統有靜態資源（前端 Build、圖片、影片），CDN 的架構（Origin、快取策略、Invalidation 策略）是否在 ARCH 中呈現？
**Risk**: CDN 架構未呈現，DevOps 配置時遺漏 CDN 設定，靜態資源直接由應用伺服器提供，效能和成本受影響，且 Cache Invalidation 無設計依據。
**Fix**: 在 ARCH 圖中補充 CDN 節點（如 CloudFront / Cloudflare），標注 Origin（S3 Bucket / Application Server）、快取策略（TTL）、以及 Invalidation 觸發條件。

---

### Layer 3: 分層架構與依賴方向（由 Backend Engineer 主審，共 4 項）

#### [HIGH] 11 — 服務間通訊模式未定義
**Check**: ARCH §5 通訊模式是否明確說明同步 vs. 非同步通訊的選用原則？是否有同步/非同步通訊矩陣（哪些操作用 REST/gRPC，哪些用 Message Queue）？完全缺少通訊模式說明視為 HIGH。
**Risk**: 通訊模式不統一，部分開發者選用同步呼叫、部分選用事件，造成分散式事務問題、重複消費、或超時雪崩效應。
**Fix**: 補充通訊模式章節：同步/非同步選用原則（如：即時查詢用 REST，高延遲操作用 Queue）+ 通訊矩陣（Service A → Service B：協定 / 同步非同步）。

#### [CRITICAL] 12 — 高可用（HA）設計違反 Min Replicas ≥ 2 原則
**Check**: ARCH §7 高可用設計中，是否有任何元件的 Min Replicas < 2？具體驗證：(1) API Server / Worker 的 minReplicas 是否 ≥ 2；(2) DB 是否為 Primary+Standby（非單節點）；(3) Redis 是否為 Sentinel 3 nodes 或 Cluster（非 standalone）；(4) 是否有任何配置標注 `replicas: 1` 或 `minReplicas: 1`。任一元件 Min Replicas < 2 視為 CRITICAL。
**Risk**: Min Replicas < 2 = SPOF = 任何一個 Pod/節點故障即導致服務中斷。HA 架構的程式碼設計（分散式鎖、Session 外置、Pub/Sub）依賴 ≥ 2 副本才能被真實測試，單副本環境通過測試不代表 HA 功能正確。
**Fix**: 逐一審查 §7 中所有元件的副本配置，將所有 replicas < 2 的配置升至 2；更新 §10.2 Phase 1 欄位確認 HA 基線已包含所有元件的最小副本要求；同步更新 LOCAL_DEPLOY 和 runbook 中的對應配置。

#### [HIGH] 13 — 資料一致性策略缺失
**Check**: 若系統存在多個服務或非同步操作，ARCH 是否說明分散式場景下的資料一致性策略（Eventual Consistency / Saga / Outbox Pattern）？以及事務邊界如何劃定？完全未提及視為 HIGH。
**Risk**: 資料一致性策略缺失，跨服務事務失敗後無補償機制，造成資料孤兒、雙重扣款、狀態不一致等業務問題。
**Fix**: 補充資料一致性章節：說明系統選用的一致性模型（Strong / Eventual）+ 跨服務事務的處理策略（Saga Choreography / Orchestration / Outbox Pattern）+ 失敗補償機制。

#### [HIGH] 14 — 架構演進路徑違反 HA 基線原則
**Check**: ARCH §10.2 Phase 演進路徑是否以 HA 基線為起點？具體驗證：(1) Phase 1 是否已標注「API ≥ 2 replica + DB Primary+Standby + Redis Sentinel」；(2) Phase 1 是否出現「Modular Monolith」「單一 DB」「single pod」等暗示 SPOF 的描述；(3) 演進觸發條件是否以「並發/QPS」為單位而非「用戶數規模」作為架構切換依據。若 Phase 1 描述包含單體或單副本架構，視為 HIGH（下游 LOCAL_DEPLOY/runbook 可能據此生成 SPOF 配置）。
**Risk**: Phase 1 允許 SPOF，工程師依此文件部署後可能在 Day 1 即產生單點故障；HA 程式碼（分散式鎖、Session 外置、Pub/Sub）無法在 Phase 1 被測試，上線後切換 HA 需要大規模重構。
**Fix**: 依照 M-03 修改方向更新 §10.2：移除「Phase 1 單體/單副本」描述，改為「Phase 1 HA 基線（啟動即 ≥ 2 replica）」；演進觸發條件從「規模大小」改為「QPS/並發閾值」；加入 Iron Constraint 注解「架構從 Day 1 採 HA，Phase 差別只在水平擴展程度」。

---

### Layer 4: 外部依賴與整合（由 Solutions Architect + Backend Engineer 聯合審查，共 3 項）

#### [HIGH] 15 — 外部依賴 SLA 和降級未評估
**Check**: ARCH §13 外部依賴地圖是否列出所有第三方服務（Payment Gateway / SMS Provider / Email Service / Map API 等）的 SLA、降級方案、以及對系統整體 SLO 的影響評估？完全未列出外部依賴視為 HIGH。
**Risk**: 外部依賴 SLA 未評估，第三方服務故障時系統無降級預案，直接影響 SLO；也無法告知業務方在外部服務不可用時的用戶體驗。
**Fix**: 補充外部依賴清單（服務名 / 用途 / SLA / 降級方案 / 影響範圍），說明每個關鍵外部依賴不可用時的系統行為（Fallback 內容 / 功能暫停 / Queue 積壓）。

#### [HIGH] 16 — API Gateway / Service Mesh 配置未說明
**Check**: ARCH §5.2 是否說明 API Gateway 或 Service Mesh 的配置（認證邊界、Rate Limiting 位置、流量路由規則、TLS termination 位置）？若系統使用 API Gateway 但未說明其責任邊界視為 HIGH。
**Risk**: API Gateway 配置未說明，不同工程師對「認證在哪做」「Rate Limiting 在哪做」有不同假設，造成重複實作或漏洞。
**Fix**: 補充 API Gateway / Service Mesh 章節：責任邊界（Auth / Rate Limit / Routing / TLS termination 各在哪層處理）+ 路由規則概覽 + 內部服務間通訊加密策略。

#### [MEDIUM] 17 — 技術棧全覽與 EDD 不一致
**Check**: ARCH §11 技術棧全覽中的所有技術和版本是否與 EDD §3.3 技術棧總覽完全一致？逐一比對技術名稱和版本號，列出不一致的項目。
**Risk**: ARCH 與 EDD 技術棧不一致，兩份文件給出矛盾的技術信息，工程師無法確認哪份為最終依據，造成環境建置偏差。
**Fix**: 以 EDD §3.3 技術棧總覽為權威來源，同步修正 ARCH §11 中所有不一致的技術名稱和版本號；未來更新技術版本時兩份文件需同步更新。

---

### Layer 5: 上游對齊（由 Solutions Architect 通盤審查，共 5 項）

#### [CRITICAL] 18 — EDD SLO 無法被 ARCH 架構支撐
**Check**: ARCH 的架構選擇（副本數、HA 方案、多 AZ / 多 Region 設計）是否能支撐 EDD 定義的 Availability SLO？若 EDD 定義 99.9% 可用性但 ARCH 是單副本部署，視為 CRITICAL。
**Risk**: ARCH 架構無法支撐 EDD SLO，系統上線後 Availability 持續不達標，SLA 違約，但工程師無法在架構文件中找到問題根因。
**Fix**: 對照 EDD SLO 數字重新評估 ARCH 架構決策；補充說明每個 SLO 是如何被架構設計支撐的（如「99.9% Availability 通過 3 副本 + Multi-AZ DB 實現」）。

#### [HIGH] 19 — PRD P0 功能模組在 ARCH 中缺少對應元件
**Check**: 對照 PRD §功能清單，每個 P0 功能模組（如「訂單管理」「用戶認證」「通知推送」）是否都能在 ARCH 圖中找到對應的 Service / Module / Component？列出缺少對應元件的 P0 功能。
**Risk**: P0 功能的架構元件缺失，工程師在設計時缺少對應模組，功能被塞入不合適的 Service，造成職責混亂和架構腐化。
**Fix**: 為每個缺少對應的 P0 功能補充架構元件（Service / Module），說明其在 ARCH 圖中的位置和職責。

#### [HIGH] 20 — ADR 索引與完整 ADR 不一致
**Check**: ARCH §1.2 ADR 索引中列出的所有決策是否在 §14 完整 ADR 章節中都有對應的詳細記錄（背景 / 選項比較 / 決策 / 後果）？索引有但 §14 缺少詳細內容視為 HIGH。
**Risk**: ADR 索引與詳細記錄不一致，架構師無法查閱決策的完整推理過程，後繼者重複進行已決定的討論，浪費時間。
**Fix**: 為 §1.2 每個 ADR 索引項目在 §14 補充完整的 ADR 記錄（Context / Considered Options / Decision / Consequences）。

#### [MEDIUM] 21 — 架構審查檢查清單未完成
**Check**: ARCH §15 架構審查檢查清單是否存在？清單項目是否都已勾選（✅ 或 ❌ 含說明）？若清單存在但全為空白（未勾選）視為 MEDIUM；若清單完全缺失視為 MEDIUM。
**Risk**: 架構審查清單未完成，無法確認架構師是否自我驗證了關鍵架構決策，可能有已知問題未被記錄。
**Fix**: 完善 §15 審查清單，逐一勾選並說明：可用性設計是否符合 SLO、安全設計是否通過內部審查、DR 策略是否已評估等。

#### [MEDIUM] 22 — FinOps 成本估算完整性

**Check**: ARCH.md 是否包含 §FinOps 或 §成本估算章節，且章節內容是否包含：
- 主要雲端資源的月費估算（運算、存儲、網路、AI API 費用）
- 不同規模下的成本預測（小規模 / 中規模 / 大規模）
- 成本優化建議（如：自動縮放、Reserved Instance、Spot Instance 使用時機）

**Risk**: 缺乏成本估算的架構文件導致工程團隊無法評估方案可行性，可能在實作後才發現成本超出預算。

**Fix**: 在 ARCH.md 補充 §FinOps 章節，要求使用 state.q4_scale 對應的規模提供具體費用估算（數字非 TBD/N/A）。

---

### Layer 6: 文件完整性（由 DevOps Expert 通盤審查，共 2 項）

#### [HIGH] 23 — Observability 架構埋點位置未標注
**Check**: ARCH §12 Observability 架構是否說明 Metrics、Logging、Tracing 的工具選型，以及各類監控資料的採集位置（在哪個元件埋點）？是否有 Alert 閾值與 EDD SLO 的對應說明？
**Risk**: Observability 埋點位置未說明，各工程師各自決定在哪裡記錄 Metrics 和 Log，造成監控覆蓋不一致，無法從 ARCH 層面保障 SLO 可觀測性。
**Fix**: 補充 Observability 架構說明：工具選型（Prometheus / Grafana / Jaeger / ELK）+ 各元件的埋點類型（哪個 Service 暴露哪些 Metrics）+ Alert 規則與 EDD SLO 的對應。

#### [LOW] 24 — 裸 Placeholder 殘留
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換的空白佔位符（元件名稱、域名、IP CIDR、SLA 數字等）？逐一列出位置（章節）。
**Risk**: 裸 placeholder 使 ARCH 文件無法直接用於 Infrastructure 配置或架構溝通，DevOps 工程師需要人工詢問架構師填寫缺漏值，降低文件可信度。
**Fix**: 替換所有裸 placeholder 為真實值（域名 / IP CIDR / 元件名稱）；若部署細節尚未確定，改為 `（待確認：描述說明）` 格式。
