from sqlalchemy.orm import Session

from app.models import Ticket
from app.schemas.ticket import TicketCreate


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Ticket).filter_by(status="esperando").all()

    def get(self, ticket_id: int):
        return self.db.query(Ticket).filter_by(id=ticket_id).first()

    def create(self, obj_in: TicketCreate):
        new_ticket = Ticket(**obj_in.model_dump())
        self.db.add(new_ticket)
        self.db.commit()
        self.db.refresh(new_ticket)
        return new_ticket

    def update(self, ticket_id: int, obj_in: TicketCreate):
        db_obj = self.get(ticket_id)
        if not db_obj:
            return None
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, ticket_id: int):
        db_obj = self.get(ticket_id)
        if not db_obj:
            return None
        db_obj.status = "cerrado"
        self.db.commit()
        return db_obj
