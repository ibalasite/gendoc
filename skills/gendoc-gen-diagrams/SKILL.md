---
name: gendoc-gen-diagrams
description: |
  從 EDD/ARCH/API/PRD 提取全部 9 種 Server UML 圖，並（條件執行）
  從 FRONTEND.md/PDD.md/VDD.md 生成 16 種 Frontend UML 圖，
  輸出至 docs/diagrams/（server-: use-case/class×3/object/sequence×N/comm/state×N/activity×N/component/deployment/er-diagram；
  frontend-: use-case/class×3/object/sequence×3/state×2/activity×3/component/deployment/communication）。
  另輸出 class-inventory.md（class→test file 對應表）。
  一律使用 Mermaid 語法，不依賴外部腳本。
  可獨立呼叫或由 gendoc-auto 自動呼叫。
allowed-tools:
  - Read
  - Write
  - Bash
  - Skill
---

# gendoc-gen-diagrams — 生成九大 UML 圖（多張，無模糊空間）

從 EDD Mermaid 架構圖章節提取所有圖，並依 API.md / PRD.md / ARCH.md 補充多張 Sequence、Activity、State Machine，
輸出至 `docs/diagrams/`，並額外產生 `class-inventory.md`（class → test file 對應表）。

**核心原則（優先順序）：**
1. **提取**：EDD §10（新版）或 §4.5（舊版）已有的 Mermaid 程式碼直接提取，不修改內容
2. **補充**：EDD 某類圖不足時，從 API.md（Sequence）/ PRD.md（Activity）/ ARCH.md（Component/Deployment）推斷並生成
3. **強制完整**：9 種 UML 類型缺一不可，生成後做完整性驗證，缺少的類型依上游文件合成
4. **最低張數**：Sequence ≥ 3、Activity ≥ 3、State Machine ≥ 每個有狀態 Entity 各一、Class 固定 3 張

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：讀取環境與 state

```bash
_CWD="$(pwd)"
_DOCS_DIR="${_CWD}/docs"
_DIAGRAMS_DIR="${_DOCS_DIR}/diagrams"
mkdir -p "$_DIAGRAMS_DIR"
_APP_NAME=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('project_name','') or '$(basename $_CWD)')" 2>/dev/null || basename "$_CWD")
_LANG_STACK=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('lang_stack','unknown'))" 2>/dev/null || echo "unknown")
echo "專案：$_APP_NAME"
echo "語言：$_LANG_STACK"
echo "=== 掃描上游文件 ==="
for f in EDD.md ARCH.md API.md SCHEMA.md PRD.md PDD.md VDD.md FRONTEND.md; do
  [[ -f "${_DOCS_DIR}/$f" ]] && echo "✓ $f" || echo "✗ $f（跳過）"
done

_CLIENT_TYPE=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('client_type','none'))" 2>/dev/null || echo "none")
echo "Client Type：$_CLIENT_TYPE"
_HAS_FRONTEND=$([ -f "${_DOCS_DIR}/FRONTEND.md" ] && echo "yes" || echo "no")
echo "Frontend UML：$( [[ "$_CLIENT_TYPE" != 'none' && "$_CLIENT_TYPE" != 'api-only' && "$_HAS_FRONTEND" == 'yes' ]] && echo '✓ 將生成 Step 2B 前端 UML' || echo '✗ 跳過（client_type=none 或 api-only，或缺 FRONTEND.md）' )"
```

---

## Step 1：讀取上游文件

讀取順序（缺檔靜默跳過）：

| 文件 | 讀取目標 | 用途 |
|------|---------|------|
| `docs/EDD.md` | **全文掃描**（優先看 §4.5 UML 9 大圖，其次 §10，其次全文） | 九大 UML 圖的 Mermaid 程式碼（**主要來源**）|
| `docs/ARCH.md` | Component / Deployment 章節 | Component Diagram、Deployment Diagram 補充 |
| `docs/API.md` | 所有 Endpoint 列表 | 補充生成多張 Sequence Diagram |
| `docs/SCHEMA.md` | 資料模型章節 | ER Diagram（額外，非 UML 9 之一）|
| `docs/PRD.md` | §User Stories / §業務流程 | 補充生成多張 Activity Diagram |
| `docs/FRONTEND.md` | UI 元件架構、WS 協議、場景系統（若存在）| **Step 2B 前端 UML 主要來源** |
| `docs/PDD.md` | 介面設計、使用者流程（若存在）| Step 2B 前端用例 / 活動圖 補充 |
| `docs/VDD.md` | 視覺設計、動畫規格（若存在）| Step 2B 前端狀態機 / 元件圖 補充 |

**提取規則：**

- **EDD 掃描策略（含版本 fallback，防止 section 編號差異導致漏圖）：**
  1. 優先讀取 EDD §4.5（UML 9 大圖，骨架標準位置）整節，提取所有 mermaid 程式碼塊
  2. 若 §4.5 找不到或圖數 < 3，嘗試 EDD §10（舊版因規則錯誤而落地於此的 UML）
  3. 最後 fallback：掃描 EDD 全文，以 mermaid 塊類型分類（`classDiagram` / `stateDiagram-v2` / `sequenceDiagram` / `erDiagram` / `flowchart` / `graph`）
  4. 以找到圖最多的那個策略為準，並在摘要中記錄「提取源：§4.5 / §10 / 全文掃描」
- 從 API.md 提取 Endpoint 列表（格式：`METHOD /path — 說明`），每個 P0 Endpoint 生成一張 Sequence Diagram
- 從 PRD §User Stories 提取每個主要業務流程，每個生成一張 Activity Diagram
- EDD 中若某類圖缺失，則依 EDD 其他章節的描述推斷並生成（非憑空捏造）
- 若相關上游文件均不存在，則跳過對應圖，在摘要中標注「✗ 跳過（缺乏來源）」

---

## Step 2：生成九大 UML 圖

逐一生成以下檔案，使用 **Write 工具**寫入 `docs/diagrams/`。

每個檔案的標準格式：

```markdown
---
diagram: <圖表識別名>
uml-type: <UML 圖類型中文名>
source: <來源文件及章節>
generated: <ISO8601 時間戳>
---

# <圖表標題>

> 來源：<文件> §<章節>

\`\`\`mermaid
<從上游文件提取或依上游文件內容推斷的 Mermaid 程式碼>
\`\`\`
```

---

> **實作完整度原則**：每張圖必須讓開發者在沒有其他文件的情況下，能夠 1:1 實作出完整系統。
> 禁止模糊標注、省略法（「...」）、無型別的方法、無條件的決策點、無協定的連線。
> 若 EDD §4.5 中已有符合本節標準的 Mermaid 程式碼，直接提取；若不符合標準，依上游文件補齊後提取。

---

### 2.1 use-case.md — Use Case Diagram

**UML 類型**：Use Case Diagram（UML 九大之一）

