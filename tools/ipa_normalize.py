"""IPA normaliser (style documented in SKILL.md): writes proposed fixes, applies nothing.

norm(p)       mechanical cleanup: brackets, dots, χ/ħ/r/ɾ/ɡ, kh/sh/ts/y, ʔ/ʕ, vowels -> a e i o u
fix_stress(p) move ˈ from before the vowel to before the syllable onset (maskˈil -> masˈkil);
              careful: wrong after a dropped glottal (tedˈu), so review the output by hand.
CLI: python3 tools/ipa_normalize.py OUT.json  -> per-note old/new list for manual review.
"""

import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DUMP, GLOSS, MODEL


def norm(p):
    p = html.unescape(re.sub(r"<[^>]+>|&nbsp;", " ", p)).strip()
    p = re.sub(r"\s+", " ", p)
    p = re.sub(r"^\s*[\[/]|[\]/]\s*$", "", p).strip()
    p = re.sub(r"(?<=\s)[\[/]|[\]/](?=\s)", "", p) if " / " not in p else p
    p = p.replace("'", "ˈ").replace("’", "ˈ")
    p = p.replace("o̞", "o").replace("u̯", "u").replace("i̯", "i").replace("ɪ̯", "")
    for a, b in [
        ("t͡s", "ʦ"),
        ("ts", "ʦ"),
        ("tz", "ʦ"),
        ("t͡ʃ", "ʧ"),
        ("tʃ", "ʧ"),
        ("d͡ʒ", "ʤ"),
        ("dʒ", "ʤ"),
        ("kh", "x"),
        ("ch", "x"),
        ("sh", "ʃ"),
        ("zh", "ʒ"),
        ("χ", "x"),
        ("ħ", "x"),
        ("ɾ", "ʁ"),
        ("r", "ʁ"),
        ("R", "ʁ"),
        ("y", "j"),
        ("ɡ", "g"),
        ("ː", ""),
        (":", ""),
        ("ʔ", ""),
        ("ʕ", ""),
        ("ə", "e"),
        ("ǝ", "e"),
        ("ɑ", "a"),
        ("ɛ", "e"),
        ("ɔ", "o"),
        ("ɪ", "i"),
        ("ʊ", "u"),
        ("ľ", "l"),
        ("ṭ", "t"),
        ("ɖ", "d"),
        ("β", "v"),
        ("ˌ", ""),
        (".", ""),
    ]:
        p = p.replace(a, b)
    p = p.replace("ʦ", "t͡s").replace("ʧ", "t͡ʃ").replace("ʤ", "d͡ʒ")
    p = re.sub(r"(?<=[aeiou])h\b", "", p)  # dirah -> dira
    p = re.sub(r"ˈ\s*ˈ", "ˈ", p)
    return p.strip()


def fix_stress(p):
    # ˈ wrongly placed between onset consonant and vowel: maskˈil -> masˈkil
    return re.sub(r"(t͡s|t͡ʃ|d͡ʒ|[bdfghjklmnpstvxzʁʃʒ])ˈ(?=[aeiou])", r"ˈ\1", p)


def main():
    t = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>|&nbsp;", " ", s))).strip()
    rows = []
    for n in json.loads(DUMP.read_text()):
        if n["model"] != MODEL:
            continue
        f = n["f"]
        old = f["IPA transcription"]
        rows.append({"id": n["id"], "he": t(f["Hebrew"]), "ru": t(f[GLOSS]), "old": old, "new": fix_stress(norm(old))})
    Path(sys.argv[1]).write_text(json.dumps(rows, ensure_ascii=False))
    print("".join(sorted(set("".join(r["new"] for r in rows)))))
    print(sum(r["old"] != r["new"] for r in rows), "changed of", len(rows))


if __name__ == "__main__":
    main()
