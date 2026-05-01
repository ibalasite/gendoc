---
name: reviewtemplate
description: |
  Template quality review & fix loop.
  輸入 TYPE（如 AUDIO、ANIM、EDD），對三件套 templates/{TYPE}.md +
  {TYPE}.gen.md + {TYPE}.review.md 執行：
    Template Architect Review subagent → Fix subagent（finding > 0 時）→
    Round summary → loop 直到 finding = 0 或達 max_rounds
  最終輸出 Total Summary。
  呼叫：/reviewtemplate AUDIO
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# reviewtemplate — Template Quality Review & Fix Loop

```
用途：review 並 iteratively fix 一組 gendoc template 三件套
      templates/{TYPE}.md        — 文件結構骨架
      templates/{TYPE}.gen.md    — AI 生成規則
      templates/{TYPE}.review.md — 審查標準
直到 finding = 0，確保任何 /gendoc TYPE 和 /reviewdoc TYPE 執行時
生成品質有保證。
```

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：解析 TYPE 參數

```bash
_TYPE="${1:-}"   # 由 skill 呼叫時傳入，如 "AUDIO"、"ANIM"、"EDD"

# 若無 TYPE 參數，詢問使用者
if [[ -z "$_TYPE" ]]; then
  echo "用法：/reviewtemplate <TYPE>"
  echo "範例：/reviewtemplate AUDIO"
  echo ""
  echo "可用的 template 類型："
  ls templates/*.md 2>/dev/null \
    | grep -v '\.gen\.md$' \
    | grep -v '\.review\.md$' \
    | sed 's|templates/||;s|\.md$||' \
    | grep -v '^pipeline$' \
    | grep -v 'GUIDE' \
    | sort \
    | sed 's/^/  /'
  exit 1
fi

_TEMPLATE_DIR="$(pwd)/templates"
_MD="${_TEMPLATE_DIR}/${_TYPE}.md"
_GEN="${_TEMPLATE_DIR}/${_TYPE}.gen.md"
_REVIEW="${_TEMPLATE_DIR}/${_TYPE}.review.md"

echo "[reviewtemplate] TYPE: ${_TYPE}"
echo "[Check] ${_TYPE}.md      → $([ -f "$_MD" ]     && echo '✅ 存在' || echo '❌ 不存在')"
echo "[Check] ${_TYPE}.gen.md  → $([ -f "$_GEN" ]    && echo '✅ 存在' || echo '❌ 不存在')"
echo "[Check] ${_TYPE}.review.md → $([ -f "$_REVIEW" ] && echo '✅ 存在' || echo '❌ 不存在')"

_MISSING=0
[[ ! -f "$_MD" ]]     && echo "[錯誤] templates/${_TYPE}.md 不存在"     && _MISSING=1
[[ ! -f "$_GEN" ]]    && echo "[錯誤] templates/${_TYPE}.gen.md 不存在" && _MISSING=1
[[ ! -f "$_REVIEW" ]] && echo "[錯誤] templates/${_TYPE}.review.md 不存在" && _MISSING=1
[[ $_MISSING -eq 1 ]] && exit 1
```

---

## Step 0-B：讀取 Review 策略

```bash
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

_MAX_ROUNDS=$(python3 -c "
import json
try: print(int(json.load(open('${_STATE_FILE}')).get('max_rounds', 5)))
except: print(5)
" 2>/dev/null || echo "5")

_REVIEW_STRATEGY=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('review_strategy','standard'))
except: print('standard')
" 2>/dev/null || echo "standard")

echo "[Config] strategy=${_REVIEW_STRATEGY}  max_rounds=${_MAX_ROUNDS}"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  reviewtemplate — ${_TYPE} 三件套審查                   ║"
echo "╠══════════════════════════════════════════════════════╣"
printf "║  %-10s %-40s ║\n" "審查對象" "${_TYPE}.md + .gen.md + .review.md"
printf "║  %-10s %-40s ║\n" "策略" "${_REVIEW_STRATEGY}（最多 ${_MAX_ROUNDS} 輪）"
echo "╚══════════════════════════════════════════════════════╝"
```

