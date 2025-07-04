# Ruta: app/services/report_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, text
from datetime import date, timedelta, datetime

from app.models.ticket import Ticket
from app.models.user import User

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_tickets_processed_over_time(self, company_id: int, start_date: date, end_date: date):
        """
        Calcula la cantidad de tickets finalizados por día en un rango de fechas.
        """
        end_date_inclusive = end_date + timedelta(days=1)

        query_result = (
            self.db.query(
                func.count(Ticket.id).label("ticket_count"),
                cast(Ticket.updated_at, Date).label("date"),
            )
            .filter(
                Ticket.company_id == company_id,
                Ticket.status == "finalizado",
                Ticket.updated_at >= start_date,
                Ticket.updated_at < end_date_inclusive,
            )
            .group_by(cast(Ticket.updated_at, Date))
            .order_by(cast(Ticket.updated_at, Date))
            .all()
        )

        data_map = {res.date.strftime("%Y-%m-%d"): res.ticket_count for res in query_result}
        
        labels = []
        data = []
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            labels.append(current_date.strftime("%d/%m"))
            data.append(data_map.get(date_str, 0))
            current_date += timedelta(days=1)

        return {"labels": labels, "data": data}

    def get_tickets_by_agent(self, company_id: int, start_date: date, end_date: date):
        """
        Calcula la cantidad de tickets finalizados por agente en un rango de fechas.
        """
        end_date_inclusive = end_date + timedelta(days=1)

        query_result = (
            self.db.query(
                func.count(Ticket.id).label("ticket_count"),
                User.full_name.label("agent_name"),
            )
            .join(User, Ticket.attended_by_id == User.id)
            .filter(
                Ticket.company_id == company_id,
                Ticket.status == "finalizado",
                Ticket.updated_at >= start_date,
                Ticket.updated_at < end_date_inclusive,
            )
            .group_by(User.full_name)
            .order_by(func.count(Ticket.id).desc())
            .all()
        )

        labels = [res.agent_name for res in query_result]
        data = [res.ticket_count for res in query_result]

        return {"labels": labels, "data": data}

    def get_daily_kpis(self, company_id: int):
        """
        Calcula los KPIs para el día actual.
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Total de tickets finalizados hoy
        total_tickets_today = (
            self.db.query(func.count(Ticket.id))
            .filter(
                Ticket.company_id == company_id,
                Ticket.status == "finalizado",
                Ticket.updated_at >= today_start,
                Ticket.updated_at < today_end,
            )
            .scalar() or 0
        )

        # Tiempo promedio de atención
        avg_attention_seconds = (
            self.db.query(
                func.avg(
                    func.timestampdiff(text("SECOND"), Ticket.created_at, Ticket.updated_at)
                )
            )
            .filter(
                Ticket.company_id == company_id,
                Ticket.status == "finalizado",
                Ticket.updated_at >= today_start,
                Ticket.updated_at < today_end,
            )
            .scalar() or 0
        )
        
        avg_minutes = int(avg_attention_seconds // 60)
        avg_seconds = int(avg_attention_seconds % 60)
        avg_attention_time = f"{avg_minutes}m {avg_seconds}s"

        return {
            "total_tickets_today": total_tickets_today,
            "avg_attention_time": avg_attention_time
        }