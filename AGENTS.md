# anki-he-skill — notes for agents working on this repo

This repo IS the `hebrew-anki` skill (SKILL.md at the root), for Claude Code and Codex.
It holds code only; the user's collection lives in a separate DATA dir (see `config.py`,
`anki-he`). Never commit collections, `.env`, `state.json` or anything personal here — this
repo is public.

- `anki-he` — bash entry point; resolves DATA, picks python (`anki` installed, else `uv`).
- `ankisync.py` — AnkiWeb sync (pull/push/status/dump), backups, media mirror, snapshot.
- `anki_he.py` — dump/find/sound/show/dups/apply on the local collection.
- `fit_templates.py` + `templates/` — auto-fit card templates (no scrolling, Hebrew ×1.35,
  pure black on AnkiDroid). Idempotent.
- `tools/` — helpers run as `anki-he tool NAME`.
- Settings: env vars listed in `config.py`; no hard-coded paths.

`make linter` before committing (also a prek pre-commit hook: `make githook`).
`make install` symlinks the checkout into ~/.claude/skills, ~/.agents/skills, ~/.codex/skills.
Schema changes in a user's collection (fields, note types, templates added/removed) force a
full sync — the code refuses them unless `push --force-upload`; keep it that way.
