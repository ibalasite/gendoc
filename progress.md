# gendoc Class Diagram 品質強化 + UML-CLASS 三件套 進度追蹤

**目標**：補足 Class Diagram 品質閘門、建立獨立呼叫路徑、清除 UML-CLASS-GUIDE.md 造成的誤導性引用。

---

## 符號說明

| 符號 | 意義 |
|------|------|
| `[ ]` | 待執行 |
| `[x]` | 已完成 + commit done |
| `[~]` | 進行中 |

---

## 背景調查結論（2026-05-03）

**UML-CLASS-GUIDE.md 現狀**：1111 行靜態參考指南，在 pipeline 生成流程中**完全不被讀取**。
`gendoc-gen-diagrams` 使用自己的 inline spec（§2.2-2.4）生成所有 class diagrams。

**5 處引用的真實性質**：

| 位置 | 表面用途 | 實際問題 |
|------|---------|---------|
| `docs/PRD.md:1130` | 描述為「Class Diagram 規範（不生成）」| 事實錯誤：class diagrams 確實由 gen-diagrams 生成 |
| `templates/EDD.review.md:76` | Fix hint「参考 UML-CLASS-GUIDE.md 範例」 | 誤導：缺漏應補跑 gendoc-gen-diagrams，不是手動參考指南 |
| `templates/EDD.review.md:86` | Fix hint「格式見 UML-CLASS-GUIDE.md §3」| 誤導：Class Inventory 由 gen-diagrams Step 3 自動生成 |
| `SKILL.md:98` | alias `uml-class → UML-CLASS-GUIDE` | 損壞：UML-CLASS-GUIDE 不是生成模板，/gendoc uml-class 無法正確運作 |
| `skills/reviewdoc/SKILL.md:69` | alias `uml-class → UML-CLASS-GUIDE` | 舊遺留：應改指向 UML-CLASS.review.md |

**根本原因**：UML-CLASS-GUIDE.md 建立於 gendoc-gen-diagrams 完整實作之前，是早期手動期的教學文件。
自動化生成成熟後，引用未隨之清理，形成「生成工具一套標準、參考文件另一套」的雙頭混亂。

---

## 一、確認修改（原有需求）

### TASK-C1：gendoc-gen-diagrams §2.9 補 3 個品質閘門

**目標**：在現有 §2.9「Class Diagram 實作完整度」末端追加 3 條強制驗收項目。

**驗收標準**：
- `[ ]` 全部 6 種關聯類型各出現 ≥ 1 次（Inheritance/Realization/Composition/Aggregation/Association/Dependency）
- `[ ]` 每張 class diagram ≥ 6 個 class（含 ≥ 1 `<<interface>>`）
- `[ ]` 每張圖末端附「技術說明」（一段工程語言說明層職責）＋「白話說明」（一段任何人都看得懂的業務意義）

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 修改 `skills/gendoc-gen-diagrams/SKILL.md` §2.9 末端 |
| `[ ]` | 確認三條驗收項與已有 checklist 格式一致 |

---

### TASK-C2：建立 UML-CLASS 三件套（standalone /gendoc UML-CLASS）

**目標**：在 `templates/` 建立三個新檔，讓 `/gendoc UML-CLASS` 可單獨呼叫，**不加入 pipeline.json**。

| 新增檔案 | 職責 |
|---------|------|
| `templates/UML-CLASS.md` | Class Diagram 文件結構骨架（6 張圖的版型） |
| `templates/UML-CLASS.gen.md` | 生成規則：inline copy §2.2-2.4 + §2B-2~2B-4 + 3 品質閘門 |
| `templates/UML-CLASS.review.md` | Review 標準：含 6 種關聯類型 + ≥6 class + 技術/白話說明驗收 |

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 建立 `templates/UML-CLASS.md` |
| `[ ]` | 建立 `templates/UML-CLASS.gen.md`（從 SKILL.md §2.2-2.4, §2B-2~2B-4 inline copy） |
| `[ ]` | 建立 `templates/UML-CLASS.review.md` |

---

### TASK-C3：修正 PRD.md 錯誤描述

**目標**：修正 `docs/PRD.md:1130` 「Class Diagram 規範（不生成）」的事實錯誤。

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | 刪除 UML-CLASS-GUIDE.md 該行，改寫為 UML-CLASS.gen.md 的正確說明 |

---

## 二、新增需求（本次調查後追加）

### TASK-C4：修正 EDD.review.md 誤導性 Fix hint

**問題**：兩處 Fix hint 告訴 reviewer「參考 UML-CLASS-GUIDE.md」，但正確做法是「補跑 gendoc-gen-diagrams」。

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | `EDD.review.md:76` Fix hint：改為「執行 `/gendoc uml` 補生成，或人工補 §4.5 對應 Mermaid 程式碼塊」 |
| `[ ]` | `EDD.review.md:86` Fix hint：改為「執行 `/gendoc uml` 重新生成 class-inventory，或人工補 Class Inventory 表格（欄位：class 名稱 / stereotype / 架構層 / src 路徑 / test 路徑）」 |

---

### TASK-C5：修正 SKILL.md alias 路由

**問題**：`uml-class → UML-CLASS-GUIDE` 在兩處出現，路由到不存在的生成模板，需改指到正確目標。

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | `SKILL.md:98`：`uml-class → UML-CLASS-GUIDE` 改為 `uml-class → UML-CLASS.gen` |
| `[ ]` | `skills/reviewdoc/SKILL.md:69`：`uml-class → UML-CLASS-GUIDE` 改為 `uml-class → UML-CLASS.review` |

---

### TASK-C6：刪除 UML-CLASS-GUIDE.md

**依據**：pipeline 無依賴，所有引用均已在 C3/C4/C5 修正，保留只會繼續造成混亂。

| 狀態 | 子任務 |
|------|-------|
| `[ ]` | `git rm templates/UML-CLASS-GUIDE.md` |

---

## 執行順序

```
C1 → C2 → C3 → C4 → C5 → C6
（C6 必須在 C4/C5 所有引用清完後才執行）
```
