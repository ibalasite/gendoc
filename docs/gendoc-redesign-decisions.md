# gendoc 重新設計 — 決策清單

> 本文件列出所有待決策的修改項目，請在「決策」欄填入 ✅ 同意 / ❌ 拒絕 / 🔄 修改（附說明）。

---

## 背景確認

**LOCAL_DEPLOY 是否參考 RUNBOOK？**
確認：否。`LOCAL_DEPLOY.gen.md` 的 upstream-docs = `req/, IDEA, BRD, PRD, PDD, EDD, ARCH, API, SCHEMA, test-plan, BDD`，RUNBOOK 不在其中。兩者是獨立文件，無依賴關係，捆在同一 step 純屬歷史遺留。

---

## 新 Step 命名對照表（提案）

| 原始 ID | 新 ID | 說明 |
|---------|-------|------|
| STEP A / DOC-A | D01-IDEA | 以 template 檔名命名 |
| STEP B / DOC-B | D02-BRD | |
| DOC-03 | D03-PRD | |
| DOC-04 | D04-PDD | |
| DOC-05 | D05-EDD | |
| DOC-06 | D06-ARCH | |
| DOC-07 | D07-API | |
| DOC-08 | D08-SCHEMA | |
| DOC-09 | D09-test-plan | 對應 test-plan.md |
| DOC-10 | D10-BDD | |
| DOC-10-D（前半） | D11-runbook | **新增，獨立拆出** |
| DOC-10-D（後半） | D12-LOCAL_DEPLOY | **新增，獨立拆出** |
| DOC-11 | D13-ALIGN | 跨文件對齊掃描 |
| DOC-12 | D14-HTML | HTML 生成 |
| DOC-12P | D14-HTML-P | GitHub Pages 驗證（子步驟，不獨立計數） |

**Review step 命名規則：** 每個 D0N-XXX 對應一個 D0N-XXX-R（Review Loop），例如 D03-PRD-R。

---

## 修改清單

### #1 gendoc-flow — 刪除 §STEP-MAPPING 死碼

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | §STEP-MAPPING（約 37 行）將舊 autodev 31步 ID 轉換為新 ID，但此對照表的輸出變數 `_AUTODEV_STEP` 從未被 skip 條件使用 |
| **說明** | 這段 mapping 是在舊版 autodev/devsop 架構下遺留的死碼，當時目的是讓外部系統設定 31 步編號後映射到 gendoc 內部步驟，現在整個架構已移除外部依賴，這段完全無效 |
| **建議** | 直接刪除 §STEP-MAPPING 整段（lines 59-96），不留替代 |
| **改後影響** | gendoc-flow 少 37 行，無功能影響，skip 條件讀取 `start_step` 邏輯不變 |
| **決策** | 同意|

---

### #2 gendoc-flow — 清除 "autodev" 字眼

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | Step 0 說明文字和變數命名中仍有 "autodev" 字樣（如 `_AUTODEV_STEP`） |
| **說明** | 上次 devsop cleanup 清了大部分，但 gendoc-flow 內部的 autodev 引用沒有完整清除 |
| **建議** | 一併在 #1 刪除 §STEP-MAPPING 時清除所有 autodev 字樣；Step 0 說明改為「gendoc-flow step 控制」 |
| **改後影響** | 純文字清理，無功能影響 |
| **決策** | 同意 |

---

### #3 gendoc-flow — DOC-10-D 拆分為兩個獨立 Step

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | DOC-10-D 把 runbook（A+B）和 LOCAL_DEPLOY（C+D）捆在同一個 step，共用一個 skip 條件「兩者都非空才跳過」 |
| **說明** | **確認：LOCAL_DEPLOY 不參考 RUNBOOK，兩者是完全獨立的文件。** 捆綁導致無法分別重跑：RUNBOOK 審查完成後若想單獨重跑 LOCAL_DEPLOY，必須整段重跑，也會重新觸發 RUNBOOK 流程 |
| **建議** | 拆成兩個獨立 step：`D11-runbook`（含 D11-runbook-R Review Loop）和 `D12-LOCAL_DEPLOY`（含 D12-LOCAL_DEPLOY-R Review Loop），各自有獨立 skip 條件 |
| **改後影響** | 總 step 數從 14 變 16（加上兩個 -R），gendoc-config 選單同步新增兩個選項；舊的 DOC-10-D skip 條件邏輯需拆分為兩條 |
| **決策** | 同意 |

