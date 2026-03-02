from __future__ import annotations

import math
import threading

import pytest
import yappi

from yapflame.tree import (
    _PACKAGE_DIR,
    _is_internal,
    build_combined,
    build_flame_tree,
    short_name,
)


def test_short_name_unix():
    assert short_name("/home/user/project/foo.py:bar") == "foo.py:bar"


def test_short_name_windows():
    assert short_name("C:\\Users\\user\\project\\foo.py:bar") == "foo.py:bar"


def test_short_name_no_path():
    assert short_name("<built-in>.len") == "<built-in>.len"


def test_short_name_mixed_sep():
    assert short_name("C:\\a\\b/c/d.py:f") == "d.py:f"


def test_is_internal_package():
    assert _is_internal(f"{_PACKAGE_DIR}/tree.py:build_flame_tree")
    assert _is_internal(f"{_PACKAGE_DIR}/__init__.py:profile")


def test_is_internal_user_code():
    assert not _is_internal("/home/user/myapp/main.py:run")
    assert not _is_internal("/Users/dev/yapflame/tests/test_tree.py:_caller")


# -- integration --


def _do_work():
    total = 0.0
    for i in range(10_000):
        total += math.sqrt(i)


@pytest.fixture(autouse=True)
def _yappi():
    yappi.clear_stats()
    yappi.set_clock_type("wall")
    yield
    if yappi.is_running():
        yappi.stop()
    yappi.clear_stats()


def test_single_thread():
    yappi.start()
    _do_work()
    yappi.stop()
    ts = yappi.get_thread_stats()
    tree = build_flame_tree(ctx_id=ts[0].id)
    assert "children" in tree

    def has_value(node):
        if node["value"] > 0:
            return True
        return any(has_value(c) for c in node.get("children", []))

    assert has_value(tree)


def test_multithreaded():
    yappi.start()
    threads = [threading.Thread(target=_do_work) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    _do_work()
    yappi.stop()
    ts = yappi.get_thread_stats()
    assert len(ts) >= 4
    for t in ts:
        tree = build_flame_tree(ctx_id=t.id)
        assert "children" in tree


def test_combined():
    yappi.start()
    t = threading.Thread(target=_do_work)
    t.start()
    t.join()
    _do_work()
    yappi.stop()
    combined = build_combined()
    assert combined["name"] == "all threads"
    assert len(combined["children"]) >= 2


def test_empty_profile():
    yappi.start()
    yappi.stop()
    ts = yappi.get_thread_stats()
    tree = build_flame_tree(ctx_id=ts[0].id)
    assert "children" in tree


def test_recursive():
    def fib(n):
        return n if n <= 1 else fib(n - 1) + fib(n - 2)

    yappi.start()
    fib(15)
    yappi.stop()
    ts = yappi.get_thread_stats()
    tree = build_flame_tree(ctx_id=ts[0].id)
    assert isinstance(tree["children"], list)
