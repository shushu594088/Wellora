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
