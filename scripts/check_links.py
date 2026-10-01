#!/usr/bin/env python3
"""Fail on any bare-root tidings.family link (BB 2026-10-01).

A link someone shares or taps to get the app must be the smart-install link
https://tidings.family/get/ (plus ?ref=/?c= where one exists), never the bare
https://tidings.family — the root is a webpage, not a store hop. Scans every
tracked file except docs/ and Markdown (historical records). A line that
intentionally links the homepage carries the marker `link-lint:allow`.

Usage: python3 scripts/check_links.py   (exit 1 + file:line list on a hit)
"""
import re
import subprocess
import sys

# Host not continued (tidings.family.com, tidings.familyx) and no path segment after it — a bare
# root, with or without a trailing slash or query string, matches; /get/, /privacy etc. don't.
BARE = re.compile(r"https?://(?:www\.)?tidings\.family(?![\w-]|\.\w)(?!/[\w.-])")
SKIP_DIRS = ("docs/",)
SKIP_EXT = (".md", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".keystore", ".jks")


def main() -> int:
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                           check=True).stdout.split()
    hits = []
    for path in files:
        if path.startswith(SKIP_DIRS) or path.lower().endswith(SKIP_EXT):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        for n, line in enumerate(lines, 1):
            if BARE.search(line) and "link-lint:allow" not in line:
                hits.append(f"{path}:{n}: {line.strip()}")
    if hits:
        print("Bare-root tidings.family link(s) — use https://tidings.family/get/:")
        print("\n".join(hits))
        return 1
    print("check_links: no bare-root tidings.family links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
