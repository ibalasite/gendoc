---
doc-type: runbook
target-path: docs/RUNBOOK.md
reviewer-roles:
  primary: "資深 SRE（Google/AWS SRE 等級）"
  primary-scope: "可執行性、故障診斷覆蓋度、命令正確性、Rollback 完整性、決策樹品質"
  secondary: "安全工程師"
  secondary-scope: "§11 安全程序、Credentials 管理、最小權限原則、明文密碼檢查、WAF 命令完整性、Audit Log 查詢"
  tertiary: "技術文件專家"
  tertiary-scope: "結構一致性、佔位符完整性、Cross-reference 正確性、Table of Contents anchor 驗證"
quality-bar: "凌晨 3 點被叫醒，零前情提要，能直接執行，不需問任何人。"
pass-conditions:
  - "CRITICAL 數量 = 0"
  - "Self-Check：template 所有 ## 章節（≥17 個）均存在且有實質內容"
  - "所有操作步驟有驗證指令（不只有文字說明）"
upstream-alignment:
  - field: Availability SLO 數字
    source: EDD §10.5 SLO/SLI
    check: Runbook §3.2 的數字是否與 EDD §10.5 完全一致
  - field: Latency P99 目標（ms）
    source: EDD §10.5 SLO/SLI
    check: Runbook §3.2 的 P99 閾值是否與 EDD §10.5 完全一致
  - field: Error Rate SLO（%）
    source: EDD §10.5 SLO/SLI
    check: Runbook §3.2 的 Error Rate 是否與 EDD §10.5 完全一致
  - field: K8s namespace
    source: EDD §7 資源規格
    check: Runbook §2 kubectl 命令的 namespace 是否一致
  - field: API Deployment 名稱
    source: EDD §7 / §9 CI/CD
    check: Runbook §4 / §7 / §9 的 deployment 名稱是否一致
  - field: RTO/RPO
    source: EDD §13.5 DR 設計
    check: Runbook §10.1 的 RTO/RPO 是否與 EDD §13.5 完全一致
---

# runbook Review Items

本檔案定義 `docs/RUNBOOK.md` 的審查標準。由 `/reviewdoc runbook` 讀取並遵循。
審查角色：三角聯合審查（資深 SRE + 安全工程師 + 技術文件專家）
審查標準：「假設公司聘請一位 15 年 SRE 資深顧問，以最嚴格的業界標準進行 Runbook 驗收審查。」

---

## Review Items

### Layer 1: 可執行性（由 SRE 主審，共 6 項）

#### [CRITICAL] 1 — §2/§4/§7/§9 kubectl 命令裸 Placeholder
**Check**: §2、§4、§7、§9 中所有 kubectl 命令的 `-n <namespace>` 和 `deployment/<name>` 是否使用真實名稱（非 `{{PLACEHOLDER}}` 格式空白）？逐一列出發現的空白 placeholder。
**Risk**: 凌晨 3 點照著空白 placeholder 下命令，kubectl 找不到資源，問題繼續惡化。
**Fix**: 替換所有裸 placeholder 為真實的 namespace 和 deployment 名稱（來自 EDD §7）。

#### [CRITICAL] 2 — §7 診斷命令缺少 Expected / If-this-fails
**Check**: §7 Troubleshooting 每個診斷命令是否都有 `# Expected:` 說明預期輸出，以及 `# If this fails:` 的處理路徑？缺少其中任一者即為 finding。逐一列出缺失命令。
**Risk**: SRE 執行命令後不知道輸出是否正常，無法判斷是繼續診斷還是已解決。
**Fix**: 為每個診斷命令補充 `# Expected: <正常輸出描述>` 和 `# If this fails: <下一步操作>`。

#### [HIGH] 3 — §7 決策樹覆蓋度不足
**Check**: §7 每個 Troubleshooting 場景的決策樹（Mermaid flowchart）是否覆蓋現實中最常見的 3–5 種故障根因？決策樹的葉節點是否都指向具體操作（而非「聯絡相關團隊」）？
**Risk**: 決策樹覆蓋不足，SRE 遇到分支外的根因時茫然無措，需要猜測下一步。
**Fix**: 補充缺少的根因分支，將「聯絡相關團隊」替換為具體的診斷或降級操作。

