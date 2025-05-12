from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from app import db, Task, Contact, Deal, Reminder
from datetime import datetime, timedelta
import json

task_bp = Blueprint('task', __name__, url_prefix='/crm/tasks')

# Görev durumları ve öncelikleri
TASK_STATUSES = ["Beklemede", "Devam Ediyor", "Tamamlandı", "İptal Edildi"]
TASK_PRIORITIES = ["Düşük", "Normal", "Yüksek", "Acil"]
RECURRENCE_TYPES = ["Günlük", "Haftalık", "Aylık", "Yıllık"]

@task_bp.route('/')
@login_required
def tasks_list():
    """Görevleri listele."""
    status_filter = request.args.get('status', '')
    
    # Görev sorgusunu hazırla
    query = Task.query.filter_by(user_id=current_user.id)
    
    # Durum filtresi uygula
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Önce zamanı yaklaşan, sonra önceliği yüksek görevleri getir
    tasks = query.order_by(Task.due_date.asc(), 
                        Task.priority.desc(), 
                        Task.created_at.desc()).all()
    
    return render_template('crm/tasks_list.html', 
                        tasks=tasks, 
                        statuses=TASK_STATUSES,
                        current_status=status_filter,
                        datetime=datetime)  # datetime template'te kullanılıyor

@task_bp.route('/new', methods=['GET', 'POST'])
@login_required
def task_new():
    """Yeni görev oluştur."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        contact_id = request.form.get('contact_id')
        deal_id = request.form.get('deal_id')
        status = request.form.get('status', TASK_STATUSES[0])
        priority = request.form.get('priority', 'Normal')
        
        # Tarihi işle
        due_date_str = request.form.get('due_date')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
        
        # Tekrarlanan görev ayarlarını al
        is_recurring = 'is_recurring' in request.form
        recurrence_type = request.form.get('recurrence_type') if is_recurring else None
        recurrence_interval = int(request.form.get('recurrence_interval', 1)) if is_recurring else None
        recurrence_end_date_str = request.form.get('recurrence_end_date')
        recurrence_end_date = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d') if recurrence_end_date_str else None
        
        # Hatırlatıcı ayarlarını al
        reminder_enabled = 'reminder_enabled' in request.form
        reminder_time_str = request.form.get('reminder_time')
        reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M') if reminder_time_str else None
        
        # Contact ID ve Deal ID doğrula
        if contact_id == '':
            contact_id = None
        if deal_id == '':
            deal_id = None
            
        # Yeni görevi oluştur
        new_task = Task(
            user_id=current_user.id,
            title=title,
            description=description,
            contact_id=contact_id,
            deal_id=deal_id,
            status=status,
            priority=priority,
            due_date=due_date,
            is_recurring=is_recurring,
            recurrence_type=recurrence_type,
            recurrence_interval=recurrence_interval,
            recurrence_end_date=recurrence_end_date,
            reminder_enabled=reminder_enabled,
            reminder_time=reminder_time
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        # Hatırlatıcı etkinleştirilmişse, bir hatırlatıcı kaydı oluştur
        if reminder_enabled and reminder_time:
            reminder = Reminder(
                user_id=current_user.id,
                task_id=new_task.id,
                contact_id=contact_id,
                deal_id=deal_id,
                title=f"Görev Hatırlatıcı: {title}",
                message=f"Görev bilgileri: {description}",
                reminder_time=reminder_time,
                notification_type="app"  # Varsayılan olarak uygulama içi bildirim
            )
            db.session.add(reminder)
            db.session.commit()
        
        flash(f"'{title}' görevi başarıyla oluşturuldu!", "success")
        return redirect(url_for('task.tasks_list'))
    
    # GET isteği - Yeni görev formu
    # URL parametre ile ön seçimli Contact veya Deal
    preselected_contact_id = request.args.get('contact_id')
    preselected_deal_id = request.args.get('deal_id')
    
    preselected_contact = None
    if preselected_contact_id:
        preselected_contact = Contact.query.filter_by(id=preselected_contact_id, user_id=current_user.id).first()
    
    preselected_deal = None
    if preselected_deal_id:
        preselected_deal = Deal.query.filter_by(id=preselected_deal_id, user_id=current_user.id).first()
    
    # Kullanıcının tüm kişileri ve fırsatları
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.first_name).all()
    deals = Deal.query.filter_by(user_id=current_user.id).order_by(Deal.title).all()
    
    return render_template('crm/task_form.html', 
                        title="Yeni Görev",
                        contacts=contacts,
                        deals=deals,
                        statuses=TASK_STATUSES,
                        priorities=TASK_PRIORITIES,
                        preselected_contact=preselected_contact,
                        preselected_deal=preselected_deal)

@task_bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task_edit(task_id):
    """Görev düzenle."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description', '')
        
        # Contact ve Deal ID'leri işle
        contact_id = request.form.get('contact_id')
        task.contact_id = None if contact_id == '' else contact_id
        
        deal_id = request.form.get('deal_id')
        task.deal_id = None if deal_id == '' else deal_id
        
        task.status = request.form.get('status', TASK_STATUSES[0])
        task.priority = request.form.get('priority', 'Normal')
        
        # Tamamlandı olarak işaretlendiyse, tamamlanma tarihini ayarla
        if task.status == "Tamamlandı" and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif task.status != "Tamamlandı":
            task.completed_at = None
        
        # Tarihi işle
        due_date_str = request.form.get('due_date')
        task.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
        
        # Tekrarlanan görev ayarlarını güncelle
        task.is_recurring = 'is_recurring' in request.form
        if task.is_recurring:
            task.recurrence_type = request.form.get('recurrence_type')
            task.recurrence_interval = int(request.form.get('recurrence_interval', 1))
            
            recurrence_end_date_str = request.form.get('recurrence_end_date')
            task.recurrence_end_date = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d') if recurrence_end_date_str else None
        else:
            task.recurrence_type = None
            task.recurrence_interval = None
            task.recurrence_end_date = None
        
        # Hatırlatıcı ayarlarını güncelle
        task.reminder_enabled = 'reminder_enabled' in request.form
        reminder_time_str = request.form.get('reminder_time')
        task.reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M') if reminder_time_str else None
        
        # Eğer görev tamamlandıysa ve tekrarlanan bir görevse, bir sonraki görevi oluştur
        if task.status == "Tamamlandı" and task.is_recurring:
            next_task = task.create_next_task()
            if next_task:
                db.session.add(next_task)
                flash(f"Bir sonraki tekrarlanan görev oluşturuldu: {next_task.due_date.strftime('%d.%m.%Y')}", "info")
                
                # Eğer hatırlatıcı da etkinse, yeni görev için de hatırlatıcı oluştur
                if next_task.reminder_enabled and next_task.reminder_time:
                    reminder = Reminder(
                        user_id=current_user.id,
                        task_id=next_task.id,
                        contact_id=next_task.contact_id,
                        deal_id=next_task.deal_id,
                        title=f"Görev Hatırlatıcı: {next_task.title}",
                        message=f"Görev bilgileri: {next_task.description}",
                        reminder_time=next_task.reminder_time,
                        notification_type="app"
                    )
                    db.session.add(reminder)
        
        # Hatırlatıcıları güncelle
        if task.reminder_enabled and task.reminder_time:
            # Mevcut hatırlatıcıları kontrol et
            existing_reminder = Reminder.query.filter_by(task_id=task.id, user_id=current_user.id).first()
            
            if existing_reminder:
                # Mevcut hatırlatıcıyı güncelle
                existing_reminder.title = f"Görev Hatırlatıcı: {task.title}"
                existing_reminder.message = f"Görev bilgileri: {task.description}"
                existing_reminder.reminder_time = task.reminder_time
                # Görev tamamlandıysa hatırlatıcıyı iptal et
                if task.status == "Tamamlandı":
                    existing_reminder.is_sent = True
                    existing_reminder.sent_at = datetime.utcnow()
            else:
                # Yeni hatırlatıcı oluştur
                new_reminder = Reminder(
                    user_id=current_user.id,
                    task_id=task.id,
                    contact_id=task.contact_id,
                    deal_id=task.deal_id,
                    title=f"Görev Hatırlatıcı: {task.title}",
                    message=f"Görev bilgileri: {task.description}",
                    reminder_time=task.reminder_time,
                    notification_type="app"
                )
                db.session.add(new_reminder)
        else:
            # Hatırlatıcı devre dışıysa, varsa sil
            existing_reminder = Reminder.query.filter_by(task_id=task.id, user_id=current_user.id).first()
            if existing_reminder:
                db.session.delete(existing_reminder)
        
        db.session.commit()
        flash(f"'{task.title}' görevi başarıyla güncellendi!", "success")
        return redirect(url_for('task.tasks_list'))
    
    # GET isteği - Düzenleme formu
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.first_name).all()
    deals = Deal.query.filter_by(user_id=current_user.id).order_by(Deal.title).all()
    
    return render_template('crm/task_form.html', 
                        title="Görevi Düzenle",
                        task=task,
                        contacts=contacts,
                        deals=deals,
                        statuses=TASK_STATUSES,
                        priorities=TASK_PRIORITIES)

