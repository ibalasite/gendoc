---
title: DRYRUN 規格推導公式
date: 2026-05-04
version: 1.0
status: 實作規範
---

# DRYRUN 規格推導公式

## 概述

本文檔定義 DRYRUN 后各 step 的期望規格推導公式。每個公式基於 DRYRUN 前提取的四個核心參數，推導該 step 的期望產出規格（如表格數、endpoint 數、section 數等）。

**核心原則**：
- 公式在 `dryrun_core.py` 的 `derive_specifications()` 方法中實現
- 推導結果存儲在 `.gendoc-rules/<step-id>-rules.json`，供 review.sh 機械式驗證
- 每個公式包含 `min_count` 與 `optional_checks` 兩部分

---

## 參數參考

| 參數 | 定義 | 範圍 |
|------|------|------|
| `entity_count` | EDD 中 entity/class 總數 | 1-200 |
| `rest_endpoint_count` | PRD/EDD 中 REST endpoint 總數 | 1-500 |
| `user_story_count` | PRD 中 user story 總數 | 1-500 |
| `arch_layer_count` | ARCH 中架構層級數 | 2-50 |
| `admin_feature_count` | EDD 中 Admin 相關功能（可選） | 0-100 |

---

## DRYRUN 后的 step 規格公式

### Step: API

**職責**：定義系統的 REST API 端點規格

**期望規格**：
```json
{
  "min_endpoint_count": "max(5, rest_endpoint_count)",
  "min_h2_sections": "ceil(rest_endpoint_count / 3) + 3",
  "required_sections": [
    "API Overview",
    "Authentication",
    "Rate Limiting",
    "Endpoint Reference",
    "Error Handling",
    "Status Codes",
    "Pagination",
    "Response Examples"
  ],
  "optional_checks": {
    "endpoint_coverage": "All {rest_endpoint_count} endpoints from PRD must be documented",
    "entity_reference": "Request/Response schemas must reference {entity_count} entities",
    "sequence_diagrams": ">= 2 sequence diagrams for complex workflows"
  }
}
```

**說明**：
- `min_endpoint_count`：最少應文檔化的 endpoint 數（至少 5 個）
- `min_h2_sections`：最少二級標題數（endpoint + 3 個固定章節）
- `required_sections`：必須出現的章節清單

---

### Step: SCHEMA

**職責**：定義資料庫 schema 與表結構

**期望規格**：
```json
{
  "min_table_count": "max(3, entity_count)",
  "min_h2_sections": "entity_count + 5",
  "required_sections": [
    "ER Diagram",
    "Table Definitions",
    "Naming Conventions",
    "Normalization Rules",
    "Indexing Strategy",
    "Foreign Keys",
    "Soft Delete Strategy",
    "Migration Strategy"
  ],
  "optional_checks": {
    "entity_coverage": "All {entity_count} EDD entities must have corresponding tables",
    "column_coverage": "All PDD display columns must exist in schema",
    "fk_validation": "Foreign keys must reference valid tables within same BC",
    "index_coverage": ">= 1 index per table"
  }
}
```

**說明**：
- `min_table_count`：最少表數（至少 3 個）
- 每個 entity 應對應至少一個表

---

### Step: FRONTEND

**職責**：定義前端組件與頁面架構（僅 `client_type != none`）

**期望規格**：
```json
{
  "condition": "client_type != none",
  "min_component_count": "max(3, arch_layer_count * 3 + user_story_count / 5)",
  "min_h2_sections": "user_story_count + arch_layer_count + 3",
  "required_sections": [
    "Component Inventory",
    "Page Structure",
    "State Management",
    "Routing",
    "Client-Server Communication",
    "Error Handling",
    "Performance Optimization",
    "Accessibility"
  ],
  "optional_checks": {
    "story_coverage": "Components for all {user_story_count} user stories",
    "pdd_alignment": "All PDD screens must have component definitions",
    "layer_separation": "Clear separation of view/controller/service layers",
    "lazy_loading": "Code splitting strategy for large components"
  }
}
```

**說明**：
- `min_component_count`：基於架構層級和 user story 數量推算
- 需涵蓋所有 user story 對應的 UI 組件

---

### Step: test-plan

**職責**：定義測試計畫與測試案例

