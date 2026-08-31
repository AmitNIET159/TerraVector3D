"""Tests for application startup and router registration."""
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def test_app_creates_successfully():
    from app.main import create_app
    app = create_app()
    assert app is not None
    assert app.title == "BhuDrishti 3D"
    assert app.version == "0.1.0"
