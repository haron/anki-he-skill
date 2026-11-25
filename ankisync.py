#!/usr/bin/env python3
"""Sync an Anki collection with AnkiWeb from a throwaway container.

Commands:
  pull    get the AnkiWeb collection into DATA/work/ (full download the first time, normal
          two-way sync afterwards, so local edits survive)
  push    normal (incremental) sync of local changes back to AnkiWeb
  With ANKI_HE_BACKUP=1 (or --backup) pull also writes a .colpkg backup, and pull/push
  mirror media and dump a diffable text snapshot into DATA.
  status  what AnkiWeb thinks needs to happen
  dump    re-dump the text snapshot from work/ (no network)

Credentials (environment variables):
  ANKIWEB_HKEY                          preferred, if you have it
  ANKIWEB_USERNAME + ANKIWEB_PASSWORD   otherwise; logs in each run
Values may also live in DATA/.env (KEY=VALUE per line); see config.py for DATA.
Optional: ANKIWEB_ENDPOINT (shard endpoint; normally learned automatically).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import time
from pathlib import Path

from anki.collection import Collection
from anki.sync_pb2 import SyncAuth, SyncCollectionResponse

from config import BACKUP, COL_PATH, DATA, WORK

ROOT = DATA
STATE = WORK / "state.json"
BACKUPS = DATA / "backups"
SNAPSHOT = DATA / "snapshot"
MEDIA_MIRROR = DATA / "media"

Req = SyncCollectionResponse.ChangesRequired


def log(msg: str) -> None:
    print(f"[ankisync] {msg}", file=sys.stderr, flush=True)


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state: dict) -> None:
    WORK.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2))
    STATE.chmod(0o600)  # holds the AnkiWeb session key


def get_auth(col: Collection) -> SyncAuth:
    state = load_state()
    endpoint = state.get("endpoint") or os.environ.get("ANKIWEB_ENDPOINT") or None
    user = os.environ.get("ANKIWEB_USERNAME")
    pw = os.environ.get("ANKIWEB_PASSWORD")
    hkey = os.environ.get("ANKIWEB_HKEY") or (state.get("hkey") if state.get("user") == user else None)
    if not hkey:
        if not (user and pw):
            sys.exit("No credentials: set ANKIWEB_HKEY or ANKIWEB_USERNAME/ANKIWEB_PASSWORD")
        log("logging in to AnkiWeb")
        auth = col.sync_login(username=user, password=pw, endpoint=endpoint)
        hkey = auth.hkey
        endpoint = auth.endpoint or endpoint
    state.update(hkey=hkey, endpoint=endpoint, user=user)
    save_state(state)
    auth = SyncAuth(hkey=hkey)
    if endpoint:
        auth.endpoint = endpoint
    return auth


def remember_endpoint(auth: SyncAuth, out) -> None:
    if out.new_endpoint:
        log(f"server moved us to {out.new_endpoint}")
        auth.endpoint = out.new_endpoint
        state = load_state()
        state["endpoint"] = out.new_endpoint
        save_state(state)


def wait_media(col: Collection) -> None:
    while True:
        st = col.media_sync_status()
        if not st.active:
            break
        time.sleep(0.5)
    log("media sync done")


def sync_media(col: Collection, auth: SyncAuth) -> None:
    log("syncing media")
    col.sync_media(auth)
    time.sleep(0.5)
    wait_media(col)


def full_sync(col: Collection, auth: SyncAuth, server_usn: int, upload: bool) -> Collection:
    log("full " + ("UPLOAD (overwrites AnkiWeb)" if upload else "download"))
    col.close_for_full_sync()
    col.full_upload_or_download(auth=auth, server_usn=server_usn, upload=upload)
    col.reopen(after_full_sync=True)
    return col


def cmd_pull(args) -> None:
    if COL_PATH.exists() and not args.force:
        return incremental_pull(args)
    if args.force and WORK.exists():
        for p in [COL_PATH, *WORK.glob("collection.anki2-*")]:
            p.unlink(missing_ok=True)
    WORK.mkdir(exist_ok=True)
    col = Collection(str(COL_PATH))
    try:
        auth = get_auth(col)
        out = col.sync_collection(auth, sync_media=False)
        remember_endpoint(auth, out)
        if out.server_message:
            log(f"server says: {out.server_message}")
        # A brand-new empty collection always ends up taking the server's copy.
        if out.required in (Req.FULL_DOWNLOAD, Req.FULL_SYNC):
            col = full_sync(col, auth, out.server_media_usn, upload=False)
        elif out.required == Req.FULL_UPLOAD:
            sys.exit("AnkiWeb collection looks empty; refusing to continue")
        sync_media(col, auth)
        log(f"{col.card_count()} cards, {col.note_count()} notes")
        if BACKUP or args.backup:
            backup(col)
            dump(col)
    finally:
        col.close()


def incremental_pull(args) -> None:
    """Local copy exists: normal two-way sync, so unpushed local edits are kept."""
    col = Collection(str(COL_PATH))
    try:
        auth = get_auth(col)
        out = col.sync_collection(auth, sync_media=False)
        remember_endpoint(auth, out)
        if out.server_message:
            log(f"server says: {out.server_message}")
        if out.required in (Req.FULL_SYNC, Req.FULL_UPLOAD, Req.FULL_DOWNLOAD):
            sys.exit(
                f"AnkiWeb wants a one-way full sync ({Req.Name(out.required)}). If the local copy "
                "has nothing worth keeping, run `pull --force` to re-download; otherwise ask the user."
            )
        log(f"incremental sync: {Req.Name(out.required)}")
        sync_media(col, auth)
        log(f"{col.card_count()} cards, {col.note_count()} notes")
        if BACKUP or args.backup:
            backup(col)
            dump(col)
    finally:
        col.close()


def cmd_push(args) -> None:
    if not COL_PATH.exists():
        sys.exit("nothing to push: run `pull` first")
    col = Collection(str(COL_PATH))
    try:
        auth = get_auth(col)
        out = col.sync_collection(auth, sync_media=False)
        remember_endpoint(auth, out)
        if out.server_message:
            log(f"server says: {out.server_message}")
        if out.required in (Req.FULL_SYNC, Req.FULL_UPLOAD, Req.FULL_DOWNLOAD):
            if not args.force_upload:
                sys.exit(
                    f"AnkiWeb requires a one-way full sync ({Req.Name(out.required)}). "
                    "Usually caused by a schema change (note type fields/templates). "
                    "Make sure every device has synced first, then rerun with --force-upload. "
                    "After that, other devices must choose 'Download from AnkiWeb'."
                )
            col = full_sync(col, auth, out.server_media_usn, upload=True)
        else:
            log(f"sync result: {Req.Name(out.required)}")
        sync_media(col, auth)
        if BACKUP or args.backup:
            mirror_media(col)
            dump(col)
    finally:
        col.close()


def cmd_status(args) -> None:
    if not COL_PATH.exists():
        sys.exit("no local collection: run `pull` first")
    col = Collection(str(COL_PATH))
    try:
        auth = get_auth(col)
        st = col.sync_status(auth)
        print(st.Required.Name(st.required))
    finally:
        col.close()


def cmd_dump(args) -> None:
    col = Collection(str(COL_PATH))
    try:
        dump(col)
    finally:
        col.close()


def backup(col: Collection) -> None:
    BACKUPS.mkdir(exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    path = BACKUPS / f"{stamp}.colpkg"
    # Media is mirrored into media/ instead, so git stores each file once.
    col.export_collection_package(str(path), include_media=False, legacy=False)
    col.reopen()  # exporting a .colpkg closes the collection
    log(f"backup: {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KiB)")
    mirror_media(col)


def mirror_media(col: Collection) -> None:
    """Copy new/changed media into media/. Never deletes (it's a backup)."""
    src = Path(col.media.dir())
    MEDIA_MIRROR.mkdir(exist_ok=True)
    copied = 0
    for f in src.iterdir():
        if not f.is_file():
            continue
        dst = MEDIA_MIRROR / f.name
        if not dst.exists() or dst.stat().st_size != f.stat().st_size or dst.read_bytes() != f.read_bytes():
            shutil.copy2(f, dst)
            copied += 1
    log(f"media mirror: {copied} files updated")


def dump(col: Collection) -> None:
    """Human-readable, diffable snapshot of content (no scheduling noise)."""
    SNAPSHOT.mkdir(exist_ok=True)
    nt_dir = SNAPSHOT / "notetypes"
    nt_dir.mkdir(exist_ok=True)
    for old in nt_dir.glob("*.json"):
        old.unlink()
    nt_names = {}
    for nt in col.models.all():
        nt_names[nt["id"]] = nt["name"]
        slim = {
            "id": nt["id"],
            "name": nt["name"],
            "fields": [f["name"] for f in nt["flds"]],
            "templates": [{"name": t["name"], "qfmt": t["qfmt"], "afmt": t["afmt"]} for t in nt["tmpls"]],
            "css": nt["css"],
        }
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in nt["name"])
        (nt_dir / f"{safe}.{nt['id']}.json").write_text(json.dumps(slim, ensure_ascii=False, indent=2) + "\n")

    decks = {d.id: d.name for d in col.decks.all_names_and_ids()}
    (SNAPSHOT / "decks.json").write_text(json.dumps(sorted(decks.values()), ensure_ascii=False, indent=2) + "\n")

    lines = []
    for nid in sorted(col.find_notes("")):
        note = col.get_note(nid)
        card_decks = sorted({decks.get(c.did, str(c.did)) for c in note.cards()})
        lines.append(
            json.dumps(
                {
                    "id": nid,
                    "type": nt_names.get(note.mid, str(note.mid)),
                    "decks": card_decks,
                    "tags": sorted(note.tags),
                    "fields": dict(note.items()),
                },
                ensure_ascii=False,
            )
        )
    (SNAPSHOT / "notes.jsonl").write_text("\n".join(lines) + "\n")
    log(f"snapshot: {len(lines)} notes -> snapshot/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--force", action="store_true", help="discard local work/ copy and re-download")
    p.add_argument("--backup", action="store_true", help="also back up, mirror media, dump a snapshot")
    p.set_defaults(fn=cmd_pull)
    p = sub.add_parser("push")
    p.add_argument("--force-upload", action="store_true")
    p.add_argument("--backup", action="store_true", help="also mirror media, dump a snapshot")
    p.set_defaults(fn=cmd_push)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("dump").set_defaults(fn=cmd_dump)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
