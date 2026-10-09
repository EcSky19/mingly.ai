# Backups

Every night the server backs up the **database** and every **uploaded photo**,
keeps 14 days of copies, and mirrors them to a **Hetzner Storage Box** - a
separate machine, so a backup survives losing the server. Every Sunday a
**restore test** restores the newest backup into a scratch database and checks
it, so we know the backups actually work instead of hoping.

| Script | What it does |
|---|---|
| `infrastructure/backup/backup.sh` | Dump the database (checked readable), archive `backend/uploads`, delete copies older than 14 days, mirror to the Storage Box |
| `infrastructure/backup/restore-test.sh` | Restore the newest dump into a scratch database next to the live one, compare row counts, check the photo archive opens, check the offsite copy matches; never touches live data |
| `infrastructure/backup/restore.sh` | **Disaster recovery.** Replace the live database and photos with a backup (asks you to type RESTORE; saves the current state aside first) |

Backups are readable by root only (`/var/backups/mingly`, mode 700). Every
failure exits non-zero, is logged to `/var/log/mingly-backup.log`, and pings
the optional health check so you get an email.

## One-time setup

**1. Order the Storage Box** (Hetzner console → Storage Boxes → BX11, about
€4/month for 1 TB; pick the same region as the server). In its settings:
- turn on **SSH support**
- turn on **automatic snapshots** (daily, keep 7-14). Snapshots protect against
  a bad sync - or someone with access to the server - wiping the offsite copy.

Note the username and host, e.g. `u123456` and `u123456.your-storagebox.de`.

**2. On the server, give it a key for the Storage Box** (asks for the Storage
Box password once):
```
apt-get install -y rsync
ssh-keygen -t ed25519 -f /root/.ssh/mingly_backup -N "" -C mingly-backup
cat /root/.ssh/mingly_backup.pub | ssh -p 23 u123456@u123456.your-storagebox.de install-ssh-key
```

**3. Tell the scripts where to send backups:**
```
cat > /etc/mingly-backup.env <<'CONF'
STORAGE_BOX=u123456@u123456.your-storagebox.de
# Optional: free alert if a backup fails or doesn't run - create a check at
# https://healthchecks.io (period 1 day, grace 2 hours) and paste its URL:
# HEALTHCHECK_URL=https://hc-ping.com/your-uuid
CONF
chmod 600 /etc/mingly-backup.env
```

**4. Run it once by hand, then prove it restores:**
```
/opt/mingly-ai/infrastructure/backup/backup.sh
/opt/mingly-ai/infrastructure/backup/restore-test.sh
```
The restore test should end with `Offsite copy matches the local backup` and
`RESTORE TEST PASSED`.

**5. Schedule it:**
```
cp /opt/mingly-ai/infrastructure/backup/mingly-backup.cron /etc/cron.d/mingly-backup
chmod 644 /etc/cron.d/mingly-backup
```

## Checking on backups
```
tail -30 /var/log/mingly-backup.log
ls -lh /var/backups/mingly/db /var/backups/mingly/photos
```

## Restoring after a disaster

Restoring loses everything since the backup, so only do it when the live data
is lost or corrupted.

**Same server:** `/opt/mingly-ai/infrastructure/backup/restore.sh` restores the
newest backup (or pass a specific `.dump` and `.tar.gz`). It stops the app,
saves the current database and photos to `/var/backups/mingly-before-restore-<time>`,
restores, runs any newer migrations, and starts the app again. Delete the
before-restore folder once you're happy.

**New server** (the old one is gone): set up the server and app as in
`infrastructure/DEPLOY.md` and steps 2-3 above, then pull the backups down and restore:
```
mkdir -p /var/backups/mingly
rsync -a -e "ssh -p 23 -i /root/.ssh/mingly_backup" u123456@u123456.your-storagebox.de:mingly-backups/ /var/backups/mingly/
/opt/mingly-ai/infrastructure/backup/restore.sh
```

## Retention and privacy
Backups hold personal data. Copies are kept 14 days, so a deleted account is
gone from backups within 14 days (plus up to 14 days in Storage Box snapshots);
the privacy policy says the same. Don't copy backups anywhere else.