#### [HIGH] 4 — §9 Rollback 非完整自包含
**Check**: §9 Rollback 程序是否完整自包含？每個步驟是否都有完整命令，不依賴「見上方步驟」或「參考 §4」的交叉引用？
**Risk**: 凌晨 3 點翻到 §9 發現需要先看 §4，情急之下容易漏步驟，導致 rollback 不完整。
**Fix**: 將 §9 中所有交叉引用替換為完整的命令副本（可以與 §4 重複，但必須自包含）。

#### [HIGH] 5 — §9.3 Regional Failover 缺少 Replication Lag 警告
**Check**: §9.3 Regional Failover（若存在）是否包含資料對齊/replication lag 的量化警告和具體檢查命令？
**Risk**: 在 replication lag 過大時觸發 failover，會造成資料丟失，且 SRE 無法提前評估影響。
**Fix**: 補充 replication lag 量化檢查命令（e.g., `SELECT ... FROM pg_stat_replication`）和可接受閾值說明。

#### [CRITICAL] 6 — §4/§6/§9 逐步驗證命令缺失
**Check**: §4（Deployment）、§6（Incident Response）、§9（Rollback）每個「主要步驟」（涉及狀態變更的 `kubectl apply`/`rollout`/`exec`/`delete` 等）之後，是否都有對應的驗證命令？檢查標準：每個狀態變更步驟後若無任何驗證指引，視為 finding。逐一列出缺少驗證命令的步驟。
**Risk**: SRE 在凌晨 3 點執行 rollout 後無法判斷成功或靜默失敗，等業務反映才發現，延長 MTTR。
**Fix**: 在每個 `kubectl apply`/`rollout restart`/`exec` 等步驟後補充驗證指令（含 Expected 輸出），例如：
- deploy 後 → `kubectl rollout status deployment/<name> -n <ns>` `# Expected: "successfully rolled out"`
- DB migrate 後 → `kubectl exec ... -- <migrate_status_cmd>` `# Expected: "No pending migrations"`
- rollback 後 → `kubectl get pods -n <ns>` `# Expected: 所有 pod STATUS = Running`

#### [HIGH] 6b — §9 Rollback 後缺少全套測試驗證
**Check**: §9 Rollback 程序最後是否要求執行完整測試驗證（Unit test + Integration test + E2E smoke test）？僅靠 pod running 狀態不足以確認功能正常（可能 DB schema 不兼容前版 code）。
**Risk**: Rollback 後 pod 啟動正常但邏輯回歸，缺少測試閉環等同 Runbook 沒有完成標準。
**Fix**: 在 §9 末尾補充「Rollback 後全套驗證」步驟：
- Unit test：`{{TEST_UNIT_CMD}}`（填入真實指令）
- Integration test：`kubectl exec ... -- {{TEST_INTEGRATION_CMD}}`（填入真實指令）
- E2E smoke test：`npx playwright test --grep @smoke --base-url http://{{PROJECT_SLUG}}.local`（填入真實 slug）
- 全部通過 → 視為 Rollback 完成，可觸發 On-Call Handoff

#### [MEDIUM] 6c — §4/§7 bash/kubectl 命令語法
**Check**: §4 和 §7 中所有 bash/kubectl 命令的語法是否正確？常見錯誤：不存在的 flag、錯誤的 resource 類型、watch 命令使用雙引號導致 subshell 展開問題。
**Risk**: 語法錯誤的命令在緊急事件中浪費寶貴診斷時間。
**Fix**: 逐一修正語法錯誤，確保每個命令可以 copy-paste 執行。

---

### Layer 2: 完整性（由 SRE + 文件專家聯合審查，共 6 項）

