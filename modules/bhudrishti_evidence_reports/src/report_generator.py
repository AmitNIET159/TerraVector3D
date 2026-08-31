"""
BhuDrishti 3D — Vertical Property Validation Report Generator.

Orchestrates:
  • HTML report rendering (Jinja2)
  • PDF report generation (ReportLab)
  • Verification manifest creation
  • Console summary output
  • Audit-hash and QR-code embedding

**Report-integrity guarantee**: ``generate_report()`` builds a single
report context (report_id, input_hash, QR payload) and passes it to
every output stage so that HTML, PDF, manifest, and console summary
always contain the exact same identifiers.

Public API
----------
- ``generate_report()``          – full pipeline (HTML + PDF + manifest)
- ``generate_html_report()``     – HTML only
- ``generate_pdf_report()``      – PDF only
- ``create_verification_manifest()``
- ``calculate_audit_hash()``     – re-exported from ``audit_hash``
"""

from __future__ import annotations

import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .audit_hash import calculate_audit_hash, calculate_file_hash
from .models import ValidationInput, mask_holder_name   # re-export mask fn
from .qr_verification import build_qr_payload, generate_qr_code_base64, generate_qr_code_bytes
from .template_renderer import render_html_report as _render_html


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER = (
    "Prototype decision-support output. Final cadastral verification, "
    "ownership determination and legal record approval remain with the "
    "authorized land-record authority."
)

_SEVERITY_COLOURS = {
    "high": colors.HexColor("#dc3545"),
    "medium": colors.HexColor("#fd7e14"),
    "low": colors.HexColor("#ffc107"),
}

