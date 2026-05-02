# SCHEMA — 資料庫 Schema 設計文件

## Document Control

| 欄位 | 值 |
|------|-----|
| Document ID | `SCHEMA-{{PROJECT_SLUG}}-{{YYYYMMDD}}` |
| Version | `{{VERSION}}` |
| Status | Draft / In Review / Approved |
| Classification | Internal / Confidential |
| Owner | Database Architect / Data Engineering Lead |
| **Owning Bounded Context / Service** | **{{BC_NAME}}**（對應 ARCH §4 / EDD §3.4；本 Schema 的唯一擁有服務） |
| Created | {{YYYYMMDD}} |
| Last Updated | {{YYYYMMDD}} |
| Upstream EDD | [docs/EDD.md](docs/EDD.md) |
| Database | PostgreSQL {{VERSION}} / MySQL {{VERSION}} |
| Source of Truth | 所有 Migration 必須對照本文件審查後才能合併 |
| Changelog | [See §16 Change Log](#16-change-log) |

## Change Log

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | {{YYYYMMDD}} | {{AUTHOR}} | Initial schema design |

---

## 1. 概述

- 資料庫：PostgreSQL {{VERSION}} / MySQL {{VERSION}}（刪除不適用的）
- 字元集：UTF-8（`utf8mb4` for MySQL）
- 時區：所有時間戳一律儲存 UTC；應用層負責轉換顯示時區
- 排序規則（Collation）：`en_US.UTF-8`（PostgreSQL） / `utf8mb4_unicode_ci`（MySQL）
- Schema 命名空間：`public`（PostgreSQL）/ `{{DB_NAME}}`（MySQL）
- 最大連線數（Connection Pool）：依 §7 計算

---

## 2. 通用欄位規範

### 2.1 命名慣例

| 類別 | 規則 | 範例 |
|------|------|------|
| 資料表名稱 | `snake_case`，**單數**，小寫 | `user`, `order_item` |
| 欄位名稱 | `snake_case`，小寫 | `first_name`, `created_at` |
| Boolean 欄位 | 以 `is_`、`has_`、`can_` 為前綴 | `is_active`, `has_verified_email`, `can_publish` |
| Enum 欄位 | 以 `_type` 或 `_status` 為後綴 | `payment_status`, `notification_type` |
| 外鍵欄位 | 參照表名稱單數 + `_id` | `user_id`, `order_id` |
| 索引名稱 | `idx_{table}_{columns}` | `idx_user_email` |
| 唯一索引 | `uq_{table}_{columns}` | `uq_user_email` |
| 外鍵約束 | `fk_{table}_{ref_table}` | `fk_order_user` |
| 主鍵約束 | `pk_{table}` | `pk_user` |

**禁止：** 保留字作為欄位名稱（`name`、`value`、`type`、`order` 等）；使用 `tbl_` 前綴；縮寫不一致。

### 2.2 所有資料表必含的基礎欄位

```sql
-- 完整標準基礎欄位（PostgreSQL）
id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
deleted_at  TIMESTAMPTZ  -- 軟刪除（若業務需要）
```

### 2.3 主鍵 ID 策略

| 策略 | 適用情境 | 優點 | 缺點 |
|------|---------|------|------|
| `BIGSERIAL` (auto-increment) | 內部系統、高寫入量、不暴露給外部 | 最小儲存、順序插入性能佳 | 可猜測、分散式環境難同步 |
| `UUID v4` | 需暴露給外部的資源 ID、跨服務資料合併 | 不可猜測、全域唯一 | 16 bytes、索引分裂、隨機插入性能較差 |
| `ULID` | 需要時間排序的 UUID 替代方案 | 字典順序=時間順序、URL-safe | 需要函式庫支援 |
| `UUID v7` | PostgreSQL 17+ / 現代系統 | 時間有序的 UUID，兼具順序插入性能 | 較新，支援度仍在成熟 |

**決策規則：**
- 外部可見的資源（API 回傳 ID、URL 中出現）→ 使用 UUID v4 或 UUID v7
- 純內部關聯表（join table）→ 可使用 BIGSERIAL
- 高寫入時序資料 → 使用 ULID 或 UUID v7 以避免 B-tree 分裂

### 2.4 軟刪除模式（Soft Delete）

```sql
-- 軟刪除標記欄位
deleted_at  TIMESTAMPTZ  -- NULL 表示未刪除

-- 所有業務查詢必須加上此條件
WHERE deleted_at IS NULL

-- 針對軟刪除建立 Partial Index（大幅節省索引大小）
CREATE INDEX idx_user_email_active
  ON "user"(email)
  WHERE deleted_at IS NULL;

-- updated_at 自動更新 Trigger（PostgreSQL）
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_updated_at
  BEFORE UPDATE ON "user"
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

**注意：** 永遠不要物理刪除有業務意義的資料；軟刪除紀錄須納入資料保留政策（見 §6.3）。

---

## 3. 資料表定義

### 3.1 `{{table_name}}`

**說明：** {{儲存什麼資料，業務用途，與其他表的關係}}

```sql
CREATE TABLE {{table_name}} (
  id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),

  -- 業務欄位
  name        VARCHAR(255) NOT NULL,
  description TEXT,
  status      VARCHAR(50)  NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'inactive', 'archived')),

  -- 關聯（外鍵必須有對應索引）
  user_id     UUID         NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,

  -- 時間戳
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  deleted_at  TIMESTAMPTZ,

  CONSTRAINT pk_{{table_name}} PRIMARY KEY (id),
  CONSTRAINT fk_{{table_name}}_user FOREIGN KEY (user_id) REFERENCES "user"(id)
);
```

**欄位說明：**

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| id | UUID | 是 | gen_random_uuid() | 主鍵，對外暴露 |
| name | VARCHAR(255) | 是 | — | 名稱，最長 255 字元 |
| status | VARCHAR(50) | 是 | 'active' | 狀態：active / inactive / archived |
| user_id | UUID | 是 | — | 關聯使用者，軟刪除不影響外鍵 |

**索引：**

```sql
-- 外鍵索引（必填，JOIN 性能關鍵）
CREATE INDEX idx_{{table_name}}_user_id ON {{table_name}}(user_id);

-- 高頻過濾索引（Partial Index：排除已刪除）
CREATE INDEX idx_{{table_name}}_status
  ON {{table_name}}(status)
  WHERE deleted_at IS NULL;

-- 排序索引
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at DESC);

