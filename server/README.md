# Wellora API test service

First milestone: username/password accounts and one private basic profile per account. Use fictional test data only.

## Local tests

Requires Python 3.12 and `uv` 0.12.19 or later. PowerShell:

```powershell
uv sync --locked --group dev --default-index https://pypi.org/simple
uv run --no-sync pytest -q
```

Tests use a fresh in-memory SQLite database. They do not verify PostgreSQL or deployment behavior.

## Production-shaped test deployment

Requires Docker Compose, a registered `PUBLIC_HOST` with an A record pointing to this server, the cloud provider's required ICP filing/record for the domain, and inbound TCP 80/443. Install `PUBLIC_HOST` and a random hex-only `DB_PASSWORD` in an untracked `.env`, then run `docker compose up -d --build`. Caddy obtains and renews HTTPS certificates. PostgreSQL has no published host port; the API is reachable only from the proxy and private data network.

Do not open port 8000 or PostgreSQL to the internet. Do not use real health data. After changing environment or network settings, verify `docker compose ps`, `docker compose logs --tail=100 api proxy`, and `https://$PUBLIC_HOST/api/v1/health` before mobile tests. These steps have not been run on the target server.

## Internal server validation before domain readiness

The current user decision is to defer ICP filing and public mobile access. Reserved API hostname: `api.shushu520.top`; preserve the apex domain. Server workspace: `/opt/wellora/server`. Create a mode-600 `.env` on the server with a random database password; do not commit it. Run `docker compose up -d --build db api` to start only the private database and API. Do not start `proxy` in this phase. Neither service publishes a host port.

On a new empty test database, prepare with `docker compose exec -T api python /app/deployment_smoke.py prepare`. This creates 20 fictional accounts, checks concurrent enforcement of the last account slot, profile isolation and optimistic version conflicts, then stores temporary tokens in `/tmp` inside the API container. Restart both services with `docker compose restart api db`; verify with `docker compose exec -T api python /app/deployment_smoke.py verify`, then always clean up with `docker compose exec -T api python /app/deployment_smoke.py cleanup`. Check the DB is empty; keep the private containers and database volume available for the next development step. Record actual exit statuses and results; PostgreSQL checks do not replace the local API suite or future TLS/mobile tests.

`verify` waits up to 30 seconds for `/health` after the container restart before checking persisted records and revoked sessions. This prevents a transient Uvicorn startup delay from being reported as failed persistence. Android instrumentation tests use only random usernames matching `android18_<8 hex>` (optionally suffixed `_a` or `_b`); after testing, run the repository-local `server/tests/cleanup_android_fixtures.py` to remove only those accounts and their cascaded profiles/sessions. The cleanup script is not baked into the API image; from the repository root, stream it to the container with `Get-Content -Raw .\server\tests\cleanup_android_fixtures.py | ssh -i $env:USERPROFILE\.ssh\wellora-backend-root root@SERVER 'docker exec -i server-api-1 python -'`. It also clears only the known management-VPN IP throttle; an unrelated shared tunnel-IP throttle record may remain.

## Observed target-server result (2026-11-10, Asia/Shanghai)

Ubuntu 24.04.4, Docker 29.1.3, Compose 2.40.3, Buildx 0.30.1. API built and runs as UID/GID 10001. PostgreSQL 16.15 migration is at `0001`; Alembic check reports no new operations. Smoke prepare and verify passed, including two-account isolation, stale-version rejection, concurrent 20-account limit, logout revocation and profile/session state after restarting both containers. Cleanup left accounts, profiles, sessions and login_throttles all at zero. Both services remain running privately, with no published host ports. Caddy was not started; HTTPS and Android/mobile tests are pending.

Docker Hub was unreachable from this server. The initial pull failed with a timeout. This run downloaded `docker.m.daocloud.io/library/postgres:16-alpine` and `docker.m.daocloud.io/library/python:3.12-slim-bookworm`, then tagged them locally as `postgres:16-alpine` and `python:3.12-slim-bookworm` before building. No daemon-wide mirror configuration was changed. Observed digests: PostgreSQL `sha256:aa6cb33cf4c19c765cefcf48d96176258800870a9a1e930ad126200f9d825139`, Python `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`. The third-party mirror is only the download path; exact image identities and literal commands/results are recorded in `evidence/transactions/P017-backend/SERVER_VERIFICATION.json`.

## P018 temporary HTTPS mobile test (current choice)

