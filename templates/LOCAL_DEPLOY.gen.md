---
doc-type: LOCAL_DEPLOY
output-path: docs/LOCAL_DEPLOY.md
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
quality-bar: "新進工程師第一天，依文件操作，5 分鐘內跑起完整本地環境，不需問任何人。"
---

# LOCAL_DEPLOY 生成規則

本檔案定義 `docs/LOCAL_DEPLOY.md` 的生成邏輯。由 `/gendoc local-deploy` 讀取並遵循。
技術基礎：Rancher Desktop + Kubernetes（k3s），所有服務（含 client/前端）均部署在同一 K8s namespace。

---

## Iron Rule: 累積上游讀取
每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## Upstream Sources（上游文件對照表）

| 上游文件 | 提供資訊 | 對應 LOCAL_DEPLOY 章節 |
|---------|---------|----------------------|
| `docs/req/*` | 原始需求素材 | 背景補充 |
| `IDEA.md` | 系統核心概念、初始業務假設 | §1 Prerequisites 目標環境說明 |
| `BRD.md` | 業務功能說明、外部依賴服務清單 | §14 Mock Services |
| `PRD.md` | 功能範疇、維護窗口限制 | §10 Common Issues 的業務背景 |
| `PDD.md` | Client 類型（Web SaaS/Unity/HTML5 等）、前端框架 | §15 Inner Loop 前端 HMR 設定 |
| `EDD.md` Document Control | PROJECT_NAME、PROJECT_SLUG、GITHUB_ORG、GITHUB_REPO | §3 Quick Start（git clone URL）|
| `EDD.md` §3.3 技術棧 | 後端語言 + Runtime、Web Framework、ORM、DB 版本、Redis 版本、K8s 版本、前端框架 | §1 Prerequisites、§2 Architecture、§9 ConfigMap Reference |
| `EDD.md` §3.5 雲端平台基礎 | K8s 服務、Container Registry URL、Base Image、Image Tag 策略 | §4.4 Build & Load Image |
| `EDD.md` §3.5 環境矩陣 Local 欄 | namespace（`PROJECT_SLUG-local`）、kubectl context（`rancher-desktop`）、資源限制 | §4.2 Rancher Desktop 設定、§9 ConfigMap Reference |
| `EDD.md` §3.5 服務 Port 對照表 | API_PORT、WEB_PORT、DB_PORT、REDIS_PORT、MINIO_PORT、MAIL_PORT、PGADMIN_PORT | §5 Service Reference、§12 Port Reference |
| `EDD.md` §2.1 系統上下文圖 | 外部依賴服務（Payment、Email、SMS 等）| §14 Mock Services |
| `ARCH.md` | 系統架構圖、元件清單 | §2 Architecture Overview |
| `API.md` | API 端點清單、認證方式 | §8 Test Data（API 測試用 curl 範例）|
| `SCHEMA.md` | DB 表結構、遷移檔案命名 | §7 Database Operations、§4.6 DB 初始化 |
| `test-plan.md` | 測試策略、E2E 測試工具 | §6 Development Commands（測試命令）|
| `BDD.md` | 驗收場景 Feature Files 位置 | §6 Development Commands（BDD 執行命令）|

---

## Key Fields（關鍵欄位提取清單）

**必須從 EDD 提取（不得留裸 `{{...}}` 空白）：**

