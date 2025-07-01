# =====================================================================================
# ||                        SISTEMATICO 1.0.0 - MAIN APPLICATION                       ||
# =====================================================================================

# 1. Agrupación de Imports
# -------------------------------------------------------------------------------------
import os
import json
import re
import shutil
import logging
from typing import Optional
from datetime import datetime

import httpx
from fastapi import (
    FastAPI, Request, Form, Depends,
    status, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
)
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from itsdangerous import URLSafeSerializer, BadSignature, URLSafeTimedSerializer, SignatureExpired

from app.api.v1.api import router as api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.close_reason import CloseReason
from app.models.advertisement import Advertisement
from app.models.media_file import MediaFile
from app.core.security import hash_password
from app.api.v1.endpoints.display import manager as display_manager
from app.schemas.ticket import TicketCreate, TicketDerive
from app.schemas.advertisement import AdvertisementCreate, AdvertisementUpdate
from app.schemas.close_reason import CloseReasonCreate
from app.services.ticket_service import TicketService
from app.services.cashier_service import CashierService
from app.services.advertisement_service import AdvertisementService
from app.services.close_reason_service import CloseReasonService
from app.services.media_file_service import MediaFileService



# 2. Inicialización y Dependencias de la Aplicación
# -------------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
settings = get_settings()
app = FastAPI(title="SISTEMATICO 1.0.0")
SECRET = settings.jwt_secret_key
session_signer = URLSafeSerializer(SECRET, "session")
password_reset_signer = URLSafeTimedSerializer(SECRET, salt="password-reset")

os.makedirs("web/static/logos", exist_ok=True)
os.makedirs("web/static/media", exist_ok=True)
os.makedirs("web/static/sounds", exist_ok=True)

app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_setup_complete_check(db: Session):
    return db.query(Company).first() is not None

def get_current_user(request: Request):
    raw_session = request.cookies.get("session")
    if not raw_session: return None
    try: return session_signer.loads(raw_session)
    except BadSignature: return None

def get_current_admin(user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    return user

def validate_password(password: str):
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[1-9]", password): return False
    if not re.search(r"[!@#$%^&*(),.?_=+;:'-`~]", password): return False
    return True

# Helper para notificar a los displays sobre cambios en la cola
async def notify_queue_update(db: Session, company_id: int):
    """Obtiene la cola de agentes actual y la transmite a los displays."""
    queue_query = db.query(Ticket).join(Service, Ticket.service_id == Service.id).filter(
        Ticket.company_id == company_id,
        or_(
            Ticket.status == 'pagado',
            (Ticket.status == 'derivado') & (Service.requires_payment == False),
            (Ticket.status == 'pendiente_pago') & (Service.requires_payment == False)
        )
    ).order_by(
        Ticket.priority_level.desc(),
        func.coalesce(Ticket.updated_at, Ticket.created_at).asc()
    ).all()
    
    queue_data = [{"id": t.id, "ticket_number": t.ticket_number, "created_at": t.created_at.isoformat()} for t in queue_query]
    
    message = {"event": "queue_update", "data": {"queue": queue_data}}
    await display_manager.broadcast_to_company(company_id=company_id, message=json.dumps(message))



# 3. Rutas Principales de la Aplicación (Setup, Login, Logout)
# -------------------------------------------------------------------------------------

# Ruta raíz: Redirige según el estado de configuración o el rol del usuario
@app.get("/", response_class=HTMLResponse, include_in_schema=False) 
async def root(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)): 
    if not is_setup_complete_check(db=db): 
        return RedirectResponse(url="/setup", status_code=status.HTTP_303_SEE_OTHER) 
    if user: 
        role = user.get("role") 
        if role == "admin": 
            company = db.query(Company).filter(Company.id == user.get("company_id")).first() 
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "company": company}) 
        elif role == "agent": 
            return RedirectResponse(url="/agent", status_code=status.HTTP_303_SEE_OTHER) 
        elif role == "cashier": 
            return RedirectResponse(url="/cashier", status_code=status.HTTP_303_SEE_OTHER) 
        else: 
            return RedirectResponse(url="/agent", status_code=status.HTTP_303_SEE_OTHER) 
    company = db.query(Company).first() 
    return templates.TemplateResponse("login.html", {"request": request, "company": company}) 

# Formulario de configuración inicial
@app.get("/setup", response_class=HTMLResponse, include_in_schema=False) 
async def setup_form(request: Request, db: Session = Depends(get_db)): 
    if is_setup_complete_check(db=db): 
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER) 
    return templates.TemplateResponse("setup.html", {"request": request}) 

# Procesamiento de la configuración inicial
@app.post("/setup", include_in_schema=False) 
async def process_setup(request: Request, db: Session = Depends(get_db), company_name: str = Form(...), country: str = Form(None), contact_person: str = Form(None), tax_id_name: str = Form(None), tax_id_value: str = Form(None), address: str = Form(None), company_email: str = Form(None), phone_number: str = Form(None), logo_file: UploadFile = File(None), admin_full_name: str = Form(...), admin_email: str = Form(...), admin_password: str = Form(...)): 
    if is_setup_complete_check(db): 
        raise HTTPException(status_code=403, detail="El sistema ya ha sido configurado.") 
    if not validate_password(admin_password): 
        return templates.TemplateResponse("setup.html", {"request": request, "error": "La contraseña no cumple los requisitos de seguridad."}) 

    logo_url_path = None 
    if logo_file and logo_file.filename: 
        file_path = f"web/static/logos/{logo_file.filename}"; 
        shutil.copyfileobj(logo_file.file, open(file_path, "wb")); 
        logo_url_path = f"/static/logos/{logo_file.filename}" 

    try: 
        new_company = Company(name=company_name, country=country, contact_person=contact_person, tax_id_name=tax_id_name, tax_id_value=tax_id_value, address=address, email=company_email, phone_number=phone_number, logo_url=logo_url_path, is_active=True); 
        db.add(new_company); 
        db.flush() 
        new_user = User(email=admin_email, hashed_password=hash_password(admin_password), full_name=admin_full_name, role="admin", company_id=new_company.id, is_active=True); 
        db.add(new_user); 
        db.commit(); 
        db.refresh(new_user) 
        return RedirectResponse(url=f"/setup/success?company_id={new_company.id}&user_id={new_user.id}", status_code=status.HTTP_303_SEE_OTHER) 
    except Exception as e: 
        db.rollback(); 
        return templates.TemplateResponse("setup.html", {"request": request, "error": f"Error en la base de datos: {e}"}) 

