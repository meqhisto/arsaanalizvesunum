from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, or_, and_

from models import db
from models.arsa_models import ArsaAnaliz, DashboardStats
from models.crm_models import Contact, Deal, Task
from ..utils.responses import success_response, error_response


dashboard_v1 = Blueprint("dashboard_v1", __name__)


@dashboard_v1.route("/summary", methods=["GET"])
@jwt_required()
def dashboard_summary():
    """Return key CRM and analysis metrics for the authenticated user."""
    try:
        user_id = get_jwt_identity()
        if isinstance(user_id, str):
            user_id = int(user_id)

        total_analyses = ArsaAnaliz.query.filter_by(user_id=user_id).count()
        total_contacts = Contact.query.filter_by(user_id=user_id).count()
        total_deals = Deal.query.filter_by(user_id=user_id).count()

        open_tasks = Task.query.filter(
            Task.status != "Tamamlandı",
            or_(
                Task.assigned_to_user_id == user_id,
                and_(Task.assigned_to_user_id.is_(None), Task.user_id == user_id)
            )
        ).count()

        total_deal_value = db.session.query(func.coalesce(func.sum(Deal.value), 0)).filter_by(user_id=user_id).scalar() or 0

        last_analysis = (
            ArsaAnaliz.query.filter_by(user_id=user_id)
            .order_by(ArsaAnaliz.created_at.desc())
            .first()
        )

        stats = DashboardStats.query.filter_by(user_id=user_id).first()

        data = {
            "total_analyses": total_analyses,
            "total_contacts": total_contacts,
            "total_deals": total_deals,
            "open_tasks": open_tasks,
            "total_deal_value": float(total_deal_value or 0),
            "last_analysis_at": last_analysis.created_at.isoformat() if last_analysis else None,
            "dashboard_stats": {
                "toplam_arsa_sayisi": stats.toplam_arsa_sayisi if stats else 0,
                "ortalama_fiyat": stats.ortalama_fiyat if stats else 0,
                "en_yuksek_fiyat": stats.en_yuksek_fiyat if stats else 0,
                "en_dusuk_fiyat": stats.en_dusuk_fiyat if stats else 0,
                "toplam_deger": float(stats.toplam_deger) if stats and stats.toplam_deger is not None else 0,
                "son_guncelleme": stats.son_guncelleme.isoformat() if stats and stats.son_guncelleme else None,
            },
        }

        return success_response(data=data, message="Dashboard summary fetched")
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.error("Dashboard summary failed: %s", exc)
        return error_response("Dashboard summary failed", 500)
