# ⚠️  Dev-only helper. NEVER run against production.
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def run_seed():
    db: Session = SessionLocal()

    try:
        # 1. Crear empresa
        company = Company(
            name="SistemÃ¡tico Corp.",
            country="Venezuela",
            tax_id_name="RIF",
            tax_id_value="J-12345678-9",
            address="Av. Intercomunal, Torre 1, Piso 5",
            phone_number="0212-1234567",
            email="contacto@sistematico.com",
            logo_url="https://cdn.sistematico.com/logo.png",
            contact_person="Carlos RodrÃ­guez",
            is_active=True,
        )
        db.add(company)
        db.commit()
        db.refresh(company)

        # 2. Crear usuario admin
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
        service = Service(
            name="Soporte TÃ©cnico",
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
        print("âœ… Datos iniciales insertados con Ã©xito.")

    except Exception as e:
        db.rollback()
        print("ðŸ’¥ Error durante seed:", e)

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
