from flask import Blueprint, jsonify, render_template, request, session
from models import User, Task, db
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_login import login_required, current_user

task_performance_bp = Blueprint('task_performance', __name__)

@task_performance_bp.route("/crm/tasks/performance")
@login_required
def task_performance_dashboard():
    """Görev performans gösterge panosu"""
    # Kullanıcının broker olup olmadığını kontrol et
    if current_user.role != 'broker':
        return render_template('errors/403.html'), 403
    
    # Varsayılan olarak son 30 günlük performans verilerini hesapla
    metrics = calculate_performance_metrics(30)
    
    # Broker'ın ekip üyelerini al
    team_members = User.query.filter_by(broker_id=current_user.id).all()
    
    # Her ekip üyesinin performans metriklerini hesapla
    for member in team_members:
        member.metrics = calculate_user_metrics(member.id, 30)
    
    # Son tamamlanan görevleri al
    recent_completed_tasks = get_recent_completed_tasks(10)
    
    # Haftalık tamamlanan görev sayıları
    weekly_data = get_weekly_completion_data(4)  # Son 4 hafta
    
    return render_template('crm/task_performance.html', 
                          metrics=metrics,
                          team_members=team_members,
                          recent_completed_tasks=recent_completed_tasks,
                          weekly_labels=weekly_data['labels'],
                          weekly_completed_data=weekly_data['data'])

@task_performance_bp.route("/crm/tasks/performance-data")
@login_required
def task_performance_data():
    """Görev performans verilerini JSON formatında döndüren API"""
    # Kullanıcının broker olup olmadığını kontrol et
    if current_user.role != 'broker':
        return jsonify({"error": "Bu sayfaya erişim yetkiniz yok"}), 403
    
    # İstek parametrelerinden periyodu al (varsayılan: 30 gün)
    period = request.args.get('period', '30')
    try:
        period = int(period)
    except ValueError:
        period = 30
    
    # Performans metriklerini hesapla
    metrics = calculate_performance_metrics(period)
    
    # Haftalık tamamlanan görev sayıları
    weekly_data = get_weekly_completion_data(4)  # Son 4 hafta
    
    return jsonify({
        "metrics": metrics,
        "weekly_labels": weekly_data['labels'],
        "weekly_completed_data": weekly_data['data']
    })

def calculate_performance_metrics(days):
    """Genel performans metriklerini hesapla"""
    user_id = current_user.id
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Brokera bağlı tüm kullanıcı ID'lerini al
    team_user_ids = db.session.query(User.id).filter_by(broker_id=user_id).all()
    team_user_ids = [id[0] for id in team_user_ids]  # Liste olarak al
    team_user_ids.append(user_id)  # Broker'ı da dahil et
    
    # Toplam görev sayısı
    total_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # Tamamlanan görev sayısı
    completed_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Tamamlandı",
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # Devam eden görevler
    in_progress_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Devam Ediyor",
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # Bekleyen görevler
    pending_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Beklemede",
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # İptal edilen görevler
    cancelled_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "İptal",
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # Süresi geçmiş görevler
    overdue_tasks = Task.query.filter(
        Task.due_date < datetime.utcnow(),
        Task.status.notin_(["Tamamlandı", "İptal"]),
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # Zamanında tamamlanan görevler
    on_time_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Tamamlandı",
        Task.due_date >= Task.completed_at,
        Task.user_id.in_(team_user_ids)
    ).count()
    
    # Zamanında tamamlama yüzdesi
    on_time_percentage = (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "pending_tasks": pending_tasks,
        "cancelled_tasks": cancelled_tasks,
        "overdue_tasks": overdue_tasks,
        "on_time_tasks": on_time_tasks,
        "on_time_percentage": on_time_percentage
    }

