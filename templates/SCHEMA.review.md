---
doc-type: SCHEMA
target-path: docs/SCHEMA.md
reviewer-roles:
  primary: "資深 Database Architect（Schema 審查者）"
  primary-scope: "正規化設計、索引策略、外鍵完整性、SQL 語法正確性、效能設計"
  secondary: "資深 Backend Engineer"
  secondary-scope: "ORM 對齊、查詢效能、Migration 安全性、資料類型選擇"
  tertiary: "資深 Security Expert"
  tertiary-scope: "PII 欄位識別、資料加密、軟刪除策略、Audit Trail"
quality-bar: "DBA 和後端工程師拿到 SCHEMA.md，能直接執行 SQL 建立完整資料庫，且所有 API endpoint 都能找到對應的資料表和欄位。"
upstream-alignment:
  - field: API.md Resource → Table 對應
    source: API.md §Endpoints
    check: API.md 中每個 Resource 的所有 request/response 欄位是否都能在 SCHEMA 中找到對應的 Table 和欄位
  - field: PRD 功能清單 → Schema 欄位覆蓋
    source: PRD.md §功能清單 / User Stories
    check: SCHEMA 的業務欄位是否支撐所有 PRD P0 功能的資料儲存需求
  - field: EDD 技術選型 → Schema 資料庫選型
    source: EDD.md §技術選型 / §架構設計
    check: SCHEMA 的資料庫類型（PostgreSQL / MySQL）、版本是否與 EDD 技術選型完全一致
  - field: ARCH 組件設計 → Multi-Tenancy 策略
    source: ARCH.md §多租戶設計（若存在）
    check: 若 ARCH 定義了 Multi-Tenancy 策略（RLS / Schema-per-Tenant），SCHEMA 是否實作對應的隔離機制
---

# SCHEMA Review Items

本檔案定義 `docs/SCHEMA.md` 的審查標準。由 `/reviewdoc SCHEMA` 讀取並遵循。
審查角色：三角聯合審查（資深 Database Architect + 資深 Backend Engineer + 資深 Security Expert）
審查標準：「假設公司聘請一位 15 年資深資料庫架構顧問，以最嚴格的業界標準進行 Schema 驗收審查。」

---

## Review Items

### Layer 1: 正規化與設計完整性（由 Database Architect 主審，共 5 項）

#### [CRITICAL] 1 — API Resource 無對應 Table（API-Schema 對齊）
**Check**: 對照 API.md（若存在）的每個 Resource Endpoint，對應的資料表是否在 SCHEMA 中存在？特別檢查：所有 API Response Schema 的欄位是否都能在 SCHEMA 的 Table 欄位中找到（含欄位名稱與資料型別）？列出所有缺漏的 Table 或欄位及其 API 來源。
**Risk**: API Resource 無對應 Table，後端工程師無 Schema 依據，需臨時設計欄位，導致欄位命名不一致、資料模型偏離 API 契約，整合期頻繁出現欄位不匹配。
**Fix**: 為每個 API Resource 補充對應的 Table 定義（含 Primary Key、業務欄位、FK、索引）；確認所有 API Response 欄位都有對應的 Schema 欄位（型別相容）。

#### [CRITICAL] 2 — PRD P0 功能資料缺失
**Check**: 對照 PRD.md（若存在）的 P0 User Stories，每個 P0 功能所需的資料（儲存什麼、查詢什麼、更新什麼）是否都在 SCHEMA 有對應欄位？逐一列出缺少資料支撐的 P0 功能及其在 PRD 中的定義位置。
**Risk**: P0 功能資料缺失，後端工程師 Sprint 中實作時才發現無 Table/欄位可用，需要緊急補充 Migration，影響交付時間表。
**Fix**: 為每個缺少資料支撐的 P0 功能補充對應的 Table 或欄位，並在欄位說明中標注對應的 PRD User Story 編號。

