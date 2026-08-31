"""Shared validation patterns and utilities for Pydantic schemas."""

import re
from typing import Any

from pydantic import field_validator

# Canonical validation patterns
ULPIN_PATTERN = re.compile(r"^[A-Z0-9]{14}$")
VERTICAL_ID_PATTERN = re.compile(
    r"^[A-Z0-9]{14}-F(G|B[1-9]|[0-9]{2})-U[A-Z0-9]{1,16}-R[0-9]{2}$"
)
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def validate_parent_ulpin(value: str) -> str:
    """Validate parent ULPIN format: exactly 14 uppercase alphanumeric characters."""
    if not ULPIN_PATTERN.match(value):
        raise ValueError(
            f"Invalid parent_ulpin '{value}': must be exactly 14 uppercase "
            f"alphanumeric characters matching {ULPIN_PATTERN.pattern}"
        )
    return value


def validate_vertical_id(value: str) -> str:
    """Validate vertical ID format: <ULPIN>-F<level>-U<unit>-R<rev>."""
    if not VERTICAL_ID_PATTERN.match(value):
        raise ValueError(
            f"Invalid vertical_id '{value}': must match format "
            f"<ULPIN>-F<level>-U<unit_code>-R<revision>"
        )
    return value


def validate_sha256_hash(value: str) -> str:
    """Validate SHA-256 hash: exactly 64 lowercase hex characters."""
    if not SHA256_PATTERN.match(value):
        raise ValueError(
            f"Invalid sha256_hash: must be exactly 64 lowercase hex characters"
        )
    return value


def validate_z_range(z_min: float, z_max: float) -> None:
    """Validate that z_min_m < z_max_m."""
    if z_min >= z_max:
        raise ValueError(
            f"z_min_m ({z_min}) must be less than z_max_m ({z_max})"
        )


def validate_holder_masked(value: str) -> str:
    """Validate that holder_name_masked contains at least one asterisk."""
    if "*" not in value:
        raise ValueError(
            "holder_name_masked must contain at least one '*' character"
        )
    return value
