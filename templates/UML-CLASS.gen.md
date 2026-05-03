# UML-CLASS.gen.md — Class Diagram 生成規則

<!-- 此為 /gendoc UML-CLASS 的獨立生成規則 -->
<!-- 內容 inline copy 自 gendoc-gen-diagrams/SKILL.md §2.2-2.4 + §2B-2~2B-4 -->
<!-- 品質閘門版本：含 3 個額外強制項（Class 數量 / 6 種關聯 / 技術說明 + 白話說明） -->
<!-- 文件結構骨架見 UML-CLASS.md | Review 標準見 UML-CLASS.review.md -->

---

## 適用場景

- **獨立呼叫**：`/gendoc UML-CLASS` → 只生成 Class Diagrams，不生成其他 8 種 UML 圖
- **補跑**：已跑 `/gendoc uml`（gendoc-gen-diagrams）但 Class Diagram 品質不足時，可單獨補強
- **不加入 pipeline.json**：Class Diagrams 在 pipeline 中由 `gendoc-gen-diagrams`（D07b-UML）負責；此三件套僅供獨立呼叫

---

## Step 0：讀取上游文件

**必讀**（按優先順序）：
1. `EDD.md` — §10.2（新版）或 §4.5.2（舊版）提取已有 classDiagram 程式碼
2. `ARCH.md` — §3 Domain 模型（確認 class 名稱一致性）
3. `SCHEMA.md` — Table 名稱（確認 entity class 名稱一致性）
4. `PRD.md` — §User Stories / Acceptance Criteria（確認 Use Case class 對應）
5. `FRONTEND.md`（若存在）— §元件架構 / §場景系統 / §網路層

**條件讀取**：
- `VDD.md`（若存在）— 前端元件清單、場景流程
- `.gendoc-state.json` — `client_type`（決定是否生成前端 Class Diagrams）

---

## Step 1：生成 class-domain.md（Domain Layer）

**輸出路徑**：`docs/diagrams/class-domain.md`

**UML 類型**：Mermaid `classDiagram`

**來源**：EDD §10.2（新版）/ §4.5.2（舊版）

**屬性格式**（三者缺一不可）：`visibility attributeName : Type`
- visibility：`+`（public）`-`（private）`#`（protected）`~`（package）
- 型別精確：`String`、`UUID`、`Integer`、`Decimal`、`Boolean`、`DateTime`，Enum 引用 enum class 名稱
- **禁止**：無 visibility、無型別、`any`、`Object` 等模糊型別

**方法格式**（四者缺一不可）：`visibility methodName(param1: Type, param2: Type) ReturnType`
- 每個參數有名稱和型別
- 回傳型別精確：`void`、`String`、`Order`、`List~Order~`、`Optional~User~`
- **禁止**：無參數型別、無回傳型別、空方法列表、`create()` 無參數

**Enum 格式**（每個 Enum 必須獨立定義，所有值列全）：
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
**禁止**「...」省略。

**關聯線格式**：`ClassA "cardinality" relationSymbol "cardinality" ClassB : roleLabel`
- 繼承：`ParentClass <|-- ChildClass`
- 介面實作：`InterfaceA <|.. ClassB`
- 組合：`ClassA *-- "1..*" ClassB : contains`
- 聚合：`ClassA o-- "0..*" ClassB : has`
- 關聯：`ClassA "1" --> "0..*" ClassB : roleLabel`
- 依賴：`ClassA ..> ClassB : uses`
- **禁止**：無 cardinality 的關聯線、無 role label 的模糊關聯

**Domain Layer 必含 stereotype（缺一不可）**：
- `<<AggregateRoot>>`（≥ 1）：含所有業務屬性和 Invariant 方法
- `<<Entity>>`（≥ 2）：所有業務 Entity
- `<<ValueObject>>`：所有值物件（Money、Address 等）
- `<<DomainEvent>>`：所有領域事件（對應 EDD §4.6 每行）
- `<<Repository>>`（interface，≥ 1）：抽象 Repository，含所有查詢方法簽名

**品質閘門（本圖必須滿足）**：
- [ ] ≥ 6 個 class（含 ≥ 1 `<<interface>>`，通常為 `<<Repository>>`）
- [ ] 6 種關聯類型各出現 ≥ 1 次
- [ ] 圖末附「技術說明」段落（描述 Domain Layer 職責邊界、Aggregate 設計決策）
- [ ] 圖末附「白話說明」段落（≤ 3 句，說明這層管理哪些業務實體及其規則）