---

### #4 gendoc-flow — 所有 Step ID 改為新命名格式

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | 所有 step 使用 `DOC-03`、`DOC-10` 等不可讀 ID，看不出在產生什麼文件 |
| **說明** | `DOC-03` 沒有語義，新人或三個月後的自己都不知道是什麼。`D03-PRD` 同時表達「第3步」和「產生 PRD」 |
| **建議** | 依新對照表全部替換（見上方命名表）。Skip 條件的整數比較邏輯：從 step 字串取出前兩位數字（`D03-PRD` → `3`），保持 `_START_STEP > N` 比較方式 |
| **改後影響** | gendoc-flow 全文 step ID 更新；gendoc-config 選單 ID 同步；gendoc-auto 中的 step ID 同步；state file 中的 `start_step` 值從 `"DOC-03"` 格式改為 `"D03-PRD"` 格式 |
| **決策** | 同意 |

---

### #5 gendoc-flow — commit 範例還有 devsop 字樣

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | gendoc-flow 的 commit 範例寫著 `docs(devsop)[DOC-03]: ...`，上次 devsop cleanup 漏掉了 |
| **說明** | 只是 commit 範例文字，不影響實際執行，但不一致 |
| **建議** | 改為 `docs(gendoc)[D03-PRD]: ...` 格式（配合 #4 新命名） |
| **改後影響** | 純文字，無功能影響 |
| **決策** | 同意 |

---

### #6 gendoc-flow — `_LOOP_COUNT` 本地計算值錯誤

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | Step 0 本地計算 `_LOOP_COUNT`：`rapid=1`、`standard=2`，但 gendoc-config 的實際定義是 `rapid=3`、`standard=5`。另外有一個不存在的策略 `thorough` |
| **說明** | 「變數統一 config set，其他 skill 只能用」原則的違反。gendoc-flow 自己算出錯誤的值，蓋過了 config 設定的正確值 |
| **建議** | 刪除本地 `_LOOP_COUNT` 計算邏輯，改為直接從 state file 讀取 `max_rounds`（由 gendoc-config 設定的正確值） |
| **改後影響** | Review loop 的最大輪次會正確反映使用者在 gendoc-config 的選擇；移除 `thorough` 策略這個不存在的分支 |
| **決策** | 同意|

---

### #7 gendoc-flow — skip 條件整數比較將在字串 ID 下失效

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-flow |
| **問題** | Skip 條件是 `_START_STEP > 3`（整數比較），但執行 #4 後 `start_step` 變成字串 `"D03-PRD"`，整數比較會報錯或永遠 false |
| **說明** | Python 比較 `"D03-PRD" > 3` 會 TypeError；bash 比較 `-gt` 對非純數字字串結果不確定 |
| **建議** | Skip 條件改為先從 step 字串提取數字：`_STEP_NUM=$(echo "$_START_STEP" | grep -oP '^\d+')` 或 Python `int(start_step.split('-')[0][1:])`，再做整數比較 |
| **改後影響** | Skip 條件行為與現在完全一致，只是能正確處理字串格式的 step ID |
| **決策** | 同意|

---

### #8 gendoc-config — `current_step` vs `start_step` key 不一致（關鍵 bug）

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-config |
| **問題** | gendoc-config Step 5 寫入 state file 時用的 key 是 `current_step`，但 gendoc-flow Step 0 讀取時用的 key 是 `start_step` |
| **說明** | 兩個 key 永遠不會對到，導致「從某個 STEP 重新開始」功能完全失效——gendoc-config 設定的值 gendoc-flow 永遠讀不到 |
| **建議** | 統一 key 名稱。建議用 `start_step`（語義更清楚：「從這個 step 開始」），gendoc-config 改為寫 `start_step` |
| **改後影響** | 「從某個 STEP 重新開始」功能恢復正常，這是目前完全失效的功能 |
| **決策** | 同意|

---

### #9 gendoc-config — 選單還有舊格式選項

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-config |
| **問題** | Step 2「從某個 STEP 重新開始」的選項列表：混合了 `STEP A/B/C/D`（gendoc-auto 內部步驟代號）和 `DOC-03`~`DOC-12P`（舊 ID），兩套命名同時存在 |
| **說明** | 執行 #4 後，選單所有 ID 都要換成新格式；STEP A/B 要合併進 D01-IDEA/D02-BRD |
| **建議** | 選單改為新 ID 清單（D01-IDEA 至 D14-HTML，含各 -R Review step），同步新增 D11-runbook 和 D12-LOCAL_DEPLOY 選項 |
| **改後影響** | 使用者看到的選單語義清晰，且與實際 step 一一對應 |
| **決策** | 同意|

