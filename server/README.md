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

## Observed target-server result (2026-11-10, Asia/Shanghai)

Ubuntu 24.04.4, Docker 29.1.3, Compose 2.40.3, Buildx 0.30.1. API built and runs as UID/GID 10001. PostgreSQL 16.15 migration is at `0001`; Alembic check reports no new operations. Smoke prepare and verify passed, including two-account isolation, stale-version rejection, concurrent 20-account limit, logout revocation and profile/session state after restarting both containers. Cleanup left accounts, profiles, sessions and login_throttles all at zero. Both services remain running privately, with no published host ports. Caddy was not started; HTTPS and Android/mobile tests are pending.

Docker Hub was unreachable from this server. The initial pull failed with a timeout. This run downloaded `docker.m.daocloud.io/library/postgres:16-alpine` and `docker.m.daocloud.io/library/python:3.12-slim-bookworm`, then tagged them locally as `postgres:16-alpine` and `python:3.12-slim-bookworm` before building. No daemon-wide mirror configuration was changed. Observed digests: PostgreSQL `sha256:aa6cb33cf4c19c765cefcf48d96176258800870a9a1e930ad126200f9d825139`, Python `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`. The third-party mirror is only the download path; exact image identities and literal commands/results are recorded in `evidence/transactions/P017-backend/SERVER_VERIFICATION.json`.
