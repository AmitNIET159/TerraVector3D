"""Module path setup and base adapter for BhuDrishti 3D modules."""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_MODULES_PATH = _PROJECT_ROOT / "modules"

def ensure_module_path() -> Path:
    root_str = str(_PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if not _MODULES_PATH.exists():
        raise RuntimeError(f"Modules directory not found at {_MODULES_PATH}.")
    return _MODULES_PATH

def get_module_names() -> list[str]:
    return [
        "bhudrishti_identity_rights",
        "bhudrishti_topology",
        "bhudrishti_geospatial_ai",
        "bhudrishti_evidence_reports",
    ]

def verify_all_modules() -> dict[str, bool]:
    ensure_module_path()
    results = {}
    for name in get_module_names():
        module_dir = _MODULES_PATH / name
        src_init = module_dir / "src" / "__init__.py"
        results[name] = module_dir.exists() and src_init.exists()
    return results

ensure_module_path()
