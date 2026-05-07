"""Tests for derive_specifications + _evaluate_spec_value + inject_multifile_baseline."""
import pytest


# ── _evaluate_spec_value ─────────────────────────────────────────────────

class TestEvaluateSpecValue:
    def test_int_passthrough(self, engine):
        assert engine._evaluate_spec_value(42, {}) == 42

    def test_float_to_int(self, engine):
        assert engine._evaluate_spec_value(3.7, {}) == 3

    def test_bool_passthrough(self, engine):
        assert engine._evaluate_spec_value(True, {}) is True
        assert engine._evaluate_spec_value(False, {}) is False

    def test_brace_substitution(self, engine):
        assert engine._evaluate_spec_value("max(5, {entity_count})", {"entity_count": 12}) == 12
        assert engine._evaluate_spec_value("max(5, {entity_count})", {"entity_count": 2}) == 5

    def test_bare_name_substitution(self, engine):
        assert engine._evaluate_spec_value("arch_layer_count + 4", {"arch_layer_count": 3}) == 7

    def test_ceil(self, engine):
        assert engine._evaluate_spec_value("ceil({user_story_count} * 0.8)", {"user_story_count": 10}) == 8

    def test_floor(self, engine):
        assert engine._evaluate_spec_value("floor({user_story_count} * 0.8)", {"user_story_count": 10}) == 8

    def test_min(self, engine):
        assert engine._evaluate_spec_value("min(100, {entity_count})", {"entity_count": 5}) == 5

    def test_round(self, engine):
        assert engine._evaluate_spec_value("round(3.6)", {}) == 4

    def test_abs(self, engine):
        assert engine._evaluate_spec_value("abs(-5)", {}) == 5

    def test_unresolved_returns_zero_fallback(self, engine):
        # Unknown identifier in expression → eval fails → fallback 0
        assert engine._evaluate_spec_value("unknown_token + 1", {"x": 1}) == 0

    def test_metadata_skipped(self, engine):
        # `metadata` key in params must not be substituted
        params = {"metadata": "ignore me", "entity_count": 5}
        assert engine._evaluate_spec_value("max(1, {entity_count})", params) == 5

    def test_other_type_returned_as_is(self, engine):
        # Non-int/float/bool/str → returned unchanged
        result = engine._evaluate_spec_value([1, 2, 3], {})
        assert result == [1, 2, 3]


# ── inject_multifile_baseline ────────────────────────────────────────────

class TestInjectMultifileBaseline:
    def test_html(self, engine, project_dir):
        # docs/ has 9 .md files in fixtures
        result = engine.inject_multifile_baseline({"id": "HTML"}, {})
        assert result["expected_html_files"] >= 1

    def test_html_no_docs(self, engine, project_dir):
        # Remove all docs and the dir
        import shutil
        shutil.rmtree(project_dir / "docs")
        result = engine.inject_multifile_baseline({"id": "HTML"}, {})
        assert result["expected_html_files"] == 1  # max(1, 0)

    def test_contracts(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "CONTRACTS"}, {"entity_count": 5}
        )
        assert result["expected_contract_count"] >= 1
        assert result["expected_schema_count"] == 5

    def test_contracts_no_api_md(self, engine, project_dir):
        (project_dir / "docs" / "API.md").unlink()
        result = engine.inject_multifile_baseline(
            {"id": "CONTRACTS"}, {"entity_count": 4}
        )
        assert result["expected_contract_count"] == 1  # max(1, 0)
        assert result["expected_schema_count"] == 4

    def test_mock(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "MOCK"}, {"rest_endpoint_count": 12, "entity_count": 5}
        )
        assert result["expected_mock_route_count"] == 12
        assert result["expected_mock_data_count"] == 5

    def test_prototype(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "PROTOTYPE"}, {}
        )
        assert result["expected_screen_count"] >= 3

    def test_prototype_no_prd(self, engine, project_dir):
        (project_dir / "docs" / "PRD.md").unlink()
        result = engine.inject_multifile_baseline({"id": "PROTOTYPE"}, {})
        assert result["expected_screen_count"] == 3  # max(3, 0)

    def test_uml(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "UML"},
            {"rest_endpoint_count": 12, "user_story_count": 10, "entity_count": 6},
        )
        assert result["required_type_coverage"] == 9
        assert result["expected_sequence_count"] >= 3
        assert result["expected_activity_count"] >= 3
        assert result["expected_state_count"] >= 1
        assert result["expected_class_files"] == 3

    def test_bdd_server(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "BDD-server"},
            {"user_story_count": 10, "acceptance_criteria_count": 3},
        )
        assert result["expected_scenario_count"] == 30  # 10 * 3

    def test_bdd_server_minimum_5(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "BDD-server"},
            {"user_story_count": 1, "acceptance_criteria_count": 1},
        )
        assert result["expected_scenario_count"] == 5  # max(5, 1*1)

    def test_bdd_client(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "BDD-client"},
            {"user_story_count": 10, "acceptance_criteria_count": 3},
        )
        # max(3, 10*3*6//10) = max(3, 18) = 18
        assert result["expected_client_scenario_count"] == 18

    def test_bdd_client_minimum_3(self, engine):
        result = engine.inject_multifile_baseline(
            {"id": "BDD-client"},
            {"user_story_count": 1, "acceptance_criteria_count": 1},
        )
        assert result["expected_client_scenario_count"] == 3

    def test_unknown_id_returns_empty(self, engine):
        assert engine.inject_multifile_baseline({"id": "UNKNOWN"}, {}) == {}


