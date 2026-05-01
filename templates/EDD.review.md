---
doc-type: EDD
target-path: docs/EDD.md
reviewer-roles:
  primary: "資深 Software Architect（EDD 審查者）"
  primary-scope: "系統架構設計、技術選型合理性、安全設計完整性、效能設計、SLO/SLI 定義、DR 設計"
  secondary: "資深 DevOps/SRE Expert"
  secondary-scope: "部署架構、可觀測性設計、擴展性策略、K8s 資源規格、CI/CD pipeline"
  tertiary: "資深 Security Expert"
  tertiary-scope: "認證授權設計、資料保護、Secret 管理、OWASP 威脅覆蓋"
quality-bar: "資深工程師拿到 EDD 後，無需任何補充資訊，即能開始實作所有核心模組、撰寫 API 規格、設計 DB Schema，且不會與任何 PRD 需求衝突。"
upstream-alignment:
  - field: PRD P0 功能覆蓋
    source: PRD.md §功能清單
    check: EDD 中每個 PRD P0 功能是否有對應的模組設計／Service／Use Case
  - field: BRD 效能需求
    source: BRD.md §非功能需求
    check: EDD §SLO/SLI 數字是否對應 BRD 的業務指標（TPS、Latency、Availability）
  - field: PDD 互動設計
    source: PDD.md §畫面清單（若存在）
    check: EDD API 設計是否支撐 PDD 每個 P0 畫面所需的資料操作
  - field: BRD 安全需求
    source: BRD.md §合規與安全
    check: EDD §安全設計是否覆蓋 BRD 明確要求的安全標準（GDPR / PCI-DSS / SOC2 等）
---

# EDD Review Items

本檔案定義 `docs/EDD.md` 的審查標準。由 `/reviewdoc EDD` 讀取並遵循。
審查角色：三角聯合審查（資深 Software Architect + 資深 DevOps/SRE Expert + 資深 Security Expert）
審查標準：「假設公司聘請一位 15 年後端架構資深顧問，以最嚴格的業界標準進行 EDD 驗收審查。」

---

## Review Items

### Layer 1: 架構設計完整性（由 Software Architect 主審，共 5 項）

#### [CRITICAL] 1 — 架構分層缺失或違規
**Check**: EDD 是否明確定義架構分層（Layered / Hexagonal / Clean Architecture）？是否有跨層直接依賴（如 Domain 層直接呼叫 Infrastructure 層）？列出所有違規依賴方向。
**Risk**: 架構分層不清，業務邏輯與技術細節耦合，後期更換資料庫或 Framework 需要大規模重構，技術債持續累積。
**Fix**: 重新定義分層說明（Presentation → Application → Domain → Infrastructure），以箭頭圖標注依賴方向，刪除所有跨層直接呼叫並改為注入介面。

#### [CRITICAL] 2 — PRD P0 功能未在 EDD 中對應
**Check**: 對照 PRD §功能清單，EDD 中每個 P0 功能（User Story / AC）是否都有對應的模組設計、Service 方法、或 Use Case 章節？列出所有缺少對應的 P0 功能。
**Risk**: P0 功能的技術設計缺失，工程師在 Sprint 中無設計依據自行決定實作方式，造成不一致並超出交付時程。
**Fix**: 為每個缺少對應的 P0 功能新增設計章節，明確說明涉及的模組、Service 方法、資料操作。

#### [HIGH] 3 — 模組介面定義不完整
**Check**: 每個核心模組（Service / Use Case）是否有公開方法的介面定義（方法名稱、參數型別、回傳型別）？僅有模組名稱無方法簽名視為 HIGH。
**Risk**: 介面未定義，前後端或微服務間整合時需口頭協商，造成整合期反覆修改，延誤交付。
**Fix**: 為每個核心模組補充介面定義（pseudocode 或目標語言格式），至少覆蓋 Public 方法，含參數與回傳型別。

#### [HIGH] 4 — 技術選型決策（ADR）缺乏理由
**Check**: EDD §3.2 技術選型決策（ADR）是否為每個關鍵選型（資料庫、框架、訊息佇列、認證方式）提供：背景說明、選項比較（至少 2 個選項）、最終決策理由、後果說明？僅有選型結果無理由視為 HIGH。
**Risk**: 決策理由缺失，未來架構師或新成員無法評估變更成本，容易在不了解 trade-off 的情況下做出破壞架構的決策。
**Fix**: 補充每個 ADR 的背景、選項比較（優/劣）、決策理由和後果；若選型已確定，至少補充「排除 XXX 的原因」。

