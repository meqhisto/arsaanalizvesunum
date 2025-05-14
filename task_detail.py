from app import app, db, User, Task, login_required, render_template, redirect, url_for, flash, session
from flask import request, g
from datetime import datetime
from werkzeug.routing import BuildError

@app.route("/crm/task/<int:task_id>")
@login_required
def crm_task_detail(task_id):
    """Görev detaylarını gösterir"""
    user_id = session["user_id"]
    current_user = User.query.get(user_id)
    
    # Görevi bul
    task = Task.query.get_or_404(task_id)
    
    # Yetki kontrolü - görevi görüntüleme yetkisi var mı?
    # Yetki 3 durumda verilir: 1) Görevi oluşturan kişiyse, 2) Görev ona atanmışsa, 3) Broker ise ve görev kendi ekibindeki birine atanmışsa
    is_authorized = (task.user_id == user_id or  # Görevi oluşturan
                    task.assigned_to_user_id == user_id or  # Görevi atanan
                    (current_user.role == "broker" and  # Broker ise ve kendi ekibindeki birine atanmışsa
                     task.assigned_to_user_id in [member.id for member in current_user.team_members.all()]))
    
    if not is_authorized:
        flash("Bu görevi görüntüleme yetkiniz bulunmuyor.", "danger")
        return redirect(url_for("crm_tasks_list"))
    
    # Görev sahibini ve atanan kişiyi bul
    owner = User.query.get(task.user_id) if task.user_id else None
    assignee = User.query.get(task.assigned_to_user_id) if task.assigned_to_user_id else None
    
    # Görev geçmişi ve diğer detaylar buraya eklenebilir...
    
    # Sayfada kullanılabilecek URL'leri kontrol et
    url_list = []
    possible_endpoints = [
        'crm_task_edit', 'crm_task_complete', 'crm_task_reassign', 'crm_task_delete'
    ]
    
    for endpoint in possible_endpoints:
        try:
            # Test et bakalım bu endpoint var mı
            url_for(endpoint, task_id=1)
            url_list.append(endpoint)
        except BuildError:
            # Endpoint yoksa listeye ekleme
            pass
    
    return render_template(
        "crm/task_detail.html",
        title="Görev Detayı",
        task=task,
        owner=owner,
        assignee=assignee,
        current_user=current_user,
        url_list=url_list
    )
