---
title: gendoc-flow 單步執行模式設計
date: 2026-05-04
version: 1.0
status: 設計文檔（D-SSOT-5.0 前置）
---

# gendoc-flow 單步執行模式設計

## 背景與需求

**現狀**：gendoc-flow 支援「從頭開始」或「從指定步驟開始往後執行」，但無法「只執行某一步驟」。

**需求**：
```bash
# 舊行為（目前支援）
gendoc-flow              # 從頭開始執行全流水線
gendoc-flow --start EDD  # 從 EDD 開始往後執行

# 新行為（需求）
gendoc-flow --only EDD   # 只執行 EDD
gendoc-flow --single EDD # 同上（備選名稱）
```

**使用場景**：
1. **補舊資料**：fishgame 等舊專案缺少 DRYRUN 后的 step 檔案，逐個補齊
2. **修復測試**：D-SSOT-4.3 需要獨立執行某個 step，驗證輸出
3. **repair skill 整合**：gendoc-repair 指揮補充指定 step

---

## 設計原則（缺一不可）

### 1. 單步執行的前置條件
```
input[] 必須全部存在且非空
├─ 必須條件（MUST）：pipeline.json 定義的 input[] 中所有文件都存在
├─ 文件檢查：file size > 0（非空檔案）
└─ 違反條件：報錯退出，列出缺失的檔案
```

### 2. 執行邏輯
```
只執行該步驟的完整 Gen → Review → Fix loop
├─ 不跳過 Gen（即使檔案已存在）
│  └─ 理由：--only 的語義是「重新執行這一步」，不是「補補看」
├─ 執行所有 review rounds（遵循 max_rounds 和 terminate condition）
├─ 最後 commit（同 normal flow）
└─ 不執行後續步驟（執行完該步即結束）
```

### 3. 與 state 的交互
```
執行前檢查：
├─ 若該 step 已在 completed_steps，警告但仍執行（user override）
├─ 清除該 step 的 review_progress 記錄（重新開始）
└─ 同時檢查 condition，條件不符時拒絕執行

執行後更新：
├─ 寫入 completed_steps（如未在）
├─ 寫入 review_progress[step_id]（包含 terminated=true 等）
└─ 保存 state 檔案
```

### 4. 與 condition 的交互
```
條件檢查優先於 input 檢查：

if condition_not_met(step):
    print "[Skip] 條件不符"
    exit 1
elif any_input_missing(step):
    print "[Error] 上游檔案缺失"
    exit 1
else:
    execute_step(step)
```

示例：
```
gendoc-flow --only AUDIO
  client_type = api-only
  → condition = "client_type == game"
  → [Skip] AUDIO 條件不符（client_type != game）
  exit 1

gendoc-flow --only EDD
  input: ["docs/IDEA.md", "docs/BRD.md", "docs/PRD.md"]
  exists: IDEA ✅ BRD ✅ PRD ✅
  → [Execute] EDD 上游齊全
```

---

## 實現清單

### Phase 1：gendoc-flow SKILL.md 修改（中等複雜度）

#### 1.1 參數解析（Step -0.5，在 Step 0 之前）
```bash
# 新增解析邏輯
_SINGLE_STEP=""
_ONLY_STEP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --only)
      _ONLY_STEP="$2"
      shift 2
      ;;
    --single)
      _SINGLE_STEP="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -n "$_ONLY_STEP" ]]; then
  TARGET_STEP="$_ONLY_STEP"
  EXEC_MODE="single-step"
elif [[ -n "$_SINGLE_STEP" ]]; then
  TARGET_STEP="$_SINGLE_STEP"
  EXEC_MODE="single-step"
else
  EXEC_MODE="normal"  # 現有行為
  TARGET_STEP=""
fi

echo "[Setup] EXEC_MODE=${EXEC_MODE} | TARGET_STEP=${TARGET_STEP}"
```

#### 1.2 Step 1 主循環修改
```python
# 在 for step_idx, step in enumerate(pipeline): 前加入判斷

if EXEC_MODE == "single-step":
    # 找到目標 step，只執行它
    target = next((s for s in pipeline if s["id"] == TARGET_STEP), None)
    if not target:
        print(f"[Error] Step '{TARGET_STEP}' 未在 pipeline 中找到")
        exit(1)
    step = target
    pipeline = [target]  # 單步執行列表
```

#### 1.3 Input 驗證（新增，在 execute_step 前）
```python
# 檢查該 step 的所有 input 檔案
def validate_step_inputs(step):
    missing = []
    for input_file in step.get("input", []):
        if not file_exists_and_nonempty(input_file):
            missing.append(input_file)
    
    if missing:
        print(f"[Error] {step['id']} 上游檔案缺失：")
        for m in missing:
            print(f"  ✗ {m}")
        exit(1)
    
    print(f"[Check] {step['id']} 上游檔案完整")
    return True

# 在 EXEC_MODE == "single-step" 時調用
if EXEC_MODE == "single-step":
    validate_step_inputs(target)
```

