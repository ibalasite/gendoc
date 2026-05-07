"""Tests for generate_rules_json + generate_manifest + embed_in_state_file."""
import json
import re
from pathlib import Path

import pytest


@pytest.fixture
def derived_engine(engine):
    """Engine with pipeline loaded + specs derived."""
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


# ── generate_rules_json ──────────────────────────────────────────────────

class TestGenerateRulesJson:
    def test_writes_lowercase_files(self, derived_engine, project_dir):
        derived_engine.generate_rules_json()
        # Critical: dryrun_core writes <step_id>.lower()-rules.json
        # Use iterdir to inspect actual on-disk filenames (case-sensitive on Linux,
        # but iterdir reports the stored name even on case-insensitive macOS APFS).
        names = sorted(p.name for p in (project_dir / ".gendoc-rules").iterdir())
        assert "api-rules.json" in names
        assert "schema-rules.json" in names
        assert "bdd-server-rules.json" in names
        # Uppercase variant must NOT exist as the stored name
        assert "API-rules.json" not in names

    def test_json_is_flat_int_dict(self, derived_engine, project_dir):
        derived_engine.generate_rules_json()
        api_rules = json.loads(
            (project_dir / ".gendoc-rules" / "api-rules.json").read_text()
        )
        # Must be flat dict with int values (not nested with step_id/type/etc)
        assert all(isinstance(v, (int, bool)) for v in api_rules.values()), \
            f"Non-int values: {api_rules}"

    def test_no_formula_string_remains(self, derived_engine, project_dir):
        derived_engine.generate_rules_json()
        for rules_file in (project_dir / ".gendoc-rules").glob("*.json"):
            content = rules_file.read_text()
            assert "{" + "rest_endpoint_count" + "}" not in content
            assert "max(" not in content
            assert "ceil(" not in content

    def test_returns_true_on_success(self, derived_engine):
        assert derived_engine.generate_rules_json() is True

    def test_returns_false_on_write_failure(self, derived_engine, project_dir, monkeypatch):
        # Make the rules dir unwritable
        def boom(*args, **kwargs):
            raise OSError("disk full")
        monkeypatch.setattr(Path, "write_text", boom)
        assert derived_engine.generate_rules_json() is False


# ── generate_manifest (THE BUG) ──────────────────────────────────────────