#### [CRITICAL] 7 — §3.2 SLO 數字與上游不一致
**Check**: §3.2 SLO 表格中的數字（Availability %、P99 ms、Error Rate %）是否與上游對齊數字（EDD §10.5）完全一致？若 EDD 存在且數字不符，視為 CRITICAL。
**Risk**: SLO 數字錯誤導致 Error Budget 計算錯誤，Alert 閾值設定不正確，無法準確判斷是否在 SLO burn rate 內。
**Fix**: 以 EDD §10.5 的數字為準，修正 §3.2 所有 SLO 數字，並重新計算 Error Budget。

#### [HIGH] 8 — §5.2 Alert 與 §7 場景對應缺失
**Check**: §5.2 Alert Reference Table 是否覆蓋 §7 所有 Troubleshooting 場景？每個 §7 場景是否有對應的 Alert 名稱，且 Runbook Section 欄位的 anchor 是否指向正確章節？列出缺失的對應關係。
**Risk**: Alert 觸發後 SRE 找不到對應的 Troubleshooting 章節，延遲問題診斷。
**Fix**: 補充缺少的 Alert 條目，或修正 Runbook Section anchor 指向正確的 §7.x 子章節。

#### [HIGH] 9 — §10.1 RTO/RPO 與 EDD 不一致
**Check**: §10.1 Backup 中的 RTO/RPO 數字是否與上游對齊數字（EDD §13.5）完全一致？若不一致或 EDD 不存在而 RTO/RPO 缺失，視為 HIGH。
**Risk**: RTO/RPO 數字錯誤導致 DR drill 的通過標準不準確，真實 DR 時無法判斷是否達標。
**Fix**: 以 EDD §13.5 的數字為準，修正 §10.1 的 RTO/RPO 值。

#### [HIGH] 10 — §14 On-Call Handoff 無可直接使用的 Slack 範本
**Check**: §14 On-Call Handoff 是否存在且包含可直接貼上 Slack 的訊息範本（含狀態、進行中事項、Grafana 連結欄位）？
**Risk**: 缺少標準化 Handoff 範本，每次換班的交接品質不一，容易遺漏重要資訊。
**Fix**: 補充 On-Call Handoff Slack 訊息範本，包含 PROJECT_NAME、日期、狀態、Grafana 連結等欄位。

#### [MEDIUM] 11 — §15 Validation 缺少具體測試場景
**Check**: §15 Runbook Validation Procedure 是否有至少 3 個具體測試場景，每個場景有明確通過標準（例如：執行時間 ≤ SLA、命令 exit 0）？「定期測試」類泛化描述視為 finding。
**Risk**: 無法驗證 Runbook 是否真的可執行；真實事件發生時才發現步驟錯誤。
**Fix**: 補充至少 3 個具體測試場景（Monthly DB 連線池壓測、Quarterly DR Drill、New On-Call walkthrough），每個含通過標準。

#### [MEDIUM] 12 — §6.8 Post-Mortem 三要素不完整
**Check**: §6.8 Post-Mortem 是否有完整的生命週期說明：草稿截止日（2 business days）、分發給參與者、30 天 check-in 排程？缺少任一元素視為 finding。
**Risk**: Post-Mortem 流程不完整，後續追蹤 action items 容易被遺忘，同類事件再次發生。
**Fix**: 補充缺少的要素（草稿截止 2 business days、分發對象說明、incident date + 30 天 check-in）。

---

### Layer 3: 安全性（由安全工程師主審，共 5 項）

#### [CRITICAL] 13 — §10.2 DB Restore 明文 Credentials
**Check**: §10.2 DB Restore（或任何 psql 命令）中是否有任何 Credentials 以明文出現在 kubectl exec 命令中？正確格式：`kubectl exec ... -- psql -U <DB_USER> -d <DB_NAME>`，密碼從 K8s Secret 讀取，不出現在命令行。
**Risk**: 明文密碼進入 shell 歷史記錄，可能被系統日誌、audit log 記錄，造成 Credentials 洩漏風險。
**Fix**: 移除命令行中的密碼參數，改為說明「密碼從 K8s Secret 讀取」，並提供 kubectl exec 的正確格式。