---

### #10 gendoc-config — `execution_mode` 被硬編碼為 `full-auto`

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-config |
| **問題** | Step 5 寫入 state file 時：`execution_mode = 'full-auto'`（hardcoded），不管使用者在 Step 3 選了什麼模式 |
| **說明** | 使用者選 `interactive` → config 確認顯示 interactive → 實際寫入 state 卻是 `full-auto`，下次執行永遠是全自動模式 |
| **建議** | 改為寫入 `_NEW_MODE`（Step 3 使用者選擇的變數） |
| **改後影響** | 使用者選擇的 interactive 模式會正確被保存，下次執行 gendoc-flow/gendoc-auto 會按選擇的模式運作 |
| **決策** | gendoc 不再有interactive 需求，接下來只auto模式，變數先保留|

---

### #11 gendoc-auto — 啟動時覆蓋 gendoc-config 設定的變數

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-auto |
| **問題** | gendoc-auto 啟動時（lines 233-237）hardcode 寫入 state file：`execution_mode='full-auto'`、`review_strategy='standard'`、`max_rounds=5`、`stop_condition='...'`，無條件覆蓋使用者透過 gendoc-config 設定的值 |
| **說明** | 「只有 config 能 SET 變數」原則的最大違反。使用者執行 gendoc-config 設成 exhaustive 模式，馬上執行 gendoc-auto，config 設定被清空回 standard |
| **建議** | gendoc-auto 改為「若 state file 不存在才寫入預設值；若已存在則不觸碰這些欄位」。或者完全移除這段硬編碼，讓 gendoc-config 負責初始設定 |
| **改後影響** | gendoc-config 的設定終於有意義；使用者客製化的 review 策略會被尊重 |
| **決策** | 同意|

---

### #12 gendoc-shared — DEPRECATED 段落仍有 SET/GET 程式碼

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-shared |
| **問題** | §gendoc_loop_count 和 §gendoc_start_step 兩段標記為 DEPRECATED，但 SET/GET 程式碼還在，其他 skill 可能誤用 |
| **說明** | 標記 DEPRECATED 卻不刪除是最壞的狀況：閱讀者不確定是否應該用，工具掃描可能誤判為有效 API |
| **建議** | 刪除這兩個 DEPRECATED 段落的所有 SET/GET 程式碼，只保留一行說明「已廢棄，請改用 state file 的 max_rounds / start_step」 |
| **改後影響** | gendoc-shared 更乾淨；若有 skill 誤用了 DEPRECATED 函式，會提前發現（但目前確認無 skill 呼叫這兩段） |
| **決策** |同意|

---

### #13 gendoc-shared — STATE-SCHEMA 描述過時

| 欄位 | 內容 |
|------|------|
| **SKILL** | gendoc-shared |
| **問題** | STATE-SCHEMA 中：`start_step` 描述為「autodev 31步編號」；`current_step` 描述為 `"01"–"31"` |
| **說明** | 這些是舊架構的遺留描述，與現在的實際格式不符，會誤導未來的開發者 |
| **建議** | 更新 STATE-SCHEMA：`start_step` 改為「gendoc-flow step ID，格式 D01-IDEA 至 D14-HTML」；移除 `current_step`（或標注為 legacy alias） |
| **改後影響** | 文件正確，無功能影響 |
| **決策** | 同意 |

---

## 執行順序建議

若全部核准，建議按此順序修改（避免互相依賴問題）：

1. gendoc-shared（#12、#13）— 先修基礎定義
2. gendoc-config（#8、#9、#10）— 修設定層
3. gendoc-auto（#11）— 修入口點
4. gendoc-flow（#1、#2、#6、#7、#3、#4、#5）— 最後修主流程

---

## 不在本次範圍的項目

- gendoc-gen-* 系列 skill（各文件生成 skill）：不改 step 內容，只有 gendoc-config 選單 ID 需要同步
- templates/*.gen.md / *.review.md / templates/*.md  不改  
- bin/ 工具：不改
