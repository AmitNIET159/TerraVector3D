"""Tests for src.audit_hash — SHA-256 hashing utilities."""

from __future__ import annotations

import tempfile
from pathlib import Path

from src.audit_hash import calculate_audit_hash, calculate_file_hash


class TestCalculateAuditHash:
    """Unit tests for calculate_audit_hash."""

    def test_string_hashing_deterministic(self) -> None:
        h1 = calculate_audit_hash("hello world")
        h2 = calculate_audit_hash("hello world")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_bytes_hashing(self) -> None:
        h = calculate_audit_hash(b"binary data")
        assert len(h) == 64

    def test_dict_hashing_sorted(self) -> None:
        h1 = calculate_audit_hash({"b": 2, "a": 1})
        h2 = calculate_audit_hash({"a": 1, "b": 2})
        assert h1 == h2

    def test_different_data_different_hash(self) -> None:
        h1 = calculate_audit_hash("data_a")
        h2 = calculate_audit_hash("data_b")
        assert h1 != h2

    def test_sample_input_hash(self, sample_raw_data: dict) -> None:
        h = calculate_audit_hash(sample_raw_data)
        assert len(h) == 64
        assert h == calculate_audit_hash(sample_raw_data)  # deterministic


class TestCalculateFileHash:
    """Unit tests for calculate_file_hash."""

    def test_file_hash(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content for hashing", encoding="utf-8")
        h = calculate_file_hash(test_file)
        assert len(h) == 64

    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        content = "identical content"
        f1.write_text(content, encoding="utf-8")
        f2.write_text(content, encoding="utf-8")
        assert calculate_file_hash(f1) == calculate_file_hash(f2)