---

## Step 1：Review → Fix Loop

主 Claude 執行以下 loop（最多 `_MAX_ROUNDS` 輪）：

### Loop 核心邏輯（pseudo-code）

```python
for round in range(1, max_rounds + 1):

    # ── Review Subagent ───────────────────────────────────
    review_result = spawn_review_agent(TYPE, round)

    finding_total = review_result["finding_total"]
    critical      = review_result["critical"]
    high          = review_result["high"]
    medium        = review_result["medium"]
    low           = review_result["low"]

    # ── 判斷終止條件 ──────────────────────────────────────
    terminate = False
    terminate_reason = ""

    if finding_total == 0:
        terminate = True
        terminate_reason = "PASSED — finding = 0"
    elif review_strategy == "tiered" and round >= 6 and (critical + high + medium) == 0:
        terminate = True
        terminate_reason = "PASSED — tiered: CRITICAL+HIGH+MEDIUM = 0"
    elif round >= max_rounds:
        terminate = True
        terminate_reason = f"MAX_ROUNDS = {max_rounds} 已達"
    elif review_strategy == "rapid" and round >= 3:
        terminate = True
        terminate_reason = "MAX_ROUNDS — rapid = 3 已達"

    # ── Fix Subagent（finding > 0 時必執行，不跳過）──────
    fix_result = None
    if finding_total > 0:
        fix_result = spawn_fix_agent(TYPE, round, review_result["findings"])
        unfixed_count = len(fix_result.get("unfixed", []))
        fixed_count   = len(fix_result.get("fixed", []))
    else:
        unfixed_count = 0
        fixed_count   = 0

    # ── Round Summary ─────────────────────────────────────
    status_icon = "✅ PASS" if finding_total == 0 else (
                  "⚠️  MAX" if terminate else "🔄 CONT")
    print(f"""
┌─── {TYPE} template Round {round}/{max_rounds} ─────────────────────────────┐
│  Review：CRITICAL={critical} HIGH={high} MEDIUM={medium} LOW={low}  Total={finding_total}
│  Fix：   修復 {fixed_count} 個 / 殘留 {unfixed_count} 個
│  本輪狀態：{status_icon}  {terminate_reason if terminate else '繼續下一輪'}
│  Fix summary：{fix_result['summary'] if fix_result else 'N/A（finding=0，無需修復）'}
└─────────────────────────────────────────────────────────────────────┘""")

    # ── 終止 ──────────────────────────────────────────────
    if terminate:
        break
```

---

### Review Subagent Prompt

主 Claude 用 **Agent tool** 派送，prompt：

