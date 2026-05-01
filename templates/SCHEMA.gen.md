---
doc-type: SCHEMA
output-path: docs/SCHEMA.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/EDD.md
  - docs/ARCH.md
  - docs/API.md
quality-bar: "ER 圖涵蓋所有資料表及 FK 關聯線；DB 欄位覆蓋所有 PDD 顯示欄位；所有 API Response 欄位在 DB 中均存在；索引策略、Soft Delete、Migration、Multi-Tenancy、GDPR 生命週期政策均已定義"
---

# SCHEMA.gen.md — Schema 文件生成規則

依 EDD 自動生成完整 Schema 文件（三合一）：
ER 圖（Mermaid erDiagram）、資料表說明文件、CREATE TABLE SQL（含 index、trigger）、
以及用於 Schema Review 效能審查的使用案例 SQL。

---

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## 上游文件讀取規則

### 必讀上游鏈（依優先順序）

| 文件 | 必讀章節 | 用途 |
|------|---------|------|
| `IDEA.md`（若存在）| 全文 | 了解產品願景與資料保留期限要求 |
| `BRD.md` | 業務資料需求、法規遵循 | 了解 GDPR/個資法等法規遵循要求 |
| `PRD.md` | 所有功能需求 | Schema 的資料表必須支援所有 AC 的資料操作 |
| `PDD.md`（若存在）| UI 畫面欄位 | **DB 欄位必須覆蓋所有 PDD 定義的顯示欄位**，不得遺漏 |
| `EDD.md` | §5.5（資料模型）、§3（分層架構）| 資料模型設計、Soft Delete 策略、Audit Log 需求 |
| `ARCH.md` | 分層架構 | Schema 的設計需符合 ARCH 的 Repository Pattern |
| `API.md` | 所有 Request/Response Schema | **DB 欄位必須能支援 API 的 Response 結構** |

### IDEA.md Appendix C 素材讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，讀取與 SCHEMA 相關的檔案。
對每個存在的 `docs/req/` 檔案，讀取全文，結合 Appendix C「應用於」欄位標有「SCHEMA §」的段落，
作為生成 Schema 對應章節（資料表設計、索引策略、欄位定義）的補充依據。
優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

### 上游衝突偵測

讀取完所有上游文件後，掃描：
- PDD 畫面欄位 vs EDD 資料模型（是否有欄位 PDD 需要但 EDD 未設計）
- API Response Schema vs EDD 資料模型（是否有 API 欄位在 DB 中不存在）
- PRD 的功能需求 vs Schema 的 NULL constraint（必填欄位是否允許 NULL）

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並依衝突解決機制處理。

---

## 文件結構規則

生成內容必須涵蓋 `templates/SCHEMA.md` 的所有章節，包含：
Document Control、命名規範、UUID 策略、Soft Delete、正規化規則（1NF-BCNF）、
索引策略（6 類型）、Audit Log GDPR、效能設計 N+1 防治、Migration Expand-Contract、
Backup PITR、Multi-Tenancy RLS 實作、Schema Review Checklist、
Data Retention & GDPR Lifecycle Policy（§17）、Database Observability & Health Monitoring（§18）。

---

## Part 1：ER 圖生成規則（Mermaid erDiagram）

**格式規範：**
- 使用 `erDiagram` 語法
- 主表（無 FK）放最上方，有 FK 的表向下展開
- 欄位標注：`PK`、`FK`、`UK`、`"NOT NULL"`、`"敏感欄位"`
- 關聯線：`||--o{`（一對多）、`||--||`（一對一）、`}o--o{`（多對多）

**必須涵蓋所有資料表及 FK 關聯線，不得省略或留 placeholder。**

---

## Part 2：每張資料表說明文件生成規則

每張表必須包含以下格式：

**欄位說明表格（必填欄：欄位、型別、Nullable、預設值、說明）**

**標準欄位（每張表必備）：**
- `id`：UUID，PRIMARY KEY，`DEFAULT gen_random_uuid()`
- `created_at`：TIMESTAMPTZ，NOT NULL，`DEFAULT NOW()`
- `updated_at`：TIMESTAMPTZ，NOT NULL，`DEFAULT NOW()`
- `deleted_at`：TIMESTAMPTZ，NULL（軟刪除標記）

**索引說明（格式：`idx_<table>_<col>`：`(<columns>)` WHERE <condition>（用途說明））**

**Constraints 說明：**
- CHECK 約束（status、enum 欄位）
- UNIQUE 約束（唯一性規則，含 WHERE 條件篩選軟刪除）

**安全注意（PII 欄位標記）：**
- 標記所有 PII 欄位及其加密要求（AES-256-GCM）
- 密碼 hash 欄位：bcrypt（cost ≥ 12），永不儲存明文

