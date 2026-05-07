"""Unit tests for DRYRUNEngine extract methods (7 quantitative anchors)."""
import json
from pathlib import Path

import pytest

import dryrun_core


# ── _extract_entity_count ─────────────────────────────────────────────────

class TestExtractEntityCount:
    def test_union_mermaid_and_section4(self, engine, upstream_data):
        # EDD fixture: 6 mermaid entities (User/Order/Product/Repository/
        # OrderStatus/BaseEntity — _PrivateImpl filtered out, regex requires
        # leading letter) + 3 §4.N entities (AdminUser/AuditLog/
        # NotificationTemplate) = 9 unique
        count = engine._extract_entity_count(upstream_data)
        assert count == 9

    def test_section4_only(self, engine):
        # No Mermaid, only §4 entities
        edd = """## §4 Entities
### §4.1 FooEntity
### §4.2 BarEntity
### 4.3 BazEntity
"""
        assert engine._extract_entity_count({"docs/EDD.md": edd}) == 3

    def test_dedup_across_sources(self, engine):
        # Same entity name in both Mermaid and §4 → counted once
        edd = """```mermaid
classDiagram
    class FooEntity
```
### §4.1 FooEntity
"""
        assert engine._extract_entity_count({"docs/EDD.md": edd}) == 3  # 1 unique → max(3, 1)

    def test_empty_edd_returns_fallback(self, engine):
        count = engine._extract_entity_count({"docs/EDD.md": ""})
        assert count == 3  # fallback

    def test_no_edd_key_returns_fallback(self, engine):
        count = engine._extract_entity_count({})
        assert count == 3

    def test_fallback_to_section_headings(self, engine):
        # No mermaid, no §4, falls back to plain ### ClassName headings
        edd = "## Section\n### User\n### Order\n### Product\n"
        count = engine._extract_entity_count({"docs/EDD.md": edd})
        assert count == 3  # max(3, 3) = 3

    def test_fallback_returns_default_when_no_match(self, engine):
        edd = "no entities here, just prose"
        count = engine._extract_entity_count({"docs/EDD.md": edd})
        assert count == 3


# ── _extract_avg_entity_field_count ──────────────────────────────────────

class TestExtractAvgEntityFieldCount:
    def test_table_with_field_lists(self, engine, upstream_data):
        # EDD fixture: User row has "id, email, name, created_at, updated_at" (5 fields, 4 commas)
        avg = engine._extract_avg_entity_field_count(upstream_data)
        assert 3 <= avg <= 20

    def test_empty_returns_fallback(self, engine):
        avg = engine._extract_avg_entity_field_count({"docs/EDD.md": ""})
        assert avg == 3

    def test_no_edd_returns_fallback(self, engine):
        assert engine._extract_avg_entity_field_count({}) == 3

    def test_no_qualifying_rows_returns_default(self, engine):
        edd = "## Section\n| Foo |\n|---|\n| Bar |\n"  # no 3+ comma cells
        assert engine._extract_avg_entity_field_count({"docs/EDD.md": edd}) == 3

    def test_clamp_to_max_20(self, engine):
        # cell with many fields gets clamped
        big_field_list = ", ".join([f"f{i}" for i in range(25)])
        edd = f"| Entity | Fields |\n|---|---|\n| User | {big_field_list} |\n"
        assert engine._extract_avg_entity_field_count({"docs/EDD.md": edd}) == 20


# ── _extract_rest_endpoint_count ─────────────────────────────────────────