#### [CRITICAL] 3 — 主鍵設計缺失或不一致
**Check**: 每張 Table 是否有明確的 Primary Key？PK 型別是否在全 Schema 一致（統一 UUID v4 或統一 BIGSERIAL）？若混用兩種 PK 型別，是否有業務依據說明（如「外部暴露的資源使用 UUID，內部關聯表使用 BIGSERIAL」）？逐一列出 PK 設計不一致的 Table。
**Risk**: 主鍵缺失導致 ORM 無法正確識別記錄；PK 型別不一致造成 JOIN 時需要隱式型別轉換，INDEX 失效，整體查詢效能下降；UUID 與整數混用在序列化時格式不一致。
**Fix**: 為每張缺少 PK 的 Table 添加主鍵；統一 PK 型別策略並在 §2 通用規範中聲明（建議：外部暴露 Resource 使用 UUID v4，純內部關聯表可用 BIGSERIAL）。

#### [CRITICAL] 4 — FK 關係錯誤或缺少中間表
**Check**: Foreign Key 方向是否符合業務語義（「多」的一方持有 FK）？M:N 關係是否有中間表（Association Table）？中間表是否同時建立兩個 FK 欄位的複合索引？ON DELETE 行為（`CASCADE` / `RESTRICT` / `SET NULL`）是否符合業務需求（如子表資料有業務意義時禁止 CASCADE）？逐一列出錯誤或缺失的 FK。
**Risk**: FK 方向錯誤導致 ORM Mapping 失敗；M:N 無中間表造成非正規化資料重複；ON DELETE CASCADE 在業務有意義的子表上可能造成意外的資料串聯刪除。
**Fix**: 依業務語義修正 FK 方向；為 M:N 關係補充中間表（含兩個 FK 欄位 + 複合索引）；逐一確認每個 ON DELETE 行為有業務依據說明。

#### [HIGH] 5 — 正規化不達 3NF（無文件化理由）
**Check**: 是否有 Table 存在傳遞依賴（非主鍵欄位依賴其他非主鍵欄位）？是否有重複欄位組（違反 1NF，如 `tag1`、`tag2`、`tag3`）？若有反正規化，是否在 Schema 中說明業務依據（如效能優化）並附上 EXPLAIN ANALYZE 佐證？列出所有違反 3NF 且無文件化理由的 Table。
**Risk**: 傳遞依賴導致更新異常（修改一個欄位需同時更新多筆記錄）、插入異常、刪除異常，資料一致性難以保障；無文件化的反正規化讓後續工程師不敢修改也不敢維護。
**Fix**: 將傳遞依賴欄位抽取到獨立 Table，建立 FK；若因效能原因刻意反正規化，必須在 Schema 中加上說明注釋（依據 §4.2 刻意反正規化規則）。

---

### Layer 2: SQL 語法與資料類型（由 Database Architect + Backend Engineer 聯合審查，共 4 項）

#### [CRITICAL] 6 — NOT NULL 約束設定錯誤
**Check**: 業務上必填的欄位是否都標記 `NOT NULL`？允許為空的欄位是否有業務依據說明（為何允許 NULL）？特別檢查：外鍵欄位是否有不應為空但未加 NOT NULL 的情況？逐一審查每張 Table 的欄位 Nullable 設定。
**Risk**: 過度允許 NULL 造成業務邏輯需要大量 NULL 判斷，ORM 生成 nullable 屬性，應用層可能產生 NullPointerException；必填欄位未標 NOT NULL 導致 DB 層無法保障資料完整性，髒資料無聲入庫。
**Fix**: 依業務規則修正 NOT NULL 設定：業務必填欄位加 NOT NULL，業務可選欄位標明 NULL 並在欄位說明中寫明業務理由（如 `-- 選填：使用者可不設定 avatar`）。