**來源**：EDD §10.1（新版）/ §4.5.1（舊版）

**格式**：Mermaid `flowchart TD`（Mermaid 不支援原生 usecase 語法）

**強制完整度標準**：
- Actor 節點：`[ActorName\n角色說明]`，名稱來自 PRD §2 使用者角色定義，不得使用「用戶」等籠統稱呼
- Use Case 節點：`((UC-N: UseCaseName))`，UC 編號與 PRD AC 編號對應
- 系統邊界：`subgraph SystemName [SystemName — BRD §1 系統名稱]`
- 每條關聯線標注關係類型：`-- 直接使用 -->`、`-- <<extend>> -->`、`-- <<include>> -->`
- 必須涵蓋 PRD 全部 P0 + P1 功能對應的 Use Case；每個 Actor 至少 2 個 Use Case
- **禁止**：省略任何 Actor、用「etc.」代替具體 Use Case、無 UC 編號的節點

若 EDD §4.5.1 已有程式碼，直接提取；若無，依 EDD §2（系統功能列表）和 PRD §2（使用者角色）推斷並生成。

---

### 2.2 class-domain.md — Class Diagram（Domain Layer）

**UML 類型**：Class Diagram（UML 九大之一）

**來源**：EDD §10.2（新版）/ §4.5.2（舊版）

**格式**：Mermaid `classDiagram`

**強制完整度標準（每個 class 每個屬性/方法都必須達到）：**

**屬性格式**（三者缺一不可）：`visibility attributeName : Type`
- visibility：`+`（public）`-`（private）`#`（protected）`~`（package）
- 型別精確：`String`、`UUID`、`Integer`、`Decimal`、`Boolean`、`DateTime`，Enum 直接引用 enum class 名稱
- **禁止**：無 visibility、無型別、`any`、`Object` 等模糊型別

**方法格式**（四者缺一不可）：`visibility methodName(param1: Type, param2: Type) ReturnType`
- 每個參數有名稱和型別
- 回傳型別精確：`void`、`String`、`Order`、`List~Order~`、`Optional~User~`
- **禁止**：無參數型別、無回傳型別、空方法列表、`create()` 無參數

**Enum 獨立定義**（每個 Enum 必須在 Domain 層圖中定義）：
```
class OrderStatus {
    <<enumeration>>
    PENDING
    CONFIRMED
    PROCESSING
    SHIPPED
    DELIVERED
    CANCELLED
    REFUNDED
}
```
所有枚舉值必須列全（來自 PRD AC 或 SCHEMA.md），**禁止「...」省略**

**關聯線格式**（格式：`ClassA "cardinality" relationSymbol "cardinality" ClassB : roleLabel`）：
- 繼承：`ParentClass <|-- ChildClass`
- 介面實作：`InterfaceA <|.. ClassB`（ClassB implements InterfaceA）
- 組合：`ClassA *-- "1..*" ClassB : contains`
- 聚合：`ClassA o-- "0..*" ClassB : has`
- 關聯：`ClassA "1" --> "0..*" ClassB : roleLabel`
- 依賴：`ClassA ..> ClassB : uses`
- cardinality 兩端都要標：`"1"`、`"0..1"`、`"1..*"`、`"0..*"`
- **禁止**：無 cardinality 的關聯線、無 role label 的模糊關聯

**Domain Layer 必含 class 類型（stereotype 必標）**：
- `<<AggregateRoot>>`（≥ 1）：含所有業務屬性和 Invariant 方法
- `<<Entity>>`（≥ 2）：所有業務 Entity
- `<<ValueObject>>`：所有值物件（Money、Address 等）
- `<<DomainEvent>>`：所有領域事件（對應 EDD §4.6 每行）
- `<<Repository>>`（interface 定義，≥ 1）：抽象 Repository，含所有查詢方法簽名

若 EDD §4.5.2 按層次提供多個 classDiagram，提取 Domain 層；若只有一張，篩選 Domain 層 class 並補齊至標準。

---

### 2.3 class-application.md — Class Diagram（Application Layer）

**UML 類型**：Class Diagram（UML 九大之一）

**來源**：EDD §10.2（新版）/ §4.5.2（舊版）

同 2.2 屬性/方法/關聯線格式標準（完全相同，不再重複）。

**Application Layer 必含 class 類型（stereotype 必標）**：
- `<<UseCase>>`（每個 PRD AC 對應一個，含 `+ execute(command: CommandDTO): ResponseDTO`）
- `<<ApplicationService>>`（跨 UseCase 的編排邏輯）
- `<<DTO>>`（Command DTO、Query DTO，含所有欄位和型別）
- `<<Port>>`（定義外部服務介面，如 `IEmailPort`、`IPaymentPort`）

---

### 2.4 class-infra-presentation.md — Class Diagram（Infrastructure + Presentation Layer）

**UML 類型**：Class Diagram（UML 九大之一）

**來源**：EDD §10.2（新版）/ §4.5.2（舊版）

同 2.2 屬性/方法/關聯線格式標準（完全相同，不再重複）。

**Infrastructure + Presentation Layer 必含 class 類型（stereotype 必標）**：
- `<<RepositoryImpl>>`（實作 Domain 層 `<<Repository>>` interface）
- `<<Adapter>>`（實作 Application 層 `<<Port>>` interface，對接外部服務）
- `<<Controller>>`（含所有 HTTP handler 方法：`+ createOrder(req: CreateOrderRequestDTO): Promise~ResponseDTO~`）
- `<<RequestDTO>>`（含 validation decorator 說明）
- `<<ResponseDTO>>`（含所有 API 回傳欄位）

**若 EDD §4.5.2 未按層次分張**，從整體 Class Diagram 依架構層次拆分成 3 張，每張對應一個層次。

**Class Inventory 表格**（所有 3 張 classDiagram 生成完畢後，在 `docs/diagrams/class-inventory.md` 填入完整清單）

---

### 2.5 object-snapshot.md — Object Diagram

**UML 類型**：Object Diagram（UML 九大之一）

**來源**：EDD §10.3（新版）/ §4.5.3（舊版）

**格式**：Mermaid `classDiagram`（instance 模式）

**強制完整度標準**：
- instance class 格式：`class entityName_instanceId { <<instance>> ... }`
- **所有屬性填具體業務範例值**（非型別定義）：
  - UUID：`"a3f8c1d2-4b5e-6f7a-8c9d-0e1f2a3b4c5d"`
  - String：`"Alice Wang"`（真實姓名，非 `"string"` 或 `"name"`）
  - Enum：直接寫枚舉值 `PROCESSING`
  - Decimal：`1250.00`
  - DateTime：`"2024-03-15T14:30:00Z"`
- 關聯線標注 role label：`ordA_ord001 --> usrB_usr123 : placedBy`
- 每個 `<<AggregateRoot>>` class 必須有 ≥ 1 張 Object Diagram；不同業務狀態各一張（如 Order PENDING 一張、Order PROCESSING 一張）
- **禁止**：屬性值為型別名稱（`id: UUID`）、空值（`name: ""`）、佔位值（`"example"`、`"test"`）