#### [MEDIUM] 5 — Mermaid 系統架構圖缺失
**Check**: EDD 是否包含 §2.1 System Context 圖（C4 Level 1）和 §2.2 Container 圖（C4 Level 2）？圖中所有節點是否與文字描述一致？
**Risk**: 無架構圖，工程師只能閱讀文字推斷系統結構，溝通成本高且容易產生不同解讀。
**Fix**: 補充 Mermaid System Context 圖和 Container 圖；確保圖中的服務、資料庫、外部系統與 §3.3 技術棧描述完全一致。

#### [CRITICAL] 5b — UML 9 大圖缺失或不完整
**Check**: EDD §4.5（UML 9 大圖）是否包含全部 9 種 UML 圖？逐一確認（⚠️ EDD 的 UML 圖集在 §4.5，§4.6 是 Domain Events，§10 是 Observability Design）：
(1) Use Case Diagram（§4.5.1 或等效段落）：是否有 Mermaid 程式碼塊，涵蓋所有主要 Actor？
(2) Class Diagram（§4.5.2 或等效段落）：是否有 classDiagram 程式碼塊，按架構層次分張（Domain/Application/Infrastructure/Presentation）？每個 class 是否標注 stereotype 和可見性？每個 public method 是否列出回傳型別？6 種關聯關係（Inheritance/Realization/Composition/Aggregation/Association/Dependency）是否各至少出現 1 次？
(3) Object Diagram（§4.5.3 或等效段落）：是否有物件實例快照（欄位含真實範例值）？
(4) Sequence Diagram（§4.5.4 或等效段落）：是否有每個主要業務流程的循序圖（含 Happy Path 和 Error Path）？**至少 3 張各自獨立**？
(5) Communication Diagram（§4.5.5 或等效段落）：是否有物件協作關係圖（訊息標注序號）？
(6) State Machine Diagram（§4.5.6 或等效段落）：是否有每個有狀態 Entity 的狀態機圖？每個 `stateDiagram-v2` 的 transition label 是否不含 `<br/>`（含則視為 CRITICAL，Safari/Firefox 破圖）？
(7) Activity Diagram（§4.5.7 或等效段落）：是否有每個主要業務流程的活動圖（含決策點）？**至少 3 張**？
(8) Component Diagram（§4.5.8 或等效段落）：是否有元件依賴圖？
(9) Deployment Diagram（§4.5.9 或等效段落）：是否有部署拓撲圖？
**Risk**: UML 圖缺失使工程師只能讀文字推斷系統結構，無法基於圖示進行精確實作，不同工程師對同一系統的理解會出現分歧，導致實作偏差。Class Diagram 缺失更直接導致無法推導 unit test skeleton，測試覆蓋率無從保證。
**Fix**: 為每種缺失的 UML 圖補充對應的 Mermaid 程式碼塊至 §4.5（参考 `templates/UML-CLASS-GUIDE.md` 範例）。Class Diagram 必須嚴格遵循 Clean Architecture 分層，所有 class 必須標注 stereotype，方法必須含回傳型別。多圖原則：每個主要業務流程一張 Sequence Diagram（≥ 3 張），每個有狀態 Entity 一張 State Machine，每個 P0 User Story 一張 Activity Diagram（≥ 3 張）。

#### [CRITICAL] 5b-sm — State Machine Diagram 使用 `<br/>` 語法
**Check**: EDD §4.5.6 的所有 `stateDiagram-v2` 程式碼塊中，是否有任何 transition label 包含 `<br/>`？掃描方式：搜尋每個 `stateDiagram-v2` 區塊內的 `-->` 行，確認無 `<br/>` 出現。
**Risk**: `stateDiagram-v2` 不支援 transition label 中的 `<br/>`，Safari 和 Firefox 會渲染空白或破圖，導致狀態機圖在非 Chrome 瀏覽器完全不可見，影響開發者理解系統狀態流程。
**Fix**: 將 transition label 精簡為 `trigger [guard] / action` 單行格式（如 `shoot [coins >= cost] / deductCoins + createBullet`），多行說明移到對應狀態旁的 `note right of STATE` 區塊。

