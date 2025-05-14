# blueprints/crm_bp.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import text, cast, Date # Sorgular için

# Modelleri ve db nesnesini models paketinden import et
from models import db
from models.user_models import User
from models.crm_models import Contact, Company, Interaction, Deal, Task

# Flask uygulamasının yapılandırmasına erişmek için current_app
from flask import current_app

crm_bp = Blueprint('crm', __name__, template_folder='../templates/crm')
# template_folder='../templates/crm' ayarı, şablonların ana 'templates/crm' klasöründe olduğunu varsayar.

# --- SABİTLER (Eski app.py'den taşındı, bir constants.py dosyasına da alınabilir) ---
DEAL_STAGES = ["Potansiyel", "Görüşme Planlandı", "Teklif Sunuldu", "Müzakere", "Kazanıldı", "Kaybedildi", "Beklemede"]
TASK_STATUSES = ["Beklemede", "Devam Ediyor", "Tamamlandı", "İptal Edildi", "Ertelendi"]
TASK_PRIORITIES = ["Düşük", "Normal", "Yüksek", "Acil"]

# --- KİŞİ (CONTACT) ROTALARI ---
@crm_bp.route('/contacts')
@login_required
def crm_contacts_list():
    user_id = current_user.id
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    return render_template('contacts_list.html', contacts=contacts, title="Kişiler")