若系統確實無任何 Aggregate（純無狀態 API），生成 1 張 DTO 實例快照，標注 `> 本系統為無狀態服務，無 Aggregate Root`。

---

### 2.6 sequence-{flow-name}.md — Sequence Diagram（每個主要業務流程一張）

**UML 類型**：Sequence Diagram（UML 九大之一）

**來源**：EDD §10.4（新版）/ §4.5.4（舊版）主 + API.md Endpoint（補充）

**格式**：Mermaid `sequenceDiagram`

**強制完整度標準（每個箭頭都必須達到）：**

**參與者宣告**（每張圖頂部必填）：
```
participant Client as Client（前端/行動端）
participant Controller as OrderController
participant Service as OrderService
participant Repo as IOrderRepository
participant DB as PostgreSQL
participant Cache as Redis（若有）
participant Queue as NATS（若有）
```

**呼叫箭頭格式**（四者缺一不可）：
```
Caller->>Callee: methodName(param1: Type, param2: Type)
```
- 方法名精確（`createOrder`、`findByUserId`）；**禁止** `call`、`request`、`create` 等模糊動詞
- 參數有名稱 + 型別（`userId: UUID, items: OrderItem[]`）；**禁止**空括號 `()` 或 `(data)` 無型別
- 第一個從 Client 發出的箭頭：`Client->>Controller: POST /orders {userId: UUID, items: OrderItem[], paymentMethod: PaymentMethod}`

**回傳箭頭格式**（二者缺一不可）：
```
Callee-->>Caller: ReturnType | HTTP StatusCode {responseBody}
```
- 服務層：`return Order` / `throw OrderNotFoundException(orderId)`
- HTTP：`201 Created {orderId: UUID, status: OrderStatus, createdAt: DateTime}` / `409 Conflict {error: "DUPLICATE_ORDER", existingOrderId: UUID}`
- **禁止**：無型別的「成功」回傳、`return result` 等模糊回傳

**alt 條件分支格式**（所有條件路徑都必須有）：
```
alt 庫存充足（inventory >= requestedQty）
    Service->>Repo: save(order: Order)
    Repo-->>DB: INSERT INTO orders ...
    DB-->>Repo: rowsAffected: 1
    Repo-->>Service: return order: Order
    Service-->>Controller: return order: Order
    Controller-->>Client: 201 Created {orderId, status: PENDING}
else 庫存不足（inventory < requestedQty）
    Service-->>Controller: throw InsufficientStockException(available: Integer)
    Controller-->>Client: 422 Unprocessable {error: "INSUFFICIENT_STOCK", available: Integer, requested: Integer}
end
```
- **禁止**：只有 Happy Path 無 alt、`alt success`/`alt error` 等無具體條件描述

**必含段落**：
- 每個 Mutation 操作：Happy Path + ≥ 3 個 Error Path（業務規則違反 + 系統故障 + 認證/授權失敗）
- 非同步操作：`par [async: 說明非同步原因]` 包裹
- 重試邏輯：`loop [retry: 最多 N 次，間隔 Xms]` 包裹
- 資料庫事務：明確標注 `DB->>DB: BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK ON ERROR`

**最低張數**：≥ API.md §3 Mutation Endpoint（POST/PATCH/PUT/DELETE）數量，且 ≥ 3 張；Happy Path 和 Error Path 各自獨立一張（**不得合併**）

**上下游一致性**：本節服務內部視角必須與 API.md §1 Client 視角邏輯一致；有差異則標記 `> ⚠️ [UPSTREAM_CONFLICT] 與 API.md §1 {endpoint} 有差異，待 ADR 釐清`

**檔名格式**：`sequence-{flow-name}.md`（如 `sequence-create-order.md`、`sequence-create-order-error.md`）

---

### 2.7 communication.md — Communication Diagram

**UML 類型**：Communication Diagram（UML 九大之一）

**來源**：EDD §10.5（新版）/ §4.5.5（舊版）

**格式**：Mermaid `flowchart LR`

**強制完整度標準**：
- 每個節點：元件名稱 + 技術：`OrderService\n(Node.js 20.x)"`
- 每條邊：序號 + 完整訊息名稱 + 通訊協定 + 埠號：
  - 同步：`"1: POST /orders\nHTTPS:443"` → 實線 `-->`
  - 非同步：`"3: OrderCreated{orderId, status}\nNATS: order.created"` → 虛線 `-.->` + 標注 `[async]`
- 序號連續（1, 2, 3...），反映完整訊息交換流程（**禁止**跳號或省略中間訊息）
- **觸發條件**：系統有 Message Queue / Event Bus → 展示事件驅動訊息流；純同步架構 → 展示主要 HTTP 呼叫協作 + 標注 `> 本系統為同步架構`
- **禁止**：無序號的邊、無協定的邊

---

### 2.8 state-machine-{entity}.md — State Machine Diagram（每個有狀態 Entity 一張）

**UML 類型**：State Machine Diagram（UML 九大之一）

**來源**：EDD §10.6（新版）/ §4.5.6（舊版）

**格式**：Mermaid `stateDiagram-v2`

**強制完整度標準（每個轉換箭頭都必須達到）：**

**轉換格式**（三者缺一不可）：
```
StateA --> StateB : trigger [guard] / action
```
- `trigger`：精確觸發事件名（`confirmOrder()`、`paymentCaptured`、`cancelRequested(reason: String)`）；**禁止**「點擊」「用戶操作」等模糊描述
- `[guard]`：觸發條件（`[balance >= amount]`、`[retries <= 3]`、`[stock > 0]`）；**必須有**，無條件填 `[always]`
- `/ action`：副作用（`/ emit OrderConfirmed`、`/ notifyUser(email: String)`、`/ decrementStock(qty: Integer)`）；**禁止省略**
- **禁止** 在 transition label 使用 `<br/>`（`stateDiagram-v2` 不支援，Safari/Firefox 破圖）；需換行說明時改用 `note right of STATE` 區塊

**進入/退出動作**（有業務邏輯的狀態必填）：
```
state PROCESSING {
    entry: validateInventory(items), lockStock(items)
    exit: releaseStockLock(items)
}
state PROCESSING : 訂單處理中，庫存已鎖定，TTL 30 分鐘
```

**必含元素**：
- 初始狀態：`[*] --> InitialState : create(params) [valid] / assignId()`
- 所有終止狀態連到 `[*]`（如 `DELIVERED --> [*]`、`CANCELLED --> [*]`）
- 所有合法轉換（正向 + 逆向，如 `PROCESSING --> CANCELLED`）
- 狀態說明標注：`state PENDING : 等待用戶確認，TTL 30 分鐘後自動取消`

