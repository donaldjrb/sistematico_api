# 📞 Sistematico API v1.0

FastAPI + SQLAlchemy + Alembic + JWT.  
Backend que gestiona colas telefónicas, compañías y publicidad para centros de
servicio.

## ⚡ Arranque rápido (dev)

```bash
git clone https://github.com/<tu-org>/sistematico_api.git
cd sistematico_api
python -m venv .venv && . .venv/Scripts/activate      # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload


Swagger UI → <http://127.0.0.1:8000/docs> 🚀

🔑 Autenticación
POST /api/v1/auth/register Registra usuario

POST /api/v1/auth/login Devuelve access_token y refresh_token

Botón Authorize en Swagger → pega el access_token

📚 Endpoints CRUD (v1)
Recurso	Prefijo	Descripción
auth	/auth	registro, login, refresh, me
companies	/companies	compañías / sucursales
services	/services	servicios de cada compañía
tickets	/tickets	turnos en cola
users	/users	operadores y admins
close_reasons	/close-reasons	motivos de cierre de ticket
advertisements	/advertisements	piezas publicitarias
media_files	/media-files	archivos subidos (S3-ready)
Cada recurso expone: GET /, GET /{id}, POST /, PUT /{id} y DELETE /{id}.

🗄️ Modelo de datos principal
mermaid
classDiagram
    Company "1" --o "0..*" Service
    Company "1" --o "0..*" Ticket
    Service "1" --o "0..*" Ticket
    Ticket  --> CloseReason : optional


🛠️ Scripts de desarrollo
scripts/reset_db_dev.py   # ⚠️  vacía y recrea la base local
scripts/seed_dev.py       # ⚠️  inserta datos dummy
scripts/db_check.py       # comprobaciones rápidas
> Nunca ejecutes estos scripts contra producción.

Calidad
Tool	Comando
Tests	pytest -q
Linter	ruff check .
Format	black . & isort .
Todos deben terminar sin errores antes de hacer push.

© 2025 – Licencia MIT