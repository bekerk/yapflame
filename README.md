# yapflame

[![CI](https://github.com/bekerk/yapflame/actions/workflows/ci.yml/badge.svg)](https://github.com/bekerk/yapflame/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/yapflame.svg)](https://pypi.org/project/yapflame/)
[![Python versions](https://img.shields.io/pypi/pyversions/yapflame.svg)](https://pypi.org/project/yapflame/)
[![Last commit](https://img.shields.io/github/last-commit/bekerk/yapflame)](https://github.com/bekerk/yapflame/commits/main)
[![License](https://img.shields.io/github/license/bekerk/yapflame)](https://github.com/bekerk/yapflame/blob/main/LICENSE)

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
