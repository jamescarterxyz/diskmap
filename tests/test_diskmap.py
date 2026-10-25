"""DiskMap self-test — fixture tree + assertions.

Run:  python3 tests/test_diskmap.py
Exit code 0 = all assertions pass.
"""

import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLI = os.path.join(ROOT, "diskmap.py")
TMP = "/tmp/diskmap-test"


def make_file(path, size):
    with open(path, "wb") as f:
        f.write(b"x" * size)


def rect_areas(html_text):
    areas = {}
    for m in re.finditer(
            r'data-path="([^"]+)" data-size="(\d+)" '
            r'style="left:([\d.]+)%;top:([\d.]+)%;width:([\d.]+)%;height:([\d.]+)%',
            html_text):
        path, _size, _l, _t, w, h = m.groups()
        areas[path] = float(w) * float(h)
    return areas


def main():
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    os.makedirs(os.path.join(TMP, "sub"))
    make_file(os.path.join(TMP, "a.txt"), 100)
    make_file(os.path.join(TMP, "b.txt"), 300)
    make_file(os.path.join(TMP, "sub", "c.txt"), 600)

    report = os.path.join(TMP, "report.html")
    r = subprocess.run([sys.executable, CLI, TMP, "-o", report],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, "exit code {}: {}".format(r.returncode, r.stderr)
    assert "1,000 B" in r.stdout or "1000 B" in r.stdout, r.stdout

    html_text = open(report).read()
    assert "1,000 B" in html_text or "1000 B" in html_text, "total missing"
    areas = rect_areas(html_text)
    c = areas[os.path.join(TMP, "sub", "c.txt")]
    b = areas[os.path.join(TMP, "b.txt")]
    a = areas[os.path.join(TMP, "a.txt")]
    # Areas must be proportional to sizes: 600 > 300 > 100.
    assert c > b > a, (c, b, a)
    # Rough proportionality (areas are in percent-squared, map = 100x100):
    # c is ~60% of the map, a ~10%.
    assert 5500 < c < 6500, c
    assert 800 < a < 1200, a
    assert "sub" in html_text and "c.txt" in html_text

    # Empty dir: no crash, zero total.
    empty = os.path.join(TMP, "empty")
    os.makedirs(empty)
    r = subprocess.run([sys.executable, CLI, empty, "-o",
                        os.path.join(TMP, "e.html")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, "empty dir crashed: " + r.stderr

    # Nonexistent path: clean exit code 2.
    r = subprocess.run([sys.executable, CLI, os.path.join(TMP, "nope"),
                        "-o", os.path.join(TMP, "n.html")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 2, r.returncode

    print("ALL DISKMAP TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
