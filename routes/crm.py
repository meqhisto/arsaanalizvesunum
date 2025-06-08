from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, abort
from models.crm_models import Contact, Company, Interaction, Deal, Task, Activity, CrmSettings
from models.db import db
from datetime import datetime, timedelta
from functools import wraps
import json
import os
from werkzeug.utils import secure_filename
import logging
from sqlalchemy import text, func, desc, or_, and_

# Blueprint tanımı
crm = Blueprint('crm', __name__, url_prefix='/crm')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Yardımcı fonksiyonlar
def get_user_id():
    """Oturum açmış kullanıcının ID'sini döndürür"""
    return session.get('user_id')

def log_activity(user_id, activity_type, entity_type, entity_id, description, 
                contact_id=None, company_id=None, deal_id=None, task_id=None):
    """CRM aktivitelerini kaydetmek için yardımcı fonksiyon"""
    try:
        activity = Activity(
            user_id=user_id,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            contact_id=contact_id,
            company_id=company_id,
            deal_id=deal_id,
            task_id=task_id
        )
        db.session.add(activity)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logging.error(f"Activity log error: {str(e)}")
        return False

def get_user_settings(user_id):
    """Kullanıcının CRM ayarlarını döndürür, yoksa varsayılan ayarlar oluşturur"""
    settings = CrmSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = CrmSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()
    return settings

@crm.route('/dashboard')
@login_required
def dashboard():
    user_id = get_user_id()
    
    # İstatistikler
    contact_count = Contact.query.filter_by(user_id=user_id).count()
    company_count = Company.query.filter_by(user_id=user_id).count()
    deal_count = Deal.query.filter_by(user_id=user_id).count()
    task_count = Task.query.filter_by(user_id=user_id).count()
    
    # Açık fırsatlar (Kazanılmadı veya Kaybedilmedi)
    open_deals = Deal.query.filter(
        Deal.user_id == user_id,
        ~Deal.stage.in_(['Kazanıldı', 'Kaybedildi'])
    ).order_by(Deal.expected_close_date).limit(5).all()
    
    # Yaklaşan görevler
    upcoming_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.status != 'Tamamlandı',
        Task.due_date >= datetime.utcnow()
    ).order_by(Task.due_date).limit(5).all()
    
    # Son aktiviteler
    recent_activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.created_at.desc()).limit(10).all()
    
    # Son eklenen kişiler
    recent_contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.created_at.desc()).limit(5).all()
    
    # Fırsat durumu dağılımı
    deal_stages = db.session.query(
        Deal.stage, func.count(Deal.id).label('count'), func.sum(Deal.value).label('total_value')
    ).filter(Deal.user_id == user_id).group_by(Deal.stage).all()
    
    # Aylık fırsat değeri
    monthly_deals = db.session.query(
        func.date_format(Deal.created_at, '%Y-%m').label('month'),
        func.sum(Deal.value).label('total_value')
    ).filter(Deal.user_id == user_id).group_by('month').order_by('month').limit(6).all()
    
    return render_template('crm/dashboard.html',
                          contact_count=contact_count,
                          company_count=company_count,
                          deal_count=deal_count,
                          task_count=task_count,
                          open_deals=open_deals,
                          upcoming_tasks=upcoming_tasks,
                          recent_activities=recent_activities,
                          recent_contacts=recent_contacts,
                          deal_stages=deal_stages,
                          monthly_deals=monthly_deals)

# -------- CONTACT (KİŞİ) İŞLEMLERİ --------

@crm.route('/contacts')
@login_required
def contacts_list():
    """Kişiler listesi sayfası"""
    user_id = get_user_id()
    # Kullanıcının kendi kişilerini, soyadına ve adına göre sıralı alalım
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    return render_template("crm/contacts_list.html", contacts=contacts, title="Kişiler")