#### [CRITICAL] 5c — Class Diagram class inventory 缺失
**Check**: EDD §4.5.2 的 Class Diagram 段落之後是否提供 Class Inventory 表格（列出所有 class 名稱、stereotype、架構層次、推斷的 src 路徑、推斷的 test 路徑）？缺少 Class Inventory 表格視為 CRITICAL。
**Risk**: 無 Class Inventory，test-plan 撰寫者必須人工掃描 classDiagram 程式碼塊提取 class 清單，容易遺漏，導致部分 class 完全沒有 unit test 覆蓋，在驗收時才被發現。
**Fix**: 在 §4.5.2 Class Diagram 程式碼塊之後，加入 Class Inventory 表格（格式見 templates/UML-CLASS-GUIDE.md §3）。表格必須覆蓋所有出現在 classDiagram 中的 class。

---

### Layer 2: 技術選型與棧完整性（由 Software Architect 主審，共 4 項）

#### [CRITICAL] 6 — 技術棧總覽含裸 Placeholder
**Check**: EDD §3.3 技術棧總覽表格中是否有任何 `{{PLACEHOLDER}}` 格式的未替換值？後端語言、框架、資料庫、ORM、認證函式庫的名稱和版本是否都已填寫具體內容？逐一列出裸 placeholder 位置。
**Risk**: 技術棧未確定，工程師無法開始環境建置，Sprint 1 無法啟動，下游 ARCH / SCHEMA 文件也無法對齊。
**Fix**: 依 BRD / PRD 的業務需求推斷並填入具體技術名稱 + 版本；若尚未決定，標注「（待確認：評估中）」而非保留裸 placeholder。

#### [HIGH] 7 — 架構模式與業務規模不匹配
**Check**: EDD §3.1 選用的架構模式（Monolith / Microservices / Modular Monolith / Event-Driven）是否與 PRD 的業務規模和 BRD 的擴展性需求匹配？是否說明了選用理由和未選擇替代方案的原因？
**Risk**: 架構模式過重（如小型系統用微服務）或過輕（如高流量場景用單體），造成開發效率低下或系統瓶頸。
**Fix**: 補充選型理由（考量因素：團隊規模、業務邊界清晰度、流量規模、SLA 差異）；若決策已定，至少補充「排除微服務的理由：...」類說明。

#### [HIGH] 8 — 部署環境規格矩陣不完整
**Check**: EDD §3.5 部署環境規格（Environment Matrix）是否涵蓋 Local / Development / Staging / Production 四個環境？每個環境的 K8s Namespace、副本數、CPU/Memory Request/Limit、DB Host 是否都有具體值？
**Risk**: 環境規格缺失，DevOps 工程師無法建立 IaC 配置，各環境資源設定不一致，Staging 無法真實模擬 Production 行為。
**Fix**: 補充缺失的環境欄位；Production 資源規格依 SLO 估算並填入；Secret 路徑使用 Secret Manager 路徑替代明文。

#### [MEDIUM] 9 — DDD Bounded Context 未定義
**Check**: 若系統涉及多個業務域，EDD §3.4 是否定義了 Bounded Context 邊界和 Context Map（上下游關係、整合模式）？未定義 Bounded Context 但系統有明顯多業務域劃分視為 MEDIUM。
**Risk**: Bounded Context 未定義，服務邊界不清，各團隊各自擴展 Domain Model，造成跨域資料耦合，後期難以拆分。
**Fix**: 補充 Bounded Context 圖（Mermaid），標注各 BC 的邊界、上下游關係（Customer/Supplier / Conformist / ACL），並說明跨域呼叫方式。

---

### Layer 3: API 與資料設計佔位符驗證（由 Software Architect 主審，共 3 項）

#### [HIGH] 10 — API 設計章節缺少 Endpoint 結構
**Check**: EDD 是否有 API 設計章節（§5 或同等章節）說明 API 的基本結構（Base URL、版本策略、認證方式、請求/回應格式）？若 API 設計完全委派給 API.md 但 EDD 未提供任何 Endpoint 結構說明，視為 HIGH。
**Risk**: API 結構說明缺失，下游 API.md 撰寫者沒有設計依據，各 Endpoint 格式不一致，前後端整合困難。
**Fix**: 補充 API 設計概覽（Base URL pattern、版本策略 /v1/、認證方式、統一回應格式、錯誤碼規範）；具體 Endpoint 可委派給 API.md 但概覽必須在 EDD 中。

