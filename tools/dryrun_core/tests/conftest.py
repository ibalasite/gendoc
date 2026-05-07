"""Shared pytest fixtures for dryrun_core tests."""
import json
import shutil
import sys
from pathlib import Path

import pytest

# Make dryrun_core importable (tests/ → tools/dryrun_core/)
_PKG_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PKG_DIR))

import dryrun_core  # noqa: E402

FIXTURES_DIR = _PKG_DIR / "fixtures"


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Set up a fake target project with sample upstream + templates + state."""
    # Copy fixtures into tmp project
    shutil.copytree(FIXTURES_DIR / "docs", tmp_path / "docs")
    shutil.copytree(FIXTURES_DIR / "templates", tmp_path / "templates")
    # Place state file at the root (DRYRUNEngine receives the path explicitly)
    state_src = FIXTURES_DIR / "state.json"
    (tmp_path / ".gendoc-state.json").write_text(state_src.read_text(), encoding="utf-8")
    return tmp_path


@pytest.fixture
def state_file(project_dir: Path) -> Path:
    return project_dir / ".gendoc-state.json"


@pytest.fixture
def engine(project_dir: Path, state_file: Path):
    """A fresh DRYRUNEngine bound to the fake project."""
    return dryrun_core.DRYRUNEngine(str(project_dir), str(state_file))


@pytest.fixture
def upstream_data(project_dir: Path) -> dict:
    """Map of every upstream filename to its content (mimics get-upstream output)."""
    upstream = {}
    for fname in (
        "IDEA.md",
        "BRD.md",
        "PRD.md",
        "CONSTANTS.md",
        "PDD.md",
        "VDD.md",
        "EDD.md",
        "ARCH.md",
    ):
        path = project_dir / "docs" / fname
        upstream[f"docs/{fname}"] = path.read_text(encoding="utf-8")
    return upstream
