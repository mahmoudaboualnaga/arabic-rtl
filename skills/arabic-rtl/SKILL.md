---
name: arabic-rtl
description: Writes Arabic (Egyptian or MSA) so it renders right-to-left without scrambled word order, and sets real RTL layout in Word, Excel, PowerPoint, HTML and PDF files. Use for every reply written in Arabic, even short ones, and whenever a reply, doc, table, report, slide deck, spreadsheet or web page is written in Arabic or mixes Arabic with English terms, numbers, file names or links — and when the user says the Arabic is mixed up, reversed, misaligned, "الكلام متداخل", "المحاذاة غلط", "العربي باظ", "اتجاه النص", or asks for RTL / right-to-left / "من اليمين للشمال".
---

# Arabic RTL

Arabic breaks in two different ways, and each has its own fix:

1. **Chat replies, Claude Docs, Markdown** — Claude cannot set the text direction. The viewer guesses each paragraph's direction from its **first strong letter** (Unicode bidi). If a paragraph or list item opens with an English word, a number, a link or a symbol, the whole block is laid out left-to-right: words jump around, the period lands on the wrong side, lines wrap in the wrong order. The fix is in how the text is written (Part A).
2. **Files Claude builds** (.docx, .xlsx, .pptx, .html, .pdf) — direction is a real setting. Set it explicitly (Part B), then run the fixer script as a safety net.

## Part A — Writing Arabic that renders correctly (chat, Docs, Markdown)

Apply every rule to every block: paragraph, bullet, numbered item, heading, table cell, bold lead-in, caption.

