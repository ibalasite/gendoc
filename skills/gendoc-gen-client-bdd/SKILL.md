---
name: gendoc-gen-client-bdd
description: |
  讀取完整上游文件鏈（IDEA/BRD/PRD/PDD/EDD/ARCH/API/SCHEMA/test-plan/server-BDD），
  依 Client 類型生成 Client 端 BDD Feature Files。
  Web SaaS → Playwright E2E feature files；
  Unity → Unity Test Framework BDD scenarios；
  Cocos → Jest TypeScript BDD；
  HTML5 → Playwright BDD。
  由 devsop-autodev STEP 16 自動呼叫，或可獨立手動呼叫。
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Agent
  - Skill
---

# gendoc-gen-client-bdd — Client 端 BDD Feature 生成

讀取完整上游文件鏈後，生成 Client 端 BDD Feature Files。

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：Session Config 讀取（靜默）

```bash
_STATE_FILE="$(pwd)/.gendoc-state.json"
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

## Step 0.5：讀取完整上游文件鏈

依「全上游對齊」規則，Client BDD 需讀取所有上游文件，確保 Client 端測試場景與業務目標和系統設計完全對齊：

```bash
_DOCS="${_DOCS:-$(pwd)/docs}"
_IDEA="${_IDEA:-$_DOCS/IDEA.md}"
_BRD="${_BRD:-$_DOCS/BRD.md}"
_PRD="${_PRD:-$_DOCS/PRD.md}"
_PDD="${_PDD:-$_DOCS/PDD.md}"
_EDD="${_EDD:-$_DOCS/EDD.md}"
_ARCH="${_ARCH:-$_DOCS/ARCH.md}"
_API="${_API:-$_DOCS/API.md}"
_SCHEMA="${_SCHEMA:-$_DOCS/SCHEMA.md}"
_TEST_PLAN="${_TEST_PLAN:-$_DOCS/test-plan.md}"
_BDD="${_BDD:-$(pwd)/features}"  # server-side BDD feature files directory
```

**上游讀取清單（依優先順序）：**

| 文件 | 必讀內容 | 用途 |
|------|---------|------|
| `IDEA.md`（若存在）| 全文 | Client BDD 場景語言需反映 IDEA 的產品願景與業務概念 |
| `BRD.md` | 業務目標、使用者角色 | Client 端測試的業務驗收標準需對應 BRD 的業務指標 |
| `PRD.md` | 所有功能 AC、User Story | **主要輸入**：每個 AC 必須有對應 Client 端 Scenario |
| `PDD.md` | §4 功能需求、§6 互動設計 | **主要輸入**：UI 互動流程、畫面欄位、響應式設計需求 |
| `EDD.md` | §4 Security、§5 BDD 設計 | Client 端認證/授權流程的 Given 步驟來自 EDD |
| `ARCH.md` | §3 元件架構、§6 前端架構 | Client 端 Contract Testing 的 API Consumer 邊界 |
| `API.md` | 所有 Endpoint、Response Schema | Client BDD `@contract` tag：每個 API 呼叫需有對應 Client Scenario |
| `SCHEMA.md` | 資料模型 | Client 端測試資料初始化的 Background 步驟設計 |
| `test-plan.md` | §3.3 E2E/BDD、§9 Risk Matrix | Smoke 標記與 Risk=High 的功能加倍 Scenario 數量 |
| `features/`（BDD）| 所有 `.feature` 檔案 | 確保 Client BDD 覆蓋所有 server-side BDD 已定義的業務流程 |

若某文件不存在，靜默跳過，依既有流程繼續。

---

## Step 1：確認前置條件

```bash
[[ -f "docs/PRD.md" ]] || { echo "[ERROR] docs/PRD.md 不存在"; exit 1; }
[[ -f "docs/PDD.md" ]] || { echo "[WARN] docs/PDD.md 不存在，僅依 PRD 生成 BDD"; }

# 優先從 state file 讀取 client_type
_CLIENT_TYPE=$(python3 -c "import json; d=json.load(open('.gendoc-state.json')); print(d.get('client_type',''))" 2>/dev/null || echo "")