| 欄位 | EDD 來源 | 提取方式 |
|-----|---------|---------|
| `PROJECT_NAME` | Document Control **專案名稱** | 可讀名稱（e.g., `Payment Gateway`）|
| `PROJECT_SLUG` | Document Control **Project Slug** | 小寫連字號格式（e.g., `payment-gateway`）|
| `GITHUB_ORG` | Document Control **GitHub Org** | e.g., `my-company` |
| `GITHUB_REPO` | Document Control **GitHub Repo** | e.g., `payment-gateway` |
| `K8S_NAMESPACE` | §3.5 環境矩陣 Local 欄 **K8s Namespace** | `{{PROJECT_SLUG}}-local`（若 EDD 未填，從 SLUG 自動組合）|
| `BACKEND_LANG` | §3.3 **後端語言** | e.g., `TypeScript` / `Python` / `Go` / `Java` |
| `RUNTIME_PLATFORM` + `RUNTIME_VERSION` | §3.3 **後端 Runtime 平台** | e.g., `Node.js 20 LTS` |
| `FRAMEWORK` + `FRAMEWORK_VERSION` | §3.3 **Web / API Framework** | e.g., `Express 4.18` |
| `ORM` | §3.3 **ORM / 資料存取層** | 用於推斷 MIGRATE_CMD |
| `DB` + `DB_VERSION` | §3.3 **資料庫** | e.g., `PostgreSQL 16` |
| `CACHE` + `CACHE_VERSION` | §3.3 **快取** | e.g., `Redis 7` |
| `MQ` + `MQ_VERSION` | §3.3 **訊息佇列** | e.g., `RabbitMQ 3.13`（若無填 `N/A`）|
| `K8S_VERSION` | §3.3 **容器編排** / §3.5 **K8s 版本** | e.g., `1.30` |
| `BASE_IMAGE` + `BASE_IMAGE_TAG` | §3.5 **Docker Base Image** | e.g., `node:20-alpine` |
| `FRONTEND_LANG` | §3.3 **前端語言** | 若純後端填 `N/A` |
| `FRONTEND_FRAMEWORK` + `FRONTEND_FW_VERSION` | §3.3 **前端框架** | 用於推斷 WEB_DEV_CMD；若純後端填 `N/A` |
| `API_PORT` | §3.5 服務 Port 對照表 **api-server K8s Internal Port** | e.g., `8080` |
| `WEB_PORT` | §3.5 服務 Port 對照表 **web-app K8s Internal Port** | e.g., `3000`；若純後端填 `N/A` |
| `DB_PORT` | §3.5 服務 Port 對照表 **PostgreSQL Local port-forward Port** | e.g., `5432` |
| `REDIS_PORT` | §3.5 服務 Port 對照表 **Redis Local port-forward Port** | e.g., `6379` |
| `MINIO_PORT` | §3.5 服務 Port 對照表 **MinIO Local port-forward Port** | e.g., `9000` |
| `MAIL_PORT` | §3.5 服務 Port 對照表 **Mailpit Web UI Local port-forward Port** | e.g., `8025` |
| `PGADMIN_PORT` | §3.5 服務 Port 對照表 **pgadmin Local port-forward Port** | e.g., `5050` |
| 外部依賴服務 | §2.1 系統上下文圖中的 External Service 節點 | 清單，用於 §14 Mock Services |

**以下欄位從 Framework 類型推斷（不得保留裸 placeholder）：**

| 欄位 | 推斷規則 |
|-----|---------|
| `MIGRATE_CMD` | ORM = Prisma → `npx prisma migrate deploy`；Alembic → `alembic upgrade head`；Flyway → `flyway migrate`；GORM AutoMigrate → `./app migrate`；TypeORM → `npx typeorm migration:run`；Spring Boot Liquibase → `./gradlew flywayMigrate`；無 ORM → `make db-migrate`（保留，含 TODO 說明） |
| `MIGRATE_STATUS_CMD` | 對應 ORM 的 status 命令；Prisma → `npx prisma migrate status`；若無則 `make db-status` |
| `SEED_CMD` | 若 EDD §3.3 有 seed 框架 → 對應指令；否則 `make db-seed`（保留，含 TODO 說明） |
| `WEB_DEV_CMD` | 前端框架 = Next.js / Nuxt.js / Remix → `npm run dev`；Vite（React/Vue/Svelte）→ `pnpm dev`；Angular → `ng serve`；純後端（N/A）→ 整個前端 inner loop 段標記跳過 |
| `RUNTIME_CMD` | Runtime = Node.js → `node`；Python → `python3`；Go → `go`；Java/Kotlin → `java` |

