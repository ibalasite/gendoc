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
  - §5.2 resource table has CPU / Memory / Disk rows with both min and recommended values
  - §6 Document boundary table includes all 6 document types
---

# DEVELOPER_GUIDE.gen.md — 開發者指南生成規則

> **Iron Law**：生成任何 DEVELOPER_GUIDE.md 之前，必須先讀取 `DEVELOPER_GUIDE.md`（結構）和 `DEVELOPER_GUIDE.gen.md`（本規則）。
>
> **禁止保留 Bare Placeholder**：輸出的 DEVELOPER_GUIDE.md 中不得含任何 `{{...}}` 格式的未替換 placeholder。若任何上游文件缺少必要值，必須停止生成並向使用者報告缺失項目，不得產出含 placeholder 的草稿。

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
| CICD.md | §4 Shared Make Targets、§6 Jenkins、§7 ArgoCD、§8 Gitea（若存在）、§9 Makefile dev-tools targets（若存在）| §2 CI/CD 診斷、§3 dev-tools 指令 |
| runbook.md | §N 常見 incident 清單 | §6 文件邊界說明（區分 runbook vs DEVELOPER_GUIDE）|
| SCHEMA.md（若存在）| DB migration tooling（Flyway/Liquibase/alembic）、frontmatter `migration-tool` 欄位 | §1 場景 B DB Migration 指令 |
| EDD.md | §3.1b Clean Architecture & SOLID 原則（SOLID 對應表 + Dependency Rule + 禁止清單）、§3.4 K8S_NAMESPACE / PROJECT_SLUG | §7 Clean Architecture 分層說明、所有 {{}} placeholder 替換 |

### 上游衝突優先級

當上游文件之間出現衝突時，依以下規則決策：

1. **Make target 名稱衝突**：若 LOCAL_DEPLOY.md §6 Make Targets 與 CICD.md §4 名稱不一致，以 **CICD.md §4 為 Source of Truth**。
2. **K8S_NAMESPACE 衝突**：若 EDD.md §3.4 的 K8S_NAMESPACE 與其他文件定義衝突，以 **EDD.md §3.4 為 Source of Truth**。
3. **遇衝突時必須在生成文件頭部以 NOTE 標註**，例如：`> NOTE: Make target 名稱依 CICD.md §4（與 LOCAL_DEPLOY.md §6 存在差異）。`

---

## 生成步驟（逐章節）

### Step 1：Document Control

從 EDD.md §3.4 提取 PROJECT_NAME 填入 Document Control 表格。

**Placeholder 填充規則**：
- `{{AUTHOR}}` — 由使用者在 gen 時提供，或從 `git config user.name` 讀取
- `{{DATE}}` — 填入當天日期（YYYY-MM-DD 格式）
- `{{STATUS}}` — 允許值：`draft`/`reviewed`/`approved`，初次生成填 `draft`

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

**場景 B DB Migration 指令**（偵測規則）：
1. 讀取 SCHEMA.md YAML frontmatter 的 `migration-tool` 欄位：
   - `migration-tool: flyway` → 只輸出 **Flyway** 指令（`V{n}__{description}.sql` 格式）
   - `migration-tool: liquibase` → 只輸出 **Liquibase** 指令（`db.changelog-{n}.xml` 格式）
   - `migration-tool: alembic` → 只輸出 **Alembic** 指令（`alembic revision --autogenerate`）
2. 若 `migration-tool` 欄位不存在，但 SCHEMA.md 存在 → 保留骨架三種工具範例，並在程式碼區塊頂部加入註解：`# TODO: 請依 SCHEMA.md migration-tool 欄位保留對應工具指令，刪除其他兩種`
3. 若 SCHEMA.md 完全不存在 → 同上，保留三種工具範例並加入 TODO 註解：`# TODO: 請依 SCHEMA.md migration-tool 欄位保留對應工具指令，刪除其他兩種`

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
- **Fallback**：若 CICD.md 無 §9 → 搜尋含 `dev-tools-install`、`dev-tools-status`、`dev-tools-forward` 關鍵字的段落，取最接近的 target 名稱填入

### Step 5：§4 FAQ

**Q: 所有 namespace 都要加 `-local` suffix 嗎？**
- 必須回答：應用 namespace 加 `-local`（值從 EDD.md §3.4 K8S_NAMESPACE 取）；dev-tools 固定 `dev-tools`；ci 固定 `ci`

**Q: 如何確認 DB Migration 已執行？**
- 依 SCHEMA.md YAML frontmatter `migration-tool` 欄位展開對應指令（偵測規則同場景 B）：
  - `flyway` → 輸出 Flyway `info` 指令
  - `liquibase` → 輸出 Liquibase `status` 指令
  - `alembic` → 輸出 Alembic `history` 指令
  - 欄位不存在 → 保留骨架三種工具範例並加 TODO 註解
- **Placeholder 來源說明**：`{{DB_URL}}`/`{{DB_USER}}`/`{{DB_NAME}}` 從 SCHEMA.md frontmatter 的 `db-url`/`db-user`/`db-name` 欄位讀取；若 SCHEMA.md 無對應欄位，則從 EDD.md §N DB 連線設定讀取

**Q: Secret 過期或遺失怎麼辦？**
- 輸出指令：`bash scripts/bootstrap-secrets.sh`（參照 LOCAL_DEPLOY.md §3.5）
- 驗證：確認 `kubectl get secret app-secrets -n {{K8S_NAMESPACE}}-local` 回傳正確

### Step 6：§5 環境維護