# 若 state file 無此欄位或不存在，回退到文件偵測（同 gendoc-gen-pdd Step 1 規則）
if [[ -z "$_CLIENT_TYPE" || "$_CLIENT_TYPE" == "null" ]]; then
  # 回退：讀取 docs/PRD.md + docs/EDD.md 關鍵字偵測
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
```

Client 類型已從 `.gendoc-state.json` 讀取（或回退到文件偵測）。
若 Client 類型為 `none`，輸出跳過訊息並結束。

確認輸出目錄：
- Web SaaS / HTML5-game → `features/client/` （Gherkin .feature 格式）
- Unity → `tests/unity/bdd/` （C# 測試類，BDD 格式註解）
- Cocos → `features/client/` （Gherkin .feature 格式，Jest runner）

---

## Step 2：spawn Agent 生成 BDD Feature Files

---

### 2a. Web SaaS / HTML5 前端（Playwright + Gherkin）

角色：QA 工程師 + UX Tester

讀取 docs/PRD.md 和 docs/PDD.md，為每個 Screen 生成 `features/client/<screen_name>.feature`：

BDD 格式規範：
```gherkin
Feature: <Screen 名稱>（對應 PRD User Story）

  Background:
    Given 使用者已登入
    And 目前在 <Screen> 頁面

  Scenario: <正常路徑場景>
    Given <前置狀態>
    When <使用者動作>
    Then <預期結果>
    And <UI 狀態變化>

  Scenario: <錯誤路徑場景>
    Given <前置狀態>
    When <使用者輸入無效資料>
    Then 應顯示錯誤訊息 "<具體訊息>"
    And 表單不應提交

  Scenario: <邊界條件場景>
    Given <邊界前置狀態>
    When <邊界操作>
    Then <邊界預期結果>

  @responsive
  Scenario Outline: 響應式 Layout 驗證
    Given 螢幕寬度為 <width>px
    When 進入 <Screen> 頁面
    Then 應顯示 <layout> 佈局
    Examples:
      | width | layout  |
      | 320   | mobile  |
      | 768   | tablet  |
      | 1440  | desktop |

  @a11y
  Scenario: Keyboard Navigation 驗證
    Given 使用者僅使用鍵盤
    When 按 Tab 鍵遍歷頁面
    Then 所有互動元件應可被 Focus
    And Focus 順序應符合視覺閱讀順序
```

每個 PRD AC 至少：
- 1 個正常路徑 Scenario
- 1 個錯誤路徑 Scenario
- 1 個邊界條件 Scenario
- `@responsive` Scenario Outline
- `@a11y` Keyboard Navigation Scenario

同時生成對應的 Playwright Step Definition 骨架：
`features/client/step_definitions/<screen_name>.steps.ts`

```typescript
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';

Given('<前置狀態>', async function() {
  // TODO: 實作前置狀態設置
});

When('<使用者動作>', async function() {
  // TODO: 實作使用者動作
});

Then('<預期結果>', async function() {
  // TODO: 實作斷言（必須因錯誤實作而 FAIL）
});
```

---

### 2b. Unity 遊戲（Unity Test Framework，BDD 風格）

角色：Unity QA 工程師

讀取 docs/PRD.md 和 docs/PDD.md，生成 `tests/unity/bdd/<Feature>Tests.cs`：

Unity BDD 格式規範（Edit Mode + Play Mode）：
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

    // Scenario: <UI 互動場景>（Play Mode）
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
- Edit Mode Test（純邏輯）
- Play Mode Test（需要 Unity 運行環境）
- 邊界條件 Test（null 輸入、最大值、最小值）

---

### 2c. Cocos Creator（Jest + TypeScript，Gherkin 語意）

角色：Cocos QA 工程師

讀取 docs/PRD.md 和 docs/PDD.md，生成：
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
      // TODO: 設置 Component 前置狀態

      // Act（When）
      // TODO: 呼叫 Component 方法

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

### 2d. HTML5 / WebGL 遊戲（Playwright + Gherkin）

同 Web SaaS 的 2a 格式，但 Tag 和重點不同：

額外 Scenario：
```gherkin
  @performance
  Scenario: 首次載入效能
    Given 使用者首次開啟遊戲
    When 頁面完全載入
    Then 首次互動時間應 < 3000ms
    And FPS 應 ≥ 30

  @webgl
  Scenario: WebGL Context Lost 處理
    Given 遊戲正在運行
    When WebGL Context 丟失（模擬）
    Then 遊戲應顯示「正在恢復...」提示
    And 5 秒內應自動恢復遊戲狀態

  @mobile
  Scenario: 觸控輸入驗證
    Given 使用者在行動裝置
    When 點擊 <Game Element>
    Then 應觸發 <對應遊戲事件>
