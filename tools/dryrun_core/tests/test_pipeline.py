"""Tests for pipeline loading + upstream validation + main()."""
import json
import sys
from pathlib import Path

import pytest

import dryrun_core


# ── _load_pipeline ───────────────────────────────────────────────────────

class TestLoadPipeline:
    def test_load_local_pipeline(self, engine):
        pipe = engine._load_pipeline()
        assert pipe["version"] == "test-v1"
        assert any(s["id"] == "DRYRUN" for s in pipe["steps"])

    def test_invalid_json_raises(self, project_dir, state_file):
        bad = project_dir / "templates" / "pipeline.json"
        bad.write_text("{not valid json", encoding="utf-8")
        eng = dryrun_core.DRYRUNEngine(str(project_dir), str(state_file))
        with pytest.raises(ValueError, match="Invalid JSON"):
            eng._load_pipeline()

    def test_missing_pipeline_uses_runtime_fallback(self, project_dir, state_file, tmp_path, monkeypatch):
        # Remove local pipeline; point HOME to tmp dir without runtime template too
        (project_dir / "templates" / "pipeline.json").unlink()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        eng = dryrun_core.DRYRUNEngine(str(project_dir), str(state_file))
        with pytest.raises(FileNotFoundError):
            eng._load_pipeline()

    def test_runtime_fallback_succeeds(self, project_dir, state_file, tmp_path, monkeypatch):
        # Remove local pipeline
        (project_dir / "templates" / "pipeline.json").unlink()
        # Create runtime location with a valid pipeline
        rt_dir = tmp_path / ".claude" / "skills" / "gendoc" / "templates"
        rt_dir.mkdir(parents=True)
        (rt_dir / "pipeline.json").write_text(json.dumps({"version": "rt", "steps": []}), encoding="utf-8")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        eng = dryrun_core.DRYRUNEngine(str(project_dir), str(state_file))
        pipe = eng._load_pipeline()
        assert pipe["version"] == "rt"


# ── validate_dryrun_upstream ─────────────────────────────────────────────

class TestValidateDryrunUpstream:
    def test_all_present(self, engine):
        assert engine.validate_dryrun_upstream() is True

    def test_missing_files(self, engine, project_dir):
        (project_dir / "docs" / "EDD.md").unlink()
        (project_dir / "docs" / "PRD.md").unlink()
        assert engine.validate_dryrun_upstream() is False


# ── _load_upstream ───────────────────────────────────────────────────────

class TestLoadUpstream:
    def test_get_upstream_failure_falls_back_to_direct_read(self, engine):
        # No tools/bin/get-upstream.sh in test project → subprocess fails → fallback
        engine._load_pipeline()
        data = engine._load_upstream()
        assert "docs/EDD.md" in data
        assert "docs/PRD.md" in data
        assert len(data) == 8  # all 8 Phase A files via fallback

    def test_no_dryrun_step_raises(self, project_dir, state_file):
        # Pipeline without DRYRUN
        (project_dir / "templates" / "pipeline.json").write_text(
            json.dumps({"version": "v", "steps": [{"id": "OTHER"}]}), encoding="utf-8"
        )
        eng = dryrun_core.DRYRUNEngine(str(project_dir), str(state_file))
        eng._load_pipeline()
        with pytest.raises(ValueError, match="DRYRUN step not found"):
            eng._load_upstream()


# ── extract_parameters lazy load ─────────────────────────────────────────

class TestExtractParametersLazy:
    def test_no_data_lazy_loads(self, engine):
        # No upstream_data passed → engine should _load_upstream itself
        engine._load_pipeline()
        params = engine.extract_parameters()
        assert "entity_count" in params
        assert params["entity_count"] >= 3