#### [HIGH] 11 — 資料模型（ER Diagram / Schema）缺失
**Check**: EDD 是否包含核心資料模型（ER Diagram 或等效描述）？資料模型是否涵蓋 PRD P0 功能所需的所有核心實體（Entity）和關係？是否說明了 Indexing 策略？
**Risk**: 無資料模型，SCHEMA.md 撰寫者無設計依據，資料庫設計與業務需求不一致，後期 migration 成本高。
**Fix**: 補充核心 ER Diagram（Mermaid erDiagram），至少涵蓋 PRD P0 功能的主要 Entity，並說明主要 Index 設計依據（查詢模式）。

#### [MEDIUM] 12 — 錯誤處理與降級策略未定義
**Check**: EDD 是否說明系統的錯誤處理策略（錯誤碼規範、Retry 策略、Circuit Breaker）和降級方案（當外部服務不可用時的行為）？完全未提及降級策略視為 MEDIUM。
**Risk**: 降級策略缺失，外部依賴不可用時系統整體崩潰，而非優雅降級，影響 SLO 達成率。
**Fix**: 補充錯誤處理章節：統一錯誤碼表、重要路徑的 Retry 策略（最大次數、backoff）、外部依賴降級方案（Fallback 內容 / Cache / 功能暫停）。

---

### Layer 4: 安全設計（由 Security Expert 主審，共 4 項）

#### [CRITICAL] 13 — 認證授權設計不明確
**Check**: EDD 是否明確定義：認證方式（JWT / Session / OAuth2 / mTLS）、Token 生命週期（Access Token TTL、Refresh Token TTL）、角色權限矩陣（Role × Permission × Endpoint）？三者缺一視為 CRITICAL。
**Risk**: Auth 設計不明確，前後端各自假設認證流程，整合時出現 Token 格式不符、權限判斷位置不一致，或 Token 無限期有效等安全漏洞。
**Fix**: 補充認證設計章節：認證方式 + Token 格式、Access Token TTL（如 15min）+ Refresh Token TTL（如 7 days）、角色權限矩陣（每個角色可執行的 Endpoint 操作）。

#### [CRITICAL] 14 — OWASP Top 10 未覆蓋
**Check**: EDD 是否對 OWASP A01–A10 逐項說明緩解措施？完全未提及 OWASP 視為 CRITICAL；僅有部分覆蓋但缺少 A01（存取控制）或 A03（注入）視為 HIGH。
**Risk**: 未對照 OWASP 設計安全措施，系統上線後面臨注入攻擊、認證繞過、敏感資料曝露等常見漏洞，法律合規風險高。
**Fix**: 補充 OWASP Top 10 緩解措施表格（A01 存取控制 / A02 加密失敗 / A03 注入 / A04 不安全設計 / A05 錯誤配置 / A06 易受攻擊元件 / A07 身份認證失敗 / A08 完整性失敗 / A09 日誌監控不足 / A10 SSRF），逐項說明本系統的對應設計。

#### [HIGH] 15 — Secret 管理方案不具體
**Check**: EDD 是否明確說明 Secret 的儲存方案（Vault / K8s Secret / AWS Secrets Manager）、Secret 分類（DB Credentials / API Keys / Certificates）、Rotation 策略？僅說明「使用環境變數」視為 HIGH（不夠具體）；任何明文 Secret 視為 CRITICAL。
**Risk**: Secret 管理方案不具體，DevOps 工程師各自選用不同工具，Secret 分散在多個位置，Rotation 和 Audit 困難；明文 Secret 進入文件版本控制永久記錄。
**Fix**: 補充 Secret 管理設計：使用工具 + Secret 路徑前綴 + 分類列表 + Rotation 週期；移除所有明文 Secret，替換為 Secret Manager 路徑佔位符（如 `arn:aws:secretsmanager:.../db-password`）。

#### [MEDIUM] 16 — Rate Limiting 設計缺失
**Check**: EDD 是否說明 API Rate Limiting 策略（限制維度：IP / User / API Key；限制數值：N req/min；觸發後行為：429 + Retry-After Header）？完全未提及 Rate Limiting 視為 MEDIUM。
**Risk**: 無 Rate Limiting 設計，API 易受暴力破解和 DoS 攻擊，也無法保護下游付費 API 免受濫用，成本失控。
**Fix**: 補充 Rate Limiting 設計：限制範圍（IP/User/API Key）、各類端點限制數值（如 Auth: 5 req/min / General: 100 req/min）、超限後回應格式（429 + Retry-After Header）。

