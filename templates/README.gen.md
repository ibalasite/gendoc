---
doc-type: README
output-path: README.md
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
  - features/          # BDD-server 輸出（Server BDD Feature Files）
  - features/client/   # BDD-client 輸出（Client E2E Feature Files，若 client_type≠none）
  - docs/RUNBOOK.md
  - docs/LOCAL_DEPLOY.md
---

# README Generation Rules

本檔案定義 `README.md` 的生成規則。由 `/gendoc readme` 讀取並遵循。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## §0 Session Config 讀取

```bash
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")
_CWD="$(pwd)"
_APP_NAME=$(basename "$_CWD")

_EXEC_MODE=$(python3 -c "
import json
try:
    d = json.load(open('${_STATE_FILE}'))
    print(d.get('execution_mode', ''))
except:
    print('')
" 2>/dev/null || echo "")
```

若 `_EXEC_MODE=interactive`：用 AskUserQuestion 確認是否覆寫（選 n → STEP_SKIPPED）。
若 `_EXEC_MODE=full-auto`：直接繼續（README.md 永遠覆蓋）。

---

## §1 Upstream Sources

| 文件 | 必讀章節 | README 章節用途 |
|------|---------|---------------|
| `IDEA.md`（若存在） | §1 Problem、§5 Leap of Faith | Why we built this：專案起源、核心假設 |
| `BRD.md` | §1 Executive Summary、§2 Business Goals | Overview、Core Features 業務語意 |
| `PRD.md` | §4 Scope、§5 User Stories | Core Features 清單 |
| `PDD.md`（若存在） | §1 Client 類型 | Tech Stack 前端框架補充 |
| `EDD.md` | §2 技術選型 | Tech Stack 完整清單 |
| `ARCH.md` | §3 元件架構、§9 部署拓撲 | Architecture 章節 Mermaid 圖 |
| `API.md` | 前 5 個 Endpoint | API Quick Reference |
| `SCHEMA.md` | 資料表清單 | Data Model 摘要 |
| `test-plan.md` | §2 工具組合 | Testing 章節工具與指令 |

---

## §2 資料收集規則

### 技術棧命令對照

```bash
_LANG_STACK=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('lang_stack','N/A'))" 2>/dev/null || echo "N/A")
_GITHUB_REPO=$(python3 -c "import json; print(json.load(open('${_STATE_FILE}')).get('github_repo',''))" 2>/dev/null || git remote get-url origin 2>/dev/null | sed 's/\.git$//' || echo "")
```

| lang_stack 關鍵字 | _PREREQ | _INSTALL_CMD | _START_CMD | _TEST_CMD |
|------------------|---------|--------------|------------|-----------|
| node/ts/typescript/fastify/express/next | Node.js 20+, npm 10+ | npm install | npm run dev | npm test |
| python/fastapi/django/flask | Python 3.11+ | pip install -r requirements.txt | python -m uvicorn main:app --reload | pytest |
| go/golang | Go 1.21+ | go mod download | go run ./cmd/... | go test ./... |
| java/spring | Java 21+, Maven 3.9+ | mvn install -DskipTests | mvn spring-boot:run | mvn test |
| 其他 | 詳見 docs/LOCAL_DEPLOY.md | # 詳見 docs/LOCAL_DEPLOY.md | （同左） | （同左） |

### 從上游文件萃取

- **BRD 標題**：`head -1 docs/BRD.md | sed 's/^# //'`，失敗用 `$_APP_NAME`
- **BRD 描述**：第一個 `##` 前的純文字，截 300 字
- **PRD P0 功能**：`P0` 段落直到下個 `##` 的條列，前 8 項
- **架構圖**：優先讀 `ARCH.md`，其次 `EDD.md` 的第一個 mermaid 區塊
- **目錄結構**：`os.listdir('.')` 過濾 node_modules/__pycache__/vendor/dist/build/.git
- **環境變數表**：`parse .env.example` → key/desc/required/default 四欄
- **API 快速參考**：從 `docs/API.md` 萃取前 5 個 `GET|POST|PUT|PATCH|DELETE /path`
- **已知限制**：從 `docs/ALIGN_REPORT.md` 或 `docs/EDD.md` 萃取 `STUBBORN:` 標記，前 5 項