**期望規格**：
```json
{
  "min_h2_sections": "arch_layer_count + user_story_count / 4 + 3",
  "min_test_cases": "user_story_count * 3",
  "min_scenarios": "user_story_count * 1.5",
  "required_sections": [
    "Test Overview",
    "Test Scope",
    "Test Environment",
    "Test Strategy",
    "Unit Test Cases",
    "Integration Test Cases",
    "E2E Test Cases",
    "Performance Test Cases",
    "Security Test Cases",
    "Test Data & Fixtures",
    "Test Execution Plan"
  ],
  "optional_checks": {
    "bva_coverage": "Boundary value analysis for numeric inputs",
    "equivalence_partitioning": "Equivalence classes for all AC",
    "negative_testing": "At least 1 negative test per AC",
    "edge_cases": "Error path & edge case scenarios"
  }
}
```

**說明**：
- `min_test_cases`：基於 user story 數量（每個故事至少 3 個 test case）
- 必須涵蓋 unit / integration / E2E 三層

---

### Step: BDD-server

**職責**：定義伺服器端 BDD 場景（Gherkin）

**期望規格**：
```json
{
  "min_scenario_count": "ceil(user_story_count * 0.8)",
  "min_step_definitions": "ceil(rest_endpoint_count * 0.6)",
  "required_sections": [
    "Feature Definitions",
    "Happy Path Scenarios",
    "Error Path Scenarios",
    "Edge Case Scenarios",
    "Step Definitions",
    "Test Data Setup",
    "Assertion Rules"
  ],
  "optional_checks": {
    "story_alignment": "{min_scenario_count} scenarios must map to user stories",
    "endpoint_coverage": "All critical endpoints have at least 1 scenario",
    "error_handling": "Error scenarios for each API error code",
    "idempotency": "Idempotency scenarios where applicable"
  }
}
```

**說明**：
- `min_scenario_count`：基於 user story（約 80% 覆蓋）
- 每個重要 endpoint 應有至少 1 個場景

---

### Step: BDD-client

**職責**：定義客戶端 BDD 場景（條件：`client_type != none`）

**期望規格**：
```json
{
  "condition": "client_type != none",
  "min_scenario_count": "ceil(user_story_count * 0.7)",
  "min_step_definitions": "ceil(user_story_count * 0.5)",
  "required_sections": [
    "Feature Definitions",
    "User Journey Scenarios",
    "UI Interaction Scenarios",
    "Error Handling Scenarios",
    "Performance Scenarios",
    "Step Definitions"
  ],
  "optional_checks": {
    "happy_path": "At least 1 happy path scenario per user story",
    "error_recovery": "Error recovery & retry scenarios",
    "offline_mode": "Offline mode handling (if applicable)",
    "performance_assertion": "Performance thresholds (LCP, FCP, etc.)"
  }
}
```

---

### Step: RTM (Requirements Traceability Matrix)

**職責**：建立需求與測試的追蹤矩陣

**期望規格**：
```json
{
  "min_h2_sections": "3",
  "min_traceability_entries": "user_story_count",
  "required_sections": [
    "RTM Overview",
    "User Story to Test Case Mapping",
    "Test Coverage Analysis",
    "Class to Test Mapping",
    "Traceability Matrix"
  ],
  "optional_checks": {
    "us_coverage": "All {user_story_count} user stories must be traced to test cases",
    "test_coverage": ">= 80% test coverage ratio",
    "class_coverage": "All {entity_count} classes must have test coverage",
    "gap_analysis": "Coverage gap analysis section"
  }
}
```

---

### Step: runbook

**職責**：定義生產運維手冊

**期望規格**：
```json
{
  "min_h2_sections": "arch_layer_count + 5",
  "required_sections": [
    "Architecture Overview",
    "Deployment Procedures",
    "Monitoring & Alerting",
    "Incident Response",
    "Backup & Recovery",
    "Scaling Procedures",
    "Database Maintenance",
    "Log Management",
    "Health Checks",
    "Troubleshooting Guide"
  ],
  "optional_checks": {
    "step_by_step_procedures": "All procedures must have step-by-step commands",
    "verification_steps": "Each procedure must include verification commands",
    "namespace_clarity": "Kubernetes namespace clearly specified",
    "service_dependencies": "Clear service dependency diagram"
  }
}
```

---

### Step: LOCAL_DEPLOY

**職責**：定義本地環境完整建置指南