class TestGenerateManifest:
    """Critical: generate_manifest must replace ALL placeholders or fail loudly.

    Iron Law (PRD §7.10): produces full MANIFEST.md or exits with error.
    NEVER leave bare {{PLACEHOLDER}} in output silently.
    """

    def test_no_bare_placeholder_after_substitution(self, derived_engine, project_dir):
        """All {{X}} must be substituted, except the literal {{PLACEHOLDER}} sentinel."""
        derived_engine.extract_metrics()
        template_path = project_dir / "templates" / "DRYRUN.md"
        output_path = project_dir / "docs" / "MANIFEST.md"

        success = derived_engine.generate_manifest(str(template_path), str(output_path))
        assert success is True

        manifest = output_path.read_text()
        # Find all bare {{X}} placeholders, excluding the literal sentinel
        bare = re.findall(r"\{\{([A-Z_]+)\}\}", manifest)
        bare_non_sentinel = [p for p in bare if p != "PLACEHOLDER"]
        assert bare_non_sentinel == [], \
            f"Bare placeholders remained: {bare_non_sentinel}"

    def test_quantitative_anchors_substituted(self, derived_engine, project_dir):
        derived_engine.extract_metrics()
        template_path = project_dir / "templates" / "DRYRUN.md"
        output_path = project_dir / "docs" / "MANIFEST.md"
        derived_engine.generate_manifest(str(template_path), str(output_path))
        manifest = output_path.read_text()

        # ENTITY_COUNT etc must be replaced with real numbers
        assert "{{ENTITY_COUNT}}" not in manifest
        assert "{{REST_ENDPOINT_COUNT}}" not in manifest
        assert "{{USER_STORY_COUNT}}" not in manifest
        assert "{{ARCH_LAYER_COUNT}}" not in manifest

    def test_state_fields_substituted(self, derived_engine, project_dir):
        """CLIENT_TYPE, HAS_ADMIN_BACKEND must come from state file."""
        derived_engine.extract_metrics()
        template_path = project_dir / "templates" / "DRYRUN.md"
        output_path = project_dir / "docs" / "MANIFEST.md"
        derived_engine.generate_manifest(str(template_path), str(output_path))
        manifest = output_path.read_text()
        assert "{{CLIENT_TYPE}}" not in manifest
        assert "{{HAS_ADMIN_BACKEND}}" not in manifest
        # State file fixture has client_type=web, has_admin_backend=true
        assert "web" in manifest
        assert "true" in manifest or "True" in manifest

    def test_step_status_substituted(self, derived_engine, project_dir):
        """API_STATUS, SCHEMA_STATUS, etc must be derived from step_specs."""
        derived_engine.extract_metrics()
        template_path = project_dir / "templates" / "DRYRUN.md"
        output_path = project_dir / "docs" / "MANIFEST.md"
        derived_engine.generate_manifest(str(template_path), str(output_path))
        manifest = output_path.read_text()
        assert "{{API_STATUS}}" not in manifest
        assert "{{SCHEMA_STATUS}}" not in manifest
        assert "{{BDD_SERVER_STATUS}}" not in manifest
        assert "{{HTML_STATUS}}" not in manifest

    def test_active_skipped_counts_substituted(self, derived_engine, project_dir):
        derived_engine.extract_metrics()
        template_path = project_dir / "templates" / "DRYRUN.md"
        output_path = project_dir / "docs" / "MANIFEST.md"
        derived_engine.generate_manifest(str(template_path), str(output_path))
        manifest = output_path.read_text()
        assert "{{ACTIVE_STEPS_COUNT}}" not in manifest
        assert "{{SKIPPED_STEPS_COUNT}}" not in manifest

    def test_sentinel_literal_preserved(self, derived_engine, project_dir):
        """{{PLACEHOLDER}} is a literal sentinel and must remain unsubstituted."""
        derived_engine.extract_metrics()
        template_path = project_dir / "templates" / "DRYRUN.md"
        output_path = project_dir / "docs" / "MANIFEST.md"
        derived_engine.generate_manifest(str(template_path), str(output_path))
        manifest = output_path.read_text()
        assert "{{PLACEHOLDER}}" in manifest

    def test_plus_n_arithmetic_substitution(self, derived_engine, project_dir, tmp_path):
        """{{XXX_PLUS_N}} should resolve to value(XXX) + N (DRYRUN_DEV_FEEDBACK feedback)."""
        derived_engine.extract_metrics()
        # Custom template using _PLUS_N expansion
        custom = tmp_path / "PLUS.md"
        custom.write_text(
            "Layers: {{ARCH_LAYER_COUNT}}\n"
            "Layers+2: {{ARCH_LAYER_COUNT_PLUS_2}}\n"
            "Layers+5: {{ARCH_LAYER_COUNT_PLUS_5}}\n"
            "Entities+1: {{ENTITY_COUNT_PLUS_1}}\n",
            encoding="utf-8",
        )
        output = tmp_path / "OUT.md"
        success = derived_engine.generate_manifest(str(custom), str(output))
        assert success is True

        text = output.read_text()
        # Should have NO bare placeholder
        import re
        bare = re.findall(r"\{\{([A-Z_]+)\}\}", text)
        bare_non_sentinel = [p for p in bare if p != "PLACEHOLDER"]
        assert bare_non_sentinel == [], f"Bare: {bare_non_sentinel}"

        # Verify arithmetic: parse out values
        import re as _re
        m_layers = _re.search(r"Layers: (\d+)", text)
        m_plus2 = _re.search(r"Layers\+2: (\d+)", text)
        m_plus5 = _re.search(r"Layers\+5: (\d+)", text)
        assert int(m_plus2.group(1)) == int(m_layers.group(1)) + 2
        assert int(m_plus5.group(1)) == int(m_layers.group(1)) + 5

    def test_plus_n_unknown_base_still_fails(self, derived_engine, project_dir, tmp_path):
        """If base anchor doesn't exist (e.g. UNKNOWN_PLUS_3), still fail-fast."""
        derived_engine.extract_metrics()
        bad = tmp_path / "BAD.md"
        bad.write_text("{{UNKNOWN_TOKEN_PLUS_3}}\n", encoding="utf-8")
        result = derived_engine.generate_manifest(
            str(bad), str(project_dir / "docs" / "MANIFEST.md")
        )
        assert result is False

    def test_returns_false_on_template_missing(self, derived_engine, project_dir):
        result = derived_engine.generate_manifest(
            "/nonexistent/template.md",
            str(project_dir / "docs" / "MANIFEST.md"),
        )
        assert result is False

    def test_fails_loudly_on_unsubstituted_placeholder(self, derived_engine, project_dir, tmp_path):
        """Iron Law: if any non-sentinel placeholder remains, return False."""
        bad_template = tmp_path / "bad.md"
        bad_template.write_text("{{UNKNOWN_ANCHOR}}\n", encoding="utf-8")
        derived_engine.extract_metrics()
        result = derived_engine.generate_manifest(
            str(bad_template),
            str(project_dir / "docs" / "MANIFEST.md"),
        )
        assert result is False, "Must return False when bare placeholders remain"


# ── embed_in_state_file ──────────────────────────────────────────────────

class TestEmbedInStateFile:
    def test_writes_step_specifications(self, derived_engine, state_file):
        derived_engine.embed_in_state_file()
        state = json.loads(state_file.read_text())
        assert "step_specifications" in state
        assert "API" in state["step_specifications"]

    def test_writes_dryrun_metadata(self, derived_engine, state_file):
        derived_engine.embed_in_state_file()
        state = json.loads(state_file.read_text())
        meta = state["dryrun_metadata"]
        assert "extraction_timestamp" in meta
        assert "extracted_metrics_count" in meta
        assert "derived_step_specs_count" in meta
        assert "dryrun_engine_version" in meta

    def test_returns_true_on_success(self, derived_engine):
        assert derived_engine.embed_in_state_file() is True

    def test_returns_false_on_write_error(self, derived_engine, monkeypatch):
        def boom(*a, **kw):
            raise OSError("write fail")
        monkeypatch.setattr(Path, "write_text", boom)
        assert derived_engine.embed_in_state_file() is False
