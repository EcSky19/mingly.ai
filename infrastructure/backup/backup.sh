#!/usr/bin/env bash
# Nightly Mingly backup: the database and every uploaded photo.
#
#   1. Dumps the database (pg_dump, custom format) and checks the dump is
#      readable before keeping it.
#   2. Archives backend/uploads (profile photos and saved LinkedIn photos).
#   3. Deletes local copies older than KEEP_DAYS.
#   4. Mirrors the backup folder to the Hetzner Storage Box, if configured,
#      so a backup survives losing this server.
#
# Run by cron (see docs/backups.md). Settings live in /etc/mingly-backup.env.
# Exits non-zero on any failure, and pings HEALTHCHECK_URL/fail if set, so a
# silent failure can't go unnoticed.
set -Eeuo pipefail

CONFIG="${CONFIG:-/etc/mingly-backup.env}"
# shellcheck disable=SC1090
[ -f "$CONFIG" ] && . "$CONFIG"

APP_DIR="${APP_DIR:-/opt/mingly-ai}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mingly}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STORAGE_BOX="${STORAGE_BOX:-}"            # e.g. u123456@u123456.your-storagebox.de
STORAGE_BOX_DIR="${STORAGE_BOX_DIR:-mingly-backups}"
SSH_KEY="${SSH_KEY:-/root/.ssh/mingly_backup}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-}"

STAMP="$(date -u +%Y-%m-%dT%H%MZ)"
compose() { docker compose --project-directory "$APP_DIR" "$@"; }
log() { echo "$(date -u +%FT%TZ) $*"; }
ping_health() { [ -n "$HEALTHCHECK_URL" ] && curl -fsS -m 10 "$HEALTHCHECK_URL$1" > /dev/null || true; }
step="starting"
on_error() {
  log "BACKUP FAILED while $step" >&2
  rm -f "$BACKUP_DIR"/db/*.partial "$BACKUP_DIR"/photos/*.partial
  ping_health /fail
  exit 1
}
trap on_error ERR

umask 077  # backups hold personal data: readable by root only
mkdir -p "$BACKUP_DIR/db" "$BACKUP_DIR/photos"

step="backing up the database"; log "Backing up the database"
db_file="$BACKUP_DIR/db/mingly-$STAMP.dump"
compose exec -T db pg_dump -U mingly -d mingly --format=custom > "$db_file.partial"
# A dump that pg_restore can't read is worse than none - it looks like a backup.
compose exec -T db pg_restore --list < "$db_file.partial" > /dev/null
mv "$db_file.partial" "$db_file"
log "  $(du -h "$db_file" | cut -f1)  $db_file"

step="backing up photos"; log "Backing up photos"
photos_file="$BACKUP_DIR/photos/photos-$STAMP.tar.gz"
if [ -d "$APP_DIR/backend/uploads" ]; then
  tar -czf "$photos_file.partial" -C "$APP_DIR/backend" uploads
else
  log "  (no uploads folder yet - writing an empty archive)"
  tar -czf "$photos_file.partial" -T /dev/null
fi
tar -tzf "$photos_file.partial" > /dev/null
mv "$photos_file.partial" "$photos_file"
log "  $(du -h "$photos_file" | cut -f1)  $photos_file"

step="removing old backups"; log "Removing local backups older than $KEEP_DAYS days"
find "$BACKUP_DIR" -type f \( -name '*.dump' -o -name '*.tar.gz' \) -mtime +"$KEEP_DAYS" -print -delete

if [ -n "$STORAGE_BOX" ]; then
  step="copying to the Storage Box"; log "Copying to the Storage Box ($STORAGE_BOX:$STORAGE_BOX_DIR)"
  # --delete keeps the offsite copy to the same KEEP_DAYS window, so deleted
  # accounts don't live on forever offsite. Storage Box snapshots (enabled
  # in the Hetzner console) protect against a bad sync wiping both copies.
  rsync -a --delete -e "ssh -p 23 -i $SSH_KEY -o BatchMode=yes -o StrictHostKeyChecking=accept-new" \
    "$BACKUP_DIR/" "$STORAGE_BOX:$STORAGE_BOX_DIR/"
else
  log "STORAGE_BOX not set - backup kept on this server only"
fi

ping_health ""
log "Backup complete"
