# yapflame

<p align="center">
    <a href="https://github.com/bekerk/yapflame/actions/workflows/ci.yml"><img src="https://github.com/bekerk/yapflame/actions/workflows/ci.yml/badge.svg?branch=main"></a>
    <a href="https://pypi.org/project/yapflame/"><img src="https://img.shields.io/pypi/v/yapflame.svg"></a>
    <a href="https://pypi.org/project/yapflame/"><img src="https://img.shields.io/pypi/dw/yapflame.svg"></a>
    <a href="https://pypi.org/project/yapflame/"><img src="https://img.shields.io/pypi/pyversions/yapflame.svg"></a>
    <a href="https://github.com/bekerk/yapflame/commits/"><img src="https://img.shields.io/github/last-commit/bekerk/yapflame.svg"></a>
    <a href="https://github.com/bekerk/yapflame/blob/main/LICENSE"><img src="https://img.shields.io/github/license/bekerk/yapflame.svg"></a>
</p>

Simple [yappi](https://github.com/sumerc/yappi) flamegraphs.

## Installation

```bash
pip install yapflame
uv add yapflame
# and others...
```

## Examples

```python
from yapflame import profile

with profile() as p:
    do_work()

p.open()       # browser
p.save("o.html")  # file
```

`enabled=False` to noop:

```python
with profile(enabled=DEBUG) as p:
    do_work()
if p:
    p.open()
```

or via cli:
```bash
yapflame script.py
yapflame script.py -o out.html
yapflame script.py --cpu
```
