from __future__ import annotations

import json
import re

import pytest

from yapflame.html import _safe_json, generate

SAMPLE = {
    "combined": {
        "name": "all threads",
        "value": 0,
        "children": [
            {"name": "main", "value": 10.5, "children": [], "f": "/app/main.py:main"}
        ],
    },
    "threads": [
        {
            "label": "MainThread (id=1, 0.50s)",
            "data": {
                "name": "main",
                "value": 10.5,
                "children": [],
                "f": "/app/main.py:main",
            },
        },
    ],
}


@pytest.fixture
def html():
    return generate(SAMPLE)


def test_safe_json_roundtrip():
    data = {"name": "foo", "value": 42}
    assert json.loads(_safe_json(data)) == data


def test_safe_json_escapes_script():
    result = _safe_json({"name": "</script><script>alert(1)"})
    assert "</script>" not in result
    assert r"<\/" in result


def test_html_structure(html):
    assert html.startswith("<!DOCTYPE html>")
    assert "FLAME_DATA" in html
    assert "main.py:main" in html


def test_no_cdn(html):
    assert 'src="https://cdn.jsdelivr.net' not in html
    assert 'src="https://d3js.org' not in html


def test_timestamp(html):
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", html)


def test_thread_tabs(html):
    assert "MainThread (id=1)" in html


def test_singular_plural():
    assert "1 thread /" in generate(SAMPLE)

    two = {
        "combined": {"name": "all threads", "value": 0, "children": []},
        "threads": [
            {
                "label": "T1 (id=1, 0.1s)",
                "data": {"name": "t1", "value": 0, "children": []},
            },
            {
                "label": "T2 (id=2, 0.2s)",
                "data": {"name": "t2", "value": 0, "children": []},
            },
        ],
    }
    assert "2 threads /" in generate(two)


def test_injection_safe():
    data = {
        "combined": {
            "name": "all threads",
            "value": 0,
            "children": [
                {"name": "</script>", "value": 1, "children": [], "f": "x.py:f"}
            ],
        },
        "threads": [],
    }
    html = generate(data)
    for block in re.findall(r"<script>(.*?)</script>", html, re.DOTALL):
        assert "</script>" not in block
