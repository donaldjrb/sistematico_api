from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ticket import TicketCreate, TicketOut
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/", response_model=List[TicketOut])
def read_all(db: Session = Depends(get_db)):
    return TicketService(db).get_all()


@router.get("/{ticket_id}", response_model=TicketOut)
def read_one(ticket_id: int, db: Session = Depends(get_db)):
    ticket = TicketService(db).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(obj_in: TicketCreate, db: Session = Depends(get_db)):
    return TicketService(db).create(obj_in)


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, obj_in: TicketCreate, db: Session = Depends(get_db)):
    updated = TicketService(db).update(ticket_id, obj_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated


@router.delete("/{ticket_id}", response_model=dict)
def close_ticket(ticket_id: int, db: Session = Depends(get_db)):
    deleted = TicketService(db).delete(ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"detail": "Ticket cerrado"}