#### [HIGH] 7 — 資料類型選用不當
**Check**: 欄位的資料類型是否符合業務需求？常見錯誤：用 `TEXT` 儲存有長度限制的欄位（應用 `VARCHAR(N)`）、用 `FLOAT` 儲存金額（應用 `NUMERIC(12,4)`，避免浮點精度問題）、用 `VARCHAR` 儲存 JSON（應用 `JSONB`）、時間戳使用 `TIMESTAMP` 而非 `TIMESTAMPTZ`（時區問題）。逐一審查高風險欄位的資料類型。
**Risk**: 類型選用不當在資料量小時無感，但在業務規模增長後爆發：FLOAT 金額計算誤差在財務對帳時引發嚴重問題；TIMESTAMP 在多時區環境中造成時間計算錯誤；TEXT 過度使用浪費存儲且無法限制輸入長度。
**Fix**: 修正不當資料類型：金額欄位使用 `NUMERIC(12,4)`；時間戳統一使用 `TIMESTAMPTZ`；有長度業務含義的字串使用 `VARCHAR(N)`；JSON 欄位使用 `JSONB`（支援索引）。

#### [HIGH] 8 — UNIQUE 約束缺失
**Check**: 業務上唯一的欄位組合（如 `email`、`slug`、`user_id + resource_id`）是否有 `UNIQUE` 約束或 `UNIQUE INDEX`？若有軟刪除（`deleted_at`），唯一約束是否使用 Partial UNIQUE Index 排除已刪除記錄（`WHERE deleted_at IS NULL`）？逐一核對業務唯一性規則。
**Risk**: 缺少 UNIQUE 約束，應用層若有 Race Condition（並發請求），DB 層無法防止重複資料插入；軟刪除場景下的唯一約束不加 `WHERE deleted_at IS NULL`，導致刪除後無法重新建立相同記錄。
**Fix**: 為每個業務唯一欄位組合補充 UNIQUE 約束；軟刪除場景使用 Partial UNIQUE Index（`CREATE UNIQUE INDEX ... WHERE deleted_at IS NULL`）。

#### [MEDIUM] 9 — CHECK 約束缺失
**Check**: 業務規則中的值域限制（如 `status IN ('active','inactive')`、`amount > 0`、`percentage BETWEEN 0 AND 100`）是否有 `CHECK` 約束？是否有欄位只在應用層驗證而 DB 層無約束？逐一核對有值域限制的業務欄位。
**Risk**: 缺少 CHECK 約束，業務規則只由應用層保障；若應用層有 Bug 或工程師直接操作 DB，無效資料可以進入資料庫；後續查詢假設欄位值域的邏輯可能產生非預期行為。
**Fix**: 為每個有值域限制的欄位補充 CHECK 約束（枚舉值、正數、百分比範圍等）；業務狀態機的狀態流轉規則可考慮用 CHECK 約束防止非法狀態轉換。

---

### Layer 3: 索引策略（由 Database Architect 主審，共 4 項）

#### [CRITICAL] 10 — 高頻查詢欄位無索引（API 查詢對齊）
**Check**: 對照 API.md 的查詢 Endpoint（若存在），每個 Endpoint 的 WHERE 條件欄位（如 `user_id`、`status`、`tenant_id`、`created_at`）是否在 SCHEMA 有對應索引？外鍵欄位是否都有索引（PostgreSQL 不自動建立外鍵索引）？逐一核對 API WHERE 條件欄位與 SCHEMA 索引定義，列出無索引的高頻查詢欄位。
**Risk**: 高頻查詢欄位無索引導致全表掃描，資料量增大後查詢效能急劇下降（10 萬筆可能從 10ms 劣化到 10s），API P95 延遲 SLO 無法達成。
**Fix**: 為每個 API 高頻 WHERE 條件欄位補充索引；所有外鍵欄位必須有對應索引（`CREATE INDEX idx_{table}_{fk_col} ON {table}({fk_col})`）；在索引定義後加注釋說明對應的查詢模式。