---

## Part 3：CREATE TABLE SQL 生成規則

每張表提供完整標準 SQL，格式包含：
- 表頭注釋（表名、用途、生成工具）
- 所有欄位（含型別、NOT NULL、DEFAULT、CHECK constraint）
- REFERENCES 定義（ON DELETE 策略）
- 標準時間戳欄位（created_at、updated_at、deleted_at）
- 必要的 CREATE INDEX（含 WHERE 條件的 Partial Index）
- UNIQUE INDEX（依業務唯一性需求）
- `updated_at` 自動更新 TRIGGER

**共用 Trigger Function（生成一次，所有表共用）：**
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**索引策略（依 EDD 和查詢模式選擇）：**
- B-Tree：預設，適合等值和範圍查詢
- Hash：適合純等值查詢
- GIN：適合全文搜尋、JSONB、陣列
- Partial Index：加 WHERE 條件（如 `WHERE deleted_at IS NULL`）
- Covering Index：INCLUDE 常用查詢欄位
- Composite Index：多欄位組合（依查詢順序排列）

---

## Part 4：使用案例 SQL 生成規則

依 PRD 的高頻使用情境，生成 **3～5 個**代表性 SQL：

每個 SQL 必須包含：
- 注釋說明使用情境（來自 PRD §<AC>）
- 預期頻率標記（高頻 / 中頻 / 低頻）
- 效能注意事項（OFFSET 大資料量問題、GROUP BY 索引需求等）

**必須涵蓋的 SQL 類型：**
1. 分頁列表查詢（SELECT + LIMIT）
2. 聚合查詢（GROUP BY + COUNT/SUM）
3. JOIN 查詢（左外連接 + 條件過濾）
4. 寫入操作（INSERT + ON CONFLICT DO UPDATE）
5. 軟刪除操作（UPDATE SET deleted_at = NOW()）

---

## Migration 策略生成規則

必須說明：
- 工具選型（依 lang_stack：alembic / golang-migrate / flyway）
- 命名規則：`V{版本:3位}_{描述}.sql`（如 `V001__create_users.sql`）
- 規則：
  - 每次 migration 只做一件事
  - ADD COLUMN 使用 DEFAULT NULL，再逐步 backfill（避免 table lock）
  - DROP COLUMN 先標記廢棄（comment），下個版本再刪
  - 大表索引：使用 `CREATE INDEX CONCURRENTLY`（PostgreSQL）

---

## 資料量估算生成規則

必須提供估算表格：

| 資料表 | 初始量 | 年增量 | 5 年預估 | 備注 |
|--------|--------|--------|---------|------|
| users | N | N/年 | N | — |
| （主要業務表）| N | N/年 | N | 超過 1 億考慮分區 |

---

## §15 Multi-Tenancy 策略生成規則

必須明確選擇以下三種策略之一並說明實作：

**選項 A：Row-Level Security（RLS）**
- 提供 PostgreSQL RLS Policy SQL
- 說明 `app.current_tenant_id` 設定方式
- 適用場景：共享 DB，資料量中等

**選項 B：Schema-per-Tenant**
- 提供 Schema 建立腳本
- 說明 `search_path` 設定方式
- 適用場景：強隔離需求，租戶數量有限

**選項 C：DB-per-Tenant**
- 說明連線路由機制
- 適用場景：最高隔離需求，大型企業客戶

---

## §17 Data Retention & GDPR Lifecycle Policy 生成規則

必須包含：
- 保留政策表格（資料類型、法規依據、保留期限、到期處理）
- GDPR Right to Erasure：
  - 軟刪除匿名化 SQL（將 PII 欄位覆寫為匿名值）
  - 非同步硬刪除任務說明（scheduled job）
- Data Access Audit：`data_access_logs` 稽核表 DDL

---

## §18 Database Observability 生成規則

必須包含：
- 慢查詢識別 SQL（`pg_stat_statements` 查詢）
- 連線數監控查詢（`pg_stat_activity`）
- Table Bloat 偵測 SQL
- Alerting 規則（至少 6 項警告閾值）：
  - 連線數超過上限（例：> 80%）
  - 複製延遲超過閾值（例：> 10s）
  - 長事務超過時間（例：> 5min）
  - 慢查詢超過閾值（例：> 1s）
  - Table Bloat 超過比率（例：> 30%）
  - 磁碟空間不足（例：> 85%）

---

## 推斷規則

### 資料表推斷
- PRD 每個功能 → 推斷需要的資料表（實體及關聯）
- PDD 每個畫面 → 確認 DB 欄位覆蓋所有顯示欄位
- API Response Schema → 確認每個回傳欄位在 DB 中存在

