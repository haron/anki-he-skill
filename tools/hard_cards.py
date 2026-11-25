#!/usr/bin/env python3
"""Hebrew notes that still miss parts of the card standard (see SKILL.md).

python3 tools/hard_cards.py [N]          hard notes only, hardest first (default N=60)
python3 tools/hard_cards.py --all [N]    every note: hard ones first, then the rest in the
                                         order the user will meet them (reviews by due date,
                                         then new cards by queue position), places last
add --json for machine-readable output.

Hard = lapses >= 4, or any «Again» since 2026-11-15 (honest grading started), or lapse rate
>= 15% with >= 2 lapses. Missing flags:
  N no nikud · E no example sentence (not required for `place` notes) · M no 💡 hint (hard notes only)
  F several meanings on the front (; or /)
Abbreviations (ט.ל.ח, מוצ״ש) are not flagged for nikud.
"""

import html
import json
import re
import sys
import time
from pathlib import Path

from anki.collection import Collection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import COL_PATH, GLOSS, MODEL

SINCE = time.mktime((2026, 11, 15, 4, 0, 0, 0, 0, -1)) * 1000


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def main():
    args = sys.argv[1:]
    as_json, everything = "--json" in args, "--all" in args
    args = [a for a in args if not a.startswith("--")]
    limit = int(args[0]) if args else 60
    col = Collection(str(COL_PATH))
    today = col.sched.today
    rows = []
    try:
        for nid in col.find_notes(f'note:"{MODEL}" -is:suspended'):
            n = col.get_note(nid)
            ids = ",".join(map(str, col.card_ids_of_note(nid)))
            reps, laps = col.db.first(f"select sum(reps), sum(lapses) from cards where id in ({ids})")
            reps, laps = reps or 0, laps or 0
            again = col.db.scalar(f"select count() from revlog where cid in ({ids}) and id > ? and ease = 1", SINCE)
            hard = bool(reps) and (laps >= 4 or again or (laps >= 2 and laps / reps >= 0.15))
            if not (hard or everything):
                continue
            he, gloss, ex = text(n["Hebrew"]), text(n[GLOSS]), n["Example"]
            sentence = re.sub(r"<span[^>]*>.*?</span>", "", ex)
            abbrev = bool(re.search(r'[.״"]', he))
            checks = [
                ("N", abbrev or re.search("[ְ-ּ]", he)),
                ("E", "place" in n.tags or re.search("[֐-׿]", sentence)),  # places are HE→RU only
                ("M", not hard or "💡" in ex),
                ("F", not re.search(r";|\s/\s|[а-я]/[а-я]{3}", gloss) or gloss == "и/или"),
            ]
            missing = "".join(flag for flag, ok in checks if not ok)
            if not missing:
                continue
            if hard:
                order = (0, -(laps / reps * 2 + again * 0.5 + laps * 0.15))
            elif "place" in n.tags:
                order = (3, 0)
            else:
                active = col.db.list(f"select due from cards where id in ({ids}) and queue in (1,2,3)")
                if active:  # review/learning: soonest first (learning due is a timestamp → treat as now)
                    order = (1, min(d - today if d < 10**6 else 0 for d in active))
                else:  # new: queue position
                    order = (2, col.db.scalar(f"select min(due) from cards where id in ({ids})") or 0)
            rows.append(
                {
                    "id": nid,
                    "he": he,
                    "gloss": gloss,
                    "ipa": text(n["IPA transcription"]),
                    "lapses": laps,
                    "reps": reps,
                    "again": again,
                    "missing": missing,
                    "order": order,
                }
            )
    finally:
        col.close()
    rows.sort(key=lambda r: r["order"])
    total = len(rows)
    rows = rows[:limit]
    if as_json:
        print(json.dumps(rows, ensure_ascii=False))
        return
    for r in rows:
        print(f"{r['id']} {r['missing']:4} L{r['lapses']:>2}/{r['reps']:<3} A{r['again']} {r['he']} = {r['gloss'][:45]}")
    print(f"({len(rows)} of {total})", file=sys.stderr)


if __name__ == "__main__":
    main()