class TestExtractRestEndpointCount:
    """Phase boundary rule: only read EDD.md and PRD.md from DRYRUN input[].
    API.md is Phase B artifact and MUST NOT be read."""

    def test_priority_edd_over_prd(self, engine):
        # EDD is endpoint SSOT in Phase A → wins over PRD
        data = {
            "docs/EDD.md": "GET /v1/a\nPOST /v1/b\nDELETE /v1/c\nPUT /v1/d\nPATCH /v1/e\nGET /v1/f",
            "docs/PRD.md": "GET /old/legacy\n",
        }
        # 6 unique from EDD → max(5, 6) = 6
        assert engine._extract_rest_endpoint_count(data) == 6

    def test_falls_back_to_prd_when_no_edd(self, engine):
        data = {
            "docs/PRD.md": "GET /api/login\nPOST /api/signup\nPOST /api/reset\nPUT /api/x\nGET /api/y\nDELETE /api/z",
        }
        assert engine._extract_rest_endpoint_count(data) == 6

    def test_phase_boundary_ignores_api_md(self, engine):
        """API.md is Phase B artifact — even if present in upstream_data,
        it must NOT influence the count (phase boundary rule)."""
        data = {
            "docs/API.md": "GET /v1/a\nPOST /v1/b\nDELETE /v1/c\nPUT /v1/d\n"
                            "PATCH /v1/e\nGET /v1/f\nPOST /v1/g\nDELETE /v1/h",  # 8 endpoints
            "docs/EDD.md": "GET /v1/a\nPOST /v1/b\nDELETE /v1/c",  # 3 unique
        }
        # Must use EDD (3) → max(5, 3) = 5, NOT API.md (8)
        assert engine._extract_rest_endpoint_count(data) == 5

    def test_endpoints_extracted_from_fixture(self, engine, upstream_data):
        # Fixture EDD has 4 unique endpoints (GET/POST/PUT/DELETE /api/users)
        # → max(5, 4) = 5
        count = engine._extract_rest_endpoint_count(upstream_data)
        assert count == 5

    def test_empty_returns_fallback(self, engine):
        assert engine._extract_rest_endpoint_count({"docs/PRD.md": ""}) == 5

    def test_no_sources_returns_fallback(self, engine):
        assert engine._extract_rest_endpoint_count({}) == 5

    def test_unique_endpoints_only(self, engine):
        # Same endpoint repeated → counted once
        data = {"docs/EDD.md": "GET /api/x\nGET /api/x\nGET /api/x\nPOST /api/y"}
        # 2 unique → max(5, 2) = 5
        assert engine._extract_rest_endpoint_count(data) == 5


# ── _extract_user_story_count ────────────────────────────────────────────

class TestExtractUserStoryCount:
    def test_us_pattern(self, engine, upstream_data):
        # Fixture PRD has US-001, US-002, US-003
        count = engine._extract_user_story_count(upstream_data)
        assert count == 5  # max(5, 3) = 5

    def test_three_segment_us_id(self, engine):
        # DRYRUN_DEV_FEEDBACK case: US-PET-001, US-AUTH-002, etc
        prd = """## §5 User Stories

### US-PET-001
### US-PET-002
### US-AUTH-001
### US-AUTH-002
### US-ARENA-001
### US-ARENA-002
### US-ARENA-003
"""
        count = engine._extract_user_story_count({"docs/PRD.md": prd})
        assert count == 7  # 7 unique three-segment IDs, max(5, 7) = 7

    def test_dedup_repeated_ids(self, engine):
        # Same US-X-N appearing in multiple places counts once
        prd = "US-PET-001 mentioned\nlater US-PET-001 again\nUS-AUTH-001 here"
        assert engine._extract_user_story_count({"docs/PRD.md": prd}) == 5  # 2 unique → max(5,2)

    def test_mixed_formats(self, engine):
        prd = """### US-1
### Story-2
### User Story 3
### US-PET-001
"""
        count = engine._extract_user_story_count({"docs/PRD.md": prd})
        assert count == 5  # 4 unique (US-1, STORY-2, USER STORY 3, US-PET-001) → max(5,4)=5

    def test_empty_returns_fallback(self, engine):
        assert engine._extract_user_story_count({"docs/PRD.md": ""}) == 5

    def test_no_prd_returns_fallback(self, engine):
        assert engine._extract_user_story_count({}) == 5

    def test_alternative_us_formats(self, engine):
        prd = "### Story-1\n### User Story 2\n### US_3\n"
        count = engine._extract_user_story_count({"docs/PRD.md": prd})
        assert count == 5  # max(5, 3) = 5