# Página de éxito de la configuración inicial
@app.get("/setup/success", response_class=HTMLResponse, include_in_schema=False) 
async def setup_success(request: Request, company_id: int, user_id: int, db: Session = Depends(get_db)): 
    company = db.query(Company).filter(Company.id == company_id).first(); 
    user = db.query(User).filter(User.id == user_id).first() 
    if not company or not user: 
        raise HTTPException(status_code=404, detail="Recursos no encontrados.") 
    return templates.TemplateResponse("setup_success.html", {"request": request, "company": company, "user": user}) 

# Procesamiento del inicio de sesión
@app.post("/login", include_in_schema=False) 
async def login(request: Request, email: str = Form(...), password: str = Form(...)): 
    async with httpx.AsyncClient(base_url=str(request.base_url).rstrip("/")) as cli: 
        login_resp = await cli.post("/api/v1/auth/login", data={"username": email, "password": password, "grant_type": "password"}, headers={"Content-Type": "application/x-www-form-urlencoded"}) 
        if login_resp.status_code != 200: 
            error_detail = "Credenciales inválidas. Por favor, intenta de nuevo." 
            company = None 
            db = SessionLocal() 
            try: 
                company = db.query(Company).first() 
            finally: 
                db.close() 
            return templates.TemplateResponse("login.html", {"request": request, "error": error_detail, "email": email, "company": company}) 

        data = login_resp.json() 
        user_data = data.get("user", {}) 
        session_data = { 
            "id": user_data.get("id"), 
            "email": user_data.get("email"), 
            "jwt": data.get("access_token"), 
            "company_id": user_data.get("company_id"), 
            "role": user_data.get("role"), 
            "full_name": user_data.get("full_name"), 
            "service_id": user_data.get("service_id") 
        }
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER) 
        response.set_cookie("session", session_signer.dumps(session_data), max_age=3600, httponly=True, samesite="lax") 
        return response 

# Cierre de sesión del usuario
@app.get("/logout", include_in_schema=False) 
def logout(): 
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER) 
    response.delete_cookie("session") 
    return response 


# 4. Flujo de Reseteo de Contraseña
# -------------------------------------------------------------------------------------

# Muestra el formulario para solicitar el reinicio de contraseña
@app.get("/forgot-password", response_class=HTMLResponse, include_in_schema=False) 
async def forgot_password_form(request: Request): 
    return templates.TemplateResponse("forgot_password.html", {"request": request}) 

# Procesa la solicitud de reinicio de contraseña, genera un token seguro
@app.post("/forgot-password", response_class=HTMLResponse, include_in_schema=False) 
async def process_forgot_password(request: Request, email: str = Form(...), db: Session = Depends(get_db)): 
    user = db.query(User).filter(User.email == email).first() 
    if not user: 
        return templates.TemplateResponse("password_reset_sent.html", {"request": request}) 
    token = password_reset_signer.dumps(user.email, salt="password-reset") 
    reset_url = request.url_for('reset_password_form', token=token) 
    # No se utiliza la sentencia print() ya que es para depuración.
    return templates.TemplateResponse("password_reset_sent.html", {"request": request, "reset_url": reset_url}) 

# Muestra el formulario para establecer una nueva contraseña, validando el token
@app.get("/reset-password/{token}", response_class=HTMLResponse, include_in_schema=False) 
async def reset_password_form(request: Request, token: str): 
    try: 
        email = password_reset_signer.loads(token, salt="password-reset", max_age=3600) 
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token}) 
    except SignatureExpired: 
        return templates.TemplateResponse("error.html", {"request": request, "error_title": "Enlace Expirado", "error_message": "El enlace para reiniciar la contraseña ha expirado. Por favor, solicita uno nuevo."}) 
    except BadSignature: 
        return templates.TemplateResponse("error.html", {"request": request, "error_title": "Enlace Inválido", "error_message": "El enlace para reiniciar la contraseña es inválido o ya ha sido utilizado."}) 

# Procesa el cambio de contraseña, validando el token y la robustez de la clave
@app.post("/reset-password/{token}", response_class=HTMLResponse, include_in_schema=False) 
async def process_reset_password( 
    request: Request, token: str, 
    new_password: str = Form(...), confirm_password: str = Form(...), 
    db: Session = Depends(get_db) 
):
    if new_password != confirm_password: 
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token, "error": "Las contraseñas no coinciden."}) 
    if not validate_password(new_password): 
        return templates.TemplateResponse("reset_password.html", {"request": request, "token": token, "error": "La contraseña no cumple con los requisitos de seguridad."}) 
    try: 
        email = password_reset_signer.loads(token, salt="password-reset", max_age=3600) 
        user = db.query(User).filter(User.email == email).first() 
        if not user: 
            raise HTTPException(status_code=404, detail="Usuario no encontrado.") 
        user.hashed_password = hash_password(new_password) 
        db.commit() 
        return templates.TemplateResponse("login.html", {"request": request, "success": "¡Tu contraseña ha sido actualizada exitosamente! Ya puedes iniciar sesión."}) 
    except (SignatureExpired, BadSignature): 
        return templates.TemplateResponse("error.html", {"request": request, "error_title": "Enlace Inválido o Expirado", "error_message": "No se pudo procesar tu solicitud. Por favor, intenta de nuevo."}) 


# 5. Rutas del Panel de Administración
# -------------------------------------------------------------------------------------

