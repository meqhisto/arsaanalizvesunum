from app import app, db, Task, User, login_required, session, flash, redirect, url_for, jsonify
from flask import request
from datetime import datetime, timedelta

# Hatırlatıcıları kontrol etmek için yeni bir rota oluşturalım
@app.route("/crm/tasks/check-reminders")
@login_required
def check_reminders():
    """Kullanıcının bekleyen hatırlatıcılarını kontrol et"""
    user_id = session["user_id"]
    current_user = User.query.get(user_id)
    
    # Aktif ve zamanı gelen görevleri bul
    upcoming_tasks = Task.query.filter(
        (Task.assigned_to_user_id == user_id) | (Task.user_id == user_id),
        Task.status != "Tamamlandı",
        Task.status != "İptal",
        Task.due_date <= datetime.utcnow() + timedelta(days=1),
        Task.due_date >= datetime.utcnow() - timedelta(days=1)
    ).all()
    
    # Hatırlatıcı verileri hazırla
    reminders_data = []
    for task in upcoming_tasks:
        days_left = 0
        if task.due_date:
            delta = task.due_date - datetime.utcnow()
            days_left = delta.days + (delta.seconds / 86400)
            
        status_text = "yaklaşıyor"
        if days_left < 0:
            status_text = "gecikti"
        elif days_left < 0.25:  # 6 saatten az
            status_text = "bugün son saatler"
        elif days_left < 1:
            status_text = "bugün bitiyor"
            
        reminders_data.append({
            'id': task.id,
            'title': task.title,
            'message': f"Görev {status_text}!",
            'time': task.due_date.strftime('%d.%m.%Y %H:%M') if task.due_date else "",
            'type': "task",
            'task_url': f"/crm/task/{task.id}"
        })
    
    return jsonify(reminders=reminders_data)
