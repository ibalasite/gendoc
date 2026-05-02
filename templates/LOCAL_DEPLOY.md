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
| k9s（選配）| ≥ 0.32 | macOS/Linux: `brew install derailed/k9s/k9s`<br>Windows: `choco install k9s` 或 `scoop install k9s` | `k9s version` |
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

### 2.1 Bounded Context 子系統拆解對照（Spring Modulith HC-1）

本地環境以 **Modular Monolith** 方式部署，所有 BC（Bounded Context）共用同一個 api-server Deployment。  
各 BC 在 **程式碼層** 已完全隔離（HC-1 Schema Ownership、HC-2 Public Interface），  
可隨時將任一 BC 獨立拉出為微服務（見 §4.5 單一子系統啟動驗證）。

| BC（子系統）| Spring Module Path | 擁有的 DB Schema | Public API Prefix | 發布的 Event Topics |
|------------|-------------------|-----------------|-------------------|-------------------|
| member | `com.{{PROJECT_SLUG}}.member` | `{{PROJECT_SLUG}}_member` | `/api/v*/members` | `member.account.*` |
| wallet | `com.{{PROJECT_SLUG}}.wallet` | `{{PROJECT_SLUG}}_wallet` | `/api/v*/wallets` | `wallet.balance.*` |
| deposit | `com.{{PROJECT_SLUG}}.deposit` | `{{PROJECT_SLUG}}_deposit` | `/api/v*/deposits` | `deposit.transaction.*` |
| lobby | `com.{{PROJECT_SLUG}}.lobby` | `{{PROJECT_SLUG}}_lobby` | `/api/v*/lobby` | `lobby.session.*` |
| game | `com.{{PROJECT_SLUG}}.game` | `{{PROJECT_SLUG}}_game` | `/api/v*/games` | `game.round.*` |

> 若子系統不同，請對照 EDD §3.4 Bounded Context Map 更新此表。

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

## 3.5 Secret Bootstrap（密碼安全管理）

> **原則**：所有 K8s Secret **禁止進 git**。禁止使用靜態明文密碼（如 `password: secret`）。本節定義三層密碼策略，確保本地開發環境的安全性符合企業標準。

### 禁止規則

以下檔案 **必須** 加入 `.gitignore`，違規者視為安全事故：

```gitignore
# Secret files — never commit
*.env
.env
.env.*
secrets.env
k8s/overlays/local/secrets.env
scripts/bootstrap-secrets.sh.local
```

### 三層 Secret 策略

| 層 | 類型 | 適用密碼 | 管理方式 |
|----|------|---------|---------|
| **層 1** | Ephemeral（每次重生成） | DB password、Redis AUTH、JWT secret、Admin init password | 每次 `make k8s-init` 或 `make secrets-rotate` 重生成 |
| **層 2** | OS Keychain（固定憑證） | Docker Hub token、npm/Maven private registry token | macOS Keychain / Windows Credential Manager |
| **層 3** | Enterprise Password Manager（可選） | OAuth client secret、API keys | 1Password `op inject` 或 Bitwarden Secrets Manager |

---

### 層 1：Ephemeral 密碼 Bootstrap（必做）

每次重啟 cluster 或執行 `make k8s-clean` 後，執行以下 bootstrap script 重新生成所有密碼：

**macOS / Linux：**

```bash
# scripts/bootstrap-secrets.sh
#!/usr/bin/env bash
# Auto-generate ephemeral K8s secrets — never commit this output
set -euo pipefail

NAMESPACE="{{K8S_NAMESPACE}}-local"

echo "[bootstrap-secrets] Generating ephemeral secrets for namespace: ${NAMESPACE}"

# Ensure namespace exists
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Delete existing secrets to force regeneration
kubectl delete secret app-secrets -n "${NAMESPACE}" --ignore-not-found

# Generate and apply
kubectl create secret generic app-secrets \
  -n "${NAMESPACE}" \
  --from-literal=DB_PASSWORD="$(openssl rand -hex 32)" \
  --from-literal=REDIS_AUTH="$(openssl rand -hex 32)" \
  --from-literal=JWT_SECRET="$(openssl rand -hex 64)" \
  --from-literal=ADMIN_INIT_PASSWORD="$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -hex 32)"

echo "[bootstrap-secrets] ✅ Ephemeral secrets created in ${NAMESPACE}"
echo "[bootstrap-secrets] ⚠️  Secrets are ephemeral — regenerated on every cluster restart"
```

```bash
# 每次 cluster 啟動時執行
chmod +x scripts/bootstrap-secrets.sh
./scripts/bootstrap-secrets.sh

# 或透過 make target（§6 Development Commands 需加入此 target）
make secrets-rotate
```

**Windows（PowerShell）：**

