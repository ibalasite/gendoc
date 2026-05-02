---
doc-type: CICD
version: 1.0.0
expert-roles:
  gen:
    - role: CI/CD Architect
      scope: Pipeline architecture, Jenkinsfile design, stage sequencing, PR Gate, Make targets alignment
    - role: DevSecOps Engineer
      scope: Secret management in CI, image scanning, RBAC, registry credentials, security gates
upstream-docs:
  required:
    - EDD.md          # §3.4 CI_TOOL / CD_TOOL / K8s cluster / registry / repo
    - ARCH.md         # §3 Tech Stack, §5 Deployment Architecture
    - LOCAL_DEPLOY.md # §3.5 Secret Bootstrap, §6 Make Targets, §21 CI/CD Local Simulation
  recommended:
    - SCHEMA.md       # DB migration strategy (used in ci-deploy target)
    - test-plan.md    # Test scope (determines unit/integration stage breakdown)
output-paths:
  - docs/CICD.md
quality-bar:
  - All {{PLACEHOLDER}} values replaced — zero bare placeholders in output
  - §2 Jenkinsfile compiles (no Groovy syntax errors in pipeline block)
  - §3 jenkinsfile-runner dry-run command matches §2 Jenkinsfile path exactly
  - §4 Make targets match LOCAL_DEPLOY.md §6 exactly (ci-build / ci-test-unit / ci-test-integration / ci-deploy / ci-smoke / ci-rollback)
  - §5 required-status-checks list matches §4 stage names exactly
  - §6 Jenkins on k3s namespace matches §1 Agent Pod namespace
  - §8 Gitea Helm chart uses ClusterIP service type (not NodePort/LoadBalancer)
  - §8 adminPassword uses {{GITEA_ADMIN_PASSWORD}} placeholder (not hardcoded plaintext)
  - §9 Makefile dev-tools targets include all 5 required targets (dev-tools-install / dev-tools-status / dev-tools-forward / dev-tools-clean / ci-setup-credentials)
---

# CICD.gen.md — CI/CD Pipeline 文件生成規則

> **Iron Law**：生成任何 CICD.md 之前，必須先讀取 `CICD.md`（結構）和 `CICD.gen.md`（本規則）。

---

## 專家角色

| 角色 | 職責範圍 |
|------|---------|
| CI/CD Architect | Pipeline 架構、Jenkinsfile 設計、Stage 順序、PR Gate、Make targets 對齊 |
| DevSecOps Engineer | CI 中的 Secret 管理、Image Scanning、RBAC、Registry 憑證、Security Gate |

---

## 必讀上游鏈

生成前必須讀取以下文件（不得跳過）：

| 上游文件 | 必讀內容 | 對應 CICD.md 章節 |
|---------|---------|----------------|
| EDD.md | §3.4 CI_TOOL / CD_TOOL / K8s cluster / registry / repo / branch strategy | §1, §6, §7 Document Control |
| ARCH.md | §3 Tech Stack（build tool、language）、§5 Deployment Architecture | §1 Agent Pod image、§2 Jenkinsfile |
| LOCAL_DEPLOY.md | §3.5 Secret Bootstrap、§6 Make Targets、§21 CI/CD Local Simulation | §3 Dry-Run、§4 Shared Make Targets |
| SCHEMA.md（若存在）| DB migration tooling（Flyway / Liquibase / alembic）| §4 ci-deploy target |
| test-plan.md（若存在）| Unit / Integration / E2E 測試範圍切分 | §2 Jenkinsfile stages |

---

## 生成步驟（逐章節）

### Step 1：Document Control 表格

**讀取 EDD.md §3.4** 提取以下欄位，填入 Document Control 表格：

| CICD.md 欄位 | 來源 |
|-------------|------|
| CI_TOOL | EDD.md §3.4 CI 工具欄 |
| CD_TOOL | EDD.md §3.4 CD 工具欄 |
| K8S_CLUSTER | EDD.md §3.5 / ARCH.md §5（Local: Rancher Desktop k3s） |
| REGISTRY | EDD.md §3.4 Registry 欄（若無，預設 ghcr.io/{{PROJECT_SLUG}}） |
| REPO_URL | EDD.md 或 ARCH.md 的 git repo URL |
| BRANCH_STRATEGY | EDD.md §3.4 branch strategy（若無，預設 main / PR branch） |