@task_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def task_delete(task_id):
    """Görevi sil."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    # İlişkili hatırlatıcıları sil
    Reminder.query.filter_by(task_id=task_id, user_id=current_user.id).delete()
    
    # Görevi sil
    db.session.delete(task)
    db.session.commit()
    
    flash(f"'{task.title}' görevi silindi!", "success")
    return redirect(url_for('task.tasks_list'))

@task_bp.route('/toggle-status/<int:task_id>', methods=['POST'])
@login_required
def task_toggle_status(task_id):
    """Görev durumunu hızlıca değiştir (tamamlandı/devam ediyor)."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    new_status = request.form.get('new_status')
    if new_status in TASK_STATUSES:
        task.status = new_status
        
        # Tamamlandı olarak işaretlendiyse, tamamlanma tarihini ayarla
        if new_status == "Tamamlandı":
            task.completed_at = datetime.utcnow()
            
            # Tekrarlanan görevse, bir sonraki görevi oluştur
            if task.is_recurring:
                next_task = task.create_next_task()
                if next_task:
                    db.session.add(next_task)
                    flash(f"Bir sonraki tekrarlanan görev oluşturuldu: {next_task.due_date.strftime('%d.%m.%Y')}", "info")
                    
                    # Eğer hatırlatıcı da etkinse, yeni görev için de hatırlatıcı oluştur
                    if next_task.reminder_enabled and next_task.reminder_time:
                        reminder = Reminder(
                            user_id=current_user.id,
                            task_id=next_task.id,
                            contact_id=next_task.contact_id,
                            deal_id=next_task.deal_id,
                            title=f"Görev Hatırlatıcı: {next_task.title}",
                            message=f"Görev bilgileri: {next_task.description}",
                            reminder_time=next_task.reminder_time,
                            notification_type="app"
                        )
                        db.session.add(reminder)
        else:
            task.completed_at = None
        
        db.session.commit()
        
        # Hatırlatıcıları güncelle
        if task.status == "Tamamlandı":
            # Görev tamamlandıysa, hatırlatıcıyı gönderildi olarak işaretle
            reminder = Reminder.query.filter_by(task_id=task.id, user_id=current_user.id).first()
            if reminder and not reminder.is_sent:
                reminder.is_sent = True
                reminder.sent_at = datetime.utcnow()
                db.session.commit()
    
    # Kullanıcıyı geldiği sayfaya geri gönder
    return redirect(request.referrer or url_for('task.tasks_list'))

