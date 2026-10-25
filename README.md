# DiskMap 🗺️

**See where your disk space actually went.**

Disk analyzers are either heavy desktop apps or cryptic CLI output.
DiskMap is a tiny Python CLI: point it at a folder and it writes one
self-contained HTML treemap — every file and folder a rectangle sized
in proportion to its disk usage, so the space hogs jump out at a
glance. Plus a Top 10 table for the biggest offenders.

## Use it

```bash
python3 diskap.py ~/Downloads -o diskap-report.html
```

Open the report in any browser. Hover any rectangle for its full path
and size. No server, no upload — the scan never leaves your machine.

## Requirements

Python 3.8+ only. No third-party packages.

## Honest limits (v1)

- Sizes are file sizes, not blocks on disk — a folder of many tiny
  files may use slightly more real disk than shown.
- Symbolic links are not followed (their own size is shown), so
  linked trees are not double-counted.
- Unreadable folders print a warning and are skipped, not silently
  treated as empty.

## Test it

```bash
python3 tests/test_diskmap.py
```

Builds a fixture tree (100 / 300 / 600 bytes) and asserts the treemap
areas are proportional to sizes, plus empty-folder and bad-path
handling.

## License

MIT — free for everyone, forever.
