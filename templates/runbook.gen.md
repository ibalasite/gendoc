---
doc-type: runbook
output-path: docs/RUNBOOK.md
upstream-docs:
  - docs/req/
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/EDD.md
  - docs/ARCH.md
  - docs/API.md
  - docs/SCHEMA.md
  - docs/test-plan.md
  - docs/BDD.md
quality-bar: "凌晨 3 點被叫醒，零前情提要，能直接執行，不需問任何人。"
---

# runbook 生成規則

本檔案定義 `docs/RUNBOOK.md` 的生成邏輯。由 `/gendoc runbook` 讀取並遵循。
品質標準：凌晨 3 點被叫醒的 SRE，零前情提要，能直接執行每一個步驟。

---

## Iron Rule: 累積上游讀取
每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## Upstream Sources（上游文件對照表）

| 上游文件 | 提供資訊 | 對應 Runbook 章節 |
|---------|---------|-----------------|
| `docs/req/*` | 原始需求素材、業務背景、利害關係人需求 | §1 System Overview 業務背景 |
| `IDEA.md` | 系統核心概念、初始業務假設、Kill Conditions | §1 Operational Constraints |
| `BRD.md` | 業務功能說明、峰值流量窗口、資料分類、業務衝擊說明 | §1 System Overview、§1 Operational Constraints |
| `PRD.md` | SLA 承諾（P1/P2 回應時間）、功能範疇（blast radius）、可用性目標、維護窗口限制 | §3.3 Customer SLA、§6.2 Severity Classification |
| `PDD.md` | 設計決策、UX 考量、Client 類型 | §1 System Overview 補充 |
| `EDD.md` | 架構圖、技術選型、SLO/SLI 量化數字、DB/Redis 連線規格、K8s 資源（namespace、deployment、HPA）、Mermaid 圖、Chaos Engineering 實驗、DR RTO/RPO | §2 架構、§3 SLO、§4 部署、§7 Troubleshooting、§9 Rollback、§10 Backup |
| `ARCH.md` | 系統拓撲、元件清單、Network 設計、ADR 決策紀錄 | §2 架構、§2.2 Component Inventory |
| `API.md` | API 端點清單、認證機制、錯誤碼 | §7 Troubleshooting API 錯誤診斷 |
| `SCHEMA.md` | DB 名稱、表結構、索引（用於 §7.5 DB troubleshooting 的 psql 查詢） | §7.5 Database Issues |
| `test-plan.md` | 測試覆蓋範圍、風險評估、性能基準 | §3 SLO 設定依據、§15 Validation |
| `BDD.md` | 驗收場景、業務行為規格 | §7 Troubleshooting 場景對應 |

---

## Key Fields（關鍵欄位提取清單）

**必須從上游文件提取（不得留空或只寫 `{{...}}`）：**