**以下欄位使用格式範例佔位符（允許保留，不視為缺失）：**

| 欄位類別 | 格式範例 |
|---------|---------|
| Grafana / 監控 URL | `http://{{PROJECT_SLUG}}.local/grafana`（local Ingress）|
| OAuth Provider 回調 | `https://{{PROJECT_SLUG}}.local/auth/callback` |
| 外部 API Key 變數名稱 | `{{EXTERNAL_API_KEY_VAR}}`（使用 EDD §2.1 外部服務名稱組合）|
| Worker queue 名稱 | `default,emails,reports`（若 EDD 有定義則使用真實值）|

---

## Inference Rules（推斷邏輯）

### Document Control
- `DOC-ID`：`LOCAL_DEPLOY-<PROJECT_SLUG 大寫>-<YYYYMMDD>`
- `Status`：`DRAFT`
- `Upstream EDD`：`docs/EDD.md`

### §1 Prerequisites 填入規則

- **Rancher Desktop**：版本固定 `1.13`（最低需求）；Install 欄填入官方網址 `https://rancherdesktop.io`
- **Runtime 工具列**：依 EDD §3.3 後端語言填入對應工具；若純 K8s 部署不需本機 runtime 工具，移除對應列並加注釋
- **前端工具列**：若 EDD §3.3 前端框架為 N/A，移除 Node.js（開發工具）列
- RAM 建議值：`max(8GB, sum(Memory Limit) × 2)`（從 EDD §3.5 Local 欄資源限制計算）

### §2 Architecture Overview 填入規則

- namespace 名稱使用 `K8S_NAMESPACE`（真實值，非 placeholder）
- 所有服務的 port 標注使用真實值
- 若純後端 API（無前端框架），移除 web-app 節點
- K8s 資源對照表：IMAGE 欄使用 `{{PROJECT_SLUG}}/api:local` 格式

### §3 Quick Start

- git clone URL：`git clone git@github.com:{{GITHUB_ORG}}/{{GITHUB_REPO}}.git`（真實值）
- health-check URL：`http://{{PROJECT_SLUG}}.local/api/health`（真實 PROJECT_SLUG）
- 若純後端：移除 web-app health-check 行

### §4 Step-by-Step Setup

**§4.2 Rancher Desktop 設定**：
- kubectl context 名稱固定為 `rancher-desktop`
- namespace 建立命令使用真實 `K8S_NAMESPACE`
- /etc/hosts 設定：`127.0.0.1 {{PROJECT_SLUG}}.local api.{{PROJECT_SLUG}}.local`

**§4.3 建立 K8s Secret**：
- secrets.env 路徑：`k8s/overlays/local/secrets.env`
- 建立命令使用 `--from-env-file`（非 `--from-literal`）
- 必須說明：`k8s/overlays/local/secrets.env` 已加入 `.gitignore`

**§4.4 Build & 載入 Image**：
- nerdctl build（非 docker）+ 使用 EDD §3.5 Base Image
- Dockerfile 路徑：`docker/api/Dockerfile`、`docker/web/Dockerfile`（若純後端只有 api）
- 明確說明：`imagePullPolicy: Never`

**§4.5 部署所有 K8s 資源**：
- `kubectl apply -k k8s/overlays/local/`
- `kubectl wait --for=condition=Ready pods --all -n {{K8S_NAMESPACE}} --timeout=180s`

**§4.6 初始化資料庫**：
- migration 等同命令：`kubectl exec -n {{K8S_NAMESPACE}} deploy/api-server -- {{MIGRATE_CMD}}`
- seed 等同命令：`kubectl exec -n {{K8S_NAMESPACE}} deploy/api-server -- {{SEED_CMD}}`

### §5 Service Reference

