#!/usr/bin/env python3
"""DiskMap — see where your disk space actually went.

Usage:
    python3 diskap.py ~/Downloads -o diskap-report.html

Scans a folder and writes a single self-contained HTML treemap: every
file and folder is a rectangle sized in proportion to its disk usage,
so the space hogs are visible at a glance. No server, no upload, no
third party — the scan never leaves your machine.

Exit code is 0 unless the target folder cannot be read.
"""

import argparse
import html
import os
import sys

COLORS = ["#0ea5e9", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
          "#ec4899", "#14b8a6", "#f97316"]


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return "{:,.0f} {}".format(n, unit) if unit == "B" \
                else "{:.1f} {}".format(n, unit)
        n /= 1024.0
    return "{:.1f} PB".format(n)


def scan(path):
    """Return a node: {name, path, size, children or None}."""
    try:
        st = os.lstat(path)
    except OSError as e:
        print("warning: cannot stat {}: {}".format(path, e), file=sys.stderr)
        return {"name": os.path.basename(path) or path, "path": path,
                "size": 0, "children": None}
    node = {"name": os.path.basename(path) or path, "path": path,
            "size": 0, "children": None}
    if os.path.isdir(path) and not os.path.islink(path):
        children = []
        try:
            entries = sorted(os.listdir(path))
        except OSError as e:
            print("warning: cannot list {}: {}".format(path, e),
                  file=sys.stderr)
            entries = []
        for entry in entries:
            child = scan(os.path.join(path, entry))
            children.append(child)
            node["size"] += child["size"]
        node["children"] = children
    else:
        node["size"] = st.st_size
    return node


def layout(node, x, y, w, h, horizontal, depth, rects):
    """Slice-and-dice treemap: rects get (node, x, y, w, h, depth)."""
    rects.append((node, x, y, w, h, depth))
    children = [c for c in (node["children"] or []) if c["size"] > 0]
    if not children or node["size"] == 0:
        return
    children.sort(key=lambda c: -c["size"])
    offset = 0.0
    for child in children:
        frac = child["size"] / node["size"]
        if horizontal:
            cw, ch, cx, cy = w * frac, h, x + offset, y
            offset += cw
        else:
            cw, ch, cx, cy = w, h * frac, x, y + offset
            offset += ch
        layout(child, cx, cy, cw, ch, not horizontal, depth + 1, rects)


def render(root, rects):
    divs = []
    for node, x, y, w, h, depth in rects:
        color = COLORS[depth % len(COLORS)]
        area = w * h
        label = ""
        if area >= 0.015:  # only label rectangles big enough to read
            label = "<span>{}<br>{}</span>".format(
                html.escape(node["name"]), human(node["size"]))
        divs.append(
            '<div class="r" data-path="{}" data-size="{}" '
            'style="left:{:.2f}%;top:{:.2f}%;width:{:.2f}%;height:{:.2f}%;'
            'background:{}" title="{} — {}">{}</div>'.format(
                html.escape(node["path"], quote=True), node["size"],
                x, y, w, h, color,
                html.escape(node["path"], quote=True), human(node["size"]),
                label))
    top = sorted((c for c in (root["children"] or [])),
                 key=lambda c: -c["size"])[:10]
    top_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{:.1f}%</td></tr>".format(
            html.escape(c["path"]), human(c["size"]),
            100.0 * c["size"] / root["size"] if root["size"] else 0)
        for c in top)
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>DiskMap — {root}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#1e293b}}
.map{{position:relative;width:100%;height:70vh;border:1px solid #cbd5e1;overflow:hidden;background:#f8fafc}}
.r{{position:absolute;box-sizing:border-box;border:1px solid #fff;overflow:hidden;padding:4px;font-size:.8rem;color:#fff}}
.r span{{text-shadow:0 1px 2px rgba(0,0,0,.6);word-break:break-all}}
table{{border-collapse:collapse;width:100%;margin-top:16px}}th,td{{border-bottom:1px solid #e2e8f0;padding:6px;text-align:left}}
</style></head><body>
<h1>🗺️ DiskMap</h1>
<p>{root} — total <strong>{total}</strong></p>
<div class="map">{divs}</div>
<h2>Top 10</h2>
<table><tr><th>Path</th><th>Size</th><th>Share</th></tr>{top}</table>
</body></html>""".format(root=html.escape(root["path"]), total=human(root["size"]),
                     divs="\n".join(divs), top=top_rows)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Map a folder's disk usage as a treemap HTML report.")
    ap.add_argument("path", help="folder to scan")
    ap.add_argument("-o", "--output", default="diskmap-report.html",
                    help="HTML report to write (default: %(default)s)")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.path):
        print("not a folder: {}".format(args.path), file=sys.stderr)
        return 2
    root = scan(args.path)
    rects = []
    layout(root, 0, 0, 100, 100, True, 0, rects)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(render(root, rects))
    print("scanned {} — total {} — report written: {}".format(
        args.path, human(root["size"]), args.output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