**最低張數**：class-domain.md 中含 `status: StatusEnum` 或 `state: StateEnum` 欄位的每個 Entity 各一張（≥ 1）

**降級處理**：若 EDD §4.5.6 / §10.6 為空，從 EDD §4.6 Domain Events 的狀態轉移描述推斷並生成（不得跳過此圖類型）

**檔名格式**：`state-machine-{entity-name}.md`（如 `state-machine-order.md`、`state-machine-payment.md`）

---

### 2.9 activity-{flow}.md — Activity Diagram（每個主要業務流程一張）

**UML 類型**：Activity Diagram（UML 九大之一）

**來源**：EDD §10.7（新版）/ §4.5.7（舊版）主 + PRD §User Stories（補充）

**格式**：Mermaid `flowchart TD`（決策點 `{ }`，開始/結束 `([ ])`）

**強制完整度標準**：

**泳道（Swimlane）強制使用**：
```mermaid
flowchart TD
  subgraph Client ["Client（使用者角色名）"]
    A([開始]) --> B[精確動作名稱(params)]
  end
  subgraph API ["API Server（ControllerName + ServiceName）"]
    C{具體條件描述？}
  end
  subgraph DB ["Database（技術名稱）"]
    D[(INSERT INTO tableName...)]
  end
```
- 每個 Actor / 系統元件獨立 subgraph 泳道
- 泳道標注 Actor 角色 + 負責的 class 名稱

**決策點格式**（必須兩個分支都標注具體條件）：
```
C{庫存 >= 請求數量？}
C -->|是（庫存充足）| D
C -->|否（庫存不足）| E
```
- **禁止**：單分支決策點、`Yes`/`No` 等無業務語意標注、無條件描述的菱形

**節點命名**：精確動詞 + 受詞（`validateInventory(items: OrderItem[])`、`chargePaymentGateway(amount: Decimal, method: PaymentMethod)`）；**禁止**「處理訂單」「進行操作」等模糊描述

**Fork/Join 並行路徑**（有並行業務流程必標）：
```
D -->|fork| E & F
E --> G
F --> G
G -->|join| H
```

**最少 3 張**（各自獨立檔案）：
1. 用戶主線操作（≥ 2 個決策點，覆蓋 PRD AC 正常 + 異常流程）
2. 系統內部處理流程（≥ 7 個步驟，含 fork/join 並行路徑）
3. 異常/補救流程（含補償動作的逆向路徑，如退款/回滾）

若已提取張數 < 3，**必須補充**至 ≥ 3 張（從 PRD User Stories 推斷）

**檔名格式**：`activity-{flow-name}.md`（如 `activity-checkout.md`、`activity-refund.md`）

---

### 2.10 component.md — Component Diagram

**UML 類型**：Component Diagram（UML 九大之一）

**來源**：EDD §10.8（新版）/ §4.5.8（舊版）主 + ARCH.md（補充）

**格式**：Mermaid `flowchart LR`（`graph LR`）

**強制完整度標準**：

**元件節點格式**（三者缺一不可）：
```
OrderSvc["OrderService\nNode.js 20.x / Express 4.18\nPort: 3000"]
```
- 元件業務名稱
- 技術 + 精確版本號（`Node.js 20.x`、`Python 3.12`、`PostgreSQL 16`）
- 通訊埠或協定（`Port: 3000`、`Port: 5432`、`gRPC: 50051`）

**連線格式**（每條連線必須標注）：
- 同步：`OrderSvc -->|"POST /payments\nHTTPS:443"| PaymentSvc`
- 非同步：`OrderSvc -.->|"NATS Subject: order.created\nasync"| EventBus`
- 資料庫：`OrderSvc -->|"TCP:5432\nPostgreSQL Wire Protocol"| DB`
- **禁止**：無協定的連線、無埠號的服務連線

**系統邊界**：
```
subgraph Internal["Internal Network Zone"]
  OrderSvc
  DB
end
subgraph External["External Services (Third-party)"]
  PaymentGW["Stripe\nPayment Gateway API v2"]
end
```

**必含元件**：EDD §3.3 技術棧總覽中所有元件（不得遺漏），每個元件至少有 1 條連線

若 EDD §4.5.8 / §10.8 已有程式碼，直接提取（檢查是否符合標準，不符合則補齊）；若無，從 ARCH.md 元件架構章節推斷。**不得跳過此圖類型**。

---

### 2.11 deployment.md — Deployment Diagram

**UML 類型**：Deployment Diagram（UML 九大之一）

**來源**：EDD §10.9（新版）/ §4.5.9（舊版）主 + ARCH.md 部署章節（補充）

**格式**：Mermaid `flowchart TD`

**強制完整度標準**：

**節點格式**（四者缺一不可）：
```
OrderSvc["OrderService\nImage: order-service:1.2.3\nCPU: 0.5 / Mem: 512Mi\nReplicas: 2-10 (HPA)"]
```
- 服務名稱
- Docker Image + 精確版本 tag（來自 EDD §9 CI/CD 或 ARCH.md）
- CPU limit / Memory limit（來自 EDD §7 k8s 資源規格）
- Replicas 範圍（含 HPA min/max）

**網路區域 subgraph（必填）**：
```
subgraph Internet["Internet"]...end
subgraph DMZ["DMZ / Ingress Zone"]...end
subgraph Internal["Internal / App Zone"]...end
subgraph DataZone["Data Zone"]...end
```
元件不得跨區域放置

**連線格式**（每條連線必須標注）：
```
Ingress -->|"HTTPS:443\nTLS 1.3"| OrderSvc
OrderSvc -->|"TCP:5432\nPostgreSQL Wire Protocol"| PostgreSQL
OrderSvc -.->|"TCP:4222\nNATS Protocol\nasync"| NATS
```
- 協定名稱 + 埠號；外部連線必填 TLS/加密說明；非同步用虛線

**儲存卷**（有 PersistentVolume 必標）：
```
PostgreSQL -->|"PVC: db-data\n100Gi / SSD"| Storage[("PersistentVolume\nStorageClass: local-path")]
```

**必含元素**：Ingress Controller、所有 Microservice（含版本）、所有 DB/Cache/Queue（含版本）、網路區域邊界、所有外部依賴

若 EDD §4.5.9 / §10.9 已有程式碼，直接提取（補齊至標準）；若無，從 ARCH.md 部署架構推斷。**不得跳過此圖類型**。

---

### 2.12 er-diagram.md — ER Diagram（額外，非 UML 9 之一）

**類型**：ER Diagram（資料庫關聯圖）

**來源**：SCHEMA.md

**明確標注**：此為資料庫表格關聯圖，與 UML Class Diagram 性質不同：
- ER Diagram → 資料庫表格、欄位、外鍵關係（`erDiagram`）
- Class Diagram → 物件模型、方法、繼承、介面實作

直接複製 SCHEMA.md 的 `erDiagram` 區塊。若 SCHEMA.md 不存在，跳過此圖。

