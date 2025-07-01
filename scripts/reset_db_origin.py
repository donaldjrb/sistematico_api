import sys
import os

# ------------------- Configuración de Ruta y Entorno -------------------
# Añadir el directorio raíz del proyecto al sys.path para encontrar el módulo 'app'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Cargar las variables de entorno desde el archivo .env de la raíz del proyecto
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        print(f"Cargando variables de entorno desde: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("ADVERTENCIA: No se encontró el archivo .env.")
except ImportError:
    print("ADVERTENCIA: 'python-dotenv' no está instalado. Asumiendo que las variables de entorno ya existen.")
# ---------------------------------------------------------------------

from sqlalchemy import text
from app.db.session import engine, SessionLocal
# Importamos 'Base' para que SQLAlchemy conozca todas las tablas
from app.db.base import Base 

def reset_database(db_engine):
    """
    Se conecta a la base de datos, obtiene una lista de todas las tablas
    en el orden correcto de dependencia y las vacía usando TRUNCATE.
    """
    # Obtenemos la lista de todas las tablas registradas en SQLAlchemy
    tables = Base.metadata.sorted_tables
    db = SessionLocal()
    
    dialect = db_engine.dialect.name
    print(f"\n--- Detectado dialecto de base de datos: {dialect} ---")
    
    try:
        # Para MySQL, es necesario deshabilitar temporalmente la revisión de claves
        if dialect == "mysql":
            print("--- Deshabilitando revisión de claves foráneas (MySQL) ---")
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))

        # Vaciamos las tablas en el orden inverso de dependencia (de hijas a padres)
        # Esto es más seguro que un orden manual.
        for table in reversed(tables):
            print(f"Borrando datos de la tabla: {table.name}...")
            db.execute(text(f"TRUNCATE TABLE `{table.name}`;"))
        
        db.commit()

    except Exception as e:
        print(f"\n💀 ERROR: Ocurrió un error durante el reseteo: {e}")
        db.rollback()
    finally:
        # Volvemos a habilitar la revisión de claves para mantener la integridad
        if dialect == "mysql":
            print("--- Habilitando revisión de claves foráneas (MySQL) ---")
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.close()
    
    print("\n✅ Reseteo de base de datos completado. Las tablas están vacías y los índices reiniciados.")

if __name__ == "__main__":
    print("Este script borrará TODO el contenido de la base de datos.")
    
    # Paso de confirmación para evitar ejecuciones accidentales
    if "--no-confirm" not in sys.argv:
        confirm = input(
            "⚠️  ADVERTENCIA: ¿Estás seguro de que quieres continuar? (escribe 'si' para confirmar): "
        )
        if confirm.lower() != "si":
            print("Operación cancelada por el usuario.")
            exit()
            
    reset_database(engine)
    