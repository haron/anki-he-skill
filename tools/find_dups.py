#!/usr/bin/env python3
"""Duplicate candidates for manual review (run after `ankisync.py pull` + `anki_he.py dump`).

Pairs printed:
  [same-root+gloss]  same consonant skeleton (ו/י, prefixes, trailing prepositions ignored)
                     AND overlapping Russian gloss words
  [same-gloss]       identical first Russian meaning, different skeleton (usually synonyms)
  [legacy]           single-word Basic_* note matching a Hebrew+IPA+RU note
A shared skeleton is not proof (רָשׁוּם vs רִשּׁוּם) — always check by eye.
"""

import collections
import html
import itertools
import json
import re
import sys
from pathlib import Path

from anki.collection import Collection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import COL_PATH, DUMP, GLOSS, MODEL

col = Collection(str(COL_PATH))
susp = {nid for (nid,) in col.db.all("select distinct nid from cards where queue=-1")}
col.close()
notes = [n for n in json.loads(DUMP.read_text()) if n["model"] != "Hebrew v6" and n["id"] not in susp]
t = lambda s: html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()
sk = lambda s: re.sub(r"[֑-ׇ\"'?!.,;:()\-־–—/=]", " ", t(s)).split()
hol = lambda w: re.sub("[וי]", "", w)
PREP = {"ל", "ב", "על", "את", "מ", "עם", "אל", "מן", "של"}


def key(n):
    ws = [hol(w) for w in sk(next(iter(n["f"].values())))]
    while ws and ws[-1] in PREP:
        ws = ws[:-1]
    return "".join(re.sub(r"^(ה|ל|ב|מ|כ|ו|ש)(?=..)", "", w) for w in ws)


def toks(n):
    g = re.sub(r"\(.*?\)", "", t(n["f"].get(GLOSS, "")).lower())
    return {w[:5] for w in re.findall(r"[а-яё]{4,}", g)} - {"котор", "очень", "также", "чтобы"}


he = [n for n in notes if n["model"] == MODEL]
pairs = []
by = collections.defaultdict(list)
for n in he:
    by[key(n)].append(n)
for ns in by.values():
    pairs += [("same-root+gloss", a, b) for a, b in itertools.combinations(ns, 2) if toks(a) & toks(b)]
fg = collections.defaultdict(list)
for n in he:
    f = re.split(r"[,;/]", re.sub(r"\(.*?\)", "", t(n["f"][GLOSS]).lower()))[0].strip()
    if len(f) > 2:
        fg[f].append(n)
for ns in fg.values():
    pairs += [("same-gloss", a, b) for a, b in itertools.combinations(ns, 2) if key(a) != key(b)]
idx = collections.defaultdict(list)
for n in he:
    ws = sk(n["f"]["Hebrew"])
    if len(ws) == 1:
        idx[hol(ws[0])].append(n)
for l in (n for n in notes if n["model"].startswith("Basic")):
    ws = sk(l["f"]["Hebrew"])
    if len(ws) == 1:
        pairs += [("legacy", l, c) for c in idx.get(hol(ws[0]), [])]
fmt = lambda n: f"{n['id']} {n['model'][:6]} | " + " | ".join(t(v)[:38] for v in list(n["f"].values())[:3])
for i, (k, a, b) in enumerate(pairs):
    print(f"{i} [{k}]\n   {fmt(a)}\n   {fmt(b)}")
