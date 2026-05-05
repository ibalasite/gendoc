---
doc-type: LOCAL_DEPLOY
target-path: docs/LOCAL_DEPLOY.md
reviewer-roles:
  primary: "資深 Kubernetes / DevOps 工程師（Google/HashiCorp 等級）"
  primary-scope: "命令可執行性、K8s 資源正確性、Port 一致性、Namespace 一致性、Inner Loop 品質、Makefile 等同命令覆蓋度、Prerequisites 版本完整性"
  secondary: "安全工程師"
  secondary-scope: "Secret 管理方式（無明文密碼）、.gitignore 覆蓋、mkcert 正確性、imagePullPolicy 安全性、K8s RBAC 注意事項、secrets.env 建立方式"
  tertiary: "技術文件專家"
  tertiary-scope: "結構完整性、Placeholder 覆蓋度、Cross-reference 一致性、Quick Start 可操作性、Common Issues 可診斷性"
quality-bar: "新進工程師第一天，依此文件操作，5 分鐘內跑起完整本地 K8s 環境，不需問任何人。"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥23 個）均存在且有實質內容"
  - "支援 ≥ 2 API server replica 的啟動方式"
  - "所有指令可直接複製執行（無需替換 placeholder）"
upstream-alignment:
  - field: K8s Namespace
    source: EDD §3.5 環境矩陣 Local 欄
    check: LOCAL_DEPLOY 全文 namespace 是否與 EDD Local Namespace 完全一致
  - field: API Port
    source: EDD §3.5 服務 Port 對照表
    check: LOCAL_DEPLOY §5 / §12 中 api-server port 是否與 EDD 一致
  - field: DB Port（port-forward）
    source: EDD §3.5 服務 Port 對照表
    check: LOCAL_DEPLOY §5 / §12 中 postgres port-forward 是否與 EDD 一致
  - field: Redis Port（port-forward）
    source: EDD §3.5 服務 Port 對照表
    check: LOCAL_DEPLOY §5 / §12 中 redis port-forward 是否與 EDD 一致
  - field: Backend Runtime
    source: EDD §3.3 技術棧
    check: LOCAL_DEPLOY §1 Prerequisites 中 Runtime 版本是否與 EDD 一致
  - field: PROJECT_SLUG
    source: EDD Document Control
    check: LOCAL_DEPLOY 全文 slug 格式是否與 EDD Project Slug 一致
---

# LOCAL_DEPLOY Review Items

本檔案定義 `docs/LOCAL_DEPLOY.md` 的審查標準。由 `/reviewdoc local-deploy` 讀取並遵循。
審查角色：三角聯合審查（K8s/DevOps 工程師 + 安全工程師 + 技術文件專家）
審查標準：「假設公司聘請一位 10 年 Kubernetes 資深顧問，以最嚴格的業界標準進行本地開發環境文件驗收。」

---

## Review Items

### Layer 1: 命令可執行性（由 K8s/DevOps 工程師主審，共 6 項）

#### [CRITICAL] 1 — §3/§4 kubectl namespace 一致性
**Check**: §3（Quick Start）和 §4（Step-by-Step）中所有 `kubectl` 命令的 `-n <namespace>` 是否使用真實 namespace 名稱（非裸 `{{PLACEHOLDER}}` 格式空白）？若文件中 K8S_NAMESPACE 和 PROJECT_SLUG 均為 placeholder，視為合規模板（非 finding）；若部分命令已填入真實值而其他仍為 placeholder，視為不一致 finding。
**Impact**: 命令帶錯誤 namespace 執行會靜默失敗，新進工程師無法判斷操作是否成功。
**Fix**: 逐一替換不一致的命令，或統一改為模板格式並加注釋。

