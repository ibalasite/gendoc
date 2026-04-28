---
name: gendoc-rebuild-templates
description: |
  全量重建 templates/ 目錄下所有 *.review.md（審查標準）、驗證 *.gen.md（生成規則）
  與審查 *.md（結構模板）。依文件管線順序、平行派送 Agent 執行，確保每份 review.md
  ≥ 20 項、≥ 4 層、有 Check/Risk/Fix 格式。
  呼叫時機：
    - 新增文件類型後需同步建立 review.md
    - 審查標準老化需全量刷新
    - 重大 pipeline 架構調整後重新驗證累積上游
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
---

# gendoc-rebuild-templates — 模板全量重建

執行環境：目前所在目錄（`$CWD`）的 `templates/` 子目錄。

---

## Iron Laws

1. **每份 *.review.md 必須**：≥ 20 review items、≥ 4 layers、每項有 Check / Risk / Fix 三段、frontmatter 含 `doc-type`、`reviewer-roles`、`upstream-alignment`、`quality-bar`。
2. **每份 *.gen.md 必須**：frontmatter 含完整 `upstream-docs`（累積上游清單）、`## Iron Rule: 累積上游讀取` 章節、IDEA.md Appendix C / `docs/req/` 特殊處理說明、章節 Section Rules、Self-Check Checklist。
3. **Gold standards**（不可降低）：`templates/runbook.review.md`（20 items，4 layers）、`templates/FRONTEND.review.md`（26 items，6 layers）。所有新建/重建 review.md 以這兩份為參考基準。
4. **累積上游原則**：每份文件讀取 **所有** 上游文件，不僅是直接上游。詳見 Step 1。

---

## Step 0：掃描現有 templates/

> **新增文件類型標準流程（不需修改任何 skill 檔案）：**
> 1. 建立 `templates/NEW_TYPE.md`（結構模板）
> 2. 建立 `templates/NEW_TYPE.gen.md`（生成規則）
> 3. 建立 `templates/NEW_TYPE.review.md`（審查標準）
> 4. 在 `templates/pipeline.json` 的 `steps` 陣列中加入新步驟（指定 id/layer/output/condition）
> 5. 執行 `./install.sh`
> 無需修改 gendoc-auto、gendoc-flow、gendoc、reviewdoc 任何 skill 檔案。

```bash
_TDIR="$(pwd)/templates"

echo "=== pipeline.json 步驟清單 ==="
python3 -c "
import json
p = json.load(open('$_TDIR/pipeline.json'))
for s in p['steps']:
    print(f\"  {s['id']:<20} {s['layer']:<6} cond={s['condition']}\")
" 2>/dev/null || echo "  (pipeline.json 不存在)"

echo ""
echo "=== *.md 結構模板 ==="
ls "$_TDIR"/*.md | grep -v '\.gen\.md\|\.review\.md\|pipeline' | sort

echo ""
echo "=== *.gen.md 生成規則 ==="
ls "$_TDIR"/*.gen.md | sort

echo ""
echo "=== *.review.md 審查標準 ==="
ls "$_TDIR"/*.review.md | sort

echo ""
echo "=== 缺少 review.md 的類型 ==="
for md in "$_TDIR"/*.md; do
  base=$(basename "$md" .md)
  [[ "$base" == *".gen"* || "$base" == *".review"* ]] && continue
  [[ ! -f "$_TDIR/${base}.review.md" ]] && echo "  ❌ 缺 ${base}.review.md"
done

echo ""
echo "=== 缺少 gen.md 的類型 ==="
for md in "$_TDIR"/*.md; do
  base=$(basename "$md" .md)
  [[ "$base" == *".gen"* || "$base" == *".review"* ]] && continue
  [[ ! -f "$_TDIR/${base}.gen.md" ]] && echo "  ❌ 缺 ${base}.gen.md"
done
```

---

## Step 1：文件管線定義（累積上游鏈）

以下是完整管線與每份文件應讀取的上游：

| 文件類型 | 累積上游（由近到遠） |
|----------|---------------------|
| IDEA | `docs/req/`（所有 input 檔） |
| BRD | `docs/req/` + IDEA.md |
| PRD | `docs/req/` + IDEA + BRD |
| PDD | `docs/req/` + IDEA + BRD + PRD |
| VDD | `docs/req/` + IDEA + BRD + PRD + PDD |
| EDD | `docs/req/` + IDEA + BRD + PRD + PDD + VDD |
| ARCH | `docs/req/` + IDEA + BRD + PRD + PDD + VDD + EDD |
| API | `docs/req/` + IDEA + BRD + PRD + PDD + VDD + EDD + ARCH |
| SCHEMA | `docs/req/` + IDEA + BRD + PRD + PDD + VDD + EDD + ARCH + API |
| test-plan | `docs/req/` + IDEA ~ VDD + SCHEMA |
| BDD | `docs/req/` + IDEA ~ VDD + test-plan |
| RTM | `docs/req/` + PRD + test-plan + BDD（RTM 是需求追溯矩陣，橫跨整個管線） |
| runbook | `docs/req/` + IDEA ~ EDD（運維文件參考架構層） |
| LOCAL_DEPLOY | `docs/req/` + IDEA + EDD + ARCH + runbook |
| ALIGN_REPORT | 全部文件（對齊掃描用） |
| README | 全部文件（摘要彙整） |
| FRONTEND | `docs/req/` + IDEA + BRD + PRD + PDD + VDD + EDD + API |

