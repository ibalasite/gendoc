---
doc-type: DEVELOPER_GUIDE
version: "1.0"
status: "{{STATUS}}"
project: "{{PROJECT_NAME}}"
upstream-docs:
  required:
    - LOCAL_DEPLOY.md
    - CICD.md
    - runbook.md
---

# Developer Guide — {{PROJECT_NAME}}

> **本文件描述** {{PROJECT_NAME}} 的日常開發操作指南。前提：已按 LOCAL_DEPLOY.md 完成初始環境建置。
>
> **適用對象**：已完成 LOCAL_DEPLOY.md 建置的開發者，需要快速查找日常操作方式。

---

## Document Control

| 欄位 | 值 |
|------|---|
| **適用環境** | Local（Rancher Desktop k3s） |
| **前置條件** | LOCAL_DEPLOY.md 初始建置已完成 |
| **Author** | {{AUTHOR}} |
| **Last Updated** | {{DATE}} |

---

## §1 日常開發工作流程

### 1.1 啟動開發環境

```bash
# 確認 Rancher Desktop 已執行
# 啟動所有服務
make k8s-apply

# 確認所有 Pod 就緒
kubectl get pods -n {{K8S_NAMESPACE}}-local

# Port-forward 到本地
make dev-forward
```

### 1.2 六大日常開發場景

#### 場景 A：修改 API 邏輯並驗證

```bash
# 1. 修改程式碼
# 2. 執行單元測試
make ci-test-unit

# 3. 重新建置 + 部署
make ci-build && make ci-deploy

# 4. 確認部署成功
kubectl rollout status deployment/{{PROJECT_SLUG}}-api -n {{K8S_NAMESPACE}}-local

# 5. 執行 smoke test
make ci-smoke
```

#### 場景 B：新增資料庫 Migration

```bash
# 1. 新增 migration 檔案（依 SCHEMA.md §N migration tooling）
# Flyway: src/main/resources/db/migration/V{n}__{description}.sql
# Liquibase: src/main/resources/db/changelog/db.changelog-{n}.xml
# Alembic: alembic revision --autogenerate -m "{description}"

# 2. 執行 migration（更新 DB Schema）
make db-migrate

# 3. 驗證 migration
make db-status

# 4. 重新部署
make ci-deploy
```

#### 場景 C：執行完整 CI Pipeline（本地模擬）

```bash
# 完整模擬 CI Pipeline（含 build/test/image/deploy/smoke）
make ci-dry-run

# 或單步執行
make ci-build
make ci-test-unit
make ci-test-integration
make ci-smoke
```

#### 場景 D：查看 Log 和除錯

```bash
# 查看 API 服務 log
kubectl logs -f deployment/{{PROJECT_SLUG}}-api -n {{K8S_NAMESPACE}}-local

# 進入 API Pod debug
kubectl exec -it deployment/{{PROJECT_SLUG}}-api -n {{K8S_NAMESPACE}}-local -- /bin/sh

# 使用 k9s（互動式 K8s UI）
k9s -n {{K8S_NAMESPACE}}-local
```

#### 場景 E：重設開發環境（出問題時）

```bash
# 軟重設（重新部署，保留資料）
make k8s-delete && make k8s-apply

# 硬重設（清除所有資料，完全重建）
make local-clean && make local-setup

# 只重設資料庫
make db-reset
```

#### 場景 F：提交 PR 前的自我檢查

```bash
# 1. 確認 build 通過
make ci-build

# 2. 確認所有測試通過
make ci-test-unit
make ci-test-integration

# 3. 確認 linting/formatting
make lint

# 4. 模擬 PR Gate
make ci-dry-run
```

---

## §2 CI/CD 診斷與修復

### 2.1 Jenkins Pipeline 未觸發

| 症狀 | 可能原因 | 診斷步驟 |
|------|---------|---------|
| push 後 Jenkins 無反應 | Webhook 未設定 | `curl -X POST http://localhost:8080/gitea-webhook/post` 測試 |
| Webhook 顯示 200 但 Pipeline 不跑 | Multibranch Pipeline 未偵測到 branch | Jenkins UI → Scan Multibranch Pipeline |
| Jenkins Pod 不存在 | Jenkins 未安裝 | `helm install jenkins jenkins/jenkins -n ci -f k8s/ci/jenkins-values.yaml` |

### 2.2 Pipeline 各 Stage 失敗排查

| Stage | 常見錯誤 | 修復方法 |
|-------|---------|---------|
| Build | 編譯錯誤 | 確認 `make ci-build` 本地可執行 |
| Unit Test | 測試失敗 | `make ci-test-unit` 本地重現 |
| Integration Test | 連線失敗 | 確認 DB/Redis Pod 就緒：`kubectl get pods -n {{K8S_NAMESPACE}}-local` |
| Image Build | Kaniko 失敗 | 確認 Registry credentials secret 存在：`kubectl get secret registry-credentials -n ci` |
| Deploy | Pod 起不來 | `kubectl describe pod -n {{K8S_NAMESPACE}}-local` |
| Smoke Test | endpoint 無回應 | 確認 port-forward 執行中 |

