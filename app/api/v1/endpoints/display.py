# app/api/v1/endpoints/display.py
import json
from typing import List, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.advertisement_service import AdvertisementService
from app.models.advertisement import Advertisement

# El router se define sin prefijo aquí. El prefijo se debe añadir
# cuando se incluye este router en app/api/v1/api.py
router = APIRouter()

class ConnectionManager:
    """
    Gestiona las conexiones WebSocket activas.
    Las agrupa por 'company_id' para poder enviar mensajes
    específicos a los displays de cada empresa.
    """
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, company_id: int):
        """Acepta y registra una nueva conexión de un display."""
        await websocket.accept()
        if company_id not in self.active_connections:
            self.active_connections[company_id] = []
        self.active_connections[company_id].append(websocket)
        print(f"Display conectado para compañía {company_id}. Total: {len(self.active_connections[company_id])}")

    def disconnect(self, websocket: WebSocket, company_id: int):
        """Elimina una conexión cuando un display se desconecta."""
        if company_id in self.active_connections and websocket in self.active_connections[company_id]:
            self.active_connections[company_id].remove(websocket)
            print(f"Display desconectado de compañía {company_id}. Restantes: {len(self.active_connections[company_id])}")

    async def broadcast_to_company(self, company_id: int, message: str):
        """Envía un mensaje a todos los displays conectados de una empresa."""
        if company_id in self.active_connections:
            for connection in self.active_connections[company_id]:
                await connection.send_text(message)

# Creamos una instancia global del manager que será usada por la aplicación
manager = ConnectionManager()


# --- INICIO DE CORRECCIÓN QUIRÚRGICA ---
# La ruta del WebSocket ahora solo contiene la parte variable.
# El prefijo completo "/ws/display" debe estar en `api.py`.
@router.websocket("/{company_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: int):
    """
    Endpoint WebSocket al que se conectarán las pantallas de display.
    Mantiene la conexión abierta y la gestiona a través del ConnectionManager.
    """
    await manager.connect(websocket, company_id)
    try:
        while True:
            # Mantenemos la conexión escuchando.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)

# Se cambia la ruta para evitar conflictos y ser más explícita.
@router.get("/get-ads/{company_id}", response_model=list)
async def get_active_advertisements(company_id: int, db: Session = Depends(get_db)):
    """
    Endpoint REST para que el display obtenga la lista inicial de anuncios
    activos y sus archivos multimedia al cargar.
    """
    adv_service = AdvertisementService(db)
    advertisements = adv_service.get_all_by_company(company_id=company_id)
    
    active_ads_data = []
    for ad in advertisements:
        if ad.is_active:
            # Asumiendo que la relación 'media_files' se carga correctamente.
            media = [{"path": mf.file_path, "type": mf.file_type} for mf in ad.media_files]
            active_ads_data.append({
                "description": ad.description,
                "media": media
            })
            
    return active_ads_data
# --- FIN DE CORRECCIÓN QUIRÚRGICA ---