@crm.route('/contact/<int:contact_id>')
@login_required
def contact_detail(contact_id):
    """Kişi detay sayfası"""
    user_id = get_user_id()
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    interactions = contact.interactions.order_by(Interaction.interaction_date.desc()).all()
    
    tasks = contact.tasks.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"),
        Task.due_date.asc(),
        Task.priority.desc()
    ).all()
    
    deals = contact.deals.order_by(Deal.expected_close_date).all()
    activities = Activity.query.filter_by(contact_id=contact_id).order_by(Activity.created_at.desc()).limit(20).all()
    
    return render_template(
        "crm/contact_detail.html",
        contact=contact,
        title=f"{contact.first_name} {contact.last_name}",
        interactions=interactions,
        tasks=tasks,
        deals=deals,
        activities=activities
    )


@crm.route('/contact/new', methods=["GET", "POST"])
@login_required
def contact_new():
    """Yeni kişi ekleme sayfası"""
    user_id = get_user_id()
    # Mevcut şirketleri al (forma göndermek için)
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == "POST":
        # Form verilerini al
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        company_id_str = request.form.get("company_id")
        role = request.form.get("role")
        status = request.form.get("status")
        source = request.form.get("source")
        notes = request.form.get("notes")
        
        # Yeni alanlar
        address = request.form.get("address")
        city = request.form.get("city")
        country = request.form.get("country")
        postal_code = request.form.get("postal_code")
        birthday = request.form.get("birthday")
        linkedin = request.form.get("linkedin")
        twitter = request.form.get("twitter")
        tags = request.form.get("tags")
        lead_score = request.form.get("lead_score", 0)

        # Temel Doğrulama
        if not first_name or not last_name:
            flash("Ad ve Soyad alanları zorunludur.", "danger")
            return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", contact=request.form, companies=companies)

        # E-posta benzersizlik kontrolü
        if email:
            existing_contact = Contact.query.filter_by(user_id=user_id, email=email).first()
            if existing_contact:
                flash(f"'{email}' e-posta adresi ile kayıtlı başka bir kişi zaten mevcut.", "warning")
                return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", contact=request.form, companies=companies)
        
        try:
            # Tarih alanını işle
            birthday_date = None
            if birthday:
                try:
                    birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()
                except ValueError:
                    flash("Doğum tarihi geçerli bir format değil (YYYY-MM-DD).", "warning")
            
            # Lead score'u sayıya çevir
            try:
                lead_score = int(lead_score) if lead_score else 0
            except ValueError:
                lead_score = 0
            
            new_contact = Contact(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                company_id=int(company_id_str) if company_id_str else None,
                role=role,
                status=status,
                source=source,
                notes=notes,
                address=address,
                city=city,
                country=country,
                postal_code=postal_code,
                birthday=birthday_date,
                linkedin=linkedin,
                twitter=twitter,
                tags=tags,
                lead_score=lead_score
            )
            db.session.add(new_contact)
            db.session.commit()
            
            # Aktivite kaydı oluştur
            log_activity(
                user_id=user_id,
                activity_type="create",
                entity_type="contact",
                entity_id=new_contact.id,
                description=f"Yeni kişi oluşturuldu: {new_contact.first_name} {new_contact.last_name}",
                contact_id=new_contact.id
            )
            
            flash(f"'{new_contact.first_name} {new_contact.last_name}' adlı kişi başarıyla eklendi.", "success")
            return redirect(url_for("crm.contacts_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Kişi eklenirken bir hata oluştu: {str(e)}", "danger")
            logging.error(f"CRM Contact New Error: {e}")
            # Hata durumunda formu ve şirket listesini tekrar gönder
            return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", contact=request.form, companies=companies)

    # GET isteği için formu ve şirket listesini gönder
    return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", companies=companies)


@crm.route('/contact/<int:contact_id>/edit', methods=["GET", "POST"])
@login_required
def contact_edit(contact_id):
    """Kişi düzenleme sayfası"""
    user_id = get_user_id()
    contact_to_edit = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == "POST":
        # Formdan gelen verileri al
        contact_to_edit.first_name = request.form.get("first_name")
        contact_to_edit.last_name = request.form.get("last_name")
        new_email = request.form.get("email")
        contact_to_edit.phone = request.form.get("phone")
        contact_to_edit.company_id = int(request.form.get("company_id")) if request.form.get("company_id") else None
        contact_to_edit.role = request.form.get("role")
        contact_to_edit.status = request.form.get("status")
        contact_to_edit.source = request.form.get("source")
        contact_to_edit.notes = request.form.get("notes")
        
        # Yeni alanlar
        contact_to_edit.address = request.form.get("address")
        contact_to_edit.city = request.form.get("city")
        contact_to_edit.country = request.form.get("country")
        contact_to_edit.postal_code = request.form.get("postal_code")
        birthday = request.form.get("birthday")
        contact_to_edit.linkedin = request.form.get("linkedin")
        contact_to_edit.twitter = request.form.get("twitter")
        contact_to_edit.tags = request.form.get("tags")
        lead_score = request.form.get("lead_score", 0)

        # Temel Doğrulama
        if not contact_to_edit.first_name or not contact_to_edit.last_name:
            flash("Ad ve Soyad alanları zorunludur.", "danger")
            return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

        # E-posta benzersizlik kontrolü (kullanıcı bazında, mevcut kişi hariç)
        if new_email and new_email != contact_to_edit.email:
            existing_contact = Contact.query.filter(
                Contact.user_id == user_id,
                Contact.email == new_email,
                Contact.id != contact_id
            ).first()
            if existing_contact:
                flash(f"'{new_email}' e-posta adresi ile kayıtlı başka bir kişi zaten mevcut.", "warning")
                return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)
        
        try:
            # Tarih alanını işle
            if birthday:
                try:
                    contact_to_edit.birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
                except ValueError:
                    flash("Doğum tarihi geçerli bir format değil (YYYY-MM-DD).", "warning")
            
            # Lead score'u sayıya çevir
            try:
                contact_to_edit.lead_score = int(lead_score) if lead_score else 0
            except ValueError:
                contact_to_edit.lead_score = 0
            
            # E-posta güncelle
            contact_to_edit.email = new_email
            
            db.session.commit()
            
            # Aktivite kaydı oluştur
            log_activity(
                user_id=user_id,
                activity_type="update",
                entity_type="contact",
                entity_id=contact_id,
                description=f"Kişi güncellendi: {contact_to_edit.first_name} {contact_to_edit.last_name}",
                contact_id=contact_id
            )
            
            flash(f"'{contact_to_edit.first_name} {contact_to_edit.last_name}' adlı kişi başarıyla güncellendi.", "success")
            return redirect(url_for("crm.contact_detail", contact_id=contact_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Kişi güncellenirken bir hata oluştu: {str(e)}", "danger")
            logging.error(f"CRM Contact Edit Error: {e}")
            return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

    # GET isteği için formu ve şirket listesini gönder
    return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)


@crm.route('/contact/<int:contact_id>/delete', methods=["POST"])
@login_required
def contact_delete(contact_id):
    """Kişi silme işlemi"""
    user_id = get_user_id()
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    
    try:
        contact_name = f"{contact.first_name} {contact.last_name}"
        
        # Aktivite kaydı oluştur (silmeden önce)
        log_activity(
            user_id=user_id,
            activity_type="delete",
            entity_type="contact",
            entity_id=contact_id,
            description=f"Kişi silindi: {contact_name}"
        )
        
        db.session.delete(contact)
        db.session.commit()
        flash(f"'{contact_name}' adlı kişi başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Kişi silinirken bir hata oluştu: {str(e)}", "danger")
        logging.error(f"CRM Contact Delete Error: {e}")
    
    return redirect(url_for("crm.contacts_list"))


@crm.route('/api/contacts', methods=['GET'])
@login_required
def api_contacts():
    """Kişiler için API endpoint'i"""
    user_id = get_user_id()
    search_term = request.args.get('q', '')
    
    # Arama terimi varsa filtreleme yap
    if search_term:
        contacts = Contact.query.filter(
            Contact.user_id == user_id,
            or_(
                Contact.first_name.ilike(f'%{search_term}%'),
                Contact.last_name.ilike(f'%{search_term}%'),
                Contact.email.ilike(f'%{search_term}%'),
                Contact.phone.ilike(f'%{search_term}%')
            )
        ).order_by(Contact.last_name, Contact.first_name).all()
    else:
        contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    
    return jsonify([contact.to_dict() for contact in contacts])


@crm.route('/api/contacts/<int:contact_id>', methods=['GET'])
@login_required
def api_contact_detail(contact_id):
    """Kişi detayı için API endpoint'i"""
    user_id = get_user_id()
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    return jsonify(contact.to_dict())

# -------- COMPANY (ŞİRKET) İŞLEMLERİ --------

@crm.route('/companies')
@login_required
def companies_list():
    """Şirketler listesi sayfası"""
    user_id = get_user_id()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()
    return render_template("crm/companies_list.html", companies=companies, title="Şirketler")


@crm.route('/company/<int:company_id>')
@login_required
def company_detail(company_id):
    """Şirket detay sayfası"""
    user_id = get_user_id()
    company = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    
    # Şirketle ilişkili kişiler
    contacts = company.contacts.order_by(Contact.last_name, Contact.first_name).all()
    
    # Şirketle ilişkili fırsatlar
    deals = company.deals.order_by(Deal.expected_close_date).all()
    
    # Şirket aktiviteleri
    activities = Activity.query.filter_by(company_id=company_id).order_by(Activity.created_at.desc()).limit(20).all()
    
    return render_template(
        "crm/company_detail.html",
        company=company,
        title=company.name,
        contacts=contacts,
        deals=deals,
        activities=activities
    )


@crm.route('/company/new', methods=["GET", "POST"])
@login_required
def company_new():
    """Yeni şirket ekleme sayfası"""
    user_id = get_user_id()
    
    if request.method == "POST":
        # Form verilerini al
        name = request.form.get("name")
        industry = request.form.get("industry")
        website = request.form.get("website")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        city = request.form.get("city")
        country = request.form.get("country")
        postal_code = request.form.get("postal_code")
        employee_count = request.form.get("employee_count")
        annual_revenue = request.form.get("annual_revenue")
        linkedin = request.form.get("linkedin")
        twitter = request.form.get("twitter")
        facebook = request.form.get("facebook")
        tags = request.form.get("tags")
        notes = request.form.get("notes")
        
        # Temel Doğrulama
        if not name:
            flash("Şirket adı zorunludur.", "danger")
            return render_template("crm/company_form.html", title="Yeni Şirket Ekle", company=request.form)
        
        # Şirket adı benzersizlik kontrolü
        existing_company = Company.query.filter_by(user_id=user_id, name=name).first()
        if existing_company:
            flash(f"'{name}' adında bir şirket zaten mevcut.", "warning")
            return render_template("crm/company_form.html", title="Yeni Şirket Ekle", company=request.form)
        
        try:
            # Sayısal alanları işle
            try:
                employee_count_int = int(employee_count) if employee_count else None
            except ValueError:
                employee_count_int = None
                flash("Çalışan sayısı geçerli bir sayı olmalıdır.", "warning")
            
            try:
                annual_revenue_float = float(annual_revenue.replace(',', '.')) if annual_revenue else None
            except ValueError:
                annual_revenue_float = None
                flash("Yıllık gelir geçerli bir sayı olmalıdır.", "warning")
            
            new_company = Company(
                user_id=user_id,
                name=name,
                industry=industry,
                website=website,
                email=email,
                phone=phone,
                address=address,
                city=city,
                country=country,
                postal_code=postal_code,
                employee_count=employee_count_int,
                annual_revenue=annual_revenue_float,
                linkedin=linkedin,
                twitter=twitter,
                facebook=facebook,
                tags=tags,
                notes=notes
            )
            db.session.add(new_company)
            db.session.commit()
            
            # Aktivite kaydı oluştur
            log_activity(
                user_id=user_id,
                activity_type="create",
                entity_type="company",
                entity_id=new_company.id,
                description=f"Yeni şirket oluşturuldu: {new_company.name}",
                company_id=new_company.id
            )
            
            flash(f"'{new_company.name}' adlı şirket başarıyla eklendi.", "success")
            return redirect(url_for("crm.companies_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Şirket eklenirken bir hata oluştu: {str(e)}", "danger")
            logging.error(f"CRM Company New Error: {e}")
            return render_template("crm/company_form.html", title="Yeni Şirket Ekle", company=request.form)
    
    # GET isteği için formu gönder
    return render_template("crm/company_form.html", title="Yeni Şirket Ekle")


@crm.route('/company/<int:company_id>/edit', methods=["GET", "POST"])
@login_required
def company_edit(company_id):
    """Şirket düzenleme sayfası"""
    user_id = get_user_id()
    company_to_edit = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    
    if request.method == "POST":
        # Formdan gelen verileri al
        new_name = request.form.get("name")
        company_to_edit.industry = request.form.get("industry")
        company_to_edit.website = request.form.get("website")
        company_to_edit.email = request.form.get("email")
        company_to_edit.phone = request.form.get("phone")
        company_to_edit.address = request.form.get("address")
        company_to_edit.city = request.form.get("city")
        company_to_edit.country = request.form.get("country")
        company_to_edit.postal_code = request.form.get("postal_code")
        employee_count = request.form.get("employee_count")
        annual_revenue = request.form.get("annual_revenue")
        company_to_edit.linkedin = request.form.get("linkedin")
        company_to_edit.twitter = request.form.get("twitter")
        company_to_edit.facebook = request.form.get("facebook")
        company_to_edit.tags = request.form.get("tags")
        company_to_edit.notes = request.form.get("notes")
        
        # Temel Doğrulama
        if not new_name:
            flash("Şirket adı zorunludur.", "danger")
            return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit, edit_mode=True)
        
        # Şirket adı benzersizlik kontrolü (kullanıcı bazında, mevcut şirket hariç)
        if new_name != company_to_edit.name:
            existing_company = Company.query.filter(
                Company.user_id == user_id,
                Company.name == new_name,
                Company.id != company_id
            ).first()
            if existing_company:
                flash(f"'{new_name}' adında bir şirket zaten mevcut.", "warning")
                return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit, edit_mode=True)
        
        try:
            # Sayısal alanları işle
            try:
                company_to_edit.employee_count = int(employee_count) if employee_count else None
            except ValueError:
                flash("Çalışan sayısı geçerli bir sayı olmalıdır.", "warning")
            
            try:
                company_to_edit.annual_revenue = float(annual_revenue.replace(',', '.')) if annual_revenue else None
            except ValueError:
                flash("Yıllık gelir geçerli bir sayı olmalıdır.", "warning")
            
            # Şirket adını güncelle
            company_to_edit.name = new_name
            
            db.session.commit()
            
            # Aktivite kaydı oluştur
            log_activity(
                user_id=user_id,
                activity_type="update",
                entity_type="company",
                entity_id=company_id,
                description=f"Şirket güncellendi: {company_to_edit.name}",
                company_id=company_id
            )
            
            flash(f"'{company_to_edit.name}' adlı şirket başarıyla güncellendi.", "success")
            return redirect(url_for("crm.company_detail", company_id=company_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Şirket güncellenirken bir hata oluştu: {str(e)}", "danger")
            logging.error(f"CRM Company Edit Error: {e}")
            return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit, edit_mode=True)
    
    # GET isteği için formu gönder
    return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit, edit_mode=True)


