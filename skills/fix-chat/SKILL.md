---
name: fix-chat
description: Fixes scrambled Arabic in an existing chat — re-posts corrected versions of earlier Arabic replies and makes right-to-left copies of the Arabic files in it. Use when the user agrees to the plugin's offer in a reopened chat, or says "ظبط الردود اللي فوق", "صلّح العربي في الشات ده", "fix the Arabic in this chat", "اعدل الردود القديمة", or names a past chat whose Arabic is mixed up.
---

# Fix an old chat

Old messages cannot be edited in place. Fixing a reply means posting a corrected version of it in the chat. Fixing a file means making a right-to-left copy and sending it. Say this in one short line before starting if the user hasn't heard it yet.

Do nothing until the user has said which parts to fix (replies, files, or both). If they haven't chosen, ask once with AskUserQuestion: «الردود والملفات» / «الردود بس» / «الملفات بس» / «لا، سيبها».

## 1. Find what needs fixing

- **This chat**: the earlier replies are in context. For a long chat, scan the transcript too:
  ```bash
  python3 ${CLAUDE_SKILL_DIR}/../arabic-rtl/scripts/rtl_scan.py --transcript "<transcript path>"
  ```
  The session-start notice lists the flagged replies and files when the chat was reopened; use that list when present.
- **A past chat the user names**: find it with the past-chats search tool, read the Arabic replies the user means (the last one by default), and fix them here in this chat.

## 2. Replies

For each flagged reply, newest first — up to three, then ask whether to continue with the rest:

1. Rewrite it following the `arabic-rtl` skill's Part A rules. Keep the same content, numbers, links and order; change only wording and layout needed for correct direction. Add no new facts.
2. Save the draft to a scratch file and run `bidi_check.py` on it until it reports no problems. If running scripts isn't allowed here, check each block by hand against the rules instead; don't stop to ask for permission just for the check.
3. Post it under a one-line Arabic label: `**النسخة المظبوطة من الرد رقم N:**` (or `**النسخة المظبوطة من ردك عن ...:**`).

If a reply is very long (a full report), offer to put the corrected version in a doc or a Word file instead of a long chat message.

## 3. Files

- **Word / Excel / PowerPoint / HTML** files from this chat (made by Claude or attached by the user):
  ```bash
  python3 ${CLAUDE_SKILL_DIR}/../arabic-rtl/scripts/fix_files.py "<file1>" "<file2>"
  ```
  This writes `NAME_RTL.ext` next to each original and never changes the original. Render a page of one result to check it (see the `arabic-rtl` skill), then send the fixed copies to the user.
- **Files the chat only links to but that are no longer here**: ask the user to attach them.
- **Claude Docs documents** in the chat: Docs has no direction setting. With the user's yes, edit the doc in place: rewrite each Arabic block that opens with an English word, ends a block with an English term, or lists English terms with commas, following Part A. Change wording only; keep every fact, table and link.
- **PDF**: rebuild it from a fixed .docx or HTML when the source is available; otherwise say it can't be fixed directly and offer to rebuild it.

## 4. Finish

Tell the user in one or two lines what was fixed (number of replies, list of files). Don't mention saving state or any internal step.

When the user picked one of the offer's options, the plugin already recorded the answer. Only when they answered in their own words, record it so the offer isn't repeated (`done` after fixing, `decline` if they refused):

```bash
python3 ${CLAUDE_SKILL_DIR}/../arabic-rtl/scripts/rtl_state.py done --session "<session id>"
```
