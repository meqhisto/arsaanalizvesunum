from app import app, db, login_required, User, flash, redirect, url_for, render_template, session

# Ekip Yönetimi
@app.route("/crm/team-management")
@login_required
def crm_team_management():
    """Broker rolüne sahip kullanıcılar için ekip yönetim sayfası"""
    user_id = session["user_id"]
    current_user = User.query.get(user_id)
    
    # Sadece broker'lar bu sayfaya erişebilir
    if current_user.role != "broker":
        flash("Bu sayfaya erişim yetkiniz bulunmuyor.", "danger")
        return redirect(url_for("crm_dashboard"))
    
    # Mevcut ekip üyelerini getir
    team_members = current_user.team_members.all()
    
    # Aynı firmadaki, ekipte olmayan, danışman rolündeki ve aktif kullanıcıları getir
    # Null firma değerlerini uyumsuz kabul et
    potential_members = User.query.filter(
        User.firma == current_user.firma,  # Aynı firma
        User.firma != None,  # Firma değeri boş olmamalı
        User.id != user_id,  # Kendisi dışındaki kullanıcılar
        User.role == "danışman",  # Sadece danışmanlar
        User.is_active == True,  # Aktif kullanıcılar
        User.report_to_id == None  # Henüz bir brokera bağlı olmayanlar
    ).all()
    
    return render_template("crm/team_management.html", 
                           title="Ekip Yönetimi",
                           team_members=team_members,
                           potential_members=potential_members,
                           current_user=current_user)

@app.route("/crm/team/add-member/<int:user_id>", methods=["POST"])
@login_required
def crm_team_add_member(user_id):
    """Broker'a danışmanı ekibine ekleme imkanı sağlar"""
    broker_id = session["user_id"]
    broker = User.query.get(broker_id)
    
    # Sadece broker'lar bu işlemi yapabilir
    if broker.role != "broker":
        flash("Bu işlemi yapma yetkiniz bulunmuyor.", "danger")
        return redirect(url_for("crm_dashboard"))
    
    # Ekibe eklenecek kullanıcıyı bul
    consultant = User.query.get_or_404(user_id)
    
    # Danışmanın, brokerla aynı firmada olduğunu kontrol et
    if consultant.firma != broker.firma or consultant.firma is None:
        flash("Bu kullanıcı aynı firmada değil veya firma bilgisi bulunamadı.", "danger")
        return redirect(url_for("crm_team_management"))
    
    # Danışman zaten bir ekibe dahil mi kontrol et
    if consultant.report_to_id is not None:
        flash(f"{consultant.ad} {consultant.soyad} zaten bir ekibe dahil.", "warning")
        return redirect(url_for("crm_team_management"))
    
    # Danışmanı ekibe ekle
    consultant.report_to_id = broker_id
    db.session.commit()
    
    flash(f"{consultant.ad} {consultant.soyad} ekibinize başarıyla eklendi.", "success")
    return redirect(url_for("crm_team_management"))

@app.route("/crm/team/remove-member/<int:user_id>", methods=["POST"])
@login_required
def crm_team_remove_member(user_id):
    """Broker'a danışmanı ekibinden çıkarma imkanı sağlar"""
    broker_id = session["user_id"]
    broker = User.query.get(broker_id)
    
    # Sadece broker'lar bu işlemi yapabilir
    if broker.role != "broker":
        flash("Bu işlemi yapma yetkiniz bulunmuyor.", "danger")
        return redirect(url_for("crm_dashboard"))
    
    # Ekipten çıkarılacak kullanıcıyı bul
    consultant = User.query.get_or_404(user_id)
    
    # Danışmanın gerçekten bu broker'a bağlı olduğunu kontrol et
    if consultant.report_to_id != broker_id:
        flash("Bu kullanıcı sizin ekibinizde değil.", "danger")
        return redirect(url_for("crm_team_management"))
    
    # Danışmanı ekipten çıkar
    consultant.report_to_id = None
    db.session.commit()
    
    flash(f"{consultant.ad} {consultant.soyad} ekibinizden çıkarıldı.", "success")
    return redirect(url_for("crm_team_management"))