@crm_bp.route('/contact/new', methods=['GET', 'POST'])
@login_required
def crm_contact_new():
    user_id = current_user.id
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        company_id_str = request.form.get('company_id')
        role = request.form.get('role', '').strip()
        status = request.form.get('status', 'Lead')
        source = request.form.get('source', '').strip()
        notes = request.form.get('notes', '').strip()
        # CRM V2 alanları
        segment = request.form.get('segment', 'Potansiyel')
        value_score_str = request.form.get('value_score', '0')
        tags_json = request.form.get('tags', '[]') # Formdan JSON string olarak gelecek

        if not first_name or not last_name:
            flash('Ad ve Soyad alanları zorunludur.', 'danger')
            return render_template('contact_form.html', title="Yeni Kişi Ekle", contact=request.form, companies=companies)

        if email:
            existing_contact = Contact.query.filter_by(user_id=user_id, email=email).first()
            if existing_contact:
                flash(f"'{email}' e-posta adresi ile kayıtlı başka bir kişi zaten mevcut.", 'warning')
                return render_template('contact_form.html', title="Yeni Kişi Ekle", contact=request.form, companies=companies)
        
        try:
            tags_list = json.loads(tags_json) if tags_json else []
            if not isinstance(tags_list, list): tags_list = []
        except json.JSONDecodeError:
            tags_list = []
            flash("Etiket verisi geçersiz formatta, etiketler kaydedilemedi.", "warning")


        try:
            new_contact = Contact(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email if email else None,
                phone=phone if phone else None,
                company_id=int(company_id_str) if company_id_str else None,
                role=role if role else None,
                status=status,
                source=source if source else None,
                notes=notes if notes else None,
                segment=segment,
                value_score=int(value_score_str) if value_score_str.isdigit() else 0,
                tags=tags_list
            )
            db.session.add(new_contact)
            db.session.commit()
            flash(f"'{new_contact.first_name} {new_contact.last_name}' adlı kişi başarıyla eklendi.", 'success')
            return redirect(url_for('crm.crm_contacts_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Contact New Error: {e}", exc_info=True)
            flash(f'Kişi eklenirken bir hata oluştu: {str(e)}', 'danger')
            # Hata durumunda form verilerini şablona geri gönder
            return render_template('contact_form.html', title="Yeni Kişi Ekle", contact=request.form, companies=companies)

    return render_template('contact_form.html', title="Yeni Kişi Ekle", companies=companies, contact={})


@crm_bp.route('/contact/<int:contact_id>')
@login_required
def crm_contact_detail(contact_id):
    user_id = current_user.id
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    interactions = contact.interactions.order_by(Interaction.interaction_date.desc()).all()
    tasks = contact.tasks.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"), # SQL Server'da CASE WHEN
        Task.due_date.asc(),
        # Task.priority.desc() # Priority için sıralama enum veya case when gerektirebilir
    ).all()
    # Fırsatlar da eklenebilir
    # deals = contact.deals.order_by(Deal.created_at.desc()).all()
    return render_template('contact_detail.html', contact=contact, title=f"{contact.first_name} {contact.last_name}", interactions=interactions, tasks=tasks)


@crm_bp.route('/contact/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def crm_contact_edit(contact_id):
    user_id = current_user.id
    contact_to_edit = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == 'POST':
        contact_to_edit.first_name = request.form.get('first_name', '').strip()
        contact_to_edit.last_name = request.form.get('last_name', '').strip()
        new_email = request.form.get('email', '').strip()
        contact_to_edit.phone = request.form.get('phone', '').strip()
        contact_to_edit.company_id = int(request.form.get('company_id')) if request.form.get('company_id') else None
        contact_to_edit.role = request.form.get('role', '').strip()
        contact_to_edit.status = request.form.get('status', 'Lead')
        contact_to_edit.source = request.form.get('source', '').strip()
        contact_to_edit.notes = request.form.get('notes', '').strip()
        # CRM V2 alanları
        contact_to_edit.segment = request.form.get('segment', contact_to_edit.segment)
        value_score_str = request.form.get('value_score', str(contact_to_edit.value_score))
        contact_to_edit.value_score = int(value_score_str) if value_score_str.isdigit() else contact_to_edit.value_score
        
        tags_json = request.form.get('tags', '[]')
        try:
            tags_list = json.loads(tags_json) if tags_json else []
            if not isinstance(tags_list, list): tags_list = contact_to_edit.tags # Hatalıysa eskiyi koru
            contact_to_edit.tags = tags_list
        except json.JSONDecodeError:
            flash("Etiket verisi geçersiz formatta, etiketler güncellenemedi.", "warning")
            # contact_to_edit.tags eski değeriyle kalır


        if not contact_to_edit.first_name or not contact_to_edit.last_name:
            flash('Ad ve Soyad alanları zorunludur.', 'danger')
            return render_template('contact_form.html', title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

        if new_email and new_email != contact_to_edit.email:
            existing_contact = Contact.query.filter(
                Contact.user_id == user_id,
                Contact.email == new_email,
                Contact.id != contact_id
            ).first()
            if existing_contact:
                flash(f"'{new_email}' e-posta adresi ile kayıtlı başka bir kişi zaten mevcut.", 'warning')
                return render_template('contact_form.html', title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)
        contact_to_edit.email = new_email if new_email else None

        try:
            db.session.commit()
            flash(f"'{contact_to_edit.first_name} {contact_to_edit.last_name}' adlı kişi başarıyla güncellendi.", 'success')
            return redirect(url_for('crm.crm_contact_detail', contact_id=contact_to_edit.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Contact Edit Error: {e}", exc_info=True)
            flash(f'Kişi güncellenirken bir hata oluştu: {str(e)}', 'danger')
            return render_template('contact_form.html', title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

    return render_template('contact_form.html', title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)


@crm_bp.route('/contact/<int:contact_id>/delete', methods=['POST'])
@login_required
def crm_contact_delete(contact_id):
    user_id = current_user.id
    contact_to_delete = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    try:
        contact_name = f"{contact_to_delete.first_name} {contact_to_delete.last_name}"
        # İlişkili kayıtlar (Interaction, Deal, Task) modeldeki cascade ayarlarıyla silinecek.
        db.session.delete(contact_to_delete)
        db.session.commit()
        flash(f"'{contact_name}' adlı kişi ve ilişkili tüm verileri başarıyla silindi.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Contact Delete Error: {e}", exc_info=True)
        flash(f'Kişi silinirken bir hata oluştu: {str(e)}', 'danger')
    return redirect(url_for('crm.crm_contacts_list'))


# --- ŞİRKET (COMPANY) ROTALARI ---
@crm_bp.route('/companies')
@login_required
def crm_companies_list():
    user_id = current_user.id
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()
    return render_template('companies_list.html', companies=companies, title="Şirketler")

@crm_bp.route('/company/new', methods=['GET', 'POST'])
@login_required
def crm_company_new():
    user_id = current_user.id
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        # ... (diğer company form alanları) ...
        industry = request.form.get('industry')
        website = request.form.get('website')
        address = request.form.get('address')
        phone = request.form.get('phone')
        notes = request.form.get('notes')

        if not name:
            flash('Şirket adı zorunludur.', 'danger')
            return render_template('company_form.html', title="Yeni Şirket Ekle", company=request.form)

        existing_company = Company.query.filter_by(user_id=user_id, name=name).first()
        if existing_company:
            flash(f"'{name}' adlı şirket zaten mevcut.", 'warning')
            return render_template('company_form.html', title="Yeni Şirket Ekle", company=request.form)
        
        try:
            new_company = Company(user_id=user_id, name=name, industry=industry, website=website, address=address, phone=phone, notes=notes)
            db.session.add(new_company)
            db.session.commit()
            flash(f"'{new_company.name}' adlı şirket başarıyla eklendi.", 'success')
            return redirect(url_for('crm.crm_companies_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Company New Error: {e}", exc_info=True)
            flash(f'Şirket eklenirken bir hata oluştu: {str(e)}', 'danger')
            return render_template('company_form.html', title="Yeni Şirket Ekle", company=request.form)
            
    return render_template('company_form.html', title="Yeni Şirket Ekle", company={})

@crm_bp.route('/company/<int:company_id>')
@login_required
def crm_company_detail(company_id):
    user_id = current_user.id
    company = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    company_contacts = company.contacts.order_by(Contact.last_name, Contact.first_name).all()
    company_deals = company.deals.order_by(Deal.created_at.desc()).all() # Fırsatları da alalım
    return render_template('company_detail.html', company=company, title=company.name, company_contacts=company_contacts, company_deals=company_deals)

@crm_bp.route('/company/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
def crm_company_edit(company_id):
    user_id = current_user.id
    company_to_edit = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    if request.method == 'POST':
        new_name = request.form.get('name', '').strip()
        # ... (diğer company form alanları) ...
        company_to_edit.industry = request.form.get('industry')
        company_to_edit.website = request.form.get('website')
        company_to_edit.address = request.form.get('address')
        company_to_edit.phone = request.form.get('phone')
        company_to_edit.notes = request.form.get('notes')


        if not new_name:
            flash('Şirket adı zorunludur.', 'danger')
            return render_template('company_form.html', title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)

        if new_name != company_to_edit.name:
            existing_company = Company.query.filter(Company.user_id == user_id, Company.name == new_name, Company.id != company_id).first()
            if existing_company:
                flash(f"'{new_name}' adlı başka bir şirket zaten mevcut.", 'warning')
                return render_template('company_form.html', title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)
        company_to_edit.name = new_name
        
        try:
            db.session.commit()
            flash(f"'{company_to_edit.name}' adlı şirket başarıyla güncellendi.", 'success')
            return redirect(url_for('crm.crm_company_detail', company_id=company_to_edit.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Company Edit Error: {e}", exc_info=True)
            flash(f'Şirket güncellenirken bir hata oluştu: {str(e)}', 'danger')
            return render_template('company_form.html', title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)
            
    return render_template('company_form.html', title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)

@crm_bp.route('/company/<int:company_id>/delete', methods=['POST'])
@login_required
def crm_company_delete(company_id):
    user_id = current_user.id
    company_to_delete = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    try:
        company_name = company_to_delete.name
        # Bağlı kişilerin company_id'lerini null yap (Modelde cascade delete yoksa)
        Contact.query.filter_by(company_id=company_id, user_id=user_id).update({"company_id": None})
        # Bağlı fırsatların company_id'lerini null yap (Modelde cascade delete yoksa)
        Deal.query.filter_by(company_id=company_id, user_id=user_id).update({"company_id": None})
        
        db.session.delete(company_to_delete)
        db.session.commit()
        flash(f"'{company_name}' adlı şirket başarıyla silindi. Bağlı kişi ve fırsatların şirket bağlantıları kaldırıldı.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Company Delete Error: {e}", exc_info=True)
        flash(f'Şirket silinirken bir hata oluştu: {str(e)}', 'danger')
    return redirect(url_for('crm.crm_companies_list'))


# --- ETKİLEŞİM (INTERACTION) ROTALARI ---
@crm_bp.route('/contact/<int:contact_id>/interaction/new', methods=['POST'])
@login_required
def crm_interaction_new(contact_id):
    user_id = current_user.id
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    deal_id_form = request.form.get("deal_id") # Formdan deal_id de gelebilir

    interaction_type = request.form.get('interaction_type')
    interaction_date_str = request.form.get('interaction_date')
    summary = request.form.get('summary')

    if not interaction_type or not interaction_date_str or not summary:
        flash('Etkileşim türü, tarihi ve özeti zorunludur.', 'danger')
        return redirect(url_for('crm.crm_contact_detail', contact_id=contact.id))

    try:
        interaction_datetime = datetime.strptime(interaction_date_str, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Geçersiz tarih formatı.', 'danger')
        return redirect(url_for('crm.crm_contact_detail', contact_id=contact.id))

    try:
        new_interaction = Interaction(
            user_id=user_id,
            contact_id=contact.id,
            deal_id=int(deal_id_form) if deal_id_form else None, # deal_id'yi de ekle
            type=interaction_type,
            interaction_date=interaction_datetime,
            summary=summary
        )
        db.session.add(new_interaction)
        db.session.commit()
        flash('Yeni etkileşim başarıyla eklendi.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Interaction New Error: {e}", exc_info=True)
        flash(f'Etkileşim eklenirken bir hata oluştu: {str(e)}', 'danger')
    
    # Eğer deal_id varsa ve etkileşim bir fırsatla da ilişkiliyse, fırsat detayına yönlendir.
    if new_interaction.deal_id:
        return redirect(url_for('crm.crm_deal_detail', deal_id=new_interaction.deal_id))
    return redirect(url_for('crm.crm_contact_detail', contact_id=contact.id))

@crm_bp.route('/interaction/<int:interaction_id>/delete', methods=['POST'])
@login_required
def crm_interaction_delete(interaction_id):
    user_id = current_user.id
    interaction_to_delete = Interaction.query.filter_by(id=interaction_id, user_id=user_id).first_or_404()
    
    contact_id_redirect = interaction_to_delete.contact_id
    deal_id_redirect = interaction_to_delete.deal_id

    try:
        db.session.delete(interaction_to_delete)
        db.session.commit()
        flash('Etkileşim başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Interaction Delete Error: {e}", exc_info=True)
        flash(f'Etkileşim silinirken bir hata oluştu: {str(e)}', 'danger')
    
    if deal_id_redirect:
        return redirect(url_for('crm.crm_deal_detail', deal_id=deal_id_redirect))
    elif contact_id_redirect:
        return redirect(url_for('crm.crm_contact_detail', contact_id=contact_id_redirect))
    return redirect(url_for('crm.crm_contacts_list'))


# --- FIRSAT (DEAL) ROTALARI ---
@crm_bp.route('/deals')
@login_required
def crm_deals_list():
    user_id = current_user.id
    deals_query = Deal.query.filter_by(user_id=user_id)
    
    deals_by_stage = {}
    for stage in DEAL_STAGES: # DEAL_STAGES bu BP içinde tanımlı
        deals_by_stage[stage] = deals_query.filter_by(stage=stage).order_by(Deal.expected_close_date.asc()).all()
    
    return render_template('deals_list.html', deals_by_stage=deals_by_stage, stages=DEAL_STAGES, title="Fırsatlar")

@crm_bp.route('/deal/new', methods=['GET', 'POST'])
@login_required
def crm_deal_new():
    user_id = current_user.id
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == 'POST':
        title_form = request.form.get('title') # Değişken adı çakışmaması için _form eklendi
        contact_id_str = request.form.get('contact_id')
        company_id_str = request.form.get('company_id')
        value_str = request.form.get('value', '0').replace(',', '')
        currency = request.form.get('currency', 'TRY')
        stage = request.form.get('stage', DEAL_STAGES[0])
        expected_close_date_str = request.form.get('expected_close_date')
        notes = request.form.get('notes')

        if not title_form or not contact_id_str:
            flash('Fırsat başlığı ve birincil kontak zorunludur.', 'danger')
            return render_template('deal_form.html', title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)

        try:
            value = Decimal(value_str) if value_str else Decimal('0.00')
        except:
            flash('Geçersiz değer formatı.', 'danger')
            return render_template('deal_form.html', title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)
        
        expected_close_date = None
        if expected_close_date_str:
            try:
                expected_close_date = datetime.strptime(expected_close_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Geçersiz beklenen kapanış tarihi formatı.', 'danger')
                return render_template('deal_form.html', title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)
        
        try:
            new_deal = Deal(
                user_id=user_id, title=title_form, contact_id=int(contact_id_str),
                company_id=int(company_id_str) if company_id_str else None,
                value=value, currency=currency, stage=stage,
                expected_close_date=expected_close_date, notes=notes
            )
            db.session.add(new_deal)
            db.session.commit()
            flash(f"'{new_deal.title}' adlı fırsat başarıyla eklendi.", 'success')
            return redirect(url_for('crm.crm_deals_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Deal New Error: {e}", exc_info=True)
            flash(f'Fırsat eklenirken bir hata oluştu: {str(e)}', 'danger')
            return render_template('deal_form.html', title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)

    return render_template('deal_form.html', title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal={})


@crm_bp.route('/deal/<int:deal_id>')
@login_required
def crm_deal_detail(deal_id):
    user_id = current_user.id
    deal = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    interactions = deal.interactions.order_by(Interaction.interaction_date.desc()).all()
    tasks = deal.tasks.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"),
        Task.due_date.asc(),
    ).all()
    return render_template('deal_detail.html', deal=deal, title=deal.title, interactions=interactions, tasks=tasks)

@crm_bp.route('/deal/<int:deal_id>/edit', methods=['GET', 'POST'])
@login_required
def crm_deal_edit(deal_id):
    user_id = current_user.id
    deal_to_edit = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == 'POST':
        deal_to_edit.title = request.form.get('title')
        contact_id_str = request.form.get('contact_id')
        company_id_str = request.form.get('company_id')
        value_str = request.form.get('value', '0').replace(',', '')
        deal_to_edit.currency = request.form.get('currency', 'TRY')
        deal_to_edit.stage = request.form.get('stage')
        expected_close_date_str = request.form.get('expected_close_date')
        actual_close_date_str = request.form.get('actual_close_date')
        deal_to_edit.notes = request.form.get('notes')

        if not deal_to_edit.title or not contact_id_str:
            flash('Fırsat başlığı ve birincil kontak zorunludur.', 'danger')
            return render_template('deal_form.html', title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)
        try:
            deal_to_edit.value = Decimal(value_str) if value_str else Decimal('0.00')
        except:
            flash('Geçersiz değer formatı.', 'danger')
            return render_template('deal_form.html', title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

        deal_to_edit.contact_id = int(contact_id_str)
        deal_to_edit.company_id = int(company_id_str) if company_id_str else None
        
        if expected_close_date_str:
            try: deal_to_edit.expected_close_date = datetime.strptime(expected_close_date_str, '%Y-%m-%d').date()
            except ValueError: flash('Geçersiz beklenen kapanış tarihi formatı.', 'danger'); return render_template('deal_form.html', title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)
        else: deal_to_edit.expected_close_date = None

        if deal_to_edit.stage in ["Kazanıldı", "Kaybedildi"] and actual_close_date_str:
            try: deal_to_edit.actual_close_date = datetime.strptime(actual_close_date_str, '%Y-%m-%d').date()
            except ValueError: flash('Geçersiz fiili kapanış tarihi formatı.', 'danger'); return render_template('deal_form.html', title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)
        elif deal_to_edit.stage not in ["Kazanıldı", "Kaybedildi"]:
             deal_to_edit.actual_close_date = None

        try:
            db.session.commit()
            flash(f"'{deal_to_edit.title}' adlı fırsat başarıyla güncellendi.", 'success')
            return redirect(url_for('crm.crm_deal_detail', deal_id=deal_to_edit.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Deal Edit Error: {e}", exc_info=True)
            flash(f'Fırsat güncellenirken bir hata oluştu: {str(e)}', 'danger')
            return render_template('deal_form.html', title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

    return render_template('deal_form.html', title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

@crm_bp.route('/deal/<int:deal_id>/delete', methods=['POST'])
@login_required
def crm_deal_delete(deal_id):
    user_id = current_user.id
    deal_to_delete = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    try:
        deal_title = deal_to_delete.title
        # İlişkili etkileşimler ve görevler modeldeki cascade ile silinecek
        db.session.delete(deal_to_delete)
        db.session.commit()
        flash(f"'{deal_title}' adlı fırsat başarıyla silindi.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Deal Delete Error: {e}", exc_info=True)
        flash(f'Fırsat silinirken bir hata oluştu: {str(e)}', 'danger')
    return redirect(url_for('crm.crm_deals_list'))


@crm_bp.route('/deal/<int:deal_id>/update_stage', methods=['POST'])
@login_required
def crm_deal_update_stage(deal_id):
    user_id = current_user.id
    deal_to_update = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    data = request.get_json()
    new_stage = data.get('stage')

    if not new_stage or new_stage not in DEAL_STAGES:
        return jsonify({'success': False, 'message': 'Geçersiz aşama.'}), 400

    try:
        old_stage = deal_to_update.stage
        deal_to_update.stage = new_stage
        if new_stage in ['Kazanıldı', 'Kaybedildi'] and not deal_to_update.actual_close_date:
            deal_to_update.actual_close_date = datetime.utcnow().date()
        elif old_stage in ['Kazanıldı', 'Kaybedildi'] and new_stage not in ['Kazanıldı', 'Kaybedildi']:
            deal_to_update.actual_close_date = None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Fırsat aşaması güncellendi.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Deal Update Stage Error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Sunucu hatası: {str(e)}'}), 500


# --- GÖREV (TASK) ROTALARI ---
@crm_bp.route('/tasks')
@login_required
def crm_tasks_list():
    user_id = current_user.id
    # Sadece kullanıcıya atanan veya kullanıcının oluşturduğu görevleri göster
    tasks_query = Task.query.filter(
        (Task.assigned_to_user_id == user_id) | (Task.user_id == user_id)
    )
    filter_status = request.args.get('status')
    if filter_status and filter_status in TASK_STATUSES:
        tasks_query = tasks_query.filter_by(status=filter_status)
    
    tasks = tasks_query.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"),
        Task.due_date.asc(),
        # Task.priority.desc() # Öncelik sıralaması için enum veya case when
    ).all()
    return render_template('tasks_list.html', tasks=tasks, title="Görevler", statuses=TASK_STATUSES, current_status=filter_status)

# Görev ekleme (genel, kişiye özel, fırsata özel)
@crm_bp.route('/task/new', methods=['GET', 'POST'])
@crm_bp.route('/contact/<int:related_contact_id>/task/new', methods=['GET', 'POST']) # Değişken adı güncellendi
@crm_bp.route('/deal/<int:related_deal_id>/task/new', methods=['GET', 'POST'])       # Değişken adı güncellendi
@login_required
def crm_task_new(related_contact_id=None, related_deal_id=None): # Değişken adları güncellendi
    user_id = current_user.id
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name).all()
    deals = Deal.query.filter_by(user_id=user_id).order_by(Deal.title).all()
    # users_for_assignment = User.query.filter_by(is_active=True).order_by(User.ad).all() # Eğer başkasına atama olacaksa

    preselected_contact = Contact.query.get(related_contact_id) if related_contact_id else None
    preselected_deal = Deal.query.get(related_deal_id) if related_deal_id else None

    if request.method == 'POST':
        title_form = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        status = request.form.get('status', TASK_STATUSES[0])
        priority = request.form.get('priority', TASK_PRIORITIES[1])
        contact_id_form = request.form.get('contact_id') # Formdan gelen
        deal_id_form = request.form.get('deal_id')       # Formdan gelen
        assigned_to_user_id_form = request.form.get('assigned_to_user_id', str(user_id)) # Varsayılan kendine ata
        
        # CRM V2 Eklemeler
        reminder_enabled_form = 'reminder_enabled' in request.form
        reminder_time_str = request.form.get('reminder_time')
        is_recurring_form = 'is_recurring' in request.form
        recurrence_type_form = request.form.get('recurrence_type')
        recurrence_interval_form = request.form.get('recurrence_interval')
        recurrence_end_date_str = request.form.get('recurrence_end_date')
        task_type_form = request.form.get('task_type', 'personal')


        if not title_form:
            flash('Görev başlığı zorunludur.', 'danger')
            return render_template('task_form.html', title="Yeni Görev Ekle", contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, preselected_contact=preselected_contact, preselected_deal=preselected_deal, task=request.form)
        
        due_date = None
        if due_date_str:
            try: due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError: flash('Geçersiz bitiş tarihi formatı.', 'danger'); return render_template('task_form.html', title="Yeni Görev Ekle", contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, preselected_contact=preselected_contact, preselected_deal=preselected_deal, task=request.form)
        
        reminder_time_dt = None
        if reminder_enabled_form and reminder_time_str:
            try: reminder_time_dt = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M')
            except ValueError: flash('Geçersiz hatırlatma zamanı formatı.', 'danger'); # Devam et, hatırlatıcı None olacak
        
        recurrence_end_date_dt = None
        if is_recurring_form and recurrence_end_date_str:
            try: recurrence_end_date_dt = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d').date()
            except ValueError: flash('Geçersiz tekrarlama bitiş tarihi formatı.', 'danger'); # Devam et

        try:
            new_task = Task(
                user_id=user_id, title=title_form, description=description, due_date=due_date,
                status=status, priority=priority,
                contact_id=int(contact_id_form) if contact_id_form else None,
                deal_id=int(deal_id_form) if deal_id_form else None,
                assigned_to_user_id=int(assigned_to_user_id_form) if assigned_to_user_id_form else user_id,
                # CRM V2
                reminder_enabled=reminder_enabled_form,
                reminder_time=reminder_time_dt,
                is_recurring=is_recurring_form,
                recurrence_type=recurrence_type_form if is_recurring_form else None,
                recurrence_interval=int(recurrence_interval_form) if is_recurring_form and recurrence_interval_form else 1,
                recurrence_end_date=recurrence_end_date_dt if is_recurring_form else None,
                task_type=task_type_form
            )
            # Eğer denetimli görevse ve atayan kişi broker ise assigned_by_user_id'yi ayarla
            if task_type_form == 'supervised' and current_user.role == 'broker' and new_task.assigned_to_user_id != user_id:
                 new_task.assigned_by_user_id = user_id


            db.session.add(new_task)
            db.session.commit()
            flash(f"'{new_task.title}' adlı görev başarıyla eklendi.", 'success')
            
            if new_task.deal_id: return redirect(url_for('crm.crm_deal_detail', deal_id=new_task.deal_id))
            elif new_task.contact_id: return redirect(url_for('crm.crm_contact_detail', contact_id=new_task.contact_id))
            return redirect(url_for('crm.crm_tasks_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Task New Error: {e}", exc_info=True)
            flash(f'Görev eklenirken bir hata oluştu: {str(e)}', 'danger')
            return render_template('task_form.html', title="Yeni Görev Ekle", contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, preselected_contact=preselected_contact, preselected_deal=preselected_deal, task=request.form)

    return render_template('task_form.html', title="Yeni Görev Ekle", contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, preselected_contact=preselected_contact, preselected_deal=preselected_deal, task={}, current_user=current_user, users_for_assignment=User.query.filter(User.id != current_user.id, User.firma == current_user.firma).all() if current_user.role == 'broker' else [])


@crm_bp.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def crm_task_edit(task_id):
    user_id = current_user.id
    # Kullanıcının ya oluşturduğu ya da kendisine atanan görevi düzenlemesine izin ver
    # Veya eğer broker ise, kendi firmasındaki herhangi bir görevi düzenleyebilsin.
    task_to_edit = Task.query.get_or_404(task_id)
    
    can_edit = False
    if task_to_edit.user_id == user_id or task_to_edit.assigned_to_user_id == user_id:
        can_edit = True
    elif current_user.role == 'broker' and task_to_edit.owner_user.firma == current_user.firma: # Broker kendi firmasındaki görevleri düzenleyebilir
        can_edit = True
    
    if not can_edit:
        flash("Bu görevi düzenleme yetkiniz yok.", "danger")
        return redirect(url_for('crm.crm_tasks_list'))

    contacts = Contact.query.filter_by(user_id=task_to_edit.user_id).order_by(Contact.last_name).all() # Görevi oluşturanın kontakları
    deals = Deal.query.filter_by(user_id=task_to_edit.user_id).order_by(Deal.title).all() # Görevi oluşturanın fırsatları
    
    # users_for_assignment: Broker ise kendi firmasındaki diğerleri, değilse sadece kendisi
    users_for_assignment = []
    if current_user.role == 'broker':
        users_for_assignment = User.query.filter(User.id != current_user.id, User.firma == current_user.firma).all()
    users_for_assignment.insert(0, current_user) # Kendisini de ekle


    if request.method == 'POST':
        original_assignee_id = task_to_edit.assigned_to_user_id

        task_to_edit.title = request.form.get('title')
        task_to_edit.description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        task_to_edit.status = request.form.get('status')
        task_to_edit.priority = request.form.get('priority')
        task_to_edit.contact_id = int(request.form.get('contact_id')) if request.form.get('contact_id') else None
        task_to_edit.deal_id = int(request.form.get('deal_id')) if request.form.get('deal_id') else None
        new_assigned_to_user_id_str = request.form.get('assigned_to_user_id', str(task_to_edit.assigned_to_user_id))
        
        # CRM V2
        task_to_edit.reminder_enabled = 'reminder_enabled' in request.form
        reminder_time_str = request.form.get('reminder_time')
        task_to_edit.is_recurring = 'is_recurring' in request.form
        task_to_edit.recurrence_type = request.form.get('recurrence_type') if task_to_edit.is_recurring else None
        task_to_edit.recurrence_interval = int(request.form.get('recurrence_interval', 1)) if task_to_edit.is_recurring else 1
        recurrence_end_date_str = request.form.get('recurrence_end_date')
        task_to_edit.task_type = request.form.get('task_type', task_to_edit.task_type)


        if not task_to_edit.title:
            flash('Görev başlığı zorunludur.', 'danger')
            # ... render_template ...
            return render_template('task_form.html', title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit, contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True, current_user=current_user, users_for_assignment=users_for_assignment)

        
        if due_date_str:
            try: task_to_edit.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError: flash('Geçersiz bitiş tarihi formatı.', 'danger'); # ... render_template ...
        else: task_to_edit.due_date = None

        if task_to_edit.reminder_enabled and reminder_time_str:
            try: task_to_edit.reminder_time = datetime.strptime(reminder_time_str, '%Y-%m-%dT%H:%M')
            except ValueError: flash('Geçersiz hatırlatma zamanı formatı.', 'danger'); task_to_edit.reminder_time = None
        else:
            task_to_edit.reminder_enabled = False
            task_to_edit.reminder_time = None

        if task_to_edit.is_recurring and recurrence_end_date_str:
            try: task_to_edit.recurrence_end_date = datetime.strptime(recurrence_end_date_str, '%Y-%m-%d').date()
            except ValueError: flash('Geçersiz tekrarlama bitiş tarihi formatı.', 'danger'); task_to_edit.recurrence_end_date = None
        elif not task_to_edit.is_recurring:
            task_to_edit.recurrence_end_date = None

        # Yeniden atama mantığı
        new_assigned_to_user_id = int(new_assigned_to_user_id_str) if new_assigned_to_user_id_str else task_to_edit.assigned_to_user_id
        if new_assigned_to_user_id != original_assignee_id:
            task_to_edit.previous_assignee_id = original_assignee_id
            task_to_edit.reassigned_by_id = current_user.id
            task_to_edit.reassigned_at = datetime.utcnow()
            task_to_edit.reassignment_reason = request.form.get('reassignment_reason')
        task_to_edit.assigned_to_user_id = new_assigned_to_user_id


        try:
            db.session.commit()
            flash(f"'{task_to_edit.title}' adlı görev başarıyla güncellendi.", 'success')
            if task_to_edit.deal_id: return redirect(url_for('crm.crm_deal_detail', deal_id=task_to_edit.deal_id))
            elif task_to_edit.contact_id: return redirect(url_for('crm.crm_contact_detail', contact_id=task_to_edit.contact_id))
            return redirect(url_for('crm.crm_tasks_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"CRM Task Edit Error: {e}", exc_info=True)
            flash(f'Görev güncellenirken bir hata oluştu: {str(e)}', 'danger')
            # ... render_template ...
            return render_template('task_form.html', title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit, contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True, current_user=current_user, users_for_assignment=users_for_assignment)

    return render_template('task_form.html', title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit, contacts=contacts, deals=deals, statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True, current_user=current_user, users_for_assignment=users_for_assignment)


@crm_bp.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def crm_task_delete(task_id):
    user_id = current_user.id
    # Sadece oluşturan veya atanan (veya broker) silebilir
    task_to_delete = Task.query.get_or_404(task_id)
    can_delete = False
    if task_to_delete.user_id == user_id or task_to_delete.assigned_to_user_id == user_id:
        can_delete = True
    elif current_user.role == 'broker' and task_to_delete.owner_user.firma == current_user.firma:
        can_delete = True
    
    if not can_delete:
        flash("Bu görevi silme yetkiniz yok.", "danger")
        return redirect(request.referrer or url_for('crm.crm_tasks_list'))
        
    redirect_url = url_for('crm.crm_tasks_list')
    if task_to_delete.deal_id: redirect_url = url_for('crm.crm_deal_detail', deal_id=task_to_delete.deal_id)
    elif task_to_delete.contact_id: redirect_url = url_for('crm.crm_contact_detail', contact_id=task_to_delete.contact_id)

    try:
        task_title = task_to_delete.title
        db.session.delete(task_to_delete)
        db.session.commit()
        flash(f"'{task_title}' adlı görev başarıyla silindi.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Task Delete Error: {e}", exc_info=True)
        flash(f'Görev silinirken bir hata oluştu: {str(e)}', 'danger')
    return redirect(redirect_url)

@crm_bp.route('/task/<int:task_id>/toggle_status', methods=['POST'])
@login_required
def crm_task_toggle_status(task_id):
    user_id = current_user.id
    # Sadece oluşturan veya atanan (veya broker) durumu değiştirebilir
    task = Task.query.get_or_404(task_id)
    can_toggle = False
    if task.user_id == user_id or task.assigned_to_user_id == user_id:
        can_toggle = True
    elif current_user.role == 'broker' and task.owner_user.firma == current_user.firma:
        can_toggle = True

    if not can_toggle:
        flash("Bu görevin durumunu değiştirme yetkiniz yok.", "danger")
        return redirect(request.referrer or url_for('crm.crm_tasks_list'))

    new_status_form = request.form.get('new_status')
    if new_status_form and new_status_form in TASK_STATUSES:
        task.status = new_status_form
    elif task.status == 'Tamamlandı':
        task.status = 'Devam Ediyor'
    else:
        task.status = 'Tamamlandı'
    
    if task.status == 'Tamamlandı':
        task.completed_at = datetime.utcnow()
    else:
        task.completed_at = None # Tamamlandı değilse tarihi temizle

    try:
        db.session.commit()
        flash(f"'{task.title}' görevinin durumu '{task.status}' olarak güncellendi.", 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"CRM Task Toggle Status Error: {e}", exc_info=True)
        flash(f'Görev durumu güncellenirken hata: {str(e)}', 'danger')
    
    if request.referrer: return redirect(request.referrer)
    return redirect(url_for('crm.crm_tasks_list'))

# --- PORTFOLYO (PORTFOLIOS) ROTALARI (Eğer ayrı bir BP yapılmayacaksa buraya gelebilir) ---
# Eski /portfolios ve /portfolio/create, /portfolio/<id> rotaları
# Şimdilik bunları main_bp.py'ye taşıyalım, çünkü daha genel kullanıcı portföyleri gibi duruyor.
# Eğer CRM ile çok entegre olacaksa buraya da gelebilir.
# Bu örnekte main_bp.py'de bırakıyorum.

# --- CRM V2 EKİP YÖNETİMİ ROTALARI ---
# Bu rotalar için yeni template'ler ve modellerde (CrmTeam, crm_team_members) bazı
# eklemeler gerekebilir. Şimdilik iskeletlerini ekleyelim.

@crm_bp.route('/team-management')
@login_required
def crm_team_management():
    if current_user.role != 'broker':
        flash("Bu sayfaya erişim yetkiniz yok.", "danger")
        return redirect(url_for('crm.crm_contacts_list')) # Veya ana sayfaya

    # Broker'ın kendi firmasındaki tüm kullanıcıları (potansiyel ekip üyeleri)
    potential_members = User.query.filter(
        User.firma == current_user.firma,
        User.id != current_user.id, # Kendisi hariç
        User.is_active == True
    ).all()
    
    # Broker'ın mevcut ekibi
    # CrmTeam modeli ve ilişkileri üzerinden çekilecek.
    # Varsayalım ki bir broker sadece bir takıma sahip olabilir (şimdilik)
    team = CrmTeam.query.filter_by(broker_id=current_user.id).first()
    team_members = []
    if team:
        team_members = team.members
        # potential_members listesinden mevcut ekip üyelerini çıkar
        potential_members = [pm for pm in potential_members if pm not in team_members]


    return render_template('team_management.html', title="Ekip Yönetimi", 
                           team_members=team_members, 
                           potential_members=potential_members,
                           current_team=team)

@crm_bp.route('/team/add_member/<int:user_id_to_add>', methods=['POST'])
@login_required
def crm_team_add_member(user_id_to_add):
    if current_user.role != 'broker':
        return jsonify(success=False, message="Yetkisiz işlem."), 403
    
    team = CrmTeam.query.filter_by(broker_id=current_user.id).first()
    if not team: # Eğer broker'ın takımı yoksa oluştur
        team = CrmTeam(broker_id=current_user.id, name=f"{current_user.firma} Ekibi")
        db.session.add(team)
    
    member_to_add = User.query.get(user_id_to_add)
    if not member_to_add or member_to_add.firma != current_user.firma:
        return jsonify(success=False, message="Kullanıcı bulunamadı veya farklı firmada."), 404
    
    if member_to_add in team.members:
        return jsonify(success=False, message="Kullanıcı zaten ekipte."), 400
        
    team.members.append(member_to_add)
    try:
        db.session.commit()
        flash(f"{member_to_add.ad} {member_to_add.soyad} ekibe eklendi.", "success")
        return jsonify(success=True, message="Kullanıcı ekibe eklendi.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ekibe üye ekleme hatası: {e}", exc_info=True)
        return jsonify(success=False, message=f"Hata: {str(e)}"), 500

@crm_bp.route('/team/remove_member/<int:user_id_to_remove>', methods=['POST'])
@login_required
def crm_team_remove_member(user_id_to_remove):
    if current_user.role != 'broker':
        return jsonify(success=False, message="Yetkisiz işlem."), 403

    team = CrmTeam.query.filter_by(broker_id=current_user.id).first()
    member_to_remove = User.query.get(user_id_to_remove)

    if not team or not member_to_remove or member_to_remove not in team.members:
        return jsonify(success=False, message="Kullanıcı ekipte bulunamadı."), 404
        
    team.members.remove(member_to_remove)
    try:
        db.session.commit()
        flash(f"{member_to_remove.ad} {member_to_remove.soyad} ekipten çıkarıldı.", "success")
        return jsonify(success=True, message="Kullanıcı ekipten çıkarıldı.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ekipten üye çıkarma hatası: {e}", exc_info=True)
        return jsonify(success=False, message=f"Hata: {str(e)}"), 500

# --- CRM Raporlama/Dashboard Rotaları ---
@crm_bp.route('/task-performance')
@login_required
def crm_task_performance():
    # Bu kısım için veri toplama ve hesaplama mantığı gerekecek
    # Örnek:
    # metrics = calculate_task_metrics(current_user.id)
    # weekly_data = get_weekly_completion_data(current_user.id)
    metrics = {"completed_tasks": 0, "total_tasks": 0, "on_time_percentage": 0, "in_progress_tasks": 0, "overdue_tasks": 0, "pending_tasks":0, "cancelled_tasks":0} # Örnek
    weekly_labels = []
    weekly_completed_data = []
    team_members_performance_data = [] # Ekip üyelerinin performans verileri

    return render_template('task_performance.html', title="Görev Performansı", metrics=metrics, weekly_labels=weekly_labels, weekly_completed_data=weekly_completed_data, team_members=team_members_performance_data)

@crm_bp.route('/team-dashboard')
@login_required
def crm_team_dashboard():
    if current_user.role != 'broker':
        flash("Bu sayfaya erişim yetkiniz yok.", "danger")
        return redirect(url_for('crm.crm_contacts_list'))
        
    # Ekip performans verilerini hesapla
    # stats = get_team_performance_stats(current_user.id)
    # team_performance = get_individual_team_member_stats(current_user.id)
    # recently_completed_tasks = get_recent_team_tasks(current_user.id, status="Tamamlandı")
    # upcoming_deadlines = get_upcoming_team_deadlines(current_user.id)
    
    # Geçici örnek veriler
    stats = {"total_tasks": 0, "completed_tasks": 0, "completion_rate": 0, "pending_tasks": 0, "overdue_tasks": 0}
    team_performance = []
    recently_completed_tasks = []
    upcoming_deadlines = []
    
    return render_template('team_dashboard.html', title="Ekip Performans Paneli", 
                           stats=stats, 
                           team_performance=team_performance, 
                           recently_completed_tasks=recently_completed_tasks, 
                           upcoming_deadlines=upcoming_deadlines)

@crm_bp.route('/team-member/<int:user_id>/detail')
@login_required
def crm_team_member_detail(user_id):
    if current_user.role != 'broker' and current_user.id != user_id:
        flash("Bu sayfaya erişim yetkiniz yok.", "danger")
        return redirect(url_for('crm.crm_team_dashboard'))

    member = User.query.get_or_404(user_id)
    # Bu üyenin performans istatistiklerini çek
    # stats = get_user_performance_stats(member.id)
    # recent_tasks = get_user_recent_tasks(member.id)
    
    # Geçici örnek veriler
    stats = {
        "total_tasks": 0, "completed_tasks": 0, "completion_rate": 0, 
        "pending_tasks": 0, "overdue_tasks": 0,
        "status_distribution": {"Beklemede": 0, "Devam Ediyor": 0, "Tamamlandı": 0, "İptal": 0},
        "priority_distribution": {"Düşük": 0, "Normal": 0, "Yüksek": 0, "Acil": 0},
        "months": [], "month_stats": []
    }
    recent_tasks = []

    return render_template('team_member_detail.html', 
                           title=f"{member.ad} Performans Detayı",
                           team_member=member, 
                           stats=stats, 
                           recent_tasks=recent_tasks)