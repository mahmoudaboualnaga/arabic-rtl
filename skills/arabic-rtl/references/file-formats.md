# RTL settings per file format

Set direction while building the file; then run `scripts/make_rtl.py` as a safety net and look at a rendered page.

## Fonts

Arabic is drawn with the **complex-script font**, which is separate from the Latin font. Always set it, or Word/PowerPoint fall back to a font that may look wrong.

| Use | Safe on any Windows/Mac/Office | Web (Google Fonts) |
|---|---|---|
| Body text | Arial, Tahoma, Segoe UI | Noto Naskh Arabic, IBM Plex Sans Arabic, Tajawal |
| Headings | Arial Bold, Sakkal Majalla | Cairo, Almarai, Noto Kufi Arabic |
| Formal / print | Simplified Arabic, Traditional Arabic | Amiri |

Arabic needs more line height than Latin: 1.5–1.8 in documents, 1.8 on the web. Bump Arabic size 1–2 pt above the Latin size for the same visual weight.

## Word (.docx)

Paragraph: `<w:pPr><w:bidi/></w:pPr>` — direction right-to-left, list numbers/bullets on the right, default alignment on the right. Do not add `w:jc="right"`; leave alignment default (or `both` for justified). In a bidi paragraph `left`/`right` are easy to get backwards.

Run: `<w:rPr><w:rtl/><w:rFonts w:cs="Arial"/><w:szCs w:val="24"/><w:bCs/><w:lang w:bidi="ar-EG"/></w:rPr>` — `szCs`, `bCs`, `iCs` are the Arabic twins of `sz`, `b`, `i`; without them Arabic ignores the size and bold you set.

Table: `<w:tblPr><w:bidiVisual/></w:tblPr>` — first column on the right.

Section: `<w:sectPr>…<w:bidi/>…</w:sectPr>` — for a mostly Arabic document (page columns, gutter).

Defaults (`styles.xml` → `docDefaults/rPrDefault/rPr`): `<w:rFonts w:cs="Arial"/>` and `<w:lang w:bidi="ar-EG"/>`.

### docx-js (JavaScript, the docx skill's default)

```js
new Paragraph({
  bidirectional: true,                      // w:bidi
  children: [new TextRun({ text: "نص عربي", rightToLeft: true, font: { cs: "Arial" }, size: 24, sizeComplexScript: 24, boldComplexScript: true })],
});
new Table({ visuallyRightToLeft: true, rows: [/* ... */] });   // w:bidiVisual
// numbered/bulleted list paragraphs also need bidirectional: true
```

### python-docx

python-docx has no RTL API. Build normally, then run `make_rtl.py` on the saved file — it adds every setting above. Or set them by hand:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
p._p.get_or_add_pPr().insert_element_before(OxmlElement("w:bidi"), "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:jc")
r._r.get_or_add_rPr().append(OxmlElement("w:rtl"))
```

Headers/footers: page numbers and dates in an Arabic footer still need `w:bidi` on the footer paragraph (the script handles header/footer parts too).

## Excel (.xlsx)

- Sheet: `ws.sheet_view.rightToLeft = True` (openpyxl) — column A on the right, scrolling from the right.
- Cells with Arabic: `Alignment(horizontal="right", vertical="center", readingOrder=2, wrap_text=True)` (`readingOrder` 2 = RTL, 1 = LTR, 0 = by content).
- Keep numbers as real numbers (not text) so they align and sum; put units in the header: `القيمة (جنيه)`.
- Do not reload and resave a workbook that has charts or images with openpyxl (it drops them). `make_rtl.py` edits the XML directly and keeps them.

## PowerPoint (.pptx)

- Paragraph: `<a:pPr rtl="1" algn="r">` (python-pptx: `pPr = p._p.get_or_add_pPr(); pPr.set("rtl", "1"); pPr.set("algn", "r")`). Centered titles keep `algn="ctr"`.
- Run: `<a:rPr lang="ar-EG">` and `<a:cs typeface="Arial"/>` inside it for the Arabic font.
- Table: `<a:tblPr rtl="1">`.
- Mirror the layout too: logo, image and accent bar positions that sit on the left in an English deck go on the right; charts' category axis reads right to left (set `orientation="maxMin"` on the category axis if the chart should read from the right).
- Bullets appear on the right automatically once `rtl="1"` is set.

## HTML / web pages / artifacts

```html
<html dir="rtl" lang="ar">
<style>
  body { font-family: "Noto Naskh Arabic", "IBM Plex Sans Arabic", Tahoma, sans-serif; line-height: 1.8; }
  p, li, td, th, h1, h2, h3 { unicode-bidi: plaintext; text-align: start; }  /* each block finds its own direction */
  code, pre { direction: ltr; unicode-bidi: isolate; }
</style>
<p>منصة <bdi>Fabconnect</bdi> بتربط الشركات بشبكة مصنّعين.</p>
```

- Use logical CSS (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `text-align: start`, `border-inline-start`) instead of left/right so the layout mirrors by itself.
- Wrap English terms, numbers with units in English, user names and file names in `<bdi>`; inputs that may hold either language get `dir="auto"`.
- Flex/grid follow `dir` automatically; icons that mean direction (arrows, "next", back) must be mirrored: `[dir=rtl] .icon-arrow { transform: scaleX(-1); }`. Do not mirror logos, clocks, media play buttons, or checkmarks.
- Charts (Chart.js, Recharts, D3): set the legend and the category axis to read from the right where the page is Arabic, and keep axis numbers in Western digits unless the user uses Arabic-Indic digits.

## PDF

Never draw Arabic directly with ReportLab, FPDF or Pillow — they don't join letters or reorder words, so the text comes out disconnected and backwards. Instead:

1. Build an RTL .docx (above), then `soffice --headless --convert-to pdf file.docx`, or
2. Build an RTL HTML page and print it to PDF with a browser engine (Chrome headless, WeasyPrint), which shapes Arabic correctly.

If ReportLab is unavoidable: reshape with `arabic_reshaper.reshape(text)` then `bidi.algorithm.get_display(...)`, and use a font that contains Arabic (e.g. Noto Naskh Arabic, DejaVu Sans) — test the output visually.

## Markdown files (.md)

Markdown has no direction setting; how it looks depends on the viewer. Apply the Part A writing rules and run `bidi_check.py --fix`. When the user needs guaranteed RTL layout, deliver HTML or .docx instead.

## Checking the result

```bash
soffice --headless --convert-to pdf out.docx
pdftoppm -png -r 70 -f 1 -l 1 out.pdf page   # then look at page-1.png
```

The test file must show: Arabic right-aligned, numbers/bullets on the right, table columns from the right, sentence-final periods at the left end, English terms in reading order mid-line, English-only paragraphs still left-to-right.