```powershell
# scripts/bootstrap-secrets.ps1
# Auto-generate ephemeral K8s secrets — never commit this output
param(
    [string]$Namespace = "{{K8S_NAMESPACE}}-local"
)

Write-Host "[bootstrap-secrets] Generating ephemeral secrets for namespace: $Namespace"

# Ensure namespace exists
kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -

# Delete existing secrets
kubectl delete secret app-secrets -n $Namespace --ignore-not-found

# Helper: generate random hex string
function New-RandomHex([int]$bytes) {
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes_arr = New-Object byte[] $bytes
    $rng.GetBytes($bytes_arr)
    return ([System.BitConverter]::ToString($bytes_arr) -replace '-','').ToLower()
}

# Generate and apply
kubectl create secret generic app-secrets `
    -n $Namespace `
    --from-literal="DB_PASSWORD=$(New-RandomHex 32)" `
    --from-literal="REDIS_AUTH=$(New-RandomHex 32)" `
    --from-literal="JWT_SECRET=$(New-RandomHex 64)" `
    --from-literal="ENCRYPTION_KEY=$(New-RandomHex 32)" `
    --from-literal="ADMIN_INIT_PASSWORD=$(New-RandomHex 16)"

Write-Host "[bootstrap-secrets] ✅ Ephemeral secrets created in $Namespace"
Write-Host "[bootstrap-secrets] ⚠️  Secrets are ephemeral — regenerated on every cluster restart"
```

```powershell
# 執行
.\scripts\bootstrap-secrets.ps1
# 或指定 namespace
.\scripts\bootstrap-secrets.ps1 -Namespace "{{K8S_NAMESPACE}}-local"
```

**重生成時機：**

```bash
# 每次執行以下任何一個動作後，必須重跑 bootstrap script
make k8s-clean        # 刪除 namespace（所有 secret 一起被刪）
make cluster-reset    # 完全重建 cluster
make secrets-rotate   # 主動輪換（安全需求或 secret 洩漏後）
```

---

### 層 2：OS Keychain 固定憑證（視需求）

適用於**不能每次重生成**的憑證，例如 Docker Hub token、npm private registry token。

**macOS Keychain（`security` CLI）：**

```bash
# 儲存憑證到 macOS Keychain（首次設定）
security add-generic-password \
  -s "{{PROJECT_SLUG}}-registry" \
  -a "dev" \
  -w "<YOUR_DOCKER_HUB_TOKEN>"

# 讀取憑證並登入（bootstrap script 中使用）
REGISTRY_TOKEN=$(security find-generic-password -w -s "{{PROJECT_SLUG}}-registry" -a "dev")
echo "${REGISTRY_TOKEN}" | docker login --username {{DOCKER_HUB_USERNAME}} --password-stdin

# 儲存 npm registry token
security add-generic-password \
  -s "{{PROJECT_SLUG}}-npm-token" \
  -a "dev" \
  -w "<YOUR_NPM_TOKEN>"
```

**Windows Credential Manager（PowerShell）：**

```powershell
# 需安裝 CredentialManager 模組（一次性安裝）
Install-Module -Name CredentialManager -Force

# 儲存憑證（首次設定）
New-StoredCredential -Target "{{PROJECT_SLUG}}-registry" -UserName "dev" -Password "<YOUR_DOCKER_HUB_TOKEN>"

# 讀取憑證
$cred = Get-StoredCredential -Target "{{PROJECT_SLUG}}-registry"
$token = $cred.GetNetworkCredential().Password
echo $token | docker login --username {{DOCKER_HUB_USERNAME}} --password-stdin
```

---

### 層 3：mittwald/kubernetes-secret-generator（進階選項）

如果偏好 **in-cluster 全自動生成**（無需手動執行 bootstrap script）：

```bash
# 安裝 mittwald/kubernetes-secret-generator
helm repo add mittwald https://helm.mittwald.de
helm upgrade --install secret-generator mittwald/kubernetes-secret-generator \
  -n kube-system

# 在 Secret manifest 中加入 annotation 即可自動生成
```

```yaml
# k8s/overlays/local/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: {{K8S_NAMESPACE}}-local
  annotations:
    # mittwald/kubernetes-secret-generator 自動填入隨機值
    secret-generator.v1.mittwald.de/autogenerate: "DB_PASSWORD,REDIS_AUTH,JWT_SECRET,ENCRYPTION_KEY"
    secret-generator.v1.mittwald.de/length: "64"
    secret-generator.v1.mittwald.de/type: "string"
type: Opaque
```

> **注意**：mittwald/secret-generator 適合不需要在 bootstrap script 中讀取密碼的場景（如 app 直接從 K8s Secret 讀取）。若需要在腳本中取得生成的密碼值，層 1（openssl rand）更直接。

---

### 驗證 Secret 已正確建立

```bash
# 確認 secret 存在（不顯示值）
kubectl get secret app-secrets -n {{K8S_NAMESPACE}}-local

# 確認所有 key 都存在
kubectl get secret app-secrets -n {{K8S_NAMESPACE}}-local -o jsonpath='{.data}' | python3 -c "
import sys, json
keys = list(json.load(sys.stdin).keys())
required = ['DB_PASSWORD', 'REDIS_AUTH', 'JWT_SECRET', 'ENCRYPTION_KEY', 'ADMIN_INIT_PASSWORD']
missing = [k for k in required if k not in keys]
print('Missing:', missing) if missing else print('✅ All required secrets present')
"

# 確認 .gitignore 涵蓋 secret 檔案
grep -E '\.env|secrets\.env' .gitignore && echo "✅ .gitignore OK" || echo "❌ .gitignore missing secret patterns"
```

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