---

## Step 2：生成 class-application.md（Application Layer）

**輸出路徑**：`docs/diagrams/class-application.md`

**UML 類型**：Mermaid `classDiagram`

**來源**：EDD §10.2（新版）/ §4.5.2（舊版）

屬性/方法/關聯線格式標準同 Step 1（完全相同）。

**Application Layer 必含 stereotype（缺一不可）**：
- `<<UseCase>>`（每個 PRD AC 對應一個，含 `+ execute(command: CommandDTO): ResponseDTO`）
- `<<ApplicationService>>`（跨 UseCase 的編排邏輯）
- `<<DTO>>`（Command DTO、Query DTO，含所有欄位和型別）
- `<<Port>>`（定義外部服務介面，如 `IEmailPort`、`IPaymentPort`）

**品質閘門（本圖必須滿足）**：
- [ ] ≥ 6 個 class（含 ≥ 1 `<<Port>>` interface）
- [ ] 6 種關聯類型各出現 ≥ 1 次
- [ ] 圖末附「技術說明」段落（描述 Application Layer 的 UseCase 編排邏輯與 Port 定義）
- [ ] 圖末附「白話說明」段落（≤ 3 句，說明這層把哪些業務流程從輸入到輸出協調起來）

---

## Step 3：生成 class-infra-presentation.md（Infrastructure + Presentation Layer）

**輸出路徑**：`docs/diagrams/class-infra-presentation.md`

**UML 類型**：Mermaid `classDiagram`

**來源**：EDD §10.2（新版）/ §4.5.2（舊版）

屬性/方法/關聯線格式標準同 Step 1（完全相同）。

**Infrastructure + Presentation Layer 必含 stereotype（缺一不可）**：
- `<<RepositoryImpl>>`（實作 Domain 層 `<<Repository>>` interface）
- `<<Adapter>>`（實作 Application 層 `<<Port>>` interface，對接外部服務）
- `<<Controller>>`（含所有 HTTP handler 方法：`+ createOrder(req: CreateOrderRequestDTO): Promise~ResponseDTO~`）
- `<<RequestDTO>>`（含 validation decorator 說明）
- `<<ResponseDTO>>`（含所有 API 回傳欄位）

**若 EDD 未按層次分張**：從整體 Class Diagram 依架構層次拆分成 3 張。

**品質閘門（本圖必須滿足）**：
- [ ] ≥ 6 個 class（含 ≥ 1 `<<RepositoryImpl>>` 實作 interface）
- [ ] 6 種關聯類型各出現 ≥ 1 次
- [ ] 圖末附「技術說明」段落（描述 Infra 層的 Repository 實作、外部服務 Adapter 和 Controller 的職責）
- [ ] 圖末附「白話說明」段落（≤ 3 句，說明這層如何把抽象接口與真實資料庫/外部系統連接起來）

---

## Step 4：生成 class-inventory.md（Class Inventory 表格）

**輸出路徑**：`docs/diagrams/class-inventory.md`

從 Steps 1-3 生成的 3 張 Server Class Diagrams 提取所有 class，填入 1:1:N 追蹤表格：

| Class 名稱 | Stereotype | 架構層 | 推斷 src 路徑 | 推斷 test 路徑 |
|-----------|-----------|-------|-------------|--------------|

- `src 路徑`：依架構層次推斷（Domain class → `src/domain/`，Controller → `src/presentation/`）
- `test 路徑`：`src` 路徑的 test 對應（`src/domain/Order.ts` → `tests/domain/Order.test.ts`）
- 所有在 classDiagram 程式碼塊中出現的 class 都必須在表中列出

---

## Step 5（條件執行）：生成前端 Class Diagrams

**執行條件**：`client_type != none` AND `client_type != api-only` AND `FRONTEND.md` 存在

若條件不符，跳過 Step 5，直接進入 Step 6（品質驗收）。

---

### Step 5A：frontend-class-component.md（UI 元件層）

**輸出路徑**：`docs/diagrams/frontend-class-component.md`

**來源**：FRONTEND.md §元件架構 + VDD.md §元件清單

