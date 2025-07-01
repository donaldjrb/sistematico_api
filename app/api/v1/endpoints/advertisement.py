from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# --- INICIO DE CORRECCIÓN ---
# Importamos la dependencia correcta desde TU archivo deps.py
from app.api.deps import get_db, get_current_user
# --- FIN DE CORRECCIÓN ---

from app.models.user import User as UserModel
from app.schemas.advertisement import AdvertisementCreate, AdvertisementOut, AdvertisementUpdate
from app.services.advertisement_service import AdvertisementService

router = APIRouter()

@router.get("/", response_model=List[AdvertisementOut])
def read_all(
    db: Session = Depends(get_db), 
    # Usamos la dependencia que ya existe en tu proyecto
    current_user: UserModel = Depends(get_current_user)
):
    """ Obtiene todos los anuncios de la compañía del usuario autenticado. """
    return AdvertisementService(db).get_all_by_company(company_id=current_user.company_id)

@router.get("/{adv_id}", response_model=AdvertisementOut)
def read_one(
    adv_id: int, 
    db: Session = Depends(get_db), 
    current_user: UserModel = Depends(get_current_user)
):
    """ Obtiene un anuncio específico de la compañía del usuario. """
    adv = AdvertisementService(db).get_by_company(adv_id=adv_id, company_id=current_user.company_id)
    if not adv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Advertisement not found")
    return adv

@router.post("/", response_model=AdvertisementOut, status_code=status.HTTP_201_CREATED)
def create(
    obj_in: AdvertisementCreate, 
    db: Session = Depends(get_db), 
    current_user: UserModel = Depends(get_current_user)
):
    """ Crea un nuevo anuncio para la compañía del usuario. """
    return AdvertisementService(db).create(obj_in=obj_in, company_id=current_user.company_id)

@router.put("/{adv_id}", response_model=AdvertisementOut)
def update(
    adv_id: int, 
    obj_in: AdvertisementUpdate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """ Actualiza un anuncio de la compañía del usuario. """
    upd = AdvertisementService(db).update(adv_id=adv_id, obj_in=obj_in, company_id=current_user.company_id)
    if not upd:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Advertisement not found")
    return upd

@router.delete("/{adv_id}", response_model=dict)
def delete(
    adv_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """ Desactiva (eliminado lógico) un anuncio de la compañía del usuario. """
    # En la API usamos el método DELETE, pero el servicio hace un borrado lógico (is_active = False)
    # Se debe crear un endpoint toggle-status para HTMX como en los otros módulos si se desea esa lógica
    adv_service = AdvertisementService(db)
    ok = adv_service.delete(adv_id=adv_id, company_id=current_user.company_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Advertisement not found")
    return {"detail": "Advertisement deactivated"}