#### 1.4 Condition 檢查（強化現有邏輯）
```python
# 現有 condition 檢查邏輯保留
# 但在 single-step 模式下，condition 不符時仍要報錯（不是 skip）

if step.get("condition") == "client_type == game" and not _is_game:
    if EXEC_MODE == "single-step":
        print(f"[Error] {step['id']} 執行條件不符：client_type={_CLIENT_TYPE}（需要 game）")
        exit(1)
    else:
        # 正常 flow 的 skip 邏輯（existing）
        _archive_and_skip(...)
```

#### 1.5 Review 記錄清除
```python
# 進入 execute_step 前，清除該 step 的 review_progress
if EXEC_MODE == "single-step":
    state_data = json.load(open(_STATE_FILE))
    if target["id"] in state_data.get("review_progress", {}):
        print(f"[Setup] 清除 {target['id']} 的舊 review 記錄，重新開始")
        del state_data["review_progress"][target["id"]]
        # 原子寫入 state
        save_state(state_data)
```

#### 1.6 執行完成後的行為
```python
# 執行結束後
if EXEC_MODE == "single-step":
    print(f"[Complete] {TARGET_STEP} 單步執行完成")
    print(f"[Next] 下一步手動選擇：")
    print(f"  • 下個 step：gendoc-flow --only NEXT_STEP")
    print(f"  • 全流程：gendoc-flow --start {TARGET_STEP}")
    exit(0)  # 不執行後續步驟
```

---

### Phase 2：gendoc-repair SKILL.md 設計（高複雜度，待後續）

#### 2.1 職責分工
```
gendoc-repair 的角色：「發現問題，指揮修復」

不做：
- 不直接修改文件
- 不呼叫 gen subagent

做：
- 檢查 DRYRUN output 有無生成
- 用 review.sh 判斷缺失的 step
- 指揮 gendoc-flow --only <step> 補充
- 遞迴檢查 input，缺失時呼叫上游
```

#### 2.2 核心邏輯流（Pseudo Code）
```python
def repair(target_project_dir):
    """
    主修復邏輯
    """
    chdir(target_project_dir)
    
    # [R-1] 檢查 DRYRUN 狀態
    dryrun_done = check_dryrun_output_exists()
    
    if not dryrun_done:
        # [R-2] DRYRUN 未執行，檢查其 input（DRYRUN 前的 step）
        missing_dryrun_upstream = check_missing_inputs("DRYRUN")
        
        if "docs/BRD.md" in missing_dryrun_upstream:
            print("[Stop] BRD.md 缺失，無法繼續。需手動建立 BRD.md 或執行 gendoc-auto")
            exit(1)
        
        if missing_dryrun_upstream:
            print(f"[Info] DRYRUN 前置缺失 {len(missing_dryrun_upstream)} 個檔案，正在補充...")
            for missing_file in missing_dryrun_upstream:
                # 從檔案名反推 step_id
                # docs/EDD.md → EDD
                step_id = extract_step_id(missing_file)
                
                # 遞迴補充
                repair_step(step_id)
        
        # [R-3] 執行 DRYRUN
        print("[Action] 執行 DRYRUN...")
        subprocess.run(["gendoc-flow", "--only", "DRYRUN"], check=True)
    
    else:
        print("[Info] DRYRUN 已執行，檢查 DRYRUN 后的 step 檔案...")
    
    # [R-4] DRYRUN 完成，用 review.sh 檢查 DRYRUN 后的 step
    review_result = subprocess.run(
        ["tools/bin/review.sh", "."],
        capture_output=True,
        text=True
    )
    
    if review_result.returncode == 0:
        print("[Complete] ✅ 全部 PASS，修復完成")
        return True
    
    # [R-5] Review 失敗，解析 report 找缺失的 step
    missing_steps = parse_review_report("docs/DRYRUN_REVIEW_REPORT.md")
    
    for step_id in missing_steps:
        print(f"[Action] 補充 {step_id}...")
        subprocess.run(["gendoc-flow", "--only", step_id], check=True)
    
    # [R-6] 循環驗證
    print("[Info] 補充後重新驗證...")
    return repair(target_project_dir)  # 遞迴


def repair_step(step_id):
    """
    補充單個 step
    """
    # 檢查 input 是否齊全
    step = find_step_in_pipeline(step_id)
    missing = check_missing_inputs(step_id)
    
    if missing:
        # 上游缺失，先補上游
        print(f"[Recursive] {step_id} 的上游缺失，正在補充...")
        for missing_file in missing:
            upstream_step = extract_step_id(missing_file)
            if upstream_step == "BRD":
                print(f"[Stop] BRD 缺失，無法補充 {step_id}。")
                raise RuntimeError("BRD.md missing")
            repair_step(upstream_step)
    
    # 上游齊全，執行該 step
    print(f"[Execute] 補充 {step_id}...")
    subprocess.run(["gendoc-flow", "--only", step_id], check=True)


def check_dryrun_output_exists():
    """檢查 DRYRUN 是否已執行"""
    return (
        os.path.isfile("docs/MANIFEST.md") or
        os.path.isdir(".gendoc-rules") or
        glob.glob(".gendoc-rules/*.json")
    )


def check_missing_inputs(step_id):
    """檢查某 step 的 input[] 有無缺失"""
    pipeline = load_pipeline()
    step = find_step_in_pipeline(step_id)
    
    missing = []
    for input_file in step.get("input", []):
        if not os.path.isfile(input_file) or os.path.getsize(input_file) == 0:
            missing.append(input_file)
    
    return missing


def parse_review_report(report_path):
    """
    解析 review.sh 生成的 DRYRUN_REVIEW_REPORT.md
    返回 FAIL 的 step ID 列表
    
    報告格式：
    |Step|Expected|Actual|Status|
    |----|--------|------|------|
    | API | 10 | 8 | ❌ FAIL |
    """
    with open(report_path) as f:
        lines = f.readlines()
    
    failed_steps = []
    for line in lines:
        if "❌ FAIL" in line:
            # 解析第一列的 step ID
            parts = line.split("|")
            if len(parts) >= 2:
                step_id = parts[1].strip()
                failed_steps.append(step_id)
    
    return failed_steps
```