Frontmatter 中加入：

```yaml
diagram: er-diagram
uml-type: ER Diagram（資料庫關聯圖，非 UML Class Diagram）
note: 此圖描述資料庫表格關聯，請勿與 class-*.md 的物件模型混淆
```

---

## Step 2.9（完整性驗證）：9 種 UML 類型全覆蓋強制檢查

**在 class-inventory.md 之前，必須執行此驗證步驟。**

```
╔════════════════════════════════════════════════════════════╗
║  UML 完整性驗證（9 種缺一不可）                             ║
╠════════════════════════════════════════════════════════════╣
║  [1] Use Case Diagram       → use-case.md             ✓/✗ ║
║  [2] Class Diagram          → class-*.md（≥3張）       ✓/✗ ║
║  [3] Object Diagram         → object-snapshot.md      ✓/✗ ║
║  [4] Sequence Diagram       → sequence-*.md（≥Mutation端點數，≥3）✓/✗ ║
║  [5] Communication Diagram  → communication.md        ✓/✗ ║
║  [6] State Machine Diagram  → state-machine-*.md（≥1）✓/✗ ║
║  [7] Activity Diagram       → activity-*.md（≥3張）    ✓/✗ ║
║  [8] Component Diagram      → component.md            ✓/✗ ║
║  [9] Deployment Diagram     → deployment.md           ✓/✗ ║
╚════════════════════════════════════════════════════════════╝
```

**驗證規則：**
- 列出 `docs/diagrams/` 目錄下實際生成的檔案
- 對照上表，標出 ✓（已生成）/ ✗（缺失）
- **任何 ✗ 必須立即補生成**，不得在摘要中標注「跳過」後結束
- 補生成策略（按優先順序）：
  1. 重新掃描 EDD 全文，尋找對應的 mermaid 塊
  2. 依 ARCH.md / API.md / PRD.md 相關章節推斷並生成
  3. 若所有來源均無線索，依專案類型和現有圖表合理推斷（標注「推斷生成」）

**額外驗證項目（9 種圖通過後執行，任一不通過必須立即補齊）：**

**Class Diagram 實作完整度**：
- [ ] 所有 class 有 stereotype（無裸 class）
- [ ] 所有屬性格式為 `visibility name: Type`（無缺 visibility、無缺型別、無 `any`/`Object`）
- [ ] 所有方法格式為 `visibility name(param: Type): ReturnType`（每個參數有名稱+型別、有回傳型別）
- [ ] 所有 Enum 獨立定義並列出全部枚舉值（禁止「...」省略）
- [ ] 所有關聯線有 cardinality（兩端）+ role label
- [ ] Domain Layer 含 ≥ 1 `<<AggregateRoot>>`、≥ 2 `<<Entity>>`、≥ 1 `<<Repository>>` interface
- [ ] 每個 `<<DomainEvent>>` class 在 EDD §4.6 Domain Events 表中有對應行
- [ ] class 名稱與 ARCH.md §3 Domain 模型和 SCHEMA.md Table 名稱完全一致

**Object Diagram 實作完整度**：
- [ ] 每個 `<<AggregateRoot>>` 有 ≥ 1 張 Object Diagram
- [ ] 所有屬性填具體業務範例值（禁止型別名稱、空值、`"example"` 等佔位值）

**Sequence Diagram 實作完整度**：
- [ ] 張數 ≥ API.md §3 Mutation Endpoint 數量（且 ≥ 3）；Happy Path 和 Error Path 各自獨立
- [ ] 每個箭頭有精確方法名 + 參數名稱和型別
- [ ] 所有回傳箭頭有型別或 HTTP 狀態碼 + 回應體結構
- [ ] 所有條件分支用 `alt` 且有具體條件描述（禁止 `alt success`/`alt error`）
- [ ] 每個 Mutation 有 ≥ 3 個 Error Path（業務規則違反 + 系統故障 + 認證/授權失敗）

**State Machine 實作完整度**：
- [ ] 每個 transition 有 `trigger [guard] / action` 三段
- [ ] 有業務邏輯的狀態有 entry/exit 動作
- [ ] 所有終態連到 `[*]`；初始狀態連自 `[*]`

**Activity Diagram 實作完整度**：
- [ ] 每張有泳道（subgraph，含 Actor 角色 + class 名稱）
- [ ] 每個決策點兩個分支都有具體條件標注（禁止 `Yes`/`No`）
- [ ] 有並行業務流程的圖有 fork/join 標注

**Component Diagram 實作完整度**：
- [ ] 每個節點有技術 + 精確版本 + 埠號
- [ ] 每條連線有協定 + 埠號（同步/非同步已區分）
- [ ] EDD §3.3 所有元件均已包含

**Deployment Diagram 實作完整度**：
- [ ] 每個節點有 Image:tag + CPU/Mem limit + Replicas
- [ ] 有網路區域 subgraph（DMZ/Internal/DataZone）
- [ ] 所有連線有協定 + 埠號；外部連線有 TLS 說明
- [ ] 有 PVC 的服務已標注儲存卷

---

## Step 2B：生成前端 / Client UML 圖（條件執行）

**執行條件**：`client_type != none` AND `client_type != api-only` AND `FRONTEND.md` 存在

若條件不符，印出 `[Step 2B] 跳過（client_type=none 或缺 FRONTEND.md）` 後直接進入 Step 3。

---

### 2B 前端 UML 總覽

所有前端 UML 輸出至 `docs/diagrams/`，檔名前綴 `frontend-`。

每個檔案使用與 Step 2 相同的標準格式（frontmatter + Mermaid block）。

> **引擎適配原則**：從 `.gendoc-state.json` 的 `tech_stack_hints` 或 FRONTEND.md 首段確認客戶端引擎
> （Cocos Creator / Unity / HTML5/Web / React Native / Flutter）。
> 所有圖的元件名稱、API、class 命名必須符合該引擎的實際 API（不得使用通用占位符）。

---

### 2B-1 frontend-use-case.md — 前端用例圖

**UML 類型**：Use Case Diagram（flowchart TD）

**來源**：FRONTEND.md 功能列表 + PDD.md §用戶流程 + PRD.md §User Stories

**強制完整度標準**：
- Actor 節點：玩家（Player）/ 管理員（Admin）/ 引擎系統（Engine）等前端相關 Actor
- Use Case 節點：`((UC-F-N: UseCaseName))`，與 PRD/PDD 的 UC 編號對應
- 系統邊界：`subgraph ClientApp [Client App — 引擎名稱 版本]`
- 涵蓋 FRONTEND.md 所有 P0 前端功能；每個 Actor 至少 3 個 Use Case
- **禁止**：「點擊」等過於細節的操作作為 Use Case；模糊描述

---

### 2B-2 frontend-class-component.md — 前端類別圖：UI 元件層

**UML 類型**：Class Diagram（classDiagram）

