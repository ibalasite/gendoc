---
name: gendoc-gen-contracts
description: |
  從 gendoc 生成的文件中提取機器可讀規格，轉換為可執行合約：
  1. OpenAPI 3.1 YAML（docs/blueprint/contracts/openapi.yaml）
  2. JSON Schema（docs/blueprint/contracts/schemas/*.json）
  3. Pact Consumer Contract（docs/blueprint/contracts/pact/*.json）
  4. IaC 模板（docs/blueprint/infra/helm/values.yaml 或 docker-compose.yml + network-policy）
  5. Seed Code Skeleton（docs/blueprint/scaffold/src/）
  呼叫時機：gendoc-flow D17-CONTRACTS 步驟（所有文件完成後）；或用戶手動執行
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Agent
---

## Step -1: Version check

Follow gendoc-shared §-1 (R-00) pattern — silent version check, update if needed.

## Step 0: Read State + Scan Source Docs

```bash
_CWD="$(pwd)"

# Read state file
_STATE=$(ls .gendoc-state-*.json 2>/dev/null | head -1 || echo ".gendoc-state.json")
_LANG_STACK=$(python3 -c "import json; print(json.load(open('$_STATE')).get('lang_stack', ''))" 2>/dev/null || echo "")
_DEPLOY_TARGET=$(python3 -c "import json; print(json.load(open('$_STATE')).get('deployment_target', 'docker'))" 2>/dev/null || echo "docker")
_PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$_STATE')).get('project_name', '$(basename $(pwd))'))" 2>/dev/null || echo "$(basename $(pwd))")
_CLIENT_TYPE=$(python3 -c "import json; print(json.load(open('$_STATE')).get('client_type', 'web'))" 2>/dev/null || echo "web")
_HAS_ADMIN=$(python3 -c "import json; print('true' if json.load(open('$_STATE')).get('has_admin_backend', False) else 'false')" 2>/dev/null || echo "false")

echo "PROJECT: $_PROJECT_NAME"
echo "LANG_STACK: $_LANG_STACK"
echo "DEPLOY_TARGET: $_DEPLOY_TARGET"
echo "CLIENT_TYPE: $_CLIENT_TYPE"
echo "HAS_ADMIN: $_HAS_ADMIN"

# Check which source docs exist
for f in docs/IDEA.md docs/BRD.md docs/PRD.md docs/EDD.md docs/API.md docs/SCHEMA.md docs/ARCH.md; do
  [[ -f "$f" ]] && echo "✅ $f" || echo "❌ $f (skip)"
done
[[ "$_HAS_ADMIN" == "true" ]] && { [[ -f "docs/ADMIN_IMPL.md" ]] && echo "✅ docs/ADMIN_IMPL.md (admin mode)" || echo "⚠️  docs/ADMIN_IMPL.md (admin mode 但文件不存在)"; }

# Required minimum
[[ ! -f "docs/EDD.md" ]] && echo "[ERROR] docs/EDD.md 不存在，無法提取 UML 結構" && exit 1
[[ ! -f "docs/API.md" ]] && echo "[WARN] docs/API.md 不存在，跳過 OpenAPI 生成"

# B-02：偵測並遷移根目錄舊版 contracts/ → docs/blueprint/contracts/
if [[ -d "contracts" && ! -L "contracts" ]]; then
  echo "[B-02] 偵測到根目錄 contracts/，遷移至 docs/blueprint/contracts/"
  mkdir -p docs/blueprint/contracts
  cp -rn contracts/. docs/blueprint/contracts/ 2>/dev/null || true
  mv contracts contracts._migrated_$(date +%Y%m%d%H%M%S)
  echo "[B-02] 遷移完成，原目錄已重命名為 contracts._migrated_*"
else
  echo "[B-02] 無根目錄 contracts/，略過遷移"
fi

# Setup output directories
mkdir -p docs/blueprint/contracts/schemas docs/blueprint/contracts/pact docs/blueprint/infra/k8s docs/blueprint/scaffold/src
```

## Step 1: Generate OpenAPI 3.1 YAML

Use **Agent tool** with this prompt:

```
你是 OpenAPI Architect（API 規格專家）。

任務：從 gendoc 生成的文件中提取 API 定義，生成 OpenAPI 3.1 YAML 規格。

**來源文件（按優先順序讀取）**：
1. `docs/API.md` — 主要 endpoint 定義（path, method, request, response）
2. `docs/EDD.md` §4.5.4 Sequence Diagram — request/response JSON 欄位定義（Note 區塊）
3. `docs/EDD.md` §4.5.2 Class Diagram — DTO 類型定義（<<RequestDTO>>, <<ResponseDTO>>, <<DTO>>）
4. `docs/SCHEMA.md` — 資料型別（用於 components/schemas 的 enum 值）
5. `docs/BRD.md` 或 `docs/IDEA.md` — 專案名稱、版本、description
6. `docs/ARCH.md` — API server base URL / domain

**生成格式**（OpenAPI 3.1.0，YAML）：

```yaml
openapi: 3.1.0
info:
  title: {project_name}
  version: "1.0.0"
  description: |
    {從 BRD.md §1 或 IDEA.md 提取的產品描述，1-2 句}
servers:
  - url: https://api.{domain}/v1
    description: Production
  - url: http://localhost:{port}/v1
    description: Local Development

paths:
  /{resource}:
    {method}:
      summary: {動詞 + 資源名}
      operationId: {camelCase 操作名}
      tags:
        - {資源分類}
      security:
        - BearerAuth: []        # 若 API.md 標注需要認證
      parameters:              # path/query/header params（來自 API.md）
        - name: {param}
          in: path|query|header
          required: true|false
          schema:
            type: string
            format: uuid
      requestBody:             # 只有 POST/PUT/PATCH 有
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/{ResourceRequest}'
      responses:
        '200':
          description: {成功說明}
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/{ResourceResponse}'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '422':
          description: {業務規則說明}
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  responses:
    BadRequest:
      description: 請求格式錯誤
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Unauthorized:
      description: 未認證
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: 資源不存在
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

  schemas:
    ErrorResponse:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
          description: 錯誤代碼（來自 API.md 或 EDD.md §4.5.4 ErrorDTO）
          example: "INSUFFICIENT_STOCK"
        message:
          type: string
          description: 人類可讀錯誤訊息
        details:
          type: object
          additionalProperties: true
          description: 結構化額外資訊（視錯誤類型而定）

    {ResourceRequest}:
      type: object
      required: [field1, field2]   # 來自 Sequence Diagram Note 或 API.md required 標注
      properties:
        {field}:
          type: {string|integer|number|boolean|array|object}
          format: {uuid|date-time|email|uri}   # 若有
          minimum: {N}                          # 若有約束
          maximum: {N}
          enum: [VALUE1, VALUE2]               # 若為 enum
          description: "{說明（來自 API.md 或 EDD.md）}"
          example: "{具體範例值}"
        {arrayField}:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/{ItemSchema}'
```

**精確度規則**：
- 每個 `required` 陣列只列 API.md/Sequence Diagram Note 標注為「required」的欄位
- Enum 值必須來自 EDD.md §4.5.2 Class Diagram 或 SCHEMA.md，不得自行假設
- 若 EDD.md §4.5.4 有 `Note: {field}: {Type} (required/optional)` → 提取為 properties
- 若 EDD.md §4.5.4 有 `Note: {field}: "{value1}" | "{value2}"` → 提取為 enum
- nullable 欄位：在來源文件標注 `nullable` 或 `0..1` 時，加 `nullable: true`
- `example` 值優先使用 §4.5.3 Object Diagram 中的具體實例值

**生成後用 Write 工具寫入** `docs/blueprint/contracts/openapi.yaml`。

最後輸出：
OPENAPI_RESULT:
  paths_count: N
  schemas_count: N
  missing_schemas: [列出無法從文件提取 schema 的 endpoints]
  conflicts: [列出 API.md 與 EDD.md 不一致的地方]
```

若 Agent 成功，顯示：
```
✅ OpenAPI: docs/blueprint/contracts/openapi.yaml（{paths_count} paths, {schemas_count} schemas）
```
若有 missing_schemas，顯示警告但繼續。

---

## Step 2: Generate JSON Schema Files

Use **Agent tool** with this prompt:

```
你是 JSON Schema Architect。

任務：從 EDD.md §4.5.2 Class Diagram 提取所有 DTO 類型，為每個 DTO 生成獨立的 JSON Schema 7 文件。

**來源**：
1. 讀取 `docs/EDD.md` §4.5.2 Class Diagram
2. 找出所有帶 <<RequestDTO>>, <<ResponseDTO>>, <<DTO>>, <<ValueObject>> stereotype 的 class
3. 讀取 Class Inventory 表格（src 路徑用於確認 class 名稱）
4. 讀取 Invariant Table（若有）—— 轉為 JSON Schema constraints

**每個 DTO 生成一個文件**，路徑：`docs/blueprint/contracts/schemas/{ClassName}.schema.json`

**格式**：
```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "$id": "https://{project}.contracts/{ClassName}",
  "title": "{ClassName}",
  "description": "{從 EDD.md class 說明提取，若無則留空}",
  "type": "object",
  "required": ["field1", "field2"],
  "properties": {
    "{field}": {
      "type": "{type}",
      "format": "{uuid|date-time|email}",
      "description": "{說明}",
      "minimum": N,
      "maximum": N,
      "minLength": N,
      "maxLength": N,
      "pattern": "{regex，若有}",
      "enum": ["VALUE1", "VALUE2"],
      "example": "{範例值}"
    },
    "{nestedObject}": {
      "$ref": "{OtherClassName}.schema.json"
    },
    "{arrayField}": {
      "type": "array",
      "items": {
        "$ref": "{ItemClassName}.schema.json"
      },
      "minItems": 1
    }
  },
  "additionalProperties": false,
  "x-source": "docs/EDD.md §4.5.2",
  "x-stereotype": "<<DTO>>"
}
```

**型別映射規則**（Mermaid → JSON Schema）：
- `String` / `string` → `"type": "string"`
- `UUID` → `"type": "string", "format": "uuid"`
- `Email` (ValueObject) → `"type": "string", "format": "email"`
- `Integer` / `int` → `"type": "integer"`
- `Decimal` / `Decimal(10,2)` → `"type": "number", "multipleOf": 0.01`
- `Boolean` → `"type": "boolean"`
- `DateTime` / `Timestamp` → `"type": "string", "format": "date-time"`
- `List<T>` / `T[]` → `"type": "array", "items": {"$ref": "T.schema.json"}`
- `Optional<T>` / `T | null` → `"oneOf": [{"$ref": "T.schema.json"}, {"type": "null"}]`
- Enum class → `"type": "string", "enum": [所有枚舉值]`

**用 Write 工具**為每個 DTO 生成獨立的 `.schema.json` 文件。

最後輸出：
JSON_SCHEMA_RESULT:
  generated: [ClassName1, ClassName2, ...]
  skipped: [說明跳過原因]
```

---

## Step 3: Generate Pact Consumer Contract Stubs

Use **Agent tool** with this prompt:

```
你是 Contract Test Architect（Pact 合約測試專家）。

任務：從 EDD.md §4.5.4 Sequence Diagram 提取服務間互動，為每個 consumer-provider 對生成 Pact 合約 JSON。

**來源**：
1. 讀取 `docs/EDD.md` §4.5.4 Sequence Diagram（所有圖）
2. 識別每對 consumer（呼叫方）→ provider（被呼叫方）
3. 提取每個互動的 request + response payload（從 Note 區塊）

**每個 consumer-provider 對生成一個文件**：`docs/blueprint/contracts/pact/{Consumer}--{Provider}.json`

**格式**：
```json
{
  "consumer": {"name": "{ConsumerService}"},
  "provider": {"name": "{ProviderService}"},
  "interactions": [
    {
      "description": "{操作說明，來自 Sequence Diagram 箭頭名稱}",
      "providerState": "{前置條件，來自 Note 的 Precondition 或 alt guard}",
      "request": {
        "method": "POST|GET|PUT|PATCH|DELETE",
        "path": "/api/v1/{resource}",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer {token}"
        },
        "body": {
          "{field}": "{matching rule 或具體值}",
          "{uuidField}": "{\"regex\": \"[0-9a-f]{8}-...\"}",
          "{enumField}": "VALUE1"
        },
        "matchingRules": {
          "$.body.{uuidField}": {"match": "regex", "regex": "[0-9a-f-]{36}"},
          "$.body.{arrayField}": {"match": "type", "min": 1}
        }
      },
      "response": {
        "status": 201,
        "headers": {"Content-Type": "application/json"},
        "body": {
          "{field}": "{matching value}"
        },
        "matchingRules": {
          "$.body.{field}": {"match": "type"}
        }
      }
    },
    {
      "description": "{錯誤場景}",
      "providerState": "{導致錯誤的前置條件}",
      "request": { },
      "response": {
        "status": 422,
        "body": {
          "code": "INSUFFICIENT_STOCK",
          "message": "{matching: type}",
          "availableQuantity": "{matching: integer}"
        }
      }
    }
  ],
  "metadata": {
    "pactSpecification": {"version": "2.0.0"},
    "x-source": "docs/EDD.md §4.5.4",
    "x-generated-by": "gendoc-gen-contracts"
  }
}
```

**規則**：
- Happy Path 和 Error Path 各生成一個 interaction
- Request body 欄位用 matchingRules 而非固定值（確保 provider 可驗證格式，不依賴具體值）
- `providerState` 必須是 provider 可以 setUp 的狀態描述（如 "user with id {uuid} exists"）
- 若 Sequence Diagram 有 `timeout` Note → 加入 `x-timeout` metadata
- 若多個 Sequence 圖涉及同一 consumer-provider 對 → 合併為一個文件的多個 interactions

**用 Write 工具**為每對生成文件。

最後輸出：
PACT_RESULT:
  pairs: [{consumer: X, provider: Y, interactions: N}]
  missing_payloads: [說明哪些 Sequence 圖缺少 request/response Note 而跳過]
```

---

## Step 4: Generate IaC Templates

Use **Agent tool** with this prompt:

```
你是 Platform Engineer（基礎設施即代碼專家）。

任務：從 EDD.md §4.5.9 Deployment Diagram 和附表提取部署配置，生成 IaC 文件。

**來源**：
1. 讀取 `docs/EDD.md` §4.5.9 Deployment Diagram
2. 讀取 HPA Configuration Table（若有）
3. 讀取 Storage Specification Table（若有）
4. 讀取 Network Policy Table（若有）
5. 讀取 `docs/ARCH.md` §13 Deployment 章節（若有額外配置）

**根據 _DEPLOY_TARGET 決定輸出格式**：

### 若 _DEPLOY_TARGET = "k8s" 或 "kubernetes"：

**輸出 1**: `docs/blueprint/infra/helm/values.yaml`
```yaml
# Generated by gendoc-gen-contracts from docs/EDD.md §4.5.9
# Source: {project_name}

global:
  registry: "{registry from Deployment Diagram}"
  imageTag: "latest"

services:
  {serviceName}:
    image:
      repository: "{image repo}"
      tag: "{tag from Deployment Diagram}"
      pullPolicy: Always
    resources:
      requests:
        cpu: "{cpu_request from Deployment Diagram}"
        memory: "{mem_request from Deployment Diagram}"
      limits:
        cpu: "{cpu_limit from Deployment Diagram}"
        memory: "{mem_limit from Deployment Diagram}"
    autoscaling:
      enabled: true
      minReplicas: {min from HPA Table}
      maxReplicas: {max from HPA Table}
      targetCPUUtilizationPercentage: {target from HPA Table}
      scaleDownStabilizationWindowSeconds: {cooldown from HPA Table, default 300}
    service:
      port: {port from Deployment Diagram}

persistence:
  {serviceName}:
    enabled: true
    storageClass: "{storageClass from Storage Spec Table}"
    size: "{size from Storage Spec Table}"
    accessMode: ReadWriteOnce

backup:
  {dbService}:
    enabled: true
    frequency: "{frequency from Storage Spec Table}"
    retention: "{retention from Storage Spec Table}"
```

**輸出 2**: `docs/blueprint/infra/k8s/network-policy.yaml`
```yaml
# Generated by gendoc-gen-contracts from docs/EDD.md §4.5.9 Network Policy Table
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {project-name}-network-policy
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # From Network Policy Table: allowed source→dest rules
    - from:
        - namespaceSelector:
            matchLabels:
              zone: "{source zone}"
      ports:
        - protocol: TCP
          port: {port}
  egress:
    # Deny internet egress for internal services
    - to:
        - namespaceSelector:
            matchLabels:
              zone: "DataZone"
      ports:
        - protocol: TCP
          port: 5432
```

### 若 _DEPLOY_TARGET = "docker" 或 "docker-compose"：

**輸出**: `docker-compose.yml`
```yaml
# Generated by gendoc-gen-contracts from docs/EDD.md §4.5.9
version: '3.8'

services:
  {service}:
    image: "{image}:{tag}"
    ports:
      - "{host_port}:{container_port}"
    environment:
      - NODE_ENV=development
    deploy:
      resources:
        limits:
          cpus: '{cpu_limit}'
          memory: {mem_limit}
        reservations:
          cpus: '{cpu_request}'
          memory: {mem_request}
    networks:
      - {zone}-network
    depends_on:
      - {dependency}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  {db_service}:
    image: "{db_image}:{version}"
    volumes:
      - {pvc_name}:{mount_path}
    networks:
      - data-network

volumes:
  {pvc_name}:
    driver: local

networks:
  {zone}-network:
    driver: bridge
```

用 Write 工具寫入所有文件。

最後輸出：
IAC_RESULT:
  deploy_target: {k8s|docker}
  files_generated: [路徑列表]
  missing_config: [說明哪些表格缺失，導致跳過的配置]
```

---

## Step 5: Generate Seed Code Skeleton

Use **Agent tool** with this prompt:

```
你是 Code Architect（骨架代碼生成專家）。

任務：從 EDD.md §4.5.2 Class Inventory 表格生成骨架代碼文件，提供工程師實作的起點。

**來源**：
1. 讀取 `docs/EDD.md` §4.5.2 Class Diagram 的 Class Inventory 表格
   （欄位：Class | Stereotype | Layer | src 路徑 | test 路徑）
2. 讀取 Class Diagram 屬性、方法、關聯線
3. `_LANG_STACK` = {_LANG_STACK}（決定代碼語言）

**語言選擇規則**：
- 含 "TypeScript" 或 "Node.js" → TypeScript (.ts)
- 含 "Java" 或 "Spring" → Java (.java)
- 含 "Python" → Python (.py)
- 含 "Go" → Go (.go)
- 含 "Kotlin" → Kotlin (.kt)
- 其他 → TypeScript（預設）

**輸出路徑**：在 `docs/blueprint/scaffold/` 下重建 Class Inventory 的 src 路徑結構

**每個 class 生成對應骨架文件**（根據語言）：

### TypeScript 範例：
```typescript
// docs/blueprint/scaffold/src/domain/order/Order.ts
// Generated by gendoc-gen-contracts | Source: docs/EDD.md §4.5.2 class-domain
// Stereotype: <<AggregateRoot>>

import { OrderStatus } from './OrderStatus';
import { OrderItem } from './OrderItem';
import { UserId } from '../user/UserId';

export class Order {
  // TODO: Implement — extracted from Class Diagram
  private readonly id: string;         // UUID
  private status: OrderStatus;
  private readonly userId: UserId;
  private items: OrderItem[];
  private total: number;              // Decimal

  // Constructor — see Invariant Table in EDD.md §4.5.2 for validation rules
  private constructor(params: {
    id: string;
    userId: UserId;
    items: OrderItem[];
  }) {
    // TODO: implement constructor + validation
    throw new Error('Not implemented');
  }

  // Factory method
  static create(userId: UserId, items: OrderItem[]): Order {
    // TODO: implement — see EDD.md §4.5.2 Invariant Table
    throw new Error('Not implemented');
  }

  // Methods — signatures extracted from Class Diagram
  confirm(): void {
    // TODO: implement — see State Machine §4.5.6
    throw new Error('Not implemented');
  }

  cancel(reason: string): void {
    // TODO: implement — see State Machine §4.5.6
    throw new Error('Not implemented');
  }

  // Getters
  getId(): string { return this.id; }
  getStatus(): OrderStatus { return this.status; }
}
```

**生成規則**：
- 每個文件頂部有 `// Generated by gendoc-gen-contracts | Source: ...` 標注
- 屬性從 Class Diagram 提取（visibility + name + type），填為 TODO 實作
- 方法簽名從 Class Diagram 提取，body 為 `throw new Error('Not implemented')`
- Enum class → 生成實際的 enum 定義（值從 Class Diagram 提取，不用 TODO）
- <<Repository>> interface → 生成 interface 定義（方法列表，無 body）
- <<Controller>> → 生成 route handler stubs（Express/Spring/FastAPI 格式視 lang_stack 而定）
- Import 語句根據 Class Diagram 的依賴關係生成

**同時生成 test 骨架**（在 Class Inventory 的 test 路徑）：
```typescript
// docs/blueprint/scaffold/tests/unit/domain/order/Order.test.ts
// Generated by gendoc-gen-contracts
import { Order } from '../../../../src/domain/order/Order';

describe('Order', () => {
  describe('create()', () => {
    it('should create order with valid items', () => {
      // TODO: implement test — see EDD.md §4.5.2 Invariant Table for constraints
      expect(true).toBe(false); // Failing placeholder
    });

    it('should reject empty items array', () => {
      // TODO: implement
    });
  });

  describe('confirm()', () => {
    it('should transition from PENDING to CONFIRMED', () => {
      // TODO: implement — see EDD.md §4.5.6 State Machine
    });

    it('should be idempotent when already CONFIRMED', () => {
      // TODO: implement — see State Machine Idempotency Table
    });
  });
});
```

用 Write 工具為每個 class 生成骨架文件。

最後輸出：
SEED_CODE_RESULT:
  language: {TypeScript|Java|Python|Go|Kotlin}
  files_generated: N
  paths: [列出生成的文件路徑]
  enums_complete: [直接可用的 enum 文件（不需 TODO）]
```

---

## Step 6: Generate CONTRACTS.md Index

Use the **Write tool** to create `docs/CONTRACTS.md`:

```markdown
# Machine-Readable Contracts Index

Generated by `gendoc-gen-contracts` from gendoc documentation pipeline.
Source documents: docs/EDD.md, docs/API.md, docs/SCHEMA.md, docs/ARCH.md

## Artifact Catalog

| Artifact | Path | Purpose | Source |
|----------|------|---------|--------|
| OpenAPI 3.1 YAML | [docs/blueprint/contracts/openapi.yaml](contracts/openapi.yaml) | API 合約，可匯入 Postman / Swagger UI / code generator | docs/API.md + EDD.md §4.5.4 |
| JSON Schema | [docs/blueprint/contracts/schemas/](contracts/schemas/) | DTO 型別定義，供 validator / IDE / code generator 使用 | EDD.md §4.5.2 |
| Pact Contracts | [docs/blueprint/contracts/pact/](contracts/pact/) | Consumer-driven 合約測試規格 | EDD.md §4.5.4 |
| Helm Values | [docs/blueprint/infra/helm/values.yaml](../docs/blueprint/infra/helm/values.yaml) | Kubernetes 部署配置 | EDD.md §4.5.9 |
| Network Policy | [docs/blueprint/infra/k8s/network-policy.yaml](../docs/blueprint/infra/k8s/network-policy.yaml) | 網路存取控制規則 | EDD.md §4.5.9 Network Policy Table |
| Seed Code | [docs/blueprint/scaffold/src/](../docs/blueprint/scaffold/src/) | 骨架代碼（空實作）+ 測試骨架 | EDD.md §4.5.2 Class Inventory |

## Usage Guide

### OpenAPI / Swagger UI
```bash
# Validate
npx @redocly/openapi-cli lint docs/blueprint/contracts/openapi.yaml

# Generate client SDK (TypeScript)
npx openapi-generator-cli generate -i docs/blueprint/contracts/openapi.yaml -g typescript-axios -o src/generated/client

# Start Swagger UI
npx swagger-ui-serve docs/blueprint/contracts/openapi.yaml
```

### JSON Schema Validation
```bash
# Validate a payload against schema
npx ajv validate -s docs/blueprint/contracts/schemas/CreateOrderRequest.schema.json -d payload.json
```

### Pact Contract Testing
```bash
# Provider verification
npx pact-verifier --pact-urls docs/blueprint/contracts/pact/*.json \
  --provider-base-url http://localhost:3000 \
  --provider-states-setup-url http://localhost:3000/_pact/setup
```

### Deploy with Helm
```bash
helm install {project-name} ./docs/blueprint/infra/helm -f docs/blueprint/infra/helm/values.yaml
```

### Scaffold
```bash
# Seed code is in docs/blueprint/scaffold/ — copy to src/ to begin implementation
cp -r docs/blueprint/scaffold/src/ src/
```

## Coverage Report

{在此插入各步驟輸出的 coverage 摘要}

---
*Generated: {date}*
*gendoc version: {version from state file}*
```

---

## Step 6.5: Admin API Contracts（has_admin_backend=true 時執行）

```bash
if [[ "$_HAS_ADMIN" == "true" ]]; then
  echo "[Admin] has_admin_backend=true → 生成 Admin 專屬合約文件"
  mkdir -p docs/blueprint/contracts/admin

  # 6.5-A: Admin OpenAPI YAML
  # 從 docs/API.md §18 Admin API 提取所有 /admin/* 端點
  # 輸出：docs/blueprint/contracts/admin/admin-api.yaml
  # 必須包含：auth/users/roles/audit-logs 全部 endpoint

  # 6.5-B: RBAC Seed JSON
  # 從 docs/ADMIN_IMPL.md §5 或 docs/EDD.md §5.5 提取 Role/Permission 定義
  # 輸出：docs/blueprint/contracts/admin/rbac-seed.json
  # 格式：{ "roles": [...], "permissions": [...], "role_permissions": [...] }

  # 6.5-C: Admin Seed SQL/JSON
  # 生成本地開發用初始 Admin 帳號 seed 數據
  # 輸出：docs/blueprint/contracts/admin/admin-seed.json
  # 包含：{ "admin_users": [{ "email": "admin@local.dev", "role": "super_admin" }] }

  echo "[Admin] Admin 合約文件生成完成"
  echo "  - docs/blueprint/contracts/admin/admin-api.yaml"
  echo "  - docs/blueprint/contracts/admin/rbac-seed.json"
  echo "  - docs/blueprint/contracts/admin/admin-seed.json"
else
  echo "[Admin] has_admin_backend=false → 跳過 Admin 合約生成"
fi
```

---

## Step 7: Commit

```bash
_NOW=$(date '+%Y-%m-%d %H:%M')
_FILES=""

[[ -f "docs/blueprint/contracts/openapi.yaml" ]] && _FILES="$_FILES docs/blueprint/contracts/openapi.yaml"
[[ -d "docs/blueprint/contracts" ]] && _FILES="$_FILES docs/blueprint/contracts/"
[[ -d "docs/blueprint/infra" ]] && _FILES="$_FILES docs/blueprint/infra/"
[[ -d "docs/blueprint/scaffold" ]] && _FILES="$_FILES docs/blueprint/scaffold/"
[[ -f "docs/CONTRACTS.md" ]] && _FILES="$_FILES docs/CONTRACTS.md"

if [[ -n "$_FILES" ]]; then
  git add $_FILES 2>/dev/null || true
  git commit -m "feat(gendoc)[CONTRACTS]: generate machine-readable specs from docs

- OpenAPI 3.1 YAML: docs/blueprint/contracts/openapi.yaml
- JSON Schema: docs/blueprint/contracts/schemas/
- Pact contracts: docs/blueprint/contracts/pact/
- IaC: docs/blueprint/infra/ (${_DEPLOY_TARGET})
- Seed code skeleton: docs/blueprint/scaffold/src/
" 2>/dev/null || echo "[Skip] 無新文件需要 commit"
fi
```

## Step 8: Final Summary

```
╔══════════════════════════════════════════════════════════════════╗
║  gendoc-gen-contracts — 機器可讀規格生成完成                      ║
╠══════════════════════════════════════════════════════════════════╣
║  OpenAPI:      docs/blueprint/contracts/openapi.yaml（{N} paths）║
║  JSON Schema:  docs/blueprint/contracts/schemas/（{N} 個 DTO）   ║
║  Pact:         docs/blueprint/contracts/pact/（{N} 個）          ║
║  IaC:          docs/blueprint/infra/（{deploy_target}）           ║
║  Seed Code:    docs/blueprint/scaffold/src/（{N} 個文件，{lang}） ║
╠══════════════════════════════════════════════════════════════════╣
║  下一步：                                                         ║
║  1. npx @redocly/openapi-cli lint docs/blueprint/contracts/openapi.yaml ║
║  2. 複製 docs/blueprint/scaffold/src/ → 開始實作                  ║
║  3. 設定 Pact broker 進行 consumer-driven 合約驗證                 ║
╚══════════════════════════════════════════════════════════════════╝
```
