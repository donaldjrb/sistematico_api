# ⚠️  Dev-only helper. NEVER run against production.
import sys
import os
from datetime import datetime, timezone

# --- INICIO DE CORRECCIÓN DE RUTA Y ENTORNO ---
# Añadir el directorio raíz del proyecto al sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Cargar las variables de entorno desde el archivo .env
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(project_root, '.env')
    if os.path.exists(dotenv_path):
        print(f"Cargando variables de entorno desde: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("ADVERTENCIA: No se encontró el archivo .env. El script asumirá que las variables de entorno están configuradas globalmente.")
except ImportError:
    print("ADVERTENCIA: 'python-dotenv' no está instalado. El script asumirá que las variables de entorno están configuradas globalmente.")
# --- FIN DE CORRECCIÓN DE RUTA Y ENTORNO ---

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import text 

from app.db.session import SessionLocal, engine
from app.models.company import Company
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_database(db: Session, db_engine):
    """
    Borra todos los datos de las tablas y reinicia los contadores de ID.
    """
    models_to_delete = [Ticket, Service, User, Company]
    
    dialect = db_engine.dialect.name
    print(f"--- Detectado dialecto: {dialect} ---")

    try:
        if dialect == "mysql":
            print("--- Deshabilitando revisión de claves foráneas (MySQL) ---")
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        for model in models_to_delete:
            table_name = model.__tablename__
            print(f"Borrando datos de la tabla: {table_name}...")
            if dialect == "postgresql":
                db.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;'))
            else:
                db.execute(text(f"TRUNCATE TABLE {table_name};"))
        
        db.commit()

    finally:
        if dialect == "mysql":
            print("--- Habilitando revisión de claves foráneas (MySQL) ---")
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        print("--- Reseteo de base de datos completado ---")


def run_seed(db: Session):
    """
    Inserta un conjunto de datos iniciales en la base de datos.
    """
    try:
        print("\n--- Iniciando inserción de datos (seeding) ---")
        # 1. Crear empresa
        print("Creando compañía: Sistematico Corp.")
        company = Company(
            name="Sistematico Corp.",
            country="Venezuela",
            tax_id_name="RIF",
            tax_id_value="J-12345678-9",
            address="Av. Intercomunal, Torre 1, Piso 5",
            phone_number="0212-1234567",
            email="contacto@sistematico.com",
            logo_url="https://cdn.sistematico.com/logo.png",
            contact_person="Carlos Rodríguez",
            is_active=True,
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        # 2. Crear usuario admin
        print("Creando usuario: admin@sistematico.com")
        hashed_password = pwd_context.hash("192837Sis*-.")
        admin = User(
            full_name="Admin Principal",
            email="admin@sistematico.com",
            hashed_password=hashed_password,
            role="admin",
            is_active=True,
            company_id=company.id,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        # 3. Crear servicio
        print("Creando servicio: Soporte Técnico")
        service = Service(
            name="Soporte Técnico",
            code="ST",
            location="TECNOLOGIA OFIC-01",
            max_capacity=50,
            priority_level=1,
            is_active=True,
            company_id=company.id,
        )
        db.add(service)
        db.commit()
        db.refresh(service)

        # 4. Crear ticket (estado inicial)
        print("Creando ticket de prueba: ST-0001")
        ticket = Ticket(
            ticket_number="ST-0001",
            priority_level=1,
            status="esperando",
            call_count=0,
            customer_phone="04141234567",
            close_reason_id=None,
            close_notes=None,
            created_at=datetime.now(timezone.utc),
            company_id=company.id,
            service_id=service.id,
        )
        db.add(ticket)

        db.commit()
        print("\n✅ Datos iniciales insertados con éxito.")

    except Exception as e:
        db.rollback()
        print(f"💀 Error durante la inserción de datos: {e}")


if __name__ == "__main__":
    db_session: Session = SessionLocal()
    
    if "--no-confirm" not in sys.argv:
        confirm = input(
            "⚠️  ADVERTENCIA: Estás a punto de borrar TODOS los datos...\n"
            "¿Estás seguro? (escribe 'si' para confirmar): "
        )
        if confirm.lower() != "si":
            print("Operación cancelada.")
            db_session.close()
            exit()

    try:
        reset_database(db_session, engine)
        run_seed(db_session)
    finally:
        db_session.close()