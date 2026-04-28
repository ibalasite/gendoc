---
name: gendoc-gen-client-bdd
description: |
  Client 端 BDD Feature Files 生成 — 智能路由：
  Web/HTML5 → 讀取 templates/BDD-client.gen.md + BDD-client.review.md
  執行 Gen → Review → Fix 三專家迴圈（與 gendoc-flow D12b 行為完全一致）。
  Unity → Unity Test Framework BDD scenarios（C# NUnit）。
  Cocos → Jest TypeScript BDD（features/client/ + tests/cocos/）。
  可由 gendoc-auto / gendoc-flow 自動呼叫，或獨立手動呼叫。
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
  - Skill
---

# gendoc-gen-client-bdd — Client 端 BDD Feature 生成（智能路由）

依 `client_type` 路由到對應的生成策略：
- **Web / HTML5**：委派給 `templates/BDD-client.gen.md` 規則（3-expert pattern，與 pipeline D12b 行為一致）
- **Unity / Cocos**：使用平台專屬生成邏輯

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：Session Config 讀取（靜默）

```bash
_CWD="$(pwd)"
_STATE_FILE="${_CWD}/.gendoc-state.json"
_EXEC_MODE=$(python3 -c "
import json, sys
try:
    d = json.load(open('${_STATE_FILE}'))
    print(d.get('execution_mode', 'full-auto'))
except Exception:
    print('full-auto')
" 2>/dev/null || echo "full-auto")
echo "[gen-client-bdd] execution_mode=${_EXEC_MODE}"
```

Full-Auto 模式：所有決策自動選預設值，不詢問。

---

## Step 1：確認前置條件 + 路由判斷

```bash
[[ -f "docs/PRD.md" ]] || { echo "[ERROR] docs/PRD.md 不存在"; exit 1; }
[[ -f "docs/PDD.md" ]] || echo "[WARN] docs/PDD.md 不存在，僅依 PRD 生成 BDD"

# 優先從 state file 讀取 client_type
_CLIENT_TYPE=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('client_type',''))" 2>/dev/null || echo "")

# 回退：文件偵測
if [[ -z "$_CLIENT_TYPE" || "$_CLIENT_TYPE" == "null" ]]; then
  if grep -qiE "unity|UnityEngine" docs/PRD.md docs/EDD.md 2>/dev/null; then
    _CLIENT_TYPE="unity"
  elif grep -qiE "cocos|CocosCreator|cc\." docs/PRD.md docs/EDD.md 2>/dev/null; then
    _CLIENT_TYPE="cocos"
  elif grep -qiE "html5|WebGL|canvas|PixiJS|Phaser|GameCanvas" docs/PRD.md docs/EDD.md 2>/dev/null; then
    _CLIENT_TYPE="html5-game"
  elif grep -qiE "web|SaaS|React|Vue|Angular|Next\.js|Nuxt|前端|browser" docs/PRD.md docs/EDD.md 2>/dev/null; then
    _CLIENT_TYPE="web-saas"
  else
    _CLIENT_TYPE="none"
  fi
fi

if [[ "$_CLIENT_TYPE" == "none" ]]; then
  echo "[INFO] client_type=none，跳過 Client BDD 生成"; exit 0
fi

echo "[gen-client-bdd] client_type=${_CLIENT_TYPE}"

# 路由決策
case "$_CLIENT_TYPE" in
  web-saas|web|html5-game|html5)
    echo "[ROUTE] → Template-driven path（BDD-client.gen.md + review loop）"
    _ROUTE="template"
    ;;
  unity)
    echo "[ROUTE] → Unity 專屬路徑（C# NUnit + PlayMode）"
    _ROUTE="unity"
    ;;
  cocos)
    echo "[ROUTE] → Cocos 專屬路徑（Jest TypeScript）"
    _ROUTE="cocos"
    ;;
  *)
    echo "[ROUTE] → 未知 client_type，fallback → template-driven"
    _ROUTE="template"
    ;;
esac
```

---