---

### Layer 5: 效能與可靠性（由 DevOps/SRE Expert 主審，共 5 項）

#### [CRITICAL] 17 — SLO/SLI 數字缺失或泛化
**Check**: EDD 是否定義了可量化的 SLO（Availability %、P95/P99 Latency ms、Error Rate %）？泛化描述（「高可用」「快速回應」）視為 CRITICAL；有數字但與 BRD 業務需求不對齊視為 HIGH。
**Risk**: 無具體 SLO 數字，ARCH、RUNBOOK、Alert 閾值均無設定依據，上線後無法判斷系統是否正常運行，也無法計算 Error Budget。
**Fix**: 補充 SLO/SLI 表格（指標 / 目標值 / 量測方式 / 優先級），至少定義：Availability（如 99.9%）、P99 Latency（如 ≤500ms）、Error Rate（如 <0.1%）；數字需與 BRD 業務需求對齊。

#### [HIGH] 18 — DR 設計（RTO/RPO）缺失
**Check**: EDD 是否定義 RTO（Recovery Time Objective）和 RPO（Recovery Point Objective）具體數值？是否說明 DR 策略（Active-Active / Active-Passive / Backup-Restore）？完全未提及視為 HIGH。
**Risk**: 無 RTO/RPO 定義，DR Drill 無通過標準，真實災難發生時無法判斷恢復進度，也無法向業務方承諾恢復時間。
**Fix**: 補充 DR 設計章節：RTO 目標值（如 ≤4 小時）+ RPO 目標值（如 ≤1 小時）+ DR 策略選擇理由 + Failover 觸發條件。

#### [HIGH] 19 — 可觀測性三柱（Logging / Metrics / Tracing）設計不完整
**Check**: EDD 是否分別說明 Logging 格式（結構化 JSON / 日誌等級策略）、Metrics（暴露 /metrics endpoint、關鍵指標清單）、Distributed Tracing（Trace ID 傳遞方式、Sampling Rate）？缺少任一柱視為 HIGH。
**Risk**: 可觀測性設計不完整，系統上線後發生問題時無法快速定位根因，MTTR 長，SLO 達成率低。
**Fix**: 補充可觀測性設計章節，三柱分別說明：Logging（格式 + 等級 + PII 遮罩策略）、Metrics（工具 + 關鍵指標清單 + Alert 閾值）、Tracing（工具 + Trace ID 傳遞 + Sampling Rate）。

#### [HIGH] 20 — K8s 資源規格（HPA / PDB）未定義
**Check**: EDD §3.5 部署環境規格是否說明 HPA（水平自動擴縮）的觸發條件（CPU/Memory threshold）和 PDB（Pod Disruption Budget）配置？Production 環境的副本數是否為 HPA min-max 範圍而非固定值？
**Risk**: 無 HPA 配置，流量峰值時系統無法自動擴展，手動擴容延遲導致 SLO 違規；無 PDB，滾動更新或節點維護時可能所有 Pod 同時下線。
**Fix**: 在環境規格矩陣中補充 Production HPA 配置（min: N / max: M / CPU threshold: X%）；補充 PDB 設定（minAvailable: N 或 maxUnavailable: N）。

#### [MEDIUM] 21 — CI/CD Pipeline 設計缺失
**Check**: EDD 是否說明 CI/CD Pipeline 的主要階段（Build / Test / Security Scan / Deploy）、各環境的 Deploy 策略（Rolling / Blue-Green / Canary）、以及 Quality Gate 標準（覆蓋率閾值、SAST 通過條件）？
**Risk**: CI/CD 設計缺失，各工程師自行設定 Pipeline，品質標準不一致，安全掃描可能被跳過，生產環境部署風險增加。
**Fix**: 補充 CI/CD 設計章節：Pipeline 階段說明 + 各環境部署策略（dev: rolling / staging: blue-green / prod: canary）+ Quality Gate 條件（覆蓋率 ≥80%、SAST 無 CRITICAL）。

---

### Layer 6: 上游對齊與文件完整性（由 Software Architect 通盤審查，共 3 項）

