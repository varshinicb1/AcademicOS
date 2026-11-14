#!/bin/bash
# Nightly backup to Cloudflare R2 (academicos-backup.timer, 02:30 IST).
#
#   pg.sql.gz      pg_dump of every JSONB store (users, papers, marking, ...)
#   files.tar.gz   the SQLite stores (consistent copies through SQLite's online backup API)
#                  and school uploads under /data, without the baked corpus
#
# Objects are keyed by day of month (01..31), so the bucket holds a rolling
# month with no pruning step and a fixed size. Needs /academicos/infra/
# r2-account-id, r2-bucket, r2-access-key-id, r2-secret-access-key.
set -euo pipefail
. /etc/academicos/stack.env
. /etc/academicos/infra.env
: "${R2_ACCOUNT_ID:?set /academicos/infra/r2-account-id}" "${R2_BUCKET:?set /academicos/infra/r2-bucket}"
ROOT=/opt/academicos
work="$ROOT/backup/run"
rm -rf "$work" && mkdir -p "$work/files"

docker exec db pg_dump -U academicos academicos | gzip -9 >"$work/pg.sql.gz"

cd "$ROOT/data"
find . -path ./corpus -prune -o -path ./syllabus -prune -o -type f -print | while read -r f; do
  mkdir -p "$work/files/$(dirname "$f")"
  case "$f" in
    *.sqlite|*.db) python3 -c 'import sqlite3, sys
src, dst = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
src.backup(dst); dst.close(); src.close()' "$f" "$work/files/$f" ;;
    *-wal|*-shm) ;;                                   # folded in by .backup
    *) cp -p "$f" "$work/files/$f" ;;
  esac
done
tar -C "$work/files" -czf "$work/files.tar.gz" .

day="$(TZ=Asia/Kolkata date +%d)"
export AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" AWS_DEFAULT_REGION=auto
for f in pg.sql.gz files.tar.gz; do
  aws s3 cp --only-show-errors "$work/$f" "s3://$R2_BUCKET/day-$day/$f" \
      --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"
done
echo "backup day-$day: $(du -h "$work/pg.sql.gz" | cut -f1) db, $(du -h "$work/files.tar.gz" | cut -f1) files"
rm -rf "$work"