#### [HIGH] 11 — Partial Index 缺失（軟刪除場景）
**Check**: 若 Table 有 `deleted_at` 軟刪除欄位，高頻查詢欄位（`status`、`user_id`、`email`）的索引是否使用 Partial Index（`WHERE deleted_at IS NULL`）？普通索引在軟刪除場景下會將已刪除記錄也納入索引，大幅增加索引體積並降低選擇性。逐一列出缺少 Partial Index 的軟刪除 Table。
**Risk**: 缺少 Partial Index，軟刪除記錄持續累積後索引體積膨脹，已刪除記錄佔比越高，索引利用率越低；在高刪除率的業務場景（如臨時資源、會話管理）下效能退化顯著。
**Fix**: 為軟刪除 Table 的高頻查詢欄位改用 Partial Index（`WHERE deleted_at IS NULL`）；可節省 30-80% 索引大小並提升選擇性。

#### [HIGH] 12 — 複合索引欄位順序錯誤
**Check**: 複合索引的欄位順序是否正確（等值過濾欄位在前，範圍查詢/排序欄位在後）？是否有複合索引將範圍查詢欄位（如 `created_at BETWEEN`）放在中間，導致最左前綴原則失效？逐一列出所有複合索引並評估欄位順序。
**Risk**: 複合索引欄位順序錯誤，後續欄位無法被 Planner 使用（最左前綴原則），查詢退化為部分索引掃描或全表掃描，等同索引白建。
**Fix**: 依查詢模式重新排列複合索引欄位順序：`(等值欄位, 高選擇性欄位, 範圍欄位, 排序欄位)`；參考 §5.3 複合索引欄位順序規則重建所有順序錯誤的複合索引。

#### [MEDIUM] 13 — 索引策略說明缺失
**Check**: 是否對每個非 PK 索引說明創建原因（對應哪個查詢模式、哪個 API Endpoint）？是否有 `CREATE INDEX` 語句缺少注釋說明，維護者無法判斷是否可安全刪除？逐一確認每個非 PK 索引是否有說明注釋。
**Risk**: 無說明的索引隨時間累積，維護者不敢刪除（怕影響效能），也不知道是否有重複索引，過多索引持續拖慢寫入效能（每個寫入需維護所有索引），最終索引維護成本超過查詢收益。
**Fix**: 為每個非 PK 索引補充注釋，說明（1）對應的查詢模式，（2）對應的 API Endpoint 或業務場景；建議在 §5 或各 Table 定義後集中列出索引策略說明。

---

### Layer 4: API-Schema 對齊（由 Backend Engineer 主審，共 3 項）

#### [CRITICAL] 14 — ER Diagram 缺失或不完整
**Check**: SCHEMA 是否包含 ER Diagram（Mermaid `erDiagram` 或等效視覺化圖）？ER Diagram 是否涵蓋所有 Table 及其 FK 關係（1:1 / 1:N / M:N）？是否有 Table 只在 DDL 中定義但未出現在 ER Diagram？逐一確認 ER Diagram 覆蓋率。
**Risk**: 無 ER Diagram，後端工程師需手動解讀多個 Table 的關係，容易遺漏 FK 設計；新進工程師理解資料模型的成本高，容易在 JOIN 查詢時寫出錯誤的關聯條件。
**Fix**: 補充 Mermaid `erDiagram`，涵蓋所有 Table 及 FK 關係，標注關係類型（`||--o{` 一對多、`||--||` 一對一）；每次新增 Table 時同步更新 ER Diagram。

#### [HIGH] 15 — 孤立 Table（無 FK 且無業務說明）
**Check**: 是否有 Table 無任何 FK 指向其他 Table（孤立表）且缺少業務說明（說明為何獨立存在）？逐一列出所有孤立 Table 及其欄位，評估是否為設計遺漏（忘記加 FK）、廢棄 Table（應刪除）、或合理的獨立實體。
**Risk**: 孤立 Table 可能是設計遺漏（忘記加 FK 導致資料無法正確關聯查詢）或廢棄 Table（佔用空間且讓 Schema 難以理解），兩者都增加維護成本並污染資料模型。
**Fix**: 為每個孤立 Table 補充業務說明（說明為何不需要 FK，如「Config Table」「Lookup Table」），或補充缺漏的 FK，或確認廢棄後使用三步驟安全刪除（重命名→觀察→刪除）。

