# AcademicOS on AWS + Cloudflare

The release that replaces Cloud Run + Cloud SQL + Firebase Hosting while the Google
Cloud billing account is closed. Free services first; AWS credits pay only for the
one thing neither provider gives away: an always-on machine.

```
 browser ──► Cloudflare Pages (web console, app.<domain> / <project>.pages.dev)
    │
    └──────► Cloudflare edge (TLS, DNS, WAF, DDoS) ──► Cloudflare Tunnel ──┐
                                                                         │ outbound only
 AWS ap-south-1 (Mumbai) ── EC2 host, no inbound ports ◄─────────────────┘
   ├─ app         the backend image (same Dockerfile as Cloud Run)
   ├─ db          PostgreSQL 16 on an encrypted EBS data volume
   ├─ cloudflared the tunnel
   └─ systemd     automations every 5 min, nightly backup ──► Cloudflare R2
```

## What is free and what uses credits

| Need | Service | Cost |
|---|---|---|
| Web console hosting | Cloudflare Pages | Free |
| TLS, DNS, WAF, DDoS, public hostname for the API | Cloudflare (free plan) + Tunnel | Free |
| Nightly backups (rolling 31 days) | Cloudflare R2 (10 GB free) | Free |
| Secrets and settings | AWS SSM Parameter Store (standard) | Free |
| Shell access, deploys | AWS SSM Session Manager / Run Command | Free |
| Deploy credentials | GitHub OIDC → IAM role (no stored keys) | Free |
| Spend alert | AWS Budgets (first two free) | Free |
| Scheduled jobs | systemd timer on the host (was Cloud Scheduler) | Free |
| **API + PostgreSQL** | **EC2 t3.small, 20 + 10 GB gp3, public IPv4** | **Credits, about $23/month (estimated)** |
| Container images | Amazon ECR (last 5 kept, about 1 GB) | Credits, under $0.20/month (estimated) |

The estimate is from AWS's published on-demand prices for ap-south-1 (t3.small
$0.0224/h, gp3 $0.0912/GB-month, public IPv4 $0.005/h), not a bill. On an account
still inside the old 12-month free tier, a t3.micro and 30 GB would be free, but
1 GiB cannot hold the API (Cloud Run gave it 1 GiB alone) and PostgreSQL together.

Why not something free for the API: AWS has no always-free Postgres, and Lambda
cannot hold the two SQLite stores (`CurriculumStore`, `OperationsStore`), which need
one long-lived writer (CLAUDE.md, "Storage"). Once R-A1 moves them to Postgres,
Lambda's free tier becomes an option.

## One-time setup (owner)

1. **AWS, CloudFormation console, region Asia Pacific (Mumbai):** Create stack →
   Upload `deploy/aws/academicos.yaml` → stack name `academicos` → enter an alert
   email → tick the IAM acknowledgement → Create. About 3 minutes. Copy the four
   values on the **Outputs** tab.
2. **Cloudflare dashboard:**
   - Add your domain (free plan) and switch its nameservers, if it is not on
     Cloudflare already.
   - Zero Trust → Networks → Tunnels → Create a tunnel (Cloudflared) named
     `academicos`. Copy the token from the install command. Add a public hostname
     `api.<domain>` → service `http://app:8080`.
   - R2 → Create bucket `academicos-backups` (location hint Asia-Pacific) → Manage
     API tokens → Create token, **Object Read & Write, this bucket only**. Copy the
     access key id and secret.
   - My Profile → API Tokens → Create token → Custom: **Account / Cloudflare Pages /
     Edit** only. Copy it, and your account id.
3. **AWS, Systems Manager → Parameter Store** (same region), type **SecureString**:

   | Name | Value |
   |---|---|
   | `/academicos/infra/cloudflared-token` | the tunnel token |
   | `/academicos/infra/r2-account-id` | Cloudflare account id |
   | `/academicos/infra/r2-bucket` | `academicos-backups` |
   | `/academicos/infra/r2-access-key-id` | R2 access key id |
   | `/academicos/infra/r2-secret-access-key` | R2 secret |

   Optional app settings go under `/academicos/env/<VARIABLE>`: e.g.
   `ACOS_SMS_AUTHKEY`, `ACOS_SMS_TEMPLATE_ID` (MSG91), `ACOS_LLM_API_KEY`,
   `ACOS_LLM_BASE_URL`. Each reaches the app on the next deploy.
4. **GitHub → Settings → Secrets and variables → Actions:**
   - Variables: `AWS_DEPLOY_ROLE_ARN`, `AWS_INSTANCE_ID`, `AWS_REGION`, `AWS_ECR_REPO`
     (from step 1), `API_ORIGIN` = `https://api.<domain>`, `PAGES_PROJECT` =
     `academicos`, `WEB_ORIGINS` = `https://academicos.pages.dev` (add
     `,https://app.<domain>` once you attach that custom domain in Pages).
   - Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
5. Merge the PR that adds this, or run **Actions → Deploy to AWS + Cloudflare → Run
   workflow** on master. The run fails loudly if a variable is missing.

The host generates its own Postgres password, principal bootstrap key, cron key and
ops key on first boot, into `/academicos/env/` in Parameter Store. Nobody types them.
Read the principal bootstrap key there when registering the first principal.

## Every deploy

`.github/workflows/deploy-aws.yml`, on each push to master: both test gates, then
build → ECR → `install.sh` + `deploy.sh` on the host over SSM. `deploy.sh` applies
`deploy/gcp/schema.sql` (all `IF NOT EXISTS`), swaps the container, and rolls back
to the previous image if the new one does not report its own commit on `/health`
within 3 minutes. The job then checks `/health` again through Cloudflare. The swap
takes about 10 to 20 seconds of downtime (Cloud Run had none).

## Operating it

- Shell: EC2 console → the `academicos` instance → Connect → Session Manager.
- Logs: `sudo docker logs --tail 200 app`
- Jobs: `systemctl list-timers 'academicos-*'`, `journalctl -u academicos-automations`
- Backup now: `sudo systemctl start academicos-backup`
- Restore: download `day-<dd>/pg.sql.gz` and `files.tar.gz` from R2, then
  `gunzip -c pg.sql.gz | sudo docker exec -i db psql -U academicos academicos` into
  an empty database, and untar `files.tar.gz` into `/opt/academicos/data` with the
  app stopped.

## Not done here

- Moving data out of Google Cloud. Cloud SQL and GCS are unreachable while that
  billing account is closed. A school with live data there needs billing back for
  an export (pg_dump + `gsutil cp`), or starts fresh here.
- `docs/compliance.md` and the DPA's sub-processor list still name Google Cloud and
  Firebase. AWS (ap-south-1) and Cloudflare must replace them before a school's
  data is served here (owner decision, compliance.md §LLM/hosting table).
- `deploy-gcp.yml` still runs its test jobs on every merge; disable it once this
  release is live.