> **客戶端引擎特定 Build 說明**（依 EDD §3.3「客戶端引擎（若有）」欄位）：
>
> | 引擎類型 | Dockerfile 策略 | `make image-build-web` 前置步驟 |
> |---------|----------------|-------------------------------|
> | Web / HTML5 / Phaser | multi-stage：`node build` → `dist/` → nginx serve | 無，直接執行 `make image-build-web` |
> | Cocos Creator | multi-stage：`node + cocos CLI build` → `build/web-mobile/` → nginx serve | 無，Dockerfile 內含 Cocos CLI build |
> | Unity WebGL | 單 stage：COPY Unity build 產出 → nginx serve | **必須先在 Unity Editor 完成 Build**（File > Build Settings > WebGL > Build，輸出至 `Assets/Builds/WebGL/`），再執行 `make image-build-web` |
>
> Unity WebGL build 不在 Dockerfile 內執行（需 Unity License + Editor）；CI 環境需使用 `unity-ci` runner image。

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

> Local 環境 API Server 維持 ≥ 2 replica，用以測試 HA 程式邏輯（共享 Session、distributed lock、pub/sub 等）。詳見 EDD §3.7 圖 B。

```
NAME                          READY   STATUS    RESTARTS   AGE
api-server-<hash1>            1/1     Running   0          60s
api-server-<hash2>            1/1     Running   0          60s
web-app-<hash>                1/1     Running   0          60s
worker-<hash1>                1/1     Running   0          60s
worker-<hash2>                1/1     Running   0          60s
postgres-0                    1/1     Running   0          60s
postgres-1                    1/1     Running   0          60s
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

### 4.8 單一子系統獨立啟動驗證（Spring Modulith Decomposability Test）

此步驟驗證每個 Bounded Context 可以在其他 BC 完全不運行的情況下獨立冷啟動，  
這是確認微服務可拆解性（HC-2 / HC-4）的本地快速驗證手段。

> **何時執行：** (1) 新增跨 BC 依賴前 (2) 每週架構守護 CI (3) BC 提取前的可行性確認

```bash
# 啟動基礎設施（DB、Redis）但不啟動其他 BC 的 API
make k8s-apply-infra        # 僅部署 postgres, redis, minio, mailpit

# 啟動單一 BC（其他 BC 以 WireMock stub 替代）
make k8s-apply-bc BC=member
# 等同：
# kubectl apply -k k8s/overlays/local-bc-member/
# （此 overlay 只包含 member BC Deployment + 其依賴 BC 的 WireMock stub）

# 驗證 member BC 獨立健康
curl -s http://{{PROJECT_SLUG}}.local/api/health | jq '.subsystems.member'
# Expected: {"status":"up","schema":"{{PROJECT_SLUG}}_member"}

# 執行單一 BC 的整合測試（其他 BC 為 stub）
make test-integration-bc BC=member
# Expected: 所有 member BC 測試通過；跨 BC 呼叫命中 WireMock stub（HTTP 200 mock response）

# 清理
make k8s-delete-bc BC=member
```

**各 BC 獨立啟動指令對照：**

| BC | 啟動指令 | Stub 替代的其他 BC | 健康檢查 URL |
|----|---------|-------------------|------------|
| member | `make k8s-apply-bc BC=member` | wallet, deposit, lobby, game | `/api/health?bc=member` |
| wallet | `make k8s-apply-bc BC=wallet` | member, deposit, lobby, game | `/api/health?bc=wallet` |
| deposit | `make k8s-apply-bc BC=deposit` | member, wallet, lobby, game | `/api/health?bc=deposit` |
| lobby | `make k8s-apply-bc BC=lobby` | member, wallet, game | `/api/health?bc=lobby` |
| game | `make k8s-apply-bc BC=game` | member, wallet, lobby | `/api/health?bc=game` |

> **Stub 設定位置：** `k8s/overlays/local-bc-<bc_name>/wiremock-<dep_bc>.yaml`  
> WireMock mapping 格式：`src/test/resources/wiremock/<dep_bc>/**/*.json`（與 Pact Consumer test 共用 stub 定義）

---

## 5. Service Reference

### Ingress 存取（需設定 /etc/hosts）

| 服務 | URL | 說明 |
|------|-----|------|
| web-app (client) | `http://{{PROJECT_SLUG}}.local` | 前端應用（/ 路徑） |
| api-server | `http://{{PROJECT_SLUG}}.local/api` | REST API |
| admin-app（若 has_admin_backend=true）| `http://{{PROJECT_SLUG}}.local/admin` | Admin 後台 SPA（/admin 路徑）|
| mailpit web UI | `http://{{PROJECT_SLUG}}.local/mailpit` | 攔截所有 outgoing email |
| minio console | `http://{{PROJECT_SLUG}}.local/minio-console` | 物件儲存 web UI |
| pgadmin | `http://{{PROJECT_SLUG}}.local/pgadmin` | 資料庫瀏覽器 |

