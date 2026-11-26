"""Confirme que les 8 failles initiales (F1 à F8) sont bien présentes."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from scripts.compare_lab_live import replay


def test_eight_initial_vulnerabilities_are_exploitable(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        replay(create_app, Path(tmp), vulnerable=True)
    out = capsys.readouterr().out
    for fid in ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"):
        assert fid in out