**來源**：FRONTEND.md §元件架構 + VDD.md §元件清單

**強制完整度標準**：
- 依引擎架構分層（Cocos Creator 用 Node/Component/Script；Unity 用 GameObject/MonoBehaviour；React 用 Component/Hook）
- 每個 Component class 必須包含：
  - 引擎基類繼承（`Component extends cc.Component` 或 `extends MonoBehaviour`）
  - 公開屬性（`@property` decorator 或 `[SerializeField]`，標注型別）
  - 生命週期方法（`onLoad/start/update` 或 `Awake/Start/Update`）
  - 業務方法（對應 FRONTEND.md 中該元件的職責）
- 元件間關聯：組合 / 依賴 / 事件訂閱（標注 EventTarget 或 Signal）
- 涵蓋 FRONTEND.md 所有主要 UI 元件（≥ 8 個 class）
- **禁止**：無引擎基類、無屬性型別、無生命週期方法

---

### 2B-3 frontend-class-scene.md — 前端類別圖：場景控制器層

**UML 類型**：Class Diagram（classDiagram）

**來源**：FRONTEND.md §場景系統 + VDD.md §場景流程

**強制完整度標準**：
- 每個 Scene/Screen class 包含：場景名稱、加載參數、場景切換方法
- 場景管理器（SceneManager）或導航服務（NavigationService）必須存在
- 場景資料傳遞機制（GlobalData / EventBus / Store）明確標注
- 涵蓋 FRONTEND.md 所有場景（≥ 3 個 Scene class + 1 個 SceneManager）
- **禁止**：場景間無連線、無資料傳遞說明

---

### 2B-4 frontend-class-services.md — 前端類別圖：Client 服務層

**UML 類型**：Class Diagram（classDiagram）

**來源**：FRONTEND.md §網路層 + API.md（WS/REST 協議）+ EDD.md §WS 協議

**強制完整度標準**：
- WebSocket 服務類：連線方法（`connect/disconnect/reconnect`）+ 訊息發送/接收方法（帶型別）+ 事件回調
- HTTP/REST 服務類（若有）：每個 API endpoint 對應一個方法（方法名、參數型別、回傳型別）
- Store/State 管理（如適用）：`GameStore`、`UserStore` 等，含 State 型別定義
- 資料模型 class（DTO）：對應 API.md 請求/回應格式，每個欄位有型別
- 涵蓋 FRONTEND.md 所有網路層元件（≥ 5 個 class）
- **禁止**：無型別的 `any`、無方法的空 class

---

### 2B-5 frontend-object-snapshot.md — 前端物件圖：UI 執行時快照

**UML 類型**：Object Diagram（classDiagram instance 模式）

**來源**：FRONTEND.md §UI 狀態管理 + VDD.md §畫面規格

**強制完整度標準**：
- 描述一個具代表性的執行時刻（如：「玩家進入遊戲房間後，主介面已載入，WebSocket 已連線」）
- 每個物件實例：`object instanceName`，屬性為具體值（非空值）
- 至少包含：遊戲主元件實例、Store 實例、WS 實例
- 物件間連線標注當前關係（has / subscribes / references）

---

### 2B-6 ~ 2B-8 frontend-sequence-*.md — 前端循序圖（≥ 3 張）

**UML 類型**：Sequence Diagram（sequenceDiagram）

**來源**：FRONTEND.md §WS 協議 + §場景切換 + §主要操作流程

必須生成至少 3 張：

**2B-6 frontend-sequence-ws.md — WebSocket 連線與訊息協議**：
- Participant：Player / Client / WebSocket / Server
- 涵蓋：連線建立（connect + handshake）、心跳（ping/pong）、斷線重連、訊息收發格式
- 每個 msg 標注訊息類型和 payload 欄位（不得用「...」省略）

**2B-7 frontend-sequence-scene.md — 場景切換流程**：
- Participant：Player / SceneManager / ResourceLoader / Server
- 涵蓋：資源預加載、loading 進度回調、舊場景解構、新場景初始化、WS 狀態保持
- 標注每個 async 操作的 await 位置

**2B-8 frontend-sequence-shoot.md — 主要遊戲交互流程（依遊戲類型）**：
- 若為捕魚遊戲：玩家射擊 → 子彈飛行 → 命中判斷（Server）→ 結果廣播 → UI 更新的完整流程
- 若為其他遊戲：以主要操作流程替代（需完整覆蓋一個完整的 request-response-UI 循環）
- Participant 涵蓋：Player、Client Components、Server、Other Players

---

### 2B-9 ~ 2B-10 frontend-state-*.md — 前端狀態機圖（≥ 2 張）

**UML 類型**：State Machine Diagram（stateDiagram-v2）

**Mermaid 強制語法規則**：
- **禁止** 在 transition label 使用 `<br/>`（無效語法）
- 複合條件用逗號分隔：`trigger [guard1, guard2] / action`
- 每個狀態的詳細說明放在 `note right of STATE` 區塊，不放在 label 中

**2B-9 frontend-state-scene.md — 場景狀態機**：
- States：LOADING / LOBBY / GAME / RESULT / ERROR 等（依 FRONTEND.md 定義）
- 每個 state 標注 entry / exit action
- Guard condition 來自 FRONTEND.md 場景切換條件
- 用 `note right of STATE` 描述每個場景的 UI 元件和 WS 狀態

**2B-10 frontend-state-ui.md — UI 元件狀態機**：
- 描述最關鍵的 UI 元件狀態（如：武器選擇器、炮台控制器、金幣顯示）
- States 對應 FRONTEND.md 定義的互動狀態（IDLE / ACTIVE / ANIMATING / DISABLED）
- 每個 transition 標注觸發事件（用戶操作 / WS 事件 / 計時器）

---

### 2B-11 ~ 2B-13 frontend-activity-*.md — 前端活動圖（≥ 3 張）

**UML 類型**：Activity Diagram（flowchart TD）

**2B-11 frontend-activity-gameplay.md — 遊戲主流程活動圖**：
- 從玩家進入房間到遊戲結束的完整流程
- 包含：資源加載 → WS 連線 → 等待玩家 → 遊戲進行中 → 結算 → 返回大廳
- fork/join 節點標注並行操作（如：UI 渲染 ‖ WS 接收 ‖ 音效播放）
- 每個 decision 節點標注條件（來自 FRONTEND.md 或 PRD）

**2B-12 frontend-activity-ui.md — UI 互動活動圖**：
- 描述主要 UI 互動的完整操作流程（點擊 → 動畫 → 狀態更新 → WS 發送 → 等待回應 → UI 刷新）
- swimlane：`Player | ClientApp | Server`
- 涵蓋 FRONTEND.md 中至少 3 個主要互動操作

