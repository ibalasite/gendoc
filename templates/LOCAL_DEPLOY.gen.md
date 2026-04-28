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
  - docs/FRONTEND.md  # Layer 6 — 前端本地啟動設定（dev server port、env vars、hot reload）
  - docs/AUDIO.md    # 若存在：本地音訊資產路徑設定（dev server static 目錄、CORS 頭設定）
  - docs/ANIM.md     # 若存在：本地動畫資產路徑、Spine/DragonBones runtime 安裝
  - docs/test-plan.md
  - features/          # BDD-server 輸出（Server BDD Feature Files）
  - features/client/   # BDD-client 輸出（Client E2E Feature Files，若 client_type≠none）
quality-bar: "新進工程師第一天，依文件操作，5 分鐘內跑起完整本地環境，不需問任何人。"
---

# LOCAL_DEPLOY 生成規則

本檔案定義 `docs/LOCAL_DEPLOY.md` 的生成邏輯。由 `/gendoc local-deploy` 讀取並遵循。
技術基礎：Rancher Desktop + Kubernetes（k3s），所有服務（含 client/前端）均部署在同一 K8s namespace。

---

## K8s-First Policy（不可覆蓋，優先於所有其他設定）

**K8s 是唯一的本地部署主角。Docker Compose 是輔助工具，不構成 LOCAL_DEPLOY 的主架構。**

此規則優先於 EDD §3.5 的任何 Docker Compose 描述：
- 若 EDD §3.5 寫「Docker Compose only」→ **忽略**，仍生成完整 k8s LOCAL_DEPLOY
- 若 EDD §3.5 有 docker-compose.yml 定義 → 可在 §14 Mock Services 提及作為開發者本機快速 DB 驗證的備用工具，但**不作為主要啟動方式**
- ALIGN-F 不得將 k8s 指令改為 Docker Compose；衝突時 k8s 永遠優先
- 若 ALIGN_REPORT 標記 k8s/Docker Compose 衝突，正確處理方式是將 EDD 改為 k8s，而非將 LOCAL_DEPLOY 改為 Docker Compose

**Single External Port 原則**：
- 所有服務（含 client/前端）必須透過同一個 Ingress（port 80/443）存取
- 禁止要求開多個對外 port（如分別開 3000 給前端、8080 給 API）
- Tunnel 場景（ngrok / cloudflare tunnel / localtunnel）：只需 tunnel 一個 port（Ingress 80）

**AI Testability 目標**（最終大目標，生成文件必須支援）：
```
AI 代理能夠執行以下完整流程，無需人工介入：
  1. make k8s-init && make image-build-all && make k8s-apply
  2. kubectl wait --for=condition=Ready pods --all -n <namespace> --timeout=300s
  3. make db-migrate && make db-seed
  4. curl http://<project>.local（或 tunnel URL）→ HTTP 200
  5. 開啟瀏覽器，在 URL 測試前端介面
```
LOCAL_DEPLOY 每個步驟都必須可由 AI 指令驅動，無需互動式輸入（除首次 secret 設定外）。

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
| `features/*.feature`（BDD-server）| Server BDD Feature Files | §6 Development Commands（後端 BDD 執行命令）|
| `features/client/*.feature`（BDD-client，若存在）| Client E2E Feature Files | §6 Development Commands（E2E / Playwright 執行命令）|

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

### §8 Test Data & Fixtures

依以下來源填入真實內容（禁止保留裸 `{{ROLE_NAME}}`/`{{ENTITY_1}}` 等 placeholder）：

**Default User Accounts（角色行）：**
- 角色來源：BRD 業務功能描述中的使用者角色 + PRD 使用者類型
- 每個 PRD/BRD 定義的角色必須有一行（不得只保留 Admin + Regular User 兩行）
- Email 格式：`<lowercase-role>@{{PROJECT_SLUG}}.local`（PROJECT_SLUG 替換為真實值）
- 密碼：統一使用 `Password1!`（強度足夠本機開發）

**Sample Data（Entity 行）：**
- Entity 清單：從 SCHEMA.md §3 資料表定義提取所有業務表（非系統表），每個業務表對應一行
- Count：依 PRD 功能測試需求推斷（至少覆蓋所有 AC 的邊界情境）
- 說明欄：列出該 Entity 涵蓋的狀態類型（active / inactive / archived / pending 等）
- Edge case Entity（最後一行）：至少 1 個資料集覆蓋最大欄位長度 + 特殊字元（Unicode CJK）