@crm.route('/company/<int:company_id>/delete', methods=["POST"])
@login_required
def company_delete(company_id):
    """Şirket silme işlemi"""
    user_id = get_user_id()
    company = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    
    # Şirketle ilişkili kişi sayısını kontrol et
    contact_count = company.contacts.count()
    if contact_count > 0:
        flash(f"Bu şirket {contact_count} kişi ile ilişkilidir. Önce ilişkili kişileri silmeli veya başka bir şirkete taşımalısınız.", "warning")
        return redirect(url_for("crm.company_detail", company_id=company_id))
    
    try:
        company_name = company.name
        
        # Aktivite kaydı oluştur (silmeden önce)
        log_activity(
            user_id=user_id,
            activity_type="delete",
            entity_type="company",
            entity_id=company_id,
            description=f"Şirket silindi: {company_name}"
        )
        
        db.session.delete(company)
        db.session.commit()
        flash(f"'{company_name}' adlı şirket başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Şirket silinirken bir hata oluştu: {str(e)}", "danger")
        logging.error(f"CRM Company Delete Error: {e}")
    
    return redirect(url_for("crm.companies_list"))


@crm.route('/api/companies', methods=['GET'])
@login_required
def api_companies():
    """Şirketler için API endpoint'i"""
    user_id = get_user_id()
    search_term = request.args.get('q', '')
    
    # Arama terimi varsa filtreleme yap
    if search_term:
        companies = Company.query.filter(
            Company.user_id == user_id,
            or_(
                Company.name.ilike(f'%{search_term}%'),
                Company.industry.ilike(f'%{search_term}%'),
                Company.email.ilike(f'%{search_term}%'),
                Company.phone.ilike(f'%{search_term}%')
            )
        ).order_by(Company.name).all()
    else:
        companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()
    
    return jsonify([company.to_dict() for company in companies])