**2B-13 frontend-activity-init.md — 客戶端初始化流程**：
- 引擎初始化 → 資源加載 → WS 連線 → 認證 → 場景載入 的完整序列
- 標注每個步驟的 timeout 和 error path（失敗時的 fallback）
- retry 邏輯可見（WS 重連次數 / 資源重試策略）

---

### 2B-14 frontend-component.md — 前端元件圖：引擎節點樹

**UML 類型**：Component Diagram（graph TD）

**來源**：FRONTEND.md §場景結構 + §節點樹設計

**強制完整度標準**：
- 描述引擎的場景節點樹（Cocos Node Tree / Unity Hierarchy / React Component Tree）
- 每個節點標注：`NodeName[NodeName\n元件: Script1, Script2\n資源: prefab路徑]`
- 節點間關係：Parent → Child（包含 ZOrder 或層級信息）
- 標注關鍵節點的 active/inactive 規則（條件顯示邏輯）
- 至少包含主遊戲場景的完整節點樹（深度 ≥ 3 層，寬度依實際設計）

---

### 2B-15 frontend-deployment.md — 前端部署圖：建構管線

**UML 類型**：Deployment Diagram（graph TD）

**來源**：FRONTEND.md §建構與部署 + ARCH.md §CDN/Hosting

**強制完整度標準**：
- 建構目標平台（Web/H5、iOS、Android、Desktop 等，來自 FRONTEND.md）
- 每個目標的建構工具和輸出格式（`Cocos Creator Build → web-mobile bundle`）
- 部署目標（CDN / App Store / Google Play / 私有伺服器）含 URL 格式
- CI/CD 管線（若 ARCH.md 有描述，包含 Pipeline 節點）
- 靜態資源版本控制策略（hash-filename / CDN invalidation）

---

### 2B-16 frontend-communication.md — 前端協作圖：WS 協議互動

**UML 類型**：Communication Diagram（flowchart LR）

**來源**：FRONTEND.md §WS/網路協議 + API.md §WebSocket Events

**強制完整度標準**：
- Participant 節點：`Client[Client\n版本+引擎]`、`WSServer[WebSocket Server\n技術棧]`、`GameRoom[Game Room\n狀態]`、`Database[DB]`
- 每條訊息線標注：編號 + 訊息類型 + payload 結構（不得省略欄位）
- 訊息分類（標色或 subgraph）：系統訊息 / 遊戲事件 / 廣播
- 雙向訊息（Client→Server 和 Server→Client）完整覆蓋
- 涵蓋 API.md 中所有 WebSocket event types

---

### 2B-17 Step 2B 完整度驗證

生成前端 UML 後執行自我檢查：

```
=== Step 2B 前端 UML 完整度驗證 ===
  frontend-use-case.md       ✓/✗ (Actor 數: N, UC 數: N)
  frontend-class-component.md ✓/✗ (class 數: N, 有基類繼承: Y/N)
  frontend-class-scene.md    ✓/✗ (Scene 數: N, 有 SceneManager: Y/N)
  frontend-class-services.md ✓/✗ (Service 數: N, 有 WS 服務: Y/N)
  frontend-object-snapshot.md ✓/✗ (instance 數: N)
  frontend-sequence-ws.md    ✓/✗ (涵蓋 connect/heartbeat/reconnect: Y/N)
  frontend-sequence-scene.md ✓/✗ (涵蓋 async 資源加載: Y/N)
  frontend-sequence-shoot.md ✓/✗ (涵蓋完整 request-response 循環: Y/N)
  frontend-state-scene.md    ✓/✗ (state 數: N, 有 note 區塊: Y/N)
  frontend-state-ui.md       ✓/✗ (state 數: N, 無 <br/> 語法: Y/N)
  frontend-activity-gameplay.md ✓/✗ (有 fork/join: Y/N)
  frontend-activity-ui.md    ✓/✗ (有 swimlane: Y/N)
  frontend-activity-init.md  ✓/✗ (有 error path: Y/N)
  frontend-component.md      ✓/✗ (節點樹深度 ≥ 3: Y/N)
  frontend-deployment.md     ✓/✗ (平台數: N)
  frontend-communication.md  ✓/✗ (訊息數: N, 雙向覆蓋: Y/N)

  不符合標準的圖：[列出] → 自動修正後重新驗證
```

若有 ✗ 項目，主 Claude 依對應章節的「強制完整度標準」自動修正後繼續。

---

## Step 3：生成 class-inventory.md

這是最重要的額外輸出，供 `test-plan` 和 RTM 讀取。

**來源**：解析 Step 2 生成的所有 `class-*.md` 中的 `class ClassName` 定義。

### 推斷 src/test 路徑規則

從 `.gendoc-state.json` 的 `lang_stack` 欄位判斷：

| lang_stack | src 副檔名 | src 根路徑 | test 命名 | test 根路徑 |
|-----------|-----------|-----------|---------|-----------|
| `typescript` / `javascript` | `.ts` / `.js` | `src/` | `*.test.ts` | `tests/unit/` |
| `python` | `.py` | `src/` | `test_*.py` | `tests/unit/` |
| `java` | `.java` | `src/main/java/` | `*Test.java` | `src/test/java/` |
| `golang` / `go` | `.go` | `internal/` | `*_test.go` | `internal/`（同目錄）|
| `csharp` / `dotnet` | `.cs` | `src/` | `*.Tests.cs` | `tests/unit/` |
| `php` | `.php` | `src/` | `*Test.php` | `tests/unit/` |
| 其他 | 標注 `（待確認）` | — | — | — |

### 路徑推斷邏輯

1. 從 classDiagram 中解析每個 `class ClassName` 和其 stereotype（`<<Entity>>`, `<<UseCase>>`, `<<Controller>>` 等）
2. 依 stereotype 對應架構層次（Domain / Application / Infrastructure / Presentation）
3. 依層次對應目錄結構：
   - Domain → `src/domain/{entity-name}/`
   - Application → `src/application/{use-case-name}/`
   - Infrastructure → `src/infrastructure/{adapter-name}/`
   - Presentation → `src/presentation/{controller-name}/` 或 `src/api/`
4. 生成 TC-ID 前綴：`TC-UNIT-{CLASSNAME-UPPER}`

### class-inventory.md 格式