> **Admin SPA 路由重要限制（has_admin_backend=true 時必讀）：**  
> Admin 前端打包時 **必須**設定 `base: '/admin/'`（Vite）或 `PUBLIC_URL=/admin`（CRA）。  
> Ingress 必須對 `/admin` 路徑配置 nginx SPA fallback（所有子路徑回傳 `/admin/index.html`），  
> 否則 Admin SPA 在 deep link reload 時會 404。詳見下方 §5 Ingress YAML 片段。

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

### Admin SPA Ingress 設定（has_admin_backend=true 時必填）

當專案有 Admin 後台前端時，K8s Ingress 必須正確路由 `/admin` 路徑並支援 SPA deep link reload。

**`k8s/overlays/local/ingress.yaml`（含 admin 路徑的完整 Ingress 設定）：**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{PROJECT_SLUG}}-local
  namespace: {{K8S_NAMESPACE}}-local
  annotations:
    # k3s 內建 traefik；若使用 nginx-ingress，改為 nginx.ingress.kubernetes.io/
    traefik.ingress.kubernetes.io/router.entrypoints: web
    # Admin SPA fallback：/admin/* 所有路徑回傳 /admin/index.html（支援 deep link reload）
    nginx.ingress.kubernetes.io/configuration-snippet: |
      location /admin {
        try_files $uri $uri/ /admin/index.html;
      }
spec:
  ingressClassName: traefik
  rules:
    - host: {{PROJECT_SLUG}}.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-server-svc
                port:
                  number: {{API_PORT}}
          - path: /admin
            pathType: Prefix
            backend:
              service:
                name: admin-app-svc
                port:
                  number: {{ADMIN_PORT}}
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-app-svc
                port:
                  number: {{WEB_PORT}}
```

> **Traefik 版本注意：** k3s 內建 Traefik 不支援 `configuration-snippet` annotation。  
> 若使用 Traefik，SPA fallback 需透過 `Middleware` + `IngressRoute` 實作，  
> 或將 Admin SPA nginx container 的 `nginx.conf` 加入 `try_files $uri $uri/ /admin/index.html;`（推薦）。

**Admin SPA nginx.conf（admin-app container 內建，支援 base path `/admin/`）：**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA deep link fallback（配合 base: '/admin/' 打包設定）
    location /admin {
        try_files $uri $uri/ /admin/index.html;
    }

    # 健康檢查（K8s liveness / readiness probe）
    location /healthz {
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

**Admin 前端打包設定（必須與 Ingress base path 一致）：**

```ts
// vite.config.ts（Admin SPA）
export default defineConfig({
  base: '/admin/',   // 必須與 Ingress /admin 路徑一致；若改為其他路徑，nginx.conf 須同步更新
  // ...
})
```

**驗證 Admin SPA Ingress 正確性：**

```bash
# 1. 驗證 /admin 根路徑可存取
curl -s -o /dev/null -w "%{http_code}" http://{{PROJECT_SLUG}}.local/admin/
# Expected: 200

# 2. 驗證 deep link reload（SPA 子路徑）
curl -s -o /dev/null -w "%{http_code}" http://{{PROJECT_SLUG}}.local/admin/users/123
# Expected: 200（不得回傳 404）

# 3. 驗證靜態資源路徑正確（必須含 /admin/ 前綴）
curl -s http://{{PROJECT_SLUG}}.local/admin/ | grep -o 'src="/admin/[^"]*"' | head -3
# Expected: src="/admin/assets/index-xxx.js" 等（不得出現 src="/assets/xxx.js"）
```

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

### 子系統隔離測試（Spring Modulith HC-1/HC-2）

| 指令 | 說明 |
|------|------|
| `make k8s-apply-infra` | 只啟動基礎設施（DB / Redis），不啟動任何 BC |
| `make k8s-apply-bc BC=<bc_name>` | 啟動指定 BC，其他 BC 以 WireMock stub 替代（見 §4.8）|
| `make k8s-delete-bc BC=<bc_name>` | 移除指定 BC 的 K8s 資源 |
| `make test-integration-bc BC=<bc_name>` | 執行指定 BC 的整合測試（其他 BC 為 stub）|
| `make test-pact-consumer` | 執行所有 Pact Consumer 測試（記錄 interaction）|
| `make test-pact-provider BC=<bc_name>` | 執行指定 BC 的 Pact Provider 驗證 |
| `make test-schema-isolation` | 執行跨 BC SQL 違規掃描（HC-1）— 應輸出 `cross_bc_queries: 0` |
| `make dag-check` | 驗證 Spring Modulith 模組依賴 DAG 無循環（HC-5）— 等同 `./mvnw test -Dtest=ModulithDAGTest` |

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

### 14.1 跨 BC 內部 Stub（Spring Modulith HC-2 驗證）

當只開發某個 BC 時，其他 BC 的 Public API 以 **WireMock stub** 替代，  
確保開發者不需要啟動全部子系統、同時確保程式碼只透過 Public API 呼叫（HC-2）。

**WireMock stub 設定方式：**

```
src/test/resources/wiremock/
  member/
    get-member-by-id.json      ← stub: GET /api/v1/members/{id}
    member-login.json          ← stub: POST /api/v1/members/login
  wallet/
    get-balance.json           ← stub: GET /api/v1/wallets/{memberId}/balance
    deduct.json                ← stub: POST /api/v1/wallets/deduct
  deposit/
    create-deposit.json        ← stub: POST /api/v1/deposits
  ...