WireGuard was installed but the phone peer never handshook. The user selected an accountless Cloudflare Quick Tunnel for fictional test data only. Container `wellora-quick-tunnel` joins `server_edge` and forwards to `http://api:8000`, publishes no ports, and has restart policy `no`. The temporary HTTPS URL is printed by `docker logs wellora-quick-tunnel`; it may change on restart. No DNS or production release URL changes. Stop with `docker stop wellora-quick-tunnel` after testing. This is a public test URL routed through Cloudflare, not production deployment or a permanent hostname; no real health information or reused credentials. API/database host port exposure is unchanged.

Build the debug APK with `gradlew.bat :app:assembleDebug -PwelloraApiBaseUrl=HTTPS_URL`. Verify HTTPS `/api/v1/health` and run `:app:connectedDebugAndroidTest` with `-Pandroid.testInstrumentationRunnerArguments.wellora.serverTest=true` (quote the whole argument in PowerShell); the opt-in creates reserved fictional `android18_` fixture accounts. Clean these with the existing `cleanup_android_fixtures.py` after testing. Never export session tokens or the server .env.

Observed one-time startup command (existing container name must be free):

```sh
docker run -d --name wellora-quick-tunnel --restart=no --network server_edge --memory=128m --pids-limit=64 docker.m.daocloud.io/cloudflare/cloudflared@sha256:4955524aeaa379e154023d5a027c250f7b35041a2e7e950cf13f144bc9b9c5ba tunnel --no-autoupdate --url http://api:8000
```

The default API proxy trust list was not expanded for Cloudflare. Login IP throttling is shared by tunnel requests at their internal connection IP; this is a small fictional-data test setup, not production rate limiting.

## Follow-up verification (2026-11-13, Asia/Shanghai)

The local API suite passed 15 tests; Alembic SQLite upgrade/check/downgrade/upgrade and Compose configuration validation passed. The deployed PostgreSQL prepare/restart/verify/cleanup scenario passed after the readiness-wait change. The Android HTTPS instrumentation suite passed 12 tests on Medium Phone API 37. Reserved Android fixture accounts were removed; final accounts/profiles/sessions counts were zero, with one unrelated shared IP-throttle row retained. The API and database have no published host ports; the temporary Quick Tunnel remains running for the pending physical-phone test. Full command and result ledger: `evidence/transactions/P017-backend/AUTO_TEST_20261113.json`.
## P021 local health-record API (2026-11-14)

P021 health-record routes and Alembic `0002` are deployed to the private test server. After migration, API health returned 200 and a PostgreSQL smoke passed 16 checks: two fictional accounts, profile ownership, unknown/none/recorded states, idempotent replay/conflict, cursor pages, cross-account 404 and version conflicts. Cleanup left accounts/profiles/sessions/health_records/idempotency_keys at 0. The shared login_throttles table contains one pre-existing row and six zero-failure hashed rows from the test windows; they were retained because the keys cannot be safely attributed to individual requests. The API binds only to the WireGuard host address `10.66.0.1:8000`; PostgreSQL 5432 is not published to a host address. Before deployment, `/opt/wellora/backups/P021-health-records-20261114/app.py`, the migrations directory, and image `wellora/p021-before-health-records:20261114` were preserved. Migration/app checksums and full output are in `evidence/transactions/P021-health-records/VERIFICATION.txt`. Use fictional data only; OSS, OCR, and model providers remain unconfigured.

## P022 private profile files (2026-11-14)


`POST /api/v1/profiles/{profile_id}/files` accepts one multipart `file`; `GET /api/v1/files/{file_id}/content` returns an attachment through the API after checking the owner session. Accepted filename/signature pairs are `.jpg`/`.jpeg` + JPEG, `.png` + PNG, or `.pdf` + PDF. Maximum file body is 20 MiB. Upload returns a file ID, SHA-256, status, and duplicate flag; identical content is deduplicated only within the same profile. Object keys are generated server-side. The API never returns an OSS URL.

Real storage uses `OSS_REGION`, `OSS_ENDPOINT`, `OSS_BUCKET`, `OSS_ACCESS_KEY_ID`, and `OSS_ACCESS_KEY_SECRET` from the server's private environment. The confirmed target is `cn-shanghai` and bucket `oss-pai-nj0fx54125p7y7intd-cn-shanghai`. If credentials are absent, storage is unconfigured and tests inject an in-memory fake. Do not use the previously exposed credential; wait for rotation confirmation. Before any real file traffic, verify bucket-private policy, least-privilege RAM scope, encryption, versioning/deletion and lifecycle settings in Alibaba Cloud. Local tests do not contact OSS. PDF page limits, malware scanning, orphan cleanup, deletion-ledger integration and byte-range downloads are not implemented; do not use real health files yet.