```
你是 Template Architect（資深 gendoc 模板設計師）。
你的職責是審查 gendoc template 三件套的設計品質，確保任何人呼叫
/gendoc {TYPE} 和 /reviewdoc {TYPE} 時，生成的文件品質有可靠保證。

**本次審查對象：**
  templates/{TYPE}.md
  templates/{TYPE}.gen.md
  templates/{TYPE}.review.md

**審查角色：三角聯合審查**
- Template Architect：評估三件套整體一致性、覆蓋完整性、可操作性
- Gen Expert：評估 {TYPE}.gen.md 生成規則是否足夠精確，讓 AI 能產出無 placeholder 的完整文件
- Review Design Expert：評估 {TYPE}.review.md 的審查項目是否覆蓋 {TYPE}.md 所有章節，
  CRITICAL/HIGH 是否正確分級，Fix 指引是否可操作

**執行步驟（不得跳過）：**
1. 讀取 templates/{TYPE}.md — 理解文件結構，列出所有 §章節
2. 讀取 templates/{TYPE}.gen.md — 審查生成規則完整性
3. 讀取 templates/{TYPE}.review.md — 審查審查標準完整性

**Template Architect 審查標準（必查項）：**

### A. {TYPE}.md 結構審查
- [ ] A-1: 每個 §章節名稱和用途是否清晰（非模糊的「其他」「備注」）？
- [ ] A-2: 是否有重要的 {{PLACEHOLDER}} 說明（讓 gen agent 知道填什麼）？
- [ ] A-3: 表格/清單的欄位是否完整（無遺漏的關鍵欄位）？
- [ ] A-4: 是否有程式碼範例（若文件類型涉及技術實作）？
- [ ] A-5: 文件章節數量是否足夠（≥ 5 個實質章節）？

### B. {TYPE}.gen.md 生成規則審查
- [ ] B-1: 是否有 Iron Law 聲明（生成前必讀 TYPE.md + TYPE.gen.md）？
- [ ] B-2: 是否有明確的專家角色定義（≥ 2 個角色，含職責範圍）？
- [ ] B-3: 是否有完整的必讀上游鏈表格（upstream-docs 對應 {TYPE}.md frontmatter）？
- [ ] B-4: 是否有逐 §章節的生成步驟（Step 1~N，對應 TYPE.md 各章節）？
- [ ] B-5: 是否有引擎/技術棧偵測規則（若文件涉及多引擎）？
- [ ] B-6: 是否有品質門（Quality Gate）自我檢查清單（生成後驗證）？
- [ ] B-7: YAML frontmatter 的 quality-bar 是否有具體可驗證的條件？
- [ ] B-8: 是否明確要求「禁止保留 {{PLACEHOLDER}}」？
- [ ] B-9: 是否有上游衝突偵測規則？

### C. {TYPE}.review.md 審查標準審查
- [ ] C-1: 是否有 YAML frontmatter（reviewer-roles + quality-bar + upstream-alignment）？
- [ ] C-2: 是否有 CRITICAL 級別的審查項目（≥ 2 個）？
- [ ] C-3: CRITICAL/HIGH/MEDIUM/LOW 分級是否合理（CRITICAL = 不修就無法使用）？
- [ ] C-4: {TYPE}.md 的每個主要 §章節是否至少有 1 個對應審查項目？
- [ ] C-5: 每個審查項目是否包含：Check + Risk + Fix 三段（缺一視為不完整）？
- [ ] C-6: 是否有覆蓋「效能預算含裸 placeholder」的審查項（若涉及效能）？
- [ ] C-7: 是否有覆蓋「引擎 API 版本正確性」的審查項（若涉及多引擎）？
- [ ] C-8: upstream-alignment 是否列出所有關鍵上游對齊點？

### D. 三件套章節引用對齊審查（Section Number Alignment）

**背景**：歷史上 EDD.gen.md 曾出現 §4.5=Domain Events、§10=UML 的錯誤，而骨架 EDD.md 實際是 §4.5=UML、§10=Observability。此錯置導致 AI 把 UML 生成在錯誤的章節位置。此類別專門檢查三件套之間的章節號一致性。

**執行步驟**：
1. 從 {TYPE}.md 提取所有主要章節（`## N. 章節名` 或 `## §N 章節名`）→ 建立「骨架章節表」
2. 從 {TYPE}.gen.md 的「章節結構 / Key Fields / TOC」區段提取所有 §N 引用 → 對照骨架
3. 從 {TYPE}.review.md 提取所有審查項目中的 §N 引用 → 對照骨架

- [ ] D-1: {TYPE}.gen.md 的章節結構 TOC 中，每個 §N 所描述的內容是否與骨架 §N 的標題一致？
  - 若 gen.md 說「§4 UML 圖」但骨架 §4 是「服務邊界」→ 判定為 CRITICAL 錯置
- [ ] D-2: {TYPE}.gen.md 中是否存在重複的 §N（同一節號出現兩次描述不同內容）？
  - 重複 §N 必然會讓 AI 混淆要在哪裡生成什麼 → CRITICAL
- [ ] D-3: {TYPE}.gen.md 的 Key Fields / ### §N 詳細規則，其 §N 是否與骨架的實際位置一致？
  - 若 gen.md Key Fields 說「### §1 ADR Index」但骨架 §1 是「架構目標」→ CRITICAL
- [ ] D-4: {TYPE}.review.md 的審查項目中引用的 §N，是否與骨架實際位置一致？
  - 若 review.md 說「檢查 §10 的 UML 圖」但骨架 §10 是「Observability」→ HIGH
