#!/usr/bin/env python3
"""IXLS 006F: deterministic allowlisted GitHub Pages staging (stdlib only).

Run: python scripts/ixls_release.py build --root . --out /tmp/ixls-stage
This script does not publish, use GitHub credentials, or modify the source files.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlsplit, unquote

OWNER_APPROVED_GLOSSARY_SHA256 = "01a1e3052a8f03f31cf5796264bf548b7aec7d88d207ec506d2b63c3befde0da"
UNCHANGED_LESSONS = {
    "lessons/gnss-epoch/index.html": "9f92eb7831d039fe73ee8cc4244afe58920ea36b44a40bc9c8855b193b71b372",
    "lessons/newtons-cooling/index.html": "fd9291a81e26be7237b366088443423b33f6b243dc3f488264dee95d8981b3e5",
}
# STRICT publishing allowlist. A file in this list is publicly accessible after deploy.
PUBLISHED = (
    "index.html",
    "lessons/gnss-epoch/index.html",
    "lessons/newtons-cooling/index.html",
    "lessons/rs-l04/index.html",
    "lessons/rs-l04/glossary.th.json",
    "assets/ix-components/v0.2.0/jargon-lens.css",
    "assets/ix-components/v0.2.0/jargon-lens.js",
    "assets/ix-components/v0.2.0/mechanism-viewer.css",
    "assets/ix-components/v0.2.0/mechanism-viewer.js",
    "assets/ix-components/v0.2.0/mv-fallback.html",
    "CODE_AND_CONTENT_RIGHTS.md",
    "licenses/MIT-CODE.txt",
)
STAGED = frozenset((*PUBLISHED, ".nojekyll"))


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def assert_safe_file(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or not relative or "\\" in relative:
        raise ValueError(f"Untrusted path: {relative}")
    path = root / rel
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing, symlinked or unsafe input: {relative}")
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError(f"Oversize staged input: {relative}")
    return path


def verify_manifest(root: Path) -> int:
    manifest = assert_safe_file(root, "SHA256SUMS.txt")
    count = 0
    observed = set()
    for n, ln in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not ln.strip():
            continue
        m = re.fullmatch(r"([a-f0-9]{64})  ([^\n]+)", ln)
        if not m:
            raise ValueError(f"Malformed SHA256SUMS line {n}")
        digest, name = m.groups()
        if name in observed:
            raise ValueError(f"Duplicate manifest path: {name}")
        observed.add(name)
        if sha256(assert_safe_file(root, name)) != digest:
            raise ValueError(f"SHA-256 mismatch: {name}")
        count += 1
    # New workflows/scripts/signoff must be protected by the manifest too.
    required = set(PUBLISHED) | {
        "scripts/ixls_release.py", ".github/workflows/ixls-pages-manual.yml",
        "release/OWNER_SIGNOFF_006F.yaml", "lessons/rs-l04/lesson.yaml",
    }
    if not required.issubset(observed):
        raise ValueError(f"Missing manifest entries: {sorted(required - observed)}")
    if sha256(root / "lessons/rs-l04/glossary.th.json") != OWNER_APPROVED_GLOSSARY_SHA256:
        raise ValueError("Owner-approved glossary hash changed; owner signoff invalid")
    for name, expected in UNCHANGED_LESSONS.items():
        if sha256(root / name) != expected:
            raise ValueError(f"Legacy lesson changed: {name}")
    page = (root / "lessons/rs-l04/index.html").read_text(encoding="utf-8")
    matches = re.findall(r'<meta name="ix-glossary-owner-approved-sha256" content="([a-f0-9]{64})">', page)
    if matches != [OWNER_APPROVED_GLOSSARY_SHA256]:
        raise ValueError("Missing or incorrect approved-glossary metadata")
    match = re.search(r'<script type="application/json" id="ix-glossary">(.*?)</script>', page, re.S)
    if not match:
        raise ValueError("Embedded glossary JSON missing")
    gl = json.loads((root / "lessons/rs-l04/glossary.th.json").read_text(encoding="utf-8"))
    if json.loads(match.group(1)) != gl or len(gl.get("terms", [])) != 9:
        raise ValueError("Embedded glossary and reviewed JSON differ")
    return count


class RefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        key = "href" if tag in {"a", "link"} else "src" if tag in {"script", "img", "source", "iframe"} else None
        if key and data.get(key):
            self.refs.append((tag, data[key]))


def check_links(stage: Path) -> int:
    count = 0
    for rel in PUBLISHED:
        if not rel.endswith(".html") or rel.endswith("mv-fallback.html"):
            continue
        page_path = stage / rel
        p = RefParser(); p.feed(page_path.read_text(encoding="utf-8"))
        for tag, ref in p.refs:
            u = urlsplit(ref)
            if u.scheme or u.netloc:
                if tag in {"script", "link", "iframe"}:
                    raise ValueError(f"External runtime dependency in {rel}: {ref}")
                continue  # visible academic links are permitted
            if ref.startswith(("javascript:", "data:")):
                raise ValueError(f"Unexpected active link in {rel}: {ref}")
            if u.path:
                dest = (page_path.parent / unquote(u.path)).resolve()
                if not dest.is_relative_to(stage.resolve()):
                    raise ValueError(f"Link escapes published root: {rel} -> {ref}")
                if dest.is_dir():
                    dest = dest / "index.html"
                if not dest.is_file():
                    raise ValueError(f"Broken internal link: {rel} -> {ref}")
            elif u.fragment and u.fragment not in p.ids:
                raise ValueError(f"Broken fragment: {rel} -> {ref}")
            count += 1
    return count


def build(root: Path, out: Path):
    root = root.resolve()
    out = out.resolve()
    if out == root or out.is_relative_to(root):
        raise ValueError("Output must be OUTSIDE source tree: protect SHA manifest")
    n = verify_manifest(root)
    if out.exists():
        raise ValueError("Output exists; use a fresh staging path, never overwrite")
    out.mkdir(parents=True)
    try:
        for rel in PUBLISHED:
            src = assert_safe_file(root, rel)
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            if sha256(src) != sha256(dst):
                raise ValueError(f"Copy integrity failure: {rel}")
        (out / ".nojekyll").write_bytes(b"")
        found = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
        if found != STAGED:
            raise ValueError(f"Unexpected stage files: {found ^ STAGED}")
        link_count = check_links(out)
        print(json.dumps({"status": "PASS", "manifest_entries": n, "published_files": len(found), "internal_links_checked": link_count, "glossary_sha256": OWNER_APPROVED_GLOSSARY_SHA256, "stage": str(out)}, ensure_ascii=False, indent=2))
    except Exception:
        shutil.rmtree(out)
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["verify", "build"])
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.command == "build":
        if not args.out:
            ap.error("build requires --out")
        build(args.root, args.out)
    else:
        n = verify_manifest(args.root.resolve())
        print(json.dumps({"status": "PASS", "manifest_entries": n, "glossary_sha256": OWNER_APPROVED_GLOSSARY_SHA256}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as ex:
        print(f"IXLS RELEASE GATE FAILED: {ex}", file=sys.stderr)
        sys.exit(1)
