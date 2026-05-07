"""Tests for main() CLI entry point — integration coverage."""
import json
import sys
from pathlib import Path

import pytest

import dryrun_core


@pytest.fixture
def cli_args(monkeypatch):
    """Reset sys.argv between tests."""
    original = sys.argv[:]
    yield monkeypatch
    sys.argv = original


def test_main_too_few_args_exits(cli_args):
    cli_args.setattr(sys, "argv", ["dryrun_core.py"])
    with pytest.raises(SystemExit) as exc:
        dryrun_core.main()
    assert exc.value.code == 1


def test_main_full_pipeline(cli_args, project_dir, state_file):
    cli_args.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
    # Should run end-to-end and not raise
    dryrun_core.main()
    # Verify outputs
    assert (project_dir / ".gendoc-rules").is_dir()
    assert any((project_dir / ".gendoc-rules").iterdir())
    state = json.loads(state_file.read_text())
    assert "step_specifications" in state


def test_main_with_template_generates_manifest(cli_args, project_dir, state_file):
    template_path = project_dir / "templates" / "DRYRUN.md"
    cli_args.setattr(
        sys,
        "argv",
        [
            "dryrun_core.py",
            str(project_dir),
            str(state_file),
            "--template",
            str(template_path),
        ],
    )
    dryrun_core.main()
    manifest = project_dir / "docs" / "MANIFEST.md"
    assert manifest.exists()
    text = manifest.read_text()
    # No bare placeholders (except sentinel)
    import re
    bare = re.findall(r"\{\{([A-Z_]+)\}\}", text)
    bare_non_sentinel = [p for p in bare if p != "PLACEHOLDER"]
    assert bare_non_sentinel == [], f"Bare placeholders: {bare_non_sentinel}"


def test_main_pipeline_load_failure_exits(cli_args, project_dir, state_file):
    # Corrupt the pipeline.json
    (project_dir / "templates" / "pipeline.json").write_text("not json")
    cli_args.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
    with pytest.raises(SystemExit) as exc:
        dryrun_core.main()
    assert exc.value.code == 1


def test_main_missing_upstream_exits(cli_args, project_dir, state_file):
    # Remove required upstream
    (project_dir / "docs" / "EDD.md").unlink()
    cli_args.setattr(sys, "argv", ["dryrun_core.py", str(project_dir), str(state_file)])
    with pytest.raises(SystemExit) as exc:
        dryrun_core.main()
    assert exc.value.code == 1


def test_main_template_substitution_failure_exits(cli_args, project_dir, state_file):
    """If template has unrecognized placeholder, main should exit 1."""
    bad = project_dir / "templates" / "BAD.md"
    bad.write_text("{{UNKNOWN_TOKEN_XYZ}}\n", encoding="utf-8")
    cli_args.setattr(
        sys,
        "argv",
        [
            "dryrun_core.py",
            str(project_dir),
            str(state_file),
            "--template",
            str(bad),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        dryrun_core.main()
    assert exc.value.code == 1