**IDEA 特殊規則**（所有 gen.md 必須記載）：
> IDEA.md 本身是上游入口，其 Appendix C 列出了 `docs/req/` 目錄下所有參考檔案的清單。
> 讀到 IDEA.md 時，**同時讀取** Appendix C 提及的所有 `docs/req/` 檔案，
> 這些檔案包含使用者原始輸入與業界參考資料，是最原始的上游資訊來源。

---

## Step 2：Review.md 品質標準

每份 *.review.md 必須包含：

### Frontmatter（YAML）
```yaml
---
doc-type: <TYPE>
target-path: docs/<TYPE>.md
reviewer-roles:
  primary: "<領域>專家（主審，共 N 項）"
  primary-scope: "<審查範圍>"
  secondary: "<領域>專家"
  secondary-scope: "<範圍>"
  tertiary: "<領域>專家"           # 若適用
  tertiary-scope: "<範圍>"
quality-bar: "<一句話：達到什麼標準才算合格>"
upstream-alignment:
  - field: <欄位名>
    source: <上游文件>.md §<章節>
    check: <對齊檢查說明>
---
```

### 必要章節結構
```markdown
# <TYPE> Review Items

本檔案定義 `docs/<TYPE>.md` 的審查標準。由 `/reviewdoc <TYPE>` 讀取並遵循。
審查角色：...
審查標準：「假設公司聘請一位 10 年以上資深...顧問，以最嚴格的業界標準進行...驗收審查。」

---

## Review Items

### Layer 1: <層名>（由 <角色> 主審，共 N 項）

#### [CRITICAL|HIGH|MEDIUM|LOW] N — <問題名稱>
**Check**: <具體检查點，引用文件§章節>
**Risk**: <若不修正，後果是什麼>
**Fix**: <具體修復方式>

...（重複至所有 items）

---

## Escalation Protocol

- **CRITICAL**：任一 CRITICAL 項目未通過 → 停止審查，立即修正後重審
- **HIGH**：≥ 3 項 HIGH 未通過 → 視為高風險，建議回頭修正再繼續
- **MEDIUM/LOW**：累計記錄，不阻擋流程

---

## Completion Criteria

- 所有 CRITICAL 項目通過 ✅
- HIGH 未通過項目 < 3 ✅
- 上游對齊欄位全部確認 ✅
- 文件輸出可直接交付下游 ✅

> 由 `/reviewdoc <TYPE>` 自動執行本 checklist。
```

---

## Step 3：Gen.md 品質標準

每份 *.gen.md 必須包含：

### Frontmatter
```yaml
---
doc-type: <TYPE>
output-path: docs/<TYPE>.md
upstream-docs:
  - docs/req/
  - docs/IDEA.md
  - docs/BRD.md
  # ... 全部累積上游
quality-bar: "<quality bar>（與 review.md 一致）"
---
```

### 必要章節
1. `## Iron Rule：累積上游讀取`（說明必須讀取所有上游，IDEA Appendix C 特殊處理）
2. `## 上游文件優先順序表`（每份上游文件 + 對應 §章節 + 用途說明）
3. `## IDEA Appendix C 特殊處理`（明確說明如何讀取 docs/req/ 清單）
4. `## Key Fields（欄位提取表）`（必填欄位、來源、推斷規則）
5. `## Section Rules`（每章節的生成規則，禁止跳過任何章節）
6. `## Inference Rules`（衍生欄位推斷邏輯）
7. `## Self-Check Checklist`（≥ 10 項自我檢核）

---

## Step 4：派送平行 Agent 執行重建

**[AI 指令]** 使用 `Agent` 工具，以以下分組派送平行 Agent 任務：

### 分組 A：IDEA + BRD review.md（新建 / 重建）
```
任務：讀取 IDEA.md/BRD.md 結構模板與現有 gen.md，
      對照 runbook.review.md / FRONTEND.review.md 品質標準，
      重建 IDEA.review.md（IDEA 特殊：無上游，檢查 Appendix C vs docs/req/ 一致性）
      和 BRD.review.md（上游對齊：7 個 IDEA→BRD 欄位）。
      每份 ≥ 24 items，6 layers，全 Check/Risk/Fix。
```

### 分組 B：PRD + PDD review.md
```
任務：PRD.review.md（22+ items，5 layers，上游對齊：IDEA+BRD）
      PDD.review.md（21+ items，6 layers，上游對齊：PRD+BRD）
```

