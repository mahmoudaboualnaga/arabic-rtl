#!/usr/bin/env python3
"""Lint Arabic / mixed Arabic-English text (Markdown, chat drafts) for bidi problems.

Viewers that pick a paragraph's direction from its first strong letter (chat apps,
Markdown renderers, many editors) scramble Arabic blocks that open with a Latin word,
and push trailing punctuation to the wrong side when a block ends in Latin text.

Usage:
  bidi_check.py FILE            report problems (exit 1 if any)
  bidi_check.py FILE --fix      write FILE with RLM marks inserted (or -o OUT)
  cat FILE | bidi_check.py -    read from stdin
"""
import argparse
import re
import sys
import unicodedata

RLM = "‏"
ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
# leading Markdown syntax that is not part of the visible text
LEAD = re.compile(r"^(\s*(?:>\s*)*(?:[-*+]\s+(?:\[[ xX]\]\s+)?|\d+[.)]\s+|#{1,6}\s+)?)")
END_LATIN_PUNCT = re.compile(r"([A-Za-z][A-Za-z0-9%)\]\"'”`*_]*)([.،,:;!?؟]+)(\s*)$")
LATIN_LIST = re.compile(r"[A-Za-z][A-Za-z0-9]*\s*[،,]\s*[A-Za-z]")
LONG_LATIN = re.compile(r"(?:[A-Za-z][\w'’-]*\s+){4,}[A-Za-z][\w'’-]*")
RANGE = re.compile(r"\d+\s*[–—-]\s*\d+\s*%?")


def first_strong(text):
    """Return 'L', 'R' or None for the first strong bidi character, skipping URLs in ](...)."""
    text = re.sub(r"\]\([^)]*\)", "]", text)  # link targets are not displayed
    for ch in text:
        if ch == RLM:
            return "R"
        b = unicodedata.bidirectional(ch)
        if b == "L":
            return "L"
        if b in ("R", "AL"):
            return "R"
    return None


def check_block(text, lineno, where, issues):
    """Check one visible block (a line, or one table cell). Return fixed text."""
    if not ARABIC.search(text):
        return text
    m = LEAD.match(text)
    lead, body = m.group(1), text[m.end():]
    fixed_body = body
    if first_strong(body) == "L":
        issues.append((lineno, where, "starts with an English word -> block renders left-to-right", body.strip()[:60]))
        fixed_body = RLM + fixed_body
    e = END_LATIN_PUNCT.search(fixed_body)
    if e and not fixed_body[: e.start(2)].endswith(RLM):
        issues.append((lineno, where, "ends with English/number + punctuation -> punctuation jumps to the wrong side", fixed_body.strip()[-40:]))
        fixed_body = fixed_body[: e.start(2)] + RLM + fixed_body[e.start(2):]
    # what the reader actually sees: no link targets, no inline code
    visible = re.sub(r"`[^`]*`", " ", re.sub(r"\]\([^)]*\)", "]", body))
    if LATIN_LIST.search(visible):
        issues.append((lineno, where, "English terms separated by commas -> reword with Arabic 'و' between them", LATIN_LIST.search(visible).group(0)))
    if LONG_LATIN.search(visible):
        issues.append((lineno, where, "long English phrase inside Arabic text -> move to its own line or shorten", LONG_LATIN.search(visible).group(0)[:50]))
    if re.search(r"\b\w+\.(?:xlsx|docx|pptx|pdf|csv|md|html|png|jpg)\b", visible, re.I):
        issues.append((lineno, where, "file name inside an Arabic sentence -> put it on its own line in backticks", re.search(r"\b\w+\.\w{2,4}\b", visible).group(0)[:50]))
    if RANGE.search(visible):
        issues.append((lineno, where, "numeric range with a dash -> write 'من X إلى Y'", RANGE.search(visible).group(0)))
    return lead + fixed_body


def process(lines):
    issues, out, in_code = [], [], False
    for i, line in enumerate(lines, 1):
        raw = line.rstrip("\n")
        nl = line[len(raw):]
        if raw.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code or not raw.strip():
            out.append(line)
            continue
        if raw.lstrip().startswith("|"):
            if re.fullmatch(r"\s*\|[\s:|-]+\|?\s*", raw):  # separator row
                out.append(line)
                continue
            cells = raw.split("|")
            new = [cells[0]]
            for c_idx, cell in enumerate(cells[1:-1], 1):
                sp = re.match(r"^(\s*)(.*?)(\s*)$", cell)
                fixed = check_block(sp.group(2), i, f"cell {c_idx}", issues)
                new.append(sp.group(1) + fixed + sp.group(3))
            new.append(cells[-1])
            out.append("|".join(new) + nl)
            continue
        out.append(check_block(raw, i, "line", issues) + nl)
    return issues, out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="text/Markdown file, or - for stdin")
    ap.add_argument("--fix", action="store_true", help="insert RLM marks where needed")
    ap.add_argument("-o", "--output", help="output path for --fix (default: overwrite input; stdout for stdin)")
    a = ap.parse_args()
    src = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8").read()
    issues, out = process(src.splitlines(keepends=True))
    for ln, where, msg, snip in issues:
        print(f"line {ln} ({where}): {msg}\n    {snip}", file=sys.stderr)
    if not issues:
        print("No bidi problems found.", file=sys.stderr)
    if a.fix:
        text = "".join(out)
        if a.output:
            open(a.output, "w", encoding="utf-8").write(text)
        elif a.file == "-":
            sys.stdout.write(text)
        else:
            open(a.file, "w", encoding="utf-8").write(text)
        print(f"Fixed {sum(1 for x in issues if 'starts' in x[2] or 'ends' in x[2])} block(s) with RLM marks.", file=sys.stderr)
    sys.exit(1 if issues and not a.fix else 0)


if __name__ == "__main__":
    main()