**5.1 定期維護表格**（逐列填充規則）：
- **每天項目**：確認所有 Pod 就緒，指令讀 LOCAL_DEPLOY.md §6 `dev-tools-status` target
- **每週項目**：清理舊 image（`docker system prune -f`）
- **每月項目**：更新 Helm chart（`helm repo update`）
- **每次 pull 項目**：同步 DB Migration（`make db-migrate`）
- 若 LOCAL_DEPLOY.md §6 有不同 target 名稱，以 LOCAL_DEPLOY.md 為準

**5.2 Rancher Desktop 資源建議**：
- 從 LOCAL_DEPLOY.md §1 Prerequisites 讀取建議規格（若有）

**5.3 升級 Dev-Tools**：
- Helm chart 名稱與 values 路徑從 CICD.md §8 Gitea/Jenkins 安裝段落讀取，或從 LOCAL_DEPLOY.md §6 `dev-tools-install` target 的 `helm upgrade --install` 指令讀取
- `helm upgrade` 指令必須與 `dev-tools-install` 使用相同的 chart repo（`gitea/gitea`、`jenkins/jenkins`）及相同的 `-f values.yaml` 路徑

### Step 6b：§7 Clean Architecture 分層說明

**生成條件**：若 EDD §3.1b 存在且非全空 placeholder。若 EDD §3.1b 尚未填寫，輸出佔位章節並標注 `[PENDING: 待 EDD §3.1b 填寫後補充]`。

**生成步驟**：

1. 讀取 EDD §3.1b SOLID 對應表，提取每個原則的「本系統實作方式」欄位
2. 讀取 EDD §3.1b Dependency Rule 禁止清單（Domain 不得 import 什麼）
3. 讀取 `docs/diagrams/class-inventory.md`（若存在）提取各層代表性 class 名稱
4. 依下方格式生成 §7，所有 class 名稱必須來自本系統實際命名（非通用佔位符）

**§7 Clean Architecture 分層說明（輸出格式）**：

```markdown
## §7 Clean Architecture 分層說明

本專案採用 Clean Architecture 四層設計（詳見 EDD §3.1b）。新進工程師在寫任何代碼前請確認所在層次。

### 依賴方向（Dependency Rule）

Presentation → Application → Domain ← Infrastructure

**核心原則**：依賴方向只能由外向內。Domain 層不得引用 Infrastructure 具體類別。

### 各層職責與 Import 規則

| 層次 | Stereotype | 代表 Class（本系統）| 可以 import | 禁止 import |
|------|-----------|---------------------|------------|------------|
| Domain | AggregateRoot / Entity / ValueObject / DomainEvent / Repository(interface) | {從 class-inventory 提取} | 同層 class、Java/語言標準庫 | ORM Entity、DB Driver、HTTP Client、Spring 框架 |
| Application | UseCase / ApplicationService / Port(interface) | {從 class-inventory 提取} | Domain 層 Interface、DTO | RepositoryImpl、Adapter、ORM |
| Infrastructure | RepositoryImpl / Adapter | {從 class-inventory 提取} | Domain Interface（實作用）、ORM、DB Driver、第三方 SDK | 無限制（但不得反向依賴 Application UseCase） |
| Presentation | Controller / RequestDTO / ResponseDTO | {從 class-inventory 提取} | Application UseCase / Service | Domain Entity（直接回傳）、Infrastructure |

### SOLID 快速對照（本系統）

| 原則 | 本系統實作方式 |
|------|--------------|
{從 EDD §3.1b SOLID 對應表逐行填入}

### 常見違規案例（FAQ）

**Q: 可以在 Domain 層 import Spring `@Repository` annotation 嗎？**
A: 不行。`@Repository` 是 Infrastructure 的技術細節；Domain 層只定義 `<<Repository>>` interface，不引用框架 annotation。

**Q: UseCase 可以直接 `new UserRepository()` 嗎？**
A: 不行。違反 DIP。UseCase 只依賴 `IUserRepository` interface，具體實作由 DI Container 注入。
```

---

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
| 無裸 Placeholder | `grep -E '\{\{[A-Z_]+\}\}' docs/DEVELOPER_GUIDE.md` | 輸出為空（注意：{{DB_URL}}/{{DB_USER}}/{{DB_NAME}} 需從 SCHEMA.md frontmatter db-url/db-user/db-name 或 EDD.md §N DB 連線設定確認替換） |
| §1 六大場景完整 | 確認場景 A~F 全部存在 | 6 個場景標題均出現 |
| §2 Jenkins 診斷表 ≥ 3 行 | 人工確認 §2.1 表格 | ≥ 3 行診斷 |
| §3 Quick Reference ≥ 8 條 | 人工確認 §3.1 表格 | ≥ 8 行 |
| §4 -local namespace FAQ | 搜尋 `-local` 關鍵字 | 出現 ≥ 1 次 |
| §7 CA 分層說明 | 確認 §7 章節存在且 SOLID 表格已填入本系統 class 名稱（非 `{從 class-inventory 提取}` 佔位） | §7 存在 + SOLID 表 5 行均有具體內容 |
| §5.2 資源建議三維度 | 確認 CPU/Memory/Disk 均有最低配置與建議配置 | 三個維度欄位均出現 |
| §6 文件邊界 6 個文件 | 確認 LOCAL_DEPLOY/CICD/runbook/API/SCHEMA/DEVELOPER_GUIDE 均列出 | 6 個文件均存在 |

**若任一項不通過 → 立即修正，不得產出含錯誤的文件。**