#### [HIGH] 22 — BRD 效能需求未反映在 SLO
**Check**: 對照 BRD §非功能需求，EDD SLO 中的 Availability、Latency、TPS 數字是否與 BRD 明確要求的業務指標一致？若 BRD 要求「99.9% 可用性」但 EDD SLO 寫「99%」視為 HIGH。
**Risk**: SLO 與 BRD 業務需求不對齊，系統達到「技術 SLO」但未達到「業務承諾」，上線後客戶投訴但工程師不知道哪裡出了問題。
**Fix**: 逐條對照 BRD 效能需求與 EDD SLO，確保每個 BRD 業務指標在 EDD SLO 中有對應且數字一致；若有設計 trade-off 需在 EDD 中明確記錄。

#### [HIGH] 23 — EDD PRD 需求追溯表缺失或不完整
**Check**: EDD §1.3 PRD 需求追溯表是否存在？是否覆蓋 PRD 所有 P0 AC（Acceptance Criteria）？每個 AC 是否有對應的 EDD 章節引用？缺少追溯表或 P0 AC 未追溯視為 HIGH。
**Risk**: 無需求追溯表，Code Review 和驗收時無法快速確認 PRD 需求已被實作設計覆蓋，遺漏項目在 Sprint 末才被發現。
**Fix**: 補充或完善 §1.3 PRD 需求追溯表，確保每個 P0 AC 都有對應的 EDD 章節引用（如 AC-1 → §5.2 POST /orders）。

#### [LOW] 24 — 裸 Placeholder 殘留
**Check**: 是否有 `{{PLACEHOLDER}}` 格式未替換的空白佔位符（技術名稱、端點、數值等）？逐一列出位置（章節）。
**Risk**: 裸 placeholder 殘留，工程師閱讀時無法確認文件完整性，需要人工詢問架構師填寫缺漏內容，降低文件可信度。
**Fix**: 替換所有裸 placeholder 為真實值；若暫時無法確定，改為 `（待確認：描述說明）` 格式並標注負責人。

---

### Layer 5: HA / SPOF / SCALE / BCP 架構規範（由 SRE / Architecture Expert 主審，共 5 項）

#### [CRITICAL] 25 — §3.6 HA/SPOF Architecture Specification 缺失
**Check**: EDD 是否有 §3.6 HA/SPOF/SCALE/BCP Architecture Specification？包含：SPOF 分析表（每個元件 Min Replicas ≥ 2）、HA 設計原則（Stateless API/冪等 Worker/Graceful Shutdown/Circuit Breaker）、SLO/RTO/RPO 具體數字、BCP 故障場景表？完全缺失視為 CRITICAL。
**Risk**: 沒有 §3.6，所有下游文件（ARCH/runbook/test-plan）缺少 HA 設計的權威來源，各文件各自定義（或不定義）HA 需求，導致設計不一致；運維人員在故障時無 BCP 可依循，RTO 延長數倍。
**Fix**: 依照 EDD.md 骨架補充完整 §3.6（含 SPOF 分析表、HA 原則、SLO/RTO/RPO、BCP 場景）；確認 §3.5 環境矩陣的 Local 副本數 ≥ 2。

#### [CRITICAL] 26 — 任何元件 Min Replicas = 1（SPOF 未消除）
**Check**: EDD §3.6.1 SPOF 分析表（或 §3.5 環境矩陣）中，是否有任何核心元件的 Min Replicas = 1？包含 API Server、Worker、DB Primary（無 Standby）、Redis（單節點）。任何核心元件 Min Replicas = 1 視為 CRITICAL。
**Risk**: Min Replicas = 1 意味著單個 Pod/Node 故障會導致服務完全中斷（SPOF），與 HA-First 架構原則直接矛盾；在 K8s rolling update 期間舊 Pod 被刪除、新 Pod 還未 ready 時，服務會有完全停機窗口。
**Fix**: 將所有核心元件的 Min Replicas 改為 ≥ 2；在 SPOF 分析表中記錄每個元件的消除方式（K8s Deployment multi-replica / RDS Multi-AZ / Redis Sentinel）；更新 K8s Deployment YAML 範本。

#### [HIGH] 27 — BCP 場景少於 3 個或缺少 RTO
**Check**: §3.6.4 BCP 場景表是否包含 ≥ 3 個故障場景？每個場景是否有具體 RTO（秒數，非「快速」「盡快」等模糊描述）？缺少場景或 RTO 模糊視為 HIGH。
**Risk**: BCP 場景不完整，運維人員在實際故障時無法按計畫操作，依賴個人經驗（不可靠）；RTO 沒有數字，無法在事後評估是否達成恢復目標。
**Fix**: 補充 BCP 場景至 ≥ 3 個（最少包含：API Pod 崩潰、DB Primary 故障、Redis 主節點故障），每個場景填入 RTO 秒數（來自 §3.6.3）。

