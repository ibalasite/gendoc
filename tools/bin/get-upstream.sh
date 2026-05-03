#!/bin/bash
# get-upstream.sh — 讀取 pipeline.json 的 input，返回檔案內容 JSON
# 用法：get-upstream --step DRYRUN --output json

set -euo pipefail

# 參數解析
STEP_ID=""
OUTPUT_FORMAT="json"

while [[ $# -gt 0 ]]; do
  case $1 in
    --step)
      STEP_ID="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FORMAT="$2"
      shift 2
      ;;
    *)
      echo "❌ Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$STEP_ID" ]]; then
  echo "❌ --step 參數必填" >&2
  exit 1
fi

# 確認目錄（必須在目標項目目錄執行）
if [[ ! -f ".gendoc-state.json" ]] && [[ ! -f ".gendoc-state-"*.json ]]; then
  echo "❌ Not in a gendoc target project directory (missing .gendoc-state.json)" >&2
  exit 1
fi

# 查找 pipeline.json（優先本地，其次 ~/.claude/skills/gendoc/templates/）
PIPELINE_JSON=""
if [[ -f "templates/pipeline.json" ]]; then
  PIPELINE_JSON="templates/pipeline.json"
elif [[ -f "$HOME/.claude/skills/gendoc/templates/pipeline.json" ]]; then
  PIPELINE_JSON="$HOME/.claude/skills/gendoc/templates/pipeline.json"
else
  echo "❌ pipeline.json not found in templates/ or ~/.claude/skills/gendoc/templates/" >&2
  exit 1
fi

# 用 Python 讀 pipeline.json 並提取 input
read_input_from_pipeline() {
  python3 << 'PYTHON_EOF'
import json
import sys

pipeline_file = sys.argv[1]
step_id = sys.argv[2]

try:
  with open(pipeline_file, 'r', encoding='utf-8') as f:
    pipeline = json.load(f)

  # 查找該 step
  for step in pipeline.get('steps', []):
    if step.get('id') == step_id:
      input_files = step.get('input', [])
      print('\n'.join(input_files))
      sys.exit(0)

  print(f"❌ Step '{step_id}' not found in pipeline.json", file=sys.stderr)
  sys.exit(1)
except Exception as e:
  print(f"❌ Error reading pipeline.json: {e}", file=sys.stderr)
  sys.exit(1)
PYTHON_EOF
}

# 讀 input 清單
INPUT_FILES=$(read_input_from_pipeline "$PIPELINE_JSON" "$STEP_ID")

if [[ -z "$INPUT_FILES" ]]; then
  echo "❌ No input files defined for step '$STEP_ID'" >&2
  exit 1
fi

# 讀檔案內容並組成 JSON
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 構建 JSON（使用 Python 以避免 Bash JSON 複雜性）
python3 << 'PYTHON_EOF'
import json
import sys
import os
from pathlib import Path

step_id = sys.argv[1]
timestamp = sys.argv[2]
input_files_str = sys.argv[3]

input_files = [f.strip() for f in input_files_str.split('\n') if f.strip()]

result = {
  "step": step_id,
  "timestamp": timestamp,
  "inputs": {}
}

# 讀每個檔案（支援章節篩選）
for file_spec in input_files:
  # 解析 "docs/FILE.md" 或 "docs/FILE.md§2"
  if '§' in file_spec:
    file_path, section = file_spec.split('§', 1)
    section_marker = f"§{section}"
  else:
    file_path = file_spec
    section_marker = None

  # 檢查檔案是否存在
  if not os.path.exists(file_path):
    print(f"❌ File not found: {file_path}", file=sys.stderr)
    sys.exit(1)

  # 讀檔案內容
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      content = f.read()
  except Exception as e:
    print(f"❌ Error reading {file_path}: {e}", file=sys.stderr)
    sys.exit(1)

  # 若指定章節，只保留該章節內容
  if section_marker:
    # 簡單實現：找到 "§2" 開始，到下一個 "§" 或檔案末尾
    lines = content.split('\n')
    section_start = None
    section_end = len(lines)

    for i, line in enumerate(lines):
      if section_marker in line:
        section_start = i
      elif section_start is not None and line.startswith('##') and section_marker not in line:
        # 遇到下一個一級標題，認為章節結束
        section_end = i
        break

    if section_start is not None:
      content = '\n'.join(lines[section_start:section_end])
    else:
      print(f"⚠️ Section {section_marker} not found in {file_path}", file=sys.stderr)

  # 使用檔案 spec 作為 key（包含章節標記若有）
  result["inputs"][file_spec] = content

# 輸出 JSON
print(json.dumps(result, ensure_ascii=False, indent=2))
PYTHON_EOF
EOF

exit_code=$?
if [[ $exit_code -ne 0 ]]; then
  exit $exit_code
fi