**強制完整度標準**：
- 依引擎架構分層（Cocos Creator 用 Node/Component；Unity 用 GameObject/MonoBehaviour；React 用 Component/Hook）
- 每個 Component class 必須包含：
  - 引擎基類繼承（`Component extends cc.Component` 或 `extends MonoBehaviour`）
  - 公開屬性（`@property` 或 `[SerializeField]`，標注型別）
  - 生命週期方法（`onLoad/start/update` 或 `Awake/Start/Update`）
  - 業務方法（對應 FRONTEND.md 中該元件的職責）
- 元件間關聯：組合 / 依賴 / 事件訂閱（標注 EventTarget 或 Signal）
- **禁止**：無引擎基類、無屬性型別、無生命週期方法

**品質閘門**：
- [ ] ≥ 8 個 class（FRONTEND.md 所有主要 UI 元件）
- [ ] 6 種關聯類型各出現 ≥ 1 次
- [ ] 圖末附「技術說明」＋「白話說明」

---

### Step 5B：frontend-class-scene.md（場景控制器層）

**輸出路徑**：`docs/diagrams/frontend-class-scene.md`

**來源**：FRONTEND.md §場景系統 + VDD.md §場景流程

**強制完整度標準**：
- 每個 Scene/Screen class 包含：場景名稱、加載參數、場景切換方法
- 場景管理器（SceneManager / NavigationService）必須存在
- 場景資料傳遞機制（GlobalData / EventBus / Store）明確標注
- **禁止**：場景間無連線、無資料傳遞說明

**品質閘門**：
- [ ] ≥ 3 個 Scene class + 1 個 SceneManager
- [ ] 6 種關聯類型各出現 ≥ 1 次（若 scene 數量不足，與其他 class 共用圖）
- [ ] 圖末附「技術說明」＋「白話說明」

---

### Step 5C：frontend-class-services.md（Client 服務層）

**輸出路徑**：`docs/diagrams/frontend-class-services.md`

**來源**：FRONTEND.md §網路層 + API.md（WS/REST 協議）

**強制完整度標準**：
- WebSocket 服務類：`connect/disconnect/reconnect` + 訊息收發方法（帶型別）+ 事件回調
- HTTP/REST 服務類（若有）：每個 API endpoint 對應一個方法（方法名、參數型別、回傳型別）
- Store/State 管理：`GameStore`、`UserStore` 等，含 State 型別定義
- 資料模型 class（DTO）：對應 API.md 請求/回應格式，每個欄位有型別
- **禁止**：無型別的 `any`、無方法的空 class

**品質閘門**：
- [ ] ≥ 5 個 class（FRONTEND.md 所有網路層元件）
- [ ] 6 種關聯類型各出現 ≥ 1 次
- [ ] 圖末附「技術說明」＋「白話說明」

---

## Step 6：品質驗收（所有圖生成完畢後執行）

```
╔══════════════════════════════════════════════════════════════╗
║  Class Diagram 品質驗收（每張圖逐一確認）                     ║
╠══════════════════════════════════════════════════════════════╣
║  [1] class-domain.md         ≥6 class / 6 種關聯 / 說明      ║
║  [2] class-application.md    ≥6 class / 6 種關聯 / 說明      ║
║  [3] class-infra-presentation ≥6 class / 6 種關聯 / 說明     ║
║  [4] class-inventory.md      所有 class 列入追蹤表            ║
║  [5] frontend-class-component.md（若有）                     ║
║  [6] frontend-class-scene.md（若有）                         ║
║  [7] frontend-class-services.md（若有）                      ║
╚══════════════════════════════════════════════════════════════╝
```

**驗收項目（每張圖）**：
- [ ] 所有 class 有 stereotype（無裸 class）
- [ ] 所有屬性格式為 `visibility name: Type`
- [ ] 所有方法格式為 `visibility name(param: Type): ReturnType`
- [ ] 所有 Enum 獨立定義並列出全部枚舉值
- [ ] 所有關聯線有 cardinality（兩端）+ role label
- [ ] **≥ 6 個 class（含 ≥ 1 `<<interface>>`）**
- [ ] **6 種關聯類型各出現 ≥ 1 次**（Inheritance / Realization / Composition / Aggregation / Association / Dependency）
- [ ] **圖末附「技術說明」段落**（工程語言）
- [ ] **圖末附「白話說明」段落**（≤ 3 句）

**任一項目不通過，立即修正後再次驗收。**
