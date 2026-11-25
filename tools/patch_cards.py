#!/usr/bin/env python3
"""Turn a compact patch file into an `anki_he.py apply` file, keeping the Example layout.

python3 tools/patch_cards.py PATCH.json OUT.json

PATCH.json: {"<note id>": {"he": …, "ipa": …, "gloss": …, "ex": "<Hebrew sentence>",
             "tr": "<Russian translation>", "hint": "<💡 text>"}, …}  — every key optional.
Example is rebuilt as: sentence + translation, then the 💡 hint line, then any existing
verb-link (← / →) lines. Missing keys keep what the note already has; "hint" replaces
the old hint (a failed mnemonic is replaced, never appended).
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DUMP, GLOSS

GREY = '<span dir=ltr style="color:#999">{}</span>'
HINT = '<span dir=ltr style="color:#b58a6a">💡 {}</span>'
HINT_RX = re.compile(r'<span dir=ltr style="color:#b58a6a">💡 .*?</span>')
LINK_RX = re.compile(r'<span dir=ltr style="color:#6a8fb5">.*?</span>')


def rebuild(old, p):
    links = LINK_RX.findall(old)
    old_hint = HINT_RX.findall(old)
    sentence = re.sub(r"(<br>)+$", "", LINK_RX.sub("", HINT_RX.sub("", old)).strip())
    if "ex" in p:
        sentence = f"{p['ex']}<br>{GREY.format(p['tr'])}"
    hint = [HINT.format(p["hint"])] if "hint" in p else old_hint[:1]
    return "<br>".join(x for x in [sentence, *hint, *links] if x)


def main():
    patch = json.loads(Path(sys.argv[1]).read_text())
    notes = {str(n["id"]): n for n in json.loads(DUMP.read_text())}
    upd = {}
    for nid, p in patch.items():
        f = notes[nid]["f"]
        out = {"Example": rebuild(f.get("Example", ""), p)}
        for key, field in (("he", "Hebrew"), ("ipa", "IPA transcription"), ("gloss", GLOSS)):
            if key in p:
                out[field] = p[key]
        if f.get("Notes") or f.get("Root+Binyan"):
            out["Notes"] = out["Root+Binyan"] = ""
        upd[nid] = out
    Path(sys.argv[2]).write_text(json.dumps({"update": upd}, ensure_ascii=False))
    print(f"{len(upd)} notes")


if __name__ == "__main__":
    main()
