"""Shared pytest fixtures for bhudrishti_identity_rights tests."""

import os
import sys

# Ensure the package root is on sys.path so ``from src...`` imports work
# when running ``pytest tests/`` from the module directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402


# -- Sample ULPINs ---------------------------------------------------------

SAMPLE_ULPIN = "7A4B9C2D8E1F6G"
ALT_ULPIN = "1X2Y3Z4W5V6U7T"


# -- Pre-built valid IDs ---------------------------------------------------

VALID_FLOOR_4 = f"{SAMPLE_ULPIN}-F04-U401-R01"
VALID_BASEMENT_PARK = f"{SAMPLE_ULPIN}-FB1-UPARK24-R01"
VALID_GROUND_SHOP = f"{SAMPLE_ULPIN}-FG-USHOP01-R02"
VALID_BASEMENT_UTIL = f"{SAMPLE_ULPIN}-FB1-UUTIL01-R01"


@pytest.fixture
def sample_ulpin():
    return SAMPLE_ULPIN


@pytest.fixture
def alt_ulpin():
    return ALT_ULPIN


@pytest.fixture
def valid_floor_id():
    return VALID_FLOOR_4


@pytest.fixture
def valid_parking_id():
    return VALID_BASEMENT_PARK


@pytest.fixture
def valid_ground_id():
    return VALID_GROUND_SHOP


@pytest.fixture
def valid_util_id():
    return VALID_BASEMENT_UTIL
