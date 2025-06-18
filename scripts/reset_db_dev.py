# ⚠️  Dev-only helper. NEVER run against production.
# reset_db.py

import subprocess

from app.db.base import Base
from app.db.session import engine


def drop_all():
    print("ðŸ’¥ Borrando todas las tablas...")
    Base.metadata.drop_all(bind=engine)
    print("âœ… Tablas eliminadas.")


def upgrade_head():
    print("ðŸš€ Aplicando migraciones con Alembic...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"], capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print("âš ï¸ Errores:", result.stderr)
    else:
        print("âœ… Migraciones aplicadas.")


if __name__ == "__main__":
    drop_all()
    upgrade_head()
