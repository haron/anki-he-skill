#!/usr/bin/env python3
"""Wrap every used note type's templates in <div class=fit> + auto-fit script (idempotent)."""

import re

from anki.collection import Collection

from config import COL_PATH, SKILL

SCRIPT = (SKILL / "templates/fit.html").read_text()
CSS = (SKILL / "templates/fit.css").read_text()


def strip(s):
    s = re.sub(r"<!--fit:v\d+-->.*?</script>\s*", "", s, flags=re.DOTALL)
    s = re.sub(r'^<div class="fit">(.*)</div>$', r"\1", s.strip(), flags=re.DOTALL)
    return s


def wrap(s):
    return f'<div class="fit">{strip(s)}</div>\n{SCRIPT}'


col = Collection(str(COL_PATH))
try:
    for nt in col.models.all():
        if not col.models.use_count(nt):
            continue
        for t in nt["tmpls"]:
            t["qfmt"], t["afmt"] = wrap(t["qfmt"]), wrap(t["afmt"])
        nt["css"] = re.sub(r"/\*fit:v\d+\*/.*", "", nt["css"], flags=re.DOTALL).rstrip() + "\n\n" + CSS
        col.models.update_dict(nt)
        print("updated", nt["name"])
finally:
    col.close()