---

## §3 章節結構規則

README.md 必須包含以下全部 20+ 節，**嚴格按順序**：

1. **Document Control**（HTML comment）— DOC-ID、Version、Status、Author、Date、Upstream docs
2. **Title + Badges**（build CI / license / version）
3. **Overview**（來自 BRD 摘要，≤ 120 字單行 tagline + 完整段落）
4. **核心功能**（PRD P0 條列，≥ 5 項，非通用描述）
5. **系統架構**（Mermaid 圖來自 ARCH.md/EDD.md）
6. **Tech Stack 表**（來自 EDD，按 Frontend/Backend/Database/Infrastructure 分層）
7. **快速啟動**（Docker / macOS+Linux / Windows 三平台各自完整命令）
8. **環境變數表**（key / 說明 / 必填 / 預設值）
9. **API 快速參考**（前 5 個 Endpoint）
10. **目錄結構**（`tree` 風格 ASCII）
11. **文件索引**（BRD/PRD/PDD/EDD/ARCH/API/SCHEMA/BDD 全部含 GitHub Pages 連結）
12. **測試**（測試命令 + 覆蓋率目標 ≥ 80%）
13. **已知限制**（非通用，針對本專案）
14. **Changelog**（指向 GitHub Releases）
15. **License**（MIT）
16. **開發說明**（gendoc 生成聲明）
17. **Security Policy**（Responsible Disclosure SLA：Critical 72h / High 7d / Medium 90d）
18. **Architecture Quick Reference**（5 大技術決策速查 + ADR 連結）
19. **Code of Conduct**（Contributor Covenant v2.1 引用）

---

## §4 格式規則

- `README.md` 輸出至**專案根目錄**（非 docs/），永遠覆蓋
- 每個 `<_VARIABLE>` 必須填入真實收集到的值，**不得保留佔位符**
- Mermaid 圖必須完整可渲染（無語法錯誤）
- Troubleshooting ≥ 5 條目，需針對本專案的真實問題（非「重開機」類通用建議）
- Badges 使用 GitHub Actions CI badge URL（從 `_GITHUB_REPO` 推算）

---

## §5 Self-Check（生成後必過）

- [ ] Document Control HTML comment 存在
- [ ] Badges 行至少包含 CI status 和 license
- [ ] Architecture Mermaid 圖來自上游文件（非預設圖）
- [ ] Tech Stack 表按分層填入真實技術（非空行）
- [ ] Quick Start 覆蓋 Docker / macOS+Linux / Windows 三平台
- [ ] 環境變數表非空（至少有來自 .env.example 或 EDD 的實際變數）
- [ ] 文件索引表包含 BRD/PRD/PDD/EDD/ARCH/API/SCHEMA/BDD 全部行
- [ ] Security Policy 含 Responsible Disclosure SLA 表格
- [ ] Architecture Quick Reference 含 5 大決策速查
- [ ] Code of Conduct 已引用 Contributor Covenant v2.1
- [ ] 無殘留 `{{PLACEHOLDER}}` 或 `<_VARIABLE>` 格式
- [ ] 輸出至 README.md（根目錄，非 docs/）

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 README.md 章節清單，無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | Quick Start 指令使用 state.lang_stack 對應的工具（pip / npm / cargo 等） | 修正至一致 |
| 數值非 TBD/N/A | 所有徽章（badge）連結填有實際 URL（非佔位符） | 從 state.github_repo 構建正確 URL |
| Quick Start 可執行 | 從 clone 到 run 的所有指令可直接 copy-paste 執行 | 改寫為具體可執行序列 |
| 架構概覽存在 | 有至少一個架構圖（Mermaid 或說明段落，非「架構圖待補」） | 從 ARCH.md §架構概覽 提取 C4 圖 |
