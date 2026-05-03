# gendoc Class Diagram 品質強化 + UML-CLASS 三件套 進度追蹤

**目標**：補足 Class Diagram 品質閘門、建立獨立呼叫路徑、清除 UML-CLASS-GUIDE.md 造成的誤導性引用。

**狀態**：全部完成 ✅ | 已 push 至 origin/main

---

## 背景調查結論（2026-05-03）

`UML-CLASS-GUIDE.md`（1111 行）是早期手動期遺留的靜態教學文件，pipeline 完全不讀取它。
`gendoc-gen-diagrams` 使用自己的 inline spec（§2.2-2.4）生成所有 class diagrams，5 處引用全為誤導性遺留，已全部清除。

---

## TASK-C1：gendoc-gen-diagrams §2.9 補 3 個品質閘門 ✅

**驗收標準（已確認存在於 SKILL.md:725-727）**：
- 每張 class diagram ≥ 6 個 class（含 ≥ 1 `<<interface>>`）
- 全部 6 種關聯類型各出現 ≥ 1 次
- 每張圖末端附「技術說明」＋「白話說明」

| 狀態 | 子任務 |
|------|-------|
| `[x]` | 修改 `skills/gendoc-gen-diagrams/SKILL.md` §2.9 末端 |
| `[x]` | 三條驗收項格式與已有 checklist 一致，已驗證 |

---

## TASK-C2：建立 UML-CLASS 三件套 ✅

實驗性小工具，不加入 pipeline，不在生產文件中提及。

| 檔案 | 行數 | 狀態 |
|------|------|------|
| `templates/UML-CLASS.md` | 134 行 | `[x]` |
| `templates/UML-CLASS.gen.md` | 253 行 | `[x]` |
| `templates/UML-CLASS.review.md` | 169 行 | `[x]` |

---

## TASK-C3：修正 PRD.md ✅

| 狀態 | 子任務 |
|------|-------|
| `[x]` | `docs/PRD.md:1130`：移除「Class Diagram 規範（不生成）」，改為正確描述 gendoc-gen-diagrams 的 4 個輸出檔案，不提 UML-CLASS 工具 |

---

## TASK-C4：修正 EDD.review.md 誤導性 Fix hint ✅

| 狀態 | 子任務 |
|------|-------|
| `[x]` | `EDD.review.md:76`：移除舊 UML-CLASS-GUIDE 引用，改為「補跑 `gendoc-gen-diagrams` skill」 |
| `[x]` | `EDD.review.md:86`：同上，移除 gendoc-repair 引用，只保留 gendoc-gen-diagrams |

---

## TASK-C5：修正 alias 路由 ✅

| 狀態 | 子任務 | 最終狀態 |
|------|-------|---------|
| `[x]` | `SKILL.md:98` | `uml-class → UML-CLASS`（正確路由到三件套） |
| `[x]` | `skills/reviewdoc/SKILL.md:69` | alias 已移除（實驗工具不進生產 skill） |

---

## TASK-C6：刪除 UML-CLASS-GUIDE.md ✅

| 狀態 | 子任務 |
|------|-------|
| `[x]` | `git rm templates/UML-CLASS-GUIDE.md`，pipeline 無依賴，已確認 |

---

## 設計原則（已寫入 CLAUDE.md）

1. `gendoc-gen-diagrams` 是唯一 UML 生成來源
2. 其他文件的 inline 圖是各文件自己的內容，與 pipeline 輸出是兩件事
3. `/gendoc UML-CLASS` 是實驗性小工具，完全隔離，不進生產流程
