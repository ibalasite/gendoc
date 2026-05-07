"""Targeted tests to close residual coverage gaps to 100%."""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import dryrun_core


# ── _load_upstream subprocess success path (lines 104-108) ───────────────

class TestLoadUpstreamSubprocessSuccess:
    def test_subprocess_returns_valid_json(self, engine):
        engine._load_pipeline()
        fake_output = {
            "step": "DRYRUN",
            "inputs": {"docs/EDD.md": "fake content"},
        }
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=json.dumps(fake_output), stderr=""
            )
            data = engine._load_upstream()
        assert data == {"docs/EDD.md": "fake content"}

    def test_subprocess_nonzero_falls_back(self, engine):
        engine._load_pipeline()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=2, stdout="", stderr="boom"
            )
            data = engine._load_upstream()
        # Falls back → reads files directly → 8 files
        assert len(data) == 8


# ── generate_manifest write error (lines 696-698) ────────────────────────

class TestGenerateManifestWriteError:
    def test_write_error_returns_false(self, engine, project_dir, monkeypatch):
        engine._load_pipeline()
        engine.extract_metrics()
        engine.derive_specifications()

        write_calls = []

        original_write_text = Path.write_text

        def selective_boom(self, *args, **kwargs):
            if self.name == "MANIFEST.md":
                raise OSError("disk full")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", selective_boom)
        result = engine.generate_manifest(
            str(project_dir / "templates" / "DRYRUN.md"),
            str(project_dir / "docs" / "MANIFEST.md"),
        )
        assert result is False


# ── _read_state exception (lines 754-755) ────────────────────────────────

class TestReadStateException:
    def test_invalid_json_returns_empty_dict(self, project_dir):
        state_file = project_dir / "bad.json"
        state_file.write_text("not valid json")
        eng = dryrun_core.DRYRUNEngine(str(project_dir), str(state_file))
        assert eng._read_state() == {}

    def test_missing_state_returns_empty_dict(self, project_dir):
        eng = dryrun_core.DRYRUNEngine(str(project_dir), "/nonexistent/state.json")
        assert eng._read_state() == {}


# ── _eval_step_condition non-always branches (lines 771-784) ─────────────

class TestEvalStepCondition:
    def test_always(self):
        assert dryrun_core.DRYRUNEngine._eval_step_condition("always", {}) is True

    def test_empty_treated_as_always(self):
        assert dryrun_core.DRYRUNEngine._eval_step_condition("", {}) is True
        assert dryrun_core.DRYRUNEngine._eval_step_condition(None, {}) is True

    def test_client_type_not_none_for_web(self):
        result = dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type != none", {"client_type": "web"}
        )
        assert result is True

    def test_client_type_not_none_for_empty(self):
        # Empty client_type is treated as 'none' equivalent
        result = dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type != none", {"client_type": ""}
        )
        assert result is False

    def test_client_type_not_none_for_api_only(self):
        # api-only also excluded (no UI)
        result = dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type != none", {"client_type": "api-only"}
        )
        assert result is False

    def test_client_type_not_api_only_for_web(self):
        result = dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type != api-only", {"client_type": "web"}
        )
        assert result is True

    def test_client_type_not_api_only_for_api_only(self):
        result = dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type != api-only", {"client_type": "api-only"}
        )
        assert result is False

    def test_client_type_eq_game_for_game(self):
        assert dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type == game", {"client_type": "game"}
        ) is True

    def test_client_type_eq_game_for_web(self):
        assert dryrun_core.DRYRUNEngine._eval_step_condition(
            "client_type == game", {"client_type": "web"}
        ) is False

    def test_has_admin_backend_true(self):
        assert dryrun_core.DRYRUNEngine._eval_step_condition(
            "has_admin_backend", {"has_admin_backend": True}
        ) is True

    def test_has_admin_backend_false(self):
        assert dryrun_core.DRYRUNEngine._eval_step_condition(
            "has_admin_backend", {"has_admin_backend": False}
        ) is False

    def test_unknown_condition_treated_as_active(self):
        # Unknown / unsupported conditions are conservative → active
        assert dryrun_core.DRYRUNEngine._eval_step_condition(
            "weird_undefined_token", {}
        ) is True