### 分組 B.5：VDD review.md
```
任務：VDD.review.md（22+ items，4 layers，上游對齊：PDD+PRD）
      確認視覺設計 → 工程交付 bridge 完整性
      Layer 1：Brand Identity & Art Direction 審查（設計方向是否與 PDD/PRD 一致）
      Layer 2：Design Token 系統完整性（CSS 變數命名規範、Token 層級結構）
      Layer 3：Asset Pipeline 規格（圖片格式/壓縮比/命名慣例/CDN 路徑）
      Layer 4：元件視覺規格可工程化性（圓角/陰影/動畫 Easing 是否有精確數值）
```

### 分組 C：EDD + ARCH review.md
```
任務：EDD.review.md（24 items，6 layers，上游對齊：PRD+BRD+PDD）
      ARCH.review.md（23 items，6 layers，上游對齊：EDD+PRD）
```

### 分組 D：API + SCHEMA review.md
```
任務：API.review.md（24+ items，6 layers，上游對齊：EDD+ARCH+PRD）
      SCHEMA.review.md（20+ items，5 layers，上游對齊：EDD+API+PRD）
```

### 分組 E：test-plan + BDD-server + BDD-client review.md
```
任務：test-plan.review.md（22+ items，5 layers，上游對齊：PRD+EDD+BDD）
      BDD-server.review.md（20+ items，4 layers）
      BDD-client.review.md（20+ items，4 layers）
```

### 分組 F：ALIGN_REPORT + README + RTM 三件套
```
任務：ALIGN_REPORT.review.md（18+ items，5 layers）
      README.review.md（16+ items，4 layers）
      RTM.gen.md（全量重建：累積上游 PRD+test-plan+BDD，IDEA Appendix C 處理）
      RTM.review.md（20+ items，5 layers）
      驗證 runbook.gen.md 和 LOCAL_DEPLOY.gen.md 的累積上游完整性
```

### 分組 G：全量結構模板（*.md）審查
```
任務：讀取所有 *.md 結構模板，
      確認每份都有 Document Control 表格、Change Log 區塊、
      所有章節序號連續、無遺漏節（特別注意 IDEA.md §8.x 序號）。
      對各文件類型，以對應領域專家視角（BA/PM/UX/Architect/SRE）
      審查章節合理性與完整性。
```

### 分組 H：FRONTEND 三件套一致性審查
```
任務：讀取 FRONTEND.md、FRONTEND.gen.md、FRONTEND.review.md，
      確認無殘留 CLIENT 舊名引用、三件套內部一致性（gen.md upstream 涵蓋 PDD+EDD+API、
      review.md reviewer roles 與 gen.md 一致）。
```

---

## Step 5：自我驗證清單

所有 Agent 完成後，執行以下驗證：

```bash
echo "=== review.md 行數統計 ==="
for f in $_CWD/templates/*.review.md; do
  lines=$(wc -l < "$f")
  name=$(basename "$f")
  if [[ $lines -lt 100 ]]; then
    echo "  ⚠️  $name: ${lines} 行（過少，需重建）"
  else
    echo "  ✅ $name: ${lines} 行"
  fi
done

echo ""
echo "=== gen.md Iron Rule 存在性 ==="
for f in $_CWD/templates/*.gen.md; do
  name=$(basename "$f")
  if grep -q "Iron Rule" "$f"; then
    echo "  ✅ $name: Iron Rule 存在"
  else
    echo "  ❌ $name: 缺 Iron Rule（需修正）"
  fi
done

echo ""
echo "=== gen.md upstream-docs 完整性 ==="
for f in $_CWD/templates/*.gen.md; do
  name=$(basename "$f")
  if grep -q "upstream-docs" "$f"; then
    echo "  ✅ $name: upstream-docs 存在"
  else
    echo "  ❌ $name: 缺 upstream-docs（需修正）"
  fi
done

echo ""
echo "=== IDEA Appendix C 特殊處理 ==="
for f in $_CWD/templates/*.gen.md; do
  name=$(basename "$f")
  if grep -qi "appendix c\|docs/req" "$f"; then
    echo "  ✅ $name: IDEA/req 特殊處理存在"
  else
    echo "  ⚠️  $name: 未提及 docs/req（若為 IDEA.gen.md 以下，需確認）"
  fi
done
```

---

## Step 6：安裝同步

```bash
if [[ -f "./install.sh" ]]; then
  ./install.sh
  echo "✅ 技能已同步至 ~/.claude/skills/"
else
  echo "ℹ️  非 gendoc 開發目錄，略過 install.sh"
fi
```

---

## Step 7：輸出摘要

```
╔══════════════════════════════════════════════════════════╗
║  /gendoc-rebuild-templates 完成                           ║
╠══════════════════════════════════════════════════════════╣
║  重建 review.md：<N> 份（全通過 ≥ 20 items / ≥ 4 layers）║
║  驗證 gen.md：<N> 份（累積上游鏈完整）                    ║
║  審查 *.md 結構：<N> 份（Document Control 完整）           ║
║  安裝：install.sh 執行完成                                ║
╚══════════════════════════════════════════════════════════╝

建議下一步：執行 /gendoc-auto 從 D01-IDEA 全量生成文件套件。
```
