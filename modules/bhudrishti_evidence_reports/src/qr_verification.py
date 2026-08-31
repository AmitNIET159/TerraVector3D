"""
QR-code generation for BhuDrishti 3D local verification.

The QR payload is a compact JSON document containing:
- report_id
- parent_ulpin
- timestamp
- sha256_hash
- verification_type  (always ``bhudrishti_3d_local``)

No internet URL is required; verification is purely local.
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import qrcode
from PIL import Image as PILImage


def build_qr_payload(
    report_id: str,
    parent_ulpin: str,
    timestamp: str,
    sha256_hash: str,
) -> dict[str, str]:
    """Construct the canonical QR verification payload."""
    return {
        "report_id": report_id,
        "parent_ulpin": parent_ulpin,
        "timestamp": timestamp,
        "sha256_hash": sha256_hash,
        "verification_type": "bhudrishti_3d_local",
    }


def generate_qr_code_base64(payload: dict[str, Any]) -> str:
    """Return a Base-64-encoded PNG of the QR code for *payload*."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(payload, sort_keys=True))
    qr.make(fit=True)
    img: PILImage.Image = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def generate_qr_code_bytes(payload: dict[str, Any]) -> bytes:
    """Return raw PNG bytes of the QR code for *payload*."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(payload, sort_keys=True))
    qr.make(fit=True)
    img: PILImage.Image = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def save_qr_code(payload: dict[str, Any], output_path: str | Path) -> Path:
    """Write the QR code PNG to *output_path* and return the path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(generate_qr_code_bytes(payload))
    return output_path

