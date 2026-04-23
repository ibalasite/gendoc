---
doc-type: ARCH
output-path: docs/ARCH.md
upstream-docs:
  - docs/req/       # 所有 req 素材（IDEA 定義）
  - docs/IDEA.md
  - docs/BRD.md
  - docs/PRD.md
  - docs/PDD.md
  - docs/VDD.md     # Layer 3.5 — 視覺設計系統（Design Token 命名空間、資產管線架構影響 CDN/Build Pipeline 選型）
  - docs/EDD.md
quality-bar: "所有 PRD P0 功能在 §2 有對應元件；每個 Service 有 Interface 定義；依賴方向正確（Controller→Service→Repository）；C4 L1/L2/L3 Mermaid 圖均已生成；Data Flow Diagram 含 PII 流向表；§9 Zero-Trust 安全架構已描述；Network Architecture VPC 圖已生成；Scalability Ceiling Analysis 至少 4 個瓶頸點；ADR 至少 1 個完整條目；Architecture Review Checklist 12 個 NFR 均已驗證；所有 Mermaid 圖均使用 TD 方向。"
---

# ARCH 生成規則

## Iron Rule: 累積上游讀取

每份文件生成時，必須讀取所有上游文件（累積，非僅直接父文件）。
若某上游文件不存在，靜默跳過；不得因上游缺失而降低覆蓋深度。
docs/req/* 中的所有素材（由 IDEA.md 定義）也必須全部關聯讀取。

---

## 上游讀取規則

- `docs/IDEA.md`（若存在）：了解產品願景與業務目標——ARCH 的系統邊界必須服務 IDEA 的商業目標
- `docs/BRD.md`：了解業務需求與成功指標——ARCH 的 SLO/可用性設計需與 BRD 的業務指標對應
- `docs/PRD.md`：了解所有 P0/P1 功能——ARCH 的元件分層必須涵蓋所有功能
- `docs/PDD.md`（若存在）：了解 UI 設計、畫面欄位、互動模式——ARCH 的前後端介面設計需與 PDD 定義一致
- `docs/VDD.md`：了解 Design Token 命名空間、資產格式規格、CDN 和 Build Pipeline 的架構需求（若存在）
- `docs/EDD.md`：了解技術選型、DDD Bounded Context、Security 模型——ARCH 需與 EDD 保持嚴格一致

**EDD 優先原則**：ARCH 的技術選型、架構風格必須與 EDD §2 一致；如有差異，標記 `[UPSTREAM_CONFLICT]`。

### docs/req/ 素材關聯讀取

若 `docs/IDEA.md` 存在且 Appendix C 引用了 `docs/req/` 素材，對每個存在的檔案讀取全文，結合 Appendix C「應用於」欄位標有「ARCH §」的段落，作為生成 ARCH 對應章節（元件分層、部署拓撲、系統邊界）的補充依據。優先採用素材原文描述，而非 AI 推斷。若無引用，靜默跳過。

---

## 上游衝突偵測規則

讀取完所有上游文件後，掃描：
- EDD 的技術選型是否與 PRD 的非功能需求衝突（e.g., 延遲、可用性目標）
- PDD 的元件架構假設是否與 EDD 的系統架構設計衝突
- BRD 的規模預期是否與 EDD 的 Capacity Planning 一致

若發現矛盾，標記 `[UPSTREAM_CONFLICT]` 並依衝突解決機制處理。

---

## 章節結構（全章節）

ARCH 必須涵蓋以下所有章節（對應 templates/ARCH.md 結構）：

- §0 Document Control（DOC-ID / 上游文件連結）
- §1 ADR Index（架構決策記錄索引，至少 3 個標題）
- §2 元件清單（Module / Package / Service）
- §3 分層設計（含依賴方向）
- §3.1~§3.3 C4 Model（L1 Context / L2 Container / L3 Component）
- §3.4 Data Flow Diagram（Write Path 序列圖 + PII 敏感資料流向表 + Masking 規則）
- §4 介面定義（Interface / Abstract Class，以 LANG_STACK 語法）
- §4 Service Boundaries（Context Map / Anti-Corruption Layer）
- §5 Domain 模型（不含 ORM annotation，純業務語意）
- §6 跨元件通訊設計
- §7 錯誤處理策略（分層錯誤轉換 + 錯誤碼規範）
- §7 High-Availability Design（HA 策略）
- §8 Mermaid 架構圖（TD 方向，至少 2 張）
- §9.1 Zero-Trust 安全架構（mTLS / RBAC / 網路分隔）
- §9.2 Secret Rotation Strategy（DB 憑證 / API Key 輪替週期）
- §9.4 Network Architecture（VPC 拓撲 Mermaid 圖 + Security Group 規則表 + AZ 配置）
- §9.5 Compliance Architecture Mapping（法規/元件/資料類型/技術措施/稽核日誌）
- §10.2 Scalability Ceiling Analysis（瓶頸上限表 + 架構演進 4 Phase 路線）
- §12 Observability Architecture（Metrics / Tracing / Logging 三支柱）
- §14 ADR（完整 ADR 條目，含 Context/Decision/Consequences）
- §15 Architecture Review Checklist（12 個 Non-Functional Requirements）
- §16 FinOps Cost Optimization（成本分配 Tag 策略 + 月度 Review 規則）
- §17 API Gateway & Service Mesh（Kong/AWS API GW 配置 + Circuit Breaker 狀態機）

---

## Key Fields

### §0 Document Control

- DOC-ID：`ARCH-<PROJECT_SLUG 大寫>-<YYYYMMDD>`
- 上游 EDD：`[EDD.md](EDD.md)`
- 上游 PDD：`[PDD.md](PDD.md)`（若存在）
- 上游 PRD：`[PRD.md](PRD.md)`

### §1 ADR Index（架構決策記錄索引）

至少列出 3 個架構決策標題，例如：
- ADR-001 選擇 PostgreSQL 作為主資料庫
- ADR-002 採用 Canary 部署策略
- ADR-003 使用 NATS 作為消息佇列

### §2 元件清單

| 元件 | 層次 | 職責 | 對應 PRD 功能 |
|------|------|------|-------------|
| `api.handler` | Controller | 接收 HTTP/gRPC，驗證輸入 | 所有 P0 功能 |
| `service.<domain>` | Service | 業務規則、事務邊界 | 依功能拆分 |
| `repository.<entity>` | Repository | DB 操作、返回 Domain 物件 | — |
| `infra.cache` | Infrastructure | Redis 快取封裝 | — |
| `infra.queue` | Infrastructure | NATS/消息佇列封裝 | — |

### §3 分層設計（含依賴方向）

```
┌──────────────────────────────────────┐
│           Controller Layer            │
│  (HTTP handler / gRPC / WebSocket)   │
│  → 輸入驗證、路由、不含業務邏輯       │
├──────────────────────────────────────┤
│            Service Layer              │
│  → 業務規則、事務邊界、跨 Repo 協調   │
├──────────────────────────────────────┤
│           Repository Layer            │
│  → DB 操作封裝，只返回 Domain 物件    │
├──────────────────────────────────────┤
│         Infrastructure Layer          │
│  → Redis、NATS、外部 API、Email 等    │
└──────────────────────────────────────┘

依賴方向：Controller → Service → Repository → DB
         Service → Infrastructure（透過 Interface）
禁止：Repository 呼叫 Service
禁止：Controller 直接存取 DB
```

### §3.1~§3.3 C4 Model

- **L1 Context Diagram**：系統邊界 + 外部參與者（用戶、第三方系統）
- **L2 Container Diagram**：主要容器（Web API / DB / Cache / Queue / Worker）
- **L3 Component Diagram**：容器內部的主要元件

所有 C4 圖均使用 Mermaid，TD 方向，包含真實服務名稱（非 placeholder）。

### §3.4 Data Flow Diagram

- Write Path 序列圖（關鍵資料寫入路徑）
- PII 敏感資料流向表：

| PII 資料類型 | 流經元件 | 儲存位置 | Masking 規則 |
|------------|---------|---------|------------|
| Email | API → UserService → DB | PostgreSQL | Log 中遮罩後 4 碼 |
| Phone | <依業務> | <依業務> | 僅顯示後 4 碼 |

### §4 介面定義

每個 Service 和 Repository 必須先定義 Interface（以 LANG_STACK 語法）。

**Python 範例**：
```python
# service/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional
from domain.models import User, Order

class UserServiceInterface(ABC):
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    async def create_user(self, email: str, name: str) -> User: ...
```

**Go 範例**：
```go
// service/interfaces.go
type UserService interface {
    GetUser(ctx context.Context, userID string) (*User, error)
    CreateUser(ctx context.Context, email, name string) (*User, error)
}
```

依實際 lang_stack 選擇對應語言語法。

### §4 Service Boundaries

- Context Map（依 EDD §3.4 對應）
- Anti-Corruption Layer：若有外部系統整合，說明翻譯層設計

### §5 Domain 模型

列出所有 Domain 物件（不含 ORM annotation，純業務語意）：

```markdown
#### User
- id: UUID
- email: string（不可變，建立後不可修改）
- name: string
- status: UserStatus（active / inactive / suspended）
- createdAt: DateTime（UTC）
- deletedAt: DateTime?（軟刪除）
```

### §6 跨元件通訊設計

| 通訊類型 | 使用場景 | 實作方式 |
|---------|---------|---------|
| 同步 HTTP | Client → API | RESTful JSON / gRPC proto |
| 事件驅動 | 非同步業務事件 | NATS / RabbitMQ（依 EDD 選型）|
| 快取 | 高頻讀取 | Redis（TTL 依業務決定）|
| DB 事務 | 跨表寫入 | PostgreSQL transaction block |

事件定義表（若有 Message Queue）：

| 事件名稱 | Publisher | Subscriber | Payload |
|---------|----------|-----------|---------|
| `order.created` | OrderService | NotificationService | {order_id, user_id, amount} |
| `user.status_changed` | UserService | AuditService | {user_id, from, to} |

### §7 錯誤處理策略

**分層錯誤轉換**

1. Repository 層 → 回傳 Domain Error（DatabaseError、NotFoundError）
2. Service 層 → 轉換為 Business Error（UserNotFound、InsufficientBalance）
3. Controller 層 → 轉換為 HTTP 4xx / 5xx

**錯誤碼規範**

| HTTP 碼 | 場景 |
|---------|------|
| 400 | 輸入驗證失敗 |
| 401 | 未認證 |
| 403 | 無權限 |
| 404 | 資源不存在 |
| 409 | 業務衝突（如重複建立）|
| 422 | 業務規則違反 |
| 429 | Rate limit |
| 500 | 系統錯誤（不揭露內部訊息）|

### §7 High-Availability Design

- HA 策略：Active-Active / Active-Standby（必須選定並說明理由）
- 失效轉移設計
- 健康檢查頻率
- 最小健康 Pod 數

### §8 Mermaid 架構圖（TD 方向，至少 2 張）

**§8.1 元件依賴圖**：展示 Controller / Service / Repository / Infrastructure 層的完整依賴關係。

**§8.2 請求生命週期圖**：依主要功能的 Sequence Diagram，展示完整請求從 Client 到 DB 的路徑。

### §9.1 Zero-Trust 安全架構

- mTLS：服務間通訊均需雙向 TLS 認證
- RBAC：角色 → 權限 → 資源的完整映射
- 網路分隔：Public Subnet（Ingress only）/ Private Subnet（Service）/ Data Subnet（DB/Cache）

### §9.2 Secret Rotation Strategy

| Secret 類型 | 輪替頻率 | 輪替方式 | 告警 |
|------------|---------|---------|------|
| DB 憑證 | 每 90 天 | 自動輪替（Vault / AWS Secrets Manager）| 到期前 14 天 |
| API Key（第三方）| 每 180 天 | 手動 + 審計 | 到期前 30 天 |
| JWT 簽署金鑰 | 每 30 天 | 自動輪替 | 立即告警 |

### §9.4 Network Architecture

- VPC 拓撲 Mermaid 圖（Public / Private / Data Subnet + NAT Gateway + Bastion）
- Security Group 規則表

| Security Group | 允許 Inbound | 允許 Outbound |
|---------------|-------------|--------------|
| SG-Ingress | 0.0.0.0/0:443 | SG-App:8080 |
| SG-App | SG-Ingress:8080 | SG-DB:5432, SG-Cache:6379 |
| SG-DB | SG-App:5432 | — |

- AZ 配置：至少 2 個 AZ，確保 HA

### §9.5 Compliance Architecture Mapping

| 法規 | 相關元件 | 資料類型 | 技術措施 | 稽核日誌 |
|------|---------|---------|---------|---------|
| GDPR | UserService, DB | PII（email, phone）| 加密 + Masking | Audit Log |
| <依業務需求列出> | <元件> | <資料類型> | <措施> | <稽核> |

至少識別 PII 相關元件。

### §10.2 Scalability Ceiling Analysis

**瓶頸上限表（至少 4 個瓶頸點）**

| 瓶頸點 | 當前上限 | 達到上限症狀 | 解決方案 |
|--------|---------|------------|---------|
| PostgreSQL 連線池 | 100 連線 | 連線等待 > 1s | PgBouncer / 讀寫分離 |
| Redis 記憶體 | <N> GB | OOM / eviction | 集群化 / TTL 調整 |
| API Pod CPU | 70% | P99 延遲上升 | HPA + 優化演算法 |
| <依系統特性> | <上限> | <症狀> | <解決方案> |

**架構演進 4 Phase 路線**

| Phase | 觸發條件 | 架構變更 |
|-------|---------|---------|
| Phase 1（現況）| QPS < N | Modular Monolith + 單一 DB |
| Phase 2 | QPS N~N | 讀寫分離 + Redis Cluster |
| Phase 3 | QPS N~N | 按業務域拆分 Microservice |
| Phase 4 | QPS > N | CQRS + Event Sourcing |

### §12 Observability Architecture

- Metrics：Prometheus + Grafana，定義關鍵 Dashboard 指標
- Tracing：Jaeger / OpenTelemetry，定義 span 命名慣例
- Logging：Loki / ELK，JSON Lines 格式

### §14 ADR（Architecture Decision Records）

每個 ADR 必須包含：

```markdown
#### ADR-<N>：<決策標題>

**狀態**：已接受 / 已棄用 / 提議中

**背景（Context）**：
<為什麼需要做這個決策？有什麼約束條件？>

**決策（Decision）**：
<選擇了什麼？為什麼？>

**後果（Consequences）**：
- 正面：<帶來的好處>
- 負面：<引入的代價或技術債>
```

至少 1 個完整 ADR 條目（含 Context / Decision / Consequences）。

### §15 Architecture Review Checklist（12 個 NFR）

| # | Non-Functional Requirement | 驗證方式 | 狀態 |
|---|--------------------------|---------|------|
| 1 | 可用性 ≥ 99.9% | SLO Dashboard | ○ |
| 2 | P99 延遲 ≤ 500ms | k6 Load Test | ○ |
| 3 | 水平擴展（HPA）| k8s HPA 測試 | ○ |
| 4 | 零停機部署 | Canary / Blue-Green | ○ |
| 5 | 資料加密（at-rest + in-transit）| 稽核 | ○ |
| 6 | RBAC 存取控制 | 滲透測試 | ○ |
| 7 | 稽核日誌完整性 | Audit Log 驗證 | ○ |
| 8 | RTO ≤ 30 分鐘 / RPO ≤ 5 分鐘 | DR 演練 | ○ |
| 9 | 可觀測性（Metrics/Tracing/Logging）| Dashboard | ○ |
| 10 | 依賴服務降級（Circuit Breaker）| Chaos Test | ○ |
| 11 | API Rate Limiting | Load Test | ○ |
| 12 | Secret Rotation 自動化 | Vault 設定驗證 | ○ |

### §16 FinOps Cost Optimization

**成本分配 Tag 策略**

每個資源必須包含以下 Tag：
- `Environment`：dev / staging / prod
- `Service`：<service-name>
- `Team`：<team-name>
- `CostCenter`：<cost-center-code>

**月度 FinOps Review 規則**

- 80% 預算：自動發送告警至 Slack #finops 頻道
- 100% 預算：自動凍結非 Critical 資源的部署
- 120% 預算：立即通知 Engineering Manager + CTO

**成本優化重點**：Reserved Instance / Spot Instance 比例、未使用資源清理、DB 儲存空間 + PIOPS 優化。

### §17 API Gateway & Service Mesh

**API Gateway 配置標準（Kong / AWS API Gateway）**

| Plugin | 配置值 | 目的 |
|--------|--------|------|
| JWT Auth | RS256，Token TTL 1h | 認證 |
| Rate Limiting | 100 req/min per IP | 防濫用 |
| Prometheus | 每個 route 暴露 metrics | 可觀測性 |
| Request Transform | Header 注入 Correlation ID | 追蹤 |

**Circuit Breaker 狀態機**

```
Closed ──(錯誤率 > 閾值)──► Open ──(等待 Timeout)──► Half-Open
  ▲                                                       │
  └──────────────(測試請求成功)──────────────────────────┘
```

配置：
- 錯誤閾值：50%（超過 10 次請求）
- Open 持續時間：30 秒
- Half-Open 測試次數：3 次

---

## Self-Check Checklist（生成前品質核查）

- [ ] 所有 PRD P0 功能在 ARCH §2 有對應元件
- [ ] 每個 Service 有對應 Interface 定義
- [ ] 依賴方向正確（Controller → Service → Repository，不逆向）
- [ ] Domain 模型不含 DB 框架 annotation（純業務語意）
- [ ] §8 至少 2 張 Mermaid 圖，均為 TD 方向
- [ ] §1 ADR Index 已建立（至少列出 3 個架構決策標題）
- [ ] §3.1~§3.3 C4 L1/L2/L3 Mermaid 圖均已生成（含真實服務名稱）
- [ ] §3.4 Data Flow Diagram 已生成（Write Path 序列圖 + PII 資料流向表）
- [ ] §9.1 Zero-Trust 安全架構已描述（含 mTLS/RBAC/網路分隔）
- [ ] §9.2 Secret Rotation Strategy 已填寫（DB 憑證/API Key 輪替週期）
- [ ] §9.4 Network Architecture VPC 圖已生成（含 Public/Private/Data Subnet + SG 規則）
- [ ] §9.5 Compliance Architecture Mapping 已填寫（至少識別 PII 相關元件）
- [ ] §10.2 Scalability Ceiling Analysis 已填寫（至少 4 個瓶頸點 + 架構演進路線）
- [ ] §14 ADR 至少 1 個完整 ADR 條目（含 Context/Decision/Consequences）
- [ ] §15 Architecture Review Checklist 已生成（12 個 NFR 均已驗證）
- [ ] §4 Service Boundaries：服務邊界定義（Context Map / Anti-Corruption Layer）是否已明確？
- [ ] §7 High-Availability Design：HA 策略（Active-Active / Active-Standby）是否已定義？
- [ ] §12 Observability Architecture：Metrics / Tracing / Logging 三支柱是否已定義？
- [ ] §16 FinOps Cost Optimization：成本分配 Tag 策略（Environment/Service/Team）是否已定義？
- [ ] §16 月度 FinOps Review：成本預算警報規則（80%/100%/120% 閾值）是否已設定？
- [ ] §17 API Gateway：Kong/AWS API GW 配置標準（JWT + Rate Limiting + Prometheus plugin）是否已說明？
- [ ] §17 Circuit Breaker：熔斷器狀態機（Closed/Open/Half-Open + 錯誤閾值配置）是否已設計？

若有遺漏，自行補齊後再寫入檔案。