# ── _extract_acceptance_criteria_count ───────────────────────────────────

class TestExtractAcceptanceCriteriaCount:
    def test_ac_per_us(self, engine, upstream_data):
        avg = engine._extract_acceptance_criteria_count(upstream_data)
        # PRD fixture: US-001=3 AC, US-002=2 AC, US-003=1 AC → avg=2
        assert avg >= 2

    def test_empty_returns_fallback(self, engine):
        assert engine._extract_acceptance_criteria_count({"docs/PRD.md": ""}) == 2

    def test_no_prd_returns_fallback(self, engine):
        assert engine._extract_acceptance_criteria_count({}) == 2

    def test_no_us_blocks_returns_fallback(self, engine):
        prd = "## Just prose, no US headers"
        assert engine._extract_acceptance_criteria_count({"docs/PRD.md": prd}) == 2

    def test_no_ac_in_blocks_returns_fallback(self, engine):
        prd = "### US-001 Title\n\n### US-002 Title\n\n"  # no AC items
        assert engine._extract_acceptance_criteria_count({"docs/PRD.md": prd}) == 2


# ── _extract_arch_layer_count ────────────────────────────────────────────

class TestExtractArchLayerCount:
    def test_numeric_h2_sections_primary(self, engine, upstream_data):
        # ARCH fixture has 7 numbered H2 sections (§1–§7)
        count = engine._extract_arch_layer_count(upstream_data)
        assert count == 7

    def test_h2_takes_priority_over_table(self, engine):
        # Even with a small table early, H2 sections win
        arch = """## §1 Overview
| Foo | Bar |
|---|---|
| a | b |
| c | d |

## §2 Components
## §3 Security
## §4 Deployment
"""
        assert engine._extract_arch_layer_count({"docs/ARCH.md": arch}) == 4

    def test_h2_dotted_form(self, engine):
        # Supports `## 1. Title` / `## 1 Title` (English-numbered)
        arch = "## 1. Foo\n## 2. Bar\n## 3. Baz\n"
        assert engine._extract_arch_layer_count({"docs/ARCH.md": arch}) == 3

    def test_empty_returns_fallback(self, engine):
        assert engine._extract_arch_layer_count({"docs/ARCH.md": ""}) == 4

    def test_no_arch_returns_fallback(self, engine):
        assert engine._extract_arch_layer_count({}) == 4

    def test_fallback_layer_heading(self, engine):
        # No numeric H2 → falls back to layer keyword headings
        arch = "### Frontend Layer\n### Backend Service\n"
        count = engine._extract_arch_layer_count({"docs/ARCH.md": arch})
        assert count == 2

    def test_table_only_last_resort(self, engine):
        # No H2, no layer headings, but a markdown table → tertiary fallback
        arch = """| Foo | Bar |
|---|---|
| a | 1 |
| b | 2 |
| c | 3 |
"""
        assert engine._extract_arch_layer_count({"docs/ARCH.md": arch}) == 3

    def test_no_table_no_heading_returns_default(self, engine):
        arch = "Just prose without table, layer headings, or numeric sections"
        assert engine._extract_arch_layer_count({"docs/ARCH.md": arch}) == 4


# ── _extract_component_count ─────────────────────────────────────────────

