---
doc-type: DEVELOPER_GUIDE
version: 1.0.0
expert-roles:
  gen:
    - role: DevOps Engineer
      scope: CI/CD workflow, K8s commands, Pipeline diagnosis, Make targets
    - role: Developer Experience (DX) Specialist
      scope: Daily workflow scenarios, FAQ content, Quick Reference, Document boundaries
upstream-docs:
  required:
    - LOCAL_DEPLOY.md  # §3.5 Secret Bootstrap, §6 Make Targets, §21 CI/CD Local Simulation
    - CICD.md          # §4 Shared Make Targets, §6 Jenkins, §7 ArgoCD, §8 Gitea
    - runbook.md       # §N 常見 incident（用於 §2 診斷區分邊界）
  recommended:
    - SCHEMA.md        # DB migration tooling（用於 §1.1 場景 B）
    - EDD.md           # §3.4 K8S_NAMESPACE, {{PROJECT_SLUG}}
output-paths:
  - docs/DEVELOPER_GUIDE.md
quality-bar:
  - All {{PLACEHOLDER}} values replaced — zero bare placeholders in output
  - §1 covers all 6 daily scenarios (A~F)
  - §2 has Jenkins-not-triggered diagnosis table with ≥ 3 rows
  - §3 Quick Reference table has ≥ 8 entries
  - §4 FAQ answers the -local namespace question
  - §6 Document boundary table includes all 6 document types
---

# DEVELOPER_GUIDE.gen.md — 開發者指南生成規則

> **Iron Law**：生成任何 DEVELOPER_GUIDE.md 之前，必須先讀取 `DEVELOPER_GUIDE.md`（結構）和 `DEVELOPER_GUIDE.gen.md`（本規則）。

---

## 專家角色

| 角色 | 職責範圍 |
|------|---------|
| DevOps Engineer | CI/CD 工作流程、K8s 指令、Pipeline 診斷、Make targets |
| Developer Experience Specialist | 日常操作場景、FAQ 內容、Quick Reference、文件邊界說明 |

---

## 必讀上游鏈

生成前必須讀取以下文件（不得跳過）：

| 上游文件 | 必讀內容 | 對應 DEVELOPER_GUIDE.md 章節 |
|---------|---------|---------------------------|
| LOCAL_DEPLOY.md | §3.5 Secret Bootstrap、§6 Make Targets、§21 CI/CD Local Simulation | §1 日常場景、§3 Quick Reference |
| CICD.md | §4 Shared Make Targets、§6 Jenkins、§7 ArgoCD、§8 Gitea（若存在）| §2 CI/CD 診斷、§3 dev-tools 指令 |
| runbook.md | §N 常見 incident 清單 | §6 文件邊界說明（區分 runbook vs DEVELOPER_GUIDE）|
| SCHEMA.md（若存在）| DB migration tooling（Flyway/Liquibase/alembic）| §1 場景 B DB Migration 指令 |
| EDD.md | §3.4 K8S_NAMESPACE / PROJECT_SLUG | 所有 {{}} placeholder 替換 |

---

## 生成步驟（逐章節）

### Step 1：Document Control

從 EDD.md §3.4 提取 PROJECT_NAME 填入 Document Control 表格。

### Step 2：§1 日常開發工作流程

**必須覆蓋全部 6 個場景（缺一不可）：**

| 場景 | 內容來源 |
|------|---------|
| A: 修改 API 邏輯並驗證 | LOCAL_DEPLOY.md §6 Make targets（ci-build/ci-deploy/ci-smoke）|
| B: 新增資料庫 Migration | SCHEMA.md migration tooling（Flyway/Liquibase/alembic）|
| C: 執行完整 CI Pipeline 本地模擬 | LOCAL_DEPLOY.md §21 + CICD.md §4（ci-dry-run target）|
| D: 查看 Log 和除錯 | EDD.md §3.4 K8S_NAMESPACE → kubectl commands |
| E: 重設開發環境 | LOCAL_DEPLOY.md §6（local-clean/local-setup/db-reset）|
| F: PR 前自我檢查 | CICD.md §5.3 Pre-PR Checklist |

