# UML-CLASS.md — Class Diagram 文件結構骨架

<!-- 此骨架定義 /gendoc UML-CLASS 產出的完整文件結構 -->
<!-- 生成規則見 UML-CLASS.gen.md | Review 標準見 UML-CLASS.review.md -->

---

## 用途

本文件為 Class Diagram 專項生成的結構骨架。
`/gendoc UML-CLASS` 會依此骨架，在 `docs/diagrams/` 輸出以下 6 個（Server）或 9 個（含 Frontend）檔案。

---

## Server 端 Class Diagram（固定 3 張）

### 1. `docs/diagrams/class-domain.md`

```markdown
---
type: class-diagram
layer: domain
generated_by: gendoc UML-CLASS
---

# Class Diagram — Domain Layer

```classDiagram
    %% {{DOMAIN_CLASSES}}
```

## 技術說明

{{TECHNICAL_DESCRIPTION_DOMAIN}}

## 白話說明

{{PLAIN_LANGUAGE_DESCRIPTION_DOMAIN}}
```

---

### 2. `docs/diagrams/class-application.md`

```markdown
---
type: class-diagram
layer: application
generated_by: gendoc UML-CLASS
---

# Class Diagram — Application Layer

```classDiagram
    %% {{APPLICATION_CLASSES}}
```

## 技術說明

{{TECHNICAL_DESCRIPTION_APPLICATION}}

## 白話說明

{{PLAIN_LANGUAGE_DESCRIPTION_APPLICATION}}
```

---

### 3. `docs/diagrams/class-infra-presentation.md`

```markdown
---
type: class-diagram
layer: infrastructure-presentation
generated_by: gendoc UML-CLASS
---

# Class Diagram — Infrastructure + Presentation Layer

```classDiagram
    %% {{INFRA_PRESENTATION_CLASSES}}
```

## 技術說明

{{TECHNICAL_DESCRIPTION_INFRA}}

## 白話說明

{{PLAIN_LANGUAGE_DESCRIPTION_INFRA}}
```

---

### 4. `docs/diagrams/class-inventory.md`

1:1:N Class → Test Traceability 表格，由 gen 規則自動從上述 3 張圖提取。

| Class 名稱 | Stereotype | 架構層 | 推斷 src 路徑 | 推斷 test 路徑 |
|-----------|-----------|-------|-------------|--------------|
| {{CLASS}} | {{STEREO}} | {{LAYER}} | {{SRC}} | {{TEST}} |

---

## Frontend Class Diagram（條件執行：client_type != none）

### 5. `docs/diagrams/frontend-class-component.md`

UI 元件層 Class Diagram（引擎適配：Cocos Creator / Unity / React / Vue 等）。

### 6. `docs/diagrams/frontend-class-scene.md`

場景控制器層 Class Diagram。

### 7. `docs/diagrams/frontend-class-services.md`

Client 服務層 Class Diagram（WebSocket / HTTP / Store）。

---

## 所有 Class Diagram 共同品質標準

每張圖（含前端）必須滿足：

| 品質項目 | 標準 |
|---------|------|
| Class 數量 | ≥ 6 個（含 ≥ 1 個 `<<interface>>`） |
| 關聯線類型覆蓋 | 6 種各 ≥ 1 次（Inheritance / Realization / Composition / Aggregation / Association / Dependency） |
| 技術說明 | 每張圖末端必附，工程語言描述層職責 |
| 白話說明 | 每張圖末端必附，≤ 3 句，非技術人員可理解 |
| Stereotype | 所有 class 必須標注 |
| 屬性格式 | `visibility name: Type`（三者缺一不可） |
| 方法格式 | `visibility name(param: Type): ReturnType` |
| Cardinality | 所有關聯線兩端都要標 |