**若 EDD.md 未指定 CI_TOOL**：預設填 Jenkins on k3s，並在文件備注「**預設值 — 請依實際情況更新**」。

---

### Step 2：§1 Pipeline Architecture

從 EDD.md / ARCH.md 提取系統名稱填入 Mermaid 圖的 node 標籤（`{{PROJECT_SLUG}}-ci` 等）。

**Agent Pod 設計表格**：
- namespace：`ci`（固定）
- image：根據 ARCH.md §3 的 Build Tool 填入（Maven → `maven:3.9-eclipse-temurin-21`；Gradle + Java → `gradle:8-jdk21`；Node → `node:22-alpine`；Python → `python:3.12-slim`）
- CPU request / limit：`500m / 2`（固定）
- Memory request / limit：`1Gi / 4Gi`（固定）

**Stage 流程圖**：保留 CICD.md 骨架的標準 6 stages，不得刪減。

---

### Step 3：§2 Jenkinsfile Skeleton

**必須替換的 {{PLACEHOLDER}}**：

| Placeholder | 來源 |
|------------|------|
| `{{PROJECT_SLUG}}` | EDD.md 專案名稱（kebab-case） |
| `{{K8S_NAMESPACE}}` | EDD.md / LOCAL_DEPLOY.md §2 namespace 定義 |
| `{{REGISTRY}}` | Document Control REGISTRY 欄 |
| `{{K8S_CLUSTER_URL}}` | ARCH.md §5 / LOCAL_DEPLOY.md cluster config |
| `agent.yaml image` | ARCH.md §3 Build Tool → 對應 image（見 Step 2） |
| `make ci-*` targets | LOCAL_DEPLOY.md §6 確認 target 名稱完全一致 |

**Jenkinsfile 結構規範**：
- 必須使用 `kubernetes { yaml """...""" }` agent block
- 必須包含以下 stages（順序固定）：
  1. Checkout（`git credentialsId`）
  2. Build（`make ci-build`）
  3. Unit Test（`make ci-test-unit`）
  4. Integration Test（`make ci-test-integration`）
  5. Image Build（Kaniko）
  6. Deploy to Local K8s（`make ci-deploy`）
  7. Smoke Test（`make ci-smoke`）
- 必須包含 `post { failure { sh 'make ci-rollback' } }` 和 `always { cleanWs() }`
- 禁止使用 Docker-in-Docker（DinD），Image Build 必須用 Kaniko

---

### Step 4：§3 Local Pipeline Dry-Run

**jenkinsfile-runner 安裝指令** — 讀取 LOCAL_DEPLOY.md §21，確認版本號一致。

**dry-run 指令中的路徑** 必須與 §2 Jenkinsfile 路徑一致：
```bash
jenkinsfile-runner -p /usr/share/jenkins/ref/plugins \
  -w /tmp/jfr-workspace \
  -f Jenkinsfile   # ← 必須與 §2 中 agent 使用的路徑相同
```

**Mock secrets 清單** — 讀取 EDD.md §3.4 所有 {{PLACEHOLDER}} secret 欄位，列出 `--env` 參數：
- 至少包含：`REGISTRY_TOKEN`、`DB_PASSWORD`、`REDIS_AUTH`、`JWT_SECRET`

---

### Step 5：§4 Shared Make Targets

**讀取 LOCAL_DEPLOY.md §6**，確認以下 targets 存在且名稱完全一致：
- `ci-build` / `ci-test-unit` / `ci-test-integration` / `ci-deploy` / `ci-smoke` / `ci-rollback` / `ci-dry-run`

**若 LOCAL_DEPLOY.md §6 缺少某 target**，在 CICD.md §4 的「Makefile 完整實作」中補全，並在備注標注「需同步加入 LOCAL_DEPLOY.md §6」。

**ci-deploy target** — 若 SCHEMA.md 存在且使用 Flyway：
```makefile
ci-deploy:
    flyway -url=$(DB_URL) -user=$(DB_USER) -password=$(DB_PASSWORD) migrate
    kubectl apply -k k8s/overlays/local
    kubectl rollout status deployment/$(PROJECT_SLUG)-api -n $(K8S_NAMESPACE)-local
```
若使用 Liquibase / alembic，對應替換 migration 指令。

