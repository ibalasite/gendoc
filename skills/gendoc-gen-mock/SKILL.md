---
name: gendoc-gen-mock
description: |
  根據 docs/API.md 與 docs/SCHEMA.md 生成 FastAPI Mock Server。
  輸出至 docs/blueprint/mock/（可整個目錄帶走）。
  包含：main.py（所有 endpoint 1:1 對應 API.md）、requirements.txt、
  data/*.json（擬真假資料）、MOCK_SERVER_GUIDE.md（前端工程師使用手冊）。
  呼叫時機：gendoc-flow D18-MOCK 步驟；或用戶手動執行。
  condition: client_type != api-only
allowed-tools:
  - Bash
  - Read
  - Write
  - Agent
---

# gendoc-gen-mock — FastAPI Mock Server 生成

讀取 API.md + SCHEMA.md，自動產生可直接啟動的 FastAPI Mock Server，
供 frontend 工程師（HTML5 / Cocos / Unity / SaaS / 後台介面）在 backend 完成前獨立開發。

---

## Step -1：版本自動更新檢查

遵循 `gendoc-shared §-1`（R-00）：靜默檢查版本，有新版時以 Agent subagent 執行 `/gendoc-update` 後繼續。

---

## Step 0：讀取 Session Config 與環境

```bash
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

_EXEC_MODE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('execution_mode','full-auto'))
except: print('full-auto')
" 2>/dev/null || echo "full-auto")

_PROJECT_NAME=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('project_name','my-project'))
except: print('my-project')
" 2>/dev/null || echo "my-project")

_CLIENT_TYPE=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('client_type','web'))
except: print('web')
" 2>/dev/null || echo "web")

_LANG_STACK=$(python3 -c "
import json
try: print(json.load(open('${_STATE_FILE}')).get('lang_stack',''))
except: print('')
" 2>/dev/null || echo "")

echo "[gendoc-gen-mock] 專案：${_PROJECT_NAME}"
echo "[gendoc-gen-mock] client_type：${_CLIENT_TYPE}"
echo "[gendoc-gen-mock] lang_stack：${_LANG_STACK:-（未設定）}"

# guard：api-only 不需要 mock server
if [[ "$_CLIENT_TYPE" == "api-only" ]]; then
  echo "[Skip] client_type=api-only，不需要 frontend mock server，跳過此步驟"
  echo "STEP_COMPLETE: D18-MOCK"
  exit 0
fi

# 確認上游文件存在
[[ ! -f "docs/API.md" ]] && echo "[ERROR] docs/API.md 不存在，請先完成 D08-API 步驟" && exit 1

# B-02：偵測並遷移根目錄舊版 mock/ → docs/blueprint/mock/
if [[ -d "mock" && ! -L "mock" ]]; then
  echo "[B-02] 偵測到根目錄 mock/，遷移至 docs/blueprint/mock/"
  mkdir -p docs/blueprint/mock
  cp -rn mock/. docs/blueprint/mock/ 2>/dev/null || true
  mv mock mock._migrated_$(date +%Y%m%d%H%M%S)
  echo "[B-02] 遷移完成，原目錄已重命名為 mock._migrated_*"
else
  echo "[B-02] 無根目錄 mock/，略過遷移"
fi

# 建立輸出目錄
mkdir -p docs/blueprint/mock/data

echo "[gendoc-gen-mock] 輸出目錄：docs/blueprint/mock/"
echo "[gendoc-gen-mock] 上游文件：docs/API.md ✅"
[[ -f "docs/SCHEMA.md" ]] && echo "[gendoc-gen-mock] 上游文件：docs/SCHEMA.md ✅" || echo "[gendoc-gen-mock] docs/SCHEMA.md 不存在，將從 API.md 推斷資料模型"
```

---

## Step 1：解析 API 結構（Agent）

派送 Agent，讀取 API.md（以及 SCHEMA.md、EDD.md 若存在），輸出結構化 API 清單。

**Agent Prompt：**

```
你是 API Parser Expert。

任務：解析以下文件，輸出結構化 API 清單，供後續 mock server 生成使用。

必讀文件（不得跳過）：
1. docs/API.md — 完整讀取所有 endpoint 定義
2. docs/SCHEMA.md — 若存在，讀取資料模型定義
3. docs/EDD.md §Entity 章節 — 若存在，補充業務實體

輸出格式（JSON，供主 Claude 解析）：

API_PARSE_RESULT:
{
  "project_name": "{專案名稱}",
  "base_url": "{base URL，如 /api/v1}",
  "endpoints": [
    {
      "method": "GET|POST|PUT|PATCH|DELETE",
      "path": "/users",
      "path_params": ["user_id"],
      "query_params": ["page", "limit"],
      "request_body_schema": "UserCreate",
      "response_schema": "User",
      "response_is_list": true,
      "description": "取得使用者列表",
      "tags": ["users"]
    }
  ],
  "schemas": [
    {
      "name": "User",
      "fields": [
        {"name": "id", "type": "int", "example": 1},
        {"name": "name", "type": "str", "example": "Alice"},
        {"name": "email", "type": "str", "example": "alice@example.com"}
      ]
    }
  ],
  "resource_groups": ["users", "orders", "products"]
}

注意：
- path_params 從 path 中的 {param} 提取
- example 值必須是符合專案語境的擬真資料（不用 "string" / "example_value" 等泛用值）
- 如果文件中有真實業務名詞（如用戶名稱、商品名稱），優先使用
- response_is_list：GET /users 型態回傳 list[Schema] 則為 true
```

主 Claude 解析 `API_PARSE_RESULT:` 後的 JSON，儲存為 `_API_PARSE` 變數供後續步驟使用。

---

## Step 2：生成擬真假資料檔案（Agent）

派送 Agent，根據 Step 1 的解析結果，為每個 resource group 生成假資料 JSON。

**Agent Prompt：**

```
你是 Mock Data Expert。

任務：根據以下 API 解析結果，為每個資源（resource）生成擬真假資料 JSON 檔案。

API 解析結果：
{_API_PARSE}

輸出規則：
1. 每個 resource group 生成兩個檔案：
   - data/{resource}.json — 正常情境，包含 5-10 筆資料
   - data/{resource}_empty.json — 空資料情境，固定為 []

2. 擬真資料要求：
   - 中文名稱欄位用中文（如「王小明」「台北市信義區...」）
   - 英文名稱欄位用英文（如 "alice@example.com"）
   - 日期用近期合理日期（2024-2025 年範圍）
   - 金額用合理範圍（不要出現 9999999 這種）
   - status 欄位使用文件中定義的實際 enum 值
   - id 從 1 開始遞增，不要用 UUID（除非文件明確要求）

3. 用 Write 工具寫入每個檔案到 docs/blueprint/mock/data/ 目錄

完成後輸出：
MOCK_DATA_COMPLETE: {已生成的檔案清單，逗號分隔}
```

---

## Step 3：生成 main.py（Agent）

派送 Agent，根據解析結果生成完整的 FastAPI mock server。

**Agent Prompt：**

```
你是 FastAPI Expert。

任務：根據以下 API 解析結果，生成完整的 FastAPI Mock Server。

API 解析結果：
{_API_PARSE}

專案名稱：{_PROJECT_NAME}
base_url：{base_url}

生成規則：

### 1. 檔案結構
輸出單一 main.py 至 docs/blueprint/mock/main.py

### 2. 固定架構（必須包含）

```python
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="{PROJECT_NAME} Mock API",
    description="Frontend development mock server — 1:1 mapping to API.md",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
_cache: dict[str, Any] = {}


def load_json(filename: str, use_cache: bool = True) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Mock data file not found: {filename}")
    if use_cache and filename in _cache:
        return _cache[filename]
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if use_cache:
        _cache[filename] = data
    return data


def save_json(filename: str, data: Any) -> None:
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _cache[filename] = data
```

### 3. 為每個 schema 生成 Pydantic model
- 欄位用 Field(..., example=...) 附上擬真範例值
- Optional 欄位用 Optional[type] = None

### 4. 健康檢查 endpoints（固定）
```python
@app.get("/")
def root() -> dict[str, str]:
    return {"message": "{PROJECT_NAME} Mock API is running"}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
```

### 5. 為每個 endpoint 生成路由
- GET list：加 scenario、delay、error query params
- GET by id：從 JSON 搜尋，找不到回 404
- POST：驗證 id 不重複，append 後存回 JSON
- PUT/PATCH：找到後更新，找不到回 404
- DELETE：找到後移除，找不到回 404
- scenario 支援：normal（預設）、empty（空資料）
- delay：毫秒模擬延遲（0 = 不延遲）
- error：bool，模擬 500 錯誤

### 6. 路由命名規則
- 用函式名稱清楚表達意圖：list_users, get_user, create_user, update_user, delete_user

### 7. 每個 endpoint 加上完整的 docstring 說明（中文）

用 Write 工具寫入 docs/blueprint/mock/main.py。

完成後輸出：
MAIN_PY_COMPLETE: {endpoint 數量} endpoints generated
```

---

## Step 4：生成 requirements.txt

用 **Write 工具**直接寫入 `docs/blueprint/mock/requirements.txt`：

```
fastapi==0.115.12
uvicorn[standard]==0.34.2
```

---

## Step 5：生成 MOCK_SERVER_GUIDE.md（Agent）

派送 Agent 生成前端工程師使用手冊。

**Agent Prompt：**

```
你是 Technical Writer。

任務：為以下 FastAPI Mock Server 生成一份完整的使用手冊（繁體中文）。

專案名稱：{_PROJECT_NAME}
API endpoint 數量：{endpoint_count}
resource groups：{resource_groups}

手冊必須涵蓋以下章節（用 Write 工具寫入 docs/blueprint/mock/MOCK_SERVER_GUIDE.md）：

---

# {PROJECT_NAME} Mock Server 使用手冊

> 本 Mock Server 根據 API.md 自動生成，提供 1:1 對應的 API endpoint，
> 供 frontend 工程師在 backend 完成前獨立開發。

## 目錄結構

```
mock/
├── main.py              # FastAPI mock server 主程式
├── requirements.txt     # 依賴套件
├── data/                # 假資料目錄（可自由修改）
│   ├── {resource}.json
│   └── {resource}_empty.json
└── MOCK_SERVER_GUIDE.md # 本說明文件
```

## 前置需求

- Python 3.10 以上（Windows / macOS 均適用）
- pip（Python 套件管理工具）

### 確認 Python 版本
```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

## 安裝步驟

### Windows

```cmd
cd mock
pip install -r requirements.txt
```

### macOS / Linux

```bash
cd mock
pip3 install -r requirements.txt
```

> 建議使用虛擬環境（venv）隔離依賴：
> ```bash
> python3 -m venv venv
> source venv/bin/activate   # macOS/Linux
> venv\Scripts\activate      # Windows
> pip install -r requirements.txt
> ```

## 啟動 Mock Server

### Windows

```cmd
uvicorn main:app --reload
```

### macOS / Linux

```bash
uvicorn main:app --reload
```

啟動後可存取：

| 服務 | URL |
|------|-----|
| API Server | http://localhost:8000 |
| Swagger UI（互動測試） | http://localhost:8000/docs |
| ReDoc（文件閱讀） | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

## Postman 匯入

### 方法一：直接從 URL 匯入（推薦）

1. 確認 Mock Server 已啟動
2. 開啟 Postman → Import
3. 選擇 **Link**
4. 輸入：`http://localhost:8000/openapi.json`

### 方法二：下載後匯入

```bash
curl http://localhost:8000/openapi.json -o openapi.json
```

再到 Postman Import → 選擇 `openapi.json` 檔案。

## Frontend 串接設定

在 frontend 專案的環境變數中設定 API base URL：

### Vite / Vue / React（.env.development）

```env
VITE_API_BASE_URL=http://localhost:8000
```

呼叫方式：
```ts
const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/users`)
const data = await res.json()
```

### Cocos Creator（config 或 global 常數）

```ts
const API_BASE = "http://localhost:8000"
```

### Unity（C#）

```csharp
const string API_BASE = "http://localhost:8000";
```

## 特殊測試情境

每個 GET list endpoint 支援以下 query parameters：

| 參數 | 說明 | 範例 |
|------|------|------|
| `scenario=empty` | 回傳空陣列 | `GET /api/v1/users?scenario=empty` |
| `delay=1000` | 延遲 1 秒（毫秒） | `GET /api/v1/users?delay=1000` |
| `error=true` | 模擬 500 錯誤 | `GET /api/v1/users?error=true` |

## 修改假資料

假資料存放在 `data/` 目錄，用任何文字編輯器直接修改 JSON 檔案即可。

### 資料檔案說明

{資料檔案說明表格：每個 resource 的 .json 和 _empty.json}

### 修改範例

開啟 `data/{resource}.json`，新增或修改資料：

```json
[
  {
    "id": 1,
    "name": "王小明",
    ...
  }
]
```

儲存後**無需重啟 server**（--reload 模式下自動偵測）。

> ⚠️ 注意：POST / PUT / DELETE 操作會直接修改 JSON 檔案。
> 如需還原，請從 git 重置：`git checkout data/`

## 常見問題

### Q: Port 8000 被佔用？

```bash
uvicorn main:app --reload --port 8001
```

Frontend 環境變數也要同步改為 `http://localhost:8001`。

### Q: CORS 錯誤？

Mock Server 已開放所有來源（`allow_origins=["*"]`），如仍有問題，
確認 frontend 的 fetch 沒有加 `credentials: "include"`。

### Q: Windows 執行 uvicorn 報錯？

確認 pip 安裝到正確的 Python 版本：
```cmd
python -m uvicorn main:app --reload
```

## 進階：對接 Backend

當 backend 完成後，只需修改 frontend 的環境變數：

```env
VITE_API_BASE_URL=https://api.yourproject.com
```

無需修改任何 frontend 業務代碼。

---

完成後輸出：
GUIDE_COMPLETE: MOCK_SERVER_GUIDE.md written
```

---

## Step 6：Git Commit

```bash
_STATE_FILE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")

# 計算生成的檔案數量
_FILE_COUNT=$(find docs/blueprint/mock -type f | wc -l | tr -d ' ')

# Pre-commit check（跳過 data/ 目錄，JSON 不掃 placeholder）
echo "[PRE-COMMIT] 跳過 mock/data/*.json 的 placeholder 掃描（JSON 格式）"

# Stage & commit
git add docs/blueprint/mock/

git commit -m "feat(gendoc)[D18-MOCK]: generate FastAPI mock server

- main.py: {endpoint_count} endpoints (1:1 mapping to API.md)
- data/: {resource_count} resources with realistic fake data
- MOCK_SERVER_GUIDE.md: frontend engineer setup & usage guide
- Platform: Windows + macOS, FastAPI + uvicorn
- Supports: scenario/delay/error test params, Postman import, CORS"

echo "[D18-MOCK] ✅ Git commit 完成"
```

---

## Step 7：輸出摘要

```
╔══════════════════════════════════════════════════════════════╗
║  D18-MOCK — FastAPI Mock Server 生成完成                      ║
╠══════════════════════════════════════════════════════════════╣
║  輸出目錄：docs/blueprint/mock/                               ║
║  Endpoints：{N} 個（1:1 對應 API.md）                         ║
║  假資料：{N} 個 resource，各含 normal + empty 情境             ║
╠══════════════════════════════════════════════════════════════╣
║  啟動方式：                                                   ║
║    cd docs/blueprint/mock                                    ║
║    pip install -r requirements.txt                            ║
║    uvicorn main:app --reload                                  ║
╠══════════════════════════════════════════════════════════════╣
║  Swagger UI：http://localhost:8000/docs                       ║
║  ReDoc：     http://localhost:8000/redoc                      ║
║  Postman：   import http://localhost:8000/openapi.json        ║
╠══════════════════════════════════════════════════════════════╣
║  Frontend 環境變數：                                          ║
║    VITE_API_BASE_URL=http://localhost:8000                    ║
╠══════════════════════════════════════════════════════════════╣
║  整個 docs/blueprint/mock/ 目錄可獨立帶走使用                  ║
╚══════════════════════════════════════════════════════════════╝

下一步：D19-HTML — HTML 文件網站生成（含 mock server 連結）
```

```
STEP_COMPLETE: D18-MOCK
```
