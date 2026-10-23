#!/usr/bin/env python3
"""Make RTL copies of Arabic files: each fixed file is saved next to its original as NAME_RTL.ext.

Originals are never changed.

Usage:
  fix_files.py --folder DIR [--depth 3]     fix every Arabic file in a folder that is missing RTL
  fix_files.py FILE [FILE ...]              fix specific files
  options: --font "Arial"  --outdir DIR (put copies there instead of next to originals)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_rtl  # noqa: E402
import rtl_scan  # noqa: E402


def rtl_name(path, outdir=None):
    stem, ext = os.path.splitext(os.path.basename(path))
    folder = outdir or os.path.dirname(os.path.abspath(path))
    candidate = os.path.join(folder, f"{stem}_RTL{ext}")
    n = 2
    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{stem}_RTL{n}{ext}")
        n += 1
    return candidate


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--folder")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--font")
    ap.add_argument("--outdir")
    a = ap.parse_args()
    targets = list(a.files)
    if a.folder:
        res = rtl_scan.scan_folder(a.folder, a.depth, max_files=5000, budget_s=600)
        targets += [f["path"] for f in res["files"]]
    if not targets:
        print("Nothing to fix: no Arabic files missing right-to-left layout.")
        return
    if a.outdir:
        os.makedirs(a.outdir, exist_ok=True)
    done = failed = 0
    for src in targets:
        dst = rtl_name(src, a.outdir)
        try:
            make_rtl.convert(src, dst, a.font)
            print(f"fixed: {src}\n    -> {dst}")
            done += 1
        except Exception as e:  # keep going on a bad file
            print(f"skipped: {src} ({e})")
            failed += 1
    print(f"\n{done} file(s) fixed, {failed} skipped. Originals were not changed.")


if __name__ == "__main__":
    main()
