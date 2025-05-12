from app import app, db, User, Task, login_required, render_template, redirect, url_for, flash, session
from sqlalchemy import func, case, text
from datetime import datetime, timedelta
from flask import g, request

@app.route("/crm/team-dashboard")
@login_required
def crm_team_dashboard():
    """Broker rolündeki kullanıcılar için ekip performans özeti"""
    user_id = session["user_id"]
    current_user = User.query.get(user_id)
    
    # Sadece broker'lar bu sayfaya erişebilir
    if current_user.role != "broker":
        flash("Bu sayfaya erişim yetkiniz bulunmuyor.", "danger")
        return redirect(url_for("crm_tasks_list"))
    
    # Ekip üyelerini getir
    team_members = current_user.team_members.all()
    
    if not team_members:
        flash("Henüz ekibinizde danışman bulunmuyor. Lütfen önce ekibinize danışman ekleyin.", "info")
        return redirect(url_for("crm_team_management"))
    
    # Ekip üyelerinin ID'lerini al
    team_member_ids = [member.id for member in team_members]
    
    # Ekibin toplam görev istatistiklerini hesapla
    total_tasks = Task.query.filter(
        (Task.assigned_to_user_id.in_(team_member_ids))
    ).count()
    
    completed_tasks = Task.query.filter(
        (Task.assigned_to_user_id.in_(team_member_ids)),
        (Task.status == "Tamamlandı")
    ).count()
    
    pending_tasks = Task.query.filter(
        (Task.assigned_to_user_id.in_(team_member_ids)),
        (Task.status != "Tamamlandı"),
        (Task.status != "İptal")
    ).count()
    
    overdue_tasks = Task.query.filter(
        (Task.assigned_to_user_id.in_(team_member_ids)),
        (Task.status != "Tamamlandı"),
        (Task.status != "İptal"),
        (Task.due_date < datetime.utcnow())
    ).count()
    
    # Tamamlanma oranını hesapla
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100)
    
    # Genel istatistikler
    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate
    }
    
    # Ekip üyelerinin performans bilgilerini topla
    team_performance = []
    
    for member in team_members:
        # Danışmana atanmış görevleri getir
        member_tasks = Task.query.filter(
            Task.assigned_to_user_id == member.id
        ).all()
        
        # Görev istatistikleri
        member_total_tasks = len(member_tasks)
        member_completed_tasks = sum(1 for task in member_tasks if task.status == "Tamamlandı")
        member_pending_tasks = sum(1 for task in member_tasks if task.status != "Tamamlandı" and task.status != "İptal")
        member_overdue_tasks = sum(1 for task in member_tasks if task.is_overdue())
        
        # Tamamlanma oranı
        member_completion_rate = 0
        if member_total_tasks > 0:
            member_completion_rate = round((member_completed_tasks / member_total_tasks) * 100)
        
        # Ortalama tamamlanma süresi (gün cinsinden)
        completed_tasks_with_time = [task for task in member_tasks if task.status == "Tamamlandı" and task.completed_at]
        avg_completion_time = 0
        if completed_tasks_with_time:
            completion_times = [task.get_completion_time() for task in completed_tasks_with_time if task.get_completion_time() is not None]
            if completion_times:
                avg_completion_time = round(sum(completion_times) / len(completion_times), 1)
        
        # Danışmanın performans bilgilerini ekle
        team_performance.append({
            'id': member.id,
            'name': f"{member.ad} {member.soyad}",
            'total_tasks': member_total_tasks,
            'completed_tasks': member_completed_tasks,
            'pending_tasks': member_pending_tasks,
            'overdue_tasks': member_overdue_tasks,
            'completion_rate': member_completion_rate,
            'avg_completion_time': avg_completion_time
        })
    
    # Son tamamlanan görevler (son 7 gün)
    last_week = datetime.utcnow() - timedelta(days=7)
    recently_completed_tasks = []
    
    tasks = Task.query.filter(
        Task.assigned_to_user_id.in_(team_member_ids),
        Task.status == "Tamamlandı",
        Task.completed_at >= last_week
    ).order_by(Task.completed_at.desc()).limit(10).all()
    
    for task in tasks:
        days_to_complete = task.get_completion_time()
        
        recently_completed_tasks.append({
            'id': task.id,
            'title': task.title,
            'assignee': task.get_assignee_name(),
            'completed_at': task.completed_at,
            'days_to_complete': round(days_to_complete, 1) if days_to_complete else None
        })
    
    # Yaklaşan son tarihler (gelecek 7 gün)
    next_week = datetime.utcnow() + timedelta(days=7)
    upcoming_deadlines = []
    
    tasks = Task.query.filter(
        Task.assigned_to_user_id.in_(team_member_ids),
        Task.status != "Tamamlandı",
        Task.status != "İptal",
        Task.due_date <= next_week,
        Task.due_date >= datetime.utcnow() - timedelta(days=1)  # Dün ve sonrası
    ).order_by(Task.due_date.asc()).limit(10).all()
    
    for task in tasks:
        days_left = task.get_days_until_due()
        
        upcoming_deadlines.append({
            'id': task.id,
            'title': task.title,
            'assignee': task.get_assignee_name(),
            'due_date': task.due_date,
            'days_left': round(days_left) if days_left is not None else None
        })
    
    return render_template(
        "crm/team_dashboard.html",
        title="Ekip Performans Özeti",
        stats=stats,
        team_performance=team_performance,
        recently_completed_tasks=recently_completed_tasks,
        upcoming_deadlines=upcoming_deadlines,
        current_user=current_user
    )

