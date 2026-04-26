---
doc-type: CONSTANTS
output-path: docs/CONSTANTS.md
upstream-docs:
  - docs/PRD.md       # 主要數值來源（唯一真相來源）
  - docs/BRD.md       # 業務指標補充（SLO 依據）
  - docs/req/         # 原始需求素材（若有量化數據）
quality-bar: "§1-§8 所有章節均有實際數值（無 placeholder）；每個數值均有 PRD §來源標注；constants.json 同步生成且與 .md 一致；全文無任何 {{...}} 佔位符；數值與 PRD 對照無誤差。"
---

# CONSTANTS 生成規則

## Iron Law

> **Iron Law**：生成 CONSTANTS.md 之前，必須先讀取 `templates/CONSTANTS.md`（結構骨架）和本文件（生成規則）。
> 本文件的唯一目的是：**從 PRD 提取所有量化數值，作為全域唯一真相來源**。
> 生成完成後必須同步輸出 `docs/constants.json`。

---

## 專家角色定義

**PRD 解讀師（PRD Analyst）**：
- 深度閱讀 PRD，識別所有量化數值（倍率、閾值、SLO、RTP、rate-limit、容量數字等）
- 區分「需求數值」（必須執行）和「指導性敘述」（不含具體數字）
- 對模糊描述（如「高可用性」）向上追溯 BRD 找量化依據，若無則標記 `TBD`

**數值一致性稽核員（Consistency Auditor）**：
- 確保同一業務概念在 PRD 不同章節的數值一致
- 發現衝突時標記 `[CONFLICT: PRD §X vs §Y]`，提取較保守的數值作為常數
- 驗證 constants.json 輸出與 CONSTANTS.md 內容完全一致

---

## 必讀上游文件

| 文件 | 讀取重點 | 對應輸出章節 |
|------|---------|------------|
| `docs/PRD.md` | 全文掃描所有量化數值 | §1-§8 全部章節 |
| `docs/BRD.md` | §成功指標 / §業務目標 | §4 SLO/SLI |
| `docs/req/*`  | 原始規格數據（若有） | 補充 §1-§3 |

---

## 生成步驟

### Step 1：全文掃描 PRD 量化數值

讀取 `docs/PRD.md`，執行以下掃描：

```
掃描目標（依類型分類）：
① 百分比數值 → §5 RTP / §4 SLO（可用性、錯誤率）
② 倍率（Nx、×N）→ §2 倍率與賠率
③ 毫秒/秒數值 → §4 SLO（延遲）
④ 次/秒/分鐘的限制 → §6 Rate Limit
⑤ 人數/並發量/TPS → §8 容量規劃
⑥ 條件閾值（超過 N 觸發...）→ §3 觸發條件
⑦ 天/月/年的期限 → §8 資料保留
⑧ 其他業務特有數值 → §7 業務規則數值
```

### Step 2：填寫 §1 遊戲/產品核心數值

- 提取 PRD 中定義產品核心玩法/功能的量化參數
- 每個數值必須標注 PRD §來源
- 若 PRD 無具體數值，寫 `TBD（PRD §X 未定義）`
- **禁止自行推斷或假設數值**

### Step 3：填寫 §2 倍率與賠率

- 掃描 PRD 中所有「×N」「N 倍」「N 連乘」的描述
- 列出每個倍率的觸發條件和數值
- 若為遊戲外的系統，標記此章節 `N/A`

### Step 4：填寫 §3 閾值與觸發條件

- 掃描 PRD 中所有「超過 N 時」「累積 N 個」「達到 N 後」的描述
- 每條觸發條件必須說明觸發後的行為

### Step 5：填寫 §4 SLO/SLI 目標

- 優先使用 PRD 明確的 SLO 數值
- 若 PRD 未明確，讀取 BRD §成功指標，轉換為可量化的 SLO
- 最低必須填寫：可用性 %、P99 延遲（ms）、錯誤率 %

### Step 6：填寫 §5 RTP / 機率設計（遊戲類型）

- 從 PRD 提取所有情境的 RTP 目標值（如：Main/ExtraBet/BuyFG 各情境）
- 非遊戲類型直接標記此章節 `N/A`

### Step 7：填寫 §6 Rate Limit

- 從 PRD §非功能需求 / §安全需求 提取 rate limit 設定
- 若 PRD 未明確，從 BRD §約束條件 補充
- 至少列出：登入端點、主要業務 API 端點的限制

### Step 8：填寫 §7 業務規則數值 + §8 容量規劃

- §7：PRD 中未被前述章節涵蓋的業務規則量化數值
- §8：最大並發用戶、峰值 TPS、資料保留期限（必須全部有值）

### Step 9：生成 docs/constants.json

讀取剛生成的 docs/CONSTANTS.md，產生對應 JSON 格式：
- 所有數值提取為 JSON 數字（非字串）
- `TBD` 值在 JSON 中記為 `null`
- 寫入 `docs/constants.json`（使用 Write 工具）

---

## Quality Gate 自我檢查

生成完成後，對照以下項目自我驗證：

| 檢查項 | 驗證方式 | 失敗處理 |
|--------|---------|---------|
| 無 {{PLACEHOLDER}} | 全文搜尋「{{」 | 補入實際數值或 TBD |
| 每個數值有 PRD §來源 | 逐行確認 PRD 來源欄 | 補上來源標注 |
| §4 SLO 三項均有值 | 確認可用性/延遲/錯誤率均非空 | 從 BRD 補充 |
| §8 容量三項均有值 | 確認並發/TPS/保留期限非空 | 標記 TBD 並說明 |
| constants.json 存在 | `ls docs/constants.json` | 重新生成 |
| JSON 與 .md 數值一致 | 抽樣對照 5 個數值 | 修正不一致項 |

---

## 上游衝突偵測

若掃描過程發現 PRD 不同章節的同一數值有衝突：

1. 標記 `[CONFLICT: PRD §X 值=A vs PRD §Y 值=B]`
2. 採用較保守的值（較小的倍率、較低的限制）
3. 在 constants.json 中加入 `"_conflicts": [{"key": "...", "note": "..."}]`
