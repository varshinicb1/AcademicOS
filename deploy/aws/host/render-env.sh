#!/bin/bash
# Writes the containers' environment files from SSM Parameter Store.
#
#   /academicos/env/<NAME>    -> NAME=<value> in the app's env file. Anything an
#                                operator adds here (ACOS_SMS_AUTHKEY, ACOS_LLM_API_KEY,
#                                ACOS_LLM_BASE_URL, ...) reaches the app on the next deploy.
#   /academicos/infra/<name>  -> host-only settings (tunnel token, R2 backup keys);
#                                never given to the app.
#
# Values never touch the repository, the deploy log or the command line.
set -euo pipefail
. /etc/academicos/stack.env
export AWS_REGION AWS_DEFAULT_REGION="$AWS_REGION"
OUT=/etc/academicos
umask 077

fetch() {  # fetch <path> -> "name<TAB>value" lines
  aws ssm get-parameters-by-path --path "$1" --recursive --with-decryption \
      --query 'Parameters[].[Name,Value]' --output text
}

tmp="$(mktemp)"
fetch /academicos/env/ | while IFS=$'\t' read -r name value; do
  printf '%s=%s\n' "${name##*/}" "$value"
done >"$tmp"

# Fixed settings for this host. The production guard (config.py) refuses to
# start if any of them is unsafe.
{
  echo "ACOS_ENV=production"
  echo "ACOS_POSTGRES_HOST=db"
  echo "ACOS_POSTGRES_DB=academicos"
  echo "ACOS_POSTGRES_USER=academicos"
  echo "ACOS_DATA_ROOT=/data"
  # From the deploy (WEB_ORIGINS repository variable) unless set in SSM.
  if [ -n "${ACOS_CORS_ORIGINS:-}" ] && ! grep -q '^ACOS_CORS_ORIGINS=' "$tmp"; then
    echo "ACOS_CORS_ORIGINS=$ACOS_CORS_ORIGINS"
  fi
} >>"$tmp"

# One LLM key, both names (as deploy-gcp.yml does): scan OCR and AI marking
# read SARVAM_API_KEY, the doubt critic reads ACOS_LLM_API_KEY.
if grep -q '^ACOS_LLM_API_KEY=' "$tmp" && ! grep -q '^SARVAM_API_KEY=' "$tmp"; then
  sed -n 's/^ACOS_LLM_API_KEY=/SARVAM_API_KEY=/p' "$tmp" >>"$tmp"
fi
install -m 0600 "$tmp" "$OUT/app.env"

# PostgreSQL gets only its own password.
pw="$(sed -n 's/^ACOS_POSTGRES_PASSWORD=//p' "$tmp")"
[ -n "$pw" ] || { echo "/academicos/env/ACOS_POSTGRES_PASSWORD is missing; run install.sh" >&2; exit 1; }
printf 'POSTGRES_USER=academicos\nPOSTGRES_DB=academicos\nPOSTGRES_PASSWORD=%s\n' "$pw" >"$OUT/db.env"
chmod 600 "$OUT/db.env"
rm -f "$tmp"

fetch /academicos/infra/ | while IFS=$'\t' read -r name value; do
  key="$(echo "${name##*/}" | tr 'a-z-' 'A-Z_')"
  printf '%s=%s\n' "$key" "$value"
done >"$OUT/infra.env"
chmod 600 "$OUT/infra.env"