#### [CRITICAL] 28 — SLO 中可用性 / RTO / RPO 缺少具體數字
**Check**: §3.6.3（或 §10.5）SLO 表中：Availability 是否有具體百分比（如 99.9%）？RTO 是否有具體秒數？RPO 是否有明確說明（0 = 同步複本，或具體秒數）？若任一為「TBD」「待確認」「越快越好」視為 CRITICAL。
**Risk**: SLO 沒有數字無法被測試覆蓋（test-plan §3.6 的通過條件需要從 SLO 推算）；也無法在故障後判斷是否達成恢復目標；oncall 工程師不知道「多快才算恢復」。
**Fix**: 依 BRD 非功能需求填入具體數字：Availability ≥ 99.9%（= 月度停機 ≤ 43.8 分鐘）、RTO ≤ 30s（API Pod）/ ≤ 30s（DB Failover）、RPO = 0（同步複本 WAL）。

#### [HIGH] 29 — Graceful Shutdown 設計未定義
**Check**: §3.6.5 或 §8 是否有 Graceful Shutdown 設計說明？包含：SIGTERM 處理方式（停止接受新請求）、in-flight 請求最大等待時間（建議 ≤ 30s）、K8s `terminationGracePeriodSeconds` 設定、Readiness Probe 在 SIGTERM 後立即失敗的設計？缺少以上說明視為 HIGH。
**Risk**: 沒有 Graceful Shutdown，每次 Deploy（Canary / Rolling Update）Pod 替換時，正在處理的請求會被強制中斷（502/503）；Scale-down 事件（HPA 縮容）也會中斷 in-flight 請求；test-plan §3.6 @graceful-shutdown 無法通過。
**Fix**: 在 §3.6.5 補充 Graceful Shutdown 流程（5 步驟：SIGTERM → Readiness 失敗 → 等待 in-flight → 正常退出 → K8s 釋放資源），並提供 lang_stack 對應的具體實作示例（Node.js / Java / Python）。

### Layer 6: 最小完整度架構圖（§3.7）（由 Software Architect 主審，共 2 項）

#### [CRITICAL] 30 — §3.7 最小完整度架構圖缺失
**Check**: EDD 是否有 §3.7 最小完整度架構圖（Minimum Viable HA Architecture）？包含：Figure A（生產環境 HA-HA Active-Active Mermaid 部署圖）和 Figure B（本地開發環境最小 HA Mermaid 架構圖）？任一圖缺失或兩圖均缺失視為 CRITICAL。
**Risk**: 沒有 §3.7，下游工程師（特別是 LOCAL_DEPLOY / runbook / ARCH）對「最小 HA 長什麼樣子」沒有視覺參考，容易設計成單副本（因為看起來更簡單）；導致 HA 程式行為（Distributed Lock / 冪等性 / Session 共享）從未被測試，生產故障時才發現設計錯誤。
**Fix**: 依 EDD.md §3.7 骨架，生成兩張 Mermaid `graph TB` 圖：Figure A（含 Global LB + 雙 Region + 每 Region ≥ 2 API Pod）和 Figure B（含 Local Nginx → api-1 + api-2 + worker-1 + worker-2）；並附上最小 Replica 表格。

#### [HIGH] 31 — Figure B 本地 API Server / Worker 副本數為 1
**Check**: §3.7.2 Figure B（本地開發環境）的最小 Replica 表格中，API Server 或 Worker 的 Min Replicas（Local）是否標注為 1 或「1（Local OK）」？若任一為 1 視為 HIGH。
**Risk**: 本地允許單副本的錯誤示範會被開發者直接套用於 docker-compose.yml，導致 Distributed Lock（Redis SETNX/Redlock）、冪等防重入（DB 唯一約束）、Session 共享（Redis）等 HA 關鍵路徑從未被測試；到生產才發現競態問題時代價極高。
**Fix**: 將 Figure B 最小 Replica 表格中 API Server 和 Worker 的 Min Replicas（Local）改為 **≥ 2**（加粗），並補充說明「必須 ≥ 2 以測試 HA 程式行為」；DB/Redis/MQ 在本地允許單節點。
