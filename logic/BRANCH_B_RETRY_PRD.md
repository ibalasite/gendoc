# gendoc-repair Branch B 重試邏輯重設計 PRD

## 背景

repair 執行時曾發生 SCHEMA gate check 誤判（check 永遠回傳 FAIL），
導致 3 輪全局配額全部消耗在同一個 step 上，其他 step 被連帶放棄。

現有設計是**全局輪次制**（`_MAX_ROUNDS = 3`）：

```
Round 1：驗證所有 post-DRYRUN steps → 收集失敗 → 補跑全部失敗項
Round 2：同上
Round 3：同上 → 3 輪後停止，做最終掃描（B-3）
```

問題：任一 step 失敗 3 輪 → 整個 Branch B 停止，無論其他 step 狀態。

---

## 目標

以 **per-step 獨立計數** 取代全局輪次，讓卡住的 step 不阻礙其他 step。

---

## 適用範圍

- **Branch B only**（DRYRUN 後的所有 steps）
- Branch A 不在此範圍（多為單一檔案，現有邏輯足夠）

---

## Branch B 實際 Step 清單（來自 pipeline.json）

| Step ID | special_skill | condition |
|---------|--------------|-----------|
| API | — | always |
| SCHEMA | — | always |
| FRONTEND | — | client_type != none |
| AUDIO | — | client_type == game |
| ANIM | — | client_type == game |
| CLIENT_IMPL | — | client_type != none |
| ADMIN_IMPL | — | has_admin_backend |
| RESOURCE | — | client_type != none |
| UML | gendoc-gen-diagrams | always |
| test-plan | — | always |
| BDD-server | — | always |
| BDD-client | — | client_type != none |
| RTM | — | always |
| runbook | — | always |
| LOCAL_DEPLOY | — | always |
| CICD | — | always |
| DEVELOPER_GUIDE | — | always |
| UML-CICD | gendoc-gen-diagrams | always |
| ALIGN | gendoc-align-check | always |
| ALIGN-FIX | gendoc-align-fix | always |
| ALIGN-VERIFY | gendoc-align-check | always |
| CONTRACTS | gendoc-gen-contracts | always |
| MOCK | gendoc-gen-mock | client_type != api-only |
| PROTOTYPE | gendoc-gen-prototype | client_type != none |
| HTML | gendoc-gen-html | always |

---

## 新演算法

```
INPUT：
  pending          = condition 成立的 post-DRYRUN steps（依 pipeline.json 順序）
  fail_count       = {}   # step_id → 累計失敗次數
  permanently_failed = []  # [(sid, layer, details)]
  done             = []   # [sid]
  MAX_PER_STEP     = 3    # 每個 step 最多失敗幾次

LOOP（每一輪）：
  next_pending = []

  FOR each step in pending（依序，不中斷）：
    執行 L1 / L2 / L3 驗證

    IF pass：
      done.append(sid)

    IF fail：
      fail_count[sid] += 1
      IF fail_count[sid] < MAX_PER_STEP：
        補跑 step（立即，不等本輪結束）
        next_pending.append(step)
      ELSE：
        permanently_failed.append((sid, layer, details))

  pending = next_pending
  IF pending 為空：break

OUTPUT：
  ✅ done 清單
  ❌ permanently_failed 清單（含最後一次失敗原因）
```

---

## 規則明細

| # | 規則 | 說明 |
|---|------|------|
| R-1 | per-step 計數 | fail_count 每個 step 獨立，互不影響 |
| R-2 | 輪內不中斷 | 一個 step 失敗後繼續處理本輪其他 steps |
| R-3 | 補跑立即執行 | 驗失敗 → 立即補跑 → next_pending，不等本輪結束 |
| R-4 | 下輪只含上輪失敗項 | pass 的 step 不再進入下輪 |
| R-5 | 全局安全閥 | 最大輪次 = MAX_PER_STEP，防止演算法異常無限循環 |
| R-6 | 失敗定義與現有一致 | L1 stale / L2 輸出缺失 / L3 spec_rules 未達門檻 |
| R-7 | 補跑方式與現有一致 | Skill('gendoc-flow', args='--only {step_id}') |
| R-8 | permanently_failed 不重試 | 達到上限後移除，不再驗證、不再補跑 |

---

## 與現有程式碼的差異

| 項目 | 現有 | 新設計 |
|------|------|--------|
| 重試計數單位 | 全局輪次 `_MAX_ROUNDS = 3` | per-step `fail_count[sid]` |
| 停止條件 | 3 輪用完 | 個別 step 達 3 次 OR pending 清空 |
| 補跑時機 | 本輪所有驗證後統一補跑 | 驗失敗當下立即補跑 |
| B-3 最終掃描 | 需要（3 輪後額外做） | 移除（結果在迴圈內即時結算） |

---

## 實作清單

| # | 變更位置 | 內容 |
|---|---------|------|
| 1 | B-0 初始化 | 移除 `_MAX_ROUNDS` / `_round_failures`；加入 `_fail_count` / `_permanently_failed` / `_done` / `_pending` |
| 2 | B-2 主迴圈 | 完全重寫：while pending 迴圈 + per-step fail_count 邏輯 |
| 3 | B-3 報告 | 移除最終掃描；直接輸出 `_done` / `_permanently_failed` |
