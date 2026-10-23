#!/usr/bin/env python3
"""Find Arabic content that needs fixing: replies in a chat transcript, and files in a chat or a folder.

Usage:
  rtl_scan.py --transcript PATH          scan a Claude chat transcript (.jsonl)
  rtl_scan.py --folder DIR [--depth 3]   scan a folder for Arabic .docx/.xlsx/.pptx/.html missing RTL
  add --json for machine-readable output
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bidi_check  # noqa: E402
import make_rtl  # noqa: E402

FILE_EXTS = tuple("." + e for e in make_rtl.SUPPORTED)
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "AppData", "Library", ".cache", ".claude", ".local"}
SEVERE = ("starts with", "file name")  # issues that visibly scramble a block


def reply_issues(text):
    issues, _ = bidi_check.process(text.splitlines(keepends=True))
    return [i for i in issues if i[2].startswith(SEVERE)]


def check_file(path):
    try:
        total, missing = make_rtl.check(path)
    except Exception:
        return None
    if total and missing:
        return {"path": path, "arabic_parts": total, "missing_rtl": missing}
    return None


def collect_paths(obj, out):
    """Pull file paths out of tool inputs (Write file_path, SendUserFile files, etc.)."""
    if isinstance(obj, dict):
        for v in obj.values():
            collect_paths(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_paths(v, out)
    elif isinstance(obj, str) and obj.lower().endswith(FILE_EXTS) and len(obj) < 500 and "\n" not in obj:
        out.add(obj)


def scan_transcript(path, cwd=None):
    replies, paths, idx = [], set(), 0
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            msg = d.get("message") if isinstance(d.get("message"), dict) else None
            if not msg:
                continue
            content = msg.get("content")
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
            if d.get("type") == "assistant":
                text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
                if text.strip():
                    idx += 1
                    found = reply_issues(text)
                    if found:
                        replies.append({"reply_number": idx, "starts_with": text.strip()[:70].replace("\n", " "),
                                        "problems": len(found)})
                for b in blocks:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        collect_paths(b.get("input"), paths)
            elif d.get("type") == "user":
                for b in blocks:
                    if isinstance(b, dict) and b.get("type") == "text":
                        for tok in b.get("text", "").split():
                            tok = tok.strip("\"'`()[]<>,")
                            if tok.lower().endswith(FILE_EXTS) and os.path.isabs(tok):
                                paths.add(tok)
    files = []
    for p in sorted(paths):
        full = p if os.path.isabs(p) else os.path.join(cwd or os.getcwd(), p)
        if os.path.isfile(full):
            r = check_file(full)
            if r:
                files.append(r)
    return {"replies": replies, "assistant_replies": idx, "files": files}


def scan_folder(root, depth=3, max_files=400, budget_s=6.0):
    start, seen, found = time.time(), 0, []
    root = os.path.abspath(root)
    base_depth = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS]
        if dirpath.count(os.sep) - base_depth >= depth:
            dirnames[:] = []
        for fn in filenames:
            if fn.startswith(("~$", ".")) or not fn.lower().endswith(FILE_EXTS):
                continue
            stem, ext = os.path.splitext(fn)
            if "_RTL" in stem or os.path.exists(os.path.join(dirpath, f"{stem}_RTL{ext}")):
                continue  # a copy this plugin made, or an original that already has one
            seen += 1
            r = check_file(os.path.join(dirpath, fn))
            if r:
                found.append(r)
            if seen >= max_files or time.time() - start > budget_s:
                return {"folder": root, "checked": seen, "files": found, "partial": True}
    return {"folder": root, "checked": seen, "files": found, "partial": False}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript")
    ap.add_argument("--folder")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not (a.transcript or a.folder):
        ap.error("give --transcript and/or --folder")
    result = {}
    if a.transcript:
        result["chat"] = scan_transcript(a.transcript)
    if a.folder:
        result["folder"] = scan_folder(a.folder, a.depth)
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return
    if "chat" in result:
        c = result["chat"]
        print(f"Chat: {len(c['replies'])} of {c['assistant_replies']} replies have scrambled Arabic blocks; "
              f"{len(c['files'])} Arabic file(s) missing RTL.")
        for r in c["replies"]:
            print(f"  reply #{r['reply_number']}: {r['starts_with']}")
        for f in c["files"]:
            print(f"  file: {f['path']} ({f['missing_rtl']}/{f['arabic_parts']} Arabic parts not RTL)")
    if "folder" in result:
        fo = result["folder"]
        print(f"Folder {fo['folder']}: checked {fo['checked']} file(s){' (stopped early)' if fo['partial'] else ''}; "
              f"{len(fo['files'])} Arabic file(s) missing RTL.")
        for f in fo["files"]:
            print(f"  {f['path']} ({f['missing_rtl']}/{f['arabic_parts']} Arabic parts not RTL)")


if __name__ == "__main__":
    main()