### 索引推斷
- 外鍵欄位一律建立索引
- 常用過濾條件（status、user_id + 時間範圍）建立複合索引
- 查詢頻繁且 deleted_at 參與條件 → 建立 Partial Index（WHERE deleted_at IS NULL）

### Soft Delete 推斷
- 所有業務資料表（非查找表）均加 `deleted_at TIMESTAMPTZ`
- UNIQUE 約束均加 `WHERE deleted_at IS NULL` 條件

---

## 生成前自我檢核清單

- [ ] §2 命名規範已說明（表名/欄位名大小寫規則 + ID 策略選擇：UUID/BIGSERIAL）
- [ ] §2.4 Soft Delete 模式已定義（deleted_at + 唯一索引策略）
- [ ] §4 正規化規則已說明（1NF-BCNF + 刻意反正規化需有理由）
- [ ] §5 索引策略已填寫（B-Tree/Hash/GIN/Partial/Covering + 選擇性查詢）
- [ ] §6 Audit Log Schema 已定義（含 GDPR erasure 支援）
- [ ] §7 Performance Design：查詢計畫分析與慢查詢閾值是否已定義？
- [ ] §8 Migration 策略已說明（Expand-Contract Pattern + 零停機遷移步驟）
- [ ] §9 Data Integrity Constraints：CHECK / UNIQUE / FOREIGN KEY 約束是否已完整定義？
- [ ] §10 Sharding & Partitioning：分表策略（Range / Hash / List）是否已評估？
- [ ] §11 Backup & Recovery 已說明（PITR + WAL + 恢復時間目標）
- [ ] §12 ER Diagram（erDiagram）已生成，涵蓋所有資料表及 FK 關聯線（使用 Mermaid erDiagram 語法，不得省略或留 placeholder）
- [ ] §15 Multi-Tenancy 策略已評估（明確選擇 RLS / Schema-per-Tenant / DB-per-Tenant 並給出依據）
- [ ] 若選擇 RLS：已提供 PostgreSQL RLS Policy SQL + app.current_tenant_id 使用說明
- [ ] 若選擇 Schema-per-Tenant：已提供 Schema 建立腳本 + search_path 設定說明
- [ ] §16 Schema Review Checklist 已生成
- [ ] §17 Data Retention & Lifecycle Policy：保留政策表（法規依據 + 保留期限）是否已定義？
- [ ] §17 GDPR Right to Erasure：軟刪除匿名化 SQL + 非同步硬刪除任務是否已提供？
- [ ] §17 Data Access Audit：`data_access_logs` 稽核表 DDL 是否已生成？
- [ ] §18 Database Observability：慢查詢識別 SQL、連線數監控查詢、Table Bloat 偵測是否已包含？
- [ ] §18 Alerting 規則：連線數/複製延遲/長事務 6 項警告閾值是否已定義？
- [ ] 所有 `[UPSTREAM_CONFLICT]` 標記均已處理或說明
- [ ] 無未替換的佔位符（`<待填>` 等）

---

## Quality Gate（生成後自檢，交 Review Agent 前必須全部通過）

在將文件交給 Review Agent 之前，Gen Agent 必須驗證以下項目。**任何一項不合格，必須先修復再繼續**。

> **讀取 lang_stack 方式**：`python3 -c "import json; print(json.load(open('.gendoc-state.json')).get('lang_stack','unknown'))"`

| 檢查項 | 合格標準 | 不合格處理 |
|--------|---------|-----------|
| 所有 §章節齊全 | 對照 SCHEMA.md 章節清單，無缺失章節 | 補寫缺失章節 |
| 無裸 placeholder | 每個 `{{...}}` 後有「: 說明」或具體範例值 | 補全說明或替換為具體值 |
| 技術棧一致 | 資料庫類型（PostgreSQL/MySQL/MongoDB 等）與 state.lang_stack 一致 | 修正至一致 |
| 數值非 TBD/N/A | 每個欄位有具體資料型別（VARCHAR(255)/INT/TIMESTAMP 等），非「類型待定」 | 依業務語義決定後填入 |
| 主鍵完整 | 每個資料表都有 PRIMARY KEY 定義 | 補充缺失的主鍵 |
| 外鍵關係明確 | 所有跨表引用都有 FOREIGN KEY 或等效說明（NoSQL 需說明引用方式） | 補充缺失的關聯定義 |
| ER 圖與表格一致 | ERD Mermaid 圖中的表格和欄位與下方文字定義一致 | 修正不一致之處 |
| HA Replication 覆蓋 | §16 HA 核查清單 5 項全部回答（Replication/讀寫分離/Lag/連線池/Shard Key）| 補充缺失說明 |
