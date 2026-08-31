"""Tests for src.report_generator — full pipeline tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models import ValidationInput, mask_holder_name
from src.report_generator import (
    DISCLAIMER,
    create_verification_manifest,
    generate_html_report,
    generate_pdf_report,
    generate_report,
    mask_holder_name as rg_mask_holder_name,
)


class TestMaskHolderName:
    """Holder-name masking for privacy."""

    @pytest.mark.parametrize(
        "name,expected",
        [
            ("Sneha Patil", "Sn**a Pa**l"),
            ("A B", "A* B*"),
            ("Jo", "J*"),
        ],
    )
    def test_mask_patterns(self, name: str, expected: str) -> None:
        assert mask_holder_name(name) == expected

    def test_mask_hides_middle_chars(self) -> None:
        result = mask_holder_name("Priya Deshmukh")
        assert result.startswith("Pr")
        assert "*" in result
        assert len(result) == len("Priya Deshmukh")

    def test_re_export_from_report_generator(self) -> None:
        """mask_holder_name is re-exported from report_generator for compat."""
        assert rg_mask_holder_name("Test Name") == mask_holder_name("Test Name")


class TestGenerateHTMLReport:
    """HTML report generation."""

    def test_returns_html_string(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contains_title(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert "BhuDrishti 3D" in html
        assert "Vertical Property Validation Report" in html

    def test_contains_ulpin(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert "7A4B9C2D8E1F6G" in html

    def test_contains_disclaimer(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert "Prototype decision-support output" in html

    def test_contains_qr_code(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert "data:image/png;base64," in html

    def test_contains_conflict_sections(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert "CONF-001" in html
        assert "CONF-002" in html
        assert "CONF-003" in html

    def test_contains_conflict_type(self, sample_input: ValidationInput) -> None:
        html = generate_html_report(sample_input)
        assert "boundary_overlap" in html
        assert "encroachment" in html

    def test_writes_file(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.html"
        generate_html_report(sample_input, output_path=out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_accepts_dict_input(self, sample_raw_data: dict) -> None:
        html = generate_html_report(sample_raw_data)
        assert "7A4B9C2D8E1F6G" in html

    def test_displays_holder_name_masked(self, sample_input: ValidationInput) -> None:
        """HTML report uses holder_name_masked, not raw names."""
        html = generate_html_report(sample_input)
        assert "Sn**a Pa**l" in html
        assert "An***a Bh**t" in html


class TestGeneratePDFReport:
    """PDF report generation."""

    def test_generates_pdf_file(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.pdf"
        result = generate_pdf_report(sample_input, out)
        assert Path(result).exists()
        with open(result, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_pdf_nonzero_size(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.pdf"
        generate_pdf_report(sample_input, out)
        assert out.stat().st_size > 1000


class TestCreateVerificationManifest:
    """Verification manifest generation."""

    def test_manifest_keys(self, sample_input: ValidationInput) -> None:
        manifest = create_verification_manifest(sample_input)
        assert "report_id" in manifest
        assert "parent_ulpin" in manifest
        assert "input_hash" in manifest
        assert "qr_payload" in manifest
        assert "summary" in manifest
        assert "disclaimer" in manifest

    def test_manifest_summary_values(
        self, sample_input: ValidationInput
    ) -> None:
        manifest = create_verification_manifest(sample_input)
        s = manifest["summary"]
        assert s["num_floors"] == 6
        assert s["num_units"] == 8
        assert s["num_conflicts"] == 3

    def test_writes_json_file(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        out = tmp_path / "manifest.json"
        create_verification_manifest(sample_input, output_path=out)
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["parent_ulpin"] == "7A4B9C2D8E1F6G"


class TestGenerateReport:
    """Full pipeline integration test."""

    def test_full_pipeline(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        result = generate_report(sample_input, output_dir=tmp_path)

        assert Path(result["html_path"]).exists()
        assert Path(result["pdf_path"]).exists()
        assert Path(result["manifest_path"]).exists()

        manifest = result["manifest"]
        assert manifest["parent_ulpin"] == "7A4B9C2D8E1F6G"
        assert "html" in manifest["output_files"]
        assert "pdf" in manifest["output_files"]

        assert len(manifest["output_files"]["html"]["sha256"]) == 64
        assert len(manifest["output_files"]["pdf"]["sha256"]) == 64

    def test_accepts_dict(
        self, sample_raw_data: dict, tmp_path: Path
    ) -> None:
        result = generate_report(sample_raw_data, output_dir=tmp_path)
        assert Path(result["html_path"]).exists()


# ===================================================================
# Priority 1: Report consistency across all outputs
# ===================================================================

class TestReportConsistency:
    """All generated artifacts must share the same report ID, input hash,
    and QR payload when produced by a single generate_report() call."""

    def test_same_report_id_across_artifacts(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        result = generate_report(sample_input, output_dir=tmp_path)
        manifest = result["manifest"]
        report_id = manifest["report_id"]

        # HTML must contain the report ID
        html_content = Path(result["html_path"]).read_text(encoding="utf-8")
        assert report_id in html_content, (
            "HTML does not contain the manifest report ID"
        )

        # Manifest JSON file must match in-memory manifest
        manifest_file = json.loads(
            Path(result["manifest_path"]).read_text(encoding="utf-8")
        )
        assert manifest_file["report_id"] == report_id, (
            "Manifest file report ID does not match in-memory report ID"
        )

        # QR payload must reference the same report ID and hash
        assert manifest["qr_payload"]["report_id"] == report_id
        assert manifest["qr_payload"]["parent_ulpin"] == manifest["parent_ulpin"]
        assert manifest["qr_payload"]["sha256_hash"] == manifest["input_hash"]

        # Input hash must be consistent across manifest file and memory
        assert manifest_file["input_hash"] == manifest["input_hash"]

    def test_same_qr_payload_in_html_and_manifest(
        self, sample_input: ValidationInput, tmp_path: Path
    ) -> None:
        result = generate_report(sample_input, output_dir=tmp_path)
        manifest = result["manifest"]

        html_content = Path(result["html_path"]).read_text(encoding="utf-8")

        # QR payload values must appear in the HTML
        assert manifest["qr_payload"]["parent_ulpin"] in html_content
        assert manifest["qr_payload"]["report_id"] in html_content