## Step 2A（Web / HTML5）：Template-Driven 3-Expert Pattern

**條件**：`_ROUTE == "template"`

此路徑與 `gendoc-flow D12b-BDD-client` 行為完全一致，確保手動呼叫與 pipeline 輸出相同。

### 2A-1：讀取 Gen Template

```bash
_TEMPLATE_DIR="$HOME/.claude/skills/gendoc/templates"
_GEN_RULES="${_TEMPLATE_DIR}/BDD-client.gen.md"
_REVIEW_RULES="${_TEMPLATE_DIR}/BDD-client.review.md"

echo "Gen rules：${_GEN_RULES}"
echo "Review rules：${_REVIEW_RULES}"
[[ -f "$_GEN_RULES" ]] || { echo "[ERROR] BDD-client.gen.md 不存在：${_GEN_RULES}"; exit 1; }
[[ -f "$_REVIEW_RULES" ]] || { echo "[WARN] BDD-client.review.md 不存在，略過 Review 迴圈"; }
```

### 2A-2：Gen Subagent（生成 features/client/）

spawn Agent，傳入：

---
角色：資深 Frontend QA Expert + E2E Automation Specialist

讀取以下 Gen Rules 文件作為生成規則（先讀完再開始生成）：
```
<gen-rules-file 內容>
```
（實際使用時：讀取 `$_GEN_RULES` 文件全文，作為生成指令）

然後讀取上游文件鏈（依 Gen Rules 中的上游文件清單，靜默跳過不存在的）：
- `docs/IDEA.md`、`docs/BRD.md`、`docs/PRD.md`、`docs/PDD.md`
- `docs/FRONTEND.md`、`docs/EDD.md`、`docs/test-plan.md`
- `features/`（BDD-server，了解後端場景邊界）

完全遵循 Gen Rules 中的格式規範、多檔案命名規則、tag 策略、禁止模式，生成所有 `features/client/` 下的 .feature 檔案。

每個生成的檔案輸出：`GENERATED_FILE: features/client/{path}.feature`

最後輸出一行（完全匹配）：
```
GEN_RESULT: {"files":[...], "scenarios_total": N, "prd_ac_covered": M}
```
---

解析 `GEN_RESULT`。

### 2A-3：Commit Gen

```bash
git add features/client/
_FILE_COUNT=$(find features/client -name "*.feature" 2>/dev/null | wc -l | tr -d ' ')
git commit -m "test(gendoc)[D12b]: gen BDD-client — ${_FILE_COUNT} feature files (client_type=${_CLIENT_TYPE})"
```

### 2A-4：Review → Fix → Commit 迴圈

讀取 state file 取得 `review_strategy` 和 `max_rounds`：

```bash
_STRATEGY=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('review_strategy','standard'))" 2>/dev/null || echo "standard")
_MAX_ROUNDS=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('max_rounds',5))" 2>/dev/null || echo "5")
echo "review_strategy=${_STRATEGY}  max_rounds=${_MAX_ROUNDS}"
```

若 `$_REVIEW_RULES` 不存在 → 跳過 Review 迴圈，直接到 Step 2A-5。

否則執行 Review → Fix → Round Summary → Commit 迴圈（最多 `_MAX_ROUNDS` 輪）：

**每輪流程（依序執行，不可跳過）：**

**A. Review Subagent**

spawn Agent（角色：資深 QA 主管）：

讀取 `$_REVIEW_RULES` 文件作為審查規則；
讀取 `features/client/` 所有 .feature 檔案；
讀取 `docs/PRD.md`、`docs/PDD.md`（若存在）、`docs/FRONTEND.md`（若存在）。

嚴格依 Review Rules 審查，對每個問題輸出：
```
[SEVERITY] 問題描述
  位置：features/client/{file}
  建議修復：<具體說明>
```

最後一行輸出（完全匹配）：
```
REVIEW_RESULT: {"findings":[{"id":"F1","sev":"CRITICAL|HIGH|MEDIUM|LOW","title":"...","file":"...","fix":"..."}],"critical":N,"high":N,"medium":N,"low":N,"total":N}
```

