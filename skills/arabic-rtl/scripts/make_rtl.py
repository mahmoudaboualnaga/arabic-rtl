#!/usr/bin/env python3
"""Set right-to-left layout on the Arabic parts of a .docx, .xlsx, .pptx or .html file.

Only paragraphs / runs / tables / sheets / slides that contain Arabic are changed,
so English-only content keeps its left-to-right layout. Charts, images and
everything else in the file are copied untouched.

Usage:
  make_rtl.py INPUT OUTPUT [--font "Arial"] [--lang ar-EG]
"""
import argparse
import re
import shutil
import sys
import zipfile

from lxml import etree

ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def w(tag):
    return f"{{{W}}}{tag}"


def a(tag):
    return f"{{{A}}}{tag}"


# Schema order of children, needed so Word accepts the file.
PPR_ORDER = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
             "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
             "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
             "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
             "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
             "sectPr", "pPrChange"]
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline",
             "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing",
             "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText",
             "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"]
TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize",
               "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar",
               "tblLook", "tblCaption", "tblDescription", "tblPrChange"]
SECTPR_ORDER = ["headerReference", "footerReference", "footnotePr", "endnotePr", "type", "pgSz", "pgMar",
                "paperSrc", "pgBorders", "lnNumType", "pgNumType", "cols", "formProt", "vAlign", "noEndnote",
                "titlePg", "textDirection", "bidi", "rtlGutter", "docGrid", "printerSettings", "sectPrChange"]


def ensure_child(parent, tag, order, ns=w):
    """Return existing child <tag>, or insert a new one at its schema position."""
    existing = parent.find(ns(tag))
    if existing is not None:
        return existing
    el = etree.Element(ns(tag))
    pos = order.index(tag)
    for i, child in enumerate(parent):
        local = etree.QName(child).localname if isinstance(child.tag, str) else None
        if local in order and order.index(local) > pos:
            parent.insert(i, el)
            return el
    parent.append(el)
    return el


def first_child(parent, tag):
    el = parent.find(w(tag))
    if el is None:
        el = etree.Element(w(tag))
        parent.insert(0, el)
    return el


def text_of(el, ns_t):
    return "".join(t.text or "" for t in el.iter(ns_t))


# ---------------------------------------------------------------- Word
def fix_docx_part(root, lang, stats):
    for p in root.iter(w("p")):
        if not ARABIC.search(text_of(p, w("t"))):
            continue
        ppr = first_child(p, "pPr")
        ensure_child(ppr, "bidi", PPR_ORDER)
        jc = ppr.find(w("jc"))
        if jc is not None and jc.get(w("val")) in ("left", "right", "start", "end"):
            ppr.remove(jc)  # default alignment of a bidi paragraph is the right edge
        stats["paragraphs"] += 1
        for r in p.iter(w("r")):
            rpr = r.find(w("rPr"))
            if rpr is None:
                rpr = etree.Element(w("rPr"))
                r.insert(0, rpr)
            if ARABIC.search(text_of(r, w("t"))):
                ensure_child(rpr, "rtl", RPR_ORDER)
                stats["runs"] += 1
            # complex-script twins so Arabic gets the same bold/italic/size as Latin
            for latin, cs in (("b", "bCs"), ("i", "iCs")):
                if rpr.find(w(latin)) is not None:
                    ensure_child(rpr, cs, RPR_ORDER)
            sz = rpr.find(w("sz"))
            if sz is not None and rpr.find(w("szCs")) is None:
                ensure_child(rpr, "szCs", RPR_ORDER).set(w("val"), sz.get(w("val")))
            lg = ensure_child(rpr, "lang", RPR_ORDER)
            lg.set(w("bidi"), lang)
    for tbl in root.iter(w("tbl")):
        if ARABIC.search(text_of(tbl, w("t"))):
            tblpr = tbl.find(w("tblPr"))
            if tblpr is None:
                tblpr = etree.Element(w("tblPr"))
                tbl.insert(0, tblpr)
            ensure_child(tblpr, "bidiVisual", TBLPR_ORDER)
            stats["tables"] += 1


def fix_docx_sections(root):
    all_text = text_of(root, w("t"))
    arabic = len(ARABIC.findall(all_text))
    latin = len(re.findall(r"[A-Za-z]", all_text))
    if arabic > latin:  # mostly Arabic document -> pages read right to left
        for sect in root.iter(w("sectPr")):
            ensure_child(sect, "bidi", SECTPR_ORDER)


def fix_docx_styles(root, font, lang):
    defaults = root.find(w("docDefaults"))
    if defaults is None:
        return
    rpr_default = defaults.find(w("rPrDefault"))
    if rpr_default is None:
        return
    rpr = rpr_default.find(w("rPr"))
    if rpr is None:
        rpr = etree.SubElement(rpr_default, w("rPr"))
    fonts = ensure_child(rpr, "rFonts", RPR_ORDER)
    if font or not fonts.get(w("cs")) and not fonts.get(w("cstheme")):
        fonts.set(w("cs"), font or "Arial")
        fonts.attrib.pop(w("cstheme"), None)
    sz = rpr.find(w("sz"))
    if sz is not None and rpr.find(w("szCs")) is None:
        ensure_child(rpr, "szCs", RPR_ORDER).set(w("val"), sz.get(w("val")))
    ensure_child(rpr, "lang", RPR_ORDER).set(w("bidi"), lang)


