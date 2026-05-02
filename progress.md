# reviewtemplate Progress — 新增 Step 三件套審查

> 所有新增 pipeline step 的三件套（.md / .gen.md / .review.md）必須通過 `/reviewtemplate` 審查，finding = 0 才算完成。
> 每個 step 審查完成後立即 commit。

---

## 狀態說明

| 符號 | 意義 |
|------|------|
| `[ ]` | 待執行 |
| `[x]` | 已完成（finding = 0 或 PASSED-tiered） |
| `[B]` | 阻塞中（需先建立缺少的 template 檔案） |
| `[N/A]` | special_skill 步驟，無標準三件套，不適用 reviewtemplate |

---

## Part A — 標準三件套（可直接 reviewtemplate）

| 狀態 | Step | 三件套完整度 | 備注 |
|------|------|------------|------|
| `[x]` | CONSTANTS | ✅✅✅ | finding=0，5輪，11個findings全修復 |
| `[x]` | AUDIO | ✅✅✅ | finding=0，3輪，9個findings全修復 |
| `[x]` | ANIM | ✅✅✅ | finding=0，2輪，7個findings全修復 |
| `[x]` | CLIENT_IMPL | ✅✅✅ | finding=0，5輪，28個findings全修復 |
| `[x]` | ADMIN_IMPL | ✅✅✅ | finding=0（fix後），5輪，MAX_ROUNDS，最終2LOW全修復 |
| `[x]` | RESOURCE | ✅✅✅ | finding=0（fix後），5輪，MAX_ROUNDS，最終4 MEDIUM/LOW全修復 |
| `[ ]` | CICD | ✅✅✅ | |
| `[ ]` | DEVELOPER_GUIDE | ✅✅✅ | |

## Part B — 需先補建 .review.md（blocked）

| 狀態 | Step | 三件套完整度 | 備注 |
|------|------|------------|------|
| `[B]` | DRYRUN | ✅✅❌ | 缺 `DRYRUN.review.md`；建立後可執行 reviewtemplate |

## Part C — special_skill 步驟（N/A）

| 狀態 | Step | 說明 |
|------|------|------|
| `[N/A]` | UML-CICD | gendoc-gen-diagrams 驅動，無標準三件套 |
| `[N/A]` | ALIGN-FIX | gendoc-align-fix 驅動，無標準三件套 |
| `[N/A]` | ALIGN-VERIFY | gendoc-align-check 驅動，無標準三件套 |
| `[N/A]` | CONTRACTS | gendoc-gen-contracts 驅動，無標準三件套 |
| `[N/A]` | MOCK | gendoc-gen-mock 驅動，無標準三件套 |
| `[N/A]` | PROTOTYPE | gendoc-gen-prototype 驅動，無標準三件套 |

---

## 執行記錄

| Step | 完成時間 | 初始 Finding | 最終 Finding | Commit |
|------|---------|------------|------------|--------|
| CONSTANTS | 2026-05-02 | 3 | 0 | 7620407 |
| AUDIO | 2026-05-02 | 6 | 0 | 534cbe9 |
| ANIM | 2026-05-02 | 7 | 0 | 2b01803 |
| CLIENT_IMPL | 2026-05-02 | 9 | 0 | f1fea52 |
| ADMIN_IMPL | 2026-05-02 | 11 | 0 | 4d57e0b |
| RESOURCE | 2026-05-02 | 23 | 0 | (pending) |
