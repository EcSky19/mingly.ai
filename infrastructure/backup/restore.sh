#!/usr/bin/env bash
# DISASTER RECOVERY: replaces the LIVE database and photos with a backup.
# Everything since that backup is lost. Read docs/backups.md first.
#
#   infrastructure/backup/restore.sh                          # newest backup
#   infrastructure/backup/restore.sh <file.dump> <photos.tar.gz>
#
# The current database and photos are saved aside first (a fresh dump and
# the old uploads folder), so a restore can itself be undone.
set -Eeuo pipefail

CONFIG="${CONFIG:-/etc/mingly-backup.env}"
# shellcheck disable=SC1090
[ -f "$CONFIG" ] && . "$CONFIG"

APP_DIR="${APP_DIR:-/opt/mingly-ai}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mingly}"
compose() { docker compose --project-directory "$APP_DIR" "$@"; }
log() { echo "$(date -u +%FT%TZ) $*"; }
trap 'log "RESTORE FAILED (line $LINENO) - the app may be stopped; see docs/backups.md" >&2; exit 1' ERR

dump="${1:-$(ls -1t "$BACKUP_DIR"/db/*.dump 2> /dev/null | head -1 || true)}"
photos="${2:-$(ls -1t "$BACKUP_DIR"/photos/*.tar.gz 2> /dev/null | head -1 || true)}"
[ -f "$dump" ] || { log "Database backup not found: $dump"; exit 1; }
[ -f "$photos" ] || { log "Photo backup not found: $photos"; exit 1; }

echo "This replaces the LIVE Mingly database and photos with:"
echo "  $dump"
echo "  $photos"
echo "Everything that happened after those backups will be lost."
read -r -p "Type RESTORE to continue: " answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }

umask 077
stamp="$(date -u +%Y-%m-%dT%H%MZ)"
# Next to the backups, not inside them: this copy isn't sent offsite or
# kept forever - delete it once you're happy with the restore.
aside="${BACKUP_DIR%/}-before-restore-$stamp"
mkdir -p "$aside"

log "Stopping the app"
compose stop backend frontend

log "Saving the current database to $aside"
compose exec -T db pg_dump -U mingly -d mingly --format=custom > "$aside/mingly.dump"

log "Restoring the database"
compose exec -T db dropdb -U mingly --if-exists mingly
compose exec -T db createdb -U mingly mingly
compose exec -T db pg_restore -U mingly -d mingly --no-owner --exit-on-error < "$dump"

log "Restoring photos (current ones moved to $aside/uploads)"
[ -d "$APP_DIR/backend/uploads" ] && mv "$APP_DIR/backend/uploads" "$aside/uploads"
tar -xzf "$photos" -C "$APP_DIR/backend"
mkdir -p "$APP_DIR/backend/uploads"

log "Starting the app"
compose start backend frontend
# A backup from before a later deploy has an older schema - bring it up to date.
compose exec -T backend alembic upgrade head
log "Restore complete. The pre-restore copy is in $aside"