#### [CRITICAL] 2 — §4.4 nerdctl vs docker / imagePullPolicy: Never
**Check**: §4.4（Build & 載入 Image）是否明確說明使用 `nerdctl` 而非 `docker`（Rancher Desktop 使用 containerd runtime），且是否包含 `imagePullPolicy: Never` 的說明？缺少其中任一者即為 finding。
**Impact**: 使用 `docker` 命令在 Rancher Desktop 上 build 的 image 無法被 containerd 識別；未設 `imagePullPolicy: Never` 會導致 K8s 嘗試從外部 registry 拉取 local image 失敗。
**Fix**: 將所有 build 命令改為 `nerdctl`，並在 §4.4 或 §2 明確記載 `imagePullPolicy: Never`。

#### [HIGH] 3 — §4.6 Migration 命令格式正確性
**Check**: §4.6（初始化資料庫）的 migration 命令格式是否正確：`kubectl exec -n <namespace> deploy/api-server -- <MIGRATE_CMD>`？若 MIGRATE_CMD 為裸 placeholder（`{{MIGRATE_CMD}}`）且無任何說明，視為 MEDIUM；若有格式範例佔位符說明，視為合規。
**Impact**: Migration 命令格式錯誤會導致 DB schema 不一致，應用程式無法啟動。
**Fix**: 補充真實的 migration 命令（依 ORM 推斷），或加上格式範例說明。

#### [HIGH] 4 — §5/§12 port-forward Port 一致性
**Check**: §5（Service Reference）port-forward 表中的 port 號碼是否與 §12（Port Reference）完全一致？逐一比對每個服務的 local port，找出矛盾。
**Impact**: port 號碼矛盾會讓新進工程師設定錯誤的 port-forward，導致服務連線失敗。
**Fix**: 統一使用 §12 Port Reference 的數字，修正矛盾的 §5 或 §12 條目。

#### [HIGH] 5 — §4.2 /etc/hosts 設定步驟
**Check**: §4.2（Rancher Desktop 設定）是否包含 `/etc/hosts` 設定步驟，且格式為 `127.0.0.1 {{PROJECT_SLUG}}.local`？這是 Ingress 解析的必要步驟。
**Impact**: 缺少 /etc/hosts 設定，瀏覽器和 curl 無法解析 `*.local` domain，Quick Start 的 health check 全部失敗。
**Fix**: 在 §4.2 補充 /etc/hosts 設定步驟。

#### [MEDIUM] 6 — §6 make 指令等同底層命令覆蓋度
**Check**: §6（Development Commands）每個 `make` 指令是否都有「等同的底層 kubectl/nerdctl 命令」說明？若 make 指令只有名稱無等同命令，開發者在 Makefile 不存在時無法手動執行。逐一列出缺少等同命令的 make 指令。
**Impact**: 在新環境或 Makefile 異常時，開發者無法手動執行等同操作，降低可靠性。
**Fix**: 在每個 make 指令旁補充完整的底層 kubectl/nerdctl 命令。

---

### Layer 2: K8s 架構完整性（由 K8s/DevOps 工程師主審，共 5 項）

#### [CRITICAL] 7 — §2 K8s 資源對照表完整性
**Check**: §2（Architecture Overview）中的 K8s 資源對照表是否涵蓋所有在 Quick Start 和 Step-by-Step 中出現的服務（api-server、web-app、worker、cron-scheduler、postgres、redis、minio、mailpit、pgadmin）？若某服務在 §3/§4 出現但 §2 資源對照表未列，視為 HIGH finding。
**Impact**: 缺少服務的 K8s 資源定義，新進工程師無法快速了解部署拓撲，難以排障。
**Fix**: 補充缺少服務的 K8s 資源對照表條目（含 image、resource limits、健康檢查端點）。

#### [CRITICAL] 8 — §9 ConfigMap DATABASE_URL 使用 K8s internal DNS
**Check**: §9（ConfigMap & Secret Reference）中 ConfigMap `{{PROJECT_SLUG}}-api-config` 的 `DATABASE_URL` 值是否使用 K8s internal DNS（`postgres://app:secret@postgres:5432/...`），而非 `localhost` 或 port-forward 位址？
**Impact**: 使用 localhost 會導致 pod 內部無法連線 DB，應用程式啟動失敗；而這是最常犯的錯誤之一。
**Fix**: 將 DATABASE_URL 的 host 改為 K8s service 名稱 `postgres`。

