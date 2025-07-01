from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.close_reason import CloseReason
from app.schemas.close_reason import CloseReasonCreate, CloseReasonUpdate

class CloseReasonService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_company(self, company_id: int) -> List[CloseReason]:
        """
        Obtiene todas las razones de cierre filtrando por company_id.
        """
        return self.db.query(CloseReason).filter(CloseReason.company_id == company_id).order_by(CloseReason.reason_text).all()

    def get_by_company(self, reason_id: int, company_id: int) -> Optional[CloseReason]:
        """
        Obtiene una razón de cierre específica, verificando que pertenezca a la company_id.
        """
        return self.db.query(CloseReason).filter(
            CloseReason.id == reason_id, 
            CloseReason.company_id == company_id
        ).first()

    def create(self, obj_in: CloseReasonCreate, company_id: int) -> CloseReason:
        """
        Crea una nueva razón de cierre, asignando la company_id del usuario.
        """
        # Creamos el objeto del modelo con los datos del schema y el company_id
        db_reason = CloseReason(**obj_in.dict(), company_id=company_id, is_active=True)
        self.db.add(db_reason)
        self.db.commit()
        self.db.refresh(db_reason)
        return db_reason

    def update(
        self, reason_id: int, obj_in: CloseReasonUpdate, company_id: int
    ) -> Optional[CloseReason]:
        """
        Actualiza una razón de cierre, verificando primero que pertenezca a la company_id.
        """
        reason = self.get_by_company(reason_id, company_id)
        if not reason:
            return None
        
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(reason, field, value)
            
        self.db.commit()
        self.db.refresh(reason)
        return reason

    def delete(self, reason_id: int, company_id: int) -> bool:
        """
        Realiza un soft-delete (desactiva) una razón de cierre,
        verificando primero que pertenezca a la company_id.
        """
        reason = self.get_by_company(reason_id, company_id)
        if not reason:
            return False
            
        reason.is_active = False
        self.db.commit()
        return True