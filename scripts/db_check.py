import sys

from sqlalchemy import text

from app.db.session import Base, engine
from app.models import (  # asegura la importación para que Base conozca los modelos
    Company,
    User,
)


def main() -> None:
    try:
        # crea tablas si no existen (solo para test, luego usaremos Alembic)
        Base.metadata.create_all(bind=engine)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar_one()
            print("Conexión OK →", result)
    except Exception as exc:
        print("Error:", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
