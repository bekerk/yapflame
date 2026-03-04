"""flame data -> self-contained html"""

from __future__ import annotations

import base64
import gzip
import json
from datetime import datetime, timezone
from importlib.resources import files
from typing import Any


def _load_vendor(name: str) -> str:
    return (files("yapflame") / "_vendor" / name).read_text(encoding="utf-8")


def _safe_json(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":")).replace("</", r"<\/")


def _intern_strings(flame_data: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    table: dict[str, int] = {}
    strings: list[str] = []

    def _walk(node: dict[str, Any]) -> dict[str, Any]:
        f = node.get("f")
        if f is not None:
            idx = table.get(f)
            if idx is None:
                idx = len(strings)
                table[f] = idx
                strings.append(f)
            node = {**node, "f": idx}
        children = node.get("children")
        if children:
            node = {**node, "children": [_walk(c) for c in children]}
        return node

    new_threads = []
    for t in flame_data["threads"]:
        new_threads.append({**t, "data": _walk(t["data"])})

    return strings, {"threads": new_threads}


def _compress(data_json: str) -> str:
    compressed = gzip.compress(data_json.encode("utf-8"), compresslevel=6)
    return base64.b64encode(compressed).decode("ascii")


def generate(flame_data: dict[str, Any]) -> str:
    threads = flame_data["threads"]

    strings, compacted = _intern_strings(flame_data)
    payload = {"s": strings, "t": compacted["threads"]}
    compressed_b64 = _compress(_safe_json(payload))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    d3_js = _load_vendor("d3.v7.min.js")
    flamegraph_js = _load_vendor("d3-flamegraph.min.js")
    flamegraph_css = _load_vendor("d3-flamegraph.css")

    tab_buttons = "".join(
        f'  <button onclick="selectView({i}, this)">{t["label"].split(",")[0]})</button>\n'
        for i, t in enumerate(threads)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>yapflame</title>
<style>
{flamegraph_css}
body {{
  font: 12px Verdana, sans-serif;
  background: #fff;
  color: #333;
  margin: 0;
  padding: 16px;
}}
h1 {{ font-size: 15px; font-weight: normal; color: #666; margin: 0 0 2px; }}
.meta {{ color: #999; font-size: 11px; margin-bottom: 12px; }}
.bar {{
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 10px;
}}
.bar button {{
  font: inherit;
  font-size: 12px;
  background: #f5f5f5;
  color: #888;
  border: 1px solid #ddd;
  padding: 4px 10px;
  cursor: pointer;
}}
.bar button:hover {{ color: #333; }}
.bar button.on {{ color: #333; border-color: #999; background: #eee; }}
.bar input {{
  font: inherit;
  font-size: 12px;
  background: #fff;
  color: #333;
  border: 1px solid #ddd;
  padding: 4px 8px;
  width: 200px;
}}
.bar input:focus {{ outline: none; border-color: #999; }}
#chart {{
  background: #fafafa;
  border: 1px solid #eee;
  padding: 8px;
  min-height: 300px;
}}
.d3-flame-graph rect {{ stroke: #fff; stroke-width: .5px; }}
.d3-flame-graph .d3-flame-graph-label {{
  font: 11px Verdana, sans-serif;
  fill: #333; pointer-events: none;
}}
#tip {{
  color: #666;
  font-size: 12px;
  margin-bottom: 8px;
  height: 18px;
}}
#tip b {{ color: #333; font-weight: normal; }}
.legend {{
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #999;
  margin-bottom: 10px;
}}
.legend .swatch {{
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 2px;
  margin-right: 3px;
  vertical-align: middle;
}}
.legend a {{ color: #aaa; }}
#loading {{
  color: #999;
  font-size: 13px;
  padding: 40px 0;
  text-align: center;
}}
</style>
</head>
<body>
<h1>yapflame</h1>
<div class="meta">{len(threads)} thread{"s" if len(threads) != 1 else ""} / ms (self time) / click to zoom / {now}</div>

<div class="bar">
  <button class="on" onclick="selectView(-1, this)">all</button>
{tab_buttons}  <input id="search" placeholder="search..." oninput="doSearch()" autofocus>
  <button onclick="resetZoom()">reset</button>
</div>

<div class="legend"><span class="swatch" style="background:rgb(225,140,65)"></span>app <span class="swatch" style="background:rgb(105,215,105)"></span>stdlib <span class="swatch" style="background:rgb(75,205,240)"></span>third-party <span class="swatch" style="background:rgb(235,225,105)"></span>builtin <a href="https://www.brendangregg.com/flamegraphs.html" target="_blank">?</a></div>
<div id="tip"></div>
<div id="chart"><div id="loading">decompressing\u2026</div></div>

<script>{d3_js}</script>
<script>{flamegraph_js}</script>
<script>
var FLAME_DATA = null, chart = null;

(function() {{
  var raw = atob("{compressed_b64}");
  var bytes = new Uint8Array(raw.length);
  for (var i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  var ds = new DecompressionStream('gzip');
  var w = ds.writable.getWriter(); w.write(bytes); w.close();
  new Response(ds.readable).text().then(function(text) {{
    var p = JSON.parse(text), S = p.s, T = p.t;
    function hydrate(n) {{
      if (typeof n.f === 'number') n.f = S[n.f];
      var ch = n.children;
      if (ch) for (var i = 0; i < ch.length; i++) hydrate(ch[i]);
    }}
    for (var i = 0; i < T.length; i++) hydrate(T[i].data);
    FLAME_DATA = {{ threads: T, combined: buildCombined(T) }};
    document.getElementById('loading').remove();
    render(FLAME_DATA.combined);
  }});
}})();

function buildCombined(threads) {{
  return {{
    name: 'all threads', value: 0,
    children: threads.map(function(t) {{
      var d = t.data;
      var label = t.label.split(',')[0] + ')';
      return d.name === '(thread root)'
        ? {{name: label, value: 0, children: d.children}}
        : {{name: label, value: 0, children: [d]}};
    }})
  }};
}}

function render(data) {{
  document.getElementById('chart').innerHTML = '';
  var w = document.getElementById('chart').clientWidth - 16;

  chart = flamegraph()
    .width(w)
    .cellHeight(18)
    .minFrameSize(2)
    .transitionDuration(200)
    .selfValue(true)
    .setColorMapper(function(d) {{
      if (!d.data || !d.data.name) return '#e8e8e8';
      if (d.highlight) return '#ee00ee';
      var f = d.data.f || '', n = d.data.name, h = 0;
      for (var i = 0; i < n.length; i++) h = ((h << 5) - h + n.charCodeAt(i)) | 0;
      h = Math.abs(h);
      var v = h % 55;
      var r, g, b;
      var sp = f.indexOf('site-packages') !== -1;
      var sl = /[/\\\\]lib[/\\\\]python[0-9]/.test(f);
      if (sp) {{
        r = 50 + v; g = 180 + (h >> 8) % 55; b = 220 + (h >> 16) % 35;
      }} else if (sl) {{
        r = 80 + v; g = 190 + (h >> 8) % 55; b = 80 + (h >> 16) % 40;
      }} else if (f.indexOf('<frozen ') === 0 || f.indexOf('<built-in') === 0) {{
        r = 220 + (h >> 8) % 35; g = 210 + (h >> 16) % 35; b = 80 + v;
      }} else {{
        r = 200 + v; g = 100 + (h >> 8) % 80; b = 50 + (h >> 16) % 30;
      }}
      return 'rgb(' + r + ',' + g + ',' + b + ')';
    }})
    .onClick(showTip)
    .onHover(showTip);

  d3.select('#chart').datum(data).call(chart);
}}

function showTip(d) {{
  var el = document.getElementById('tip');
  if (d && d.data) {{
    var s = (d.data.value || 0).toFixed(1);
    var t = (d.value || 0).toFixed(1);
    el.innerHTML = '<b>' + esc(d.data.name)
      + '</b> self: ' + s + 'ms total: ' + t + 'ms';
  }} else {{
    el.innerHTML = '';
  }}
}}

function selectView(idx, btn) {{
  if (!FLAME_DATA) return;
  document.querySelectorAll('.bar button').forEach(function(b) {{ b.className = ''; }});
  btn.className = 'on';
  render(idx < 0 ? FLAME_DATA.combined : FLAME_DATA.threads[idx].data);
}}

function doSearch() {{
  var t = document.getElementById('search').value;
  if (chart) {{ if (t) chart.search(t); else chart.clear(); }}
}}

function resetZoom() {{ if (chart) chart.resetZoom(); }}

function esc(s) {{
  var d = document.createElement('span');
  d.textContent = s; return d.innerHTML;
}}

window.addEventListener('resize', function() {{
  var a = document.querySelector('.bar button.on');
  if (a) a.click();
}});
</script>
</body>
</html>"""