#### [HIGH] 9 — §9 ConfigMap REDIS_URL 使用 K8s internal DNS
**Check**: §9（ConfigMap & Secret Reference）中 `REDIS_URL` 值是否使用 K8s internal DNS（`redis://redis:6379/0`），而非 `localhost:6379`？
**Impact**: 同 §9 DATABASE_URL 問題，使用 localhost 導致 pod 內部無法連線 Redis。
**Fix**: 將 REDIS_URL 的 host 改為 K8s service 名稱 `redis`。

#### [HIGH] 10 — §15 Inner Loop 完整性
**Check**: §15（Inner Loop）是否涵蓋後端快速迭代方法（build + rollout restart）和 skaffold 自動偵測兩種模式？若只有一種，視為 MEDIUM；若兩種都缺失，視為 HIGH。
**Impact**: 缺少 inner loop 說明，每次程式碼更改需要完整重新部署，大幅降低開發效率。
**Fix**: 補充 nerdctl build + kubectl rollout restart 步驟，以及 skaffold dev --profile local 命令。

#### [MEDIUM] 11 — §2 Architecture 圖 Port 一致性
**Check**: §2（Architecture）的 ASCII 架構圖或 Mermaid 圖中，所有服務節點標注的 port 號碼是否與 §12（Port Reference）一致？
**Impact**: 架構圖與 Port Reference 矛盾，新進工程師無法確認哪個是權威數字。
**Fix**: 以 §12 Port Reference 的數字為準，修正架構圖中的 port 標注。

---

### Layer 3: 安全性（由安全工程師主審，共 7 項）

#### [CRITICAL] 12 — §7 明文密碼無安全警示
**Check**: §7（Database Operations）的 psql 連線字串中是否有明文密碼（如 `postgres://app:secret@...`）且**未加任何「本地開發用，禁止生產使用」注釋**？若已有注釋說明僅本機開發使用，視為合規。
**Impact**: 開發者可能複製 psql 命令至 staging/production 環境，造成生產資料庫安全風險。
**Fix**: 在所有含明文密碼 `secret` 的連線字串前，加入安全警示注釋或 blockquote。

#### [CRITICAL] 13 — §4.3 secrets.env .gitignore 說明 + --from-env-file
**Check**: §4.3（建立 K8s Secret）是否明確說明 `secrets.env` 已加入 `.gitignore`，且建立 Secret 使用 `--from-env-file` 方式而非 `--from-literal`？缺少 .gitignore 說明視為 CRITICAL。
**Impact**: 若 secrets.env 進入 git 歷史，所有開發者和 git hosting 都能看到明文密碼；`--from-literal` 會把密碼暴露在 shell 歷史記錄中。
**Fix**: 在 §4.3 明確說明 secrets.env 已加入 .gitignore，並將 Secret 建立命令改為 `--from-env-file`。

#### [HIGH] 14 — §13 Local HTTPS 使用 mkcert
**Check**: §13（Local HTTPS 設定）是否使用 `mkcert` 生成憑證，而非 `openssl` 自簽？自簽憑證無法被瀏覽器信任。
**Impact**: 使用 openssl 自簽憑證且未說明信任步驟，開發者每次訪問都會看到安全警告，影響開發體驗，且可能養成繞過 TLS 的壞習慣。
**Fix**: 將憑證生成命令改為 `mkcert`，並說明 `mkcert -install` 步驟。

#### [HIGH] 15 — §4.4/§2 imagePullPolicy: Never 明確記載
**Check**: §4.4（Build & 載入 Image）或 §2（Architecture）是否明確記載本地 image 使用 `imagePullPolicy: Never`？
**Impact**: 未明確記載 `imagePullPolicy: Never` 的文件會導致新進工程師不知需在 K8s manifest 設定此項，K8s 嘗試從外部 registry 拉取 local image 失敗。
**Fix**: 在 §4.4 或 §2 補充 `imagePullPolicy: Never` 的說明。