- Ingress 存取表：所有 URL 使用 `http://{{PROJECT_SLUG}}.local/<path>` 格式
- port-forward 表：所有指令使用真實 namespace 和真實 port
- 若純後端：移除 web-app 列

### §6 Development Commands

三個分類（Image & Deployment、觀察 & 偵錯、測試）的 `make` 指令**必須**提供等同底層 kubectl/nerdctl 命令：

| make 指令 | 等同底層命令 |
|-----------|------------|
| `make image-build-api` | `nerdctl build -t {{PROJECT_SLUG}}/api:local -f docker/api/Dockerfile .` |
| `make k8s-restart-all` | `kubectl rollout restart deployment --all -n {{K8S_NAMESPACE}}-local` |
| `make k8s-delete` | `kubectl delete -k k8s/overlays/local/` |
| `make k8s-clean` | `kubectl delete namespace {{K8S_NAMESPACE}}-local` |
| `make shell-db` | `kubectl exec -it -n {{K8S_NAMESPACE}}-local statefulset/postgres -- psql -U app -d {{PROJECT_SLUG}}_dev` |
| `make test-unit` | `{{TEST_UNIT_CMD}}` |
| `make test-e2e` | `npx playwright test --base-url http://{{PROJECT_SLUG}}.local` |

### §7 Database Operations

- namespace：真實 `K8S_NAMESPACE`
- pod selector：`statefulset/postgres`
- DB 連線字串：`postgres://app:secret@localhost:{{DB_PORT}}/{{PROJECT_SLUG}}_dev`
- **所有含明文密碼 `secret` 的連線字串前，必須加安全警示**：
  ```
  # ⚠️  WARNING: 密碼 'secret' 僅為本機開發預設值，staging / production 環境禁止使用。
  ```
- Migration 等同命令加 `#` 前綴（避免被誤當作可直接執行的命令）

### §9 ConfigMap & Secret Reference

- `DATABASE_URL` 值使用 K8s internal DNS：`postgres://app:secret@postgres:5432/{{PROJECT_SLUG}}_dev`（非 localhost）
- `REDIS_URL` 值使用 K8s internal DNS：`redis://redis:6379/0`（非 localhost:6379）
- `CORS_ORIGINS`：`http://{{PROJECT_SLUG}}.local`
- `STORAGE_ENDPOINT`：`http://minio:9000`
- `SMTP_HOST`：`mailpit`
- Secret 表格只列 Key 名稱，不填入任何值

### §10 Common Issues & Fixes

必須涵蓋 5 類常見問題（含真實 namespace 和服務名稱）：
1. Pod stuck in Pending — 資源不足
2. CrashLoopBackOff — `kubectl logs --previous` 診斷
3. ImagePullBackOff — nerdctl images 驗證 + 重新 build
4. Ingress 無法解析 — /etc/hosts 驗證 + traefik pod 確認
5. DB 連線拒絕 — postgres pod Ready 確認 + K8s DNS 驗證

另加 3 個框架特定問題（從 EDD §3.3 推斷）：
- ORM = Prisma：`prisma migrate resolve` 步驟
- ORM = Alembic：`alembic stamp head` 步驟
- Redis：maxmemory 設定

### §14 Mock Services

從 EDD §2.1 外部依賴建立 Mock 表格：
- Email → mailpit
- 物件儲存 → minio
- Payment → Stripe CLI 或 WireMock（含具體啟動步驟）
- SMS → Log mock
- OAuth → MockOAuth2Server（含 K8s manifest 啟用說明）
- 若 EDD §2.1 未定義外部依賴 → 保留 mailpit 和 minio 列（本地 K8s 標配）

### §15 Inner Loop

**後端 inner loop**：
- nerdctl build + rollout restart：`kubectl rollout restart deploy/api-server -n {{K8S_NAMESPACE}}`

**前端 inner loop**（若有前端）：
- HMR 命令使用推斷的 `WEB_DEV_CMD`
- 若純後端：整段標記 `（純後端服務，無前端 inner loop）`