#### [MEDIUM] 16 — Schema 欄位命名不一致
**Check**: 所有 Table 的欄位命名是否統一遵循 `snake_case`？Boolean 欄位是否有 `is_`、`has_`、`can_` 前綴（如 `is_active`）？Enum 欄位是否有 `_type` 或 `_status` 後綴（如 `payment_status`）？外鍵欄位是否命名為 `{referenced_table}_id`？索引名稱是否遵循 `idx_{table}_{columns}` 規範？逐一列出命名不一致的欄位/索引。
**Risk**: 欄位命名不一致造成 ORM Model 混亂（部分用 camelCase、部分用 snake_case），前後端欄位對應時需要手動轉換，且容易因命名混淆而誤操作欄位。
**Fix**: 依 §2.1 命名慣例統一修正所有不符合規範的欄位名稱、索引名稱、約束名稱；修正後需同步更新對應的 Migration 腳本。

---

### Layer 5: 安全與合規（由 Security Expert 主審，共 4 項）

#### [CRITICAL] 17 — PII 欄位未識別或未加保護
**Check**: SCHEMA 是否有 PII 欄位清單（敏感資料清單章節）？識別欄位（email、phone、name、address、IP address）是否都在清單中標注保護方式（pgcrypto 加密、Tokenization、HTTPS only）和保留期限？`password_hash` 欄位是否明確說明使用 bcrypt（cost >= 12）或 Argon2id，且明確禁止儲存明文密碼？逐一確認所有潛在 PII 欄位的標注情況。
**Risk**: PII 欄位未識別，GDPR / PDPA 合規稽核時無法提供資料處理記錄；密碼未加密（或使用 MD5/SHA1 等弱 Hash）在資料庫洩露後，使用者密碼直接暴露；不符合 OWASP API2:2023（Broken Authentication）。
**Fix**: 建立或補充敏感資料清單章節，列出所有 PII 欄位及其保護方式和保留期限；`password_hash` 欄位加上注釋說明加密算法（bcrypt cost=12 / Argon2id）；明確標注禁止儲存明文密碼。

#### [CRITICAL] 18 — 軟刪除策略不一致
**Check**: 若 Schema 設計了軟刪除，是否所有 Table 使用一致的策略（統一使用 `deleted_at TIMESTAMPTZ NULL` 或統一使用 `is_deleted BOOLEAN`）？是否有 Table 混用兩種策略？未使用軟刪除的 Table 是否有業務說明（說明為何可以物理刪除）？
**Risk**: 混用兩種軟刪除策略，ORM 查詢需要針對不同 Table 撰寫不同的過濾條件，容易遺漏 `WHERE deleted_at IS NULL` 或 `WHERE is_deleted = FALSE`，導致已刪除資料出現在查詢結果中（GDPR 違規 + 資料洩露風險）。
**Fix**: 統一所有 Table 的軟刪除策略（建議 `deleted_at TIMESTAMPTZ NULL`，支援 Partial Index 和時間追蹤）；在 §2 通用規範中聲明全局軟刪除策略，例外（允許物理刪除的 Table）逐一說明業務理由。

#### [HIGH] 19 — Audit Trail 欄位缺失
**Check**: 每個業務 Table 是否有標準審計欄位（`created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`、`updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`）？`updated_at` 是否有自動更新 Trigger？高業務重要性的 Table（訂單、支付、使用者帳號變更）是否有 Audit Log Table 或 Trigger 記錄所有 DML 操作？逐一列出缺少審計欄位的 Table。
**Risk**: 缺少審計欄位，無法追蹤資料變更時間，Debug 生產問題時缺乏時間線依據；無法支援增量資料同步（ETL）；高業務重要性 Table 無 Audit Log，安全事件後無法追溯操作者（GDPR Art.5 問責制）。
**Fix**: 為每個業務 Table 補充缺少的審計欄位；添加 `updated_at` 自動更新 Trigger；為高業務重要性 Table 配置審計 Trigger（`audit_trigger_fn`）記錄 INSERT/UPDATE/DELETE 操作。

