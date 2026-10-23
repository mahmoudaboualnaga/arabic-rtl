---
name: fix-folder
description: Finds Arabic Word, Excel, PowerPoint and HTML files in a folder whose right-to-left layout is wrong and, after the user agrees, saves corrected RTL copies next to the originals. Use when a folder with Arabic files is connected or opened and the user agrees to the plugin's offer, or when the user says "صلّح ملفات الفولدر", "ظبط اتجاه الملفات العربي اللي في الفولدر", "fix the Arabic files in this folder", or "make these files right-to-left".
---

# Fix a folder of Arabic files

Originals are never changed. Each fixed file is saved as `NAME_RTL.ext` next to it.

## 1. Scan

Find the folder: the working folder, a folder the user connected, or one they name.

- **Folder on this machine** (working folder, or the user's computer through a shell on it):
  ```bash
  python3 ${CLAUDE_SKILL_DIR}/../arabic-rtl/scripts/rtl_scan.py --folder "<folder>" --depth 3
  ```
- **Folder on the user's computer reachable only through file-transfer tools** (no shell there): list it, bring the .docx / .xlsx / .pptx / .html files into the workspace, scan them here, and write the fixed copies back to the same folder.

## 2. Ask

If the scan finds nothing, say so in one line and stop. Otherwise tell the user how many files need fixing and ask once (AskUserQuestion when available): «أيوه، صلّحهم» / «وريني القائمة الأول» / «لا، سيب الفولدر». For «وريني القائمة الأول», list the files (name and folder), then ask again.

Picking an option is recorded by the plugin automatically. If they refuse in their own words, record it so the folder isn't offered again:
```bash
python3 ${CLAUDE_SKILL_DIR}/../arabic-rtl/scripts/rtl_state.py decline --folder "<folder>"
```

## 3. Fix

```bash
python3 ${CLAUDE_SKILL_DIR}/../arabic-rtl/scripts/fix_files.py --folder "<folder>" --depth 3
```

Add `--font "Arial"` (or the user's preferred Arabic font) when they ask for a font. Use `--outdir "<folder>/RTL"` when the user wants the copies in one separate folder.

Check one fixed file of each type visually (render a page, as the `arabic-rtl` skill describes) before reporting.

## 4. Report

One or two lines: how many files were fixed, where the copies are, any that were skipped and why (password-protected, damaged). Don't list every file unless there are only a few.