**期望規格**：
```json
{
  "min_h2_sections": "12",
  "required_sections": [
    "Overview",
    "System Requirements",
    "Prerequisites",
    "Kubernetes Setup (Rancher Desktop / k3s)",
    "Database Setup",
    "Application Deployment",
    "Environment Variables",
    "Port Mappings",
    "Test Data Loading",
    "Verification Checklist",
    "Troubleshooting",
    "Docker Compose Alternative"
  ],
  "optional_checks": {
    "step_completeness": "No TBD or unfinished steps",
    "client_in_k8s": "Client application must be deployable in k8s pod",
    "single_port": "Single entry point on port 80",
    "e2e_tests": "All E2E tests runnable after setup",
    "dev_platform": "Local Developer Platform (Gitea/Jenkins/ArgoCD) included"
  }
}
```

---

### Step: DEVELOPER_GUIDE

**職責**：定義開發者日常操作手冊

**期望規格**：
```json
{
  "min_h2_sections": "5",
  "required_sections": [
    "Daily Development Workflow",
    "CI/CD Diagnostics",
    "Quick Commands",
    "Common Issues & Fixes",
    "Environment Maintenance"
  ],
  "optional_checks": {
    "git_workflow": "Git push → CI trigger → CD deployment workflow documented",
    "quick_commands": ">= 5 Makefile targets (make dev-status, make dev-logs, etc.)",
    "troubleshooting": ">= 10 common issues with solutions",
    "local_vs_prod": "Clear distinction between local and production environments"
  }
}
```

---

### Step: CICD

**職責**：定義 CI/CD 流水線設計

**期望規格**：
```json
{
  "min_h2_sections": "8",
  "required_sections": [
    "Pipeline Overview",
    "Build Stage",
    "Test Stage",
    "Security Scanning",
    "Deployment Stage",
    "Monitoring",
    "Rollback Procedures",
    "Local Developer Platform"
  ],
  "optional_checks": {
    "stage_clarity": "Clear CI/CD stages with dependencies",
    "test_automation": "Automated test execution (unit/integration/E2E)",
    "dev_tools": "Local Gitea/Jenkins/ArgoCD setup documented",
    "webhook_integration": "Git webhook integration to Jenkins"
  }
}
```

---

### Step: AUDIO（條件：`client_type == game`）

**期望規格**：
```json
{
  "condition": "client_type == game",
  "min_h2_sections": "6",
  "min_audio_items": "max(5, rest_endpoint_count / 3)",
  "required_sections": [
    "Audio Strategy",
    "BGM List",
    "SFX List",
    "Voice Over",
    "Audio Engine Setup",
    "Performance Budget"
  ],
  "optional_checks": {
    "state_machine": "Audio trigger state machine for each sound",
    "format_specs": "Audio file format & bitrate specifications",
    "memory_budget": "Memory budget for audio resources"
  }
}
```

---

### Step: ANIM（條件：`client_type == game`）

**期望規格**：
```json
{
  "condition": "client_type == game",
  "min_h2_sections": "6",
  "min_animation_items": "max(8, user_story_count / 2)",
  "required_sections": [
    "Animation Strategy",
    "Skeletal Animations",
    "Frame Animations",
    "Particle Effects",
    "Shader Effects",
    "Performance Budget"
  ],
  "optional_checks": {
    "lod_strategy": "LOD (Level of Detail) strategy for effects",
    "performance_targets": "Frame rate targets (60fps/30fps)",
    "asset_specs": "Sprite/model resolution specifications"
  }
}
```

---

### Step: UML

**職責**：生成 Server 端 UML 圖表

**期望規格**：
```json
{
  "min_diagram_count": "9",
  "diagram_types": [
    "Class Diagram (3 layers: Entity / Service / Repository)",
    "Use Case Diagram",
    "Sequence Diagram (API flow)",
    "Activity Diagram",
    "State Machine Diagram",
    "Component Diagram",
    "Deployment Diagram"
  ],
  "required_content": {
    "class_diagram_coverage": "All {entity_count} entities must appear in class diagrams",
    "sequence_flow": "All {rest_endpoint_count} major API flows must have sequence diagrams",
    "class_inventory": "class-inventory.md with method-level detail"
  },
  "optional_checks": {
    "class_completeness": "Methods signatures with types and return values",
    "relationship_coverage": "All 6 relationship types (Inheritance/Realization/Composition/Aggregation/Association/Dependency)",
    "diagram_clarity": "Each diagram has technical + plain-language explanation"
  }
}
```

---

### Step: CONTRACTS