#### [HIGH] 20 — GDPR 被遺忘權實作缺失
**Check**: 若系統處理 EU 使用者資料（或 PRD/EDD 有合規要求），SCHEMA 是否定義了被遺忘權（Right to Erasure）的實作路徑？是否有 `erase_user_pii` 類型的 Procedure 或說明匿名化流程（替換 PII 為無意義值，保留業務完整性）？資料保留期限是否有定義（§17 或等效章節）？
**Risk**: 缺少被遺忘權實作，收到 GDPR 刪除請求時無安全的執行路徑，工程師可能因程序不清而操作失誤，或延誤響應（GDPR 要求 30 天內響應，違規罰款最高 2000 萬歐元或全球年營業額 4%）。
**Fix**: 補充 GDPR 被遺忘權實作章節：定義匿名化 Procedure（替換 PII 欄位為 `deleted_xxx@gdpr.invalid` 格式）、刪除計劃（軟刪除 → 30 天後硬刪除 Job）、刪除請求稽核記錄表（`gdpr_erasure_requests`）。

---

### Layer 6: 效能考量（由 Backend Engineer + Database Architect 聯合審查，共 4 項）

#### [HIGH] 21 — Migration Plan 包含不可逆操作
**Check**: Migration Script 是否包含不可逆操作（`DROP COLUMN`、`TRUNCATE`、不可回滾的資料轉換）？每個 Migration 是否同時撰寫 DOWN migration（可回滾）？大表操作（新增欄位、建立索引）是否使用 `CONCURRENTLY` 或批次 backfill 避免長時間鎖表？逐一審查每個 Migration 步驟。
**Risk**: 不可逆 Migration 執行後若發現錯誤，無法通過 Rollback 恢復資料，需依賴備份恢復，大幅增加 MTTR；大表無 CONCURRENTLY 建立索引會造成全表鎖（可能持續數分鐘到數小時），生產環境服務中斷。
**Fix**: 為每個不可逆操作補充 Rollback Plan（備份命令、資料恢復步驟）；或改用 Expand-Contract Pattern（三階段安全 Migration）；所有大表索引建立使用 `CREATE INDEX CONCURRENTLY`。

#### [HIGH] 22 — 大表缺少分區策略（預期資料量 > 1 億筆）
**Check**: 若有預期資料量超過 1 億筆的 Table（如 `event_log`、`audit_records`、`transactions`、`notifications`），是否說明分區策略（Range / List / Hash Partitioning）？是否評估過 BRIN 索引是否足夠（避免過早分區）？逐一識別高資料量 Table 及其現有策略。
**Risk**: 大表無分區策略，隨資料量增長查詢效能持續下降，Index Bloat 問題加劇；未來改造分區成本極高（需要重建 Table 並停機或使用複雜的 Online Migration 方案）。
**Fix**: 為每個預期大表補充分區策略說明（分區鍵、分區類型、預計每個分區資料量和保留期限）；1,000 萬行以下先評估 Partial Index + BRIN 是否足夠，避免過早優化。

#### [MEDIUM] 23 — 連線池與效能設計缺失
**Check**: SCHEMA 是否說明連線池大小計算（依 §7.3 公式或等效說明）？是否定義 Read Replica 路由策略（哪些查詢走 Primary，哪些走 Read Replica）？是否有查詢效能基準表（關鍵查詢的預期 P95 延遲與使用索引）？
**Risk**: 連線池設定不當（過小造成連線排隊，過大造成 DB 過載）直接影響 API 效能；無 Read Replica 路由策略，報表查詢拖垮 Primary，影響線上服務；無效能基準表，無法在 Code Review 時判斷新查詢是否符合效能要求。
**Fix**: 補充連線池計算說明（CPU 核心數 × 2 + 磁碟數）；定義 Read Replica 路由規則（寫入→Primary，報表/背景任務→Replica）；在效能基準表列出關鍵查詢的預期 P95 延遲。

