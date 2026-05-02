---
doc-type: CICD
version: 1.0.0
reviewer-roles:
  - role: CI/CD Pipeline Reviewer
    scope: Pipeline completeness, stage ordering, Make target alignment, PR Gate correctness
  - role: DevSecOps Auditor
    scope: Secret handling in CI, RBAC correctness, Image build security, no privileged containers
quality-bar:
  - Zero bare {{PLACEHOLDER}} in output
  - §2 Jenkinsfile has all 7 required stages
  - §4 Make targets match LOCAL_DEPLOY.md §6 exactly
  - §5 required-status-checks matches §4 stage names
  - No Docker-in-Docker; Kaniko used for image build
  - No hardcoded secrets anywhere in document
  - §8 Gitea uses ClusterIP service type (not NodePort/LoadBalancer)
  - §9 has all 5 dev-tools make targets (dev-tools-install / dev-tools-status / dev-tools-forward / dev-tools-clean / ci-setup-credentials)
upstream-alignment:
  - EDD.md §3.4 CI_TOOL / CD_TOOL / K8s cluster / registry matches §6 Jenkins + §7 ArgoCD
  - LOCAL_DEPLOY.md §6 Make targets matches §4 Shared Make Targets
  - LOCAL_DEPLOY.md §3.5 Secret Bootstrap matches §8 Secret location table
---

# CICD.review.md — CI/CD Pipeline 文件審查標準

---

## Layer 1：Pipeline 結構完整性（共 4 項）

### [CRITICAL] R-01：§2 Jenkinsfile 缺少必要 Stage

**Check**：確認 §2 Jenkinsfile 包含全部 7 個 stages：
1. Checkout
2. Build（`make ci-build`）
3. Unit Test（`make ci-test-unit`）
4. Integration Test（`make ci-test-integration`）
5. Image Build（Kaniko）
6. Deploy to Local K8s（`make ci-deploy`）
7. Smoke Test（`make ci-smoke`）

**Risk**：缺少任何 stage 代表 CI 流程不完整，可能讓破壞性變更直接進入 CD 階段。

**Fix**：在 §2 Jenkinsfile 的 `stages` block 中補全缺少的 stage，保持順序。

---

### [CRITICAL] R-02：使用 Docker-in-Docker（DinD）建置 Image

**Check**：確認 §2 Jenkinsfile 的 Image Build stage 使用 Kaniko（`gcr.io/kaniko-project/executor`），而非 `docker build` 或 `docker:dind`。

**Risk**：DinD 需要 `privileged: true` container，在 k8s 環境中造成嚴重安全漏洞，且 Rancher Desktop k3s 預設禁止 privileged containers。

**Fix**：將 Image Build stage 替換為 Kaniko executor：
```groovy
container('kaniko') {
  sh """
    /kaniko/executor --context . \
      --dockerfile Dockerfile \
      --destination ${REGISTRY}/${PROJECT_SLUG}:${GIT_COMMIT}
  """
}
```

---

### [HIGH] R-03：§4 Shared Make Targets 與 LOCAL_DEPLOY.md §6 不符

**Check**：逐一比對 §4 table 中的 Make target 名稱與 LOCAL_DEPLOY.md §6 的實際 target 名稱：
- ci-build / ci-test-unit / ci-test-integration / ci-deploy / ci-smoke / ci-rollback / ci-dry-run

**Risk**：CI 環境呼叫不存在的 make target → pipeline 立即失敗，開發者無法本地重現 CI 失敗。

**Fix**：以 LOCAL_DEPLOY.md §6 的 target 名稱為準，更新 §4 table。若 LOCAL_DEPLOY.md 缺少 target，在 §4 備注「需同步加入 LOCAL_DEPLOY.md §6」。

---

### [HIGH] R-04：§5 PR Gate required-status-checks 與 §4 Stage 名稱不一致

**Check**：確認 §5 `branch-protection.yml` 的 `required-status-checks.contexts` 清單每一項都能在 §4 Make Targets table 的 CI Stage 欄找到對應。

**Risk**：required-status-checks 引用不存在的 stage → branch protection 永遠無法被滿足，PR 永遠 blocked。

**Fix**：從 §4 table 的「CI Stage」欄逐項複製到 §5 required-status-checks.contexts。

---

## Layer 2：Secret 安全性（共 4 項）

### [CRITICAL] R-05：CICD.md 中存在 Hardcoded Secret 值