#### [MEDIUM] 16 — §9 Secret 表格無實際值
**Check**: §9（ConfigMap & Secret Reference）中 Secret 表格是否只列出 Key 名稱，不填入任何實際值（包含「預設值」範例密碼）？若 Secret 表格的「說明」欄有任何看起來像真實密碼的值（如：`Password1!`、`my-secret-key`），視為 finding。
**Impact**: 文件中出現密碼範例值，開發者可能誤用為真實值，降低安全性。
**Fix**: 移除 Secret 表格中所有看起來像真實密碼的值，只保留 Key 名稱說明。

#### [CRITICAL] 16b — .env 或 secrets.env 可能進 git
**Check**: `.gitignore` 是否包含以下全部規則：`*.env`、`secrets.env`、`.env.*`？缺少任一規則視為 CRITICAL。同時確認 §3.5 Secret Bootstrap 段落存在且明確聲明禁止規則。若 §3.5 不存在，視為 CRITICAL。
**Risk**: `.env` 或 `secrets.env` 進入 git 歷史 → 所有有 repo 存取權的人均能看到明文密碼；即使之後刪除，git 歷史仍保留，需 `git filter-repo` 才能徹底清除。
**Fix**: (1) 在 `.gitignore` 補充 `*.env`、`secrets.env`、`.env.*` 規則；(2) 在 §3.5 Secret Bootstrap 明確說明禁止規則清單；(3) 驗證 `git check-ignore -v secrets.env` 輸出顯示已被忽略。

#### [HIGH] 16c — 靜態密碼無重生成機制
**Check**: §3.5 Secret Bootstrap 中，`bootstrap-secrets.sh` 和 `bootstrap-secrets.ps1` 是否使用 `openssl rand`（bash）或 PowerShell CSPRNG 生成隨機密碼？若 script 中出現任何硬編碼密碼值（如 `DB_PASSWORD=secret123`），視為 HIGH。若 §3.5 完全不存在，升級為 CRITICAL。
**Risk**: 靜態密碼模式可被猜測；多個開發者使用相同密碼，一人洩漏影響全團隊；靜態密碼可能被意外複製到 staging/production。
**Fix**: 確認 bootstrap script 使用 `openssl rand -hex 32` 或 PowerShell `[System.Security.Cryptography.RandomNumberGenerator]::Create()` 生成密碼，不得有任何 literal password 值。

---

### Layer 4: 文件品質（由技術文件專家主審，共 4 項）

#### [HIGH] 17 — §10 Common Issues 完整性
**Check**: §10（Common Issues & Fixes）是否涵蓋以下 K8s 本地開發最常見的 5 類問題？缺少任一類視為 HIGH：
- Pod stuck in `Pending`（資源不足）
- `CrashLoopBackOff`（應用程式崩潰）
- `ImagePullBackOff`（image 未 build 或 tag 錯誤）
- Ingress 無法解析（/etc/hosts 未設定）
- DB 連線拒絕（postgres pod 未就緒）
**Impact**: 新進工程師第一天最可能遇到這 5 類問題；若 §10 缺少對應診斷步驟，等於需要詢問他人。
**Fix**: 補充缺少的問題類型，每類問題需有具體診斷命令和修復步驟。

#### [CRITICAL] 18 — 指令區塊中裸 Placeholder
**Check**: 所有在 shell code block（``` ``` ``` 包裹）內出現的 `{{PLACEHOLDER}}` 是否已全部替換為真實值？特別檢查：`{{PROJECT_SLUG}}`、`{{K8S_NAMESPACE}}`、`{{API_PORT}}`、`{{WEB_PORT}}`、`{{DB_PORT}}`、`{{REDIS_PORT}}`、`{{MIGRATE_CMD}}`、`{{SEED_CMD}}`、`{{TEST_UNIT_CMD}}`、`{{TEST_INTEGRATION_CMD}}`。帶有格式範例說明的（如 `{{PROJECT_SLUG}}-local` 出現在注釋行）允許保留；shell 指令行中的裸 placeholder 一律視為 CRITICAL finding。
**Impact**: 工程師直接 copy-paste 含裸 placeholder 的指令會立即報錯，無法執行任何操作。等同文件失效。
**Fix**: 從 EDD §3.5 / test-plan.md 提取對應真實值並填入所有 shell code block 中的 placeholder。

#### [HIGH] 18b — 測試指令可執行性
**Check**: §6（Testing & Verification）中的測試指令是否完整且可執行？具體檢查：
- Unit test 指令是否具體（`npm test`/`pytest`/`go test ./...` 等，非裸 `{{TEST_UNIT_CMD}}`）？
- Integration test 指令是否包含正確的容器執行方式（`kubectl exec`）？
- E2E test 指令的 `--base-url` 是否使用真實 domain（`http://{{PROJECT_SLUG}}.local`，其中 slug 已填入）？
- 每個測試指令後是否有 Expected 輸出說明？
**Impact**: 測試指令不具體或含裸 placeholder，工程師完成部署後無法驗證系統，缺乏品質閘門。
**Fix**: 從 test-plan.md 提取具體測試指令；將每個指令補充 Expected 輸出（如 `# Expected: X tests passed`）。