@app.route("/crm/team-member/<int:user_id>")
@login_required
def crm_team_member_detail(user_id):
    """Bir ekip üyesinin detaylı performans bilgilerini gösterir"""
    manager_id = session["user_id"]
    manager = User.query.get(manager_id)
    
    # Sadece broker'lar bu sayfaya erişebilir
    if manager.role != "broker":
        flash("Bu sayfaya erişim yetkiniz bulunmuyor.", "danger")
        return redirect(url_for("crm_tasks_list"))
    
    # Kullanıcının ekip üyesi olduğunu kontrol et
    team_member = User.query.get(user_id)
    if not team_member or team_member.report_to_id != manager_id:
        flash("Bu danışman ekibinizde bulunmuyor.", "danger")
        return redirect(url_for("crm_team_dashboard"))
    
    # Danışmanın görev istatistiklerini hesapla
    consultant_tasks = Task.query.filter(
        Task.assigned_to_user_id == user_id
    ).all()
    
    # Görev istatistikleri
    total_tasks = len(consultant_tasks)
    completed_tasks = sum(1 for task in consultant_tasks if task.status == "Tamamlandı")
    pending_tasks = sum(1 for task in consultant_tasks if task.status != "Tamamlandı" and task.status != "İptal")
    overdue_tasks = sum(1 for task in consultant_tasks if task.is_overdue())
    
    # Tamamlanma oranı
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100)
    
    # Ortalama tamamlanma süresi (gün cinsinden)
    completed_tasks_with_time = [task for task in consultant_tasks if task.status == "Tamamlandı" and task.completed_at]
    avg_completion_time = 0
    if completed_tasks_with_time:
        completion_times = [task.get_completion_time() for task in completed_tasks_with_time if task.get_completion_time() is not None]
        if completion_times:
            avg_completion_time = round(sum(completion_times) / len(completion_times), 1)
    
    # Öncelik dağılımı
    priority_distribution = {
        "Düşük": sum(1 for task in consultant_tasks if task.priority == "Düşük"),
        "Normal": sum(1 for task in consultant_tasks if task.priority == "Normal"),
        "Yüksek": sum(1 for task in consultant_tasks if task.priority == "Yüksek"),
        "Acil": sum(1 for task in consultant_tasks if task.priority == "Acil")
    }
    
    # Durum dağılımı
    status_distribution = {
        "Beklemede": sum(1 for task in consultant_tasks if task.status == "Beklemede"),
        "Devam Ediyor": sum(1 for task in consultant_tasks if task.status == "Devam Ediyor"),
        "Tamamlandı": completed_tasks,
        "İptal": sum(1 for task in consultant_tasks if task.status == "İptal")
    }
    
    # Son görevler (aktif + tamamlanan)
    recent_tasks = []
    tasks = Task.query.filter(
        Task.assigned_to_user_id == user_id
    ).order_by(Task.updated_at.desc()).limit(15).all()
    
    for task in tasks:
        status_class = {
            "Beklemede": "secondary", 
            "Devam Ediyor": "primary", 
            "Tamamlandı": "success", 
            "İptal": "danger"
        }.get(task.status, "secondary")
        
        days_info = ""
        if task.status == "Tamamlandı" and task.get_completion_time() is not None:
            days_info = f"{round(task.get_completion_time(), 1)} günde tamamlandı"
        elif task.get_days_until_due() is not None:
            days_left = task.get_days_until_due()
            if days_left < 0:
                days_info = f"{abs(round(days_left))} gün gecikti"
            elif days_left < 1:
                days_info = "Bugün son gün"
            else:
                days_info = f"{round(days_left)} gün kaldı"
        
        recent_tasks.append({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'status_class': status_class,
            'priority': task.priority,
            'created_at': task.created_at,
            'days_info': days_info
        })
    
    # Görev yüzdesi (aylar bazında)
    now = datetime.utcnow()
    months = []
    month_stats = []
    
    for i in range(5, -1, -1):  # Son 6 ay
        target_month = now - timedelta(days=30*i)
        month_name = target_month.strftime('%b %Y')
        months.append(month_name)
        
        month_start = datetime(target_month.year, target_month.month, 1)
        if target_month.month == 12:
            month_end = datetime(target_month.year + 1, 1, 1)
        else:
            month_end = datetime(target_month.year, target_month.month + 1, 1)
        
        # O ay içinde tamamlanan görevler
        monthly_completed = Task.query.filter(
            Task.assigned_to_user_id == user_id,
            Task.status == "Tamamlandı",
            Task.completed_at >= month_start,
            Task.completed_at < month_end
        ).count()
        
        # O ay içinde oluşturulan görevler
        monthly_created = Task.query.filter(
            Task.assigned_to_user_id == user_id,
            Task.created_at >= month_start,
            Task.created_at < month_end
        ).count()
        
        month_stats.append({
            'month': month_name,
            'completed': monthly_completed,
            'created': monthly_created
        })
    
    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate,
        'avg_completion_time': avg_completion_time,
        'priority_distribution': priority_distribution,
        'status_distribution': status_distribution,
        'months': months,
        'month_stats': month_stats
    }
    
    return render_template(
        "crm/team_member_detail.html",
        title=f"{team_member.ad} {team_member.soyad} - Performans Detayı",
        team_member=team_member,
        stats=stats,
        recent_tasks=recent_tasks,
        current_user=manager
    )