- [ ] D-5: {TYPE}.gen.md 的章節結構是否引用了骨架中不存在的 §N？
  - 若 gen.md 說 §17 但骨架最多到 §16 → HIGH（孤立的幻影章節）

**判斷方法**：
```
骨架 §N 章節表（從 {TYPE}.md 提取）：
  §1 = [標題A]
  §2 = [標題B]
  ...

Gen.md TOC 引用（從 {TYPE}.gen.md 章節結構 / Key Fields 提取）：
  §1 = [Gen說的內容X]  → 比對骨架 §1=[標題A]：一致 / 不一致
  §2 = [Gen說的內容Y]  → 比對骨架 §2=[標題B]：一致 / 不一致
  ...

不一致 → D-1 CRITICAL
重複§N → D-2 CRITICAL
§N不存在於骨架 → D-5 HIGH
```

**完成後必須輸出（格式嚴格）：**
TEMPLATE_REVIEW_RESULT:
  type: {TYPE}
  round: {round}
  finding_total: N
  critical: N
  high: N
  medium: N
  low: N
  passed: true|false
  findings:
    - id: TF-{N:02d}
      severity: CRITICAL|HIGH|MEDIUM|LOW
      file: "{TYPE}.md | {TYPE}.gen.md | {TYPE}.review.md"
      check_ref: "A-N | B-N | C-N"
      section: "§X.Y 或 frontmatter 或 Step N"
      issue: "具體問題描述（引用 template 中的具體內容）"
      fix_guide: "如何修復（精確到要加什麼內容、修改哪一段）"
```

---

### Fix Subagent Prompt

```
你是 Template Fix Expert（gendoc 模板修復專家）。

任務：依照以下 findings，精準修復 template 三件套。

本輪 Findings（Round {round}，共 {finding_total} 個）：
{findings_text}

被修復的文件：
  templates/{TYPE}.md
  templates/{TYPE}.gen.md
  templates/{TYPE}.review.md

**執行步驟（不得跳過）：**
1. 讀取每個 finding 對應的 file + section
2. 讀取對應 template 檔案的相關段落
3. 執行精準修復：
   - CRITICAL + HIGH：必須修復，不得跳過
   - MEDIUM + LOW：盡力修復
   - 只修改 finding 指出的具體位置
   - 不修改 finding 未提及的部分（最小修改原則）
   - 保持 template 整體風格、章節命名、frontmatter 格式不變
4. 修復後重讀修復段落，確認問題已解決

**常見修復模式：**
- B-1（缺 Iron Law）→ 在 gen.md 加入：
  > **Iron Law**：生成任何 {TYPE}.md 之前，必須先讀取 `{TYPE}.md`（結構）和 `{TYPE}.gen.md`（本規則）。
- B-4（缺生成步驟）→ 加入 Step N 章節，逐 §章節說明生成指引
- B-6（缺 Quality Gate）→ 加入品質門表格 + 警告區塊模板
- C-5（缺 Fix 段落）→ 在審查項目末尾加入 **Fix**: 行
- C-2（CRITICAL 不足）→ 將最高風險的 HIGH 升級為 CRITICAL，並加入 Risk 說明
- D-1（章節錯置）→ 步驟：(1) 讀取 {TYPE}.md 確認骨架實際章節號 (2) 在 gen.md 章節結構 TOC 中找到錯誤的 §N (3) 修正為正確 §N 及正確內容描述 (4) 同步修正 Key Fields 中的 ### §N 標題
- D-2（重複 §N）→ 讀取骨架確認該 §N 的真正內容，保留正確的描述，刪除或重新編號錯誤的那個
- D-3（Key Fields §N 錯置）→ 讀取骨架確認正確位置，修改 ### §N 標題及內部描述對應到正確骨架章節
- D-4（review.md §N 錯置）→ 讀取骨架確認正確 §N，在 review.md 中找到並修正對應審查項的 §N 引用
- D-5（幻影 §N）→ 讀取骨架確認最大 §N，若 gen.md 引用超出範圍的 §N，刪除或修改為骨架實際存在的 §N