**Check**：全文搜尋是否有任何明文密碼、token 或 private key（regex: `password\s*=\s*[^${\[]`、`token\s*=\s*[^${\[]`）。

**Risk**：密碼進入 git 歷史 → 不可撤回的憑證洩漏。

**Fix**：所有 secret 值必須以 `${VARIABLE}` 或 `credentials('jenkins-credential-id')` 方式引用，禁止硬編碼任何明文值。

---

### [HIGH] R-06：§8 Secret Location Table 與 LOCAL_DEPLOY.md §3.5 不一致

**Check**：比對 §8 Secret Location 表格與 LOCAL_DEPLOY.md §3.5 的三層策略（Ephemeral / OS Keychain / mittwald）。確認每個 Secret 的儲存類型標注正確。

**Risk**：Secret 類型誤標導致 CI 操作員使用錯誤的 credential 管理方式，可能將 fixed credentials 寫入 ephemeral storage → 環境重啟後遺失。

**Fix**：對照 LOCAL_DEPLOY.md §3.5 三層策略重新分類：
- Ephemeral（重啟後重生）：DB_PASSWORD / REDIS_AUTH / ENCRYPTION_KEY / JWT_SECRET
- Fixed（需持久化）：Registry Token / OAuth Client Secret / External Service Token
- In-cluster 生成（mittwald）：TLS Certs / Internal service tokens

---

### [HIGH] R-07：§6 Jenkins RBAC ServiceAccount 權限過寬

**Check**：確認 §6 ClusterRole（或 Role）的 `verbs` 清單符合最小權限原則：
- 允許：`pods`, `pods/exec`, `pods/log` 的 get/list/watch/create/update/patch/delete
- 禁止：`nodes`, `clusterroles`, `secrets`（非 ci namespace）的 write 權限

**Risk**：過寬的 RBAC → CI agent pod 若被 compromised，攻擊者可存取整個 cluster 的 secret。

**Fix**：將 ClusterRole 改為 namespace-scoped Role（`kind: Role`），限制在 `ci` namespace 內。

---

### [MEDIUM] R-08：§3 Dry-Run Mock Secrets 未覆蓋所有 CI 使用的 Secrets

**Check**：確認 §3 `jenkinsfile-runner --env` 參數清單包含 §2 Jenkinsfile 所有 `credentials()` 或 `env.SECRET_*` 引用的 secret 名稱。

**Risk**：dry-run 缺少 mock secret → 本地測試通過但 CI 失敗（因 secret binding 異常）。

**Fix**：從 §2 Jenkinsfile 逐行掃描 `credentials('...')` 呼叫，每個 credential-id 都在 §3 加入對應的 `--env CREDENTIAL_ID=mock-value`。

---

## Layer 3：上游對齊（共 3 項）

### [CRITICAL] R-09：Document Control 中 CI/CD Tool 與 EDD.md 不符

**Check**：Document Control 表格的 CI_TOOL / CD_TOOL 欄位值是否與 EDD.md §3.4 的 CI 工具 / CD 工具欄一致。

**Risk**：文件間不一致 → 開發者按 CICD.md 操作的工具與系統實際部署工具不同，造成 on-call 困惑。

**Fix**：以 EDD.md §3.4 為 Source of Truth，更新 Document Control 表格。若 EDD.md 未指定，在文件備注「**待確認 — 使用預設值 Jenkins on k3s**」。

---

### [HIGH] R-10：§7 ArgoCD Application namespace 與 §1 Agent Pod namespace 不符

**Check**：確認 §7 ArgoCD Application YAML 的 `spec.destination.namespace` 與 §1 Agent Pod 設計表格的 namespace 欄位一致（應均使用 EDD.md 定義的 K8S_NAMESPACE）。

**Risk**：ArgoCD 同步到錯誤 namespace → 部署成功但服務不在預期位置，smoke test 找不到服務。

**Fix**：統一從 EDD.md §3.4 K8S_NAMESPACE 取值，填入 §1 namespace 欄和 §7 `spec.destination.namespace`。

---

### [MEDIUM] R-11：§1 Agent Pod image 與 ARCH.md Build Tool 不符

**Check**：確認 §1 Agent Pod image 與 ARCH.md §3 Tech Stack 的 Build Tool 對應：
- Maven + Java 21 → `maven:3.9-eclipse-temurin-21`
- Gradle + Java 21 → `gradle:8-jdk21`
- Node.js 22 → `node:22-alpine`
- Python 3.12 → `python:3.12-slim`