```

**WireMock stub 範本（`get-member-by-id.json`）：**

```json
{
  "request": {
    "method": "GET",
    "urlPathPattern": "/api/v1/members/([0-9]+)"
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "jsonBody": {
      "id": "{{request.pathSegments.2}}",
      "username": "stub_user",
      "status": "ACTIVE"
    }
  }
}
```

**K8s WireMock Deployment（`k8s/overlays/local-bc-<bc_name>/wiremock-<dep_bc>.yaml`）：**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wiremock-<dep_bc>
  namespace: {{K8S_NAMESPACE}}-local
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: wiremock
          image: wiremock/wiremock:3.x
          args:
            - --root-dir=/home/wiremock
            - --port=8080
          volumeMounts:
            - name: stubs
              mountPath: /home/wiremock/mappings
      volumes:
        - name: stubs
          configMap:
            name: wiremock-<dep_bc>-stubs
---
apiVersion: v1
kind: Service
metadata:
  name: <dep_bc>-svc          # 與正式 service 同名，呼叫方零配置切換
  namespace: {{K8S_NAMESPACE}}-local
spec:
  selector:
    app: wiremock-<dep_bc>
  ports:
    - port: {{DEP_BC_PORT}}
      targetPort: 8080
```

> **重要：** WireMock Service 名稱必須與正式 BC Service 相同（`<dep_bc>-svc`），  
> 呼叫方程式碼不需任何修改即可在 stub / 真實 BC 之間切換（HC-2 的 Public API 封裝效益）。

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

### 前端（Web / HTML5 / Phaser client）

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

### 前端（Cocos Creator client）

Cocos Creator 支援 CLI build，整合在 Dockerfile multi-stage 內：

```bash
# 方法 1：Dockerfile 內含 cocos build，直接 rebuild image（約 60-120 秒）
make image-build-web && make k8s-restart-web

# 方法 2（開發迭代）：Cocos Editor 內建「預覽」在 localhost 驗證邏輯，確認後再部署 k8s
# Cocos Editor → 點擊「預覽」→ http://localhost:7456

# 方法 3：手動 CLI build
npx cocos-creator build --platform web-mobile --output-dir build/web-mobile
make image-build-web && make k8s-restart-web
```

### 前端（Unity WebGL client）

Unity WebGL 無 HMR，每次改動需重新 build：

```bash
# 步驟 1：在 Unity Editor 執行 WebGL Build
# File > Build Settings > 選 WebGL > 點 Build
# 輸出目錄：Assets/Builds/WebGL/

# 步驟 2（可選）：命令列 build（CI 或無 GUI 環境）
UNITY_PATH="/Applications/Unity/Hub/Editor/{{CLIENT_ENGINE_VERSION}}/Unity.app/Contents/MacOS/Unity"
"$UNITY_PATH" -batchmode -quit \
  -projectPath "$(pwd)" \
  -buildTarget WebGL \
  -customBuildPath "Assets/Builds/WebGL"

# 步驟 3：Build image 並套用至 k8s
make image-build-web && make k8s-restart-web
```

> **Unity inner loop 建議**：用 Unity Editor Play Mode 驗證邏輯（不需 k8s），
> 全量 WebGL build 約 2–10 分鐘，只在需要確認 WebGL 特定行為時才走完整 build。

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

> **注意**：docker-compose 模式預設各服務各自對外暴露 port。如需與 K8s 一致的單一 port 80 模式，  
> 需額外加入 nginx reverse proxy 容器（見下方 §19.1 單一 port nginx proxy 方案）。

### 19.1 Docker Compose 單一 Port Nginx Proxy（整合 client + admin + api）

此方案讓 Docker Compose 模式與 K8s Ingress 行為完全一致：對外只暴露 port 80，  
適合分享測試連結（AI agent 測試 / QA 驗收 / 跨團隊協作）。

**`docker/nginx-proxy/nginx.conf`：**