@crm.route('/api/companies/<int:company_id>', methods=['GET'])
@login_required
def api_company_detail(company_id):
    """Şirket detayı için API endpoint'i"""
    user_id = get_user_id()
    company = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    return jsonify(company.to_dict())

# -------- DEAL (FIRSAT) İŞLEMLERİ --------

@crm.route('/deals')
@login_required
def deals_list():
    """Fırsatlar listesi sayfası"""
    user_id = get_user_id()
    deals = Deal.query.filter_by(user_id=user_id).order_by(Deal.expected_close_date).all()
    
    # Fırsat aşamaları için istatistikler
    stage_stats = db.session.query(
        Deal.stage, func.count(Deal.id).label('count'), func.sum(Deal.value).label('total_value')
    ).filter(Deal.user_id == user_id).group_by(Deal.stage).all()
    
    # Fırsat durumları için istatistikler
    stage_data = {}
    for stage, count, total_value in stage_stats:
        stage_data[stage] = {
            'count': count,
            'total_value': float(total_value) if total_value else 0
        }
    
    return render_template(
        "crm/deals_list.html", 
        deals=deals, 
        title="Fırsatlar",
        stage_data=stage_data
    )


@crm.route('/deal/<int:deal_id>')
@login_required
def deal_detail(deal_id):
    """Fırsat detay sayfası"""
    user_id = get_user_id()
    deal = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    
    # Fırsatla ilişkili etkileşimler
    interactions = deal.interactions.order_by(Interaction.interaction_date.desc()).all()
    
    # Fırsatla ilişkili görevler
    tasks = deal.tasks.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"),
        Task.due_date.asc(),
        Task.priority.desc()
    ).all()
    
    # Fırsat aktiviteleri
    activities = Activity.query.filter_by(deal_id=deal_id).order_by(Activity.created_at.desc()).limit(20).all()
    
    return render_template(
        "crm/deal_detail.html",
        deal=deal,
        title=deal.title,
        interactions=interactions,
        tasks=tasks,
        activities=activities
    )


