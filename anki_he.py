#!/usr/bin/env python3
"""hebrew-anki helpers working on the local collection (DATA/work/collection.anki2, see config.py).

Port of dotfiles/skills/hebrew-anki/anki-he; same commands, but no Anki-Connect.

anki_he.py dump              dump deck $ANKI_HE_DECK to DATA/work/he-dump.json
anki_he.py find TERM...      Hebrew TERM: skeleton/hollow match; ~REGEX: any field
anki_he.py show ID...        all fields of the given notes
anki_he.py sound WORD...     closest notes by sound: Russian-letter spelling («мугзам») vs IPA
anki_he.py dups              repeated «Русский перевод» across Hebrew+IPA+RU notes
anki_he.py apply FILE        {"add":[fields], "update":{id: fields}, "delete":[ids]}
"""

import html
import json
import re
import signal
import sys
from collections import defaultdict
from pathlib import Path

from config import COL_PATH, DATA, DECK, DUMP, GLOSS, MODEL

ROOT = DATA
MAX_HITS = 15


def open_col():
    from anki.collection import Collection

    if not COL_PATH.exists():
        sys.exit("anki_he: no local collection, run `anki-he pull` first")
    return Collection(str(COL_PATH))


def text(s):
    # unescape entities (&quot; &nbsp; …) so חו&quot;ל and חו"ל compare equal
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def skel(s):
    return re.sub(r"[֑-ׇ]", "", text(s))


def hollow(s):
    return re.sub("[וי]", "", skel(s))


def load():
    if not DUMP.exists():
        dump()
    return json.loads(DUMP.read_text())


def line(n, width=80):
    vals = [v[:width] for v in map(text, n["f"].values()) if v]
    return f"  {n['id']} {n['model']} | " + " | ".join(vals)


def dump(col=None):
    own = col is None
    col = col or open_col()
    try:
        out = []
        for nid in col.find_notes(f'deck:"{DECK}"'):
            note = col.get_note(nid)
            out.append({"id": nid, "model": note.note_type()["name"], "f": dict(note.items())})
    finally:
        if own:
            col.close()
    DUMP.write_text(json.dumps(out, ensure_ascii=False))
    print(f"{len(out)} notes -> {DUMP.relative_to(ROOT)}")


def matches(term, n):
    if term.startswith("~"):
        rx = re.compile(term[1:], re.IGNORECASE)
        return any(rx.search(text(v)) for v in n["f"].values())
    sk = skel(term)
    if len(sk.replace(" ", "")) <= 3:  # hollow and all-field matching flood on short words
        return sk in skel(next(iter(n["f"].values()), ""))
    return any(sk in skel(v) or hollow(term) in hollow(v) for v in n["f"].values())


def find(*terms):
    notes = load()
    for t in terms:
        hits = [n for n in notes if matches(t, n)]
        print(f"{t}: {len(hits)}")
        for n in hits[:MAX_HITS]:
            print(line(n))
        if len(hits) > MAX_HITS:
            print(f"  … +{len(hits) - MAX_HITS} more, narrow the term")


def show(*ids):
    by_id = {n["id"]: n for n in load()}
    for i in ids:
        print(json.dumps(by_id[int(i)], ensure_ascii=False))


def dups():
    groups = defaultdict(list)
    for n in load():
        if n["model"] == MODEL and (g := text(n["f"].get(GLOSS, "")).lower()):
            groups[g].append(n)
    for g, ns in sorted(groups.items()):
        if len(ns) > 1:
            print(f"«{g}»")
            for n in ns:
                print(line(n))


def apply(file):
    spec = json.loads(Path(file).read_text())
    col = open_col()
    errors = []
    try:
        for i, fields in spec.get("update", {}).items():
            try:
                note = col.get_note(int(i))
                for k, v in fields.items():
                    note[k] = v
                col.update_note(note)
            except Exception as e:  # noqa: BLE001
                errors.append(("update", i, str(e)))
        if spec.get("delete"):
            col.remove_notes([int(i) for i in spec["delete"]])
        model = col.models.by_name(MODEL)
        did = col.decks.id(DECK, create=False)
        for fields in spec.get("add", []):
            fields = dict(fields)
            tags = fields.pop("tags", [])
            try:
                note = col.new_note(model)
                for k, v in fields.items():
                    note[k] = v
                note.tags = tags
                col.add_note(note, did)
            except Exception as e:  # noqa: BLE001
                errors.append(("add", fields.get("Hebrew"), str(e)))
        for e in errors:
            print("ERROR", json.dumps(e, ensure_ascii=False))
        print(
            f"updated {len(spec.get('update', {}))}, deleted {len(spec.get('delete', []))}, "
            f"added {len(spec.get('add', [])) - sum(e[0] == 'add' for e in errors)}, errors {len(errors)}"
        )
        dump(col)
    finally:
        col.close()
    if errors:
        sys.exit(1)


CYR = dict(
    zip(
        "абвгдеёжзийклмнопрстуфхцчшщыэюяь",
        [
            "a",
            "b",
            "v",
            "g",
            "d",
            "e",
            "o",
            "ʒ",
            "z",
            "i",
            "j",
            "k",
            "l",
            "m",
            "n",
            "o",
            "p",
            "ʁ",
            "s",
            "t",
            "u",
            "f",
            "x",
            "ts",
            "tʃ",
            "ʃ",
            "ʃ",
            "i",
            "e",
            "ju",
            "ja",
            "",
        ],
    )
)


def flat_ipa(s):
    s = text(s).lower().replace("t͡s", "ts").replace("t͡ʃ", "tʃ").replace("d͡ʒ", "dʒ").replace("r", "ʁ").replace("h", "x")
    return re.sub(r"[ˈˌ\s.()\-–—?!,/]", "", s)


def sound(*words):
    """Voice dictation gives Hebrew as Russian letters («мугзам»): rank notes by IPA similarity."""
    from difflib import SequenceMatcher

    notes = [n for n in load() if n["f"].get("IPA transcription")]
    for w in words:
        q = flat_ipa("".join(CYR.get(ch, ch) for ch in w.lower()))
        scored = sorted(((SequenceMatcher(None, q, flat_ipa(n["f"]["IPA transcription"])).ratio(), n) for n in notes), key=lambda x: -x[0])
        print(f"{w} ({q}):")
        for r, n in scored[:5]:
            print(f"  {r:.2f}{line(n)}")


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `anki-he find … | head` must not traceback
    cmds = {"dump": dump, "find": find, "show": show, "dups": dups, "apply": apply, "sound": sound}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