**完成後必須輸出：**
TEMPLATE_FIX_RESULT:
  type: {TYPE}
  round: {round}
  fixed:
    - id: TF-{N:02d}
      file: "{TYPE}.gen.md"
      action: "具體修復說明（在 §N 加入了什麼內容）"
  unfixed:
    - id: TF-{N:02d}
      reason: "無法修復的原因（若有）"
  summary: "一句話：本輪共修復 N 個 findings，主要修復了 ..."
```

---

## Step 2：Total Summary

loop 結束後輸出：

```
╔══════════════════════════════════════════════════════════════════╗
║  reviewtemplate — {TYPE} 三件套審查完成                           ║
╠══════════════════════════════════════════════════════════════════╣
║  審查文件：{TYPE}.md + {TYPE}.gen.md + {TYPE}.review.md          ║
║  審查輪次：{rounds_completed} 輪（最大 {max_rounds}）             ║
║  終止原因：{terminate_reason}                                    ║
║  最終 Findings：CRITICAL={c} HIGH={h} MEDIUM={m} LOW={l}         ║
╠══════════════════════════════════════════════════════════════════╣
║  各輪 Findings 趨勢：                                            ║
║    初始→ R1:{r1} → R2:{r2} → ... → Rn:{rn}（目標：0）           ║
╠══════════════════════════════════════════════════════════════════╣
║  主要改善項目：                                                   ║
║    {改善摘要列表，每行一條}                                       ║
╚══════════════════════════════════════════════════════════════════╝
```

**依終止原因輸出建議：**

```python
if terminate_reason == "PASSED":
    print("""
✅ 三件套品質達標。
   可安心執行：/gendoc {TYPE}  ←  生成此類文件
               /reviewdoc {TYPE}  ←  生成後審查
   建議：執行 /gendoc-upgrade 同步到 ~/.claude/skills/""")

elif terminate_reason.startswith("MAX_ROUNDS"):
    print(f"""
⚠️  達最大輪次（{max_rounds}），仍有 CRITICAL/HIGH findings 殘留。
   建議：/gendoc-config → 選 exhaustive 策略 → 重跑 /reviewtemplate {TYPE}
   殘留 findings：{[f for f in findings if f.severity in ('CRITICAL','HIGH')]}""")
```

---

## 附錄：常見 Template 問題速查

| 問題 | 所在檔案 | 嚴重度 | 快速修法 |
|------|---------|-------|---------|
| 缺 Iron Law 聲明 | .gen.md | CRITICAL | 在 ## Iron Rule 後加 **Iron Law** blockquote |
| 無 Quality Gate | .gen.md | HIGH | 加入品質門表格（6~10 行自我檢查） |
| CRITICAL 審查項 < 2 | .review.md | HIGH | 將最高風險 HIGH 升為 CRITICAL，補 Risk |
| 審查項缺 Fix 指引 | .review.md | HIGH | 每項補 **Fix**: 一行 |
| §章節未被審查覆蓋 | .review.md | MEDIUM | 加入對應 layer 的審查項 |
| 上游鏈不完整 | .gen.md | MEDIUM | 比對 frontmatter upstream-docs，補缺漏的上游 |
| frontmatter quality-bar 太模糊 | .gen.md | MEDIUM | 改為可驗證的具體條件（如「§9 所有數值非 placeholder」） |
| gen.md §N 與骨架 §N 內容不一致（錯置） | .gen.md | CRITICAL | 讀骨架確認正確 §N，修正 gen.md TOC + Key Fields 對應位置 |
| gen.md 同一 §N 出現兩次（重複）| .gen.md | CRITICAL | 保留正確描述，刪除或重編號錯誤條目 |
| review.md §N 引用與骨架不一致 | .review.md | HIGH | 讀骨架確認正確 §N，修正 review.md 審查項引用 |
| gen.md 引用骨架不存在的 §N（幻影）| .gen.md | HIGH | 刪除幻影 §N 或對應到骨架實際存在的章節 |
