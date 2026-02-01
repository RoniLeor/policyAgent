"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_pdfs_dir(project_root: Path) -> Path:
    """Get sample PDFs directory."""
    return project_root / "tests" / "fixtures" / "pdfs"


@pytest.fixture
def models_dir(project_root: Path) -> Path:
    """Get models directory."""
    return project_root / "models"


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    yield output_dir
