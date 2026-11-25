# hebrew-anki

An agent skill (Claude Code, Codex) that turns Hebrew lesson material — pasted text,
textbook screenshots, lesson transcripts, SMS — into Anki cards, and keeps improving the
existing ones: nikud, IPA, a precise Russian gloss, an everyday example and a sound-alike
mnemonic. It talks to **AnkiWeb directly** (via the official `anki` Python package), so no
Anki Desktop or AnkiConnect is needed — it works from a laptop or a throwaway cloud container.

## Install

```sh
git clone https://github.com/haron/anki-he-skill ~/dev/anki-he-skill
make -C ~/dev/anki-he-skill install   # symlinks into ~/.claude/skills, ~/.agents/skills, ~/.codex/skills
```

Needs `python3` with `pip install -r requirements.txt`, or [uv](https://docs.astral.sh/uv/)
(then nothing else to install).

## Configure

| variable | meaning | default |
|---|---|---|
| `ANKIWEB_USERNAME`, `ANKIWEB_PASSWORD` | AnkiWeb login (or `ANKIWEB_HKEY`) | — |
| `ANKI_HE_DATA` | where the collection, backups and snapshots live | see below |
| `ANKI_HE_DECK` | deck for new notes | `Everything` |
| `ANKI_HE_MODEL` | note type of the Hebrew cards | `Hebrew+IPA+RU` |
| `ANKI_HE_GLOSS` | its translation field | `Русский перевод` |

DATA is `$ANKI_HE_DATA`, else the git repo around the current directory if it contains an
empty `.anki-he` file, else `~/.local/share/anki-he`. Variables may also be put in
`DATA/.env`. If DATA is a git repo (e.g. a private one), every pull/push commits a backup
(`.colpkg`), a media mirror and a diffable text snapshot there.

The note type is expected to have the fields `Hebrew`, `IPA transcription`, the gloss
field and `Example`.

## Use

Ask your agent to add or fix Hebrew cards, paste a text, or drop a screenshot; the agent
follows `SKILL.md`. By hand:

```sh
anki-he pull            # sync from AnkiWeb
anki-he find שלום       # search
anki-he sound шалом     # search by sound (Russian letters)
anki-he apply edits.json
anki-he push "message"  # sync back
```
