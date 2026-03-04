"""yappi stats -> d3-flame-graph tree dicts"""

from __future__ import annotations

import os
from typing import Any

import yappi

_PACKAGE_DIR: str = os.path.dirname(os.path.abspath(__file__))


def _is_internal(full_name: str) -> bool:
    return _PACKAGE_DIR in full_name


def short_name(full_name: str) -> str:
    for sep in ("/", "\\"):
        idx = full_name.rfind(sep)
        if idx != -1:
            return full_name[idx + 1 :]
    return full_name


def build_flame_tree(ctx_id: int) -> dict[str, Any]:
    func_stats = yappi.get_func_stats(ctx_id=ctx_id)

    by_name: dict[str, Any] = {}
    for fs in func_stats:
        if not _is_internal(fs.full_name):
            by_name[fs.full_name] = fs

    cache: dict[str, dict[str, Any]] = {}
    visiting: set[str] = set()

    def _node(fs: Any) -> dict[str, Any]:
        key = fs.full_name
        if key in cache:
            return cache[key]

        if key in visiting:
            return {
                "name": short_name(fs.name) + " (recursive)",
                "value": round(fs.tsub * 1000, 2),
                "children": [],
                "f": fs.full_name,
            }

        visiting.add(key)
        children: list[dict[str, Any]] = []
        if fs.children:
            for child in fs.children:
                child_fs = by_name.get(child.full_name)
                if child_fs is None:
                    children.append(
                        {
                            "name": short_name(child.name),
                            "value": round(child.ttot * 1000, 2),
                            "children": [],
                            "f": child.full_name,
                        }
                    )
                else:
                    children.append(_node(child_fs))
        visiting.discard(key)

        node = {
            "name": short_name(fs.name),
            "value": round(max(0.0, fs.tsub) * 1000, 2),
            "children": children,
            "f": fs.full_name,
        }
        cache[key] = node
        return node

    all_child_names: set[str] = set()
    for fs in by_name.values():
        if fs.children:
            for ch in fs.children:
                all_child_names.add(ch.full_name)

    roots = [
        _node(fs) for fs in by_name.values() if fs.full_name not in all_child_names
    ]
    if len(roots) == 1:
        return roots[0]
    return {"name": "(thread root)", "value": 0, "children": roots}
