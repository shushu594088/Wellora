FROM python:3.12-slim-bookworm

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.19
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app.py object_store.py alembic.ini ./
COPY migrations ./migrations
COPY tests/deployment_smoke.py ./
RUN useradd --system --uid 10001 --no-create-home wellora
USER 10001:10001

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=172.29.240.2"]
