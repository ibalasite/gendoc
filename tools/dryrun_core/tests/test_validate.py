"""Tests for validate_completeness + validate_spec_quality + print_metrics_summary."""
import pytest


@pytest.fixture
def derived_engine(engine):
    engine._load_pipeline()
    engine.extract_metrics()
    engine.derive_specifications({
        "entity_count": 5,
        "rest_endpoint_count": 12,
        "user_story_count": 8,
        "arch_layer_count": 4,
        "acceptance_criteria_count": 3,
    })
    return engine


# ── validate_completeness ────────────────────────────────────────────────

class TestValidateCompleteness:
    def test_passes_when_specs_valid(self, derived_engine):
        assert derived_engine.validate_completeness() is True

    def test_fails_when_no_specs(self, engine):
        # No specs derived
        assert engine.validate_completeness() is False

    def test_fails_on_empty_step_spec(self, derived_engine):
        derived_engine.step_specs["EMPTY"] = {}
        assert derived_engine.validate_completeness() is False

    def test_fails_on_non_int_value(self, derived_engine):
        derived_engine.step_specs["BAD"] = {"min_x": "not_an_int"}
        assert derived_engine.validate_completeness() is False

    def test_fails_on_non_dict_value(self, derived_engine):
        derived_engine.step_specs["BAD"] = "not_a_dict"
        assert derived_engine.validate_completeness() is False


# ── validate_spec_quality ────────────────────────────────────────────────

class TestValidateSpecQuality:
    def test_passes_with_valid_specs(self, derived_engine):
        assert derived_engine.validate_spec_quality() is True

    def test_warns_when_missing_quantitative(self, derived_engine, capsys):
        # Add a downstream step with no min_*/max_*
        derived_engine.step_specs["API"] = {"some_other_key": True}
        # Still passes (warning, not error)
        assert derived_engine.validate_spec_quality() is True
        captured = capsys.readouterr()
        assert "warnings" in captured.out.lower() or "warning" in captured.out.lower()

    def test_fails_on_unresolved_placeholder(self, derived_engine):
        derived_engine.step_specs["API"] = {"min_x": 5, "extra": "{{LEFTOVER}}"}
        assert derived_engine.validate_spec_quality() is False

    def test_fails_on_negative_value(self, derived_engine):
        derived_engine.step_specs["API"] = {"min_x": -1}
        assert derived_engine.validate_spec_quality() is False

    def test_passes_on_bool_value(self, derived_engine):
        derived_engine.step_specs["API"] = {"min_x": 5, "flag": True}
        assert derived_engine.validate_spec_quality() is True


# ── print_metrics_summary ────────────────────────────────────────────────

class TestPrintMetricsSummary:
    def test_prints_without_error(self, engine, capsys):
        engine._load_pipeline()
        engine.extract_metrics()
        engine.print_metrics_summary()
        captured = capsys.readouterr()
        assert "Extracted Metrics Summary" in captured.out

    def test_prints_with_empty_metrics(self, engine, capsys):
        # No extract_metrics() called → self.metrics is {}
        engine.print_metrics_summary()
        captured = capsys.readouterr()
        # All defaults to 0
        assert "0" in captured.out
