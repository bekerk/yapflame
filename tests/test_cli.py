from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(*args, ok=True):
    r = subprocess.run(
        [sys.executable, "-m", "yapflame", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if ok:
        assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def test_version():
    assert "yapflame" in _run("--version").stdout
    assert "yapflame" in _run("-V").stdout


def test_help():
    assert "script" in _run("--help").stdout


def test_missing_script():
    assert _run("/nonexistent.py", ok=False).returncode != 0


def test_profile(tmp_path: Path):
    script = tmp_path / "hello.py"
    out = tmp_path / "out.html"
    script.write_text("import math\nfor i in range(1000): math.sqrt(i)\n")
    r = _run("-o", str(out), str(script))
    assert "DecompressionStream" in out.read_text()
    assert "FLAME_DATA" in out.read_text()
    assert "wrote" in r.stdout


def test_script_args(tmp_path: Path):
    script = tmp_path / "t.py"
    out = tmp_path / "out.html"
    script.write_text(
        f"import sys\nassert sys.argv == [{str(script)!r}, 'a', 'b'], "
        + "f'got {sys.argv}'\n",
    )
    _run("-o", str(out), str(script), "a", "b")
    assert out.exists()


def test_exception(tmp_path: Path):
    script = tmp_path / "crash.py"
    out = tmp_path / "out.html"
    script.write_text("raise RuntimeError('boom')\n")
    r = _run("-o", str(out), str(script))
    assert out.exists()
    assert "RuntimeError" in r.stderr


def test_sys_exit(tmp_path: Path):
    script = tmp_path / "e.py"
    out = tmp_path / "out.html"
    script.write_text("import sys; sys.exit(0)\n")
    _run("-o", str(out), str(script))
    assert out.exists()


def test_cpu(tmp_path: Path):
    script = tmp_path / "c.py"
    out = tmp_path / "out.html"
    script.write_text("import math\nfor i in range(1000): math.sqrt(i)\n")
    _run("--cpu", "-o", str(out), str(script))
    assert out.exists()