#### 2.3 調用介面（User facing）
```bash
# 在目標專案目錄執行
/gendoc-repair

# 或指定目錄
/gendoc-repair /path/to/project
```

---

## 實現順序（Critical Path）

| Phase | Task | 複雜度 | 優先度 | 時間 |
|-------|------|--------|--------|------|
| 1 | 參數解析 + 單步邏輯 | 中 | 🔴 必須 | 1h |
| 1 | Input 驗證 + Condition 檢查 | 中 | 🔴 必須 | 1h |
| 1 | State 更新邏輯 | 低 | 🟡 需要 | 0.5h |
| 1 | 測試驗證（fishgame） | 中 | 🔴 必須 | 1h |
| 2 | gendoc-repair 設計細化 | 高 | 🟡 後續 | 2h |
| 2 | gendoc-repair 實現 | 高 | 🟡 後續 | 3h |

---

## 驗證檢查清單

### Phase 1 完成後
- [ ] `gendoc-flow --only EDD` 成功執行 EDD
- [ ] `gendoc-flow --only EDD` 檢查 input 是否齐全
- [ ] 缺失 input 時報錯（含檔案名稱）
- [ ] Condition 不符時報錯（如 `--only AUDIO` 在 api-only 專案）
- [ ] State 正確記錄 completed_steps 和 review_progress
- [ ] fishgame 補充一個 missing step（如 CONSTANTS）

### Phase 2 完成後（待後續）
- [ ] `gendoc-repair` 偵測 DRYRUN 未執行
- [ ] 自動識別缺失的 DRYRUN 前的 step 檔案
- [ ] 遞迴補充上游（非 BRD）
- [ ] 執行 DRYRUN，生成 .gendoc-rules/
- [ ] 用 review.sh 驗證 DRYRUN 后的 step
- [ ] 補充缺失 step，循環至全 PASS

---

## 關鍵決策與理由

### 決策 1：--only 不跳過 Gen
**決策**：即使檔案已存在，--only 仍執行完整 Gen → Review → Fix。

**理由**：
- 語義清晰：--only 表示「重新執行這一步」，不是「如果需要則執行」
- 支援修復場景：舊的生成品質差，需要重新生成
- 避免隱晦行為：不會讓使用者困惑為何某個 step 沒有執行

### 決策 2：BRD 缺失時停止
**決策**：BRD 是核心源頭，缺失時 repair 停止，不遞迴補充。

**理由**：
- BRD 是高級別商業文件，只能人工撰寫或由 gendoc-auto 生成
- repair 無法自動生成 BRD（需要業務方輸入）
- 明確的停止點，避免無限递迴或錯誤補充

### 決策 3：Condition 檢查優先於 Input 檢查
**決策**：先檢查條件（client_type 等），條件不符直接拒絕；只有條件符合才檢查 input。

**理由**：
- 語義清晰：「這個 step 在你的專案裡不適用」vs「你缺少前置檔案」
- 避免誤導：不會說「缺 X 檔案」但實際上該 step 根本不該執行
- 効率：減少不必要的檔案檢查

---

## 已知限制與未來擴展

### 限制 1：不支援跨 step 的增量補充
```
gendoc-flow --only API --only SCHEMA  # 不支援，一次只能一個 step
```
**理由**：順序有依賴，需要逐個執行，防止並行導致的競態條件。

### 限制 2：repair 的遞迴深度
如果某 step 的 input 依賴鏈很深（A→B→C→D），repair 需要逐層補充。
目前設計無深度限制，但實務上 DRYRUN 前的 step 層級不深（最多 IDEA→BRD→PRD→EDD）。

---

## 後續任務

**D-SSOT-5.1**：實現 gendoc-flow --only 參數（Phase 1）
- 改 SKILL.md
- 本地測試（fishgame 補充 CONSTANTS.md）
- 驗證 state 更新

**D-SSOT-5.2**：實現 gendoc-repair（Phase 2，待 D-SSOT-5.1 完成）
- 設計 repair SKILL.md
- 實現 review report 解析
- 整合測試（fishgame 完整補齊）