# ── derive_specifications ────────────────────────────────────────────────

class TestDeriveSpecifications:
    def test_basic_derivation(self, engine):
        engine._load_pipeline()
        specs = engine.derive_specifications({
            "entity_count": 5,
            "rest_endpoint_count": 12,
            "user_story_count": 8,
            "arch_layer_count": 4,
            "acceptance_criteria_count": 3,
        })
        # API: max(5, 12) = 12
        assert specs["API"]["min_endpoint_count"] == 12
        # SCHEMA: max(3, 5) = 5
        assert specs["SCHEMA"]["min_table_count"] == 5
        # API: arch_layer_count + 4 = 8 (overridden by template_h2_count if API.md exists)

    def test_lazy_param_extraction(self, engine):
        # No params passed → engine extracts them itself
        engine._load_pipeline()
        specs = engine.derive_specifications()
        assert "API" in specs

    def test_lazy_pipeline_load(self, engine):
        # No pipeline loaded → engine loads it lazily
        specs = engine.derive_specifications({
            "entity_count": 3, "rest_endpoint_count": 5,
            "user_story_count": 5, "arch_layer_count": 2,
            "acceptance_criteria_count": 2,
        })
        assert specs  # non-empty

    def test_template_h2_count_override(self, engine, project_dir):
        engine._load_pipeline()
        specs = engine.derive_specifications({
            "entity_count": 3, "rest_endpoint_count": 5,
            "user_story_count": 5, "arch_layer_count": 2,
            "acceptance_criteria_count": 2,
        })
        # API.md fixture has 4 ## sections, so min_h2_sections should be 4
        assert specs["API"].get("template_h2_count") == 4
        assert specs["API"]["min_h2_sections"] == 4

    def test_steps_without_spec_rules_skipped(self, engine):
        engine._load_pipeline()
        specs = engine.derive_specifications({
            "entity_count": 3, "rest_endpoint_count": 5,
            "user_story_count": 5, "arch_layer_count": 2,
            "acceptance_criteria_count": 2,
        })
        # IDEA, BRD, DRYRUN have no spec_rules → not in specs
        assert "IDEA" not in specs
        assert "BRD" not in specs
        assert "DRYRUN" not in specs

    def test_special_skill_strips_h2_sections(self, engine):
        engine._load_pipeline()
        specs = engine.derive_specifications({
            "entity_count": 3, "rest_endpoint_count": 5,
            "user_story_count": 5, "arch_layer_count": 2,
            "acceptance_criteria_count": 2,
        })
        # HTML has special_skill + multi_file → min_h2_sections removed
        assert "min_h2_sections" not in specs.get("HTML", {})

    def test_multifile_uses_inject_baseline(self, engine):
        engine._load_pipeline()
        specs = engine.derive_specifications({
            "entity_count": 3, "rest_endpoint_count": 5,
            "user_story_count": 5, "arch_layer_count": 2,
            "acceptance_criteria_count": 2,
        })
        # BDD-server: multi_file → expected_scenario_count from inject (5*2=10)
        assert "expected_scenario_count" in specs["BDD-server"]