**B. 判斷終止條件（不立即 break，只設 terminate flag）**

```python
terminate = False
if finding_total == 0:
    terminate = True; reason = "PASSED — finding=0"
elif strategy == "tiered" and round >= 6 and (critical + high + medium) == 0:
    terminate = True; reason = "TIERED_PASS — C+H+M=0"
elif round >= max_rounds:
    terminate = True; reason = f"MAX_ROUNDS={max_rounds}"
elif strategy == "rapid" and round >= 3:
    terminate = True; reason = "MAX_ROUNDS — rapid=3"
```

**C. Fix Subagent（finding_total > 0 時執行，包括最後一輪）**

spawn Agent（角色：資深 Frontend QA + E2E Specialist）：

讀取所有 REVIEW_RESULT findings；
讀取對應的 .feature 檔案；
逐一修復每個 CRITICAL / HIGH finding（MEDIUM / LOW 評估修復必要性）；
無法修復的 → 在 .feature 頂部加 `# TODO[REVIEW-DEFERRED-RN]: <finding>` 標記；

最後一行輸出（完全匹配）：
```
FIX_RESULT: {"fixed":N,"unfixed":N,"unfixed_ids":["F2"],"summary":"..."}
```

**D. Round Summary（每輪必輸出，在 commit 前）**

```
┌─── BDD-client Review Round {round}/{max_rounds} ──────────────┐
│  Review：CRITICAL={C} HIGH={H} MEDIUM={M} LOW={L}
│  Fix：   修復 {fixed} 個 / 殘留 {unfixed} 個
│  本輪狀態：{✅ PASS / 🔧 FIX / ⚠️ MAX}  {reason}
│  Fix summary：{fix_result.summary}
└──────────────────────────────────────────────────────────────┘
```

**E. Commit（每輪必執行，PASS 和 FIX 路徑都 commit）**

```bash
git add features/client/
if [[ $finding_total -eq 0 ]]; then
  git commit -m "test(gendoc)[D12b]: review-r${round} — PASS (0 findings)"
else
  git commit -m "test(gendoc)[D12b]: review-r${round} — fix ${fixed}/${finding_total} findings"
fi
```

**F. Break（在 commit 之後）**

```python
if terminate:
    break
```

### 2A-5：輸出生成摘要

```
Client BDD 已生成（Template-Driven，與 pipeline D12b 一致）：
  client_type：{_CLIENT_TYPE}
  Feature Files：{N} 個（features/client/）
  Scenarios 總計：{M} 個
  覆蓋 PRD AC：{X}/{TOTAL}
  Review 輪次：{round}，終止原因：{reason}
```

---

## Step 2B（Unity）：Unity Test Framework BDD

**條件**：`_ROUTE == "unity"`

確認輸出目錄：`tests/unity/bdd/`

spawn Agent（角色：Unity QA 工程師）：

讀取 `docs/PRD.md` 和 `docs/PDD.md`（若存在），生成 `tests/unity/bdd/<Feature>Tests.cs`：

格式規範：
```csharp
// Feature: <功能名稱>（對應 PRD User Story）
// 使用 NUnit + Unity Test Framework

using NUnit.Framework;
using UnityEngine.TestTools;
using System.Collections;

[TestFixture]
public class <Feature>Tests
{
    // Scenario: <正常路徑場景>
    // Given <前置狀態>
    // When <觸發條件>
    // Then <預期結果>
    [Test]
    public void <FeatureName>_<NormalPath>_<ExpectedResult>()
    {
        // Arrange（Given）
        // TODO: 設置前置狀態

        // Act（When）
        // TODO: 執行操作

        // Assert（Then）— 必須因錯誤實作而 FAIL
        Assert.Fail("TODO: 實作斷言");
    }

    // Play Mode Test（UI 互動）
    [UnityTest]
    public IEnumerator <UIFeature>_<UserAction>_<UIState>()
    {
        // Arrange
        // TODO: 載入 Scene / Prefab
        yield return null;

        // Act
        // TODO: 模擬輸入
        yield return null;

        // Assert
        Assert.Fail("TODO: 實作 UI 狀態斷言");
    }
}
```