**pgadmin 登入（必須填入真實 port）：**
- `{{PGADMIN_PORT}}`：來自 Key Fields `PGADMIN_PORT`
- `{{PROJECT_SLUG}}-pgadmin-secret`：使用真實 PROJECT_SLUG
- DB Name：`{{PROJECT_SLUG}}_dev`（替換為真實值）

### §11 Logs & Debugging

所有 kubectl 命令使用真實 namespace 和 deployment 名稱：
- `{{K8S_NAMESPACE}}`：使用 Key Fields `K8S_NAMESPACE`
- `{{RUNTIME_CMD}}`：使用 Key Fields 中推斷的 `RUNTIME_CMD`（node / python3 / go 等）

**「查看 Pod 日誌」區塊：**
- 若 EDD §7 無 `worker` Deployment → 移除 `make logs-worker` 行並加注釋
- 若 EDD §7 無 `web-app` Deployment（純後端）→ 移除 `make logs-web` 行

**「常見 Log 模式」表格：**
- `{{name}}`（Worker job）行：從 EDD §7 CronJob/Worker 定義中提取真實 job 名稱（若無 Worker，移除此兩行）
- `[ERROR] Migration {{name}} failed` 行：`{{name}}` 替換為 EDD §3.3 ORM 遷移工具的典型錯誤格式（Prisma → `migration XXX_...`、Alembic → `Rev: ...`）

### §12 Port Reference

**Ingress 表格：**
- `{{PROJECT_SLUG}}.local`：替換為真實 PROJECT_SLUG（全表）
- 若純後端（無 web-app）→ 移除 `http://{{PROJECT_SLUG}}.local/` 前端行，並加注釋「純後端服務，無前端 UI」
- Ingress path 清單與 §5 Service Reference 表格完全對齊（無矛盾行）

**port-forward 表格：**
- 所有 port 數字來自 Key Fields（`API_PORT`、`WEB_PORT`、`DB_PORT`、`REDIS_PORT`、`MINIO_PORT`、`MAIL_PORT`、`PGADMIN_PORT`）
- 若某 port 為 `N/A`（如純後端的 WEB_PORT）→ 移除對應行
- `{{K8S_NAMESPACE}}`：替換為真實值（全表）

**驗證一致性**：§12 Port Reference 所有 port 必須與 §2 Architecture Overview Mermaid 圖中的 port 標注一致。

### §13 Local HTTPS 設定

- `{{PROJECT_SLUG}}.local` + `*.{{PROJECT_SLUG}}.local`：替換為真實值（生成憑證命令）
- mkcert 憑證路徑（`.pem` 檔案名稱）：依 mkcert 預設命名規則（`{{PROJECT_SLUG}}.local+1.pem`）填入
- K8s TLS Secret 名稱：`{{PROJECT_SLUG}}-local-tls`（替換為真實 PROJECT_SLUG）
- `{{K8S_NAMESPACE}}`：替換為真實值
- 若 EDD §3.5 未提及 HTTPS 需求 → 在本節標頭加注釋「若無 OAuth 回調 / SameSite Secure Cookie 需求，可跳過此節」
- `.gitignore` 加入憑證私鑰：`{{PROJECT_SLUG}}.local-key.pem`（替換為真實值）

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

### §17 Tunnel Access（必須生成，不得省略）

目標：讓 AI 代理或開發者透過單一 tunnel URL 存取完整前端，無需多個 port。

- **工具**：生成 ngrok（推薦）+ Cloudflare Tunnel 兩種方式的完整指令
- **tunnel 指令**：`ngrok http 80 --host-header={{PROJECT_SLUG}}.local`（single port = Ingress 80）
- **Ingress wildcard patch**：說明如何讓 Ingress 接受任意 host（供 tunnel 動態域名使用）
- **驗證步驟**：`curl -s -o /dev/null -w "%{http_code}" "${_TUNNEL_URL}/"` → 200
- 若 `client_type=none`（純後端）：保留 API health check 驗證，移除前端 UI open 步驟

### §18 AI Agent Quick Start（必須生成）

目標：**AI 代理可一鍵執行腳本，從零啟動完整 k8s 環境並驗證前端可存取，無需人工介入。**

此章節代表整份 LOCAL_DEPLOY.md 的「最終大目標」：所有前面的步驟（Prerequisites、Secret 設定、Build、Deploy、DB 初始化）都是為了讓這個腳本可以成功執行。

