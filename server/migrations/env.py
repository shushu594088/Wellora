from alembic import context
from app import Base, engine

if context.is_offline_mode():
    raise RuntimeError("Use an online migration connection; DATABASE_URL is required")

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
