"""Shared settings for the hebrew-anki scripts.

The code lives in this skill directory; the collection and its history live in a separate
DATA directory, chosen by the `anki-he` wrapper and passed down as ANKI_HE_DATA:
    $ANKI_HE_DATA, else the git repo around the current directory if it has an `.anki-he`
    marker file, else ${XDG_DATA_HOME:-~/.local/share}/anki-he.

Settings come from environment variables; a `.env` file (KEY=VALUE lines) in DATA is read
too, real environment variables win:
    ANKIWEB_USERNAME, ANKIWEB_PASSWORD   AnkiWeb login (or ANKIWEB_HKEY, a session key)
    ANKI_HE_DECK     deck for new notes and dumps        (default: Default)
    ANKI_HE_MODEL    note type of the Hebrew cards       (default: Hebrew+IPA+RU)
    ANKI_HE_GLOSS    its translation field               (default: Русский перевод)
    ANKI_HE_BACKUP   1 = on every pull/push also keep a .colpkg backup, a media mirror and a
                     text snapshot in DATA (default: off — Anki's own backups are enough)
"""

import os
from pathlib import Path

SKILL = Path(__file__).resolve().parent
DATA = Path(os.environ.get("ANKI_HE_DATA") or Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share") / "anki-he")
WORK = DATA / "work"
COL_PATH = WORK / "collection.anki2"
DUMP = WORK / "he-dump.json"


def load_dotenv() -> None:
    path = DATA / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.removeprefix("export ").split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip("'\""))


load_dotenv()
DECK = os.environ.get("ANKI_HE_DECK", "Default")
MODEL = os.environ.get("ANKI_HE_MODEL", "Hebrew+IPA+RU")
GLOSS = os.environ.get("ANKI_HE_GLOSS", "Русский перевод")
BACKUP = os.environ.get("ANKI_HE_BACKUP", "").lower() in ("1", "true", "yes", "on")