生成規則：
- 腳本命名：`ai-quickstart.sh`，置於 `docs/` 或 repo root
- 6 個步驟對應 §3 Quick Start 的全部動作（確認 context → init → build → apply → db → verify）
- `kubectl wait` 逾時：`300s`（比 §3 的 180s 寬鬆，因 AI 不需等人確認）
- 末尾輸出：`前端 UI → http://{{PROJECT_SLUG}}.local` + tunnel 啟動提示
- AI 測試完整流程說明：`ai-quickstart.sh` → ngrok tunnel → Playwright 開啟 `_TUNNEL_URL` → 驗證 `features/client/*.feature` 所描述的功能

**質量要求**：此腳本必須可以被 AI 直接 copy-paste 執行，不得含任何需要人工決策的互動式步驟（secret 設定除外，須在說明中標記「首次需人工建立 secrets.env」）。

---

## Prohibited Patterns（禁止模式）

- 文件中不得有明文密碼（ConfigMap 中只有範例值 `secret` 並加注釋「僅本機開發用，禁止 production 使用」）
- Secret 建立使用 `--from-env-file`（非 `--from-literal`）
- `kubectl exec` 連線字串中不得包含硬編碼真實密碼
- nerdctl 命令禁止替換為 docker（Rancher Desktop 使用 containerd runtime）
- ConfigMap 中 DATABASE_URL、REDIS_URL 禁止使用 `localhost`

---

## Self-Check Checklist（生成後自我檢核，共 27 項）

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

**結構完整性（10 項）**
- [ ] §1 Prerequisites 包含 Rancher Desktop（非 Docker Desktop）
- [ ] §2 Architecture 的 Mermaid 圖節點 port 標注與 §12 Port Reference 一致
- [ ] §4.3 明確說明 secrets.env 已加入 .gitignore，且不提交 git
- [ ] §4.4 包含 `imagePullPolicy: Never` 的說明
- [ ] §5 port-forward 表與 §12 Port Reference 完全一致（無矛盾）
- [ ] §8 Test Data 角色清單來自 BRD/PRD 定義（無裸 `{{ROLE_NAME}}`/`{{ENTITY_N}}` placeholder）
- [ ] §10 Common Issues 涵蓋 Pending / CrashLoopBackOff / ImagePullBackOff / Ingress 解析失敗 / DB 連線拒絕
- [ ] §11 Logs & Debugging 所有 kubectl 命令使用真實 namespace（非 placeholder）
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

---

### Service Startup / Shutdown Sequencing（強制）

LOCAL_DEPLOY.md 必須包含服務啟動和關閉的依賴順序圖：

**啟動順序（Dependency Graph）**：

```
[Infrastructure Layer]
  PostgreSQL → Redis → NATS
          ↓
[Application Layer]
  Wait: PostgreSQL ready (pg_isready / SELECT 1)
  Wait: Redis ready (PING)
  Wait: NATS ready (health check endpoint)
          ↓
  UserService → OrderService → PaymentService
  (無依賴)    (依賴 UserSvc)  (依賴 OrderSvc)
          ↓
[Gateway Layer]
  API Gateway (等所有 Application Layer 服務通過 /health)
```

**每個服務的就緒判斷（readiness gate）**：
| 服務 | Readiness Check | 逾時 | 失敗行為 |
|-----|----------------|------|---------|
| PostgreSQL | `pg_isready -h localhost -p 5432` | 30s | 停止啟動，顯示錯誤 |
| Redis | `redis-cli ping` → PONG | 10s | 停止啟動 |
| OrderService | `GET /health` → 200 + `"status":"ready"` | 60s | 停止啟動 |
| API Gateway | 所有 upstream /health 通過 | 90s | 停止啟動 |

**優雅關閉（Graceful Shutdown）**：
| 關閉順序 | 服務 | drain timeout | 強制 kill timeout |
|---------|-----|--------------|-----------------|
| 1 | API Gateway | 30s（等待進行中請求完成） | 60s |
| 2 | Application Services | 15s | 30s |
| 3 | Infrastructure | 不 drain | 10s |

**禁止**：LOCAL_DEPLOY.md 無啟動順序說明；依賴服務啟動無就緒判斷（導致「先啟動者」連線失敗）

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

