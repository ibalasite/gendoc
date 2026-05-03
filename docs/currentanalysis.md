# gendoc 專案現況分析 — 專家評估報告

<!-- 評估日期：2026-05-03 | 評估人：Claude Sonnet 4.6 -->

---

## 核心問題：「讓 AI 或工程師按規格書直接建置系統」—— 這個目標合理嗎？

### 結論

**目標合理，而且是正確的方向。但有三個結構性風險值得正視。**

---

## 合理的部分（做對的事）

### 1. 文件分層設計是對的

BRD / PRD / PDD / EDD 分層，對應 Why / What / How it works / How to build，與 IEEE 29148、Wiegers 的實踐完全一致。跨職能團隊最大的溝通成本來自「不同角色看同一份文件卻期待不同的東西」，分層從根本上解決了這個問題。

### 2. 以「可實作」而非「可閱讀」為品質標準

市面上 99% 的文件工具產出的是說明書，gendoc 要求 EDD 到 class/method 層級、API 到欄位 validation、Schema 到 DDL、test-plan 到具體邊界值。這個標準讓文件真的能驅動實作，而不只是「參考資料」。

| 普通技術文件 | gendoc 開發藍圖 |
|------------|---------------|
| 描述功能意圖 | 定義到 class、method 簽名、參數型別 |
| 說明 API 端點 | 包含每個欄位的型別、驗證規則、錯誤回應範例 |
| 提及需要測試 | 列出具體測試情境、邊界值、等價類劃分 |
| 描述資料結構 | 給出 Schema DDL、index 策略、constraint 定義 |
| 說明架構組件 | 包含 sequence diagram、component 間呼叫合約 |

### 3. Cumulative Upstream Reading 是結構性創新

每份文件讀所有上游文件，從機制上保證了知識繼承。大多數文件系統（包括人工撰寫）最大的問題是「下游文件的前提假設和上游不一致」。cumulative upstream reading 防止了這個問題。

### 4. AI-native 雙受眾設計是時代正確的押注

> 如果文件細到 AI 能直接實作，人類一定也能。但反過來不成立。

MetaGPT（ICLR 2024）和 ChatDev（ACL 2024）都驗證了：給 AI 模糊輸入，就得到模糊輸出；給精確的分層文件，品質才會收斂。gendoc 在這個方向上走在業界前面。

---

## 三個結構性風險

### 風險一：文件品質 ≠ 實作品質（The Last Mile Problem）

gendoc 產出的是**規格書**，但規格書到「系統可以跑起來」之間還有一個 Last Mile：

- Schema DDL 寫了，但 migration 順序、rollback 策略、seed data 的邊界條件是否覆蓋？
- API 合約定義了，但 concurrent request 時的 race condition 規格書是否定義到？
- EDD 的 class 設計合理，但 dependency injection container 的 lifecycle 誰決定？

**改善方向**：CONTRACTS + MOCK 已經在往這個方向走（OpenAPI → 可測試合約）。下一步是讓 DRYRUN 的量化基線更精準，以及把可驗證的測試 spec 自動綁定到規格書條目，讓「規格書有無漏洞」可以被 CI/CD 自動驗收。

### 風險二：規格收斂假設（「文件寫完就是正確的」）

目前設計假設：只要每份文件的 review loop finding = 0，文件就是正確的。但「語法正確」≠「語義正確」——EDD 可以完全符合模板要求，但 class 設計可能選錯了架構模式（例如在需要 event-driven 的場景硬用 request-response）。

**改善方向**：ALIGN check 已在做跨文件一致性，但還缺一個「設計合理性」層面的 review——例如 EDD 的架構選擇是否符合 PRD 的非功能需求（latency / throughput / consistency）。這是比語法更難自動化的問題，可能需要引入架構 ADR（Architecture Decision Record）驗證機制。

### 風險三：Context Window 與知識遞減（The Knowledge Decay Problem）

每份文件讀所有上游文件，在前幾份時沒問題。但到 DRYRUN 后的 step 尾端（SCHEMA → FRONTEND → test-plan），上游已累積 IDEA + BRD + PRD + CONSTANTS + PDD + VDD + EDD + ARCH + API，context 可能超過 100k tokens。AI 在深層 context 的注意力是否均勻分配值得懷疑——早期文件（BRD 的商業需求）可能被稀釋。

**改善方向**：Phase D-2 Agent subagent 包裝隔離 context 是正確的方向。下一步可以讓每份文件的 gen 規則明確指定「必須讀哪幾份上游的哪些章節」，而不是「讀所有上游的全文」——精確的知識索引比全量 context 更可靠。

---

## 整體評分

| 維度 | 評分 | 說明 |
|------|------|------|
| 設計理念 | ★★★★★ | 分層、精確、可傳遞——理論上最先進的方向 |
| 工程執行 | ★★★★☆ | Pipeline 完整、有 review loop、有 DRYRUN gate |
| AI 可用性 | ★★★★☆ | MetaGPT / ChatDev 都在做類似的事，gendoc 走在前面 |
| 最後一哩 | ★★★☆☆ | 規格書到「可跑」還有 gap，CONTRACTS + MOCK 是在填 |
| 知識收斂 | ★★★☆☆ | Context 遞減問題在長 pipeline 裡真實存在 |

---

## 下一個里程碑建議

讓 gendoc 產出的規格書**可被 CI/CD 自動驗收**：

1. **合約測試自動化** — OpenAPI spec → Pact consumer-driven contract test，每次 push 自動跑
2. **Schema 遷移可驗證** — DDL diff → migration script → 自動回滾測試
3. **知識索引精確化** — 每份文件 gen 規則改為「讀上游的指定章節」而非全文
4. **ADR 驗證機制** — 架構決策記錄（Architecture Decision Record）綁定到 EDD，review 時驗證決策前提是否仍成立

當這四項完成，「按規格書建置系統」才會真正閉環——不只是人工確認，而是機器可驗收。

---

*評估基準：ISO/IEC/IEEE 29148:2018、MetaGPT (ICLR 2024)、ChatDev (ACL 2024)、Wiegers & Beatty Software Requirements 3rd ed.*