| 欄位 | 來源 | 提取方式 |
|-----|------|---------|
| `PROJECT_NAME` | EDD §0 DOC-ID 或 BRD 標題 | 可讀名稱（e.g., `Payment Gateway`）|
| `PROJECT_SLUG` | EDD §0 DOC-ID | 小寫連字號格式（e.g., `payment-gateway`）|
| `SYSTEM_BUSINESS_FUNCTION` | BRD §1 系統描述（前 2-3 句） | 業務功能說明（非技術棧描述）|
| `K8S_NAMESPACE` | EDD §7 k8s 資源規格的 namespace 欄位 | 完整 namespace 字串（e.g., `payment-prod`）|
| `API_DEPLOYMENT_NAME` | EDD §9 CI/CD 設計 或 EDD §7 資源規格 | Deployment 名稱（e.g., `payment-api-server`）|
| `WORKER_DEPLOYMENT_NAME` | EDD §9 CI/CD 設計 或 EDD §7 資源規格 | Worker Deployment 名稱（若有）|
| `API_APP_LABEL` | EDD §7 K8s Label 定義 | label selector（e.g., `app=payment-api-server`）|
| `DB_NAMESPACE` | EDD §7 DB Pod 所在 namespace | 若 DB 在獨立 namespace，需單獨記錄 |
| `CRON_JOB_NAME` | EDD §7 CronJob 定義（若有） | 逗號分隔的完整 CronJob 名稱清單（若無設為 N/A）|
| `API_PORT` | EDD §7 K8s Service 定義 或 ARCH | 容器監聽 port（e.g., `8080`）|
| `AVAILABILITY_SLO` | EDD §10.5 SLO/SLI | 百分比數字（e.g., `99.9`）|
| `P99_TARGET_MS` | EDD §10.5 SLO/SLI Latency P99 | 毫秒數字（e.g., `500`）|
| `ERROR_RATE_SLO` | EDD §10.5 SLO/SLI Error Rate | 百分比（e.g., `0.1`）|
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` | EDD §2 技術選型 + SCHEMA.md | 完整連線資訊 |
| `REDIS_HOST` / `REDIS_PORT` | EDD §2 技術選型 | Redis 連線資訊 |
| `RTO` | EDD §13.5 DR 設計 RTO 目標 | 分鐘數（e.g., `30`）|
| `RPO` | EDD §13.5 DR 設計 RPO 目標 | 分鐘數（e.g., `5`）|
| `P1_RESPONSE_TIME` | PRD 可用性要求 或 EDD §13.6 | 時間字串（e.g., `1 hour`）|
| `P2_RESPONSE_TIME` | PRD 可用性要求 | 時間字串（e.g., `4 hours`）|
| `PEAK_WINDOW` | BRD 業務描述 + PRD 維護窗口限制 | 時間描述（e.g., `Mon–Fri 09:00–18:00 UTC`）|
| `DATA_CLASSIFICATION` | BRD 資料分類章節 | 分類字串（e.g., `PCI DSS Cardholder Data`）|
| Mermaid 架構圖 | EDD §10 直接引用 | 完整 Mermaid 程式碼塊 |

**以下欄位允許使用有意義的格式範例佔位符（不得保留裸 `{{PLACEHOLDER}}`）：**

| 欄位類別 | 允許格式範例 |
|---------|------------|
| Grafana dashboard URL | `https://grafana.{{DOMAIN}}/d/{{DASHBOARD_ID}}/service-health` |
| PagerDuty URL | `https://{{ORG}}.pagerduty.com/services/{{SERVICE_ID}}` |
| GH_OWNER / GH_REPO | `{{GITHUB_ORG}}/{{REPO_NAME}}` |
| Status Page URL | `https://status.{{COMPANY_DOMAIN}}` |
| Incident channel | `#incidents-{{PROJECT_SLUG}}` |
| CI Pipeline URL | `https://github.com/{{GH_OWNER}}/{{GH_REPO}}/actions` |

---

## Section Rules（章節生成規則）

### §0 Document Control
- `DOC-ID`: `RUNBOOK-<PROJECT_SLUG 大寫>-<YYYYMMDD>`
- `Status`: `DRAFT`
- `Upstream docs`: 列出已讀取的上游文件清單

### §1 System Overview

從 BRD §1 提取業務功能說明（3–6 句），必須覆蓋：
1. 系統做什麼（業務功能，非技術棧描述）
2. 誰依賴它（上游呼叫方與下游消費者）
3. 系統下線時什麼會壞掉（blast radius）
4. 非顯而易見的操作限制（峰值流量、批次時間窗口）

Operational Constraints 從 BRD 峰值流量窗口 + PRD 維護窗口限制填入真實數據。

**禁止**：「The system is a Node.js microservice that...」類技術棧描述替代業務功能說明。

### §2 Architecture

**§2.1 Runtime Topology Mermaid 圖處理規則**：
- 若 EDD §10 已有 Mermaid → 直接引用，並在節點標籤中新增 k8s deployment 名稱標注
- 若 EDD 無 Mermaid → 從 ARCH.md 推斷重建，使用 `graph TB` 方向，節點名稱使用真實 K8s 資源名稱
- Data Plane 節點填入真實 `DB_HOST:DB_PORT`、`REDIS_HOST:REDIS_PORT`

**§2.2 Component Inventory**：每行有真實 `K8s Namespace` 和 `K8s Deployment` 名稱（來自 EDD §7）。

**§2.3 Network and Port Reference**：從 ARCH.md Network Design 或 EDD §7 K8s Service 提取。

### §3 SLI/SLO/SLA

**所有 SLO 數字必須來自 EDD §10.5，不得使用預設值：**
- AVAILABILITY_SLO、P99_TARGET_MS、ERROR_RATE_SLO：從 EDD §10.5 提取
- P1/P2 回應時間：從 PRD 提取（非預設 1h/4h）
- Error Budget = `(1 - AVAILABILITY_SLO/100) × 30 × 24 × 60` 分鐘（填入真實數字計算結果）