@task_bp.route('/check-reminders')
@login_required
def check_reminders():
    """Kullanıcının bekleyen hatırlatıcılarını kontrol et."""
    # Zamanı gelen ve henüz gönderilmemiş hatırlatıcılar
    due_reminders = Reminder.query.filter(
        Reminder.user_id == current_user.id,
        Reminder.is_sent == False,
        Reminder.reminder_time <= datetime.utcnow()
    ).all()
    
    reminders_data = []
    for reminder in due_reminders:
        # Hatırlatıcıyı gönderildi olarak işaretle
        reminder.is_sent = True
        reminder.sent_at = datetime.utcnow()
        
        # Front-end için veri hazırla
        reminder_data = {
            'id': reminder.id,
            'title': reminder.title,
            'message': reminder.message,
            'time': reminder.reminder_time.strftime('%d.%m.%Y %H:%M'),
            'type': reminder.notification_type,
        }
        
        if reminder.task_id:
            reminder_data['task_url'] = url_for('task.task_edit', task_id=reminder.task_id)
        if reminder.contact_id:
            reminder_data['contact_name'] = reminder.contact.first_name + ' ' + reminder.contact.last_name if reminder.contact else ""
        if reminder.deal_id:
            reminder_data['deal_title'] = reminder.deal.title if reminder.deal else ""
        
        reminders_data.append(reminder_data)
    
    db.session.commit()
    
    return jsonify({
        'reminders': reminders_data,
        'count': len(reminders_data)
    })

# Bu blueprint'i ana uygulamaya kaydetmek için
def init_app(app):
    app.register_blueprint(task_bp)
