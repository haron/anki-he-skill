#!/usr/bin/env python3
"""Render cards in headless Chromium and check they fit the screen (no scrolling).

python3 tools/check_cards.py              # 4 longest cards of every used note type
python3 tools/check_cards.py NID NID ...  # specific notes, also saves screenshots
Viewports: phone 360x640, e-reader 600x800 at 1.6x font, desktop 1000x700; plus an
AnkiDroid-class pass that checks every text colour is pure black. Needs Node + Playwright
(preinstalled in the cloud container). Screenshots go to DATA/work/render/.
"""

import json
import subprocess
import sys
from pathlib import Path

from anki.collection import Collection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import COL_PATH, SKILL, WORK

OUT = WORK / "render"
OUT.mkdir(parents=True, exist_ok=True)
col = Collection(str(COL_PATH))
cards = []


def add(c):
    r = c.render_output()
    for side, html in (("q", r.question_text), ("a", r.answer_text)):
        cards.append({"name": f"{c.note_type()['name']}-{c.nid}-{side}", "css": r.css, "html": html, "ord": c.ord})


if len(sys.argv) > 1:
    for nid in sys.argv[1:]:
        for c in col.get_note(int(nid)).cards():
            add(c)
else:
    for nt in col.models.all():
        if col.models.use_count(nt):
            cs = [col.get_card(i) for i in col.find_cards(f'note:"{nt["name"]}"')]
            for c in sorted(cs, key=lambda c: -len(c.answer()))[:4]:
                add(c)
col.close()
(OUT / "cards.json").write_text(json.dumps(cards, ensure_ascii=False))
shots = "1" if len(sys.argv) > 1 else "0"
sys.exit(subprocess.call(["node", str(SKILL / "tools/check_cards.js"), str(OUT / "cards.json"), str(OUT), shots], cwd=OUT))