> **讀取 lang_stack 方式**：`python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('lang_stack','unknown'))"`

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 LOCAL_DEPLOY.md 章節清單（§1–§18），無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | 所有工具、套件管理器、執行指令與 state.lang_stack 一致 | 修正至一致 |
| 前置需求有版本號 | 每個前置工具（Rancher Desktop / kubectl / helm 等）都指定具體版本號 | 從 EDD §環境規格 提取版本號 |
| 指令可直接執行 | 所有 shell 指令可直接 copy-paste 執行（非概念描述） | 改寫為具體可執行指令 |
| Smoke Test 存在 | 部署完成後有驗證步驟（至少一個 curl / HTTP 請求驗證服務正常） | 補充 smoke test 指令 |
| §17 Tunnel Access 存在 | 包含 ngrok + cloudflare 兩種 tunnel 方式 + 驗證 curl 指令 | 生成 §17 |
| §18 AI Quick Start 可執行 | ai-quickstart.sh 腳本可被 AI 直接執行，6 步驟完整，末尾輸出前端 URL | 修正腳本使每步驟無需人工介入 |
| K8s-First 合規 | 文件主架構為 k8s（非 Docker Compose）；若有 docker-compose 提及，僅出現在 §14 輔助說明 | 移除 Docker Compose 主架構引用 |

---

## F-04：Docker/Sandbox 執行驗證要求

LOCAL_DEPLOY.md 生成完成後，**必須執行以下自動驗證**，確認所有指令可成功執行：

```bash
# F-04 驗證流程（在專案根目錄執行）

echo "[F-04] 開始 LOCAL_DEPLOY 自動驗證..."

# Step 1：驗證 Rancher Desktop + K8s 環境依賴
echo "[F-04-1] 驗證 Rancher Desktop + K8s 環境依賴..."
_MISSING_DEPS=0
command -v rdctl      > /dev/null 2>&1 || { echo "  ⚠️  rdctl 未安裝（需 Rancher Desktop）"; _MISSING_DEPS=1; }
command -v kubectl    > /dev/null 2>&1 || { echo "  ⚠️  kubectl 未安裝（Rancher Desktop 應自動安裝）"; _MISSING_DEPS=1; }
command -v nerdctl    > /dev/null 2>&1 || { echo "  ⚠️  nerdctl 未安裝（Rancher Desktop 應自動安裝）"; _MISSING_DEPS=1; }
command -v helm       > /dev/null 2>&1 || { echo "  ⚠️  helm 未安裝（brew install helm）"; _MISSING_DEPS=1; }
command -v make       > /dev/null 2>&1 || { echo "  ⚠️  make 未安裝（brew install make）"; _MISSING_DEPS=1; }
[[ $_MISSING_DEPS -eq 0 ]] && echo "  ✅ Rancher Desktop + K8s 環境確認" || echo "  ⚠️  有缺失依賴（不阻斷，繼續驗證）"

# Step 2：驗證 k8s manifest 結構（k8s-first 必查）
if [[ -d "k8s/overlays/local" ]]; then
  echo "  ✅ k8s/overlays/local/ 目錄存在"
  ls k8s/overlays/local/kustomization.yaml > /dev/null 2>&1 \
    && echo "  ✅ kustomization.yaml 存在" \
    || echo "  ⚠️  k8s/overlays/local/kustomization.yaml 不存在 → 需建立"
else
  echo "  ⚠️  k8s/overlays/local/ 目錄不存在 → LOCAL_DEPLOY 指令將無法執行"
fi

# Step 3：Dry-run 關鍵指令（模擬，不實際執行）
echo "[F-04-3] 指令格式驗證（dry-run）..."
# 從 LOCAL_DEPLOY.md 提取所有 shell 指令區塊，確認無語法明顯錯誤
_DEPLOY_MD="docs/LOCAL_DEPLOY.md"
if [[ -f "$_DEPLOY_MD" ]]; then
  _CMD_COUNT=$(grep -c '^\$ \|^nerdctl\|^docker\|^kubectl\|^make ' "$_DEPLOY_MD" 2>/dev/null || echo 0)
  echo "  📋 共偵測到 ${_CMD_COUNT} 個可執行指令"
fi

echo "[F-04] 驗證完成。"
echo "[F-04] ⚠️  若上述有 ❌ 項目，請在提交前修正 LOCAL_DEPLOY.md 中對應指令。"
```

**驗證失敗處理**：
- `k8s/overlays/local/` 不存在 → 在 LOCAL_DEPLOY.md §4.5 加注釋「需先建立 k8s manifest 目錄」（不阻斷生成）
- 環境依賴缺失 → 在 LOCAL_DEPLOY.md §1 Prerequisites 補充安裝說明（不阻斷生成）
- 驗證結果輸出到 stdout，由 gendoc-flow 記錄到 git commit message