@crm.route('/deal/new', methods=["GET", "POST"])
@login_required
def deal_new():
    """Yeni fırsat ekleme sayfası"""
    user_id = get_user_id()
    
    # Formda kullanılacak kişi ve şirket listelerini al
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()
    
    # Kullanıcı ayarlarından fırsat aşamalarını al
    settings = get_user_settings(user_id)
    try:
        deal_stages = json.loads(settings.deal_stages)
    except (json.JSONDecodeError, AttributeError):
        deal_stages = ["Potansiyel", "İlk Görüşme", "Teklif", "Müzakere", "Kazanıldı", "Kaybedildi"]
    
    if request.method == "POST":
        # Form verilerini al
        title = request.form.get("title")
        contact_id_str = request.form.get("contact_id")
        company_id_str = request.form.get("company_id")
        value = request.form.get("value")
        currency = request.form.get("currency")
        stage = request.form.get("stage")
        probability = request.form.get("probability")
        expected_close_date = request.form.get("expected_close_date")
        source = request.form.get("source")
        notes = request.form.get("notes")
        products = request.form.get("products")
        tags = request.form.get("tags")
        priority = request.form.get("priority")
        
        # Temel Doğrulama
        if not title:
            flash("Fırsat başlığı zorunludur.", "danger")
            return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", deal=request.form, contacts=contacts, companies=companies, deal_stages=deal_stages)
        
        if not contact_id_str:
            flash("Kişi seçimi zorunludur.", "danger")
            return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", deal=request.form, contacts=contacts, companies=companies, deal_stages=deal_stages)
        
        try:
            # Sayısal alanları işle
            try:
                value_float = float(value.replace(',', '.')) if value else 0.0
            except ValueError:
                value_float = 0.0
                flash("Değer geçerli bir sayı olmalıdır.", "warning")
            
            try:
                probability_int = int(probability) if probability else 0
                # 0-100 arasında olduğunu kontrol et
                probability_int = max(0, min(100, probability_int))
            except ValueError:
                probability_int = 0
                flash("Olasılık geçerli bir sayı olmalıdır (0-100).", "warning")
            
            # Tarih alanını işle
            expected_close_date_obj = None
            if expected_close_date:
                try:
                    expected_close_date_obj = datetime.strptime(expected_close_date, "%Y-%m-%d").date()
                except ValueError:
                    flash("Beklenen kapanış tarihi geçerli bir format değil (YYYY-MM-DD).", "warning")
            
            new_deal = Deal(
                user_id=user_id,
                title=title,
                contact_id=int(contact_id_str),
                company_id=int(company_id_str) if company_id_str else None,
                value=value_float,
                currency=currency,
                stage=stage,
                probability=probability_int,
                expected_close_date=expected_close_date_obj,
                source=source,
                notes=notes,
                products=products,
                tags=tags,
                priority=priority
            )
            db.session.add(new_deal)
            db.session.commit()
            
            # Aktivite kaydı oluştur
            log_activity(
                user_id=user_id,
                activity_type="create",
                entity_type="deal",
                entity_id=new_deal.id,
                description=f"Yeni fırsat oluşturuldu: {new_deal.title}",
                deal_id=new_deal.id,
                contact_id=new_deal.contact_id,
                company_id=new_deal.company_id
            )
            
            flash(f"'{new_deal.title}' adlı fırsat başarıyla eklendi.", "success")
            return redirect(url_for("crm.deals_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Fırsat eklenirken bir hata oluştu: {str(e)}", "danger")
            logging.error(f"CRM Deal New Error: {e}")
            return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", deal=request.form, contacts=contacts, companies=companies, deal_stages=deal_stages)
    
    # GET isteği için formu gönder
    return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, deal_stages=deal_stages)