**Risk**：Image 版本不符導致 CI 環境與開發環境 Java/Node 版本差異，測試結果不可靠。

**Fix**：讀取 ARCH.md §3，更新 §1 Agent Pod image 欄位到對應的 official image tag。

---

## Layer 4：操作可用性（共 2 項）

### [MEDIUM] R-12：§3 jenkinsfile-runner dry-run path 與 §2 Jenkinsfile 不一致

**Check**：§3 中的 `jenkinsfile-runner -f` 參數路徑是否與 §2 Jenkinsfile 的實際 checkout 路徑一致（通常為 `Jenkinsfile` in repo root）。

**Risk**：dry-run 指向不存在路徑 → 每次本地測試都失敗，開發者放棄使用 dry-run。

**Fix**：確認 §2 Jenkinsfile 的 `checkout` stage 使用 repo root 的 `Jenkinsfile`，§3 dry-run 指令對應 `-f Jenkinsfile`。

---

### [LOW] R-13：§9 Observability metrics endpoint 與 ARCH.md 不符

**Check**：§9 Prometheus metrics 清單中的 endpoint path（如 `/actuator/prometheus`）是否與 ARCH.md §7（Observability）一致。

**Risk**：endpoint path 錯誤 → Prometheus 抓不到 metrics，alert rules 靜默失效。

**Fix**：讀取 ARCH.md §7 或 LOCAL_DEPLOY.md §18（若有 Monitoring 章節），更新 §9 metrics endpoint path。

---

## Layer 5：Local Developer Platform（共 3 項）

### [HIGH] R-14：§8 Gitea service type 非 ClusterIP

**Check**：確認 `k8s/dev-tools/gitea-values.yaml`（或文件中的 gitea-values.yaml 範例）的 `service.type` 欄位為 `ClusterIP`，而非 `NodePort` 或 `LoadBalancer`。

**Risk**：NodePort / LoadBalancer 會將 Gitea dev-tools 對外暴露，違反 Port 分離原則——App domain（port 80）與 dev-tools domain（3000/8080/8443）應完全隔離。外部可直連 Gitea 意味著任何能存取 cluster 的人都可以推送程式碼。

**Fix**：在 `gitea-values.yaml` 中設定：
```yaml
service:
  type: ClusterIP
  port: 3000
```
若需本地存取，使用 `kubectl port-forward` 或 `make dev-tools-forward`（§9），而非對外暴露 NodePort。

---

### [HIGH] R-15：§8 Gitea adminPassword 明文寫入

**Check**：確認 §8.3 gitea-values.yaml 範例中的 `gitea.admin.password` 欄位值為 `{{GITEA_ADMIN_PASSWORD}}` placeholder，而非任何靜態明文密碼（如 `admin123`、`password`、`gitea`）。

**Risk**：明文密碼進入 git 歷史，所有有 repo 存取權限的人都能讀取 → Gitea admin 帳號遭接管，攻擊者可篡改 CI Pipeline 觸發惡意 build。

**Fix**：確認文件使用 `{{GITEA_ADMIN_PASSWORD}}` placeholder，並加入說明：值應由 `scripts/bootstrap-secrets.sh` 透過 OS Keychain 生成，或使用 `openssl rand -hex 16` 一次性生成並存入 OS Keychain，不得以任何靜態值替換 placeholder。

---

### [MEDIUM] R-16：§9 Makefile dev-tools targets 不完整

**Check**：確認 §9 Makefile 包含全部 5 個必要 target：
1. `dev-tools-install`
2. `dev-tools-status`
3. `dev-tools-forward`
4. `dev-tools-clean`
5. `ci-setup-credentials`

**Risk**：缺少任何 target → 開發者無法透過標準化命令設定本地 CI 平台，導致每個人各自手動操作，環境一致性無法保證；新進工程師第一天無法自助完成 dev-tools 安裝。

**Fix**：從 §9 骨架補全缺少的 target，並確認 target 名稱與文件 §8 的說明一致。

---

## 審查完成標準

| 級別 | 數量要求 |
|------|---------|
| CRITICAL | 0（所有 R-01/R-02/R-05/R-09 必須全數修復） |
| HIGH | 0（首次生成）；後續迭代允許 ≤ 1（需附風險說明）；R-14/R-15 需全數修復 |
| MEDIUM | ≤ 2 |
| LOW | 不限 |

**CRITICAL 為 0 且 HIGH 為 0 → PASSED，可進行 commit。**
