#!/usr/bin/env python3
"""UserPromptSubmit + PostToolUse(AskUserQuestion) hook for the Arabic RTL plugin.

- When the user's message contains Arabic, reminds Claude of the RTL writing rules.
- When the user picks an answer to the plugin's "fix old content?" offer, records it, so the
  offer is not shown again in that chat / folder.
Prints nothing for non-Arabic messages, and never fails the prompt.
"""
import json
import os
import re
import sys

ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "skills", "arabic-rtl", "scripts"))

CHAT_YES = {"الردود والملفات", "الردود بس", "الملفات بس", "أيوه، ظبّط الردود", "أيوه، ظبّط الملفات"}
CHAT_NO = {"لا، سيبها"}
FOLDER_YES = {"أيوه، صلّحهم"}
FOLDER_NO = {"لا، سيب الفولدر"}
YES_ANY = {"أيوه", "ايوه", "اه", "آه", "أه", "نعم", "تمام", "موافق", "اوك", "ok", "yes", "أيوه ظبطهم", "ظبطهم", "صلحهم"}
NO_ANY = {"لا", "لأ", "لا شكرا", "لا شكرًا", "no", "سيبهم", "مش عاوز"}


def normalize(t):
    return re.sub(r"[\s‏‎«»\"'.]+", " ", t).strip()


def decide(text, yes, no, typed):
    """Return 'done', 'declined' or None for one answer text.

    A typed message may answer a combined question, so any yes/no option counts for every pending offer;
    a button pick counts only for its own offer.
    """
    p = normalize(text)
    all_yes = {normalize(x) for x in CHAT_YES | FOLDER_YES} | YES_ANY
    all_no = {normalize(x) for x in CHAT_NO | FOLDER_NO} | NO_ANY
    if p in {normalize(x) for x in yes} or (typed and (p in all_yes or p.lower() in all_yes)):
        return "done"
    if p in {normalize(x) for x in no} or (typed and (p in all_no or p.lower() in all_no)):
        return "declined"
    return None


def record(data, answers, typed=False):
    """answers: list of answer strings (a typed prompt, or the choices picked in AskUserQuestion)."""
    try:
        import rtl_state
    except Exception:
        return
    st = rtl_state.load()
    session = data.get("session_id") or ""
    folder = os.path.abspath(data.get("cwd") or os.getcwd())
    changed = False
    for ans in answers:
        if st.get("sessions", {}).get(session) == "offered":
            d = decide(ans, CHAT_YES, CHAT_NO, typed)
            if d:
                st["sessions"][session], changed = d, True
        if st.get("folders", {}).get(folder) == "offered":
            d = decide(ans, FOLDER_YES, FOLDER_NO, typed)
            if d:
                st["folders"][folder], changed = d, True
    if changed:
        rtl_state.save(st)


def picked_answers(resp):
    """Collect answer strings from an AskUserQuestion tool response, whatever its shape."""
    out = []
    if isinstance(resp, dict):
        for k, v in resp.items():
            if k in ("answers",) and isinstance(v, dict):
                out += [str(x) for x in v.values()]
            else:
                out += picked_answers(v)
    elif isinstance(resp, list):
        for v in resp:
            out += picked_answers(v)
    elif isinstance(resp, str):
        known = CHAT_YES | CHAT_NO | FOLDER_YES | FOLDER_NO
        out += [k for k in known if k in resp]
    return out


try:
    data = json.load(sys.stdin)
    prompt = data.get("prompt", "") if isinstance(data, dict) else ""
except Exception:
    sys.exit(0)

if data.get("hook_event_name") == "PostToolUse":
    try:
        record(data, picked_answers(data.get("tool_response")) + picked_answers(data.get("tool_input", {}).get("answers", {})))
    except Exception:
        pass
    sys.exit(0)

try:
    record(data, [prompt], typed=True)
except Exception:
    pass

if ARABIC.search(prompt):
    print(
        "Arabic RTL: if you reply or write files in Arabic, follow the arabic-rtl rules — every paragraph, "
        "bullet, heading and table cell starts with an Arabic word (Arabic noun before English names, e.g. "
        "شركة PCBWay); no comma-separated English terms; file names, links and code on their own line; "
        "ranges as 'من X إلى Y'; Arabic labels. For Arabic .docx/.xlsx/.pptx/.html/.pdf, load the arabic-rtl "
        "skill and set right-to-left layout."
    )
sys.exit(0)