1. **Open every block with an Arabic word.** Never with a Latin word, link, code span, file name or a bolded English name. (Digits and symbols don't decide direction by themselves, but `20 PCB ...` does — the first *letter* counts.)
   - Bad: `**PCBWay باختصار:** هي مصنّع...` — the block goes LTR and scrambles.
   - Good: `**باختصار، شركة PCBWay** هي مصنّع...`
   - Bad: `1. CNC والطباعة ثلاثية الأبعاد` · Good: `1. خدمات CNC والطباعة ثلاثية الأبعاد`
   - Bad: `- 3D printing بأسعار منافسة` · Good: `- طباعة ثلاثية الأبعاد (3D printing) بأسعار منافسة`
2. **Put an Arabic head noun before every English term**: `منصة Fabconnect`، `شركة PCBWay`، `ماكينات CNC`، `ملف Excel`، `برنامج SolidWorks`. Prefer this over gluing `الـ` to Latin letters (`الـCNC`); if `الـ` is needed, leave a space: `الـ CNC`.
3. **Never end a sentence or block with an English term or a number followed by punctuation** (`... في الـ Idea Vault.`) — the period jumps to the wrong side. Reorder so the sentence ends in Arabic (`... في سجل الأفكار Idea Vault الخاص بك.`), or insert U+200F (RLM) right after the Latin term, before the punctuation.
4. **Keep English chunks short (1–3 words) and never list several English terms with commas between them.** `PCB، CNC، 3D` reorders badly. Write `الـ PCB والـ CNC والطباعة ثلاثية الأبعاد` — Arabic `و` between them.
5. **Move long English out of the sentence.** File names, URLs, paths, code, formulas and English sentences go on their own line in backticks or a code block, under an Arabic label line:
   ```
   الملف المرفق:
   `Industrial_Marketplace_Competitor_Tracker_and_Model.xlsx`
   ```
   Links: put the Arabic words as the link text — `[النسخة العربية](url)` — never a bare URL inside an Arabic sentence.
6. **Numbers**: write ranges in words — `من 15 إلى 25%` not `15–25%`; keep the unit in Arabic after the number — `348 ألف جنيه`، `6 أسابيع`; avoid `+`/`-` signs and `x` for multiplication inside Arabic sentences (`ضعفين`، `زيادة 20%`). Use one digit style throughout (Western 0–9 unless the user uses ٠–٩).
7. **Parentheses and quotes** with English inside must sit mid-sentence with Arabic after them; never let `(DFM)` or `"..."` close a block.
8. **Headings and bold labels**: the label itself is Arabic — `**الافتراض الأخطر:**`، not `**Key risk:**`. Put an English equivalent after it if needed.
9. **Tables**: first column Arabic, every cell starts with an Arabic word (or is a bare number alone in the cell). Put English names in a later column or after an Arabic word.
10. **Invisible safety net**: when a block must start with Latin or a digit (a product code, a quote), prefix it with U+200F (RLM, `‏`). In Markdown put it after the list marker: `- ‏PCBWay ...`. It is invisible and forces the block right-to-left.
11. **Claude Docs**: paragraphs follow the same first-letter rule. Bulleted and numbered lists can still lay out left-to-right there, so for Arabic Docs prefer short paragraphs that start with a bold Arabic label, or a table, over long lists; when a list is needed, start each item with RLM and an Arabic word. Docs has no direction setting — when the user needs guaranteed RTL layout, offer a Word file or an HTML page (Part B).

**Before sending any Arabic reply or doc**, scan each block: does it start with an Arabic letter? does any sentence end with Latin/digits + punctuation? are there comma-separated English terms? Fix those before sending. For long text, run the linter on a draft saved to a file:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/bidi_check.py draft.md          # report problems
python3 ${CLAUDE_SKILL_DIR}/scripts/bidi_check.py draft.md --fix    # insert RLM marks where needed
```

The linter is a backstop; rewording with rules 1–9 reads better than RLM marks.

## Part B — Files with real right-to-left layout

Build the file with direction set from the start, following the format's section in `references/file-formats.md` (Word, Excel, PowerPoint, HTML, PDF, plus Arabic fonts). The essentials:

| Format | Must set |
|---|---|
| Word .docx | paragraph `bidi`, run `rtl`, table `bidiVisual`, section `bidi`, complex-script font (`w:cs`) and sizes (`szCs`, `bCs`) |
| Excel .xlsx | sheet view `rightToLeft`, cell alignment right with reading order RTL |
| PowerPoint .pptx | paragraph `rtl="1"` + `algn="r"`, run `lang="ar-EG"`, table `rtl="1"` |
| HTML | `<html dir="rtl" lang="ar">`, `unicode-bidi: plaintext` on text blocks, `<bdi>` around English terms, an Arabic web font |
| PDF | never draw Arabic glyph-by-glyph (ReportLab, FPDF without shaping): build HTML or .docx with RTL, then convert to PDF |

Then run the fixer on every Arabic .docx / .xlsx / .pptx / .html before delivering it:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/make_rtl.py input.docx output.docx
python3 ${CLAUDE_SKILL_DIR}/scripts/make_rtl.py input.docx output.docx --font "Arial"
```

It sets RTL only on paragraphs, runs, tables, sheets and slides that contain Arabic, so English-only parts stay left-to-right. It also fixes Arabic files the user uploads ("الملف ده العربي فيه مقلوب"): run it on a copy and send the result back in the same format.

**Check the result visually before delivering.** Convert to PDF and look at a page:

```bash
soffice --headless --convert-to pdf output.docx && pdftoppm -png -r 70 -f 1 -l 1 output.pdf page
```

Look for: text right-aligned, list bullets and numbers on the right, table columns starting from the right, periods at the left end of lines, English terms in the middle of lines in reading order.

## Old chats, attached files and folders

Never change existing content without the user's yes. When an old chat is reopened, when the user attaches Arabic files, or when a folder with Arabic files is connected, and their Arabic is scrambled or their layout isn't right-to-left, ask once whether to fix them. The `fix-chat` skill handles replies and files in a chat; the `fix-folder` skill handles folders. Both make corrected copies and leave originals untouched. Check any file quickly with:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/rtl_scan.py --folder "<folder>"
```

### In plain chat

The plugin's automatic checks (session-start rules, the old-chat and folder offers) run in Cowork and Claude Code. In plain chat on claude.ai only this skill loads. So when this skill loads in a chat whose earlier Arabic replies break the Part A rules, offer once, at the end of your reply, to post corrected versions of them — and follow the `fix-chat` skill if the user agrees.

## Requirements

The file scripts need Python 3 with `lxml` (`pip install lxml` if the import fails). `bidi_check.py` needs only Python 3.

## When the content is mostly English

Apply Part A only to the Arabic blocks. A reply that is mainly English with a few Arabic words needs no changes.

## Reference files

- `references/file-formats.md` — exact settings and code (python-docx, docx-js, openpyxl, python-pptx, HTML/CSS, PDF route, fonts)
- `references/bidi-explained.md` — why the scrambling happens, the Unicode marks (RLM, LRM, isolates), and before/after examples from real broken replies