```

---

## Step 3：獨立審查、驗證與輸出

spawn Agent（角色：Client BDD 品質審查員，subagent_type: "Model QA Specialist"）：
  讀取所有生成的 Client BDD 檔案（`features/client/` 或 `tests/unity/bdd/` 或 `tests/cocos/`）以及 `docs/PRD.md`、`docs/PDD.md`（若存在）。
  依 Client 類型（`_CLIENT_TYPE`）套用對應審查維度：

  **通用維度（所有 Client 類型）：**
  [CRITICAL] PRD 中任何 AC 在 Client BDD 中沒有對應 Scenario（必須逐一比對）
  [CRITICAL] 任何斷言是假斷言（Unity: `Assert.Fail("TODO")` 原封不動；Playwright: `expect(true).toBe(false)` hardcode；Cocos: `expect(true).toBe(false)` hardcode）
  [HIGH] 每個 PRD AC 對應的 Scenario 少於 3 個（正常路徑 + 錯誤路徑 + 邊界條件）
  [HIGH] Step Definition 骨架不存在或為空檔（web/html5 類型）
  [MEDIUM] Gherkin 步驟使用技術語言而非業務語言

  **Web SaaS / HTML5 額外維度：**
  [CRITICAL] 缺少 `@responsive` Scenario Outline（未驗證 320/768/1440 三個斷點）
  [HIGH] 缺少 `@a11y` Keyboard Navigation Scenario
  [HIGH] Playwright Step Definition 骨架未生成（`features/client/step_definitions/` 目錄不存在或為空）

  **Unity 額外維度：**
  [CRITICAL] 缺少 Play Mode Test（`[UnityTest]` 方法）
  [HIGH] 缺少 Edit Mode Test（`[Test]` 方法）
  [HIGH] 缺少邊界條件 Test（null 輸入 / 最大值 / 最小值測試）

  **Cocos 額外維度：**
  [CRITICAL] 缺少對應的 Jest `.test.ts` 檔案（只有 Gherkin `.feature` 但無實作）
  [HIGH] Jest describe/it 命名未遵循 BDD 語意（Given/When/Then 結構）

  在輸出最後一行輸出（完全匹配）：
  REVIEW_JSON: {"findings":[{"id":"F1","sev":"CRITICAL","title":"...","fix":"..."}],"total":N}
  若無問題：REVIEW_JSON: {"findings":[],"total":0}

解析 REVIEW_JSON findings；對每個 finding 逐一強制處理（無例外）：
  可修復 → 完整修復對應的 Client BDD 檔案
  無法修復 → 在對應檔案頂部寫入 TODO[REVIEW-DEFERRED] 標記

所有 CRITICAL / HIGH 未修或未 TODO[REVIEW-DEFERRED] 前不得 commit。

**審查通過後輸出摘要：**
```
Client BDD 已生成並通過審查：
  Client 類型：<TYPE>
  Feature Files：<N> 個
  Scenarios：<M> 個（正常路徑 / 錯誤路徑 / 邊界條件 / 平台特定）
  Step Definition 骨架：<K> 個
  覆蓋 PRD AC：<X>/<TOTAL>
  Review findings：CRITICAL=0 HIGH=0（或已 TODO 數量）
```

提交：`test(devsop): generate client BDD features — <client_type> <N> scenarios`
