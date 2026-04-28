# LOCAL_DEPLOY — Local Development Deployment Guide (Rancher Desktop + Kubernetes)

---

## Document Control

| Field | Value |
|-------|-------|
| **DOC-ID** | LOCAL_DEPLOY-{{PROJECT_SLUG}}-{{YYYYMMDD}} |
| **Project** | {{PROJECT_NAME}} |
| **Version** | v1.0 |
| **Status** | DRAFT / ACTIVE / DEPRECATED |
| **Author** | {{AUTHOR}} |
| **Date** | {{DATE}} |
| **Upstream EDD** | [EDD.md](EDD.md) |
| **Last Verified** | {{YYYYMMDD}} |
| **Verified By** | {{VERIFIER}} |

---

## 1. Prerequisites

Install and verify every tool before proceeding. The setup will not work without exact version minimums.

| Tool | Min Version | Install | Verify |
|------|------------|---------|--------|
| macOS | 13.0+ | — | `sw_vers -productVersion` |
| **Rancher Desktop** | 1.13 | [rancherdesktop.io](https://rancherdesktop.io) | `rdctl version` |
| kubectl | 1.29 | Bundled with Rancher Desktop | `kubectl version --client` |
| helm | 3.14 | Bundled with Rancher Desktop | `helm version` |
| nerdctl | 1.7 | Bundled with Rancher Desktop | `nerdctl version` |
| k9s（選配）| 0.32 | `brew install k9s` | `k9s version` |
| skaffold（選配）| 2.11 | `brew install skaffold` | `skaffold version` |
| psql client | 15 | `brew install libpq && brew link libpq` | `psql --version` |
| mkcert | 1.4 | `brew install mkcert` | `mkcert --version` |
| Git | 2.40 | `brew install git` | `git --version` |
| Make | 4.3 | `brew install make` | `make --version` |
| curl | 8.0 | Pre-installed | `curl --version` |

> **Rancher Desktop 設定：** 啟動後進入 **Preferences > Virtual Machine > Resources**，至少配置 **8 GB RAM / 4 CPU**。Container engine 選 **containerd**（nerdctl）。
> **kubectl context：** Rancher Desktop 啟動後會自動注入 `rancher-desktop` context。執行 `kubectl config use-context rancher-desktop` 確認。

---

## 2. Architecture Overview

本地環境完全在 Kubernetes 內執行，與 staging / production 採用相同 K8s 資源模型（Deployment、Service、ConfigMap、Secret、Ingress）。開發者透過 Ingress（traefik，k3s 內建）或 `kubectl port-forward` 存取各服務。

**所有服務均在 namespace `{{K8S_NAMESPACE}}-local` 內。**

```
┌────────────────────────────────────────────────────────────────────────┐
│  Rancher Desktop (k3s)  —  namespace: {{K8S_NAMESPACE}}-local          │
│                                                                        │
│  Ingress (traefik)  ← http://{{PROJECT_SLUG}}.local（需設定 /etc/hosts）│
│         │                                                              │
│  ┌──────┴──────┐   ┌──────────────┐   ┌────────────────────────────┐  │
│  │  web-app    │   │  api-server  │   │  worker / cron-scheduler   │  │
│  │ (client)    │   │  :{{API_PORT}}│   │                            │  │
│  │ :{{WEB_PORT}}│   └──────┬───────┘   └────────────┬───────────────┘  │
│  └─────────────┘          │                        │                  │
│                    ┌──────┴──────────────────────── ┘                 │
│                    ▼                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  postgres   │  │  redis      │  │  minio      │  │  mailpit    │  │
│  │ (StatefulSet│  │ (StatefulSet│  │ (S3 local)  │  │ (SMTP trap) │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  pgadmin（DB 瀏覽器）                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

```mermaid
graph TB
    Dev["Developer<br/>(localhost)"]
    Ingress["Ingress (traefik)<br/>{{PROJECT_SLUG}}.local"]

    subgraph K8s["K8s Namespace: {{K8S_NAMESPACE}}-local"]
        Web["web-app (client)\nDeployment\n:{{WEB_PORT}}"]
        API["api-server\nDeployment\n:{{API_PORT}}"]
        Worker["worker\nDeployment"]
        Cron["cron-scheduler\nCronJob"]
        DB[("postgres\nStatefulSet\n:{{DB_PORT}}")]
        Cache[("redis\nStatefulSet\n:{{REDIS_PORT}}")]
        Storage["minio\nDeployment\n:{{MINIO_PORT}}"]
        Mail["mailpit\nDeployment\n:{{MAIL_PORT}}"]
        PGA["pgadmin\nDeployment\n:{{PGADMIN_PORT}}"]
    end

    Dev -->|Ingress / port-forward| Ingress
    Ingress -->|/| Web
    Ingress -->|/api| API
    Dev -->|kubectl port-forward| DB
    Dev -->|kubectl port-forward| Storage
    Dev -->|kubectl port-forward| Mail
    Dev -->|kubectl port-forward| PGA
    Web -->|ClusterIP| API
    API -->|ClusterIP| DB
    API -->|ClusterIP| Cache
    API -->|ClusterIP| Storage
    API -->|ClusterIP| Mail
    Worker -->|ClusterIP| DB
    Worker -->|ClusterIP| Cache
    Worker -->|ClusterIP| Mail
    Cron -->|triggers| Worker
```

**K8s 資源對照：**

| 服務 | Kind | Image | ConfigMap | Secret |
|------|------|-------|-----------|--------|
| web-app | Deployment | `{{PROJECT_SLUG}}/web:local` | `{{PROJECT_SLUG}}-web-config` | — |
| api-server | Deployment | `{{PROJECT_SLUG}}/api:local` | `{{PROJECT_SLUG}}-api-config` | `{{PROJECT_SLUG}}-api-secret` |
| worker | Deployment | `{{PROJECT_SLUG}}/api:local` | `{{PROJECT_SLUG}}-api-config` | `{{PROJECT_SLUG}}-api-secret` |
| cron-scheduler | CronJob | `{{PROJECT_SLUG}}/api:local` | `{{PROJECT_SLUG}}-api-config` | `{{PROJECT_SLUG}}-api-secret` |
| postgres | StatefulSet | `postgres:{{DB_VERSION}}` | — | `{{PROJECT_SLUG}}-db-secret` |
| redis | StatefulSet | `redis:{{CACHE_VERSION}}-alpine` | — | — |
| minio | Deployment | `minio/minio:RELEASE.{{MINIO_TAG}}` | — | `{{PROJECT_SLUG}}-minio-secret` |
| mailpit | Deployment | `axllent/mailpit:latest` | — | — |
| pgadmin | Deployment | `dpage/pgadmin4:latest` | — | `{{PROJECT_SLUG}}-pgadmin-secret` |

> **K8s manifest 位置：** `k8s/overlays/local/`（Kustomize）或 `helm/values-local.yaml`（Helm）。

---

## 3. Quick Start（5 分鐘上手）

適合熟悉 K8s 的工程師。初次設定請使用 Section 4。

```bash
# 1. Clone 並進入專案
git clone git@github.com:{{GITHUB_ORG}}/{{REPO_NAME}}.git
cd {{REPO_NAME}}

# 2. 確認 kubectl context 為 Rancher Desktop
kubectl config use-context rancher-desktop

# 3. 建立 namespace 與基礎 Secret
make k8s-init

# 4. Build 並載入所有 image
make image-build-all

# 5. 部署所有 K8s 資源
make k8s-apply

# 6. 等待所有 Pod 就緒
kubectl wait --for=condition=Ready pods --all -n {{K8S_NAMESPACE}}-local --timeout=180s

# 7. 初始化資料庫（migration + seed）
make db-migrate
make db-seed

# 8. 驗證所有服務健康
make health-check
```

預期輸出：

```
[OK] web-app     http://{{PROJECT_SLUG}}.local
[OK] api-server  http://{{PROJECT_SLUG}}.local/api/health
[OK] postgres    pod/postgres-0 — Running
[OK] redis       pod/redis-0 — Running
[OK] minio       pod/minio — Running
[OK] mailpit     pod/mailpit — Running
```

如有任何 `[FAIL]`，請進入 Section 10（Common Issues）。

---

## 4. Step-by-Step Setup

### 4.1 Clone & Configure

```bash
# Clone repository
git clone git@github.com:{{GITHUB_ORG}}/{{REPO_NAME}}.git
cd {{REPO_NAME}}

# 確認 branch
git status
# Expected: On branch main / develop
```

### 4.2 Rancher Desktop 設定

```bash
# 1. 確認 k3s context 已注入
kubectl config get-contexts
# 應看到 rancher-desktop 並標示 *（current）

# 若未自動設定：
kubectl config use-context rancher-desktop

# 2. 確認 K8s API server 可連線
kubectl cluster-info
# Expected: Kubernetes control plane is running at https://127.0.0.1:6443

# 3. 建立本地 namespace
kubectl create namespace {{K8S_NAMESPACE}}-local --dry-run=client -o yaml | kubectl apply -f -

# 4. 設定 /etc/hosts（一次性）— 讓 Ingress domain 可解析
echo "127.0.0.1   {{PROJECT_SLUG}}.local api.{{PROJECT_SLUG}}.local" | sudo tee -a /etc/hosts
```

### 4.3 建立 K8s Secret

Secret 不走 configmap，不提交到 git。Local 環境全為開發假值，直接從範例複製即可，**無需人工填寫**：

```bash
# 從範例複製（local 假值，不需修改）
[[ ! -f k8s/overlays/local/secrets.env ]] && \
  cp k8s/overlays/local/secrets.example.env k8s/overlays/local/secrets.env

# 建立 K8s Secret（從 secrets.env 讀取）
make k8s-init
# 等同執行：
# kubectl create secret generic {{PROJECT_SLUG}}-api-secret \
#   --from-env-file=k8s/overlays/local/secrets.env \
#   -n {{K8S_NAMESPACE}}-local \
#   --dry-run=client -o yaml | kubectl apply -f -
```

> `k8s/overlays/local/secrets.env` 已加入 `.gitignore`。`secrets.example.env` 是變數名稱的唯一來源，新增變數時需同步更新。

### 4.4 Build & 載入 Image

Rancher Desktop 使用 containerd runtime，需用 nerdctl 建置並直接載入到 k3s 內部 registry（不需額外 push step）。

```bash
# 一次 build 全部 image（api + web-app）
make image-build-all

# 等同：
nerdctl build -t {{PROJECT_SLUG}}/api:local -f docker/api/Dockerfile .
nerdctl build -t {{PROJECT_SLUG}}/web:local -f docker/web/Dockerfile .

# 確認 image 存在
nerdctl images | grep {{PROJECT_SLUG}}
```

> **imagePullPolicy：** 本地環境所有 Deployment 設定 `imagePullPolicy: Never`，確保使用本機 build 的 image，不從 registry 拉取。

### 4.5 部署所有 K8s 資源

```bash
# 使用 Kustomize 部署 local overlay
make k8s-apply
# 等同：
# kubectl apply -k k8s/overlays/local/

# 觀察 Pod 啟動狀態（Ctrl+C 結束）
kubectl get pods -n {{K8S_NAMESPACE}}-local -w

# 等待全部 Ready
kubectl wait --for=condition=Ready pods --all -n {{K8S_NAMESPACE}}-local --timeout=180s
```

預期 Pod 狀態（全部 `Running`）：

```
NAME                          READY   STATUS    RESTARTS   AGE
api-server-<hash>             1/1     Running   0          60s
web-app-<hash>                1/1     Running   0          60s
worker-<hash>                 1/1     Running   0          60s
postgres-0                    1/1     Running   0          60s
redis-0                       1/1     Running   0          60s
minio-<hash>                  1/1     Running   0          60s
mailpit-<hash>                1/1     Running   0          60s
pgadmin-<hash>                1/1     Running   0          60s
```

如有 Pod 停在 `Pending` 或 `CrashLoopBackOff`，請見 Section 10。

### 4.6 初始化資料庫

```bash
# 執行所有 pending migration
make db-migrate
# 等同：
# kubectl exec -n {{K8S_NAMESPACE}}-local deploy/api-server -- {{MIGRATE_CMD}}

# 載入 seed / fixture 資料
make db-seed
# 等同：
# kubectl exec -n {{K8S_NAMESPACE}}-local deploy/api-server -- {{SEED_CMD}}
```

預期 migration 輸出：

```
Running migration 001_create_users...          OK
Running migration 002_create_{{entity}}...     OK
Running migration 003_add_indexes...           OK
All migrations applied. Schema is up to date.
```

### 4.7 驗證所有服務健康

```bash
make health-check
```

個別驗證：

```bash
# Web-app（透過 Ingress）
curl -s -o /dev/null -w "%{http_code}" http://{{PROJECT_SLUG}}.local
# Expected: 200

# API health（透過 Ingress）
curl -s http://{{PROJECT_SLUG}}.local/api/health | jq .
# Expected: {"status":"ok","version":"{{VERSION}}"}

# PostgreSQL（port-forward 後）
kubectl port-forward -n {{K8S_NAMESPACE}}-local statefulset/postgres 5432:5432 &
# ⚠️  WARNING: 密碼 'secret' 僅為本機開發預設值，staging / production 環境禁止使用。
psql "postgres://app:secret@localhost:5432/{{PROJECT_SLUG}}_dev" -c "SELECT 1;"
# Expected: 1 row

# Redis（port-forward 後）
kubectl port-forward -n {{K8S_NAMESPACE}}-local statefulset/redis 6379:6379 &
redis-cli ping
# Expected: PONG
```

---

## 5. Service Reference

### Ingress 存取（需設定 /etc/hosts）

| 服務 | URL | 說明 |
|------|-----|------|
| web-app (client) | `http://{{PROJECT_SLUG}}.local` | 前端應用 |
| api-server | `http://{{PROJECT_SLUG}}.local/api` | REST API |
| mailpit web UI | `http://{{PROJECT_SLUG}}.local/mailpit` | 攔截所有 outgoing email |
| minio console | `http://{{PROJECT_SLUG}}.local/minio-console` | 物件儲存 web UI |
| pgadmin | `http://{{PROJECT_SLUG}}.local/pgadmin` | 資料庫瀏覽器 |

### kubectl port-forward 存取（直連 Pod）

| 服務 | 指令 | 本地 URL |
|------|------|---------|
| api-server | `kubectl port-forward -n {{K8S_NAMESPACE}}-local deploy/api-server {{API_PORT}}:{{API_PORT}}` | `http://localhost:{{API_PORT}}` |
| postgres | `kubectl port-forward -n {{K8S_NAMESPACE}}-local statefulset/postgres {{DB_PORT}}:5432` | `localhost:{{DB_PORT}}` |
| redis | `kubectl port-forward -n {{K8S_NAMESPACE}}-local statefulset/redis {{REDIS_PORT}}:6379` | `localhost:{{REDIS_PORT}}` |
| minio | `kubectl port-forward -n {{K8S_NAMESPACE}}-local deploy/minio {{MINIO_PORT}}:9000` | `http://localhost:{{MINIO_PORT}}` |
| mailpit | `kubectl port-forward -n {{K8S_NAMESPACE}}-local deploy/mailpit {{MAIL_PORT}}:8025` | `http://localhost:{{MAIL_PORT}}` |
| pgadmin | `kubectl port-forward -n {{K8S_NAMESPACE}}-local deploy/pgadmin {{PGADMIN_PORT}}:80` | `http://localhost:{{PGADMIN_PORT}}` |

> **Make shortcuts：** `make pf-api`、`make pf-db`、`make pf-redis` 等會在背景啟動 port-forward 並記錄 PID。`make pf-stop` 停止全部。

---

## 6. Development Commands

所有 `make` 指令從 repo root 執行。

### Image & Deployment

| 指令 | 等同底層命令 | 使用時機 |
|------|------------|---------|
| `make image-build-api` | `nerdctl build -t {{PROJECT_SLUG}}/api:local -f docker/api/Dockerfile .` | 修改後端程式碼後 |
| `make image-build-web` | `nerdctl build -t {{PROJECT_SLUG}}/web:local -f docker/web/Dockerfile .` | 修改前端程式碼後 |
| `make image-build-all` | 依序執行上兩條 `nerdctl build` 命令 | 初次設定或全面更新 |
| `make k8s-apply` | `kubectl apply -k k8s/overlays/local/` | 變更 K8s manifest 後 |
| `make k8s-restart-api` | `kubectl rollout restart deploy/api-server -n {{K8S_NAMESPACE}}-local` | Build 新 image 後套用 |
| `make k8s-restart-web` | `kubectl rollout restart deploy/web-app -n {{K8S_NAMESPACE}}-local` | Build 新 image 後套用 |
| `make k8s-restart-worker` | `kubectl rollout restart deploy/worker -n {{K8S_NAMESPACE}}-local` | Build 新 image 後套用 |
| `make k8s-restart-all` | `kubectl rollout restart deployment --all -n {{K8S_NAMESPACE}}-local` | 更新 ConfigMap / Secret 後 |
| `make k8s-delete` | `kubectl delete -k k8s/overlays/local/` | 重新部署時（保留 PVC）|
| `make k8s-clean` | `kubectl delete namespace {{K8S_NAMESPACE}}-local` | 完全重置（銷毀所有資料）|

### 觀察 & 偵錯

| 指令 | 說明 |
|------|------|
| `make pods` | `kubectl get pods -n {{K8S_NAMESPACE}}-local` |
| `make logs-api` | `kubectl logs -f deploy/api-server -n {{K8S_NAMESPACE}}-local` |
| `make logs-web` | `kubectl logs -f deploy/web-app -n {{K8S_NAMESPACE}}-local` |
| `make logs-worker` | `kubectl logs -f deploy/worker -n {{K8S_NAMESPACE}}-local` |
| `make shell-api` | `kubectl exec -it deploy/api-server -n {{K8S_NAMESPACE}}-local -- sh` |
| `make shell-db` | `kubectl exec -it -n {{K8S_NAMESPACE}}-local statefulset/postgres -- psql -U app -d {{PROJECT_SLUG}}_dev` |
| `make health-check` | 依序執行 `curl -s http://{{PROJECT_SLUG}}.local/api/health`、`kubectl get pods -n {{K8S_NAMESPACE}}-local`（見 §4.7 個別驗證）|
| `make k9s` | `k9s -n {{K8S_NAMESPACE}}-local`（需已安裝 k9s）|

### 測試

| 指令 | 說明 |
|------|------|
| `make test-unit` | 在本機執行 unit test（不需 K8s）— 等同 `{{TEST_UNIT_CMD}}`（由專案定義，如 `npm test` / `pytest` / `go test ./...`）|
| `make test-integration` | `kubectl exec -it deploy/api-server -n {{K8S_NAMESPACE}}-local -- {{TEST_INTEGRATION_CMD}}` |
| `make test-e2e` | 執行 E2E test（Playwright）— 等同 `npx playwright test --base-url http://{{PROJECT_SLUG}}.local` |
| `make lint` | Lint 全部原始碼 — 等同 `{{LINT_CMD}}`（由專案定義，如 `eslint .` / `flake8` / `golangci-lint run`）|

---

## 7. Database Operations

### 進入 psql Shell

> ⚠️ **安全注意：** 下方連線字串中的密碼 `secret` 僅為本機開發預設值，禁止複製至 staging / production 環境。正式環境請從 Vault / Secret Manager 取得憑證。

```bash
# 方法 1：透過 kubectl exec（不需 port-forward）
kubectl exec -it -n {{K8S_NAMESPACE}}-local statefulset/postgres -- \
  psql -U app -d {{PROJECT_SLUG}}_dev

# 方法 2：port-forward 後用本地 psql client
kubectl port-forward -n {{K8S_NAMESPACE}}-local statefulset/postgres {{DB_PORT}}:5432 &
psql "postgres://app:secret@localhost:{{DB_PORT}}/{{PROJECT_SLUG}}_dev"

# Make shortcut
make shell-db
```

### 執行 Migration

```bash
# 執行所有 pending migration
make db-migrate
# 等同：
# kubectl exec -n {{K8S_NAMESPACE}}-local deploy/api-server -- {{MIGRATE_CMD}}

# 查看 migration 狀態
make db-status
# 等同：
# kubectl exec -n {{K8S_NAMESPACE}}-local deploy/api-server -- {{MIGRATE_STATUS_CMD}}

# Rollback 最後一個 migration
make db-rollback
# 等同：
# kubectl exec -n {{K8S_NAMESPACE}}-local deploy/api-server -- {{MIGRATE_ROLLBACK_CMD}}
```

### Seed 測試資料

```bash
# 載入所有 seed（idempotent，可重複執行）
make db-seed

# 載入特定 seed
kubectl exec -n {{K8S_NAMESPACE}}-local deploy/api-server -- \
  {{SEED_CMD}} --file seeds/{{SEED_FILE}}
```

### 重置為乾淨狀態

```bash
# Drop + recreate + migrate + seed（銷毀所有本地資料）
make db-reset
# Warning: PVC 內資料全部清除
```

### Backup / Restore

> ⚠️ **安全注意：** 下方連線字串中的密碼 `secret` 僅為本機開發預設值，禁止複製至 staging / production 環境。

```bash
# Backup（port-forward 後執行）
kubectl port-forward -n {{K8S_NAMESPACE}}-local statefulset/postgres {{DB_PORT}}:5432 &
pg_dump "postgres://app:secret@localhost:{{DB_PORT}}/{{PROJECT_SLUG}}_dev" \
  > backups/local-$(date +%Y%m%d-%H%M%S).sql

# Restore
psql "postgres://app:secret@localhost:{{DB_PORT}}/{{PROJECT_SLUG}}_dev" \
  < backups/local-20240115-093000.sql
```

---

## 8. Test Data & Fixtures

`make db-seed` 後以下帳號與資料固定可用。

### Default User Accounts

| Role | Email | Password | 說明 |
|------|-------|----------|------|
| Admin | `admin@{{PROJECT_SLUG}}.local` | `Password1!` | 全權限 |
| Regular User | `user@{{PROJECT_SLUG}}.local` | `Password1!` | 標準角色 |
| Read-only | `readonly@{{PROJECT_SLUG}}.local` | `Password1!` | 唯讀角色 |
| {{ROLE_NAME}} | `{{role}}@{{PROJECT_SLUG}}.local` | `Password1!` | {{ROLE_DESCRIPTION}} |

### Sample Data

| Entity | Count | 說明 |
|--------|-------|------|
| Users | 10 | 涵蓋所有角色，密碼同上 |
| {{ENTITY_1}} | 50 | 包含所有狀態（active / inactive / archived）|
| {{ENTITY_2}} | 20 | 關聯至 seed users |
| {{ENTITY_3}} | 5 | Edge case：最大欄位長度、特殊字元 |

### pgadmin 登入

- URL：`http://{{PROJECT_SLUG}}.local/pgadmin`（或 port-forward `{{PGADMIN_PORT}}`）
- Email：`admin@{{PROJECT_SLUG}}.local`
- Password：從 `{{PROJECT_SLUG}}-pgadmin-secret` 讀取（預設 `pgadmin-local-secret`，僅本機開發用；如需修改，請更新 `k8s/overlays/local/secrets.env` 並重新執行 `make k8s-init`）
- 新增 Server：Host = `postgres`（K8s service 名稱），Port = `5432`，DB = `{{PROJECT_SLUG}}_dev`

---

## 9. ConfigMap & Secret Reference

### ConfigMap — `{{PROJECT_SLUG}}-api-config`

| Key | Default | 說明 |
|-----|---------|------|
| `NODE_ENV` | `development` | Runtime 環境 |
| `PORT` | `{{API_PORT}}` | API 監聽 port |
| `DATABASE_URL` | `postgres://app:secret@postgres:5432/{{PROJECT_SLUG}}_dev` | PostgreSQL 連線字串（使用 K8s service DNS）|
| `REDIS_URL` | `redis://redis:6379/0` | Redis 連線字串 |
| `LOG_LEVEL` | `debug` | `debug` / `info` / `warn` / `error` |
| `CORS_ORIGINS` | `http://{{PROJECT_SLUG}}.local` | 允許的 CORS origins |
| `STORAGE_ENDPOINT` | `http://minio:9000` | S3-compatible storage URL |
| `STORAGE_BUCKET` | `{{PROJECT_SLUG}}-local` | 預設 bucket 名稱 |
| `SMTP_HOST` | `mailpit` | SMTP server（K8s service DNS）|
| `SMTP_PORT` | `1025` | SMTP port |
| `FEATURE_{{FLAG_NAME}}` | `true` | Feature flag for {{FEATURE_DESCRIPTION}} |

### ConfigMap — `{{PROJECT_SLUG}}-web-config`

| Key | Default | 說明 |
|-----|---------|------|
| `VITE_API_BASE_URL` | `http://{{PROJECT_SLUG}}.local/api` | 前端 API base URL（由 Ingress 路由）|
| `VITE_ENV` | `local` | 環境識別 |
| `{{VITE_OTHER_VAR}}` | `{{DEFAULT}}` | {{DESCRIPTION}} |

### Secret — `{{PROJECT_SLUG}}-api-secret`（從 `k8s/overlays/local/secrets.env` 建立）

| Key | 說明 | 設定方式 |
|-----|------|---------|
| `SECRET_KEY` | JWT signing secret | `secrets.env` |
| `STORAGE_ACCESS_KEY` | MinIO access key | `secrets.env` |
| `STORAGE_SECRET_KEY` | MinIO secret key | `secrets.env` |
| `{{EXTERNAL_API_KEY_VAR}}` | 第三方 API key for {{EXTERNAL_SERVICE}} | `secrets.env`（測試 {{FEATURE}} 時需填入）|

### 查看目前 ConfigMap / Secret

```bash
# 查看 ConfigMap 內容
kubectl get configmap {{PROJECT_SLUG}}-api-config -n {{K8S_NAMESPACE}}-local -o yaml

# 查看 Secret key 清單（值會 base64 遮罩）
kubectl get secret {{PROJECT_SLUG}}-api-secret -n {{K8S_NAMESPACE}}-local -o yaml

# 解碼特定 secret 值
kubectl get secret {{PROJECT_SLUG}}-api-secret -n {{K8S_NAMESPACE}}-local \
  -o jsonpath='{.data.SECRET_KEY}' | base64 -d
```

### 更新 ConfigMap / Secret 並套用

```bash
# 修改 ConfigMap
kubectl edit configmap {{PROJECT_SLUG}}-api-config -n {{K8S_NAMESPACE}}-local
# 或直接重新 apply：
kubectl apply -k k8s/overlays/local/

# 更新後需 rolling restart 才生效
make k8s-restart-all
```

---

## 10. Common Issues & Fixes

| Issue | Symptom | Root Cause | Fix |
|-------|---------|------------|-----|
| Pod stuck in `Pending` | `kubectl get pods` 顯示 Pending | 資源不足或 namespace 未建立 | `kubectl describe pod <name> -n {{K8S_NAMESPACE}}-local` 查看 Events；增加 Rancher Desktop RAM 至 8 GB |
| Pod in `CrashLoopBackOff` | Pod 反覆重啟 | 應用程式啟動失敗（設定錯誤、DB 未就緒）| `kubectl logs <pod> -n {{K8S_NAMESPACE}}-local --previous` 查看上次崩潰日誌 |
| `ImagePullBackOff` | Pod 無法找到 image | image 未 build 或 tag 錯誤 | `nerdctl images \| grep {{PROJECT_SLUG}}`；重新執行 `make image-build-all` |
| Ingress 無法解析 | `curl: Could not resolve host` | /etc/hosts 未設定 | 確認 `/etc/hosts` 有 `127.0.0.1 {{PROJECT_SLUG}}.local` |
| DB 連線拒絕 | api-server log: `ECONNREFUSED postgres` | postgres pod 未就緒 | `kubectl wait --for=condition=Ready pod/postgres-0 -n {{K8S_NAMESPACE}}-local --timeout=60s` |
| Migration 失敗 | `relation already exists` | Migration 被部分執行過 | `make db-reset`（銷毀資料）或手動修正 migration 狀態 |
| Secret 找不到 | Pod 事件：`secret not found` | `make k8s-init` 未執行 | 重新執行 `make k8s-init`；確認 `secrets.env` 已填寫 |
| port-forward 斷線 | `port-forward` 背景 process 結束 | 網路超時或 Pod 重啟 | `make pf-api`（Make 會重新啟動）；或在另一個 terminal 重新執行 |
| Rancher Desktop K8s 未啟動 | `kubectl: connection refused` | k3s 服務未運行 | 開啟 Rancher Desktop GUI，進入 **Kubernetes** 頁面確認已啟用並等待 Ready |
| nerdctl build 失敗（network）| Build 時 `npm install` 連線失敗 | containerd 沙箱 DNS 問題 | 嘗試 `nerdctl build --network=host ...`；或重啟 Rancher Desktop |
| 舊 ConfigMap 未更新 | 修改 configmap 後服務行為未變 | Pod 未重啟，仍用舊版設定 | `make k8s-restart-all` |

---

## 11. Logs & Debugging

### 查看 Pod 日誌

```bash
# 即時 tail 指定服務
kubectl logs -f deploy/api-server -n {{K8S_NAMESPACE}}-local
kubectl logs -f deploy/web-app -n {{K8S_NAMESPACE}}-local
kubectl logs -f deploy/worker -n {{K8S_NAMESPACE}}-local
kubectl logs -f statefulset/postgres -n {{K8S_NAMESPACE}}-local

# Make shortcuts
make logs-api
make logs-web
make logs-worker

# 查看上次 crash 日誌
kubectl logs deploy/api-server -n {{K8S_NAMESPACE}}-local --previous

# 多 container pod（若有 sidecar）
kubectl logs deploy/api-server -n {{K8S_NAMESPACE}}-local -c api-server
```

### 進入 Pod Shell

```bash
# api-server shell
kubectl exec -it deploy/api-server -n {{K8S_NAMESPACE}}-local -- sh
# Make shortcut：
make shell-api

# 查看環境變數（含 ConfigMap + Secret 注入的值）
kubectl exec deploy/api-server -n {{K8S_NAMESPACE}}-local -- env | sort

# 在 pod 內執行一次性指令
kubectl exec deploy/api-server -n {{K8S_NAMESPACE}}-local -- {{RUNTIME_CMD}} --version
```

### 查看 Pod 事件（啟動失敗時最有用）

```bash
kubectl describe pod <pod-name> -n {{K8S_NAMESPACE}}-local
# 重點看 Events 區塊的 Warning 訊息
```

### 常見 Log 模式

| Pattern | 含義 | 處理 |
|---------|------|------|
| `[ERROR] Database connection failed` | postgres pod 未就緒或 DNS 解析失敗 | 確認 postgres pod Running；確認 SERVICE 名稱為 `postgres` |
| `[WARN] Redis connection lost, retrying` | Redis 暫時不可用 | 通常自動恢復；`kubectl get pod redis-0 -n {{K8S_NAMESPACE}}-local` |
| `[ERROR] Migration {{name}} failed` | Migration SQL 異常 | 查看完整錯誤；`make db-rollback` |
| `[INFO] Worker job {{name}} completed` | Background job 正常完成 | 正常，無需處理 |
| `[ERROR] Worker job {{name}} failed after 3 retries` | Job 已耗盡重試次數 | 查看 job 參數；確認外部服務可用 |

### 使用 k9s（推薦）

```bash
# 開啟 k9s，自動切換至 local namespace
k9s -n {{K8S_NAMESPACE}}-local
# 在 k9s 內：
#   :pod   — 查看所有 pod
#   :log   — 查看 log
#   s      — 進入 pod shell
#   d      — describe resource
#   Ctrl+K — 刪除 resource
```

---

## 12. Port Reference

### Ingress（需 /etc/hosts 設定）

| Path | 服務 | 說明 |
|------|------|------|
| `http://{{PROJECT_SLUG}}.local/` | web-app | 前端應用（React/Vue/Next.js 等）|
| `http://{{PROJECT_SLUG}}.local/api` | api-server | REST API（包含 `/api/health`、`/api/docs`）|
| `http://{{PROJECT_SLUG}}.local/mailpit` | mailpit | Email 預覽 UI |
| `http://{{PROJECT_SLUG}}.local/minio-console` | minio console | 物件儲存 web UI |
| `http://{{PROJECT_SLUG}}.local/pgadmin` | pgadmin | 資料庫瀏覽器 |

### port-forward（直連 ClusterIP Service）

| 服務 | 指令 | 本地 Port |
|------|------|---------|
| api-server | `make pf-api` | `{{API_PORT}}` |
| web-app（偵錯用，通常透過 Ingress 存取）| `kubectl port-forward -n {{K8S_NAMESPACE}}-local deploy/web-app {{WEB_PORT}}:{{WEB_PORT}}` | `{{WEB_PORT}}` |
| postgres | `make pf-db` | `{{DB_PORT}}` |
| redis | `make pf-redis` | `{{REDIS_PORT}}` |
| minio (S3 API) | `make pf-minio` | `{{MINIO_PORT}}` |
| mailpit (SMTP web) | `make pf-mail` | `{{MAIL_PORT}}` |
| pgadmin | `make pf-pgadmin` | `{{PGADMIN_PORT}}` |

> 全部 port-forward：`make pf-all`。停止：`make pf-stop`。

---

## 13. Local HTTPS 設定

部分功能需要 HTTPS（OAuth 2.0 回調、`SameSite=Secure` Cookie、Service Worker）。

```bash
# 1. 建立本地 CA（只需執行一次）
mkcert -install

# 2. 為本地 domain 生成憑證
mkcert "{{PROJECT_SLUG}}.local" "*.{{PROJECT_SLUG}}.local"
# 生成 {{PROJECT_SLUG}}.local+1.pem 和 {{PROJECT_SLUG}}.local+1-key.pem

# 3. 建立 K8s TLS Secret
kubectl create secret tls {{PROJECT_SLUG}}-local-tls \
  --cert={{PROJECT_SLUG}}.local+1.pem \
  --key={{PROJECT_SLUG}}.local+1-key.pem \
  -n {{K8S_NAMESPACE}}-local \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. 啟用 HTTPS Ingress（已在 k8s/overlays/local/ 提供，預設 disabled）
# 編輯 k8s/overlays/local/kustomization.yaml，啟用 tls-ingress patch：
# patches:
#   - path: patches/ingress-tls.yaml   # 取消此行註解

kubectl apply -k k8s/overlays/local/
```

OAuth 本地回調設定：

```
https://{{PROJECT_SLUG}}.local/auth/callback
```

---

## 14. Mock Services & External Integration Stubs

第三方服務在本地開發時使用 Mock，避免消耗真實 API 配額。所有 mock service 已包含在 K8s local overlay 內。

| 服務 | 本地替代方案 | K8s Service DNS | 說明 |
|------|-----------|----------------|------|
| Email（SendGrid / SES）| mailpit | `mailpit:1025` | SMTP trap + web UI |
| 物件儲存（S3 / GCS）| minio | `minio:9000` | S3-compatible API |
| 支付（Stripe）| Stripe CLI（`stripe listen`）| — | 在本機執行，webhook 轉發至 api-server |
| SMS（Twilio）| Log mock | — | 輸出到 api-server stdout |
| OAuth Provider | MockOAuth2Server（可選）| `mock-oauth:8080` | 在 k8s/overlays/local/ 啟用 |
| {{CUSTOM_SERVICE}} | {{MOCK_TOOL}} | `{{MOCK_SERVICE_DNS}}` | {{DESCRIPTION}} |

---

## 15. Inner Loop — 快速迭代開發

每次修改程式碼後不需要重建整個環境。

### 後端（api-server / worker）

```bash
# 方法 1：重 build + rolling restart（約 30-60 秒）
make image-build-api && make k8s-restart-api

# 方法 2：使用 skaffold（自動偵測檔案變更，約 10-20 秒）
skaffold dev --profile local
# skaffold 會 watch 原始碼，變更後自動 build + sync + restart
```

### 前端（web-app client）

```bash
# 方法 1：重 build + rolling restart
make image-build-web && make k8s-restart-web

# 方法 2：hot reload（若前端框架支援 HMR）
# 在 k8s/overlays/local/patches/ 的 web-app deployment 已設定 volume mount 至
# 本地 src/ 目錄，配合框架的 dev server 實現 HMR，無需每次 rebuild。
# 啟動 HMR 模式：
make web-dev
# 等同：
# kubectl exec -it deploy/web-app -n {{K8S_NAMESPACE}}-local -- \
#   {{WEB_DEV_CMD}}  # e.g. npm run dev / pnpm dev
```

### 使用 skaffold（完整 inner loop）

`skaffold.yaml` 已設定在 repo root，`local` profile 對應 `k8s/overlays/local/`：

```bash
# 啟動 skaffold watch 模式（Ctrl+C 停止）
skaffold dev --profile local

# 一次性 build + deploy（不 watch）
skaffold run --profile local

# 清除 skaffold 部署的資源
skaffold delete --profile local
```

---

## 16. Cleanup

### 停止 port-forward

```bash
make pf-stop
```

### 刪除所有 K8s 資源（保留 PVC 資料）

```bash
make k8s-delete
# 等同：
kubectl delete -k k8s/overlays/local/
```

### 完全重置（刪除所有資源 + 資料）

```bash
make k8s-clean
# 等同：
kubectl delete namespace {{K8S_NAMESPACE}}-local
# Warning: 所有 PVC（資料庫、minio 資料）永久刪除
```

### 重建本地環境

```bash
make k8s-clean && make k8s-init && make image-build-all && make k8s-apply && \
  kubectl wait --for=condition=Ready pods --all -n {{K8S_NAMESPACE}}-local --timeout=180s && \
  make db-migrate && make db-seed
```

### 確認清除乾淨

```bash
kubectl get namespace {{K8S_NAMESPACE}}-local
# Expected: Error from server (NotFound)

nerdctl images | grep {{PROJECT_SLUG}}
# 若需清除 local image：
nerdctl rmi {{PROJECT_SLUG}}/api:local {{PROJECT_SLUG}}/web:local
```

---

## 17. Tunnel Access（單一對外 Port，AI 可測試模式）

所有服務均透過同一個 Ingress（port 80）路由，tunnel 只需暴露一個 port。

### ngrok（推薦）

```bash
# 安裝（一次性）
brew install ngrok

# 啟動 tunnel → Ingress port 80
ngrok http 80 --host-header={{PROJECT_SLUG}}.local

# 輸出範例：
# Forwarding  https://a1b2c3d4.ngrok-free.app -> http://localhost:80
# 記錄此 URL，後續測試步驟使用 _TUNNEL_URL
_TUNNEL_URL="https://a1b2c3d4.ngrok-free.app"
```

### Cloudflare Tunnel（無公開 URL 限制）

```bash
# 安裝 cloudflared（一次性）
brew install cloudflared

# 快速 tunnel（dev mode，無需帳號）
cloudflared tunnel --url http://localhost:80

# 輸出範例：
# https://random-name.trycloudflare.com
_TUNNEL_URL="https://random-name.trycloudflare.com"
```

### 設定 Ingress Host header（ngrok / tunnel 需）

Ingress 預設只接受 `{{PROJECT_SLUG}}.local`，tunnel 需額外設定：

```bash
# 方法 1：啟動 ngrok 時加 --host-header（推薦）
ngrok http 80 --host-header={{PROJECT_SLUG}}.local

# 方法 2：Ingress 加 wildcard host（更彈性）
# 編輯 k8s/overlays/local/patches/ingress-tunnel.yaml：
# spec.rules[0].host: ""  # 空字串 = 接受所有 host
kubectl apply -k k8s/overlays/local/
```

### 驗證 Tunnel 可存取

```bash
# 前端 UI 可存取（HTTP 200）
curl -s -o /dev/null -w "%{http_code}" "${_TUNNEL_URL}/"
# Expected: 200

# API health 可存取
curl -s "${_TUNNEL_URL}/api/health" | jq .
# Expected: {"status":"ok","version":"{{VERSION}}"}

# 開啟瀏覽器測試前端
open "${_TUNNEL_URL}"
```

---

## 18. AI Agent Quick Start

AI 代理可執行以下完整腳本，從零啟動完整本地環境並驗證前端可存取，**無需任何人工介入**。

```bash
#!/usr/bin/env bash
# ai-quickstart.sh — AI 一鍵啟動 {{PROJECT_NAME}} 本地 K8s 環境
set -e

echo "=== [1/6] 確認 kubectl context ==="
kubectl config use-context rancher-desktop
kubectl cluster-info

echo "=== [2/6] 初始化 namespace + Secret（自動從 example 建立 local 假值）==="
# local 環境全為開發假值，直接從範例複製，無需人工填寫
[[ ! -f k8s/overlays/local/secrets.env ]] && \
  cp k8s/overlays/local/secrets.example.env k8s/overlays/local/secrets.env
make k8s-init

echo "=== [3/6] 建置所有 Image ==="
make image-build-all

echo "=== [4/6] 部署所有 K8s 資源 ==="
make k8s-apply
kubectl wait --for=condition=Ready pods --all \
  -n {{K8S_NAMESPACE}}-local --timeout=300s

echo "=== [5/6] 初始化資料庫 ==="
make db-migrate
make db-seed

echo "=== [6/6] 驗證環境健康 ==="
make health-check

echo ""
echo "✅ {{PROJECT_NAME}} 本地環境已就緒"
echo "   前端 UI  → http://{{PROJECT_SLUG}}.local"
echo "   API      → http://{{PROJECT_SLUG}}.local/api/health"
echo ""
echo "如需 Tunnel 存取（AI 測試 / ngrok）："
echo "  ngrok http 80 --host-header={{PROJECT_SLUG}}.local"
```

> **AI 測試前端的完整流程**：執行 `ai-quickstart.sh` → 啟動 ngrok tunnel → 使用 Playwright 開啟 `_TUNNEL_URL` 驗證前端頁面可見、主要功能可操作（見 `features/client/*.feature`）。

---

## 19. Docker Compose（輔助方案）

> **定位**：Docker Compose 是 K8s 的**輔助工具**，非主要部署方式。用於以下場景：
> - 不需要 K8s 完整功能時的快速驗證（如單純測試 API 回應）
> - CI 環境中的輕量 integration test
> - 開發者偏好 Docker Compose 作為入門門檻較低的初次了解環境
>
> **所有功能與行為必須與 K8s 環境一致**；如有差異，以 K8s 為準。

### 服務對照

| K8s Deployment | Docker Compose Service | Image |
|---------------|----------------------|-------|
| api-server | `api` | `{{PROJECT_SLUG}}/api:local` |
| web-app | `web` | `{{PROJECT_SLUG}}/web:local` |
| worker | `worker` | `{{PROJECT_SLUG}}/api:local` |
| postgres | `db` | `postgres:{{DB_VERSION}}` |
| redis | `cache` | `redis:{{CACHE_VERSION}}-alpine` |
| minio | `storage` | `minio/minio` |
| mailpit | `mail` | `axllent/mailpit` |

### 啟動步驟

```bash
# 1. 確認 Docker 執行中（Rancher Desktop container engine 即可）
docker info

# 2. 建置所有 image
docker compose build

# 3. 啟動所有服務（背景執行）
docker compose up -d

# 4. 確認所有容器啟動
docker compose ps
# Expected: 所有服務 Status = "Up" / "running"

# 5. 初始化資料庫
docker compose exec api {{MIGRATE_CMD}}
docker compose exec api {{SEED_CMD}}

# 6. 驗證 API 健康
curl -s http://localhost:{{API_PORT}}/health | jq .
# Expected: {"status":"ok","version":"{{VERSION}}"}

# 7. 驗證前端（若有 web-app）
curl -s -o /dev/null -w "%{http_code}" http://localhost:{{WEB_PORT}}
# Expected: 200
```

### 對外 Port（docker-compose 模式）

| 服務 | 本地 Port | 說明 |
|------|---------|------|
| web-app | `{{WEB_PORT}}` | 前端應用 |
| api-server | `{{API_PORT}}` | REST API |
| postgres | `{{DB_PORT}}` | DB（直連）|
| redis | `{{REDIS_PORT}}` | Cache（直連）|
| minio | `{{MINIO_PORT}}` | 物件儲存 |
| mailpit | `{{MAIL_PORT}}` | Email 預覽 UI |

> **注意**：docker-compose 模式無 Ingress，各服務各自對外暴露 port，與 K8s 單一 port 80 不同。這是兩者唯一的架構差異。

### 測試（docker-compose 模式）

```bash
# Unit test（不需 Docker，直接在本機執行）
{{TEST_UNIT_CMD}}

# Integration test（在 api container 內執行）
docker compose exec api {{TEST_INTEGRATION_CMD}}

# E2E test（Playwright，連 web-app container）
npx playwright test --base-url http://localhost:{{WEB_PORT}}
```

### 停止與清除

```bash
# 停止（保留資料）
docker compose stop

# 停止並移除 container（保留 volume 資料）
docker compose down

# 完全重置（移除 container + volume）
docker compose down -v
# Warning: 所有 DB、minio 資料永久刪除
```
