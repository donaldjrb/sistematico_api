from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement
from app.schemas.advertisement import AdvertisementCreate, AdvertisementUpdate


class AdvertisementService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_by_company(self, company_id: int) -> List[Advertisement]:
        """ Obtiene todos los anuncios filtrando por company_id. """
        return self.db.query(Advertisement).filter(Advertisement.company_id == company_id).all()

    def get_by_company(self, adv_id: int, company_id: int) -> Optional[Advertisement]:
        """ Obtiene un anuncio específico, verificando que pertenezca a la company_id. """
        return self.db.query(Advertisement).filter(
            Advertisement.id == adv_id, 
            Advertisement.company_id == company_id
        ).first()

    # --- INICIO DE LA CORRECCIÓN QUIRÚRGICA ---
    def create(self, obj_in: AdvertisementCreate) -> Advertisement:
        """ 
        Crea un anuncio a partir de un objeto de schema Pydantic.
        Se espera que el `company_id` ya venga incluido en `obj_in`.
        """
        # Se crea el objeto del modelo SQLAlchemy directamente desde el schema,
        # que ya contiene todos los datos necesarios (incluyendo company_id).
        db_adv = Advertisement(**obj_in.dict())
        self.db.add(db_adv)
        self.db.commit()
        self.db.refresh(db_adv)
        return db_adv
    # --- FIN DE LA CORRECCIÓN QUIRÚRGICA ---

    def update(
        self, adv_id: int, obj_in: AdvertisementUpdate, company_id: int
    ) -> Optional[Advertisement]:
        """ Actualiza un anuncio, verificando primero que pertenezca a la company_id. """
        adv = self.get_by_company(adv_id, company_id) # Usamos el método seguro
        if not adv:
            return None
        
        # Obtenemos los datos del schema de actualización que no son nulos
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(adv, field, value)
            
        self.db.commit()
        self.db.refresh(adv)
        return adv

    def delete(self, adv_id: int, company_id: int) -> bool:
        """ Desactiva un anuncio (eliminado lógico), verificando que pertenezca a la company_id. """
        adv = self.get_by_company(adv_id, company_id) # Usamos el método seguro
        if not adv:
            return False
            
        adv.is_active = False # Eliminado lógico
        self.db.commit()
        return True