-- 複合索引（等值欄位在前，範圍/排序欄位在後）
CREATE INDEX idx_{{table_name}}_user_status
  ON {{table_name}}(user_id, status)
  WHERE deleted_at IS NULL;
```

---

### 3.2 `user`（基礎使用者表）

```sql
CREATE TABLE "user" (
  id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  email            VARCHAR(320) NOT NULL,
  is_email_verified BOOLEAN     NOT NULL DEFAULT FALSE,

  -- 敏感欄位（加密儲存）
  password_hash    VARCHAR(255),  -- bcrypt hash，cost factor >= 12，永不儲存明文

  -- Profile
  display_name     VARCHAR(100),
  avatar_url       TEXT,

  -- 時間戳
  last_login_at    TIMESTAMPTZ,
  created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  deleted_at       TIMESTAMPTZ,

  CONSTRAINT pk_user PRIMARY KEY (id)
);

-- 大小寫不敏感的唯一 email（僅對未刪除使用者）
CREATE UNIQUE INDEX uq_user_email
  ON "user"(LOWER(email))
  WHERE deleted_at IS NULL;
```

**安全注意：**
- `password_hash` 使用 bcrypt（cost factor >= 12）或 Argon2id；永遠不儲存明文密碼
- `email` 索引使用 `LOWER()` 確保大小寫不敏感查詢
- `email` 欄位屬於 PII，需納入加密與保留政策（見 §6）

---

## 4. 正規化規則（Normalization Rules）

### 4.1 各正規化形式說明

| 正規化 | 要求 | 常見違反 | 修正方式 |
|--------|------|---------|---------|
| 1NF | 每欄位為原子值；無重複欄位組 | `tag1`, `tag2`, `tag3` 三欄 | 拆出 `tag` 表 + 關聯表 |
| 2NF | 非主鍵欄位完全依賴整個主鍵（1NF + 消除部分依賴） | 複合主鍵中只依賴其中一個欄位 | 拆表 |
| 3NF | 非主鍵欄位不依賴其他非主鍵欄位（2NF + 消除遞移依賴） | `city` 依賴 `zip_code` 而非 `user_id` | 拆出 `zip_code` 表 |
| BCNF | 每個決定因子（Determinant）都是候選鍵（3NF 的強化版） | 複合候選鍵之間的依賴 | 謹慎拆表，評估查詢成本 |

**範例：1NF 違反與修正**

```sql
-- 違反 1NF：重複欄位組
CREATE TABLE product (
  id       UUID PRIMARY KEY,
  tag1     VARCHAR(50),
  tag2     VARCHAR(50),
  tag3     VARCHAR(50)  -- 若有第 4 個 tag 就要改 schema
);

