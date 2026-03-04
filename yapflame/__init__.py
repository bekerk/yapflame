"""Simple yappi flamegraphs."""

from __future__ import annotations

import os
import tempfile
import webbrowser
from importlib.metadata import version as _pkg_version
from typing import Any

import yappi

from yapflame.html import generate
from yapflame.tree import build_flame_tree

__all__ = ["profile", "Result", "__version__"]
__version__: str = _pkg_version("yapflame")

_EMPTY = {"threads": []}


class Result:
    def __init__(self, enabled: bool = True) -> None:
        self._data: dict[str, Any] | None = None
        self._enabled = enabled

    def __bool__(self) -> bool:
        return self._enabled

    @property
    def data(self) -> dict[str, Any]:
        if not self._enabled:
            return _EMPTY
        if self._data is None:
            thread_stats = yappi.get_thread_stats()
            threads: list[dict[str, Any]] = []
            for ts in thread_stats:
                tree = build_flame_tree(ctx_id=ts.id)
                threads.append(
                    {
                        "label": f"{ts.name} (id={ts.id}, {ts.ttot:.2f}s)",
                        "data": tree,
                    }
                )
            self._data = {"threads": threads}
        return self._data

    def save(self, path: str) -> None:
        if not self._enabled:
            return
        with open(path, "w") as f:
            f.write(generate(self.data))

    def open(self) -> None:
        if not self._enabled:
            return
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as tmp:
            tmp.write(generate(self.data))
        webbrowser.open(f"file://{tmp.name}")


class profile:
    def __init__(self, clock: str = "wall", enabled: bool = True) -> None:
        if clock not in ("wall", "cpu"):
            raise ValueError(f"clock must be 'wall' or 'cpu', got {clock!r}")
        self.clock = clock
        self.enabled = enabled
        self.result = Result(enabled=enabled)
        self._yappi_was_running = False

    def __enter__(self) -> Result:
        if self.enabled:
            self._yappi_was_running = yappi.is_running()
            if not self._yappi_was_running:
                yappi.set_clock_type(self.clock)
                yappi.start()
        return self.result

    def __exit__(self, *exc: object) -> None:
        if self.enabled:
            try:
                if not self._yappi_was_running:
                    yappi.stop()
                _ = self.result.data
            finally:
                if not self._yappi_was_running:
                    yappi.clear_stats()


def _cli_main() -> None:
    import argparse
    import runpy
    import sys

    p = argparse.ArgumentParser(
        prog="yapflame",
        usage="yapflame [-o FILE] [--cpu] script [args ...]",
    )
    p.add_argument("-o", "--out", default=None)
    p.add_argument("--cpu", action="store_true")
    p.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    args, rest = p.parse_known_args()

    if not rest:
        p.error("missing script")

    script, script_args = rest[0], rest[1:]
    if not os.path.isfile(script):
        print(f"yapflame: {script!r} is not a file", file=sys.stderr)
        sys.exit(1)

    sys.argv = [script, *script_args]

    yappi.set_clock_type("cpu" if args.cpu else "wall")
    yappi.start()
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit:
        pass
    except Exception:
        import traceback

        traceback.print_exc()
    finally:
        yappi.stop()
        result = Result()
        _ = result.data
        yappi.clear_stats()

        if args.out:
            result.save(args.out)
            print(f"wrote {args.out}")
        else:
            result.open()
