---
doc-type: DEVELOPER_GUIDE
version: 1.0.0
reviewer-roles:
  - role: Developer Experience Auditor
    scope: Daily workflow completeness, scenario coverage, FAQ accuracy
  - role: CI/CD Operations Reviewer
    scope: Pipeline diagnosis accuracy, K8s command correctness, Make target alignment
quality-bar:
  - Zero bare {{PLACEHOLDER}} in output
  - §1 covers all 6 daily scenarios (A~F)
  - §2.1 Jenkins-not-triggered diagnosis has ≥ 3 rows
  - §4 answers the -local namespace question explicitly
  - §6 document boundary table includes all 6 document types
upstream-alignment:
  - LOCAL_DEPLOY.md §6 Make targets match §3.1 Quick Reference entries
  - CICD.md §8 Gitea Webhook URL matches §2.1 diagnosis curl command
  - EDD.md §3.4 K8S_NAMESPACE used consistently (with -local suffix) in all kubectl commands
---

# DEVELOPER_GUIDE.review.md — 開發者指南審查標準

---

## Layer 1：日常場景完整性（共 3 項）

### [CRITICAL] R-01：§1 缺少必要日常開發場景

**Check**：確認 §1 包含全部 6 個場景：
1. 場景 A：修改 API 邏輯並驗證
2. 場景 B：新增資料庫 Migration
3. 場景 C：執行完整 CI Pipeline 本地模擬
4. 場景 D：查看 Log 和除錯
5. 場景 E：重設開發環境
6. 場景 F：提交 PR 前的自我檢查

**Risk**：缺少任何場景代表開發者遇到該情境時無參考，只能翻多份文件自行拼湊。

**Fix**：在 §1 補全缺少的場景，參照 LOCAL_DEPLOY.md §6 Make targets 和 CICD.md §5.3 Pre-PR Checklist。

---

### [CRITICAL] R-02：§2.1 Jenkins Pipeline 未觸發診斷表 < 3 行

**Check**：確認 §2.1 表格至少包含 3 種診斷情境（Webhook 未設定、Pipeline 未偵測 branch、Jenkins Pod 不存在）。

**Risk**：診斷表不完整 → 開發者遇到 Jenkins 問題時無法自助排查，直接 escalate 降低開發效率。

**Fix**：補充缺少的診斷行，來源：CICD.md §6 Jenkins 安裝指令 + LOCAL_DEPLOY.md §21.1。

---

### [HIGH] R-03：§3.1 Quick Reference 指令表 < 8 條

**Check**：確認 §3.1 表格至少 8 條最常用指令。

**Risk**：Quick Reference 不夠全面，開發者找不到常用指令仍需翻其他文件。

**Fix**：從 LOCAL_DEPLOY.md §6 逐一補充 Make targets 到 §3.1。

---

## Layer 2：K8s 命名一致性（共 3 項）

### [CRITICAL] R-04：§4 FAQ 未明確回答 -local namespace 問題

**Check**：確認 §4 包含「所有 namespace 都要加 -local suffix 嗎？」的問答，且回答明確說明應用 namespace 規則（加 -local）vs dev-tools/ci（不加）。

**Risk**：namespace 混淆 → 開發者在 Production namespace 執行 local 操作，影響共享環境。

**Fix**：在 §4 加入 namespace 規則問答，從 EDD.md §3.4 K8S_NAMESPACE 取值。

---

### [HIGH] R-05：kubectl 指令的 namespace 未一致使用 -local suffix

**Check**：掃描全文所有 `kubectl` 指令，確認 App namespace 均使用 `{{K8S_NAMESPACE}}-local`（非裸 `{{K8S_NAMESPACE}}`）。

**Risk**：指令 namespace 錯誤 → 開發者誤操作到錯誤 namespace。

**Fix**：統一所有 kubectl 指令的 namespace 參數為 `{{K8S_NAMESPACE}}-local`。

---

### [MEDIUM] R-06：§2.2 Pipeline Stage 失敗表未列出 Image Build 行

**Check**：確認 §2.2 表格包含 Image Build（Kaniko）失敗的診斷行（症狀：Kaniko 失敗；修復：確認 registry-credentials secret）。

**Risk**：Image Build 是最難 debug 的 stage，缺少診斷 → 開發者難以獨立解決。

**Fix**：在 §2.2 表格加入 Image Build 行：`kubectl get secret registry-credentials -n ci`。

---

## Layer 3：CI/CD 上游對齊（共 2 項）

### [HIGH] R-07：§2.1 Webhook URL 與 CICD.md §8.4 不一致

**Check**：比對 §2.1 診斷表中的 Webhook curl 指令 URL 與 CICD.md §8.4 Webhook URL：
- 期望值：`http://jenkins.ci.svc.cluster.local:8080/gitea-webhook/post`

**Risk**：URL 錯誤 → 診斷指令無效，開發者誤以為 Webhook 正常。

**Fix**：從 CICD.md §8.4 複製正確 URL 到 §2.1 診斷指令。

---

### [HIGH] R-08：§3.1 Quick Reference 的 Make targets 與 LOCAL_DEPLOY.md §6 不符

**Check**：逐一比對 §3.1 表格中的 `make <target>` 與 LOCAL_DEPLOY.md §6 的 Makefile 定義。

**Risk**：Quick Reference 列出不存在的 target → 開發者執行後失敗，降低文件可信度。

**Fix**：以 LOCAL_DEPLOY.md §6 為 Source of Truth，更新 §3.1 表格中的 target 名稱。

---

## Layer 4：文件邊界清晰度（共 2 項）

### [HIGH] R-09：§6 文件邊界表格缺少必要文件類型

**Check**：確認 §6 表格包含以下 6 個文件類型的邊界說明：LOCAL_DEPLOY.md / CICD.md / runbook.md / API.md / SCHEMA.md / DEVELOPER_GUIDE.md。

**Risk**：邊界不清 → 開發者遇到問題時翻到錯誤文件，浪費時間。

**Fix**：補全缺少的文件行，來源：各文件的 Document Control 表格描述。

---

### [MEDIUM] R-10：§5 環境維護表格缺少 Rancher Desktop 資源建議

**Check**：確認 §5.2 包含 CPU / Memory / Disk 三個資源維度的最低配置和建議配置。

**Risk**：資源不足 → Pod Pending，開發者不知道如何調整。

**Fix**：補充 §5.2 Rancher Desktop 資源建議表格（CPU/Memory/Disk）。

---

## 審查完成標準

| 級別 | 數量要求 |
|------|---------|
| CRITICAL | 0（R-01/R-02/R-04 必須全數修復）|
| HIGH | 0（首次生成）；後續迭代允許 ≤ 1（需附風險說明）|
| MEDIUM | ≤ 2 |
| LOW | 不限 |

**CRITICAL 為 0 且 HIGH 為 0 → PASSED，可進行 commit。**