**職責**：生成機器可讀規格（OpenAPI / JSON Schema / Pact）

**期望規格**：
```json
{
  "min_h2_sections": "4",
  "required_artifacts": [
    "OpenAPI 3.1 YAML",
    "JSON Schema files",
    "Pact (contract testing)",
    "Helm values.yaml"
  ],
  "optional_checks": {
    "openapi_completeness": "OpenAPI covers all {rest_endpoint_count} endpoints",
    "schema_validation": "All schemas are valid JSON Schema Draft 2020-12",
    "example_values": "Request/response examples for each endpoint"
  }
}
```

---

### Step: MOCK

**職責**：生成 Mock Server（FastAPI）

**期望規格**：
```json
{
  "min_endpoints": "rest_endpoint_count",
  "required_artifacts": [
    "FastAPI application",
    "Mock data JSON files",
    "Swagger UI",
    "Postman collection"
  ],
  "optional_checks": {
    "endpoint_coverage": "All {rest_endpoint_count} endpoints implemented",
    "cross_platform": "Windows/macOS launch instructions",
    "realistic_data": "Mock data reflects real entity structures"
  }
}
```

---

### Step: ALIGN / ALIGN-FIX / ALIGN-VERIFY（審查層，不推導規格）

**說明**：這三個 step 屬於「審查層」（見 CLAUDE.md 設計決策 #3），無獨立「內容規格」推導。

```json
{
  "note": "Audit layer steps - no spec derivation required",
  "purpose": "Global cross-file alignment verification",
  "quantitative_checks": "Mechanical pattern matching only"
}
```

---

### Step: HTML（輸出層，條件：always）

**說明**：HTML 是最終發布步驟，無量化規格要求（內容由所有 DRYRUN 后的 step 決定）。

```json
{
  "note": "Publication layer - content determined by DRYRUN 后的 step outputs",
  "requirements": [
    "All phase B documents must be present and error-free",
    "HTML generation must succeed without errors",
    "Navigation sidebar must include all available diagrams"
  ]
}
```

---

## 公式實現規則（dryrun_core.py）

### `derive_specifications()` 方法簽名

```python
def derive_specifications(self, params: dict) -> dict:
    """
    根據提取的四個核心參數，推導所有 DRYRUN 后的 step 的期望規格。
    
    Args:
        params: {
            "entity_count": int,
            "rest_endpoint_count": int,
            "user_story_count": int,
            "arch_layer_count": int,
            "admin_feature_count": int or None,
            "metadata": {...}
        }
    
    Returns:
        {
            "step_specifications": {
                "API": {"min_endpoint_count": 12, ...},
                "SCHEMA": {"min_table_count": 10, ...},
                ...
            },
            "timestamp": "2026-05-04T10:30:00Z",
            "parameter_source": params["metadata"]
        }
    """
    
    specs = {}
    
    # API
    specs["API"] = {
        "min_endpoint_count": max(5, params["rest_endpoint_count"]),
        "min_h2_sections": math.ceil(params["rest_endpoint_count"] / 3) + 3,
        "entity_coverage": params["entity_count"]
    }
    
    # SCHEMA
    specs["SCHEMA"] = {
        "min_table_count": max(3, params["entity_count"]),
        "min_h2_sections": params["entity_count"] + 5
    }
    
    # test-plan
    specs["test-plan"] = {
        "min_h2_sections": params["arch_layer_count"] + math.ceil(params["user_story_count"] / 4) + 3,
        "min_test_cases": params["user_story_count"] * 3
    }
    
    # ... 其他 step
    
    return {"step_specifications": specs, "timestamp": datetime.now().isoformat()}
```

---

## 檢查清單

- [ ] 所有 DRYRUN 后的 step 都有規格公式定義
- [ ] 每個公式包含 min_count 與可選檢查項
- [ ] 公式使用四個核心參數
- [ ] Fallback 邏輯清晰
- [ ] 已明確標記不推導規格的 step（審查層 + 輸出層）

---

## 相關檔案

| 檔案 | 用途 |
|------|------|
| `docs/DRYRUN_PARAMETER_EXTRACTION.md` | 參數提取規則（STEP 1） |
| `tools/bin/dryrun_core.py` | 實作公式計算 |
| `.gendoc-rules/<step-id>-rules.json` | 公式推導結果（輸出） |
| `tools/bin/review.sh` | 機械式驗證（對比預期 vs 實際） |
