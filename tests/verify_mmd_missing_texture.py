"""Exercise missing-texture recovery using an isolated copy of the optional street PMX."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import command
from tools.asset_audit import inspect


def main():
    source = Path(r"C:\a\tools\mmd64\UserFile\Model\environments pack 03 (FFA)\street01_android\street01_android.pmx")
    if not source.is_file():
        print("SKIP optional street PMX is unavailable")
        return
    absent = "atlas02_street_d.png"
    rows = inspect(source)["texture_dependencies"]
    assert any(row["name"] == absent for row in rows)
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as destination:
        verify_import(source, rows, absent, output, Path(destination))


def verify_import(source, rows, absent, output, destination):
    args = command("tests/mmd_missing_texture_smoke.gd", headless=True)
    def run(request, expected):
        log = request.parent / "engine.log"
        args[args.index("--log-file") + 1] = str(log)
        result = subprocess.run(args, cwd=ROOT, env={**os.environ, "HAS_MMD_TEST_REQUEST": str(request)}, timeout=150)
        trace = log.read_text(encoding="utf-8")
        assert result.returncode == 0 and expected in trace and "ERROR" not in trace, trace

    with tempfile.TemporaryDirectory(dir=output) as temp:
        folder = Path(temp)
        fixture = folder / "fixture"
        fixture.mkdir()
        shutil.copyfile(source, fixture / source.name)
        # A traversal reference must fail even when its texture is absent.
        original = source.read_bytes()
        unsafe_name = "../" + absent[3:]
        encoding = next(enc for enc in ("utf-16-le", "utf-8") if absent.encode(enc) in original)
        malformed = fixture / "unsafe.pmx"
        malformed.write_bytes(original.replace(absent.encode(encoding), unsafe_name.encode(encoding)))
        rejected = folder / "rejected"
        attempt = subprocess.run([sys.executable, str(ROOT / "tools/prepare_mmd.py"), str(malformed),
                                  "--output", str(rejected)], capture_output=True, text=True, timeout=30)
        assert attempt.returncode == 1 and "Unsafe texture dependency" in attempt.stdout, attempt
        assert not rejected.exists()
        for row in rows:
            assert not row.get("unsafe") and row["present"]
            if row["name"] != absent:
                dest = fixture / row["name"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source.parent / row["name"], dest)
        request = folder / "request.json"
        request.write_text(json.dumps(dict(folder=temp, source=str(source), absent=absent)))
        run(request, "MISSING_TEXTURE_REOPEN true")
        project, = folder.glob("app_*/street.has")
        with zipfile.ZipFile(project) as packed:
            assert packed.testzip() is None
            geometry, = [name for name in packed.namelist() if name.endswith(".glb")]
            geometry_hash = hashlib.sha256(packed.read(geometry)).hexdigest()
        moved = destination / "relocated.has"
        shutil.copyfile(project, moved)
    request = destination / "request.json"
    request.write_text(json.dumps(dict(folder=str(destination), source=str(source), absent=absent,
                                       packed=str(moved), geometry_hash=geometry_hash)))
    run(request, "MISSING_TEXTURE_PORTABLE true")
    print("PASS street PMX warning and cold reopen of relocated packed mesh with missing-texture metadata")


if __name__ == "__main__":
    main()