每個 PRD AC 至少：
- 1 個 Edit Mode Test（純邏輯）
- 1 個 Play Mode Test（需 Unity 運行環境）
- 1 個邊界條件 Test（null / 最大值 / 最小值）

---

spawn Agent（角色：Unity BDD 審查員）審查生成結果：
- [CRITICAL] PRD 中任何 AC 在 BDD 中沒有對應 Test
- [CRITICAL] 假斷言（`Assert.Fail("TODO")` 原封不動未替換）
- [CRITICAL] 缺少 Play Mode Test（`[UnityTest]` 方法）
- [HIGH] 缺少 Edit Mode Test（`[Test]` 方法）
- [HIGH] 缺少邊界條件 Test

審查通過後：

```bash
git add tests/unity/bdd/
git commit -m "test(gendoc)[D12b]: gen BDD-client (Unity) — $(ls tests/unity/bdd/*.cs 2>/dev/null | wc -l | tr -d ' ') test files"
```

輸出摘要：
```
Client BDD 已生成（Unity 專屬）：
  client_type：unity
  Test Files：{N} 個（tests/unity/bdd/）
  Edit Mode Tests / Play Mode Tests：{E} / {P}
  覆蓋 PRD AC：{X}/{TOTAL}
```

---

## Step 2C（Cocos）：Jest TypeScript BDD

**條件**：`_ROUTE == "cocos"`

確認輸出目錄：`features/client/`（Gherkin）+ `tests/cocos/`（Jest 實作）

spawn Agent（角色：Cocos QA 工程師）：

讀取 `docs/PRD.md` 和 `docs/PDD.md`（若存在），生成：
- `features/client/<Feature>.feature`（Gherkin 格式，文件用途）
- `tests/cocos/<Feature>.test.ts`（Jest 實作，BDD 語意命名）

Jest BDD 格式規範：
```typescript
// Feature: <功能名稱>
// 對應 PRD User Story: <AC 編號>

import { <Component> } from '../../src/components/<Component>';

describe('<Feature>', () => {
  describe('Scenario: <正常路徑>', () => {
    it('Given <前置> When <動作> Then <結果>', () => {
      // Arrange（Given）
      // Act（When）
      // Assert（Then）— 必須因錯誤實作而 FAIL
      expect(true).toBe(false); // TODO: 替換為真實斷言
    });
  });

  describe('Scenario: <錯誤路徑>', () => {
    it('Given <無效輸入> Then <錯誤處理>', () => {
      expect(() => {
        // TODO: 觸發錯誤路徑
      }).toThrow('<具體錯誤訊息>');
    });
  });
});
```

---

spawn Agent（角色：Cocos BDD 審查員）審查：
- [CRITICAL] PRD 中任何 AC 在 BDD 中沒有對應 Scenario
- [CRITICAL] 缺少對應的 Jest `.test.ts` 檔案
- [HIGH] Jest describe/it 命名未遵循 BDD 語意（Given/When/Then 結構）
- [CRITICAL] 假斷言（`expect(true).toBe(false)` hardcode 未替換）

審查通過後：

```bash
git add features/client/ tests/cocos/
_F=$(find features/client -name "*.feature" 2>/dev/null | wc -l | tr -d ' ')
_T=$(find tests/cocos -name "*.test.ts" 2>/dev/null | wc -l | tr -d ' ')
git commit -m "test(gendoc)[D12b]: gen BDD-client (Cocos) — ${_F} features / ${_T} jest tests"
```

輸出摘要：
```
Client BDD 已生成（Cocos 專屬）：
  client_type：cocos
  Feature Files：{F} 個（features/client/）
  Jest Test Files：{T} 個（tests/cocos/）
  覆蓋 PRD AC：{X}/{TOTAL}
```