#### [LOW] 24 — 裸 Placeholder 掃描
**Check**: 文件中是否有 `{{PLACEHOLDER}}` 格式未替換的空白佔位符（`{{table_name}}`、`{{YYYYMMDD}}`、`{{VERSION}}`、`{{DB_NAME}}`、`{{PROJECT_SLUG}}`）？逐一掃描全文，列出所有裸 placeholder 及其位置（章節）。注意：格式範例型 placeholder 若有說明則允許；純空白、無資訊的 placeholder 才是 finding。
**Risk**: 裸 placeholder 的 Table 名稱或欄位名稱無法執行 Migration，工程師需手動識別並替換；`{{DB_NAME}}` 等配置 placeholder 若未替換可能導致 PgBouncer 連線失敗。
**Fix**: 替換所有裸 placeholder 為真實的 Table 名稱、欄位名稱、版本號、或配置值；若真的無法確定，改為 `（待確認：描述）` 說明而非保留 `{{PLACEHOLDER}}`。

---

### Layer 6: HA / Replication / Read-Write Split（由 Backend DBA Expert 主審，共 4 項）

#### [CRITICAL] 25 — 缺少 Primary-Standby Replication 設計說明
**Check**: SCHEMA.md 或引用的 EDD §3.6 是否說明 DB 複本架構？包含：Primary 節點數量、Standby 節點數量（≥ 1）、Replication 模式（同步/非同步）、Failover 機制（自動/手動）？若完全無說明，或明確表示「單一 DB 節點，無 Replica」，視為 CRITICAL。
**Risk**: 單一 DB 節點是整個系統最高風險的 SPOF：節點故障→所有服務停止；無 Replica→故障時無法切換，需等待節點恢復或從備份還原（RTO 數小時）。
**Fix**: 在 §11 Backup & Recovery 或 §10 Sharding & Partitioning 補充 Replication 架構說明（Primary + ≥ 1 Standby），引用 EDD §3.6 HA Architecture；若使用 RDS 等 Managed Service，說明 Multi-AZ 設定。

#### [HIGH] 26 — 讀寫分離策略未定義
**Check**: 是否定義哪些查詢走 Primary，哪些走 Read Replica？是否說明：報表查詢、背景任務必須走 Replica（不影響線上服務）、用戶即時查詢是否允許走 Replica（可能有 Lag）、Replica Lag 可接受上限（建議 ≤ 1s）？缺少以上任一項視為 HIGH。
**Risk**: 無讀寫分離策略，所有查詢打 Primary：Analytics/報表查詢佔用 Primary CPU/IO，直接影響線上 API 效能；Primary 達到 IOPS 上限時，所有服務（讀+寫）同時降速。
**Fix**: 在 §7 效能設計或 §23 連線池設計補充讀寫分離規則：明確列出哪些 Service/API 使用 Replica 連線，說明 Replica Lag 監控指標（lag_seconds < 1s 告警）。

#### [HIGH] 27 — Replica Lag 監控未定義
**Check**: 是否說明 Replica Lag 的監控方式和告警門檻？包含：監控指標名稱（`pg_stat_replication.write_lag`、`seconds_behind_master`）、告警門檻（如 lag > 5s 警告，> 30s 嚴重）、Lag 過高時的降級策略（暫時讓讀查詢也走 Primary）？
**Risk**: Replica Lag 無監控，業務應用程式不知道自己讀到的是過期資料，導致用戶看到不一致的狀態（剛才的操作「消失」）；Lag 過高時若未降級，可能引發業務邏輯錯誤。
**Fix**: 在 §18 Database Observability 補充 Replica Lag 監控項：監控指標、告警門檻、降級策略（Lag > N s 時改從 Primary 讀取）。