**Skaffold 段**：profile 固定為 `local`：`skaffold dev --profile local`

### §16 Cleanup

所有命令使用真實 namespace：
- `kubectl delete -k k8s/overlays/local/`
- `kubectl delete namespace {{K8S_NAMESPACE}}`

---

## Prohibited Patterns（禁止模式）

- 文件中不得有明文密碼（ConfigMap 中只有範例值 `secret` 並加注釋「僅本機開發用，禁止 production 使用」）
- Secret 建立使用 `--from-env-file`（非 `--from-literal`）
- `kubectl exec` 連線字串中不得包含硬編碼真實密碼
- nerdctl 命令禁止替換為 docker（Rancher Desktop 使用 containerd runtime）
- ConfigMap 中 DATABASE_URL、REDIS_URL 禁止使用 `localhost`

---

## Self-Check Checklist（生成後自我檢核，共 25 項）

**欄位提取正確性（10 項）**
- [ ] PROJECT_SLUG 已從 EDD Document Control 正確提取（小寫連字號格式）
- [ ] GITHUB_ORG + GITHUB_REPO 已填入 git clone URL（非 placeholder）
- [ ] K8S_NAMESPACE 格式為 `{{PROJECT_SLUG}}-local`（來自 EDD §3.5 Local 欄）
- [ ] 所有 port 號碼來自 EDD §3.5 服務 Port 對照表，而非預設值
- [ ] DB_PORT 的 port-forward 命令映射至 postgres StatefulSet 的 5432（非 pod 直連）
- [ ] MIGRATE_CMD 已依 ORM 類型推斷（Prisma/Alembic/GORM/TypeORM 等），非裸 placeholder
- [ ] WEB_DEV_CMD 已依前端框架推斷，或已標記純後端跳過
- [ ] ConfigMap 中所有 URL 使用 K8s internal DNS（service 名稱），非 localhost
- [ ] secrets.env 路徑和 `--from-env-file` 建立方式已正確記錄
- [ ] Quick Start 的 git clone URL 含真實 GITHUB_ORG 和 GITHUB_REPO

**結構完整性（8 項）**
- [ ] §1 Prerequisites 包含 Rancher Desktop（非 Docker Desktop）
- [ ] §2 Architecture 的 Mermaid 圖節點 port 標注與 §12 Port Reference 一致
- [ ] §4.3 明確說明 secrets.env 已加入 .gitignore，且不提交 git
- [ ] §4.4 包含 `imagePullPolicy: Never` 的說明
- [ ] §5 port-forward 表與 §12 Port Reference 完全一致（無矛盾）
- [ ] §10 Common Issues 涵蓋 Pending / CrashLoopBackOff / ImagePullBackOff / Ingress 解析失敗 / DB 連線拒絕
- [ ] §14 Mock Services 表從 EDD §2.1 外部依賴生成（非全部保留模板預設）
- [ ] §15 Inner Loop 若純後端已移除/標記前端段落

**安全性（4 項）**
- [ ] §7 Database Operations 所有含明文密碼 `secret` 的連線字串前均有安全警示注釋
- [ ] Secret 建立使用 `--from-env-file` 方式
- [ ] §13 Local HTTPS 使用 mkcert（非自簽憑證），且憑證私鑰加入 .gitignore
- [ ] pgadmin Secret 密碼注釋「本機使用，勿使用於其他環境」

**裸 placeholder 掃描（3 項）**
- [ ] 全文無裸 `{{PROJECT_NAME}}`、`{{PROJECT_SLUG}}`、`{{K8S_NAMESPACE}}` placeholder（應已全部替換）
- [ ] 全文無裸 `{{API_PORT}}`、`{{WEB_PORT}}`、`{{DB_PORT}}`、`{{REDIS_PORT}}` placeholder（應已全部替換）
- [ ] 允許保留的格式範例佔位符（Grafana URL、PagerDuty URL、外部 API Key）均已加上說明，不會被誤認為必填空白