def docx(zin, name, data, opts, stats):
    if name == "word/styles.xml":
        root = etree.fromstring(data)
        fix_docx_styles(root, opts.font, opts.lang)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    if re.fullmatch(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml", name):
        root = etree.fromstring(data)
        fix_docx_part(root, opts.lang, stats)
        if name == "word/document.xml":
            fix_docx_sections(root)
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    return data


# ---------------------------------------------------------------- PowerPoint
P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def is_title(p):
    sp = p.getparent()
    while sp is not None and etree.QName(sp).localname != "sp":
        sp = sp.getparent()
    if sp is None:
        return False
    ph = sp.find(f".//{{{P}}}ph")
    return ph is not None and ph.get("type") in ("title", "ctrTitle", "subTitle")


def pptx(zin, name, data, opts, stats):
    if not re.fullmatch(r"ppt/(slides/slide|notesSlides/notesSlide)\d+\.xml", name):
        return data
    root = etree.fromstring(data)
    for p in root.iter(a("p")):
        if not ARABIC.search(text_of(p, a("t"))):
            continue
        ppr = p.find(a("pPr"))
        if ppr is None:
            ppr = etree.Element(a("pPr"))
            p.insert(0, ppr)
        ppr.set("rtl", "1")
        if ppr.get("algn") == "l" or (ppr.get("algn") is None and not is_title(p)):
            ppr.set("algn", "r")  # titles keep their inherited (often centered) alignment
        stats["paragraphs"] += 1
        for r in p.iter(a("r")):
            if ARABIC.search(text_of(r, a("t"))):
                rpr = r.find(a("rPr"))
                if rpr is None:
                    rpr = etree.Element(a("rPr"))
                    r.insert(0, rpr)
                rpr.set("lang", opts.lang)
                if opts.font:
                    cs = rpr.find(a("cs"))
                    if cs is None:
                        cs = etree.Element(a("cs"))
                        # cs goes after latin/ea, before sym/hlink*
                        anchor = None
                        for tag in ("sym", "hlinkClick", "hlinkMouseOver", "rtl", "extLst"):
                            anchor = rpr.find(a(tag))
                            if anchor is not None:
                                break
                        if anchor is not None:
                            anchor.addprevious(cs)
                        else:
                            rpr.append(cs)
                    cs.set("typeface", opts.font)
                stats["runs"] += 1
    for tbl in root.iter(a("tbl")):
        if ARABIC.search(text_of(tbl, a("t"))):
            tblpr = tbl.find(a("tblPr"))
            if tblpr is None:
                tblpr = etree.Element(a("tblPr"))
                tbl.insert(0, tblpr)
            tblpr.set("rtl", "1")
            stats["tables"] += 1
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------------------------------------------------------------- Excel
def xlsx_shared_strings(zin):
    try:
        root = etree.fromstring(zin.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(t.text or "" for t in si.iter(f"{{{S}}}t")) for si in root.findall(f"{{{S}}}si")]


def xlsx_sheet_has_arabic(root, shared):
    for c in root.iter(f"{{{S}}}c"):
        v = c.find(f"{{{S}}}v")
        if c.get("t") == "s" and v is not None and v.text and v.text.isdigit():
            idx = int(v.text)
            txt = shared[idx] if idx < len(shared) else ""
        else:
            txt = "".join(t.text or "" for t in c.iter(f"{{{S}}}t"))
        if ARABIC.search(txt):
            return True
    return False


def xlsx(zin, name, data, opts, stats):
    if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
        return data
    if "_ss" not in stats:
        stats["_ss"] = xlsx_shared_strings(zin)
    shared = stats["_ss"]
    root = etree.fromstring(data)
    if not xlsx_sheet_has_arabic(root, shared):
        return data
    views = root.find(f"{{{S}}}sheetViews")
    if views is None:
        views = etree.Element(f"{{{S}}}sheetViews")
        # sheetViews comes after sheetPr and dimension
        idx = 0
        for i, child in enumerate(root):
            if etree.QName(child).localname in ("sheetPr", "dimension"):
                idx = i + 1
        root.insert(idx, views)
    view = views.find(f"{{{S}}}sheetView")
    if view is None:
        view = etree.SubElement(views, f"{{{S}}}sheetView", workbookViewId="0")
    view.set("rightToLeft", "1")
    stats["sheets"] += 1
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------------------------------------------------------------- HTML
HTML_CSS = """<style id="arabic-rtl">
p, li, td, th, dd, dt, blockquote, figcaption, h1, h2, h3, h4, h5, h6 { unicode-bidi: plaintext; text-align: start; }
body { line-height: 1.8; }
code, pre, kbd, samp { direction: ltr; unicode-bidi: isolate; }
</style>"""


def html_file(src, dst, opts):
    html = open(src, encoding="utf-8").read()
    m = re.search(r"<html\b[^>]*>", html, re.I)
    if m:
        tag = m.group(0)
        new = re.sub(r'\sdir="[^"]*"', "", tag)
        new = re.sub(r'\slang="[^"]*"', "", new)
        new = new[:-1] + f' dir="rtl" lang="{opts.lang.split("-")[0]}">'
        html = html.replace(tag, new, 1)
    else:
        html = f'<html dir="rtl" lang="{opts.lang.split("-")[0]}">\n{html}\n</html>'
    if 'id="arabic-rtl"' not in html:
        if re.search(r"</head>", html, re.I):
            html = re.sub(r"</head>", HTML_CSS + "\n</head>", html, count=1, flags=re.I)
        else:
            html = html.replace(">", ">\n" + HTML_CSS, 1)
    open(dst, "w", encoding="utf-8").write(html)
    print(f"HTML: set dir=rtl, lang, and bidi-safe CSS -> {dst}")


# ---------------------------------------------------------------- API
HANDLERS = {"docx": docx, "dotx": docx, "docm": docx, "pptx": pptx, "potx": pptx,
            "xlsx": xlsx, "xlsm": xlsx, "xltx": xlsx}
SUPPORTED = tuple(HANDLERS) + ("html", "htm")


class Opts:
    def __init__(self, font=None, lang="ar-EG"):
        self.font, self.lang = font, lang


def convert(src, dst, font=None, lang="ar-EG"):
    """Write an RTL copy of src to dst. Returns a dict of counts."""
    opts = Opts(font, lang)
    ext = src.lower().rsplit(".", 1)[-1]
    if ext in ("html", "htm"):
        html_file(src, dst, opts)
        return {"html": 1}
    handler = HANDLERS.get(ext)
    if handler is None:
        raise ValueError(f"Unsupported file type: .{ext} (use .docx, .xlsx, .pptx or .html)")
    stats = {"paragraphs": 0, "runs": 0, "tables": 0, "sheets": 0}
    tmp = dst + ".tmp"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".xml"):
                data = handler(zin, item.filename, data, opts, stats)
            zout.writestr(item, data)
    shutil.move(tmp, dst)
    stats.pop("_ss", None)
    return stats