### 2.3 ArgoCD 同步失敗

```bash
# 查看 ArgoCD 同步狀態
argocd app get {{PROJECT_SLUG}} --auth-token $(argocd account generate-token)

# 強制重新同步
argocd app sync {{PROJECT_SLUG}}

# 查看 diff
argocd app diff {{PROJECT_SLUG}}
```

---

## §3 Quick Reference 指令表

### 3.1 最常用指令

| 目的 | 指令 |
|------|------|
| 啟動所有服務 | `make k8s-apply` |
| 重新建置並部署 | `make ci-build && make ci-deploy` |
| 執行所有測試 | `make ci-test-unit && make ci-test-integration` |
| 查看服務狀態 | `kubectl get pods -n {{K8S_NAMESPACE}}-local` |
| 查看 API log | `kubectl logs -f deploy/{{PROJECT_SLUG}}-api -n {{K8S_NAMESPACE}}-local` |
| 重設環境 | `make local-clean && make local-setup` |
| 模擬 CI Pipeline | `make ci-dry-run` |
| Port-forward | `make dev-forward` |
| K8s 互動 UI | `k9s -n {{K8S_NAMESPACE}}-local` |

### 3.2 Dev-Tools 指令

| 目的 | 指令 |
|------|------|
| 安裝 dev-tools | `make dev-tools-install` |
| 查看 dev-tools 狀態 | `make dev-tools-status` |
| Port-forward dev-tools | `make dev-tools-forward` |
| 進入 Gitea | http://localhost:3000 |
| 進入 Jenkins | http://localhost:8080 |
| 進入 ArgoCD | https://localhost:8443 |

---

## §4 本地環境常見問題（FAQ）

### Q: Pod 一直 Pending，怎麼處理？

```bash
# 查看 Event
kubectl describe pod <pod-name> -n {{K8S_NAMESPACE}}-local

# 常見原因：資源不足
kubectl top nodes
# 若記憶體不足：Rancher Desktop → Preferences → Virtual Machine → 增加 Memory
```

### Q: 所有 namespace 都要加 `-local` suffix 嗎？

是的。本地環境規定：所有應用 namespace 加 `-local`（例：`{{K8S_NAMESPACE}}-local`）；dev-tools namespace 固定為 `dev-tools`；ci namespace 固定為 `ci`。這樣可避免與 staging/production 環境衝突。

### Q: 如何確認 DB Migration 已執行？

```bash
# Flyway
kubectl exec -it deploy/{{PROJECT_SLUG}}-api -n {{K8S_NAMESPACE}}-local \
  -- flyway -url={{DB_URL}} info

# Liquibase
kubectl exec -it deploy/{{PROJECT_SLUG}}-api -n {{K8S_NAMESPACE}}-local \
  -- liquibase status

# 直接查 migration history table
kubectl exec -it sts/postgres -n {{K8S_NAMESPACE}}-local \
  -- psql -U {{DB_USER}} -d {{DB_NAME}} -c "SELECT * FROM flyway_schema_history ORDER BY installed_on DESC LIMIT 5;"
```

### Q: Secret 過期或遺失怎麼辦？

```bash
# 重新執行 Secret Bootstrap
bash LOCAL_DEPLOY.md §3.5 bootstrap-secrets.sh

# 或只重設特定 Secret
kubectl delete secret app-secrets -n {{K8S_NAMESPACE}}-local
# 重跑 bootstrap 腳本
```

---

## §5 環境維護

### 5.1 定期維護項目

| 頻率 | 維護項目 | 指令 |
|------|---------|------|
| 每天 | 確認所有 Pod 就緒 | `make dev-tools-status` |
| 每週 | 清理舊 image | `docker system prune -f` |
| 每月 | 更新 Helm chart | `helm repo update` |
| 每次 pull | 同步 DB Migration | `make db-migrate` |

### 5.2 Rancher Desktop 資源建議

| 資源 | 最低配置 | 建議配置 |
|------|---------|---------|
| CPU | 4 cores | 8 cores |
| Memory | 8 GB | 16 GB |
| Disk | 40 GB | 80 GB |

### 5.3 升級 Dev-Tools

```bash
helm repo update
helm upgrade gitea gitea-charts/gitea -n dev-tools -f k8s/dev-tools/gitea-values.yaml
helm upgrade jenkins jenkins/jenkins -n ci -f k8s/ci/jenkins-values.yaml
```

---

## §6 文件邊界說明

| 問題 | 查找文件 |
|------|---------|
| 初次環境建置（安裝 k8s/DB/Redis 等） | LOCAL_DEPLOY.md |
| CI/CD Pipeline 架構（Jenkinsfile/ArgoCD） | CICD.md |
| 生產環境 incident 處理 | runbook.md |
| API 規格 | API.md |
| DB Schema 設計 | SCHEMA.md |
| 日常開發操作（本文件） | DEVELOPER_GUIDE.md |
| 環境無法啟動 / Pod 異常 | DEVELOPER_GUIDE.md §4 FAQ |
| CI Pipeline 失敗 | DEVELOPER_GUIDE.md §2 |