@crm.route('/api/interactions', methods=['POST'])
@login_required
def add_interaction():
    user_id = get_user_id()
    data = request.form
    
    try:
        interaction = Interaction(
            user_id=user_id,
            contact_id=int(data['contact_id']),
            deal_id=int(data['deal_id']) if data.get('deal_id') else None,
            type=data['type'],
            interaction_date=datetime.fromisoformat(data['interaction_date']) if data.get('interaction_date') else datetime.utcnow(),
            summary=data['summary'],
            outcome=data.get('outcome'),
            next_steps=data.get('next_steps'),
            duration_minutes=int(data.get('duration_minutes', 0)) if data.get('duration_minutes') else None,
            location=data.get('location')
        )
        db.session.add(interaction)
        db.session.commit()
        
        # Aktivite kaydı oluştur
        log_activity(
            user_id=user_id,
            activity_type="create",
            entity_type="interaction",
            entity_id=interaction.id,
            description=f"Yeni etkileşim oluşturuldu: {interaction.type}",
            contact_id=interaction.contact_id,
            deal_id=interaction.deal_id
        )
        
        return jsonify({'success': True, 'id': interaction.id})
    except Exception as e:
        db.session.rollback()
        logging.error(f"CRM Interaction Add Error: {e}")
        return jsonify({'success': False, 'error': str(e)})