```markdown
---
generated: <ISO8601>
source: docs/diagrams/class-*.md
purpose: class-to-test mapping for test-plan RTM
---

# Class Inventory — 類別清單與測試追蹤

> 自動生成自 docs/diagrams/class-*.md
> 規則：1 Class → 1 src/ 實作檔 → 1 tests/unit/ 測試檔

## 類別清單

| Class | Stereotype | Layer | src 路徑（推斷）| test 路徑（推斷）| TC-ID 前綴 |
|-------|-----------|-------|--------------|--------------|-----------|
| User | Entity | Domain | src/domain/user/User.ts | tests/unit/domain/User.test.ts | TC-UNIT-USER |
| IUserRepository | interface/Repository | Domain | src/domain/user/IUserRepository.ts | tests/unit/domain/IUserRepository.test.ts | TC-UNIT-IUSERREPO |
| CreateUserUseCase | UseCase | Application | src/application/user/CreateUserUseCase.ts | tests/unit/application/CreateUserUseCase.test.ts | TC-UNIT-CREATEUSER |
| UserRepositoryImpl | RepositoryImpl | Infrastructure | src/infrastructure/user/UserRepositoryImpl.ts | tests/unit/infrastructure/UserRepositoryImpl.test.ts | TC-UNIT-USERREPOIMPL |
| UserController | Controller | Presentation | src/presentation/user/UserController.ts | tests/unit/presentation/UserController.test.ts | TC-UNIT-USERCTRL |

## 測試追蹤統計

| 層次 | Class 數 | 預期 Test File 數 |
|------|---------|----------------|
| Domain | N | N |
| Application | N | N |
| Infrastructure | N | N |
| Presentation | N | N |
| **合計** | **N** | **N** |

## 1:1:N 規則提醒

- 每個 Class 對應一個測試檔案（1:1）
- 每個 Public Method 至少 3 個測試案例：S（Success）/ E（Error）/ B（Boundary）（1:N）

## 給 test-plan 的指示

test-plan.md §15.2 Unit Test RTM 應從本表格填充 Class 和 Test File 欄位。
每個 TC-ID 前綴後接 `-S01`, `-E01`, `-B01` 等流水號。
```

---

## Step 4：輸出摘要

生成完成後輸出以下摘要：

```
=== gendoc-gen-diagrams 完成 ===
  輸出目錄：docs/diagrams/
  
  Server UML 九大圖：
    ✓/✗ use-case.md                  （Use Case Diagram，來自 EDD §4.5.1）
    ✓/✗ class-domain.md              （Class Diagram - Domain，來自 EDD §4.5.2）
    ✓/✗ class-application.md        （Class Diagram - Application，來自 EDD §4.5.2）
    ✓/✗ class-infra-presentation.md （Class Diagram - Infra/Presentation，來自 EDD §4.5.2）
    ✓/✗ object-snapshot.md          （Object Diagram，來自 EDD §4.5.3）
    ✓/✗ sequence-{flow}.md          （Sequence Diagram，共 N 張，來自 EDD §4.5.4 + API.md）
    ✓/✗ communication.md            （Communication Diagram，來自 EDD §4.5.5）
    ✓/✗ state-machine-{entity}.md   （State Machine Diagram，共 N 張，來自 EDD §4.5.6）
    ✓/✗ activity-{flow}.md          （Activity Diagram，共 N 張，來自 EDD §4.5.7 + PRD.md）
    ✓/✗ component.md                （Component Diagram，來自 EDD §4.5.8）
    ✓/✗ deployment.md               （Deployment Diagram，來自 EDD §4.5.9）
  
  Server 額外圖表：
    ✓/✗ er-diagram.md               （ER Diagram，資料庫關聯圖，來自 SCHEMA.md）
  
  關鍵輸出：
    ✓/✗ class-inventory.md          （Class → Test File 對應表，共 N 個 class）

  Frontend UML（Step 2B，條件執行：client_type != none + FRONTEND.md 存在）：
    ✓/✗/skip frontend-use-case.md          （前端用例圖）
    ✓/✗/skip frontend-class-component.md   （前端類別圖：UI 元件層）
    ✓/✗/skip frontend-class-scene.md       （前端類別圖：場景控制器層）
    ✓/✗/skip frontend-class-services.md    （前端類別圖：Client 服務層）
    ✓/✗/skip frontend-object-snapshot.md   （前端物件圖：UI 執行時快照）
    ✓/✗/skip frontend-sequence-ws.md       （前端循序圖：WS 協議）
    ✓/✗/skip frontend-sequence-scene.md    （前端循序圖：場景切換）
    ✓/✗/skip frontend-sequence-shoot.md    （前端循序圖：主要遊戲交互）
    ✓/✗/skip frontend-state-scene.md       （前端狀態機：場景）
    ✓/✗/skip frontend-state-ui.md          （前端狀態機：UI 元件）
    ✓/✗/skip frontend-activity-gameplay.md （前端活動圖：遊戲主流程）
    ✓/✗/skip frontend-activity-ui.md       （前端活動圖：UI 互動）
    ✓/✗/skip frontend-activity-init.md     （前端活動圖：客戶端初始化）
    ✓/✗/skip frontend-component.md         （前端元件圖：引擎節點樹）
    ✓/✗/skip frontend-deployment.md        （前端部署圖：建構管線）
    ✓/✗/skip frontend-communication.md     （前端協作圖：WS 協議互動）

  注意：
    - test-plan.md §15.2 RTM 應讀取 class-inventory.md 填充 Class 欄位
    - ER Diagram ≠ Class Diagram（前者為 DB 表格，後者為物件模型）
    - Sequence Diagram 每個主要業務流程各一張（共 N 張）
    - Frontend UML 的 stateDiagram-v2 禁止使用 <br/> 語法（已強制）

Server 圖合計：N 張 UML + 1 個 er-diagram.md + class-inventory.md
Frontend 圖合計：N 張（skip 時：0 張）
```

---

## 附錄：UML 九大圖對照表

| # | UML 圖類型 | EDD §章節（新版→舊版）| 輸出檔案 | Mermaid 語法 | 最低張數 |
|---|-----------|---------------------|---------|-------------|---------|
| 1 | Use Case Diagram | §10.1 → §4.5.1 | `use-case.md` | `flowchart TD` | 1 |
| 2 | Class Diagram | §10.2 → §4.5.2 | `class-domain.md`, `class-application.md`, `class-infra-presentation.md` | `classDiagram` | 3（固定）|
| 3 | Object Diagram | §10.3 → §4.5.3 | `object-snapshot.md` | `classDiagram`（instance 模式）| 1 |
| 4 | Sequence Diagram | §10.4 → §4.5.4 + API.md | `sequence-{flow}.md`（多張）| `sequenceDiagram` | **≥ 3** |
| 5 | Communication Diagram | §10.5 → §4.5.5 | `communication.md` | `flowchart LR` | 1 |
| 6 | State Machine Diagram | §10.6 → §4.5.6 | `state-machine-{entity}.md`（多張）| `stateDiagram-v2` | **≥ 1 per Entity** |
| 7 | Activity Diagram | §10.7 → §4.5.7 + PRD.md | `activity-{flow}.md`（多張）| `flowchart TD` | **≥ 3** |
| 8 | Component Diagram | §10.8 → §4.5.8 + ARCH.md | `component.md` | `graph TD` | 1 |
| 9 | Deployment Diagram | §10.9 → §4.5.9 + ARCH.md | `deployment.md` | `graph TD` | 1 |
| — | ER Diagram（額外）| SCHEMA.md | `er-diagram.md` | `erDiagram` | 1（可選）|