_STATUS_COLOURS = {
    "valid": colors.HexColor("#198754"),
    "conflict": colors.HexColor("#dc3545"),
    "pending": colors.HexColor("#6c757d"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_report_id() -> str:
    return f"RPT-{uuid.uuid4().hex[:12].upper()}"


# ---------------------------------------------------------------------------
# Context builder  (single source of truth per run)
# ---------------------------------------------------------------------------

def _build_report_context(input_data: ValidationInput) -> dict[str, Any]:
    """Build the template context dict from validated input.

    Every field that must be identical across HTML, PDF, manifest, and
    console summary is computed **once** here.
    """

    report_id = _new_report_id()
    input_hash = calculate_audit_hash(
        input_data.model_dump(mode="json")
    )

    # QR payload & image -------------------------------------------------
    qr_payload = build_qr_payload(
        report_id=report_id,
        parent_ulpin=input_data.parent_ulpin,
        timestamp=input_data.timestamp,
        sha256_hash=input_hash,
    )
    qr_base64 = generate_qr_code_base64(qr_payload)

    # Summary stats ------------------------------------------------------
    num_units = len(input_data.spatial_units)
    num_valid = sum(
        1 for u in input_data.spatial_units if u.validation_status == "valid"
    )
    num_conflicts = len(input_data.topology_conflicts)
    overall_confidence = input_data.confidence_scores.get("overall", 0.0)

    # Unit register — uses holder_name_masked directly -------------------
    rights_map: dict[str, list[Any]] = {}
    for right in input_data.property_rights:
        rights_map.setdefault(right.vertical_id, []).append(right)

    unit_register: list[dict[str, Any]] = []
    for unit in input_data.spatial_units:
        rights = rights_map.get(unit.vertical_id, [])
        masked_holder = rights[0].holder_name_masked if rights else "N/A"
        rights_type = rights[0].rights_type if rights else "N/A"
        unit_register.append(
            {
                "vertical_id": unit.vertical_id,
                "level_id": unit.level_id,
                "unit_type": unit.unit_type,
                "area_sqm": unit.area_sqm,
                "usage_type": unit.usage_type,
                "rights_type": rights_type,
                "masked_holder": masked_holder,
                "validation_status": unit.validation_status,
            }
        )

    # Conflict list sorted by severity ----------------------------------
    severity_order = {"high": 0, "medium": 1, "low": 2}
    sorted_conflicts = sorted(
        input_data.topology_conflicts,
        key=lambda c: severity_order.get(c.severity, 3),
    )

    return {
        "report_id": report_id,
        "title": "BhuDrishti 3D \u2014 Vertical Property Validation Report",
        "parent_ulpin": input_data.parent_ulpin,
        "building_name": input_data.building.building_name,
        "num_floors": input_data.building.num_floors,
        "num_units": num_units,
        "num_valid_units": num_valid,
        "num_conflicts": num_conflicts,
        "overall_confidence": overall_confidence,
        "confidence_scores": input_data.confidence_scores,
        "unit_register": unit_register,
        "conflicts": [c.model_dump(mode="json") for c in sorted_conflicts],
        "evidence_sources": [
            s.model_dump(mode="json") for s in input_data.source_metadata
        ],
        "qr_base64": qr_base64,
        "qr_payload": qr_payload,
        "input_hash": input_hash,
        "disclaimer": DISCLAIMER,
        "timestamp": input_data.timestamp,
        "generated_by": input_data.generated_by,
    }


# ===================================================================
# Internal renderers (accept a pre-built context)
# ===================================================================

# ---------------------------------------------------------------------------
# HTML (internal)
# ---------------------------------------------------------------------------

def _render_html_from_context(
    context: dict[str, Any],
    output_path: str | Path | None = None,
) -> str:
    """Render HTML from an already-built context dict."""
    html_content = _render_html(context)
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html_content, encoding="utf-8")
    return html_content


# ---------------------------------------------------------------------------
# PDF styles & helpers
# ---------------------------------------------------------------------------

def _pdf_styles() -> dict[str, ParagraphStyle]:
    """Pre-build reusable ReportLab paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "RPTitle", parent=base["Title"],
            fontSize=18, leading=22, alignment=TA_CENTER,
            spaceAfter=4 * mm,
            textColor=colors.HexColor("#1a3c5e"),
        ),
        "heading": ParagraphStyle(
            "RPHeading", parent=base["Heading2"],
            fontSize=12, leading=15,
            spaceBefore=6 * mm, spaceAfter=2 * mm,
            textColor=colors.HexColor("#1a3c5e"),
        ),
        "body": ParagraphStyle(
            "RPBody", parent=base["Normal"],
            fontSize=9, leading=12, alignment=TA_JUSTIFY,
        ),
        "small": ParagraphStyle(
            "RPSmall", parent=base["Normal"],
            fontSize=7.5, leading=10, alignment=TA_LEFT,
        ),
        "cell": ParagraphStyle(
            "RPCell", parent=base["Normal"],
            fontSize=7, leading=9, alignment=TA_LEFT,
        ),
        "cell_center": ParagraphStyle(
            "RPCellCenter", parent=base["Normal"],
            fontSize=7, leading=9, alignment=TA_CENTER,
        ),
        "cell_mono": ParagraphStyle(
            "RPCellMono", parent=base["Normal"],
            fontSize=6.5, leading=8.5, alignment=TA_LEFT,
            fontName="Courier",
        ),
    }


def _common_table_style() -> list[tuple]:
    """Return a base TableStyle command list."""
    return [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dee2e6")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    """Wrap text in a Paragraph for automatic word-wrap in table cells."""
    return Paragraph(str(text), style)


def _make_page_footer(canvas, doc, report_id: str) -> None:
    """Draw footer with report ID, page number, and disclaimer."""
    canvas.saveState()
    w, _h = doc.pagesize
    left = doc.leftMargin
    right = w - doc.rightMargin

    # Separator line
    canvas.setStrokeColor(colors.HexColor("#dee2e6"))
    canvas.setLineWidth(0.5)
    canvas.line(left, 1.5 * cm, right, 1.5 * cm)

    # Report ID (left) and page number (right)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#6c757d"))
    canvas.drawString(left, 1.15 * cm, f"Report: {report_id}")
    canvas.drawRightString(right, 1.15 * cm, f"Page {doc.page}")

    # Disclaimer (centred, two lines at small size)
    canvas.setFont("Helvetica-Oblique", 5.5)
    canvas.setFillColor(colors.HexColor("#adb5bd"))
    canvas.drawCentredString(
        w / 2, 0.72 * cm,
        "Prototype decision-support output. Final cadastral verification,",
    )
    canvas.drawCentredString(
        w / 2, 0.38 * cm,
        "ownership determination and legal record approval remain with the authorized land-record authority.",
    )
    canvas.restoreState()


# ---------------------------------------------------------------------------
# PDF (internal)
# ---------------------------------------------------------------------------

def _render_pdf_from_context(
    context: dict[str, Any],
    output_path: str | Path,
) -> str:
    """Render PDF from an already-built context dict.

    Layout priorities:
    - All table cells use Paragraph objects for word wrapping.
    - Footer on every page: report ID · page number · disclaimer.
    - No standalone disclaimer element → no nearly-blank final page.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(out), pagesize=A4,
        rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=2 * cm, bottomMargin=2.2 * cm,
    )

    styles = _pdf_styles()
    elements: list[Any] = []

    report_id = context["report_id"]

    # ── Title ──────────────────────────────────────────────────────────
    elements.append(Paragraph(context["title"], styles["title"]))
    elements.append(Spacer(1, 1 * mm))

    meta_lines = (
        f"<b>Report ID:</b> {report_id}<br/>"
        f"<b>Generated:</b> {context['timestamp']}<br/>"
        f"<b>Generated By:</b> {context['generated_by']}"
    )
    elements.append(Paragraph(meta_lines, styles["body"]))
    elements.append(Spacer(1, 2 * mm))

    # ── 1. Summary ─────────────────────────────────────────────────────
    elements.append(Paragraph("1. Summary", styles["heading"]))

    summary_data = [
        [_p("Field", styles["cell"]), _p("Value", styles["cell"])],
        [_p("Parent ULPIN", styles["cell"]), _p(context["parent_ulpin"], styles["cell"])],
        [_p("Building Name", styles["cell"]), _p(context["building_name"], styles["cell"])],
        [_p("Number of Floors", styles["cell"]), _p(str(context["num_floors"]), styles["cell"])],
        [_p("Total Units", styles["cell"]), _p(str(context["num_units"]), styles["cell"])],
        [_p("Valid Units", styles["cell"]), _p(str(context["num_valid_units"]), styles["cell"])],
        [_p("Conflicts Detected", styles["cell"]), _p(str(context["num_conflicts"]), styles["cell"])],
        [_p("Overall Confidence", styles["cell"]), _p(f"{context['overall_confidence']:.1%}", styles["cell"])],
    ]
    for key, val in context["confidence_scores"].items():
        if key != "overall":
            summary_data.append([
                _p(f"  └ {key.replace('_', ' ').title()}", styles["cell"]),
                _p(f"{val:.1%}", styles["cell"]),
            ])

    summary_table = Table(summary_data, colWidths=[7 * cm, 9 * cm])
    summary_table.setStyle(TableStyle(
        _common_table_style()
        + [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")])]
    ))
    elements.append(summary_table)

    # ── 2. Vertical-Unit Register ───────────────────────────────────────
    elements.append(Paragraph("2. Vertical-Unit Register", styles["heading"]))

    reg_header = [
        _p("Vertical ID", styles["cell_center"]),
        _p("Level", styles["cell_center"]),
        _p("Type", styles["cell_center"]),
        _p("Area (m²)", styles["cell_center"]),
        _p("Usage", styles["cell_center"]),
        _p("Rights", styles["cell_center"]),
        _p("Holder", styles["cell_center"]),
        _p("Status", styles["cell_center"]),
    ]
    reg_data = [reg_header]
    for u in context["unit_register"]:
        reg_data.append([
            _p(u["vertical_id"], styles["cell_mono"]),
            _p(u["level_id"], styles["cell"]),
            _p(u["unit_type"], styles["cell"]),
            _p(f"{u['area_sqm']:.1f}", styles["cell_center"]),
            _p(u["usage_type"], styles["cell"]),
            _p(u["rights_type"], styles["cell"]),
            _p(u["masked_holder"], styles["cell"]),
            _p(u["validation_status"].upper(), styles["cell_center"]),
        ])

    col_widths = [4.4*cm, 1.3*cm, 1.6*cm, 1.2*cm, 1.7*cm, 1.5*cm, 2.5*cm, 1.4*cm]
    reg_table = Table(reg_data, colWidths=col_widths, repeatRows=1)
    ts_reg = _common_table_style() + [
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]
    for i, u in enumerate(context["unit_register"], start=1):
        bg = _STATUS_COLOURS.get(u["validation_status"], colors.white)
        ts_reg.append(("BACKGROUND", (-1, i), (-1, i), bg))
        ts_reg.append(("TEXTCOLOR", (-1, i), (-1, i), colors.white))
    reg_table.setStyle(TableStyle(ts_reg))
    elements.append(reg_table)

    # ── 3. Topology Conflicts ──────────────────────────────────────────
    elements.append(Paragraph("3. Topology Conflicts", styles["heading"]))

    if not context["conflicts"]:
        elements.append(Paragraph("No topology conflicts detected.", styles["body"]))
    else:
        for conflict in context["conflicts"]:
            sev = conflict["severity"]
            sev_color = {"high": "#dc3545", "medium": "#fd7e14", "low": "#ffc107"}.get(sev, "#6c757d")

            header_parts = [
                f'<font color="{sev_color}"><b>[{sev.upper()}]</b></font>',
                f'Conflict {conflict["conflict_id"]}',
            ]
            if conflict.get("conflict_type"):
                header_parts.append(
                    f'<font color="#6c757d">— {conflict["conflict_type"]}</font>'
                )
            elements.append(Paragraph(" ".join(header_parts), styles["body"]))
            elements.append(Spacer(1, 1 * mm))

            details: list[list[str]] = []
            if conflict.get("conflict_type"):
                details.append(["Conflict Type", conflict["conflict_type"]])
            details.append(["Conflicting Units", ", ".join(conflict["conflicting_unit_ids"])])
            details.append(["Vertical IDs", ", ".join(conflict["conflicting_vertical_ids"])])
            details.append(["Overlap Area", f"{conflict['overlap_area_sqm']:.2f} m²"])
            if conflict.get("overlap_volume_cbm") is not None:
                details.append(["Overlap Volume", f"{conflict['overlap_volume_cbm']:.2f} m³"])
            if (conflict.get("overlapping_z_min_m") is not None
                    and conflict.get("overlapping_z_max_m") is not None):
                details.append([
                    "Z Overlap Range",
                    f"{conflict['overlapping_z_min_m']:.1f} – {conflict['overlapping_z_max_m']:.1f} m",
                ])
            details.append(["Action", conflict["recommended_action"]])
            details.append(["Explanation", conflict["explanation"]])

            detail_data = [
                [_p(r[0], styles["cell"]), _p(r[1], styles["cell"])]
                for r in details
            ]
            detail_table = Table(detail_data, colWidths=[3.5 * cm, 13 * cm])
            detail_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dee2e6")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(detail_table)
            elements.append(Spacer(1, 2 * mm))

    # ── 4. Evidence Sources ────────────────────────────────────────────
    elements.append(Paragraph("4. Evidence Sources", styles["heading"]))

    ev_header = [
        _p("Source File", styles["cell_center"]),
        _p("Type", styles["cell_center"]),
        _p("Timestamp", styles["cell_center"]),
        _p("Conf.", styles["cell_center"]),
        _p("SHA-256 (truncated)", styles["cell_center"]),
    ]
    ev_data = [ev_header]
    for s in context["evidence_sources"]:
        ev_data.append([
            _p(s["file_name"], styles["cell"]),
            _p(s["source_type"], styles["cell"]),
            _p(s["timestamp"], styles["cell"]),
            _p(f"{s['confidence']:.0%}", styles["cell_center"]),
            _p(s["sha256_hash"][:16] + "…", styles["cell_mono"]),
        ])
    ev_table = Table(
        ev_data,
        colWidths=[3.8*cm, 2.2*cm, 3.2*cm, 1.2*cm, 3.2*cm],
        repeatRows=1,
    )
    ev_table.setStyle(TableStyle(
        _common_table_style()
        + [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")])]
    ))
    elements.append(ev_table)

    # ── 5. QR Verification ─────────────────────────────────────────────
    elements.append(Paragraph("5. QR Verification", styles["heading"]))
    elements.append(Paragraph(
        "Scan the QR code below to verify report authenticity locally.",
        styles["body"],
    ))
    elements.append(Spacer(1, 1 * mm))

    qr_bytes = generate_qr_code_bytes(context["qr_payload"])
    qr_buf = io.BytesIO(qr_bytes)
    qr_img = Image(qr_buf, width=3.5 * cm, height=3.5 * cm)
    qr_img.hAlign = "CENTER"
    elements.append(qr_img)
    elements.append(Spacer(1, 1 * mm))

    qr_text = (
        f"<b>Report ID:</b> {context['qr_payload']['report_id']}<br/>"
        f"<b>ULPIN:</b> {context['qr_payload']['parent_ulpin']}<br/>"
        f"<b>Input SHA-256:</b> {context['input_hash'][:32]}…"
    )
    elements.append(Paragraph(qr_text, styles["small"]))

    # ── Build PDF with footer ──────────────────────────────────────────
    footer_fn = lambda canvas, doc: _make_page_footer(canvas, doc, report_id)
    doc.build(elements, onFirstPage=footer_fn, onLaterPages=footer_fn)
    return str(out.resolve())


# ---------------------------------------------------------------------------
# Manifest (internal)
# ---------------------------------------------------------------------------

def _build_manifest_from_context(
    context: dict[str, Any],
    input_data: ValidationInput,
    html_path: str | Path | None = None,
    pdf_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build verification manifest from a pre-built context."""

    manifest: dict[str, Any] = {
        "report_id": context["report_id"],
        "parent_ulpin": input_data.parent_ulpin,
        "timestamp": input_data.timestamp,
        "generated_by": input_data.generated_by,
        "input_hash": context["input_hash"],
        "qr_payload": context["qr_payload"],
        "summary": {
            "building_name": context["building_name"],
            "num_floors": context["num_floors"],
            "num_units": context["num_units"],
            "num_valid_units": context["num_valid_units"],
            "num_conflicts": context["num_conflicts"],
            "overall_confidence": context["overall_confidence"],
        },
        "confidence_scores": input_data.confidence_scores,
        "output_files": {},
    }

    if html_path and Path(html_path).exists():
        manifest["output_files"]["html"] = {
            "path": str(html_path),
            "sha256": calculate_file_hash(html_path),
        }
    if pdf_path and Path(pdf_path).exists():
        manifest["output_files"]["pdf"] = {
            "path": str(pdf_path),
            "sha256": calculate_file_hash(pdf_path),
        }

    manifest["disclaimer"] = DISCLAIMER

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    return manifest


# ===================================================================
# Public API  (preserved signatures)
# ===================================================================

def generate_html_report(
    input_data: ValidationInput | dict[str, Any],
    output_path: str | Path | None = None,
) -> str:
    """Generate the HTML validation report.

    When called standalone, builds its own context.  When called from
    ``generate_report()``, shares the pipeline context.
    """
    if isinstance(input_data, dict):
        input_data = ValidationInput(**input_data)
    context = _build_report_context(input_data)
    return _render_html_from_context(context, output_path)


def generate_pdf_report(
    input_data: ValidationInput | dict[str, Any],
    output_path: str | Path,
) -> str:
    """Generate the PDF validation report.

    Returns the absolute path of the generated PDF.
    """
    if isinstance(input_data, dict):
        input_data = ValidationInput(**input_data)
    context = _build_report_context(input_data)
    return _render_pdf_from_context(context, output_path)


def create_verification_manifest(
    input_data: ValidationInput | dict[str, Any],
    html_path: str | Path | None = None,
    pdf_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Create a verification manifest JSON."""
    if isinstance(input_data, dict):
        input_data = ValidationInput(**input_data)
    context = _build_report_context(input_data)
    return _build_manifest_from_context(
        context, input_data, html_path, pdf_path, output_path
    )


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def print_console_summary(
    input_data: ValidationInput,
    manifest: dict[str, Any],
) -> None:
    """Print a human-readable summary to stdout."""
    sep = "=" * 64
    print(f"\n{sep}")
    print("  BhuDrishti 3D — Validation Report Summary")
    print(sep)
    print(f"  Report ID       : {manifest['report_id']}")
    print(f"  Parent ULPIN    : {input_data.parent_ulpin}")
    print(f"  Building        : {input_data.building.building_name}")
    print(f"  Floors          : {input_data.building.num_floors}")
    print(f"  Total Units     : {manifest['summary']['num_units']}")
    print(f"  Valid Units     : {manifest['summary']['num_valid_units']}")
    print(f"  Conflicts       : {manifest['summary']['num_conflicts']}")
    print(f"  Overall Conf.   : {manifest['summary']['overall_confidence']:.1%}")
    print(f"  Input SHA-256   : {manifest['input_hash'][:48]}…")
    print(f"  Timestamp       : {input_data.timestamp}")
    print(sep)

    if manifest.get("output_files"):
        print("  Generated files:")
        for kind, info in manifest["output_files"].items():
            print(f"    [{kind.upper()}] {info['path']}")
    print(f"\n  {DISCLAIMER}\n")


# ---------------------------------------------------------------------------
# Full pipeline  — single context for all outputs
# ---------------------------------------------------------------------------

def generate_report(
    input_data: ValidationInput | dict[str, Any],
    output_dir: str | Path = "output",
) -> dict[str, Any]:
    """Run the full report-generation pipeline.

    Builds a **single** report context and passes it to every stage,
    guaranteeing that HTML, PDF, manifest, and console summary contain
    the exact same report_id, input_hash, QR payload, and timestamps.
    """
    if isinstance(input_data, dict):
        input_data = ValidationInput(**input_data)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = output_dir / "BhuDrishti3D_validation_report.html"
    pdf_path = output_dir / "BhuDrishti3D_validation_report.pdf"
    manifest_path = output_dir / "verification_manifest.json"

    # ── Single context for the entire run ──
    context = _build_report_context(input_data)

    # ── Generate all outputs from the same context ──
    _render_html_from_context(context, html_path)
    _render_pdf_from_context(context, pdf_path)
    manifest = _build_manifest_from_context(
        context, input_data, html_path, pdf_path, manifest_path
    )

    # Console output
    print_console_summary(input_data, manifest)

    return {
        "html_path": str(html_path),
        "pdf_path": str(pdf_path),
        "manifest_path": str(manifest_path),
        "manifest": manifest,
    }