SLO Burn Rate PromQL（Google SRE Workbook 標準）：
- Critical（P1）：burn rate factor = **14.4x**，multi-window（1h + 5m）
- Warning（P2）：burn rate factor = **6x**，multi-window（6h + 30m）
- PromQL 中直接填入計算後的靜態浮點數，不保留 `<AVAILABILITY_SLO>` 字串

**若 EDD §10.5 缺失**：SLO 欄位使用 `{{EDD_SLO_REQUIRED}}` 格式佔位符，並加入 WARNING HTML 注釋。

### §4 Deployment Procedures

- Pre-Deployment Checklist 中 URL 使用格式範例佔位符
- 所有 kubectl 命令使用真實 deployment 名稱（`API_DEPLOYMENT_NAME`）和真實 namespace（`K8S_NAMESPACE`）

### §5 Monitoring and Alerting

**§5.2 Alert Reference Table** 必須包含以下 Alert（使用真實 PROJECT_SLUG 填入）：
- `<slug>_high_error_rate`（P1）
- `<slug>_availability_breach`（P1）
- `<slug>_p99_latency_high`（P2）
- `<slug>_queue_depth_high`（P2，若 EDD 有 Queue 設計）
- `<slug>_db_connection_pool_exhausted`（P1）
- `<slug>_pod_crashloopbackoff`（P1）
- `<slug>_slo_burn_rate_critical`（P1）
- `<slug>_slo_burn_rate_warning`（P2）

### §6 Incident Response

從 PRD §6.2（或等效章節）提取 P1/P2/P3 定義：
- P1/P2 回應時間使用 PRD 定義值（非預設 15 分/2 小時）
- §6.8 Post-Mortem 必須包含：草稿截止 2 business days、分發給所有參與者、incident date + 30 天 check-in

**若 PRD 不存在或無 §6.2**：使用 `{{PRD_P1_RESPONSE_REQUIRED}}` 格式佔位符 + WARNING HTML 注釋。

### §7 Troubleshooting

**這是最關鍵的章節。每個場景必須：**
1. 有 Mermaid flowchart 決策樹（從症狀到解法的完整路徑）
2. 所有 kubectl 命令使用真實 namespace 和 deployment 名稱
3. 每個診斷命令有 `# Expected:` 預期輸出
4. 每個命令有 `# If this fails:` 處理路徑（不得留空或「聯絡相關團隊」）

必須覆蓋的場景：
- §7.1 API Server 5xx 錯誤
- §7.2 服務完全不可用
- §7.3 High Latency（流量暴增、DB 慢查詢、Cache Miss Rate、上游依賴分支）
- §7.4 Job Queue Backlog（若 EDD 有 Queue 設計）
- §7.5 Database Issues（§7.5.1 連線池耗盡、§7.5.2 複製延遲）
- §7.6 Pod CrashLoopBackOff
- §7.7 Disk Pressure
- §7.8 External Dependency Failure（若 EDD 有外部依賴）
- §7.9 Backup Failure（若 EDD §13.5 有備份策略）
- §7.10 Cron Job / Batch Failure（若 EDD 有 CronJob 設計）

### §9 Rollback Procedures

**§9 各子章節完整自包含（不得引用「見上方」）：**
```bash
kubectl rollout undo deployment/<API_DEPLOYMENT_NAME> -n <K8S_NAMESPACE>
# Expected: "deployment.apps/<API_DEPLOYMENT_NAME> rolled back"
```

§9.3 Regional Failover 必須包含 replication lag 量化警告和檢查命令。

### §10 Backup and Restore

- RTO/RPO 來自 EDD §13.5（非預設值）
- DB Restore 命令：`kubectl exec -n <DB_NAMESPACE> <pod> -- psql -U <DB_USER> -d <DB_NAME>`
- **Credentials 不得以明文出現在 kubectl 命令中**

### §11 Security Procedures

**§11.1 Secret Rotation 正確順序**：
1. 先在 PostgreSQL 執行 `ALTER USER <user> WITH PASSWORD '<new>'`（更新 DB 密碼）
2. 再更新 K8s Secret（`kubectl create secret generic ...`）
3. 最後 Rolling Restart Pod（`kubectl rollout restart`）
順序錯誤會導致服務中斷。

**§11.3 Compromised Credentials**：
- 明確定義 15 分鐘撤銷 SLA
- 具體步驟：kubectl delete secret → recreate → pod restart

**§11.4 WAF Block（若有 WAF 設計）**：
`aws wafv2 update-web-acl` 命令必須含 `--scope`、`--id`、`--default-action`、`--visibility-config` 四個 flag。

