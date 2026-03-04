from __future__ import annotations

import math
from pathlib import Path

import pytest
import yappi

from yapflame import Result, __version__, profile


def _work():
    total = 0.0
    for i in range(5_000):
        total += math.sqrt(i)


def test_result_bool():
    assert Result(enabled=True)
    assert not Result(enabled=False)


def test_disabled_empty():
    r = Result(enabled=False)
    assert r.data["threads"] == []


def test_disabled_noop():
    r = Result(enabled=False)
    r.save("/nonexistent/path/file.html")
    r.open()


def test_basic():
    with profile() as p:
        _work()
    assert p
    assert len(p.data["threads"]) >= 1


def test_cpu():
    with profile(clock="cpu") as p:
        _work()
    assert len(p.data["threads"]) >= 1


def test_disabled():
    with profile(enabled=False) as p:
        _work()
    assert not p
    assert p.data["threads"] == []


def test_bad_clock():
    with pytest.raises(ValueError, match="invalid"):
        profile(clock="invalid")


def test_save(tmp_path: Path):
    with profile() as p:
        _work()
    path = tmp_path / "test.html"
    p.save(str(path))
    assert "DecompressionStream" in path.read_text()


def test_cleanup():
    with profile():
        _work()
    assert not yappi.is_running()


def test_no_clobber():
    yappi.set_clock_type("wall")
    yappi.start()
    _work()
    with profile():
        _work()
    assert yappi.is_running()
    yappi.stop()
    yappi.clear_stats()


def test_exception_keeps_data():
    with pytest.raises(RuntimeError), profile() as p:
        _work()
        raise RuntimeError("boom")
    assert len(p.data["threads"]) >= 1
    assert not yappi.is_running()


def test_version():
    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) >= 2