#### [CRITICAL] 14 — §11.3 Compromised Credentials 缺少 15 分鐘 SLA
**Check**: §11.3 Compromised Credentials 是否明確定義 15 分鐘撤銷 SLA，以及具體的撤銷步驟（kubectl delete secret → recreate → pod restart 順序）？
**Risk**: 缺少明確 SLA 的安全響應流程，在 Credentials 洩漏事件時無法確保及時撤銷，延長曝露時間。
**Fix**: 補充「撤銷 SLA：15 分鐘內」說明，並列出完整的撤銷步驟（含 secret delete、recreate、rolling restart）。

#### [HIGH] 15 — §11.1 Secret Rotation 順序錯誤
**Check**: §11.1 Secret Rotation 是否覆蓋 DB Credential 輪換的正確順序：必須先在 PostgreSQL 執行 `ALTER USER <user> WITH PASSWORD '<new>'`，再更新 K8s Secret，最後 Rolling Restart Pod。
**Risk**: 若順序錯誤（先更新 K8s Secret 再改 DB），Pod restart 後新密碼的 Pod 無法連線 DB（DB 密碼尚未更新），導致服務中斷。
**Fix**: 明確標注步驟順序（1→2→3），並說明順序錯誤的後果。

#### [HIGH] 16 — §11.4 WAF Block 命令不完整
**Check**: §11.4 WAF Block（若存在）的 `aws wafv2 update-web-acl` 命令是否完整（含 `--scope`、`--id`、`--default-action`、`--visibility-config` 四個必要 flag）？缺少任一 flag 命令無法執行。
**Risk**: WAF 命令缺少必要 flag，緊急情況下執行失敗，無法即時封鎖惡意流量。
**Fix**: 補充缺少的 flag，提供完整可執行的 `aws wafv2 update-web-acl` 命令。

#### [MEDIUM] 17 — §11.5 Audit Log Query 泛化
**Check**: §11.5 Audit Log Query（若存在）是否提供具體的查詢命令和時間窗口過濾參數？「查看 Audit Log」類泛化說明視為 finding。
**Risk**: 泛化的 Audit Log 說明無法指導 SRE 快速查找安全事件的相關記錄。
**Fix**: 補充具體的查詢命令（含 Elasticsearch/CloudWatch/BigQuery 查詢範例），以及 time range、filter 參數說明。

---

### Layer 4: 結構一致性（由技術文件專家主審，共 3 項）

#### [HIGH] 18 — Table of Contents Anchor 失效
**Check**: Table of Contents（§目錄）的每個 anchor link 是否有效？逐一確認每個 `[§X.Y Title](#anchor)` 是否對應實際章節標題（anchor = 標題小寫 + 空格換連字號 + 移除特殊字元）。列出所有無效的 anchor。
**Risk**: 失效的 anchor link 讓 SRE 在緊急事件中無法快速跳轉到所需章節，浪費寶貴時間。
**Fix**: 修正失效的 anchor link，確保與實際章節標題完全對應。

#### [MEDIUM] 19 — 裸 Placeholder 掃描
**Check**: 文件中是否有裸的 `{{PLACEHOLDER}}` 格式（雙大括號包裹文字）且既無格式範例說明也無 TODO 注釋的空白佔位符？注意：帶有格式範例的佔位符（如 `{{GITHUB_ORG}}/{{REPO_NAME}}`）允許保留；只有完全空白、無資訊的 placeholder 才是 finding。列出所有違規的裸 placeholder 及其位置（章節）。
**Risk**: 裸 placeholder 讓 SRE 在執行時遇到「命令包含未替換的模板字符串」錯誤。
**Fix**: 對每個裸 placeholder，填入真實值或加上格式範例說明（`（格式範例：XXX）`）。

#### [LOW] 20 — 交叉引用不一致
**Check**: §7 或其他章節中的交叉引用（如「見 §7.1」「參見 §9.3」）是否指向正確章節號碼和標題？列出不一致的引用。
**Risk**: 錯誤的章節引用讓 SRE 翻到錯誤章節，浪費時間，降低對 Runbook 的信任。
**Fix**: 修正所有不一致的交叉引用，確保章節號碼和標題與實際章節完全匹配。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/runbook.md`，提取所有 `^## ` heading（含條件章節），共約 17 個
2. 讀取 `docs/runbook.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
