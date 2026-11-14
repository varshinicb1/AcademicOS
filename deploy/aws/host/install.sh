#!/bin/bash
# Prepares the AcademicOS host. Idempotent: every GitHub deploy runs it before
# deploy.sh, so a change to these scripts or units ships with the release.
#   - mounts the encrypted data volume at /opt/academicos
#   - generates the secrets production needs, once, into SSM Parameter Store
#   - installs the systemd timers (automations every 5 min, nightly backup)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. /etc/academicos/stack.env
export AWS_REGION AWS_DEFAULT_REGION="$AWS_REGION"
ROOT=/opt/academicos

# ---------------------------------------------------------------- data volume
# The second disk (the one that is not the root disk). On Nitro instances it is
# an NVMe device whatever name CloudFormation attached it under.
if ! mountpoint -q "$ROOT"; then
  rootdisk="/dev/$(lsblk -no PKNAME "$(findmnt -no SOURCE /)")"
  dev=""
  for _ in $(seq 1 60); do
    dev="$(lsblk -dpno NAME,TYPE | awk '$2=="disk"{print $1}' | grep -vx "$rootdisk" | head -n1 || true)"
    [ -n "$dev" ] && break
    sleep 5
  done
  [ -n "$dev" ] || { echo "data volume never appeared" >&2; exit 1; }
  if ! blkid "$dev" >/dev/null 2>&1; then
    mkfs.xfs -L acos-data "$dev"      # first boot only: blkid finds no filesystem
  fi
  mkdir -p "$ROOT"
  uuid="$(blkid -s UUID -o value "$dev")"
  grep -q "$uuid" /etc/fstab || echo "UUID=$uuid $ROOT xfs defaults,nofail 0 2" >>/etc/fstab
  mount "$ROOT"
fi
mkdir -p "$ROOT/pg" "$ROOT/data" "$ROOT/backup"
chown 1001:1001 "$ROOT/data"          # the image's non-root user (Dockerfile USER 1001)
chmod 700 "$ROOT/backup"

# ---------------------------------------------------------------- secrets
# Generated here, never typed by a person and never in the repository.
# put-parameter without --overwrite fails if the name exists, so an existing
# secret is never replaced (a new Postgres password would lock the app out).
gen() {
  local name="/academicos/env/$1"
  aws ssm put-parameter --name "$name" --type SecureString \
      --value "$(openssl rand -hex 32)" >/dev/null 2>&1 && echo "generated $name" || true
}
gen ACOS_POSTGRES_PASSWORD
gen ACOS_PRINCIPAL_BOOTSTRAP_KEY
gen ACOS_CRON_KEY
gen ACOS_OPS_KEY

# ---------------------------------------------------------------- scripts + units
install -d /opt/academicos-bin
install -m 0755 "$HERE"/render-env.sh "$HERE"/deploy.sh "$HERE"/backup.sh "$HERE"/run-automations.sh /opt/academicos-bin/
install -m 0644 "$HERE"/systemd/*.service "$HERE"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now academicos-automations.timer academicos-backup.timer
echo "host ready"