```nginx
# docker/nginx-proxy/nginx.conf
# 單一對外 port 80；路由規則與 K8s Ingress 保持一致

events { worker_connections 1024; }

http {
    upstream api_backend {
        server api:{{API_PORT}};
    }

    upstream web_frontend {
        server web:{{WEB_PORT}};
    }

    # admin upstream（has_admin_backend=true 時啟用）
    upstream admin_frontend {
        server admin:{{ADMIN_PORT}};
    }

    server {
        listen 80;
        server_name localhost;

        # API 路由
        location /api/ {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Admin SPA（has_admin_backend=true 時啟用）
        location /admin {
            proxy_pass http://admin_frontend;
            proxy_set_header Host $host;
            # SPA fallback：nginx proxy 無法直接 try_files，由 admin container 自身 nginx 處理
            proxy_intercept_errors on;
            error_page 404 = /admin/index.html;
        }

        # Client SPA（/ 根路徑，所有非 /api / /admin 的請求）
        location / {
            proxy_pass http://web_frontend;
            proxy_set_header Host $host;
        }
    }
}
```

**`docker-compose.yml`（新增 nginx proxy service）：**

```yaml
services:
  # ... 現有 services（api, web, db, cache 等）...

  # 單一 port nginx proxy（與 K8s Ingress 行為一致）
  proxy:
    image: nginx:alpine
    ports:
      - "80:80"        # 對外只暴露 port 80
    volumes:
      - ./docker/nginx-proxy/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
      - web
      # - admin        # has_admin_backend=true 時取消註解
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/api/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Admin SPA（has_admin_backend=true 時啟用）
  # admin:
  #   image: {{PROJECT_SLUG}}/admin:local
  #   expose:
  #     - "{{ADMIN_PORT}}"
  #   # Admin container 自身 nginx 處理 SPA fallback（見 §5 nginx.conf）
```

**啟動並驗證單一 port 模式：**

```bash
# 啟動含 proxy 的完整環境
docker compose up -d

# 驗證單一 port 路由
curl -s -o /dev/null -w "%{http_code}" http://localhost/
# Expected: 200（client SPA）

curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health
# Expected: 200（API）

# Admin SPA（has_admin_backend=true 時）
curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/
# Expected: 200

curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/users/123
# Expected: 200（SPA deep link，不得 404）

# 確認沒有其他 port 對外暴露（api, web 只 expose，不 ports）
docker compose ps --format json | python3 -c "
import json,sys
for line in sys.stdin:
    svc = json.loads(line)
    print(svc.get('Name','?'), '→', svc.get('Publishers','[]'))
"
# Expected: 只有 proxy 有 0.0.0.0:80->80/tcp；其他服務無對外 port
```

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

---

## 20. k9s Quick Reference（互動式 K8s 操作）

> **定位**：k9s 是 kubectl 的互動式補充層，適合 on-call 快速診斷與資源瀏覽。所有操作等同 kubectl 指令，但以鍵盤驅動，不適合腳本化。`kubectl` 仍是 canonical 工具（腳本、CI、Makefile 均用 kubectl）；k9s 是 power user 效率層。

### 啟動

```bash
# 指定 namespace 啟動（推薦）
k9s -n {{K8S_NAMESPACE}}-local

# 全 cluster 啟動
k9s --all-namespaces
```

### 資源切換（命令模式，按 `:` 進入後輸入）

| 命令 | 說明 |
|------|------|
| `:pod` | 查看所有 Pod |
| `:deploy` | 查看 Deployment |
| `:svc` | 查看 Service |
| `:cm` | 查看 ConfigMap |
| `:secret` | 查看 Secret |
| `:hpa` | 查看 HorizontalPodAutoscaler |
| `:job` | 查看 Job |
| `:cronjob` | 查看 CronJob |
| `:node` | 查看 Node |
| `:ns` | 切換 Namespace |
| `:netpol` | 查看 NetworkPolicy |
| `:pvc` | 查看 PersistentVolumeClaim |
| `:event` | 查看 Events（等同 `kubectl get events`） |

### 常用按鍵（Resource 選中後）

| 按鍵 | 說明 | kubectl 等效 |
|------|------|------------|
| `l` | 查看 logs（即時串流） | `kubectl logs -f` |
| `p` | 查看前次容器 logs（CrashLoopBackOff 用） | `kubectl logs --previous` |
| `s` | exec 進入 container shell | `kubectl exec -it -- sh` |
| `d` | describe | `kubectl describe` |
| `e` | edit（直接編輯 YAML） | `kubectl edit` |
| `ctrl-d` | delete resource（會要求確認） | `kubectl delete` |
| `shift-f` | port-forward | `kubectl port-forward` |
| `f` | fullscreen logs 切換 | — |
| `/` | 文字篩選（過濾清單，支援正則） | `grep` |
| `Esc` | 返回上層 / 清除篩選 | — |
| `?` | 顯示所有按鍵說明 | — |
| `q` | 退出 k9s | — |

### 篩選技巧

```bash
# 在 :pod 清單中篩選 api server
/{{API_APP_LABEL}}

# 在 :event 中篩選 Warning 事件
/Warning

# 在 :pod 中篩選崩潰中的 Pod
/CrashLoop

# 在 :pod 中按 subsystem 篩選（Spring Modulith）
/subsystem=member
```

