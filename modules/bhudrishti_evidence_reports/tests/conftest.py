"""
Shared pytest fixtures for bhudrishti_evidence_reports tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models import ValidationInput


_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
_SAMPLE_INPUT = _EXAMPLES_DIR / "sample_input.json"


@pytest.fixture()
def sample_raw_data() -> dict:
    """Return the sample input as a raw dict."""
    with open(_SAMPLE_INPUT, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture()
def sample_input(sample_raw_data: dict) -> ValidationInput:
    """Return the sample input as a validated :class:`ValidationInput`."""
    return ValidationInput(**sample_raw_data)


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary output directory."""
    out = tmp_path / "report_output"
    out.mkdir()
    return out
