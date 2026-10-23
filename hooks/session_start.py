#!/usr/bin/env python3
"""SessionStart hook for the Arabic RTL plugin.

1. Always gives Claude the Arabic writing rules.
2. When an old chat is reopened (source == "resume"), scans its earlier replies and files; if Arabic
   there would render scrambled, tells Claude to ask the user whether to fix them.
3. Scans the working folder for Arabic Office/HTML files missing right-to-left layout and, if any,
   tells Claude to offer fixing them.
Nothing is ever changed without the user's yes. Errors never block the session.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "skills", "arabic-rtl", "scripts")
sys.path.insert(0, SCRIPTS)


def rules():
    try:
        with open(os.path.join(HERE, "arabic-rtl-context.md"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "Arabic RTL plugin is active: start every Arabic block with an Arabic word."


def mark(group, key):
    """Remember that the offer was shown, so the user's answer can be recorded."""
    try:
        import rtl_state
        st = rtl_state.load()
        st.setdefault(group, {})[key] = "offered"
        rtl_state.save(st)
    except Exception:
        pass


def state():
    try:
        import rtl_state
        return rtl_state.load()
    except Exception:
        return {"sessions": {}, "folders": {}}


def options(n_replies, n_files):
    if n_replies and n_files:
        opts = ["الردود والملفات", "الردود بس", "الملفات بس"]
    elif n_replies:
        opts = ["أيوه، ظبّط الردود"]
    else:
        opts = ["أيوه، ظبّط الملفات"]
    return " / ".join(f"«{o}»" for o in opts + ["لا، سيبها"])


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    out = [rules()]
    try:
        import rtl_scan
    except Exception:
        print(out[0])
        return
    st = state()
    session = data.get("session_id") or ""
    source = data.get("source") or ""
    cwd = data.get("cwd") or os.getcwd()
    py = f'python3 "{SCRIPTS}'

    # ---- reopened chat
    transcript = data.get("transcript_path")
    if source == "resume" and transcript and os.path.isfile(transcript) and st.get("sessions", {}).get(session) in (None, "offered"):
        try:
            chat = rtl_scan.scan_transcript(transcript, cwd)
        except Exception:
            chat = {"replies": [], "files": []}
        n_r, n_f = len(chat["replies"]), len(chat["files"])
        if n_r or n_f:
            lines = [
                "",
                "ARABIC RTL — OLD CHAT CHECK (do this in your next reply):",
                f"This reopened chat has {n_r} earlier repl{'y' if n_r == 1 else 'ies'} whose Arabic will display "
                f"scrambled and {n_f} Arabic file(s) missing right-to-left layout.",
            ]
            for r in chat["replies"][:6]:
                lines.append(f"- reply #{r['reply_number']}: \"{r['starts_with']}\"")
            for f in chat["files"][:6]:
                lines.append(f"- file: {f['path']}")
            lines += [
                "First answer what the user just asked. Then, once, ask whether they want these fixed — with "
                "AskUserQuestion when available, otherwise one short question — in the user's language. Arabic "
                "wording: «لقيت في الشات ده ردود أو ملفات عربي اتجاهها مش مظبوط. تحب أظبطها؟» with the options "
                + options(n_r, n_f) + ".",
                "Never fix anything before they choose. Say plainly that old messages can't be edited in place: "
                "fixing a reply means posting a corrected version of it here.",
                "If they say yes: load the fix-chat skill and follow it for the parts they chose.",
                "Picking one of these options is recorded automatically, so the question won't come back. Only if "
                f"they decline in other words, run {py}/rtl_state.py\" decline --session {session}.",
            ]
            out.append("\n".join(lines))
            mark("sessions", session)

    # ---- working folder
    home = os.path.abspath(os.path.expanduser("~"))
    folder = os.path.abspath(cwd)
    if folder not in (home, os.sep) and st.get("folders", {}).get(folder) in (None, "offered"):
        try:
            res = rtl_scan.scan_folder(folder, depth=3, max_files=300, budget_s=4.0)
        except Exception:
            res = {"files": []}
        files = [f for f in res["files"] if not f["path"].startswith(ROOT)]
        if files:
            lines = [
                "",
                "ARABIC RTL — FOLDER CHECK (do this in your next reply, after answering the user):",
                f"The working folder {folder} has {len(files)} Arabic file(s) whose right-to-left layout is missing:",
            ]
            for f in files[:8]:
                lines.append(f"- {os.path.relpath(f['path'], folder)}")
            lines += [
                "Ask once, in the user's language (AskUserQuestion when available): «لقيت ملفات عربي في الفولدر ده "
                "اتجاهها مش مظبوط. تحب أعمل لها نسخ مظبوطة جنب الأصل؟» options «أيوه، صلّحهم» / «وريني القائمة الأول» / «لا، سيب الفولدر». Picking an option is recorded automatically.",
                f"Yes: run {py}/fix_files.py\" --folder \"{folder}\" (makes NAME_RTL copies, never touches originals), "
                "then report what was fixed.",
                f"If they answer «لا» in other words than the option, run {py}/rtl_state.py\" decline --folder \"{folder}\".",
            ]
            out.append("\n".join(lines))
            mark("folders", folder)
    if len(out) == 3:
        out.append("Both checks fired: ask them together in ONE AskUserQuestion call (two questions), not in two turns.")
    print("\n".join(out))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(rules())
    sys.exit(0)
