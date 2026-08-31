"""Tests for src.qr_verification — QR code generation."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from src.qr_verification import (
    build_qr_payload,
    generate_qr_code_base64,
    generate_qr_code_bytes,
    save_qr_code,
)


class TestBuildQRPayload:
    """Verify QR payload structure."""

    def test_payload_keys(self) -> None:
        payload = build_qr_payload(
            report_id="RPT-TEST123",
            parent_ulpin="7A4B9C2D8E1F6G",
            timestamp="2024-11-20T12:00:00+05:30",
            sha256_hash="a" * 64,
        )
        assert payload["report_id"] == "RPT-TEST123"
        assert payload["parent_ulpin"] == "7A4B9C2D8E1F6G"
        assert payload["verification_type"] == "bhudrishti_3d_local"
        assert "timestamp" in payload
        assert "sha256_hash" in payload


class TestGenerateQRCodeBase64:
    """Verify base64-encoded QR output."""

    def test_returns_valid_base64_png(self) -> None:
        payload = build_qr_payload("RPT-1", "7A4B9C2D8E1F6G", "2024-01-01", "b" * 64)
        b64 = generate_qr_code_base64(payload)
        raw = base64.b64decode(b64)
        # PNG magic bytes
        assert raw[:4] == b"\x89PNG"

    def test_deterministic(self) -> None:
        payload = build_qr_payload("RPT-1", "7A4B9C2D8E1F6G", "2024-01-01", "c" * 64)
        assert generate_qr_code_base64(payload) == generate_qr_code_base64(payload)


class TestGenerateQRCodeBytes:
    """Verify raw PNG bytes output."""

    def test_returns_png_bytes(self) -> None:
        payload = build_qr_payload("RPT-2", "7A4B9C2D8E1F6G", "2024-01-01", "d" * 64)
        raw = generate_qr_code_bytes(payload)
        assert isinstance(raw, bytes)
        assert raw[:4] == b"\x89PNG"


class TestSaveQRCode:
    """Verify QR code file output."""

    def test_saves_png_file(self, tmp_path: Path) -> None:
        payload = build_qr_payload("RPT-3", "7A4B9C2D8E1F6G", "2024-01-01", "e" * 64)
        out = tmp_path / "qr.png"
        result = save_qr_code(payload, out)
        assert result.exists()
        assert result.stat().st_size > 0
        # Verify PNG header
        assert result.read_bytes()[:4] == b"\x89PNG"