class TestExtractComponentCount:
    def test_h4_components(self, engine, upstream_data):
        count = engine._extract_component_count(upstream_data)
        # ARCH fixture has 5 #### components
        assert count >= 5

    def test_empty_returns_fallback(self, engine):
        assert engine._extract_component_count({"docs/ARCH.md": ""}) == 5

    def test_no_arch_returns_fallback(self, engine):
        assert engine._extract_component_count({}) == 5

    def test_fallback_to_bullet_items(self, engine):
        arch = "## Section\n- Component A\n- Component B\n- Component C\n- Component D\n- Component E\n- Component F\n"
        count = engine._extract_component_count({"docs/ARCH.md": arch})
        assert count == 6  # 6 bullets, max(5, min(6, 20)) = 6

    def test_clamp_max_20(self, engine):
        bullets = "\n".join([f"- Item{i}" for i in range(30)])
        arch = f"## Section\n{bullets}\n"
        assert engine._extract_component_count({"docs/ARCH.md": arch}) == 20


# ── extract_parameters orchestration ─────────────────────────────────────

class TestExtractParameters:
    def test_returns_all_seven_keys(self, engine, upstream_data):
        params = engine.extract_parameters(upstream_data)
        assert set(params.keys()) >= {
            "entity_count",
            "avg_entity_field_count",
            "rest_endpoint_count",
            "user_story_count",
            "acceptance_criteria_count",
            "arch_layer_count",
            "component_count",
        }

    def test_all_values_are_int(self, engine, upstream_data):
        params = engine.extract_parameters(upstream_data)
        for k, v in params.items():
            if k == "metadata":
                continue
            assert isinstance(v, int), f"{k} is {type(v).__name__}: {v!r}"

    def test_values_are_positive(self, engine, upstream_data):
        params = engine.extract_parameters(upstream_data)
        # Each metric has fallback ≥ 2, so all should be positive
        for k, v in params.items():
            if k == "metadata":
                continue
            assert v >= 1


# ── extract_metrics (legacy mapping) ─────────────────────────────────────

class TestExtractMetrics:
    def test_legacy_mapping(self, engine, project_dir):
        # extract_metrics calls extract_parameters internally → needs pipeline + upstream
        engine._load_pipeline()
        metrics = engine.extract_metrics()
        assert "entity_count" in metrics
        assert "rest_endpoint_count" in metrics
        assert "user_story_count" in metrics
        assert "layer_count" in metrics

    def test_self_metrics_populated(self, engine):
        engine._load_pipeline()
        engine.extract_metrics()
        assert engine.metrics  # non-empty


# ── _grep_count ──────────────────────────────────────────────────────────

class TestGrepCount:
    def test_match_count(self, engine, project_dir):
        edd = project_dir / "docs" / "EDD.md"
        c = engine._grep_count(edd, r"^\s*class\s+", fallback=0)
        assert c >= 1

    def test_missing_file_returns_fallback(self, engine, tmp_path):
        c = engine._grep_count(tmp_path / "nope.md", "x", fallback=7)
        assert c == 7

    def test_exception_returns_fallback(self, engine, tmp_path, monkeypatch):
        f = tmp_path / "f.md"
        f.write_text("x")

        def boom(*a, **kw):
            raise OSError("read error")

        monkeypatch.setattr(Path, "read_text", boom)
        c = engine._grep_count(f, "x", fallback=42)
        assert c == 42

    def test_zero_matches_returns_fallback(self, engine, tmp_path):
        f = tmp_path / "f.md"
        f.write_text("hello world")
        # max(fallback=10, 0 matches) → 10
        assert engine._grep_count(f, "ZZZ", fallback=10) == 10


# ── count_h2_lines (static) ──────────────────────────────────────────────

class TestCountH2Lines:
    def test_count_h2(self, tmp_path):
        f = tmp_path / "t.md"
        f.write_text("# Title\n## A\n## B\n### C\n## D\n")
        assert dryrun_core.DRYRUNEngine.count_h2_lines(f) == 3

    def test_no_h2(self, tmp_path):
        f = tmp_path / "t.md"
        f.write_text("# Title\n### subsection only\n")
        assert dryrun_core.DRYRUNEngine.count_h2_lines(f) == 0

    def test_missing_file_returns_zero(self, tmp_path):
        assert dryrun_core.DRYRUNEngine.count_h2_lines(tmp_path / "missing.md") == 0
