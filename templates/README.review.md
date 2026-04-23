---
doc-type: README
target-path: README.md
reviewer-roles:
  primary: "資深 Tech Writer（README 審查者）"
  primary-scope: "完整性、清晰度、快速上手可行性、安裝步驟正確性、文件結構合理性"
  secondary: "資深 Developer Advocate"
  secondary-scope: "首次開發者體驗、Getting Started 流程、API 文件品質、範例程式碼正確性"
  tertiary: "資深 DevOps Expert"
  tertiary-scope: "部署說明正確性、環境要求完整性、Docker/K8s 指令可執行性、安全配置說明"
quality-bar: "新加入的工程師從 README 開始，無需額外文件，30 分鐘內能在本地跑起系統。每個步驟都能獨立執行，無隱含前置依賴。"
upstream-alignment:
  - field: Tech Stack 清單
    source: docs/EDD.md §2 技術選型
    check: README Tech Stack 表格是否與 EDD §2 完全一致，無遺漏框架或版本差異
  - field: 核心功能清單
    source: docs/PRD.md P0 User Stories
    check: README 核心功能是否覆蓋所有 PRD P0 功能，且描述一致
  - field: 環境變數清單
    source: docs/EDD.md 環境變數 / .env.example
    check: README 環境變數表是否與 EDD 定義的必要環境變數完整對應
  - field: 文件索引連結
    source: docs/ 目錄下所有文件
    check: README 文件索引的所有連結是否指向真實存在的文件
  - field: 架構圖
    source: docs/ARCH.md / docs/EDD.md
    check: README 系統架構圖是否來自 ARCH.md 或 EDD.md（非預設範例圖）
---

# README Review Items

本檔案定義 `README.md` 的審查標準。由 `/reviewdoc readme` 讀取並遵循。
審查角色：三角聯合審查（資深 Tech Writer + 資深 Developer Advocate + 資深 DevOps Expert）
審查標準：「假設一位全新加入的工程師，只有 README，30 分鐘內能跑起完整的本地環境，並理解專案的核心功能和技術決策。」

---

## Review Items

### Layer 1: 快速上手完整性（由 Tech Writer + Developer Advocate 聯合審查，共 5 項）

#### [CRITICAL] 1 — Quick Start 含裸 Placeholder 或步驟不完整
**Check**: §Quick Start 的 Prerequisites、安裝步驟、啟動命令是否都已填入真實值？是否有 `{{PLACEHOLDER}}`、`<VARIABLE>` 等未替換的佔位符？核對 Docker、macOS+Linux、Windows 三個平台的命令是否都已提供具體命令（非「見文件」）？逐一列出所有未替換的 placeholder 和缺失的步驟。
**Risk**: Quick Start 含裸 placeholder，工程師無法直接跟著做，第一印象是「文件沒做完」，降低專案可信度；缺失步驟導致本地環境設置失敗，需要反覆問人。
**Fix**: 替換所有裸 placeholder 為真實值（來自 EDD、BRD 或 .env.example）；補充缺失的平台命令，確保三個平台的 Quick Start 均完整可執行。

#### [CRITICAL] 2 — 環境變數表缺失或不完整
**Check**: README 是否有環境變數表（key / 說明 / 必填 / 預設值 四欄）？是否涵蓋啟動系統所需的所有必要環境變數？對照 .env.example 或 EDD 中定義的環境變數，列出 README 缺少的必要環境變數。
**Risk**: 環境變數缺失，工程師 `cp .env.example .env` 後直接啟動，系統因缺少必要設定而異常，且沒有任何提示說明哪些變數是必填的。
**Fix**: 補充完整的環境變數表，涵蓋所有必要環境變數；標注哪些是必填（Required）、哪些有預設值可選填；說明如何取得無法有預設值的環境變數（如 API Key）。

#### [HIGH] 3 — 先決條件版本要求不明確
**Check**: Prerequisites 是否明確列出所有工具的最低版本要求（如 Node.js 20+、Python 3.11+、Docker 24+）？是否有工具只列出名稱但未說明版本（如「需要安裝 Node.js」但未指定版本）？逐一核對 EDD §2 技術選型中的 Runtime 版本要求。
**Risk**: 版本不明確，工程師使用舊版工具（如 Node.js 16）啟動系統，遇到不相容錯誤，浪費大量除錯時間。
**Fix**: 為每個工具明確標注最低版本（來自 EDD §2），並提供版本檢查命令（如 `node --version`）。

#### [HIGH] 4 — 啟動後驗證步驟缺失
**Check**: Quick Start 步驟完成後，是否提供「如何確認系統已正常啟動」的驗證方法（如 `curl http://localhost:8080/health`、開啟瀏覽器訪問 URL、看到特定日誌輸出）？缺少驗證步驟視為 finding。
**Risk**: 工程師跑完所有步驟後不知道是否成功，需要猜測或問人「怎麼確認啟動成功」，影響新工程師的入職體驗。
**Fix**: 在 Quick Start 末尾補充驗證步驟（推薦：health check curl 命令 + 預期輸出）；若有前端，補充 UI 訪問 URL 和預期畫面說明。