---

### Step 6：§5 PR Gate

**required-status-checks** 清單必須與 §4 Make Targets 的 CI stage 名稱完全對應：
```yaml
required-status-checks:
  contexts:
    - Build
    - Unit Test
    - Integration Test
    - Image Build
```

**branch-protection.yml** 中的 `repository`、`branch` 欄位：
- 從 EDD.md / ARCH.md 的 git repo / branch strategy 填入

**開發者 Pre-PR Checklist**：
- 保留骨架的 8 項檢查，不得刪減
- 若 test-plan.md 存在且有 BDD feature files，加入第 9 項：「BDD feature files 通過（`make ci-test-bdd`）」

---

### Step 7：§6 Jenkins on k3s

**Helm values（jenkins-values.yaml）**：
- `jenkins.master.image.tag`：固定 `lts-jdk21`
- `jenkins.master.resources`：CPU `500m / 2`、Memory `2Gi / 4Gi`
- `plugins` 清單：必須包含 `kubernetes:4267.v45f5cba_2047d`、`workflow-aggregator:600.vb_57cdd26fdd7`、`git:5.2.2`、`kaniko:1.1.0`

**RBAC ServiceAccount**：
- namespace：`ci`（與 §1 Agent Pod namespace 一致）
- `verbs: [get, list, watch, create, update, patch, delete]` for `pods`, `pods/exec`, `pods/log`

**Registry credentials secret**：
```bash
kubectl create secret docker-registry registry-credentials \
  --docker-server={{REGISTRY}} \
  --docker-username={{REGISTRY_USER}} \
  --docker-password={{REGISTRY_TOKEN}} \
  -n ci
```
其中 `{{REGISTRY}}` 從 Document Control REGISTRY 欄取得。

---

### Step 8：§7 ArgoCD CD Integration

**Application YAML** 中填入：
- `metadata.name`：`{{PROJECT_SLUG}}-local`
- `spec.source.repoURL`：從 EDD.md / ARCH.md git repo URL；LOCAL mode 改為 Gitea ClusterIP URL（見 §7.2 注釋）
- `spec.source.targetRevision`：從 EDD.md branch strategy（通常 `main`）
- `spec.source.path`：`k8s/overlays/local`（固定）
- `spec.destination.namespace`：`{{K8S_NAMESPACE}}-local`

**GitOps Sequence** 保留骨架 sequenceDiagram，不得刪減步驟。

---

### Step 9：§8 Local Developer Platform（Gitea）

**讀取來源**：若 LOCAL_DEPLOY.md §21.0 存在，優先從中讀取 Gitea 設定；否則使用以下預設值。

**gitea-values.yaml 填充規則**：
| 欄位 | 來源 | 預設值 |
|-----|------|-------|
| `gitea.admin.password` | OS Keychain bootstrap（LOCAL_DEPLOY.md §3.5）| `{{GITEA_ADMIN_PASSWORD}}`（不得填明文）|
| `service.type` | 固定 | `ClusterIP`（禁止 NodePort / LoadBalancer）|
| `persistence.size` | EDD.md §3.5 資源規格（若無）| `256Mi` |
| `resources.requests.cpu` | EDD.md §3.5（若無）| `100m` |
| `resources.requests.memory` | EDD.md §3.5（若無）| `128Mi` |
| `resources.limits.cpu` | EDD.md §3.5（若無）| `500m` |
| `resources.limits.memory` | EDD.md §3.5（若無）| `512Mi` |

**§8.5 ArgoCD app-local.yaml** 中：
- `spec.source.repoURL`：填入 `http://gitea.dev-tools.svc.cluster.local:3000/dev/{{PROJECT_SLUG}}.git`（替換 PROJECT_SLUG）
- `spec.destination.namespace`：填入 `{{K8S_NAMESPACE}}-local`（替換 K8S_NAMESPACE）

**Port 分離原則驗證**：確認 App Ingress port 80 與 dev-tools ports（3000/8080/8443）無衝突。

---

