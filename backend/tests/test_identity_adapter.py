"""Tests for the identity service adapter."""
import sys
from pathlib import Path
import pytest
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.identity_service import IdentityService

@pytest.fixture
def identity_service():
    return IdentityService()

def test_generate_vertical_id(identity_service):
    result = identity_service.generate("7A4B9C2D8E1F6G", "04", "401", 1)
    assert result["vertical_id"] == "7A4B9C2D8E1F6G-F04-U401-R01"

def test_validate_valid_id(identity_service):
    result = identity_service.validate("7A4B9C2D8E1F6G-F04-U401-R01")
    assert result["is_valid"] is True