def calculate_user_metrics(user_id, days):
    """Belirli bir kullanıcının performans metriklerini hesapla"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Atanan toplam görev sayısı
    assigned_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.assigned_to_user_id == user_id
    ).count()
    
    # Tamamlanan görev sayısı
    completed_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Tamamlandı",
        Task.assigned_to_user_id == user_id
    ).count()
    
    # Tamamlama oranı
    completion_rate = (completed_tasks / assigned_tasks * 100) if assigned_tasks > 0 else 0
    
    # Zamanında tamamlanan görevler
    on_time_tasks = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Tamamlandı",
        Task.due_date >= Task.completed_at,
        Task.assigned_to_user_id == user_id
    ).count()
    
    # Zamanında tamamlama oranı
    on_time_rate = (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0
    
    # Tamamlanan görevleri al
    completed_task_records = Task.query.filter(
        Task.created_at >= start_date,
        Task.status == "Tamamlandı",
        Task.assigned_to_user_id == user_id,
        Task.completed_at.isnot(None)
    ).all()
    
    # Ortalama tamamlama süresi (gün cinsinden)
    total_days = 0
    valid_tasks = 0
    
    for task in completed_task_records:
        if task.created_at and task.completed_at:
            days = (task.completed_at - task.created_at).total_seconds() / 86400  # saniyeyi güne çevir
            total_days += days
            valid_tasks += 1
    
    avg_completion_days = total_days / valid_tasks if valid_tasks > 0 else 0
    
    return {
        "assigned_tasks": assigned_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": completion_rate,
        "on_time_tasks": on_time_tasks,
        "on_time_rate": on_time_rate,
        "avg_completion_days": avg_completion_days
    }

def get_recent_completed_tasks(limit=10):
    """Son tamamlanan görevleri al"""
    user_id = current_user.id
    
    # Broker'a bağlı tüm kullanıcı ID'lerini al
    team_user_ids = db.session.query(User.id).filter_by(broker_id=user_id).all()
    team_user_ids = [id[0] for id in team_user_ids]
    team_user_ids.append(user_id)  # Broker'ı da dahil et
    
    completed_tasks = Task.query.filter(
        Task.status == "Tamamlandı",
        Task.user_id.in_(team_user_ids),
        Task.completed_at.isnot(None)
    ).order_by(Task.completed_at.desc()).limit(limit).all()
    
    # Ek task verileri
    task_data = []
    for task in completed_tasks:
        assignee = User.query.get(task.assigned_to_user_id) if task.assigned_to_user_id else None
        
        # Görevin zamanında tamamlanıp tamamlanmadığını kontrol et
        was_completed_on_time = True
        if task.due_date and task.completed_at:
            was_completed_on_time = task.completed_at <= task.due_date
        
        # Tamamlanma süresi (gün cinsinden)
        completion_days = 0
        if task.created_at and task.completed_at:
            completion_days = (task.completed_at - task.created_at).total_seconds() / 86400
        
        task_info = {
            "id": task.id,
            "title": task.title,
            "assignee": assignee,
            "due_date": task.due_date,
            "completed_at": task.completed_at,
            "was_completed_on_time": was_completed_on_time,
            "completion_days": completion_days
        }
        task_data.append(task_info)
    
    return task_data

def get_weekly_completion_data(weeks=4):
    """Haftalık tamamlanan görev sayılarını al"""
    user_id = current_user.id
    
    # Broker'a bağlı tüm kullanıcı ID'lerini al
    team_user_ids = db.session.query(User.id).filter_by(broker_id=user_id).all()
    team_user_ids = [id[0] for id in team_user_ids]
    team_user_ids.append(user_id)  # Broker'ı da dahil et
    
    # Son X hafta için tarih aralıklarını oluştur
    end_date = datetime.utcnow()
    labels = []
    data = []
    
    for i in range(weeks):
        start_week = end_date - timedelta(days=7)
        
        # Haftayı etiketle
        week_label = f"{start_week.strftime('%d.%m')} - {end_date.strftime('%d.%m')}"
        labels.insert(0, week_label)
        
        # Bu hafta içinde tamamlanan görev sayısını al
        week_completed = Task.query.filter(
            Task.completed_at.between(start_week, end_date),
            Task.status == "Tamamlandı",
            Task.user_id.in_(team_user_ids)
        ).count()
        
        data.insert(0, week_completed)
        
        # Bir sonraki döngü için end_date'i güncelle
        end_date = start_week
    
    return {
        "labels": labels,
        "data": data
    }