#### [HIGH] 28 — Sharding Key 選擇未說明
**Check**: 若 §10 定義了 Sharding 策略，Shard Key 的選擇依據是否已說明？包含：為何選擇此欄位（高基數、查詢頻率、資料分布均勻性）、熱點分析（是否有特定 Shard Key 值資料量遠大於其他）、跨 Shard 查詢限制（JOIN 不跨 Shard）？若有 Sharding 但無以上說明，視為 HIGH。
**Risk**: Shard Key 選擇錯誤（如使用低基數欄位如 status），導致資料分布嚴重不均（Hot Shard）；或使用時間戳作為 Shard Key 導致所有最新資料集中在一個 Shard；Hot Shard 的效能等同於單台 DB。
**Fix**: 在 §10 Sharding & Partitioning 補充 Shard Key 選擇分析：基數評估、資料分布均勻性、跨 Shard 查詢影響、以及不選擇其他欄位的原因。

---

### Layer 7: BC 隔離（Spring Modulith HC-1，由 Software Architect 主審，共 2 項）

#### [CRITICAL] 29 — 跨 BC DB-level FK 存在（HC-1 違反）
**Check**: 掃描 SCHEMA.md 所有 `REFERENCES` 和 `FK` 宣告，確認是否有 Table A（屬於 BC-X）的 FK 指向 Table B（屬於 BC-Y，不同 BC）？判斷方式：對照 Document Control 的 `Owning BC / Service` 欄位，若 FK 的 source table 和 target table 屬於不同 BC，視為 CRITICAL。
**Risk**: 跨 BC 的 DB-level FK 建立了資料庫層面的強耦合，違反 HC-1（Spring Modulith）；BC 提取為獨立服務時，FK 必然導致 Migration 失敗（無法拆分 DB）；即使不拆服務，這樣的 FK 讓 BC 邊界形同虛設，所有服務最終可以 JOIN 所有資料。
**Fix**: 移除所有跨 BC 的 DB-level FK；將跨 BC 引用改為應用層解析（Application Layer join）：Consumer BC 儲存對應 ID（無 FK 約束），透過 API 呼叫 Publisher BC 取得完整資料；或透過 Domain Event 冗余儲存必要的快照欄位（denormalization）。

#### [HIGH] 30 — SCHEMA 缺少 BC Ownership 宣告
**Check**: SCHEMA.md 的 Document Control 是否有 `Owning BC / Service` 欄位（或等效章節），且每張 Table 均標注其所屬 BC？若無明確的 BC Ownership 宣告，工程師無法判斷哪些 FK 是跨 BC（違反 HC-1），視為 HIGH。
**Risk**: 無 BC Ownership 宣告，跨 BC FK 在 Code Review 中無法機械式驗證；下游 ARCH 的 §4.0 API-BC-Schema 映射表也無法正確填入 Owned Tables 欄位。
**Fix**: 在 SCHEMA.md Document Control 補充 `Owning BC / Service` 欄位，標注每張 Table 所屬 BC（與 EDD §3.4 Bounded Context Map 保持一致）；若多張 Table 屬於同一 BC，可在章節標題標注「BC: {BC_NAME}」。


---

## Self-Check：章節完整性驗證

> 此節由 gendoc-flow Review subagent 在每輪 Review 開始前自動執行（Step A-0）。
> 不需人工逐項填寫；reviewer 執行此 Self-Check 後將結果加入 findings。

**指令：**
1. 讀取 `{_TEMPLATE_DIR}/SCHEMA.md`，提取所有 `^## ` heading（含條件章節），共約 20 個
2. 讀取 `docs/SCHEMA.md`，提取所有 `^## ` heading
3. 逐一比對：template 中每個 heading 是否存在且有實質內容（非空、非 `{{PLACEHOLDER}}`）
4. 任何缺失或空白 → CRITICAL finding（"§X 章節缺失或無實質內容，template 要求此章節必須填寫"）

**通過條件：**
- template 中所有 `^## ` heading 均在輸出文件中存在
- 每個 heading 下方有實質內容（至少 2 行非空行，或說明跳過原因）