**場景 B DB Migration 指令**：
- 讀取 SCHEMA.md migration tooling → 展開對應的指令（Flyway/Liquibase/alembic 三選一）
- 若 SCHEMA.md 不存在，使用骨架的三個工具範例

### Step 3：§2 CI/CD 診斷與修復

**2.1 Jenkins Pipeline 未觸發診斷表**：
- 讀取 CICD.md §8.4 Gitea Webhook URL（`http://jenkins.ci.svc.cluster.local:8080/gitea-webhook/post`）
- 讀取 LOCAL_DEPLOY.md §21.1 Jenkins 安裝指令
- 確認表格有 ≥ 3 行診斷項目

**2.2 Pipeline Stage 失敗排查表**：
- 讀取 CICD.md §4 Make Targets（ci-build/ci-test-unit/ci-test-integration 等）
- 讀取 EDD.md §3.4 K8S_NAMESPACE 填入 kubectl 指令中的 namespace

**2.3 ArgoCD 同步失敗**：
- 讀取 CICD.md §7.3 GitOps 流程
- 確認 {{PROJECT_SLUG}} 替換正確

### Step 4：§3 Quick Reference 指令表

**3.1 最常用指令**（≥ 8 條）：
- 讀取 LOCAL_DEPLOY.md §6 Make targets 逐一填入
- 讀取 EDD.md §3.4 K8S_NAMESPACE → kubectl 指令

**3.2 Dev-Tools 指令**（若 CICD.md §8 Gitea 存在）：
- 讀取 CICD.md §9 Makefile dev-tools targets（dev-tools-install/status/forward）

### Step 5：§4 FAQ

**Q: 所有 namespace 都要加 `-local` suffix 嗎？**
- 必須回答：應用 namespace 加 `-local`（值從 EDD.md §3.4 K8S_NAMESPACE 取）；dev-tools 固定 `dev-tools`；ci 固定 `ci`

**Q: 如何確認 DB Migration 已執行？**
- 依 SCHEMA.md migration tooling 展開對應指令（同場景 B）

### Step 6：§5 環境維護

**5.2 Rancher Desktop 資源建議**：
- 從 LOCAL_DEPLOY.md §1 Prerequisites 讀取建議規格（若有）

### Step 7：§6 文件邊界說明

**必須包含以下 6 個文件的邊界說明**：

| 問題 | 查找文件 |
|------|---------|
| 初次環境建置 | LOCAL_DEPLOY.md |
| CI/CD Pipeline 架構 | CICD.md |
| 生產環境 incident | runbook.md |
| API 規格 | API.md |
| DB Schema | SCHEMA.md |
| 日常開發操作 | DEVELOPER_GUIDE.md |

---

## Quality Gate（生成後自我檢查）

完成生成後，逐項驗證：

| 項目 | 驗證方式 | 通過條件 |
|------|---------|---------|
| 無裸 Placeholder | `grep -E '\{\{[A-Z_]+\}\}' docs/DEVELOPER_GUIDE.md` | 輸出為空 |
| §1 六大場景完整 | 確認場景 A~F 全部存在 | 6 個場景標題均出現 |
| §2 Jenkins 診斷表 ≥ 3 行 | 人工確認 §2.1 表格 | ≥ 3 行診斷 |
| §3 Quick Reference ≥ 8 條 | 人工確認 §3.1 表格 | ≥ 8 行 |
| §4 -local namespace FAQ | 搜尋 `-local` 關鍵字 | 出現 ≥ 1 次 |
| §6 文件邊界 6 個文件 | 確認 LOCAL_DEPLOY/CICD/runbook/API/SCHEMA/DEVELOPER_GUIDE 均列出 | 6 個文件均存在 |

**若任一項不通過 → 立即修正，不得產出含錯誤的文件。**
