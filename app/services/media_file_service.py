import os
import shutil
from typing import List, Optional
import mimetypes

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.media_file import MediaFile
from app.schemas.media_file import MediaFileCreate, MediaFileUpdate

# Directorio base donde se almacenarán todos los archivos multimedia.
MEDIA_ROOT_DIR = "web/static/media"

class MediaFileService:
    """
    Service layer containing all the business logic for managing media files.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_company(self, media_file_id: int, company_id: int) -> Optional[MediaFile]:
        """
        Retrieves a single media file by its ID, ensuring it belongs to the correct company.
        """
        return self.db.query(MediaFile).filter(
            MediaFile.id == media_file_id,
            MediaFile.company_id == company_id
        ).first()

    def get_all_by_company(self, company_id: int) -> List[MediaFile]:
        """
        Retrieves all media files for a given company.
        """
        return self.db.query(MediaFile).filter(MediaFile.company_id == company_id).order_by(MediaFile.date_create.desc()).all()

    def create_media_file(
        self,
        *,
        file: UploadFile,
        name: str,
        duration_seconds: int,
        company_id: int
    ) -> MediaFile:
        """
        Handles the creation of a new media file. This includes:
        1. Validating the file type.
        2. Creating a company-specific directory if it doesn't exist.
        3. Saving the file to the server's filesystem.
        4. Creating a record in the database.
        """
        # 1. Validar tipo de archivo (MIME type)
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type or not (mime_type.startswith('image/') or mime_type.startswith('video/')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de archivo no soportado. Solo se permiten imágenes y videos."
            )
        
        file_type = "video" if mime_type.startswith('video/') else "image"

        # 2. Crear directorio de la compañía si no existe
        company_media_dir = os.path.join(MEDIA_ROOT_DIR, str(company_id))
        os.makedirs(company_media_dir, exist_ok=True)

        # 3. Guardar el archivo en el servidor
        # Se utiliza un nombre de archivo seguro para evitar colisiones.
        file_path = os.path.join(company_media_dir, file.filename)
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()

        # 4. Crear el registro en la base de datos
        # La URL se guarda como una ruta relativa para ser servida por StaticFiles.
        file_url = f"/static/media/{company_id}/{file.filename}"
        
        db_obj_in = MediaFileCreate(
            name=name,
            file_type=file_type,
            url=file_url,
            duration_seconds=duration_seconds,
            company_id=company_id
        )
        
        db_obj = MediaFile(**db_obj_in.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_status(self, media_file_id: int, status: bool, company_id: int) -> Optional[MediaFile]:
        """
        Toggles the active status of a media file.
        """
        db_obj = self.get_by_company(media_file_id, company_id)
        if not db_obj:
            return None
        
        db_obj.status = status
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_media_file(self, media_file_id: int, company_id: int) -> Optional[MediaFile]:
        """
        Deletes a media file record from the database and its corresponding
        file from the filesystem.
        """
        db_obj = self.get_by_company(media_file_id, company_id)
        if not db_obj:
            return None

        # Eliminar el archivo físico del servidor
        # Se construye la ruta completa al archivo en el sistema de archivos.
        file_system_path = os.path.join("web", db_obj.url.lstrip('/'))
        if os.path.exists(file_system_path):
            os.remove(file_system_path)
        
        # Eliminar el registro de la base de datos
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

