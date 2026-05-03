# UML-CLASS.review.md — Class Diagram Review 標準

<!-- 此為 /gendoc-review UML-CLASS 的審查規則 -->
<!-- 生成規則見 UML-CLASS.gen.md | 文件結構骨架見 UML-CLASS.md -->

---

## 審查範圍

審查 `docs/diagrams/` 下所有 Class Diagram 文件：
- `class-domain.md`
- `class-application.md`
- `class-infra-presentation.md`
- `class-inventory.md`
- `frontend-class-component.md`（若 client_type != none）
- `frontend-class-scene.md`（若有）
- `frontend-class-services.md`（若有）

---

## Layer 0：文件存在性

#### [CRITICAL] 0a — Server Class Diagrams 缺失

**Check**：`docs/diagrams/` 是否存在 `class-domain.md`、`class-application.md`、`class-infra-presentation.md` 全部三張？

**Risk**：無 Class Diagram，工程師只能讀文字推斷 class 結構，實作偏差機率極高，unit test skeleton 無從自動推導。

**Fix**：執行 `/gendoc uml` 或 `/gendoc UML-CLASS` 補生成。

#### [CRITICAL] 0b — Class Inventory 缺失

**Check**：`docs/diagrams/class-inventory.md` 是否存在？

**Risk**：無 Class Inventory，test-plan 撰寫者必須人工掃描 classDiagram 程式碼塊，容易遺漏 class，導致部分 class 完全沒有 unit test 覆蓋。

**Fix**：執行 `/gendoc uml` 或 `/gendoc UML-CLASS` 補生成；class-inventory.md 由生成工具自動從三張 Server Class Diagrams 提取。

---

## Layer 1：class 數量與 interface 覆蓋

#### [CRITICAL] 1a — Class 數量不足

**Check**：每張 Class Diagram 是否含 ≥ 6 個 class？其中是否含 ≥ 1 個 `<<interface>>`？

**驗證方式**：數 classDiagram 程式碼塊中 `class ` 宣告的行數。

**Risk**：class 數量不足代表設計過於粗略，工程師無法依此生成有意義的 unit test skeleton。

**Fix**：補充缺失的 class；若設計確實只有 5 個 class，需解釋合理性（如：極簡 CRUD 服務）並標注「設計說明：本層職責單一，class 數目合理」。

---

## Layer 2：6 種關聯類型覆蓋

#### [CRITICAL] 2a — 關聯類型不全

**Check**：每張 Class Diagram 是否包含全部 6 種關聯類型，各出現 ≥ 1 次？

| 關聯類型 | Mermaid 語法 | 說明 |
|---------|-------------|------|
| Inheritance（繼承） | `ParentClass <\|-- ChildClass` | 子類繼承父類 |
| Realization（介面實作） | `InterfaceA <\|.. ClassB` | Class 實作 interface |
| Composition（組合） | `ClassA *-- ClassB` | A 擁有 B，生命週期相依 |
| Aggregation（聚合） | `ClassA o-- ClassB` | A 有 B，生命週期獨立 |
| Association（關聯） | `ClassA --> ClassB` | A 使用/參照 B |
| Dependency（依賴） | `ClassA ..> ClassB` | A 暫時依賴 B |

**驗證方式**：逐一搜尋圖中是否出現 `<|--`、`<|..`、`*--`、`o--`、`-->`、`..>`。

**Risk**：關聯類型不全代表物件關係表達不完整，工程師無法推斷正確的 ownership、lifecycle 和 dependency injection 設計。

**Fix**：補充缺失的關聯類型；若特定層次確實不需某種關聯，需說明理由，並可從其他圖借用不同層次的關聯來完整覆蓋（需標注）。

---

## Layer 3：格式完整度

#### [CRITICAL] 3a — Stereotype 缺失

**Check**：是否所有 class 都有 stereotype 標注？（`<<AggregateRoot>>`、`<<Entity>>`、`<<Repository>>`、`<<UseCase>>`、`<<Controller>>` 等）

**Risk**：無 stereotype 的「裸 class」無法讓工程師判斷 class 在架構中的角色，導致錯誤的繼承或依賴關係設計。

**Fix**：為所有裸 class 補充適當的 stereotype（依架構層次和 Clean Architecture 角色判斷）。