#### [MEDIUM] 19 — §8 Default User Accounts 完整性
**Check**: §8（Test Data & Fixtures）Default User Accounts 表格是否包含至少 3 種角色（Admin、Regular User、Read-only 或類似角色）？且每個帳號的 email 格式是否使用 `{{PROJECT_SLUG}}.local` domain（與 Ingress domain 一致）？
**Impact**: 測試帳號不完整，新進工程師無法驗證所有權限等級的功能。
**Fix**: 補充缺少的角色，並統一使用 `xxx@{{PROJECT_SLUG}}.local` 格式的 email。

#### [MEDIUM] 19b — 裸 Placeholder 掃描（非指令區塊）
**Check**: 文件正文（非 code block）是否有裸的 `{{PLACEHOLDER}}` 格式且**既無格式範例說明也無 TODO 注釋**的空白佔位符？列出所有違規的裸 placeholder 及其位置。（Code block 內的裸 placeholder 已由 [CRITICAL] 18 覆蓋）
**Impact**: 裸 placeholder 讓新進工程師不知道需要填什麼，導致操作失敗。
**Fix**: 對每個裸 placeholder，填入真實值或加上格式範例說明。

#### [MEDIUM] 19 — §8 Default User Accounts 完整性
**Check**: §8（Test Data & Fixtures）Default User Accounts 表格是否包含至少 3 種角色（Admin、Regular User、Read-only 或類似角色）？且每個帳號的 email 格式是否使用 `{{PROJECT_SLUG}}.local` domain（與 Ingress domain 一致）？
**Impact**: 測試帳號不完整，新進工程師無法驗證所有權限等級的功能。
**Fix**: 補充缺少的角色，並統一使用 `xxx@{{PROJECT_SLUG}}.local` 格式的 email。

#### [LOW] 20 — §12 Port Reference 完整性
**Check**: §12（Port Reference）的 Ingress 路徑表和 port-forward 表是否完整涵蓋所有在 §2、§5 中出現的服務？若有遺漏服務（如 minio console 路徑），視為 LOW finding。
**Impact**: Port Reference 不完整，新進工程師在設定 port-forward 時需要自己查找正確 port，增加配置錯誤風險。
**Fix**: 補充遺漏的服務條目至 §12 Port Reference。

---

### Layer 5: Docker Compose 輔助方案（由 DevOps 工程師主審，共 3 項）

#### [CRITICAL] 21 — §19 Docker Compose 章節存在且可執行
**Check**: §19（Docker Compose 輔助方案）是否存在？服務對照表中是否有裸 `{{SERVICE_NAME}}`、`{{IMAGE_NAME}}` placeholder？啟動步驟的 port（`{{API_PORT}}`、`{{WEB_PORT}}`）是否已填入真實值？
**Impact**: 缺少 docker-compose 章節或 port 仍為 placeholder，表示輔助方案無法使用，違背「雙路徑可建置」設計目標。新進工程師在不熟悉 k8s 時無替代方案。
**Fix**: 確保 §19 存在；將所有裸 port placeholder 替換為從 EDD §3.5 提取的真實值；服務名稱使用 EDD 定義的短名稱。