#### [HIGH] 5 — 測試執行命令不完整
**Check**: README 的 Testing 章節是否提供完整的測試執行命令（Unit Test、Integration Test、E2E Test 各自的命令）？是否說明覆蓋率目標（≥ 80%）？是否列出測試框架？
**Risk**: 測試命令不完整，貢獻者提交 PR 前不確定跑哪些測試、測試是否通過，導致 CI 失敗率上升。
**Fix**: 補充所有測試層級的執行命令和覆蓋率查看命令；對齊 test-plan.md 的工具組合。

---

### Layer 2: 文件清晰度（由 Tech Writer 主審，共 4 項）

#### [HIGH] 6 — 文件索引連結無效或不完整
**Check**: 文件索引（Documentation 章節）是否涵蓋 BRD/PRD/PDD/EDD/ARCH/API/SCHEMA/test-plan/BDD 所有文件？每個連結是否指向真實存在的文件路徑（`docs/BRD.md` 等）？逐一驗證每個連結路徑。
**Risk**: 無效連結讓工程師找不到對應的詳細文件，需要手動瀏覽目錄結構，降低文件的可用性。
**Fix**: 補充缺少的文件連結；修正指向不存在路徑的連結；對目前不存在的文件，標注「（即將完成）」而非保留死連結。

#### [HIGH] 7 — Overview 太過泛化或無專案特定資訊
**Check**: Overview 是否說明了本專案的核心問題域（非通用描述如「這是一個 Node.js 應用程式」）？是否說明了目標用戶和核心價值主張？是否包含了專案的非顯而易見的特性或決策？
**Risk**: 泛化的 Overview 讓讀者無法快速判斷這個專案是否是他們要找的東西，也讓新工程師缺乏上下文理解為什麼要這樣做。
**Fix**: 改寫 Overview，包含三要素：1）解決什麼具體問題 2）給什麼角色用 3）為什麼用這個而非其他方案；從 BRD/IDEA.md 萃取真實的業務背景。

#### [MEDIUM] 8 — 目錄結構說明缺失或不準確
**Check**: README 是否有目錄結構（ASCII tree 或等效格式）？是否涵蓋主要目錄並說明其用途？目錄結構是否與實際專案結構一致（無多餘或缺失的目錄）？
**Risk**: 無目錄結構說明，工程師需要自行探索專案結構，找不到相關程式碼的位置；過時的目錄結構說明讓工程師困惑（「README 說有 src/services/ 但找不到」）。
**Fix**: 補充目錄結構圖，涵蓋主要目錄並說明用途；確認與實際專案結構一致。

#### [MEDIUM] 9 — 核心功能清單過於通用
**Check**: README 核心功能是否列出 ≥ 5 項具體的業務功能（非「使用者認證」等通用描述，而是「支援 JWT + Refresh Token 的無狀態認證，Token 有效期 15 分鐘」）？是否覆蓋所有 PRD P0 功能？
**Risk**: 功能描述過通用，讀者無法了解本系統的具體功能邊界，也無法評估系統是否適合他們的需求。
**Fix**: 將每個功能描述改寫為具體的業務能力描述（從 PRD P0 User Stories 萃取關鍵字），避免使用通用技術術語作為功能說明。

---

### Layer 3: 上游文件連結（由 Tech Writer + Developer Advocate 聯合審查，共 3 項）

#### [HIGH] 10 — 架構圖非來自上游文件
**Check**: README 的系統架構圖（Mermaid 或圖片）是否來自 ARCH.md 或 EDD.md 的真實架構？是否包含真實的元件名稱（非「ServiceA → ServiceB」的通用示例圖）？若架構圖是預設範例或完全通用的，視為 finding。
**Risk**: 使用預設架構圖讓工程師對系統架構產生錯誤理解，入職後花時間理解實際架構才發現與 README 不符。
**Fix**: 替換為來自 ARCH.md 或 EDD.md 的真實 Mermaid 架構圖；若上游文件不存在，標注「架構圖待補充」而非保留通用示例。

#### [HIGH] 11 — Tech Stack 表與 EDD 不一致
**Check**: README Tech Stack 表（Frontend/Backend/Database/Infrastructure 分層）是否與 EDD §2 技術選型完全一致？是否有技術項目在 EDD 有但 README 沒有？是否有版本號碼不一致的技術？
**Risk**: Tech Stack 不一致讓工程師參照 README 安裝了錯誤版本的工具（如 EDD 要求 Node.js 20 但 README 寫 18），導致環境不相容。
**Fix**: 以 EDD §2 技術選型為 Source of Truth，修正 README Tech Stack 表中不一致的技術和版本；補充遺漏的技術項目。