#### [CRITICAL] 3b — 屬性格式不符

**Check**：是否所有屬性格式為 `visibility attributeName : Type`？是否有缺 visibility、缺型別或使用 `any`/`Object` 的情況？

**Fix**：補充缺失的 visibility（預設 `+`）和型別；將 `any`/`Object` 替換為精確業務型別。

#### [HIGH] 3c — 方法格式不符

**Check**：是否所有方法格式為 `visibility methodName(param: Type): ReturnType`？是否有缺回傳型別或無參數型別的情況？

**Fix**：補充缺失的回傳型別和參數型別；若方法確實無參數，保留空括號 `()`；若回傳 void，明確標注。

#### [HIGH] 3d — Enum 省略枚舉值

**Check**：是否所有 `<<enumeration>>` class 都列出了全部枚舉值？是否有使用「...」省略的情況？

**Fix**：從 PRD Acceptance Criteria 或 SCHEMA.md 補充全部枚舉值。

#### [HIGH] 3e — 關聯線缺 Cardinality 或 Role Label

**Check**：是否所有關聯線（`-->`、`*--`、`o--`）兩端都標注了 cardinality（`"1"`、`"0..1"`、`"1..*"`、`"0..*"`）和 role label？

**Fix**：補充兩端 cardinality 和語意清晰的 role label。

---

## Layer 4：技術說明與白話說明

#### [CRITICAL] 4a — 缺技術說明

**Check**：每張 Class Diagram 檔案末端是否有「技術說明」段落（`## 技術說明` 或等效標題）？

**Risk**：無技術說明，後續 AI session 或工程師必須從 classDiagram 程式碼塊重新推斷設計意圖，容易誤解關鍵設計決策。

**Fix**：在每張圖末端補充「技術說明」段落，說明該層的職責邊界、主要設計模式選擇（如：Repository Pattern、Factory、策略模式）和與其他層的依賴方向。

#### [CRITICAL] 4b — 缺白話說明

**Check**：每張 Class Diagram 檔案末端是否有「白話說明」段落（`## 白話說明` 或等效標題）？說明是否 ≤ 3 句且非技術人員可理解？

**Risk**：無白話說明，非技術 stakeholder（PM、QA、業務分析師）無法理解 Class Diagram 的業務意義，跨職能溝通成本高。

**Fix**：補充「白話說明」段落，用日常語言描述「這層負責管理哪些業務實體」和「它解決了什麼業務問題」，≤ 3 句。

---

## Layer 5：一致性驗證

#### [HIGH] 5a — Class 名稱與上游不一致

**Check**：Server Class Diagram 的 class 名稱是否與以下來源完全一致？
- ARCH.md §3 Domain 模型中的 Entity 名稱
- SCHEMA.md 的 Table 名稱（Domain Entity 對應 Table 的部分）

**Fix**：對齊所有不一致的名稱；若刻意使用不同名稱（如 ORM 映射），需在技術說明中標注。

#### [HIGH] 5b — DomainEvent 未在 EDD §4.6 對應

**Check**：Domain Layer Class Diagram 中每個 `<<DomainEvent>>` class 是否在 EDD §4.6 Domain Events 表中有對應行？

**Fix**：補充 EDD §4.6 缺失的 DomainEvent 定義，或從 Class Diagram 移除未定義的 DomainEvent class。

#### [MEDIUM] 5c — class-inventory 覆蓋不完整

**Check**：`class-inventory.md` 是否覆蓋了三張 Server Class Diagrams 中所有出現的 class？逐一核對。

**Fix**：補充 class-inventory.md 中缺失的 class 行。

---

## Review 通過標準

| 嚴重性 | 標準 |
|-------|------|
| CRITICAL | 全部通過（≥1 CRITICAL = 未通過） |
| HIGH | 全部通過（≥1 HIGH = 條件通過，需記錄） |
| MEDIUM | 提供修復建議，不阻斷通過 |

**最終結論**：
- `PASS`：無 CRITICAL，無 HIGH
- `PASS-WITH-WARNINGS`：無 CRITICAL，有 HIGH（需記錄並排期修復）
- `FAIL`：有任何 CRITICAL
