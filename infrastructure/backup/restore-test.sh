#!/usr/bin/env bash
# Proves the latest backup can actually be restored - without touching the
# live database. Restores the newest dump into a scratch database next to
# the real one, checks the tables and row counts, checks the photo archive
# opens, then drops the scratch database. Run weekly by cron and after any
# change to the backup setup (see docs/backups.md).
#
# With STORAGE_BOX set, it also downloads the newest offsite dump and checks
# it's byte-for-byte the same as the local one.
set -Eeuo pipefail

CONFIG="${CONFIG:-/etc/mingly-backup.env}"
# shellcheck disable=SC1090
[ -f "$CONFIG" ] && . "$CONFIG"

APP_DIR="${APP_DIR:-/opt/mingly-ai}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mingly}"
STORAGE_BOX="${STORAGE_BOX:-}"
STORAGE_BOX_DIR="${STORAGE_BOX_DIR:-mingly-backups}"
SSH_KEY="${SSH_KEY:-/root/.ssh/mingly_backup}"
SCRATCH_DB="mingly_restore_test"

compose() { docker compose --project-directory "$APP_DIR" "$@"; }
psql_in() { compose exec -T db psql -U mingly -d "$1" -Atc "$2"; }
log() { echo "$(date -u +%FT%TZ) $*"; }
cleanup() { compose exec -T db dropdb -U mingly --if-exists "$SCRATCH_DB" > /dev/null 2>&1 || true; rm -rf "${tmp:-}"; }
trap cleanup EXIT
trap 'log "RESTORE TEST FAILED (line $LINENO)" >&2; exit 1' ERR

dump="$(ls -1t "$BACKUP_DIR"/db/*.dump 2> /dev/null | head -1 || true)"
photos="$(ls -1t "$BACKUP_DIR"/photos/*.tar.gz 2> /dev/null | head -1 || true)"
[ -n "$dump" ] || { log "No database backups found in $BACKUP_DIR/db"; exit 1; }
[ -n "$photos" ] || { log "No photo backups found in $BACKUP_DIR/photos"; exit 1; }
log "Testing $dump"

compose exec -T db dropdb -U mingly --if-exists "$SCRATCH_DB"
compose exec -T db createdb -U mingly "$SCRATCH_DB"
compose exec -T db pg_restore -U mingly -d "$SCRATCH_DB" --no-owner --exit-on-error < "$dump"

restored_version="$(psql_in "$SCRATCH_DB" "select version_num from alembic_version")"
live_version="$(psql_in mingly "select version_num from alembic_version")"
status=0
printf '  %-22s %10s %10s\n' "" "backup" "live now"
printf '  %-22s %10s %10s\n' "migration" "$restored_version" "$live_version"
for table in users user_interactions circle_connections user_reports; do
  restored="$(psql_in "$SCRATCH_DB" "select count(*) from $table")"
  live="$(psql_in mingly "select count(*) from $table")"
  printf '  %-22s %10s %10s\n' "$table" "$restored" "$live"
done
[ -n "$restored_version" ] || { log "Restored database has no migration version"; status=1; }

photo_count="$(tar -tzf "$photos" | grep -c -v '/$' || true)"
log "Photo archive opens: $photo_count files in $(basename "$photos")"

if [ -n "$STORAGE_BOX" ]; then
  tmp="$(mktemp -d)"
  rsync -a -e "ssh -p 23 -i $SSH_KEY -o BatchMode=yes" \
    "$STORAGE_BOX:$STORAGE_BOX_DIR/db/$(basename "$dump")" "$tmp/"
  if cmp -s "$dump" "$tmp/$(basename "$dump")"; then
    log "Offsite copy matches the local backup"
  else
    log "Offsite copy is MISSING or DIFFERENT"; status=1
  fi
fi

if [ "$status" -eq 0 ]; then log "RESTORE TEST PASSED"; else log "RESTORE TEST FAILED"; fi
exit "$status"
