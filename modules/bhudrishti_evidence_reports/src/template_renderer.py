"""
Jinja2 template rendering for BhuDrishti 3D validation reports.

Templates are discovered relative to the package ``templates/`` directory
by default, but a custom template directory may be supplied.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


# Default template directory: <package_root>/templates/
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_TEMPLATE_DIR = _PACKAGE_ROOT / "templates"


def _create_environment(template_dir: str | Path | None = None) -> Environment:
    """Create a Jinja2 :class:`Environment` with HTML autoescaping."""
    search_path = str(template_dir or _DEFAULT_TEMPLATE_DIR)
    return Environment(
        loader=FileSystemLoader(search_path),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_html_report(
    context: dict[str, Any],
    template_name: str = "validation_report.html.j2",
    template_dir: str | Path | None = None,
) -> str:
    """Render the HTML validation report.

    Parameters
    ----------
    context:
        Template variables (see :func:`report_generator.build_report_context`).
    template_name:
        Jinja2 template file name.
    template_dir:
        Override template search directory.

    Returns
    -------
    str
        Rendered HTML string.
    """
    env = _create_environment(template_dir)
    template = env.get_template(template_name)
    return template.render(**context)