### Step 10：§9 Makefile dev-tools Targets

**從骨架複製 5 個必要 target**，替換以下 placeholder：
- `{{PROJECT_SLUG}}`：從 EDD.md 專案名稱（kebab-case）填入
- `{{K8S_NAMESPACE}}`：從 EDD.md §3.5 環境矩陣填入

**5 個必要 target 清單**（缺一不可）：
1. `dev-tools-install` — 安裝 Gitea + Jenkins + ArgoCD
2. `dev-tools-status` — 檢查所有元件 Pod 狀態
3. `dev-tools-forward` — Port-forward（背景執行）
4. `dev-tools-clean` — 卸載（保留 PVC）
5. `ci-setup-credentials` — 引導執行 §21.4 bootstrap-secrets

**確認**：這 5 個 target 不得與 §4 Shared Make Targets 的 `ci-*` target 命名衝突。

---

### Step 11：§10 Security + §11 Observability

**§10 Secret location 表格**：
- 讀取 LOCAL_DEPLOY.md §3.5 Secret Bootstrap 確認 ephemeral vs OS Keychain vs mittwald 各自對應的 secret 類型
- 在 CICD.md §10 表格中對應標注

**§11 Prometheus metrics 清單**：
- 讀取 ARCH.md §7（若有 Observability 章節）確認 metrics endpoint 路徑
- 若 ARCH.md 未定義，使用骨架預設值（`/actuator/prometheus` for Spring Boot）

---

## Quality Gate（生成後自我檢查）

完成生成後，逐項驗證：

| 項目 | 驗證方式 | 通過條件 |
|------|---------|---------|
| 無裸 Placeholder | `grep -E '\{\{[A-Z_]+\}\}' docs/CICD.md` | 輸出為空 |
| §2 Jenkinsfile 結構完整 | 人工確認有 7 stages + post block | 無缺漏 |
| §4 Make targets 對齊 | 比對 LOCAL_DEPLOY.md §6 | 7 個 targets 完全匹配 |
| §5 PR Gate stages 一致 | 比對 §4 stage 名稱 | 完全一致 |
| §6 RBAC namespace 一致 | 比對 §1 Agent Pod namespace | 均為 `ci` |
| §3 dry-run path 正確 | 比對 §2 Jenkinsfile path | 路徑一致 |
| Secret 無明文 | 確認無 hardcoded password 值 | 全用 `${SECRET}` 引用 |
| §8 Gitea service type | 確認 gitea-values.yaml `service.type: ClusterIP` | 非 NodePort / LoadBalancer |
| §8 adminPassword 無明文 | 確認 `{{GITEA_ADMIN_PASSWORD}}` placeholder 存在 | 非任何靜態密碼字串 |
| §9 dev-tools targets 完整 | 確認 5 個必要 target 均存在 | dev-tools-install / dev-tools-status / dev-tools-forward / dev-tools-clean / ci-setup-credentials |

**若任一項不通過 → 立即修正，不得產出含錯誤的文件。**

---

## 常見錯誤防範

| 錯誤 | 防範措施 |
|------|---------|
| §4 Make target 名稱與 LOCAL_DEPLOY.md §6 不符 | 必讀 LOCAL_DEPLOY.md §6 後再填寫 |
| §5 PR Gate 的 required-status-checks 引用不存在的 stage | 從 §4 table 逐項複製 stage 名稱 |
| Jenkinsfile 使用 DinD | 一律使用 Kaniko；DinD 需 privileged container，禁止 |
| §7 ArgoCD Application namespace 與 §1 不符 | 統一從 EDD.md §3.4 K8S_NAMESPACE 取值 |
| §8 Gitea service type 不是 ClusterIP | 強制使用 ClusterIP；NodePort/LoadBalancer 違反 Port 分離原則 |
| §8 adminPassword 明文寫入 gitea-values.yaml | 使用 `{{GITEA_ADMIN_PASSWORD}}` placeholder，值來自 OS Keychain bootstrap |
| §9 dev-tools Makefile target 缺失 | 對照 5 個必要 target 清單逐一確認 |
| §10 Secret 類型誤標（OS Keychain 標為 ephemeral）| 對照 LOCAL_DEPLOY.md §3.5 三層策略 |