### §12 Contacts and Escalation

完全使用格式範例佔位符，不填入虛構姓名或電話。

### §13 Change Log

初始只有一行 DRAFT 記錄（Version 0.1，含生成日期）。

### §14 On-Call Handoff

必須包含可直接貼上 Slack 的訊息範本：
```
[ON-CALL HANDOFF] <PROJECT_NAME>
日期：<DATE>
值班接手：@<INCOMING_ENGINEER>

目前狀態：<GREEN / DEGRADED / INCIDENT>
進行中事項：<DESCRIPTION or "無">
需注意：<DESCRIPTION or "無">
待處理 ticket：<URL or "無">
Grafana：<GRAFANA_OVERVIEW_DASHBOARD>
```

### §15 Runbook Validation Procedure

至少 3 個具體測試場景（含通過標準，不得只說「定期測試」）：
1. **Monthly**: 模擬 DB 連線池耗盡，確認 §7.5.1 診斷步驟可執行
2. **Quarterly DR Drill**: 在 Staging 執行 §9.3 Regional Failover，記錄實際 RTO/RPO
3. **New On-Call**: 新工程師獨立走過 §4.2 Standard Deployment，不需協助

通過標準：每個場景執行時間 ≤ 規定 SLA，每個 kubectl 命令成功執行（exit 0）。

---

## Prohibited Patterns（禁止模式）

- `§1` 中禁止「The system is a Node.js microservice that...」類技術棧描述
- `§9` Rollback 禁止「見 §4」類交叉引用（必須完整自包含）
- `§10.2` DB Restore 禁止明文 Credentials
- `§11.1` Secret Rotation 順序不得顛倒（必須先改 DB 再改 K8s Secret）
- `§15` 禁止「定期測試」類泛化描述（必須有具體場景和通過標準）
- SLO 數字禁止使用預設值（99.9% / 500ms / 0.1%）—— 必須來自 EDD §10.5

---

## Self-Check Checklist（生成後自我檢核，共 22 項）

- [ ] §1 System Overview 有具體業務功能說明（非泛型技術棧描述）
- [ ] §2 Mermaid 圖使用真實元件名稱（非 `{{PLACEHOLDER}}` 樣板）
- [ ] §2.2 Component Inventory 每行有真實 namespace 和 deployment 名稱
- [ ] §3 SLO 數字來自 EDD §10.5（非預設 99.9%/500ms/0.1%）
- [ ] §3.3 P1/P2 SLA 回應時間來自 PRD（非預設 1h/4h）
- [ ] §3.2 Error Budget 已用真實 SLO 數字計算（以分鐘表示）
- [ ] §5.2 SLO Burn Rate PromQL 已填入計算後的靜態浮點數（非 `<AVAILABILITY_SLO>` 字串）
- [ ] §7 Troubleshooting 所有 kubectl 命令使用真實 namespace/deployment 名稱
- [ ] §7 每個診斷命令有 `# Expected:` 和 `# If this fails:` 說明
- [ ] §9 Rollback 命令有正確 deployment 名稱，完整自包含（不引用「見上方」）
- [ ] §9.3 Regional Failover 有 replication lag 量化警告和檢查命令
- [ ] §10 Backup RTO/RPO 來自 EDD §13.5（非預設值）
- [ ] §10.2 DB Restore 無明文 Credentials
- [ ] §11.1 Secret Rotation 覆蓋 DB Credential 正確輪換順序（先改 DB 再改 K8s Secret）
- [ ] §11.3 Compromised Credentials 有 15 分鐘撤銷 SLA
- [ ] §14 On-Call Handoff 有可直接貼上 Slack 的範本
- [ ] §15 Runbook Validation 有具體測試場景和通過標準（非「定期測試」）
- [ ] 已無裸 `{{PLACEHOLDER}}` 格式的空白欄位（格式範例佔位符允許保留）
- [ ] §5.2 每個 Alert 的 Runbook Section anchor 指向真實存在的 §7.x 子章節
- [ ] §6 Incident Response P1/P2 回應時間來自 PRD；若 PRD 無此資訊，已使用格式佔位符並加 WARNING 注釋
- [ ] §6.8 Post-Mortem 包含草稿截止日（2 business days）、分發對象、30 天 check-in 三要素
- [ ] §12 Contacts 所有 Name/Contact 欄位為格式範例佔位符（無虛構姓名或電話號碼）