# ── arch_layer_count tertiary fallback break (line 314) ──────────────────

class TestArchLayerTableBreakAfterFirst:
    def test_table_followed_by_non_table_content_breaks_loop(self, engine):
        # No H2, no layer headings → falls to table fallback.
        # Table followed by prose triggers the `break  # first table done` line.
        arch = """| Tech | Vendor |
|---|---|
| Frontend | React |
| Backend | FastAPI |
| Database | Postgres |

This prose appears after the table to trigger the break.
| Another | Table |
|---|---|
| Should | Be ignored |
"""
        # First table has 3 data rows → returns 3 (max(2, 3))
        assert engine._extract_arch_layer_count({"docs/ARCH.md": arch}) == 3


# ── _build_manifest_replacements PLUS_N negative skip (line 833) ─────────

class TestPlusNNegativeBaseSkipped:
    def test_negative_base_skipped(self, engine):
        engine._load_pipeline()
        engine.extract_metrics()
        # Inject a negative-valued metric that would propagate to repl
        engine.metrics['negative_anchor'] = -5
        repl = engine._build_manifest_replacements()
        # Base placeholder should still be there
        assert repl.get('{{NEGATIVE_ANCHOR}}') == '-5'
        # But _PLUS_N variants must NOT be generated for negatives
        assert '{{NEGATIVE_ANCHOR_PLUS_1}}' not in repl
        assert '{{NEGATIVE_ANCHOR_PLUS_5}}' not in repl


# ── _build_manifest_replacements skipped_count branch (line 743) ─────────

class TestSkippedCountBranch:
    def test_step_with_failing_condition_counts_skipped(self, engine, project_dir):
        # Override pipeline to include a step that should be skipped
        custom = {
            "version": "v1",
            "steps": [
                {"id": "WEB_ONLY", "type": "X", "condition": "client_type != none", "spec_rules": {}},
                {"id": "ALWAYS", "type": "Y", "condition": "always", "spec_rules": {}},
            ],
        }
        (project_dir / "templates" / "pipeline.json").write_text(
            json.dumps(custom), encoding="utf-8"
        )
        # State has client_type=api-only → WEB_ONLY skipped
        (project_dir / ".gendoc-state.json").write_text(
            json.dumps({"client_type": "api-only"}), encoding="utf-8"
        )
        engine._load_pipeline()
        repl = engine._build_manifest_replacements()
        assert repl["{{ACTIVE_STEPS_COUNT}}"] == "1"
        assert repl["{{SKIPPED_STEPS_COUNT}}"] == "1"
        assert repl["{{WEB_ONLY_STATUS}}"] == "skipped"
        assert repl["{{ALWAYS_STATUS}}"] == "active"


# ── main() error paths (lines 860-901) ───────────────────────────────────

@pytest.fixture
def cli(monkeypatch):
    yield monkeypatch


class TestMainErrorPaths:
    def test_extract_parameters_failure(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])

        def boom(*a, **kw):
            raise RuntimeError("extract failed")

        cli.setattr(dryrun_core.DRYRUNEngine, "extract_parameters", boom)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1

    def test_derive_specifications_failure(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])

        def boom(self, params=None):
            raise RuntimeError("derive failed")

        cli.setattr(dryrun_core.DRYRUNEngine, "derive_specifications", boom)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1

    def test_generate_rules_returns_false(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
        cli.setattr(dryrun_core.DRYRUNEngine, "generate_rules_json", lambda self: False)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1

    def test_generate_rules_raises(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])

        def boom(self):
            raise RuntimeError("write boom")

        cli.setattr(dryrun_core.DRYRUNEngine, "generate_rules_json", boom)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1

    def test_embed_state_returns_false(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
        cli.setattr(dryrun_core.DRYRUNEngine, "embed_in_state_file", lambda self: False)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1

    def test_validate_completeness_returns_false(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
        cli.setattr(dryrun_core.DRYRUNEngine, "validate_completeness", lambda self: False)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1

    def test_validate_spec_quality_returns_false(self, cli, project_dir, state_file):
        cli.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
        cli.setattr(dryrun_core.DRYRUNEngine, "validate_spec_quality", lambda self: False)
        with pytest.raises(SystemExit) as exc:
            dryrun_core.main()
        assert exc.value.code == 1