#### [MEDIUM] 12 — API 快速參考未對齊 API.md
**Check**: README 的 API Quick Reference（若有）是否列出真實的 API Endpoint（來自 API.md 的 P0 Endpoint）？是否包含 Request/Response 格式說明或連結到 API.md？若 API Quick Reference 使用的是範例路徑（`/api/users`）而非真實 Endpoint，視為 finding。
**Risk**: API 快速參考使用通用範例，工程師整合前端或第三方客戶端時參考了錯誤的 Endpoint，導致整合失敗。
**Fix**: 從 API.md 萃取前 5 個 P0 Endpoint（真實路徑和方法），並加入連結到完整 API.md 的說明。

---

### Layer 4: 環境與部署（由 DevOps Expert 主審，共 4 項）

#### [HIGH] 13 — Docker 啟動指令不可執行
**Check**: README 的 Docker 快速啟動命令是否包含完整的 `docker compose up` 或 `docker run` 命令？是否說明需要的 Docker 版本？docker-compose.yml（若存在）路徑是否正確？命令是否需要先行設定環境變數才能執行（若需要，是否有說明）？
**Risk**: Docker 指令不完整，工程師執行後遇到「找不到 docker-compose.yml」或「缺少環境變數」等錯誤，且 README 沒有說明如何解決。
**Fix**: 提供完整可直接貼上執行的 Docker 啟動命令序列（含 `cp .env.example .env`、`docker compose up -d` 等所有步驟）；說明所有前置環境變數設定要求。

#### [HIGH] 14 — 安全配置說明缺失
**Check**: README 是否有 Security Policy 章節（含 Responsible Disclosure SLA：Critical 72h / High 7d / Medium 90d）？是否有警示說明 .env 文件不應提交版控？是否說明哪些環境變數是敏感值（SECRET、KEY、PASSWORD 類）？
**Risk**: 無安全配置說明，新工程師可能不知道不能提交 .env 文件，或不知道如何負責任地揭露漏洞，造成安全風險。
**Fix**: 補充 Security Policy 章節（含 Responsible Disclosure SLA）；在環境變數表中標注敏感變數；補充 .env 處理說明（`.gitignore` 和 `.env.example` 說明）。

#### [MEDIUM] 15 — 開發工作流程說明缺失
**Check**: README 是否說明貢獻開發的工作流程（Fork → Branch → PR 流程）？是否說明 Commit Message 格式規範（若有）？是否有 Code of Conduct 引用？
**Risk**: 無貢獻流程說明，外部貢獻者不知道如何提交 PR、使用什麼分支命名規則，導致 PR 格式混亂。
**Fix**: 補充 Contributing 章節，說明 Fork/Branch/PR 流程；若有 Conventional Commits 規範，補充 Commit Message 格式說明；引用 Code of Conduct。

#### [MEDIUM] 16 — Troubleshooting 過於泛化
**Check**: README 的 Troubleshooting 章節是否有 ≥ 5 條針對本專案的具體問題（而非「重開機試試」「清除快取」等通用建議）？是否包含常見的環境設置問題（如 Port 衝突、DB 連線失敗）和對應的診斷命令？
**Risk**: 泛化的 Troubleshooting 在工程師遇到具體問題時完全無用，且讓工程師對專案文件品質產生負面印象。
**Fix**: 補充 ≥ 5 條本專案特有的 Troubleshooting 條目（從 LOCAL_DEPLOY.md 的 Common Issues 萃取）；每條包含問題描述、診斷命令和解決方案。

---

### Layer 5: 維護與貢獻（由 Developer Advocate 主審，共 2 項）

#### [MEDIUM] 17 — Changelog 和版本管理說明缺失
**Check**: README 是否說明如何查看 Changelog（連結到 GitHub Releases 或 CHANGELOG.md）？是否說明版本號碼規則（SemVer 或其他）？Badges 是否包含 Version badge（連結到最新 Release）？
**Risk**: 無 Changelog 說明，使用者無法得知版本之間的差異和升級注意事項；無版本 badge 讓讀者不確定 README 對應哪個版本。
**Fix**: 補充 Changelog 連結（指向 GitHub Releases）；在 README 頭部加入 Version badge；若使用 SemVer，說明 major/minor/patch 的語意。

#### [LOW] 18 — 裸 Placeholder 掃描
**Check**: README 全文掃描是否有任何 `{{PLACEHOLDER}}`、`<VARIABLE>`、`YOUR_XXX`、`example.com` 格式的未替換佔位符？重點掃描：專案名稱、GitHub Repo URL、Badge URL、Tech Stack 版本、Quick Start 命令、環境變數預設值。列出所有未替換的佔位符及其位置（章節）。
**Risk**: 含裸 placeholder 的 README 讓讀者感覺文件未完成，降低專案的可信度；部分佔位符（如錯誤的 CI badge URL）會顯示為破圖，影響第一印象。
**Fix**: 替換所有裸 placeholder 為真實值（來自上游文件）；無法確定的值加上 `（待確認：描述）` 說明而非保留裸佔位符。
