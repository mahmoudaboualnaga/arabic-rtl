# Arabic RTL

Makes Arabic content read correctly, right to left — automatically, from the moment it's installed.

## Install

In Claude Code:

```
/plugin marketplace add mahmoudaboualnaga/arabic-rtl
/plugin install arabic-rtl@arabic-rtl
```

On Claude Code 2.1.275 or later, one step:

```
/plugin install arabic-rtl --marketplace mahmoudaboualnaga/arabic-rtl
```

In the Claude app (web, desktop or mobile): go to **Customize → Plugins → Add → Add marketplace**, enter `mahmoudaboualnaga/arabic-rtl`, then install **Arabic RTL**.

## What it does

- **Chat replies and Claude Docs** — Claude writes Arabic so it doesn't scramble: every paragraph and bullet starts with an Arabic word, English names get an Arabic word before them, file names and links go on their own line, ranges are written in words, and invisible right-to-left marks are added where needed.
- **Files** — Word, Excel, PowerPoint, HTML and PDF outputs get real right-to-left layout: text aligned right, bullets and numbers on the right, tables and sheets starting from the right, proper Arabic fonts and sizes.
- **Fixing your files** — upload an Arabic Word, Excel or PowerPoint file whose layout is wrong and ask Claude to fix the direction.

## Automatic, no setup

Once installed, the plugin turns on by itself in every session:

- At the start of each session it gives Claude the Arabic writing rules.
- Every message that contains Arabic gets a short reminder of those rules.
- Arabic files are built with right-to-left layout through the `arabic-rtl` skill.

Nobody needs to type a command or mention the plugin.

## Old chats and folders — the user decides

- **Reopening an old chat**: if earlier replies or files in it have scrambled Arabic, Claude asks once whether to fix the replies, the files, both, or nothing. Old messages can't be edited in place, so fixed replies are posted as corrected versions in the chat, and fixed files are sent as new copies.
- **Working in a folder**: if it holds Arabic Word, Excel, PowerPoint or HTML files whose layout isn't right-to-left, Claude asks once whether to make fixed copies (saved as `NAME_RTL.ext` next to each original).
- Nothing is changed without a yes, originals are never overwritten, and once the user answers, that chat or folder isn't asked about again.
- Run it any time by asking — "صلّح العربي في الشات ده" or "ظبط ملفات الفولدر ده" — through the `fix-chat` and `fix-folder` skills.

## Where it works

| Surface | Writing rules and file fixing (skills) | Automatic rules at start, old-chat and folder offers (hooks) |
|---|---|---|
| Claude Code | Yes | Yes |
| Cowork (desktop, web and mobile) | Yes | Yes |
| Chat on claude.ai (web, desktop Chat tab) | Yes | No — chat doesn't run plugin hooks; the skill offers to fix earlier replies when it loads instead |

Plugins need a paid Claude plan. Installed plugins are saved to your account, so they follow you across devices.

## What it runs and stores

- **No network access.** Nothing the plugin runs sends data anywhere.
- **At session start** (Cowork, Claude Code): reads the current chat's transcript to find earlier Arabic replies and file paths that need fixing, and lists Office/HTML files in the working folder (up to 3 levels deep, 300 files, a few seconds) to check their text direction. It changes nothing.
- **On each message**: checks whether the message contains Arabic, and whether it answers the plugin's offer.
- **Stores one small file**, `~/.claude/arabic-rtl/state.json`, holding chat IDs and folder paths with the answer given ("offered", "done", "declined"), so the offer isn't repeated. Delete it, or run `rtl_state.py reset`, to forget all answers.
- **Fixing files** writes new `NAME_RTL` copies next to the originals; originals are never modified or deleted.

## Skill

| Skill | Use it when |
|---|---|
| `arabic-rtl` | Any reply, document, deck, sheet or page in Arabic or mixed Arabic/English, or when Arabic text looks mixed up. |
| `fix-chat` | Fixing the Arabic replies and files of an existing chat, after the user agrees. |
| `fix-folder` | Making right-to-left copies of the Arabic files in a folder, after the user agrees. |

## Scripts (used by Claude)

- `scripts/bidi_check.py` — checks Arabic text for lines that will scramble and can fix them.
- `scripts/rtl_scan.py` — finds Arabic replies and files that need fixing in a chat or a folder.
- `scripts/fix_files.py` — makes `NAME_RTL` copies of Arabic files, leaving originals untouched.
- `scripts/rtl_state.py` — remembers each chat's and folder's answer so the offer isn't repeated (stored in `~/.claude/arabic-rtl/state.json`).
- `hooks/` — the start-of-session rules and checks, the per-message reminder, and recording the user's answer. They need Python 3; without it, the writing rules still load.
- `scripts/make_rtl.py` — sets right-to-left on the Arabic parts of a .docx, .xlsx, .pptx or .html file. Needs Python 3 with `lxml`.

## Limits

Chat and Claude Docs don't offer a direction setting, so there the fix is how the text is written. For guaranteed right-to-left layout, ask for a Word file or an HTML page.

## License

MIT — see [LICENSE](LICENSE).