## P023 Hong Kong primary host

Target: existing SSH alias `server1` (`api.shushu520.top` -> `38.76.195.17`, Ubuntu 22.04). Preserve its apex Nginx site, unrelated API on `127.0.0.1:8000`, PostgreSQL 14 and other containers. Deploy Wellora with a distinct Compose project name and PostgreSQL volume; API binds only to `127.0.0.1:8010`, database has no host port. Install the HTTP-01 challenge vhost, issue a certificate specifically for the API subdomain, then enable the HTTPS Nginx vhost. OSS credentials remain omitted; file uploads/downloads fail closed until a fresh least-privilege identity is configured server-side. Use fictional data only.

After revoking the old chat-exposed OSS key, create a fresh least-privilege RAM key and run `powershell -ExecutionPolicy Bypass -File .\server\deploy\configure-hk-oss.ps1` from the repository root. Type uppercase `ROTATED` exactly at the confirmation prompt, then enter only the fresh key; it streams JSON through SSH stdin to a root-owned helper, atomically updates `.env` mode 0600, restarts only the Wellora API, and never echoes secret values. Do not use a key previously disclosed in chat. API account login is username/password, not a static API key. DeepSeek/XFYUN credentials are not yet passed to this API/Compose deployment and should not be entered there.

The API cert uses `/etc/letsencrypt/renewal-hooks/deploy/20-reload-nginx` to reload Nginx after a successful renewal; Certbot's timer and this hook were checked on `server1`. Health remains `https://api.shushu520.top/api/v1/health`. The OSS installer does not retrieve or display credentials; it stores only a newly issued OSS identity after the user confirms revocation of the exposed key.

## P023 Hong Kong primary host

Target: existing SSH alias `server1` (`api.shushu520.top` -> `38.76.195.17`, Ubuntu 22.04). Preserve its apex Nginx site, unrelated API on `127.0.0.1:8000`, PostgreSQL 14 and other containers. Deploy Wellora with a distinct Compose project name and PostgreSQL volume; API binds only to `127.0.0.1:8010`, database has no host port. Install the HTTP-01 challenge vhost, issue a certificate specifically for the API subdomain, then enable the HTTPS Nginx vhost. OSS credentials are stored only in the server-private environment; use fictional data only.

After revoking the old chat-exposed OSS key, create a fresh least-privilege RAM key and run `powershell -ExecutionPolicy Bypass -File .\server\deploy\configure-hk-oss.ps1` from the repository root. Type uppercase `ROTATED` exactly at the confirmation prompt, then enter only the fresh key; it streams JSON through SSH stdin to a root-owned helper, atomically updates `.env` mode 0600, restarts only the Wellora API, and never echoes secret values. Do not use a key previously disclosed in chat. API account login is username/password, not a static API key. DeepSeek/XFYUN credentials are not yet passed to this API/Compose deployment and should not be entered there.

The API cert uses `/etc/letsencrypt/renewal-hooks/deploy/20-reload-nginx` to reload Nginx after a successful renewal; Certbot's timer and this hook were checked on `server1`. Health remains `https://api.shushu520.top/api/v1/health`. The OSS installer does not retrieve or display credentials; it stores only a newly issued OSS identity after the user confirms revocation of the exposed key.

P023 follow-up: the installer completed with masked local prompts and initialized `AliyunObjectStore`. A fictional PNG round trip through the authenticated public API returned upload 201 and download 200 with matching bytes; the exact test object/account were deleted afterward. Read-only bucket checks returned ACL `private`, public access blocking enabled, and no public Allow bucket-policy statements. Versioning was disabled, and no server-side encryption or lifecycle rule was configured. Do not store real health files until encryption and lifecycle/version-deletion retention policy are reviewed and set. If the key entered in the latest run was the AccessKey ID previously posted in chat, revoke that pair and configure a newly generated pair instead.

## P024 provider credentials

From the repository root, run `powershell -ExecutionPolicy Bypass -File .\server\deploy\configure-hk-provider-keys.ps1`. Select `DEEPSEEK`, `XFYUN`, or `BOTH`, then enter freshly issued values only in the local masked prompts. Values travel over SSH stdin to the root-owned helper, are written to the server-private `.env` (0600), and only the Wellora API is recreated. Do not use a credential previously posted in chat. This stores configuration only; provider clients and vendor API requests are not implemented. Confirm model/product IDs, pricing, quotas, request formats and retention before actual provider integration.