#### [HIGH] 22 — §19 測試指令完整性
**Check**: §19 測試區塊是否包含 Unit test、Integration test、E2E test 三類指令？`{{TEST_UNIT_CMD}}`、`{{TEST_INTEGRATION_CMD}}` 是否已替換為真實指令（不得為裸 placeholder）？
**Impact**: 測試指令保留裸 placeholder，工程師在 docker-compose 模式下無法執行任何測試，等同缺少驗證手段。
**Fix**: 從 test-plan.md 或 EDD §6 提取真實測試指令並填入。若純後端專案無前端 E2E，移除前端 E2E 行而非保留 placeholder。

#### [MEDIUM] 23 — §19 架構差異說明
**Check**: §19 對外 Port 表格下方是否有注意事項，說明「docker-compose 模式無 Ingress，各服務各自對外暴露 port，與 K8s 單一 port 80 的差異」？
**Impact**: 缺少差異說明，工程師會誤以為 docker-compose 和 k8s 的 port 行為相同，在 E2E 測試設定時使用錯誤的 base URL。
**Fix**: 在對外 Port 表格後加注意事項，明確說明兩種模式的架構差異。

---

### Layer 5: Local HA 驗證（由 SRE / Backend Lead 主審，共 3 項）

#### [CRITICAL] 24 — API Server 本地副本數 < 2
**Check**: LOCAL_DEPLOY.md 中的 API Server Deployment（K8s）副本數是否 ≥ 2？確認方式：搜尋 `replicas:` 欄位中 API Server 的值；或查看 `kubectl get pods` 範例輸出是否顯示 ≥ 2 個 api-server pod。副本數 = 1 視為 CRITICAL。
**Risk**: Local 環境 API Server 只有 1 個副本，無法測試 HA 相關程式碼（shared session、distributed lock、pub/sub、sticky session 等）；Local 通過測試的程式在 Staging（多副本）失敗，修改成本極高。
**Fix**: 將 API Server Deployment 的 `replicas` 改為 2（或以上）；在 §4 部署確認步驟補充驗證指令：`kubectl get pods -l app=api-server | grep Running | wc -l` 輸出 ≥ 2。

#### [CRITICAL] 25 — Worker 本地副本數 < 2
**Check**: 若系統有 Background Worker（Job Queue 消費者），其 Deployment 副本數是否 ≥ 2？確認 Worker 副本數設定並在 `kubectl get pods` 範例中驗證。
**Risk**: Worker 只有 1 個副本，無法驗證冪等性（同一 Job 是否只執行一次，在兩個 Worker 同時消費時）；也無法測試分散式鎖（Distributed Lock）的正確性。
**Fix**: 將 Worker Deployment 的 `replicas` 改為 2；補充冪等性驗證步驟：送出同一 Job 兩次，確認業務結果只執行一次（DB 記錄不重複）。

#### [HIGH] 26 — 缺少 Local HA 驗證步驟
**Check**: LOCAL_DEPLOY.md 的驗證步驟（§4 或 §6）是否包含 HA 驗證：強制終止一個 API Pod 後，服務是否在 ≤ 5s 內恢復？包含以下指令：`kubectl delete pod <api-pod-name>` + `curl -s http://localhost:8080/health` 驗證？若無此類步驟，視為 HIGH。
**Risk**: 無 HA 驗證步驟，開發者不知道如何在 Local 環境確認 HA 相關功能正常，也無法在 PR 合併前驗證。
**Fix**: 在 §4 Quick Verify 或 §6 驗證步驟新增 HA 驗證區塊（遵循 EDD §3.7 圖 B + test-plan.md §3.6.3）：  
`kubectl delete pod $(kubectl get pods -l app=api-server -o jsonpath='{.items[0].metadata.name}')`  
`sleep 5 && curl -s http://localhost:8080/health | jq .status`  
期望：`"ok"` 或 `200`。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/LOCAL_DEPLOY.md`，提取所有 `^## ` heading（含條件章節），共約 23 個
2. 讀取 `docs/LOCAL_DEPLOY.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
