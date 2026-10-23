# Privacy — Arabic RTL plugin

Last updated: 23 October 2026

The Arabic RTL plugin runs entirely inside your Claude session. It has no server, makes no network requests, and sends no data to the author or to any third party.

## What it reads

- **Your current chat's transcript** (Cowork and Claude Code only, when a chat is reopened): to find earlier Arabic replies whose text would display scrambled, and paths of files mentioned in the chat. The transcript is read on your machine or in your Claude session and is not copied or sent anywhere.
- **File names and text direction settings of Office and HTML files** in the working folder (up to 3 levels deep, 300 files): to find Arabic files missing right-to-left layout.
- **Your message text**, only to check whether it contains Arabic and whether it answers the plugin's offer.

## What it stores

One local file, `~/.claude/arabic-rtl/state.json`, containing chat IDs and folder paths with your answer to the fix offer ("offered", "done" or "declined"), so the offer isn't repeated. It stores no message content. Delete the file, or run `rtl_state.py reset`, to remove it.

## What it changes

Nothing without your yes. When you agree to fix files, it writes new copies named `NAME_RTL.ext` next to the originals; originals are never modified or deleted.

## Contact

Open an issue at https://github.com/mahmoudaboualnaga/arabic-rtl/issues