### Scale Deployment（互動式）

```
1. 進入 k9s -n {{K8S_NAMESPACE}}-local
2. 輸入 :deploy
3. 選中目標 Deployment
4. 按 s → 輸入新 replica 數 → 確認
```

### 皮膚與設定

```bash
# k9s 設定目錄
ls ~/.config/k9s/

# 設定 default namespace（config.yml 範例）
# currentContext: rancher-desktop
# namespace: {{K8S_NAMESPACE}}-local

# 推薦 skin（deep sea 或 dracula）
# 下載：https://github.com/derailed/k9s/tree/master/skins
```

### 與 Makefile 整合

```bash
# §6 Development Commands 已提供
make k9s   # 等同 k9s -n {{K8S_NAMESPACE}}-local
```

---

## 21. CI/CD 本地模擬（Jenkins on k3s）

> 本節讓開發者在本機完整重現 CI/CD Pipeline，確保 `Jenkinsfile` 和 `make ci-*` targets 在 commit 前可驗證，避免 PR 被 pipeline 失敗 reject。

### 21.0 Local Developer Platform 整體架構

本節說明本地 CI/CD 平台的整體架構。所有元件均在 Rancher Desktop k3s cluster 內執行，開發者 push 到本地 Gitea 即可觸發完整 CI/CD 流程，不依賴任何外部服務。

```mermaid
graph LR
    subgraph DevMachine["開發者本機（Rancher Desktop k3s）"]
        subgraph DevTools["dev-tools namespace"]
            Gitea["Gitea\n(ClusterIP:3000)\nLocal Git Server"]
        end
        subgraph CI["ci namespace"]
            Jenkins["Jenkins\n(ClusterIP:8080)\nCI Pipeline"]
        end
        subgraph ArgoNS["argocd namespace"]
            Argo["ArgoCD\n(ClusterIP:443)\nCD GitOps"]
        end
        subgraph App["{{K8S_NAMESPACE}}-local namespace"]
            AppPods["App Pods\n(Ingress port 80)"]
        end
    end
    Dev["Developer\ngit push"] --> Gitea
    Gitea -->|"Webhook POST"| Jenkins
    Jenkins -->|"build image\nupdate helm values"| Gitea
    Argo -->|"watch repo"| Gitea
    Argo -->|"sync"| AppPods
```

**元件說明**：

| 元件 | Namespace | ClusterIP Port | 本地存取（port-forward）|
|------|-----------|---------------|----------------------|
| Gitea（Local Git）| `dev-tools` | 3000 | `make dev-tools-forward` → http://localhost:3000 |
| Jenkins（CI）| `ci` | 8080 | `make dev-tools-forward` → http://localhost:8080 |
| ArgoCD（CD）| `argocd` | 443 | `make dev-tools-forward` → https://localhost:8443 |
| App Ingress | `{{K8S_NAMESPACE}}-local` | 80 | http://{{PROJECT_SLUG}}.local |

> **Port 分離原則**：App domain（port 80 via Ingress）與 dev-tools domain（3000/8080/8443 via port-forward）完全隔離，不互相干擾。詳細 Gitea 安裝與 Jenkins Webhook 設定見 CICD.md §8；Makefile dev-tools targets 見 CICD.md §9。

### 21.1 Jenkins on k3s 安裝

**前提**：Rancher Desktop 已執行（見 §1），k3s cluster 可用。

```bash
# 新增 Jenkins Helm repo
helm repo add jenkins https://charts.jenkins.io
helm repo update

# 安裝 Jenkins（使用 k8s/jenkins/jenkins-values.yaml）
kubectl create namespace ci
helm install jenkins jenkins/jenkins \
  --namespace ci \
  --values k8s/jenkins/jenkins-values.yaml \
  --version 5.1.x

# 等待 Jenkins 就緒（約 2~3 分鐘）
kubectl rollout status deployment/jenkins -n ci --timeout=300s

# 取得初始密碼
kubectl exec -n ci \
  $(kubectl get pod -n ci -l app.kubernetes.io/name=jenkins -o name) \
  -- cat /run/secrets/additional/chart-admin-password
```

**Port Forward 到本地**：
```bash
kubectl port-forward svc/jenkins -n ci 8080:8080
# 開啟瀏覽器：http://localhost:8080
# 帳號：admin  密碼：上方取得的密碼
```

### 21.2 Pipeline 設定（Multibranch Pipeline）

1. New Item → Multibranch Pipeline → 命名 `{{PROJECT_SLUG}}`
2. Branch Sources → Git → `{{REPO_URL}}`
3. Credentials → 選擇 `git-credentials`（見 §21.4）
4. Build Configuration → by Jenkinsfile → 路徑 `Jenkinsfile`
5. Scan Now → 自動偵測所有 branch

### 21.3 jenkinsfile-runner（快速本地 Dry-Run，無需 Jenkins Server）

> 適合在 push 前快速驗證 `Jenkinsfile` 語法和邏輯，不需啟動完整 Jenkins。