# 5.1. Panel de Inicio
# -------------------------------------------------------------------------------------
@app.get("/admin/home", response_class=HTMLResponse) 
async def get_home_panel(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    company = db.query(Company).filter(Company.id == admin.get("company_id")).first() 
    if not company: 
        raise HTTPException(status_code=404, detail="Compañía no encontrada.") 
    return templates.TemplateResponse("partials/admin/home_panel.html", {"request": request, "company": company}) 

# 5.2. Módulo de Usuarios
# -------------------------------------------------------------------------------------
@app.get("/admin/users", response_class=HTMLResponse) 
async def get_users_panel(request: Request, admin: dict = Depends(get_current_admin)): 
    return templates.TemplateResponse("partials/admin/users_panel.html", {"request": request}) 

@app.get("/admin/users/table", response_class=HTMLResponse) 
async def get_users_table(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    current_admin_email = admin.get("email") 
    other_users = db.query(User).filter(User.company_id == admin.get("company_id"), User.email != current_admin_email).order_by(User.full_name).all() 
    return templates.TemplateResponse("partials/admin/_users_table.html", {"request": request, "users": other_users}) 

@app.get("/admin/users/add-form", response_class=HTMLResponse) 
async def get_user_add_form(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    # Obtiene la lista de servicios para el formulario de usuario
    services = db.query(Service).filter(Service.company_id == admin.get("company_id")).order_by(Service.name).all() 
    return templates.TemplateResponse("partials/admin/user_form.html", {"request": request, "user": None, "services": services}) 

@app.get("/admin/users/{user_id}/edit-form", response_class=HTMLResponse) 
async def get_user_edit_form(user_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    user_to_edit = db.query(User).filter(User.id == user_id, User.company_id == admin.get("company_id")).first() 
    if not user_to_edit: 
        raise HTTPException(status_code=404, detail="Usuario no encontrado") 
    # Obtiene la lista de servicios para el formulario de edición de usuario
    services = db.query(Service).filter(Service.company_id == admin.get("company_id")).order_by(Service.name).all() 
    return templates.TemplateResponse("partials/admin/user_form.html", {"request": request, "user": user_to_edit, "services": services}) 

@app.get("/admin/users/{user_id}/confirm-toggle", response_class=HTMLResponse) 
async def get_user_toggle_confirmation(user_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    user_to_toggle = db.query(User).filter(User.id == user_id, User.company_id == admin.get("company_id")).first() 
    if not user_to_toggle: 
        raise HTTPException(status_code=404, detail="Usuario no encontrado") 
    return templates.TemplateResponse("partials/admin/_user_confirm_dialog.html", {"request": request, "user": user_to_toggle}) 

@app.post("/admin/users", response_class=Response)
async def create_user(
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    full_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    role: str = Form(...),
    service_id: str = Form(None)
):
    if db.query(User).filter(User.email == email, User.company_id == admin.get("company_id")).first():
        raise HTTPException(status_code=400, detail="El correo ya está en uso.")
    if not validate_password(password):
        raise HTTPException(status_code=400, detail="La contraseña no cumple los requisitos.")
    
    # Se convierte el service_id a entero de forma segura, tratando "" como None.
    try:
        user_service_id = int(service_id) if service_id and service_id.isdigit() else None
    except (ValueError, TypeError):
        user_service_id = None
    
    final_service_id = user_service_id if role == 'agent' else None
    
    new_user = User(
        full_name=full_name, 
        email=email, 
        hashed_password=hash_password(password), 
        role=role, 
        company_id=admin.get("company_id"), 
        is_active=True,
        service_id=final_service_id
    )
    db.add(new_user); db.commit()
    headers = {"HX-Trigger": json.dumps({"refreshList": None, "closeModal": None})}
    return Response(status_code=204, headers=headers)

@app.post("/admin/users/{user_id}", response_class=Response)
async def update_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    full_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(None), 
    role: str = Form(...),
    service_id: str = Form(None)
):
    user_to_update = db.query(User).filter(User.id == user_id, User.company_id == admin.get("company_id")).first()
    if not user_to_update: raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user_to_update.full_name = full_name
    user_to_update.email = email
    user_to_update.role = role
    
    # Se convierte el service_id a entero de forma segura, tratando "" como None.
    try:
        user_service_id = int(service_id) if service_id and service_id.isdigit() else None
    except (ValueError, TypeError):
        user_service_id = None
    
    user_to_update.service_id = user_service_id if role == 'agent' else None
    
    if password:
        if not validate_password(password): raise HTTPException(status_code=400, detail="La nueva contraseña no cumple los requisitos.")
        user_to_update.hashed_password = hash_password(password)
    db.commit()
    headers = {"HX-Trigger": json.dumps({"refreshList": None, "closeModal": None})}
    return Response(status_code=204, headers=headers) 

@app.post("/admin/users/{user_id}/toggle-status", response_class=Response) 
async def toggle_user_status(user_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    user_to_toggle = db.query(User).filter(User.id == user_id, User.company_id == admin.get("company_id")).first() 
    if not user_to_toggle: 
        raise HTTPException(status_code=404, detail="Usuario no encontrado") 
    if user_to_toggle.email == admin.get("email"): 
        raise HTTPException(status_code=403, detail="No puedes cambiar tu propio estado.") 
    user_to_toggle.is_active = not user_to_toggle.is_active 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

# 5.3. Módulo de "Mi Cuenta"
# -------------------------------------------------------------------------------------
@app.get("/admin/account", response_class=HTMLResponse) 
async def get_my_account_form(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    user_account = db.query(User).filter(User.email == admin.get("email")).first() 
    return templates.TemplateResponse("partials/admin/my_account_form.html", {"request": request, "user": user_account}) 

@app.post("/admin/account", response_class=Response) 
async def update_my_account(request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin), full_name: str = Form(...), password: str = Form(None)): 
    user_to_update = db.query(User).filter(User.email == admin.get("email")).first() 
    user_to_update.full_name = full_name 
    if password: 
        if not validate_password(password): 
            raise HTTPException(status_code=400, detail="La nueva contraseña no cumple los requisitos.") 
        user_to_update.hashed_password = hash_password(password) 
    db.commit() 
    updated_session_data = admin.copy() 
    updated_session_data['full_name'] = full_name 
    response = Response(status_code=200, headers={"HX-Refresh": "true"}) 
    response.set_cookie("session", session_signer.dumps(updated_session_data), max_age=3600, httponly=True, samesite="lax") 
    return response 

# 5.4. Módulo de Compañía
# -------------------------------------------------------------------------------------
@app.get("/admin/company/edit-form", response_class=HTMLResponse) 
async def get_company_edit_form(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    company = db.query(Company).filter(Company.id == admin.get("company_id")).first() 
    if not company: 
        raise HTTPException(status_code=404, detail="Compañía no encontrada.") 
    return templates.TemplateResponse("partials/admin/company_form.html", {"request": request, "company": company}) 

@app.post("/admin/company", response_class=Response) 
async def update_company_info(db: Session = Depends(get_db), admin: dict = Depends(get_current_admin), name: str = Form(...), contact_person: str = Form(None), email: str = Form(None), phone_number: str = Form(None), address: str = Form(None), tax_id_name: str = Form(None), tax_id_value: str = Form(None)): # [42, 43]
    company_to_update = db.query(Company).filter(Company.id == admin.get("company_id")).first() 
    if not company_to_update: 
        raise HTTPException(status_code=404, detail="Compañía no encontrada.") 
    company_to_update.name, company_to_update.contact_person, company_to_update.email, company_to_update.phone_number, company_to_update.address, company_to_update.tax_id_name, company_to_update.tax_id_value = name, contact_person, email, phone_number, address, tax_id_name, tax_id_value 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshHomePanel": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

# 5.5. Módulo de Servicios
# -------------------------------------------------------------------------------------
@app.get("/admin/services", response_class=HTMLResponse) 
async def get_services_list(request: Request, admin: dict = Depends(get_current_admin)): 
    """Devuelve el panel principal para la gestión de servicios."""
    return templates.TemplateResponse("partials/admin/services_panel.html", {"request": request}) 

@app.get("/admin/services/table", response_class=HTMLResponse) 
async def get_services_table(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    """Devuelve la tabla de servicios para ser inyectada con HTMX."""
    company_id = admin.get("company_id") 
    services = db.query(Service).filter(Service.company_id == company_id).order_by(Service.name).all() 
    return templates.TemplateResponse("partials/admin/_services_table.html", {"request": request, "services": services}) 

@app.get("/admin/services/add-form", response_class=HTMLResponse) 
async def get_service_add_form(request: Request, admin: dict = Depends(get_current_admin)): 
    """Devuelve el formulario para añadir un nuevo servicio."""
    return templates.TemplateResponse("partials/admin/service_form.html", {"request": request, "service": None}) 

@app.get("/admin/services/{service_id}/edit-form", response_class=HTMLResponse) 
async def get_service_edit_form(service_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    """Devuelve el formulario para editar un servicio existente."""
    service = db.query(Service).filter(Service.id == service_id, Service.company_id == admin.get("company_id")).first() 
    if not service: 
        raise HTTPException(status_code=404, detail="Servicio no encontrado.") 
    return templates.TemplateResponse("partials/admin/service_form.html", {"request": request, "service": service}) 

@app.get("/admin/services/{service_id}/confirm-toggle", response_class=HTMLResponse) 
async def get_service_toggle_confirmation(service_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    """Devuelve el diálogo de confirmación para activar/desactivar un servicio."""
    service = db.query(Service).filter(Service.id == service_id, Service.company_id == admin.get("company_id")).first() 
    if not service: 
        raise HTTPException(status_code=404, detail="Servicio no encontrado.") 
    return templates.TemplateResponse("partials/admin/_service_confirm_dialog.html", {"request": request, "service": service}) 

@app.post("/admin/services", response_class=Response) 
async def create_service( 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    name: str = Form(...), 
    code: str = Form(...), 
    location: str = Form(...), 
    max_capacity: int = Form(0), 
    priority_level: int = Form(0), 
    requires_payment: bool = Form(False) 
):
    """Procesa la creación de un nuevo servicio con todos los campos."""
    company_id = admin.get("company_id") 
    existing_service = db.query(Service).filter(Service.company_id == company_id, Service.code == code).first() 
    if existing_service: 
        raise HTTPException(status_code=400, detail=f"El código de servicio '{code}' ya está en uso.") 
    new_service = Service( 
        name=name, 
        code=code, 
        location=location, 
        max_capacity=max_capacity, 
        priority_level=priority_level, 
        company_id=company_id, 
        requires_payment=requires_payment 
    )
    db.add(new_service); 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshServiceList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

@app.post("/admin/services/{service_id}", response_class=Response) 
async def update_service( 
    service_id: int, 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    name: str = Form(...), 
    code: str = Form(...), 
    location: str = Form(...), 
    max_capacity: int = Form(0), 
    priority_level: int = Form(0), 
    requires_payment: bool = Form(False) 
):
    """Procesa la actualización de un servicio existente."""
    company_id = admin.get("company_id") 
    service_to_update = db.query(Service).filter(Service.id == service_id, Service.company_id == company_id).first() 
    if not service_to_update: 
        raise HTTPException(status_code=404, detail="Servicio no encontrado.") 
    existing_service = db.query(Service).filter(Service.company_id == company_id, Service.code == code, Service.id != service_id).first() 
    if existing_service: 
        raise HTTPException(status_code=400, detail=f"El código de servicio '{code}' ya está en uso por otro servicio.") 
    service_to_update.name = name 
    service_to_update.code = code 
    service_to_update.location = location 
    service_to_update.max_capacity = max_capacity 
    service_to_update.priority_level = priority_level 
    service_to_update.requires_payment = requires_payment 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshServiceList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

@app.post("/admin/services/{service_id}/toggle-status", response_class=Response) 
async def toggle_service_status(service_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    """Cambia el estado (activo/inactivo) de un servicio."""
    service = db.query(Service).filter(Service.id == service_id, Service.company_id == admin.get("company_id")).first() 
    if not service: 
        raise HTTPException(status_code=404, detail="Servicio no encontrado.") 
    service.is_active = not service.is_active 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshServiceList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 


# 6. Rutas de Paneles de Operación (Caja y Agente)
# -------------------------------------------------------------------------------------

# Dependencia para proteger rutas que requieren un rol de operación (admin, agent, cashier)
def get_current_agent(user: dict = Depends(get_current_user)): 
    if not user or user.get("role") not in ["admin", "agent", "cashier"]: 
        raise HTTPException( 
            status_code=status.HTTP_303_SEE_OTHER, 
            headers={"Location": "/"}, 
        )
    return user 

# 6.1 Rutas para la Interfaz de Caja
# -------------------------------------------------------------------------------------
def get_current_agent(user: dict = Depends(get_current_user)):
    if not user or user.get("role") not in ["admin", "agent", "cashier"]:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/"})
    return user

# 6.1. Lógica de Caja
@app.get("/cashier", response_class=HTMLResponse, include_in_schema=False)
async def get_cashier_dashboard(request: Request, agent: dict = Depends(get_current_agent), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == agent.get("company_id")).first()
    return templates.TemplateResponse("cashier_dashboard.html", {"request": request, "user": agent, "company": company})

@app.get("/ui/cashier/table", response_class=HTMLResponse, include_in_schema=False)
async def get_cashier_table(request: Request, agent: dict = Depends(get_current_agent), db: Session = Depends(get_db)):
    company_id = agent.get("company_id")
    tickets_in_cashier_queue = db.query(Ticket).filter(
        Ticket.company_id == company_id,
        Ticket.status == 'pendiente_pago'
    ).order_by(
        Ticket.priority_level.desc(),
        func.coalesce(Ticket.updated_at, Ticket.created_at).asc()
    ).all()
    return templates.TemplateResponse("partials/cashier/_cashier_table.html", {"request": request, "tickets": tickets_in_cashier_queue})

@app.post("/ui/cashier/tickets/{ticket_id}/process-payment", response_class=Response, include_in_schema=False)
async def process_cashier_payment_ui(request: Request, ticket_id: int, db: Session = Depends(get_db), agent: dict = Depends(get_current_agent)):
    company_id = agent.get("company_id")
    user_id = agent.get("id")
    cashier_service = CashierService(db)
    try:
        cashier_service.process_payment(ticket_id, user_id, company_id)
        await notify_queue_update(db, company_id) # Notificar al display
        return Response(status_code=200)
    except HTTPException as e:
        headers = {"HX-Trigger": json.dumps({"showNotification": {"text": e.detail, "type": "error"}})}
        return Response(content="", status_code=400, headers=headers)


# -------------------------------------------------------------------------------------
# 6.2.1. Funciones Auxiliares (Helpers)
# -------------------------------------------------------------------------------------

def _get_next_ticket_for_agent(
    db: Session,
    company_id: int,
    service_id: int,
    exclude_ticket_id: Optional[int] = None
) -> Optional[Ticket]:
    """
    Encapsula la lógica de negocio para obtener el siguiente ticket prioritario de una cola.
    Utiliza la consulta SQL validada que une con la tabla de servicios.
    """
    query = db.query(Ticket).join(Service, Ticket.service_id == Service.id).filter(
        Ticket.company_id == company_id,
        Ticket.service_id == service_id,
        (
            (Ticket.status == 'pagado') |
            (Ticket.status == 'derivado') & (Service.requires_payment == False) |
            (Ticket.status == 'pendiente_pago') & (Service.requires_payment == False)
        )
    )
    
    if exclude_ticket_id:
        query = query.filter(Ticket.id != exclude_ticket_id)
        
    return query.order_by(
        Ticket.priority_level.desc(),
        func.coalesce(Ticket.updated_at, Ticket.created_at).asc()
    ).first()

def _render_agent_panel(
    request: Request,
    db: Session,
    agent: dict,
    ticket_to_display: Optional[Ticket]
) -> HTMLResponse:
    """
    Renderiza el parcial _agent_ticket_panel.html de forma consistente.
    Centraliza la obtención de datos necesarios para los formularios (servicios, motivos de cierre).
    """
    company_id = agent.get("company_id")
    agent_service_id = agent.get("service_id")
    
    available_services = db.query(Service).filter(
        Service.company_id == company_id,
        Service.is_active == True,
        Service.id != agent_service_id
    ).order_by(Service.name).all()

    close_reasons = db.query(CloseReason).filter(
        CloseReason.company_id == company_id,
        CloseReason.is_active == True
    ).order_by(CloseReason.reason_text).all()

    return templates.TemplateResponse("partials/agent/_agent_ticket_panel.html", {
        "request": request,
        "ticket": ticket_to_display,
        "available_services": available_services,
        "close_reasons": close_reasons
    })

# -------------------------------------------------------------------------------------
# 6.2.2. Rutas Principales y de Acción del Agente
# -------------------------------------------------------------------------------------

def _get_next_ticket_for_agent(db: Session, company_id: int, service_id: int, exclude_ticket_id: Optional[int] = None) -> Optional[Ticket]:
    query = db.query(Ticket).join(Service, Ticket.service_id == Service.id).filter(
        Ticket.company_id == company_id,
        Ticket.service_id == service_id,
        or_(
            Ticket.status == 'pagado',
            (Ticket.status == 'derivado') & (Service.requires_payment == False),
            (Ticket.status == 'pendiente_pago') & (Service.requires_payment == False)
        )
    )
    if exclude_ticket_id:
        query = query.filter(Ticket.id != exclude_ticket_id)
    return query.order_by(Ticket.priority_level.desc(), func.coalesce(Ticket.updated_at, Ticket.created_at).asc()).first()

def _render_agent_panel(request: Request, db: Session, agent: dict, ticket_to_display: Optional[Ticket]) -> HTMLResponse:
    company_id = agent.get("company_id")
    agent_service_id = agent.get("service_id")
    available_services = db.query(Service).filter(Service.company_id == company_id, Service.is_active == True, Service.id != agent_service_id).order_by(Service.name).all()
    close_reasons = db.query(CloseReason).filter(CloseReason.company_id == company_id, CloseReason.is_active == True).order_by(CloseReason.reason_text).all()
    return templates.TemplateResponse("partials/agent/_agent_ticket_panel.html", {"request": request, "ticket": ticket_to_display, "available_services": available_services, "close_reasons": close_reasons})

@app.get("/agent", response_class=HTMLResponse, include_in_schema=False)
async def get_agent_dashboard(request: Request, agent: dict = Depends(get_current_agent), db: Session = Depends(get_db)):
    company_id = agent.get("company_id")
    if not company_id:
        response = templates.TemplateResponse("login.html", {"request": request, "error": "Error de sesión. Inicie sesión nuevamente."}); response.delete_cookie("session"); return response
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        response = templates.TemplateResponse("login.html", {"request": request, "error": "Compañía no encontrada. Inicie sesión nuevamente."}); response.delete_cookie("session"); return response
    return templates.TemplateResponse("agent_dashboard.html", {"request": request, "user": agent, "company": company})

@app.get("/agent/next-ticket", response_class=HTMLResponse, include_in_schema=False)
async def get_agent_next_ticket_route(request: Request, agent: dict = Depends(get_current_agent), db: Session = Depends(get_db)):
    agent_service_id = agent.get("service_id")
    if not agent_service_id: return _render_agent_panel(request, db, agent, None)
    next_ticket = _get_next_ticket_for_agent(db, agent.get("company_id"), agent_service_id)
    return _render_agent_panel(request, db, agent, next_ticket)

@app.post("/agent/tickets/{ticket_id}/call", response_class=HTMLResponse, include_in_schema=False)
async def call_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db), agent: dict = Depends(get_current_agent)):
    company_id = agent.get("company_id")
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.company_id == company_id).first()
    if not ticket: raise HTTPException(status_code=404, detail="Ticket no encontrado")
    ticket.call_count += 1; ticket.status = "atendiendo"; ticket.attended_by_id = agent.get("id"); ticket.updated_at = datetime.now()
    db.commit(); db.refresh(ticket)
    call_message = {"event": "new_call", "data": {"ticket_number": ticket.ticket_number, "location": ticket.service.location if ticket.service else "N/A"}}
    await display_manager.broadcast_to_company(company_id=company_id, message=json.dumps(call_message))
    await notify_queue_update(db, company_id)
    return _render_agent_panel(request, db, agent, ticket)

@app.post("/agent/tickets/{ticket_id}/skip", response_class=HTMLResponse, include_in_schema=False)
async def skip_ticket(request: Request, ticket_id: int, db: Session = Depends(get_db), agent: dict = Depends(get_current_agent)):
    company_id = agent.get("company_id"); agent_service_id = agent.get("service_id")
    ticket_to_skip = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.company_id == company_id).first()
    if ticket_to_skip:
        ticket_to_skip.status = 'pagado'; ticket_to_skip.call_count = 0; ticket_to_skip.attended_by_id = None
        db.commit()
        await notify_queue_update(db, company_id)
    next_ticket = _get_next_ticket_for_agent(db, company_id, agent_service_id, exclude_ticket_id=ticket_id)
    return _render_agent_panel(request, db, agent, next_ticket)

@app.post("/agent/tickets/{ticket_id}/derive", response_class=HTMLResponse, include_in_schema=False)
async def derive_ticket(request: Request, ticket_id: int, new_service_id: int = Form(...), db: Session = Depends(get_db), agent: dict = Depends(get_current_agent)):
    company_id = agent.get("company_id"); agent_service_id = agent.get("service_id")
    ticket_to_derive = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.company_id == company_id).first()
    if not ticket_to_derive: raise HTTPException(status_code=404, detail="Ticket a derivar no encontrado")
    new_service = db.query(Service).filter(Service.id == new_service_id, Service.company_id == company_id).first()
    if not new_service: raise HTTPException(status_code=404, detail="Servicio de destino no encontrado")
    ticket_to_derive.status = 'pendiente_pago' if new_service.requires_payment else 'derivado'
    ticket_to_derive.service_id = new_service_id; ticket_to_derive.priority_level = 10; ticket_to_derive.updated_at = datetime.now()
    db.commit()
    await notify_queue_update(db, company_id)
    next_ticket = _get_next_ticket_for_agent(db, company_id, agent_service_id)
    return _render_agent_panel(request, db, agent, next_ticket)

@app.post("/agent/tickets/{ticket_id}/close", response_class=HTMLResponse, include_in_schema=False)
async def close_ticket(request: Request, ticket_id: int, close_reason_id: int = Form(...), close_notes: Optional[str] = Form(None), db: Session = Depends(get_db), agent: dict = Depends(get_current_agent)):
    company_id = agent.get("company_id"); agent_service_id = agent.get("service_id")
    ticket_to_close = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.company_id == company_id).first()
    if not ticket_to_close: raise HTTPException(status_code=404, detail="Ticket a cerrar no encontrado")
    ticket_to_close.status = "finalizado"; ticket_to_close.close_reason_id = close_reason_id; ticket_to_close.close_notes = close_notes; ticket_to_close.attended_by_id = agent.get("id"); ticket_to_close.updated_at = datetime.now()
    db.commit()
    await notify_queue_update(db, company_id)
    next_ticket = _get_next_ticket_for_agent(db, company_id, agent_service_id)
    return _render_agent_panel(request, db, agent, next_ticket)


# 6.3 Rutas para el Kiosko Público
# -------------------------------------------------------------------------------------
@app.get("/kiosk/{company_id}", response_class=HTMLResponse, include_in_schema=False) 
async def get_kiosk_view(request: Request, company_id: int, db: Session = Depends(get_db)): 
    """Muestra la página principal del kiosko de autoservicio."""
    company = db.query(Company).filter(Company.id == company_id).first() 
    if not company: 
        raise HTTPException(status_code=404, detail="Compañía no encontrada") 

    services = db.query(Service).filter( 
        Service.company_id == company_id, 
        Service.is_active == True 
    ).order_by(Service.name).all() 

    return templates.TemplateResponse("kiosk.html", { 
        "request": request, 
        "company": company, 
        "services": services, 
        "now": datetime.now 
    })

@app.post("/kiosk/{company_id}/generate-ticket", response_class=HTMLResponse, include_in_schema=False) 
async def process_kiosk_ticket_generation( 
    request: Request, 
    company_id: int, 
    db: Session = Depends(get_db), 
    service_id: int = Form(...) 
):
    """
    Gestiona la creación de un ticket desde el kiosko y devuelve el HTML con el resultado.
    Siempre devuelve un fragmento de HTML renderizable.
    """
    company = db.query(Company).filter(Company.id == company_id).first() 
    ticket_service = TicketService(db) 
    ticket_data = TicketCreate(service_id=service_id) 
    try: 
        new_ticket = ticket_service.create(obj_in=ticket_data, company_id=company_id) 
        return templates.TemplateResponse("partials/kiosk/_kiosk_ticket_result.html", { 
            "request": request, 
            "ticket": new_ticket, 
            "company": company 
        })
    except HTTPException as e: 
        return templates.TemplateResponse("partials/kiosk/_kiosk_error.html", { 
            "request": request, 
            "company_id": company_id, 
            "error_message": e.detail 
        })
    except Exception as e: 
        # Se eliminaron las sentencias print() de depuración.
        return templates.TemplateResponse("partials/kiosk/_kiosk_error.html", { 
            "request": request, 
            "company_id": company_id, 
            "error_message": "Ocurrió un error inesperado. Por favor, intente de nuevo." 
        })


# 7. Módulo de Publicidad
# -------------------------------------------------------------------------------------
@app.get("/admin/advertisements", response_class=HTMLResponse) 
async def get_advertisements_panel(request: Request, admin: dict = Depends(get_current_admin)): 
    """Devuelve el panel principal para la gestión de publicidad."""
    return templates.TemplateResponse("partials/admin/advertisements_panel.html", {"request": request}) 

@app.get("/admin/advertisements/table", response_class=HTMLResponse) 
async def get_advertisements_table(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    """Devuelve la tabla de anuncios para ser inyectada con HTMX."""
    company_id = admin.get("company_id") 
    advertisements = AdvertisementService(db).get_all_by_company(company_id=company_id) 
    return templates.TemplateResponse("partials/admin/_advertisements_table.html", {"request": request, "advertisements": advertisements}) 

@app.get("/admin/advertisements/add-form", response_class=HTMLResponse) 
async def get_advertisement_add_form(request: Request, admin: dict = Depends(get_current_admin)): 
    """Devuelve el formulario para añadir un nuevo anuncio."""
    return templates.TemplateResponse("partials/admin/advertisement_form.html", {"request": request, "advertisement": None}) 

@app.get("/admin/advertisements/{adv_id}/edit-form", response_class=HTMLResponse) 
async def get_advertisement_edit_form(adv_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    """Devuelve el formulario para editar un anuncio existente."""
    adv = AdvertisementService(db).get_by_company(adv_id=adv_id, company_id=admin.get("company_id")) 
    if not adv: 
        raise HTTPException(status_code=404, detail="Anuncio no encontrado.") 
    return templates.TemplateResponse("partials/admin/advertisement_form.html", {"request": request, "advertisement": adv}) 

@app.get("/admin/advertisements/{adv_id}/confirm-toggle", response_class=HTMLResponse) 
async def get_advertisement_toggle_confirmation(adv_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    """Devuelve el diálogo de confirmación para activar/desactivar un anuncio."""
    adv = AdvertisementService(db).get_by_company(adv_id=adv_id, company_id=admin.get("company_id")) 
    if not adv: 
        raise HTTPException(status_code=404, detail="Anuncio no encontrado.") 
    return templates.TemplateResponse("partials/admin/_advertisement_confirm_dialog.html", {"request": request, "advertisement": adv}) 

@app.post("/admin/advertisements", response_class=Response) 
async def create_advertisement( 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    description: str = Form(...) 
):
    """Procesa la creación de un nuevo anuncio."""
    adv_in = AdvertisementCreate(description=description, company_id=admin.get("company_id")) 
    AdvertisementService(db).create(obj_in=adv_in) 
    headers = {"HX-Trigger": json.dumps({"refreshAdvList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

@app.post("/admin/advertisements/{adv_id}", response_class=Response) 
async def update_advertisement( 
    adv_id: int, 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    description: str = Form(...) 
):
    """Procesa la actualización de un anuncio existente."""
    adv_in = AdvertisementUpdate(description=description) 
    updated_adv = AdvertisementService(db).update(adv_id=adv_id, obj_in=adv_in, company_id=admin.get("company_id")) 
    if not updated_adv: 
        raise HTTPException(status_code=404, detail="Anuncio no encontrado.") 
    headers = {"HX-Trigger": json.dumps({"refreshAdvList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

@app.post("/admin/advertisements/{adv_id}/toggle-status", response_class=Response) 
async def toggle_advertisement_status(adv_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    """Cambia el estado (activo/inactivo) de un anuncio."""
    adv_service = AdvertisementService(db) 
    adv = adv_service.get_by_company(adv_id=adv_id, company_id=admin.get("company_id")) 
    if not adv: 
        raise HTTPException(status_code=404, detail="Anuncio no encontrado.") 
    update_data = AdvertisementUpdate(is_active=not adv.is_active) 
    adv_service.update(adv_id=adv_id, obj_in=update_data, company_id=admin.get("company_id")) 
    headers = {"HX-Trigger": json.dumps({"refreshAdvList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

# 7.1 Módulo de Gestión Multimedia
# -------------------------------------------------------------------------------------
# Esta sección contiene las rutas que sirven la interfaz de usuario (UI)

@app.get("/admin/media-files", response_class=HTMLResponse)
async def get_media_files_panel(request: Request, admin: dict = Depends(get_current_admin)):
    """
    Devuelve el panel principal para la gestión de multimedia.
    """
    return templates.TemplateResponse("partials/admin/media_files_panel.html", {"request": request})

@app.get("/admin/media-files/gallery", response_class=HTMLResponse)
async def get_media_files_gallery(request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)):
    """
    Devuelve la galería de archivos multimedia para ser inyectada con HTMX.
    """
    company_id = admin.get("company_id")
    media_files = MediaFileService(db).get_all_by_company(company_id)
    return templates.TemplateResponse("partials/admin/_media_files_gallery.html", {"request": request, "media_files": media_files})

@app.get("/admin/media-files/add-form", response_class=HTMLResponse)
async def get_media_file_add_form(request: Request, admin: dict = Depends(get_current_admin)):
    """
    Devuelve el formulario para añadir un nuevo archivo multimedia.
    """
    return templates.TemplateResponse("partials/admin/media_file_form.html", {"request": request})

@app.post("/admin/media-files/upload", response_class=Response)
async def handle_media_file_upload(
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
    name: str = Form(...),
    duration_seconds: int = Form(10),
    file: UploadFile = File(...)
):
    """
    Procesa la subida de un nuevo archivo multimedia.
    """
    company_id = admin.get("company_id")
    service = MediaFileService(db)
    try:
        service.create_media_file(
            file=file,
            name=name,
            duration_seconds=duration_seconds,
            company_id=company_id
        )
        # Devuelve una respuesta que dispara el refresco de la galería
        headers = {"HX-Trigger": "refreshMediaGallery"}
        return Response(status_code=204, headers=headers)
    except HTTPException as e:
        # En caso de error, se podría notificar al usuario
        raise e

@app.post("/admin/media-files/{media_file_id}/toggle-status", response_class=Response)
async def toggle_media_file_status_ui(
    media_file_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """
    Cambia el estado de un archivo multimedia y refresca la galería.
    """
    company_id = admin.get("company_id")
    service = MediaFileService(db)
    current_file = service.get_by_company(media_file_id, company_id)
    if not current_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    
    service.update_status(media_file_id, not current_file.status, company_id)
    
    # Refresca la galería para mostrar el cambio de estado
    headers = {"HX-Trigger": "refreshMediaGallery"}
    return Response(status_code=204, headers=headers)

@app.delete("/admin/media-files/{media_file_id}", response_class=Response)
async def delete_media_file_ui(
    media_file_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """
    Elimina un archivo multimedia y refresca la galería.
    """
    company_id = admin.get("company_id")
    service = MediaFileService(db)
    deleted = service.delete_media_file(media_file_id, company_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    # Refresca la galería después de eliminar
    headers = {"HX-Trigger": "refreshMediaGallery"}
    return Response(status_code=200, headers=headers)


# 8. Módulo de Razones de Cierre
# -------------------------------------------------------------------------------------
@app.get("/admin/reasons", response_class=HTMLResponse) 
async def get_reasons_panel(request: Request, admin: dict = Depends(get_current_admin)): 
    return templates.TemplateResponse("partials/admin/reasons_panel.html", {"request": request}) 

@app.get("/admin/reasons/table", response_class=HTMLResponse) 
async def get_reasons_table(request: Request, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)): 
    company_id = admin.get("company_id") 
    reasons = CloseReasonService(db).get_all_by_company(company_id=company_id) 
    return templates.TemplateResponse("partials/admin/_reasons_table.html", {"request": request, "reasons": reasons}) 

@app.get("/admin/reasons/add-form", response_class=HTMLResponse) 
async def get_reason_add_form(request: Request, admin: dict = Depends(get_current_admin)): 
    return templates.TemplateResponse("partials/admin/reason_form.html", {"request": request, "reason": None}) 

@app.get("/admin/reasons/{reason_id}/edit-form", response_class=HTMLResponse) 
async def get_reason_edit_form(reason_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    reason = CloseReasonService(db).get_by_company(reason_id=reason_id, company_id=admin.get("company_id")) 
    if not reason: 
        raise HTTPException(status_code=404, detail="Razón no encontrada.") 
    return templates.TemplateResponse("partials/admin/reason_form.html", {"request": request, "reason": reason}) 

@app.get("/admin/reasons/{reason_id}/confirm-toggle", response_class=HTMLResponse) 
async def get_reason_toggle_confirmation(reason_id: int, request: Request, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    reason = CloseReasonService(db).get_by_company(reason_id=reason_id, company_id=admin.get("company_id")) 
    if not reason: 
        raise HTTPException(status_code=404, detail="Razón no encontrada.") 
    return templates.TemplateResponse("partials/admin/_reason_confirm_dialog.html", {"request": request, "reason": reason}) 

@app.post("/admin/reasons", response_class=Response) 
async def create_reason( 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    reason_text: str = Form(...) 
):
    reason_in = CloseReasonCreate(reason_text=reason_text) 
    CloseReasonService(db).create(obj_in=reason_in, company_id=admin.get("company_id")) 
    headers = {"HX-Trigger": json.dumps({"refreshReasonList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

@app.post("/admin/reasons/{reason_id}", response_class=Response) 
async def update_reason( 
    reason_id: int, 
    db: Session = Depends(get_db), 
    admin: dict = Depends(get_current_admin), 
    reason_text: str = Form(...) 
):
    reason_service = CloseReasonService(db) 
    reason_to_update = reason_service.get_by_company(reason_id=reason_id, company_id=admin.get("company_id")) 
    if not reason_to_update: 
        raise HTTPException(status_code=404, detail="Razón no encontrada.") 
    reason_to_update.reason_text = reason_text 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshReasonList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

@app.post("/admin/reasons/{reason_id}/toggle-status", response_class=Response) 
async def toggle_reason_status(reason_id: int, db: Session = Depends(get_db), admin: dict = Depends(get_current_admin)): 
    reason_service = CloseReasonService(db) 
    reason_to_toggle = reason_service.get_by_company(reason_id=reason_id, company_id=admin.get("company_id")) 
    if not reason_to_toggle: 
        raise HTTPException(status_code=404, detail="Razón no encontrada.") 
    reason_to_toggle.is_active = not reason_to_toggle.is_active 
    db.commit() 
    headers = {"HX-Trigger": json.dumps({"refreshReasonList": None, "closeModal": None})} 
    return Response(status_code=204, headers=headers) 

# 9. Ruta del Display Público
# -------------------------------------------------------------------------------------
@app.get("/display/{company_id}", response_class=HTMLResponse, include_in_schema=False)
async def get_display_view(request: Request, company_id: int, db: Session = Depends(get_db)):
    """
    Muestra la página del display de atención, cargando todos los datos
    necesarios para la interfaz, incluyendo la playlist de multimedia.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Compañía no encontrada")

    # --- INICIO DE MODIFICACIÓN ---

    # 1. Obtener los anuncios de texto para la marquesina.
    text_advertisements_query = db.query(Advertisement).filter(
        Advertisement.company_id == company_id,
        Advertisement.is_active == True
    ).all()
    text_advertisements_data = [
        {"description": ad.description} for ad in text_advertisements_query
    ]

    # 2. Obtener la cola de agentes inicial.
    initial_queue_query = db.query(Ticket).join(Service, Ticket.service_id == Service.id).filter(
        Ticket.company_id == company_id,
        or_(
            Ticket.status == 'pagado',
            (Ticket.status == 'derivado') & (Service.requires_payment == False),
            (Ticket.status == 'pendiente_pago') & (Service.requires_payment == False)
        )
    ).order_by(
        Ticket.priority_level.desc(),
        func.coalesce(Ticket.updated_at, Ticket.created_at).asc()
    ).all()
    initial_queue_data = [
        {"id": t.id, "ticket_number": t.ticket_number, "created_at": t.created_at.isoformat()}
        for t in initial_queue_query
    ]
    
    # 3. Obtener la playlist de archivos multimedia activos.
    media_files_query = db.query(MediaFile).filter(
        MediaFile.company_id == company_id,
        MediaFile.status == True
    ).order_by(MediaFile.date_create.desc()).all()
    
    media_playlist_data = [
        {
            "url": media.url,
            "file_type": media.file_type,
            "duration_seconds": media.duration_seconds,
            "name": media.name
        } for media in media_files_query
    ]

    # 4. Construir el contexto completo para la plantilla.
    context = {
        "request": request,
        "company": company,
        "text_advertisements": text_advertisements_data,
        "initial_queue": initial_queue_data,
        "media_playlist": media_playlist_data  # Se añade la playlist al contexto
    }
    
    return templates.TemplateResponse("display.html", context)

@app.get("/admin/media-files/{media_file_id}/confirm-delete", response_class=HTMLResponse)
async def get_media_file_delete_confirmation(
    media_file_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """
    Devuelve el diálogo de confirmación para eliminar un archivo.
    """
    company_id = admin.get("company_id")
    file_to_delete = MediaFileService(db).get_by_company(media_file_id, company_id)
    if not file_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")
    return templates.TemplateResponse("partials/admin/_media_file_confirm_dialog.html", {"request": request, "file": file_to_delete})



@app.websocket("/ws/{company_id}")
async def websocket_display_endpoint(websocket: WebSocket, company_id: int):
    logging.info(f"Display intentando conectar para company_id={company_id}")
    await display_manager.connect(websocket, company_id)
    logging.info(f"Display conectado para company_id={company_id}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.info(f"Display desconectado para company_id={company_id}")
        display_manager.disconnect(websocket, company_id)
    except Exception as e:
        logging.error(f"Error en WebSocket para company_id={company_id}: {e}")
        display_manager.disconnect(websocket, company_id)


# 10. Inclusión del Router de la API
# -------------------------------------------------------------------------------------
app.include_router(api_router, prefix="/api/v1") 