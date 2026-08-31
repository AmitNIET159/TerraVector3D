"""Tests for Pydantic schema validation."""
import sys
from pathlib import Path
import pytest
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.common import validate_parent_ulpin, validate_vertical_id, validate_sha256_hash, validate_z_range, validate_holder_masked
from app.schemas.validation import IdentityGenerateRequest

def test_valid_ulpin():
    assert validate_parent_ulpin("7A4B9C2D8E1F6G") == "7A4B9C2D8E1F6G"

def test_ulpin_too_short():
    with pytest.raises(ValueError):
        validate_parent_ulpin("7A4B9C2D8E1F6")

def test_valid_vertical_id():
    assert validate_vertical_id("7A4B9C2D8E1F6G-F04-U401-R01") == "7A4B9C2D8E1F6G-F04-U401-R01"

def test_valid_sha256():
    valid_hash = "a" * 64
    assert validate_sha256_hash(valid_hash) == valid_hash

def test_valid_z_range():
    validate_z_range(0.0, 3.0)

def test_invalid_z_range_equal():
    with pytest.raises(ValueError):
        validate_z_range(3.0, 3.0)

def test_valid_holder_masked():
    assert validate_holder_masked("R***A") == "R***A"

def test_holder_not_masked():
    with pytest.raises(ValueError):
        validate_holder_masked("Ramesh Kumar")