**安裝**：
```bash
# macOS / Linux（Homebrew）
brew install jenkins-x/jx/jfr

# 或直接下載 jar（版本 1.0-beta-33+）
curl -Lo jenkinsfile-runner.jar \
  https://github.com/jenkinsci/jenkinsfile-runner/releases/download/1.0-beta-33/jenkinsfile-runner-1.0-beta-33.jar

# 驗證
jfr version    # 或 java -jar jenkinsfile-runner.jar --version
```

**Dry-Run 執行**：
```bash
# 設定 mock secrets（避免 CI 憑證外洩）
export REGISTRY_TOKEN="mock-token"
export DB_PASSWORD="mock-db-password"
export REDIS_AUTH="mock-redis-auth"
export JWT_SECRET="mock-jwt-secret-64chars"

# 執行 dry-run
jfr run \
  --file Jenkinsfile \
  --workspace /tmp/jfr-workspace-{{PROJECT_SLUG}} \
  --no-sandbox

# 或使用 make target
make ci-dry-run
```

**預期輸出**：
```
[Pipeline] Start of Pipeline
[Pipeline] stage (Checkout)
[Pipeline] stage (Build)
...
[Pipeline] End of Pipeline
Finished: SUCCESS
```

### 21.4 CI 所需 Secrets 設定（Jenkins Credentials）

```bash
# Registry Token（用於 Image Push）
kubectl create secret generic registry-credentials \
  --from-literal=username={{REGISTRY_USER}} \
  --from-literal=password={{REGISTRY_TOKEN}} \
  -n ci

# Git Credentials（SSH key 或 Personal Access Token）
kubectl create secret generic git-credentials \
  --from-literal=username={{GIT_USER}} \
  --from-literal=password={{GIT_TOKEN}} \
  -n ci

# DB + Redis（從 §3.5 bootstrap-secrets.sh 讀取）
kubectl create secret generic app-secrets \
  --from-env-file=secrets.env \
  -n ci

# 確認所有 secrets 存在
kubectl get secret -n ci
```

### 21.5 ArgoCD CD 層設定（GitOps）

```bash
# 安裝 ArgoCD（若尚未安裝）
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 等待就緒
kubectl rollout status deployment/argocd-server -n argocd --timeout=300s

# Port Forward
kubectl port-forward svc/argocd-server -n argocd 8443:443

# 取得初始密碼
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# 登入 CLI
argocd login localhost:8443 --username admin --insecure

# 建立 Application（對應 k8s/overlays/local）
argocd app create {{PROJECT_SLUG}}-local \
  --repo {{REPO_URL}} \
  --path k8s/overlays/local \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace {{K8S_NAMESPACE}}-local \
  --sync-policy automated
```

### 21.6 Shared Make Targets（CI ↔ 本地對齊）

| Target | 作用 | CI 呼叫 | 本地可重現 |
|--------|------|---------|-----------|
| `make ci-build` | 編譯 + package | Stage: Build | ✅ |
| `make ci-test-unit` | 單元測試 | Stage: Unit Test | ✅ |
| `make ci-test-integration` | 整合測試 | Stage: Integration Test | ✅（需 k3s 運行） |
| `make ci-deploy` | 部署到 local k3s | Stage: Deploy | ✅ |
| `make ci-smoke` | Smoke test | Stage: Smoke Test | ✅ |
| `make ci-rollback` | 回滾到前一版本 | post { failure } | ✅ |
| `make ci-dry-run` | jenkinsfile-runner | 手動觸發 | ✅ |

> 確保 Makefile 中以上 7 個 targets 全部存在，CI 和本地使用完全相同的 target 名稱。

### 21.7 PR Gate 驗證（Pre-Push Checklist）

在 push 到 feature branch 之前，確認以下項目：

```bash
# 1. 所有 CI targets 本地通過
make ci-build
make ci-test-unit
make ci-test-integration   # 需 k3s 運行

# 2. Jenkinsfile dry-run 無錯誤
make ci-dry-run

# 3. Image 可本地 build（Kaniko 模擬）
make ci-build-image        # 本地 docker build（CI 用 Kaniko）

# 4. Deploy + Smoke 通過
make ci-deploy && make ci-smoke

# 全部通過後才 push
git push origin feature/your-branch
```

### 21.8 常見問題排查

| 問題 | 原因 | 解決 |
|------|------|------|
| `jenkinsfile-runner: command not found` | jfr 未安裝 | `brew install jenkins-x/jx/jfr` |
| `Pipeline: No such DSL method 'kubernetes'` | Kubernetes plugin 未載入 | 確認 jenkins-values.yaml plugins 清單含 kubernetes plugin |
| `ImagePullBackOff` in ci namespace | Registry credentials 未設定 | 執行 §21.4 registry-credentials |
| `ArgoCD: App not synced` | Git commit 未 push 或 path 錯誤 | 確認 `spec.source.path: k8s/overlays/local` |
| `make ci-test-integration` 失敗 | k3s 未運行 | 啟動 Rancher Desktop → 執行 §4 Step 4 setup |
