"""Resolve prepared test fixtures without depending on the installed Studio cache."""
from pathlib import Path
import os

def fixture_output():
    configured=os.environ.get('HYBRID_NATIVE_FIXTURES')
    root=Path(configured).expanduser().resolve(strict=True) if configured else Path(__file__).resolve().parents[1]/'output'
    if not root.is_dir():raise ValueError('HYBRID_NATIVE_FIXTURES must select an existing prepared-fixture directory')
    return root
