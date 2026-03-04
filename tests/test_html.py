from __future__ import annotations

import base64
import gzip
import json
import re

import pytest

from yapflame.html import _compress, _intern_strings, _safe_json, generate

SAMPLE = {
    "threads": [
        {
            "label": "MainThread (id=1, 0.50s)",
            "data": {
                "name": "main",
                "value": 10.5,
                "children": [
                    {
                        "name": "helper",
                        "value": 3.2,
                        "children": [],
                        "f": "/app/main.py:helper",
                    }
                ],
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


def test_safe_json_compact():
    data = {"a": 1, "b": [2, 3]}
    result = _safe_json(data)
    assert " " not in result


def test_safe_json_escapes_script():
    result = _safe_json({"name": "</script><script>alert(1)"})
    assert "</script>" not in result
    assert r"<\/" in result


def test_intern_strings_basic():
    data = {
        "threads": [
            {
                "label": "T1",
                "data": {
                    "name": "a",
                    "value": 1,
                    "children": [
                        {"name": "b", "value": 2, "children": [], "f": "/x.py:b"},
                    ],
                    "f": "/x.py:a",
                },
            }
        ]
    }
    strings, compacted = _intern_strings(data)
    assert len(strings) == 2
    assert "/x.py:a" in strings
    assert "/x.py:b" in strings
    root = compacted["threads"][0]["data"]
    assert isinstance(root["f"], int)
    assert strings[root["f"]] == "/x.py:a"
    assert isinstance(root["children"][0]["f"], int)


def test_intern_strings_dedup():
    data = {
        "threads": [
            {
                "label": "T1",
                "data": {
                    "name": "a",
                    "value": 1,
                    "children": [
                        {"name": "b", "value": 2, "children": [], "f": "/same.py:f"},
                    ],
                    "f": "/same.py:f",
                },
            }
        ]
    }
    strings, compacted = _intern_strings(data)
    assert len(strings) == 1
    root = compacted["threads"][0]["data"]
    assert root["f"] == root["children"][0]["f"]


def test_intern_strings_no_mutation():
    data = {
        "threads": [
            {
                "label": "T1",
                "data": {"name": "a", "value": 1, "children": [], "f": "/x.py:a"},
            }
        ]
    }
    _intern_strings(data)
    assert data["threads"][0]["data"]["f"] == "/x.py:a"


def test_compress_roundtrip():
    original = json.dumps({"hello": "world", "nums": list(range(100))})
    compressed = _compress(original)
    raw = base64.b64decode(compressed)
    decompressed = gzip.decompress(raw).decode("utf-8")
    assert json.loads(decompressed) == json.loads(original)


def test_html_structure(html):
    assert html.startswith("<!DOCTYPE html>")
    assert "DecompressionStream" in html
    assert "buildCombined" in html


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
        "threads": [
            {
                "label": "T (id=1, 0.1s)",
                "data": {
                    "name": "</script>",
                    "value": 1,
                    "children": [],
                    "f": "x.py:f",
                },
            },
        ],
    }
    html = generate(data)
    for block in re.findall(r"<script>(.*?)</script>", html, re.DOTALL):
        assert "</script>" not in block


def _extract_payload(html: str) -> dict:
    m = re.search(r'atob\("([^"]+)"\)', html)
    assert m, "could not find compressed payload in HTML"
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def test_embedded_payload_decodable(html):
    payload = _extract_payload(html)
    assert isinstance(payload["s"], list)
    assert isinstance(payload["t"], list)


def test_no_combined_in_payload(html):
    payload = _extract_payload(html)
    assert "combined" not in payload