def check(path):
    """Return (arabic_units, units_missing_rtl) for a file; (0, 0) when it has no Arabic.

    Units: paragraphs for Word/PowerPoint, sheets for Excel, the page for HTML.
    """
    ext = path.lower().rsplit(".", 1)[-1]
    if ext in ("html", "htm"):
        html = open(path, encoding="utf-8", errors="ignore").read()
        if not ARABIC.search(re.sub(r"<[^>]+>", " ", html)):
            return 0, 0
        tag = re.search(r"<html\b[^>]*>", html, re.I)
        ok = bool(tag and re.search(r'dir\s*=\s*["\']?rtl', tag.group(0), re.I)) or bool(
            re.search(r'<body\b[^>]*dir\s*=\s*["\']?rtl', html, re.I))
        return 1, 0 if ok else 1
    total = missing = 0
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if ext in ("docx", "dotx", "docm"):
            for n in names:
                if re.fullmatch(r"word/(document|header\d*|footer\d*)\.xml", n):
                    root = etree.fromstring(z.read(n))
                    for p in root.iter(w("p")):
                        if ARABIC.search(text_of(p, w("t"))):
                            total += 1
                            ppr = p.find(w("pPr"))
                            bidi = ppr.find(w("bidi")) if ppr is not None else None
                            if bidi is None or bidi.get(w("val")) in ("0", "false"):
                                missing += 1
        elif ext in ("pptx", "potx"):
            for n in names:
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", n):
                    root = etree.fromstring(z.read(n))
                    for p in root.iter(a("p")):
                        if ARABIC.search(text_of(p, a("t"))):
                            total += 1
                            ppr = p.find(a("pPr"))
                            if ppr is None or ppr.get("rtl") != "1":
                                missing += 1
        elif ext in ("xlsx", "xlsm", "xltx"):
            shared = xlsx_shared_strings(z)
            for n in names:
                if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n):
                    root = etree.fromstring(z.read(n))
                    if xlsx_sheet_has_arabic(root, shared):
                        total += 1
                        view = root.find(f".//{{{S}}}sheetView")
                        if view is None or view.get("rightToLeft") not in ("1", "true"):
                            missing += 1
    return total, missing


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--font", help='Arabic (complex-script) font, e.g. "Arial", "Simplified Arabic", "Cairo"')
    ap.add_argument("--lang", default="ar-EG", help="language tag for Arabic text (default ar-EG)")
    opts = ap.parse_args()

    try:
        stats = convert(opts.input, opts.output, opts.font, opts.lang)
    except ValueError as e:
        sys.exit(str(e))
    done = ", ".join(f"{v} {k}" for k, v in stats.items() if v)
    print(f"RTL set on: {done or 'nothing (no Arabic found)'} -> {opts.output}")


if __name__ == "__main__":
    main()