-- 修正：拆出關聯表
CREATE TABLE product (
  id   UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE product_tag (
  product_id UUID NOT NULL REFERENCES product(id) ON DELETE CASCADE,
  tag        VARCHAR(50) NOT NULL,
  PRIMARY KEY (product_id, tag)
);
```

### 4.2 刻意反正規化（Intentional Denormalization）

以下情境可接受反正規化，但**必須以文件記錄理由與同步策略**：

| 情境 | 反正規化手法 | 文件要求 |
|------|------------|---------|
| 高頻聚合查詢（如計數） | 在父表儲存 `comments_count` | 說明 trigger 或應用層同步方式 |
| 報表/BI 查詢 | 獨立的 denormalized 報表表 | 說明 ETL 頻率與可接受的延遲 |
| 避免 N 層 JOIN | 冗餘儲存 `tenant_id` | 說明更新時的一致性保證 |
| 效能瓶頸已量測 | 複製欄位 | 附上 EXPLAIN ANALYZE 輸出作為佐證 |

> 規則：沒有 EXPLAIN ANALYZE 佐證的反正規化不允許合併。

---

## 5. 索引策略（Indexing Strategy）

### 5.1 何時建立索引

**應建立索引：**
- 外鍵欄位（JOIN 的必要條件）
- 高頻 WHERE 過濾欄位（選擇性 > 5%，即 cardinality 高）
- ORDER BY 欄位（排序用）
- UNIQUE 約束欄位
- 範圍查詢欄位（如日期區間）

**不應建立索引：**
- 選擇性極低的欄位（如 Boolean、少數可能值的 status）→ 改用 Partial Index
- 寫多讀少的表（索引維護成本高過查詢收益）
- 已有複合索引覆蓋的欄位前綴

**選擇性（Selectivity）評估查詢：**
```sql
-- 評估欄位選擇性（越接近 1 越適合建索引）
SELECT
  COUNT(DISTINCT status)::FLOAT / COUNT(*) AS selectivity
FROM {{table_name}};
```

### 5.2 索引類型選用表

| 索引類型 | 適用情境 | 範例 |
|---------|---------|------|
| B-tree（預設） | 等值、範圍、排序查詢；大多數場景 | `WHERE id = ?`, `ORDER BY created_at` |
| Hash | 僅等值查詢，PostgreSQL 10+ 才持久化 | `WHERE user_id = ?`（高頻等值） |
| GIN | 陣列、JSONB、全文搜尋（tsvector） | `WHERE tags @> '{news}'`, `to_tsvector` |
| GiST | 幾何、地理座標（PostGIS）、範圍類型 | `WHERE location && ST_MakeEnvelope(...)` |
| BRIN | 物理有序的超大表（如時序資料） | `WHERE event_time BETWEEN ...`（TB 級 log 表） |
| SP-GiST | 非平衡樹結構資料（IP 範圍、電話號碼） | `WHERE ip_addr << '192.168.0.0/16'` |

### 5.3 複合索引欄位順序規則

```
(等值條件欄位) → (高選擇性欄位) → (範圍條件欄位) → (排序欄位)
```

```sql
-- 查詢：WHERE tenant_id = ? AND status = 'active' ORDER BY created_at DESC
-- 正確複合索引欄位順序：
CREATE INDEX idx_order_tenant_status_created
  ON "order"(tenant_id, status, created_at DESC)
  WHERE deleted_at IS NULL;

-- 錯誤（排序欄位放中間，後續欄位無法使用索引）：
CREATE INDEX idx_bad ON "order"(tenant_id, created_at, status);
```

### 5.4 Partial Index 應用

```sql
-- 只對未刪除記錄建索引（節省 30-80% 索引大小）
CREATE INDEX idx_user_email_active
  ON "user"(email)
  WHERE deleted_at IS NULL;

-- 只對特定狀態建索引
CREATE INDEX idx_order_pending
  ON "order"(created_at DESC)
  WHERE status = 'pending';

-- 覆蓋索引（Index-Only Scan）
CREATE INDEX idx_user_list_cover
  ON "user"(tenant_id, created_at DESC)
  INCLUDE (id, display_name, email)
  WHERE deleted_at IS NULL;
```

### 5.5 索引膨脹（Index Bloat）監控查詢

```sql
-- 偵測索引膨脹（需要 pgstattuple extension）
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- 從未被使用的索引
ORDER BY pg_relation_size(indexrelid) DESC;

-- 重建膨脹索引（不鎖表）
REINDEX INDEX CONCURRENTLY idx_{{table_name}}_{{column}};
```

---

## 6. 稽核與合規資料表（Audit & Compliance）

### 6.1 標準稽核日誌表

```sql
CREATE TABLE audit_log (
  id           BIGSERIAL    PRIMARY KEY,
  -- 操作對象
  table_name   VARCHAR(100) NOT NULL,
  record_id    TEXT         NOT NULL,  -- 目標記錄的主鍵（轉字串以支援任何類型）
  operation    VARCHAR(10)  NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  -- 變更內容
  old_values   JSONB,       -- UPDATE/DELETE 時的舊值
  new_values   JSONB,       -- INSERT/UPDATE 時的新值
  changed_fields TEXT[],   -- 僅記錄有變更的欄位名稱
  -- 操作者資訊
  actor_id     UUID,        -- 執行操作的使用者 ID（NULL 表示系統）
  actor_type   VARCHAR(50)  NOT NULL DEFAULT 'user',  -- 'user', 'system', 'api_key'
  -- 請求上下文
  ip_address   INET,
  user_agent   TEXT,
  request_id   VARCHAR(100),  -- 分散式追蹤 ID
  -- 時間
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 索引（稽核日誌以插入為主，索引精簡）
CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_actor_id ON audit_log(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
-- BRIN 索引節省大型稽核表的空間
CREATE INDEX idx_audit_log_created_brin ON audit_log USING BRIN(created_at);
```

### 6.2 自動稽核 Trigger 模式

```sql
-- 通用稽核 trigger function
CREATE OR REPLACE FUNCTION audit_trigger_fn()
RETURNS TRIGGER AS $$
DECLARE
  old_data JSONB;
  new_data JSONB;
  changed  TEXT[];
BEGIN
  IF TG_OP = 'DELETE' THEN
    old_data := to_jsonb(OLD);
    new_data := NULL;
  ELSIF TG_OP = 'INSERT' THEN
    old_data := NULL;
    new_data := to_jsonb(NEW);
  ELSE  -- UPDATE
    old_data := to_jsonb(OLD);
    new_data := to_jsonb(NEW);
    SELECT array_agg(key) INTO changed
    FROM jsonb_each(old_data) o
    JOIN jsonb_each(new_data) n USING (key)
    WHERE o.value IS DISTINCT FROM n.value;
  END IF;

  INSERT INTO audit_log(
    table_name, record_id, operation,
    old_values, new_values, changed_fields,
    actor_id, request_id, created_at
  ) VALUES (
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id)::TEXT,
    TG_OP,
    old_data, new_data, changed,
    current_setting('app.current_user_id', true)::UUID,
    current_setting('app.request_id', true),
    NOW()
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 套用到需要稽核的表
CREATE TRIGGER trg_{{table_name}}_audit
  AFTER INSERT OR UPDATE OR DELETE ON {{table_name}}
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_fn();
```

### 6.3 GDPR / 個資保護

**PII 欄位清單：**

| 資料表 | 欄位 | PII 分類 | 保護方式 | 保留期限 |
|--------|------|---------|---------|---------|
| `user` | `email` | 識別資料 | 查詢層加密（pgcrypto） | 帳號刪除後 30 天 |
| `user` | `display_name` | 識別資料 | 無（非敏感） | 帳號刪除後 30 天 |
| `user` | `avatar_url` | 識別資料 | HTTPS only | 帳號刪除後 30 天 |
| `user` | `password_hash` | 認證資料 | bcrypt（cost >= 12） | 立即隨帳號刪除 |
| `audit_log` | `ip_address` | 網路識別 | 雜湊或截斷（EU 用戶） | 90 天 |
| `{{table}}` | `{{field}}` | {{分類}} | {{方式}} | {{期限}} |

**被遺忘權（Right to Erasure）實作模式：**

```sql
-- 替換 PII 而非物理刪除（保留業務完整性）
CREATE OR REPLACE PROCEDURE erase_user_pii(p_user_id UUID)
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE "user" SET
    email         = 'deleted_' || id || '@erased.invalid',
    display_name  = 'Deleted User',
    avatar_url    = NULL,
    password_hash = NULL,
    deleted_at    = NOW()
  WHERE id = p_user_id;

  -- 清除稽核日誌中的 PII（依法規決定是否執行）
  UPDATE audit_log SET
    old_values = old_values - '{email,display_name}'::TEXT[],
    new_values = new_values - '{email,display_name}'::TEXT[]
  WHERE table_name = 'user' AND record_id = p_user_id::TEXT;

  -- 記錄抹除操作本身
  INSERT INTO audit_log(table_name, record_id, operation, actor_type)
  VALUES ('user', p_user_id::TEXT, 'GDPR_ERASE', 'system');
END;
$$;
```

---

## 7. 效能設計（Performance Design）

### 7.1 查詢效能基準表

| 查詢描述 | 預期 P95 | 實測 P95 | 使用索引 | EXPLAIN ANALYZE 備注 |
|---------|---------|---------|---------|---------------------|
| 依 user_id 列出訂單（limit 20） | < 10ms | — | `idx_order_user_id` | — |
| 全文搜尋文章 | < 100ms | — | GIN tsvector | — |
| 報表聚合（當月） | < 2s | — | BRIN created_at | 可接受非即時 |
| {{查詢描述}} | < {{ms}} | — | {{索引}} | {{備注}} |

### 7.2 N+1 查詢防護

```sql
-- 典型 N+1 反模式：先查清單，再迴圈查細節
-- 錯誤做法（N+1）：
SELECT id FROM "order" WHERE user_id = $1 LIMIT 20;
-- 然後對每個 order 執行：
SELECT * FROM order_item WHERE order_id = $1;

-- 正確做法：一次 JOIN 取回所需資料
SELECT
  o.id,
  o.status,
  o.created_at,
  COALESCE(
    json_agg(
      json_build_object(
        'id',       oi.id,
        'sku',      oi.sku,
        'quantity', oi.quantity,
        'price',    oi.unit_price
      ) ORDER BY oi.id
    ) FILTER (WHERE oi.id IS NOT NULL),
    '[]'
  ) AS items
FROM "order" o
LEFT JOIN order_item oi ON oi.order_id = o.id
WHERE o.user_id = $1
  AND o.deleted_at IS NULL
GROUP BY o.id
ORDER BY o.created_at DESC
LIMIT 20;
```

### 7.3 連線池大小公式

```
最佳連線數 = (CPU 核心數 * 2) + 有效磁碟數
```

| 環境 | 計算範例 | 建議設定 |
|------|---------|---------|
| 開發（4 核） | (4*2)+1 = 9 | max_connections = 20 |
| 生產（16 核） | (16*2)+2 = 34 | PgBouncer pool_size = 40 |
| Serverless | 每 function 1 連線 | 強制使用 Transaction Pooler |

**PgBouncer 設定範本：**

```ini
[databases]
{{DB_NAME}} = host=localhost dbname={{DB_NAME}}

[pgbouncer]
pool_mode = transaction       # Serverless 必用 transaction mode
max_client_conn = 1000
default_pool_size = 40
min_pool_size = 5
reserve_pool_size = 5
server_idle_timeout = 600
```

### 7.4 Read Replica 路由規則

| 查詢類型 | 路由目標 | 說明 |
|---------|---------|------|
| 寫入（INSERT/UPDATE/DELETE） | Primary | 必須，確保一致性 |
| 即時讀取（使用者剛寫入後讀） | Primary | 避免 replication lag 問題 |
| 報表、匯出 | Read Replica | 減輕 Primary 負擔 |
| 背景 Job 查詢 | Read Replica | 可接受輕微延遲 |
| 全文搜尋 | Read Replica | 非即時可接受 |

---

## 8. Migration 策略（Migration Strategy）

### 8.1 命名規範

| 工具 | 格式 | 範例 |
|------|------|------|
| Flyway | `V{version}__{description}.sql` | `V001__create_user.sql` |
| Alembic | `{revision}_{description}.py` | `a3f1b2c4_add_email_verified.py` |
| golang-migrate | `{version}_{description}.{up\|down}.sql` | `000001_create_user.up.sql` |
| Liquibase | `{YYYYMMDD}-{description}.xml` | `20240315-add-order-table.xml` |

**命名規則：**
- 描述使用小寫 `snake_case`
- 動詞優先：`create_`, `add_`, `drop_`, `rename_`, `alter_`
- 每個 Migration 只做一件邏輯上的事
- 永遠同時撰寫 UP 與 DOWN migration

### 8.2 零停機 Migration 模式（Expand-Contract Pattern）

**大原則：** 資料庫 schema 變更必須與應用程式版本解耦，分三個部署周期完成。

```
Phase 1 (Expand)   → 新增欄位/表，舊應用仍正常運作
Phase 2 (Migrate)  → 部署新應用，同時寫入新舊欄位
Phase 3 (Contract) → 舊欄位確認無流量後，下一個 Migration 移除
```

### 8.3 大表新增欄位（4 步驟無鎖流程）

```sql
-- 情境：對 1 億筆記錄的 "order" 表新增 currency 欄位
-- 錯誤做法（會鎖全表）：
ALTER TABLE "order" ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'USD';

-- 正確做法（4 步驟）：

-- Step 1：新增 nullable 欄位（瞬間完成，不鎖表）
ALTER TABLE "order" ADD COLUMN currency VARCHAR(3);

-- Step 2：批次 backfill（分批更新，避免長事務鎖表）
-- 執行此段直到 rows_updated = 0
UPDATE "order"
SET currency = 'USD'
WHERE id IN (
  SELECT id FROM "order"
  WHERE currency IS NULL
  LIMIT 10000  -- 每批 10,000 筆
);

-- Step 3（等 Step 2 完成後）：加上 NOT NULL 約束
-- PostgreSQL 11+ 若有 DEFAULT 可直接加，否則需先 backfill
ALTER TABLE "order"
  ALTER COLUMN currency SET NOT NULL,
  ALTER COLUMN currency SET DEFAULT 'USD';

-- Step 4：驗證無 NULL 值
SELECT COUNT(*) FROM "order" WHERE currency IS NULL;  -- 應為 0
```

### 8.4 各 Migration 類型的 Rollback 策略

| Migration 類型 | Rollback 難度 | 策略 |
|-------------- |-------------|------|
| 新增資料表 | 低 | DROP TABLE（Down migration） |
| 新增欄位 | 低 | DROP COLUMN（Down migration） |
| 重命名欄位 | 中 | 新增欄位→複製資料→刪舊欄位；Rollback 反向操作 |
| 刪除欄位 | 高 | 先標記廢棄（加 `_deprecated` 後綴），下個版本才刪 |
| 資料型別變更 | 高 | 新增新欄位→複製資料→切換→廢棄舊欄位 |
| 資料遷移 | 視規模 | 必須備份後才執行；大量資料用批次腳本 |

### 8.5 Migration 測試檢查清單

- [ ] UP migration 在乾淨 DB 執行成功
- [ ] DOWN migration 能完整還原
- [ ] 在含有生產資料量的 Staging 環境測試過執行時間
- [ ] 確認不持有超過 3 秒的 table lock
- [ ] EXPLAIN ANALYZE 新增的查詢，確認使用正確索引
- [ ] 驗證 foreign key 約束未被破壞
- [ ] CI 中的 migration lint（無破壞性語法）通過

---

## 9. 資料完整性約束（Data Integrity Constraints）

### 9.1 外鍵 ON DELETE 行為選用

| 行為 | 語義 | 適用情境 |
|------|------|---------|
| `CASCADE` | 刪除父記錄時自動刪除子記錄 | 子表資料不具獨立意義（如 `order_item` 隨 `order` 消滅） |
| `RESTRICT` | 有子記錄時禁止刪除父記錄（立即檢查） | 刪除必須由業務邏輯明確處理 |
| `NO ACTION` | 有子記錄時禁止刪除父記錄（延遲檢查） | 與 `RESTRICT` 相似，但支援延遲約束 |
| `SET NULL` | 刪除父記錄時將子記錄外鍵設為 NULL | 子記錄可獨立存在（如文章刪除後留存的留言） |
| `SET DEFAULT` | 刪除父記錄時將子記錄外鍵設為預設值 | 有合理預設父記錄（如「未分類」分類） |

### 9.2 CHECK 約束範例

```sql
-- 正數約束
unit_price   NUMERIC(12, 4) NOT NULL CHECK (unit_price >= 0),
quantity     INTEGER        NOT NULL CHECK (quantity > 0),

-- 日期邏輯約束
expires_at   TIMESTAMPTZ    CHECK (expires_at > created_at),

-- 格式約束（email 簡易驗證）
email        VARCHAR(320)   CHECK (email ~* '^[^@]+@[^@]+\.[^@]+$'),

-- 互斥欄位約束（只能有其中一個值）
CONSTRAINT chk_payment_source CHECK (
  (stripe_payment_id IS NOT NULL)::INT +
  (paypal_payment_id IS NOT NULL)::INT = 1
),

-- 業務規則約束
CONSTRAINT chk_order_status_transition CHECK (
  NOT (status = 'completed' AND refunded_at IS NULL AND total_amount > 0)
)
```

### 9.3 Unique 約束 vs Unique Index

| 方式 | 語義差異 | 建議使用時機 |
|------|---------|------------|
| `UNIQUE` 約束 | 宣告式，DDL 層語義明確 | 簡單唯一鍵（單欄或少數欄組合） |
| `CREATE UNIQUE INDEX` | 支援 Partial、函式表達式 | 需要 WHERE 條件（如軟刪除）、大小寫不敏感、CONCURRENTLY 建立 |

```sql
-- Unique 約束（簡單）
ALTER TABLE "user" ADD CONSTRAINT uq_user_email UNIQUE (email);

-- Unique Index（進階，支援 Partial 與函式）
CREATE UNIQUE INDEX uq_user_email_active
  ON "user"(LOWER(email))
  WHERE deleted_at IS NULL;
```

### 9.5 跨 BC FK 禁止（Spring Modulith HC-1）

> **HC-1 硬約束**：本 Schema 的 Tables **不得** DB-level FK 引用屬於其他 Bounded Context 的 Tables。  
> 跨 BC 引用改為**應用層管理的 ID-only 策略**：僅儲存對方 BC 的業務 ID，不建立 DB-level FK。

**判斷一個 FK 是否跨 BC：**
1. 查看 Document Control 的「Owning BC / Service」— 這是本 Schema 的 BC
2. 查看被引用 Table 所屬的 SCHEMA.md 的「Owning BC / Service」
3. 若兩者不同 → 跨 BC FK，必須移除並改為 ID-only

**ID-only 跨 BC 引用範例：**

```sql
-- ❌ 禁止：跨 BC DB-level FK
ALTER TABLE wallet_transactions
  ADD CONSTRAINT fk_member
  FOREIGN KEY (member_id) REFERENCES member.users(id);

-- ✅ 正確：ID-only，應用層負責一致性
-- wallet.wallet_transactions.member_id BIGINT NOT NULL
-- Cross-BC reference to member.users(id): enforced at application layer, no DB FK.
COMMENT ON COLUMN wallet_transactions.member_id IS
  'Cross-BC reference to member.users(id). Enforced at application layer, no DB FK (HC-1).';
```

**本 Schema 跨 BC 引用清單（必填）：**

| Column | 引用的 BC | 引用的 Table | 說明 |
|--------|----------|------------|------|
| `{{column_name}}` | `{{target_bc}}` | `{{target_table}}(id)` | Application layer enforced |

---

### 9.4 延遲約束（Deferred Constraints）

用於解決循環外鍵或批次插入的順序問題：

```sql
-- 範例：A 表外鍵參照 B，B 外鍵參照 A（循環依賴）
ALTER TABLE "user"
  ADD CONSTRAINT fk_user_primary_org
  FOREIGN KEY (primary_org_id) REFERENCES organization(id)
  DEFERRABLE INITIALLY DEFERRED;  -- 事務結束時才檢查，而非每行操作後

-- 使用方式
BEGIN;
INSERT INTO "user"(id, primary_org_id) VALUES ('u1', 'o1');  -- 此時 o1 可能尚未插入
INSERT INTO organization(id, owner_id) VALUES ('o1', 'u1');
COMMIT;  -- 提交時才檢查約束
```

---

## 10. 分區策略（Sharding & Partitioning）

### 10.1 分區策略決策矩陣

| 條件 | 建議 |
|------|------|
| 單表 < 1,000 萬筆，查詢 < 100ms | 不需分區，加好索引即可 |
| 單表 1,000 萬 ~ 1 億筆 | 評估 Partial Index + BRIN 是否足夠 |
| 單表 > 1 億筆，或有明顯時間局部性 | Range Partitioning（按時間） |
| 多租戶（multi-tenant）隔離需求 | List Partitioning（按 tenant_id） |
| 隨機分散，無明顯查詢模式 | Hash Partitioning |

### 10.2 分區鍵選擇準則

- **Range 分區：** 最常見的過濾維度（通常是時間欄位）
- **List 分區：** 高基數的分類值（tenant、region、type）
- **Hash 分區：** 均勻分散寫入壓力，無業務語義需求

**注意：** 分區鍵必須包含在所有 unique constraint 中（PostgreSQL 限制）。

### 10.3 分區範例

```sql
-- Range 分區：按月份分區的事件日誌
CREATE TABLE event_log (
  id           UUID         NOT NULL DEFAULT gen_random_uuid(),
  event_type   VARCHAR(100) NOT NULL,
  payload      JSONB,
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE event_log_2024_q1 PARTITION OF event_log
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE event_log_2024_q2 PARTITION OF event_log
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- 預設分區（捕捉超出範圍的資料）
CREATE TABLE event_log_default PARTITION OF event_log DEFAULT;

-- List 分區：多租戶隔離
CREATE TABLE order_partitioned (
  id        UUID NOT NULL,
  tenant_id UUID NOT NULL,
  status    VARCHAR(50) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY LIST (tenant_id);

CREATE TABLE order_tenant_a PARTITION OF order_partitioned
  FOR VALUES IN ('{{TENANT_A_UUID}}');

-- Hash 分區：4 個分片均勻分散
CREATE TABLE session (
  id         UUID NOT NULL,
  user_id    UUID NOT NULL,
  token_hash VARCHAR(64) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL
) PARTITION BY HASH (user_id);

CREATE TABLE session_0 PARTITION OF session FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE session_1 PARTITION OF session FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE session_2 PARTITION OF session FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE session_3 PARTITION OF session FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### 10.4 跨分區查詢注意事項

- Planner 需要能 Partition Pruning（分區裁剪）：WHERE 條件必須包含分區鍵
- 跨分區 JOIN 性能差，盡量在同一分區完成查詢
- `CREATE INDEX` 需對每個分區單獨建立（PostgreSQL 13+ 的分區索引可自動繼承）

---

## 11. 備份與復原（Backup & Recovery）

### 11.1 備份策略表

| 類型 | 頻率 | 保留期限 | 工具 | 儲存位置 |
|------|------|---------|------|---------|
| Full Backup | 每日 00:00 UTC | 30 天 | `pg_dump` / `pgbackrest` | S3 / GCS（跨區域） |
| WAL Archiving（PITR 基礎） | 持續（每 5 分鐘歸檔） | 7 天 | `pgbackrest archive-push` | S3 |
| Logical Backup（特定表） | 每週 | 90 天 | `pg_dump --table` | S3 |
| Snapshot（DB Instance） | 每日 | 7 天 | RDS Snapshot / Cloud SQL | 雲端托管 |

### 11.2 Point-in-Time Recovery（PITR）設定

```sql
-- postgresql.conf 設定（啟用 WAL 歸檔）
wal_level = replica
archive_mode = on
archive_command = 'pgbackrest --stanza={{STANZA_NAME}} archive-push %p'
archive_timeout = 300  -- 最多 5 分鐘強制歸檔一次

-- 還原到指定時間點
SELECT pg_promote();  -- 升級 standby 為 primary（若使用 standby 方式 PITR）
-- 或使用 pgbackrest restore：
-- pgbackrest --stanza={{STANZA_NAME}} --target="2024-03-15 14:30:00+00" restore
```

### 11.3 備份驗證程序

每月至少執行一次備份還原測試：

1. 從 S3 下載最新備份
2. 在隔離環境（非生產）執行還原
3. 執行 schema 完整性檢查：`pg_dump --schema-only` 比對
4. 執行基本業務查詢驗證資料可讀性
5. 記錄 RTO（還原時間）與 RPO（資料損失上限）實測值

| 指標 | 目標 | 實測值（最近一次驗證日期） |
|------|------|--------------------------|
| RTO | < 4 小時 | — |
| RPO | < 15 分鐘 | — |

---

## 12. 關聯圖（ER Diagram）

**【必須】** 使用 Mermaid `erDiagram` 語法繪製完整 ER Diagram，涵蓋所有資料表及其關聯（1:1 / 1:N / N:M）。

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK
        varchar name
        timestamptz created_at
        timestamptz deleted_at
    }
    {{table_name}} {
        uuid id PK
        uuid user_id FK
        varchar status
        timestamptz created_at
        timestamptz deleted_at
    }
    {{child_table}} {
        uuid id PK
        uuid {{table_name}}_id FK
        text content
        timestamptz created_at
    }
    users ||--o{ {{table_name}} : "has"
    {{table_name}} ||--o{ {{child_table}} : "contains"
```

> 說明：依實際資料模型填入所有資料表，關聯線必須反映 FK 約束，不得省略。

---

## 13. 資料量估算

| 資料表 | 預估初始量 | 年增長量 | 備注 |
|--------|-----------|---------|------|
| `user` | 10,000 | +5,000 | — |
| `{{table_name}}` | 100,000 | +50,000 | 超過 5,000 萬考慮分區 |
| `audit_log` | — | +1M/月 | 3 個月後考慮分區或歸檔 |

---

## 14. 敏感資料清單

| 資料表 | 欄位 | 分類 | 保護方式 | 保留期限 |
|--------|------|------|---------|---------|
| `user` | `email` | PII | pgcrypto 欄位加密 | 帳號刪除後 30 天 |
| `user` | `password_hash` | Credential | bcrypt cost=12 | 立即刪除 |
| `user` | `avatar_url` | PII | HTTPS only | 帳號刪除後 30 天 |
| `audit_log` | `ip_address` | 網路識別 | 截斷至 /24（EU 用戶） | 90 天 |
| `{{table}}` | `{{field}}` | {{分類}} | {{方式}} | {{期限}} |

---

## 15. Multi-Tenancy Data Isolation Strategies（多租戶資料隔離策略）

### 策略比較

| 策略 | 隔離等級 | 成本 | 資料洩露風險 | 適用場景 |
|------|:-------:|:----:|:-----------:|---------|
| **Shared DB + 共用 Schema**（RLS）| 低 | 低 | 中（依 RLS 正確性）| 中小型 SaaS、快速起步 |
| **Shared DB + Schema-per-Tenant** | 中 | 中 | 低（Schema 隔離）| 中型 B2B SaaS |
| **DB-per-Tenant** | 高 | 高 | 極低（完全隔離）| 企業級 / 合規要求高 |
| **混合策略** | 可設定 | 可設定 | 可設定 | 不同 Tier 套不同策略 |

**本產品決策：** {{CHOSEN_STRATEGY}}

**決策依據：** {{DECISION_RATIONALE}}

---

### Row-Level Security 實作（PostgreSQL RLS 範例）

```sql
-- 1. 在所有租戶資料表加入 tenant_id
ALTER TABLE {{TABLE_NAME}} ADD COLUMN tenant_id UUID NOT NULL
  REFERENCES tenants(id);

-- 2. 啟用 RLS
ALTER TABLE {{TABLE_NAME}} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {{TABLE_NAME}} FORCE ROW LEVEL SECURITY;

-- 3. 建立 Policy（應用層透過 current_setting 設定當前 tenant）
CREATE POLICY tenant_isolation_policy ON {{TABLE_NAME}}
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- 4. 應用層在每個連線 / Transaction 開始時設定
SET LOCAL app.current_tenant_id = '{{TENANT_UUID}}';

-- 5. 建立跨租戶查詢的超級管理員 Role（繞過 RLS）
CREATE ROLE platform_admin BYPASSRLS;
```

**RLS 安全性注意事項：**
- BYPASSRLS 只授予平台管理員 Role，禁止應用程式 Service Account 使用
- 連線池（PgBouncer）需使用 Transaction-mode，確保 SET LOCAL 不洩漏到其他 Session
- 必須測試 RLS Bypass 情境（SQL injection、Role escalation）

---

### Schema-per-Tenant 遷移策略（若採用）

```sql
-- 建立租戶 Schema
CREATE SCHEMA tenant_{{TENANT_SLUG}};

-- 在租戶 Schema 下建立資料表
CREATE TABLE tenant_{{TENANT_SLUG}}.{{TABLE_NAME}} (
  -- 與 public schema 相同結構，但無 tenant_id 欄位
);

-- 設定搜尋路徑（應用層在每個請求設定）
SET search_path TO tenant_{{TENANT_SLUG}}, public;
```

---

### 租戶識別與路由

| 識別方式 | 範例 | 適用場景 |
|---------|------|---------|
| Subdomain | `tenant1.app.com` | 品牌化 SaaS |
| URL Path | `app.com/t/tenant1/...` | 簡單 Multi-tenant |
| JWT Claim | `{ "tenant_id": "uuid" }` | API-first 產品 |
| Custom Domain | `tenant1.com`（CNAME to app）| 企業級白標 |

**本產品識別方式：** {{TENANT_IDENTIFICATION_METHOD}}

---

## 16. Schema 審查檢查清單（Schema Review Checklist）

在提交 Schema PR 前，逐項確認：

### 命名與結構
- [ ] 所有資料表名稱為 `snake_case` 單數形式
- [ ] Boolean 欄位有 `is_`、`has_`、`can_` 前綴
- [ ] Enum 欄位有 `_type` 或 `_status` 後綴
- [ ] 外鍵欄位命名為 `{referenced_table}_id`
- [ ] 索引、約束名稱遵循命名規範

### 正規化與完整性
- [ ] 無重複欄位組（違反 1NF）
- [ ] 所有非主鍵欄位完全依賴主鍵（2NF）
- [ ] 無遞移依賴（3NF），或已文件化反正規化原因
- [ ] 所有 CHECK 約束涵蓋業務規則
- [ ] 外鍵 ON DELETE 行為已明確選擇並有理由

### 索引
- [ ] 所有外鍵欄位有對應索引
- [ ] 軟刪除查詢使用 Partial Index（WHERE deleted_at IS NULL）
- [ ] 複合索引欄位順序正確（等值在前，範圍在後）
- [ ] 已使用 EXPLAIN ANALYZE 驗證高頻查詢使用正確索引
- [ ] 無重複或冗餘索引

### 安全與合規
- [ ] PII 欄位已列入敏感資料清單
- [ ] 密碼欄位僅儲存 hash（bcrypt/Argon2id），無明文
- [ ] 無直接暴露內部 ID 的設計疑慮
- [ ] 資料保留期限已定義
- [ ] GDPR 被遺忘權實作路徑已確認

### 效能
- [ ] 高寫入量表已評估索引數量（過多索引拖慢寫入）
- [ ] 超過預估 1 億筆的表已規劃分區策略
- [ ] 連線池設定已依公式計算
- [ ] 查詢效能基準表已填寫（§7.1）

### Migration
- [ ] UP 與 DOWN migration 均已撰寫
- [ ] 大表操作使用 CONCURRENTLY / 批次 backfill
- [ ] Migration 在 Staging 環境測試過執行時間
- [ ] 不會持有超過 3 秒的 table lock
- [ ] Migration 命名遵循規範

### 稽核與監控
- [ ] 有業務意義的寫入操作已套用稽核 trigger
- [ ] `updated_at` trigger 已建立
- [ ] 備份策略（§11）已確認適用於此資料庫
- [ ] 索引膨脹監控查詢已加入維運 Runbook

### HA / Replication / Read-Write Split（必查）
- [ ] Primary-Standby 或 Multi-Primary 複本架構已於 §10 或 EDD §3.6 說明，無單一寫入節點 SPOF
- [ ] 讀寫分離策略已定義（哪些查詢走 Replica，Write 一律走 Primary）

### Bounded Context 隔離（Spring Modulith HC-1，必查）
- [ ] Document Control「Owning BC / Service」已填入具體服務名稱（非 placeholder）
- [ ] 本 Schema 所有 Tables 均屬同一個 BC，無混入其他 BC 的 Table
- [ ] 無跨 BC DB-level FK（§9.5 跨 BC 引用清單已填寫；若無跨 BC 引用，明確標注「無」）
- [ ] 所有跨 BC 引用已改為 ID-only + 應用層一致性（§9.5 有對應 COMMENT 說明）
- [ ] Replica Lag 可接受上限已定義（建議 ≤ 1s），並有 Lag 監控告警
- [ ] 連線池（PgBouncer 等）已設定最大連線數，且高峰期不超過 DB max_connections 的 80%
- [ ] Sharding / Partitioning 策略（§10）已定義，含 Shard Key 選擇依據與熱點分析

---

## 17. Data Retention & Lifecycle Policy

### 17.1 資料保留政策總覽

> **法規依據**：GDPR Article 5(1)(e) Storage Limitation Principle、個人資料保護法（PDPA）、CCPA

| 資料類別 | 資料表 | 保留期限 | 保留依據 | 刪除方式 |
|---------|--------|---------|---------|---------|
| 使用者帳號資料 | `users` | 帳號刪除後 30 天 | 服務條款 | 軟刪除 → 排程硬刪除 |
| 交易記錄 | `orders`, `payments` | 7 年 | 稅務法規 | 歸檔後軟刪除 |
| 日誌記錄 | `audit_logs` | 2 年 | 合規稽核需求 | 滾動刪除（older than retention） |
| 會話資料 | `sessions` | 90 天 | 安全需求 | TTL 自動過期 |
| 個人識別資訊 | `users.email`, `users.phone` | 依帳號保留期 | GDPR Art.17 | 匿名化（anonymize）或刪除 |
| 行銷同意記錄 | `consents` | 同意撤銷後 5 年 | GDPR Art.7 舉證義務 | 永久保留（合規要求） |
| 系統備份 | S3/GCS Backup | 90 天 | DR 需求 | Object lifecycle policy |

### 17.2 GDPR Right to Erasure（被遺忘權）實作

```sql
-- ============================================================
-- GDPR Art.17 Right to Erasure — 使用者資料刪除程序
-- ============================================================

-- Step 1: 觸發軟刪除（立即執行）
UPDATE users
SET
    deleted_at  = NOW(),
    -- 匿名化個人可識別資訊
    email       = CONCAT('deleted_', id, '@gdpr.invalid'),
    phone       = NULL,
    name        = 'Deleted User',
    -- 保留統計需要的非個人欄位
    status      = 'deleted'
WHERE id = $1
  AND deleted_at IS NULL;

-- Step 2: 刪除關聯個人資料（立即執行）
DELETE FROM user_profiles WHERE user_id = $1;
DELETE FROM sessions       WHERE user_id = $1;
DELETE FROM notifications  WHERE user_id = $1;
-- 注意：orders 等交易記錄依稅務規定保留，但需匿名化 user 欄位

-- Step 3: 記錄刪除請求（審計用）
INSERT INTO gdpr_erasure_requests (
    user_id, requested_at, completed_at, requestor_ip, status
) VALUES ($1, NOW(), NOW(), $2, 'completed');
```

**非同步清理任務（Async Job，30 天後執行）：**

```python
# tasks/gdpr_hard_delete.py
from datetime import datetime, timedelta

def run_gdpr_hard_delete():
    """30 天軟刪除後執行硬刪除（GDPR Art.17 合規）"""
    cutoff = datetime.utcnow() - timedelta(days=30)

    with db.transaction():
        # 刪除軟刪除超過 30 天的使用者
        deleted_users = db.execute("""
            SELECT id FROM users
            WHERE deleted_at < %s
            AND status = 'deleted'
        """, (cutoff,))

        for user in deleted_users:
            # 確認已匿名化（防禦性檢查）
            assert db.get("SELECT email FROM users WHERE id=%s", user.id).email.endswith('@gdpr.invalid')
            # 硬刪除關聯資料
            db.execute("DELETE FROM users WHERE id = %s", user.id)

        logger.info(f"GDPR hard delete: {len(deleted_users)} users removed")
```

### 17.3 資料最小化原則（Data Minimization）

**收集前評估清單（DPIA Checklist）：**

- [ ] 此欄位是否為業務功能必需？（不需要 → 不收集）
- [ ] 是否已取得使用者明確同意（如需要）？
- [ ] 是否已記錄在 Privacy Notice 中？
- [ ] 是否已定義保留期限並實作自動刪除？
- [ ] 是否為敏感資料？（需額外加密或存取控制）
- [ ] 是否需要跨境傳輸？（GDPR Chapter V 合規審查）

**敏感欄位分類：**

| 敏感程度 | 欄位類型 | 處理要求 |
|---------|---------|---------|
| 最高 | 密碼、支付卡號、社保/身分號碼 | 加密儲存、嚴格存取控制、不可備份至非加密存儲 |
| 高 | Email、電話、地址、IP 地址 | 欄位加密或 Tokenization、存取日誌 |
| 中 | 姓名、出生年月、使用偏好 | 標準存取控制、匿名化備份 |
| 低 | 非識別統計資料、公開資訊 | 標準保護 |

### 17.4 資料存取稽核（Data Access Audit）

```sql
-- 每次存取敏感欄位時記錄（透過 PostgreSQL Row-Level Security + audit trigger）
CREATE TABLE data_access_logs (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name  VARCHAR(100) NOT NULL,
    record_id   UUID         NOT NULL,
    field_name  VARCHAR(100),           -- NULL = 整筆記錄存取
    action      VARCHAR(20)  NOT NULL,  -- SELECT, UPDATE, DELETE
    actor_id    UUID,                   -- 操作者（user_id 或 service_account）
    actor_type  VARCHAR(50),            -- 'user', 'admin', 'service', 'system'
    reason      TEXT,                   -- 存取原因（如：GDPR deletion request）
    ip_address  INET,
    accessed_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 索引（依稽核查詢需求）
CREATE INDEX idx_dal_record    ON data_access_logs (table_name, record_id);
CREATE INDEX idx_dal_actor     ON data_access_logs (actor_id, accessed_at);
CREATE INDEX idx_dal_accessed  ON data_access_logs (accessed_at);
```

### 17.5 跨境資料傳輸合規（Cross-Border Data Transfer）

| 傳輸場景 | 合規機制 | 說明 |
|---------|---------|------|
| EU → US 傳輸 | EU-US Data Privacy Framework / SCCs | 若使用美國 Cloud Provider |
| 台灣 → EU 傳輸 | GDPR Art.46 Adequacy Decision / BCR | 視傳輸性質判斷 |
| 資料落地（Data Residency）要求 | 區域化部署 + Multi-Region DB | 若客戶合約要求資料落地 |
| 備份傳輸 | 加密傳輸（TLS 1.3） + 靜態加密（AES-256） | 所有備份場景 |

### 17.6 Schema 刪除安全模式

```sql
-- NEVER 直接 DROP TABLE 包含用戶資料的表
-- CORRECT: 三步驟安全刪除

-- Step 1: 標記廢棄（不影響服務）
COMMENT ON TABLE old_feature_table IS 'DEPRECATED: 2026-01-01 - will be removed 2026-07-01';
ALTER TABLE old_feature_table RENAME TO _deprecated_old_feature_table_20260101;

-- Step 2: 驗證無流量（觀察 6 個月）
-- 監控 pg_stat_user_tables 確認 last_seq_scan / last_idx_scan

-- Step 3: 確認無流量後安全刪除
-- DROP TABLE _deprecated_old_feature_table_20260101;  -- 僅在確認後執行
```

---

## 18. Database Observability & Health Monitoring

### 18.1 關鍵監控指標

```sql
-- 連線數監控
SELECT count(*), state, wait_event_type, wait_event
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state, wait_event_type, wait_event;

-- 慢查詢識別（需啟用 pg_stat_statements）
SELECT query, calls, mean_exec_time, stddev_exec_time, rows
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- 超過 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 表格膨脹（Table Bloat）監控
SELECT schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    n_dead_tup, n_live_tup,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;

-- 索引使用率（找出未使用的索引）
SELECT indexrelid::regclass AS index_name,
    relid::regclass AS table_name,
    idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0  -- 從未被使用
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 18.2 Alerting 規則

| 指標 | 警告閾值 | 緊急閾值 | 說明 |
|------|---------|---------|------|
| 連線數使用率 | > 70% | > 90% | 最大連線數的百分比 |
| 複製延遲（Replication Lag） | > 10s | > 60s | Primary-Replica 延遲 |
| 表格膨脹率（Dead Tuple Ratio） | > 10% | > 30% | 需執行 VACUUM |
| 長事務（Long Running Transactions） | > 60s | > 300s | 可能造成鎖等待 |
| Lock Wait | > 5s | > 30s | 鎖競爭問題 |
| Disk Usage | > 70% | > 85% | 儲存空間不足 |

---
