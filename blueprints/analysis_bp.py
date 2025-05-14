# blueprints/analysis_bp.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, send_from_directory
)
from flask_login import login_required, current_user
from datetime import datetime
import uuid # Rapor ID'leri için
import tempfile # Kullanılmıyorsa kaldırılabilir
import traceback
import json
from decimal import Decimal # Sayısal dönüşümler için
from werkzeug.utils import secure_filename # Dosya yükleme için
import os
import logging # logging için

# Modelleri ve db nesnesini models paketinden import et
from models import db
from models.user_models import User
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats, AnalizMedya

# Özel modüllerinizi import edin
# Bu import yolları, projenizin klasör yapısına göre ayarlanmalıdır.
# Eğer blueprints klasörü, modules klasörü ile aynı seviyedeyse:
from modules.analiz import ArsaAnalizci
from modules.document_generator import DocumentGenerator
from modules.fiyat_tahmini import FiyatTahminModeli # FiyatTahminModeli'ne engine geçilecek

# Flask uygulamasının yapılandırmasına erişmek için current_app
from flask import current_app

analysis_bp = Blueprint('analysis', __name__, template_folder='../templates/analysis')# template_folder='../templates' ana şablon klasörünü kullanır.
# Eğer analiz şablonları templates/analysis/ altındaysa, template_folder='../templates/analysis' yapın.

# --- YARDIMCI FONKSİYONLAR (app.py'den taşınabilir veya burada tanımlanabilir) ---
def allowed_file(filename):
    # ALLOWED_EXTENSIONS'ı current_app.config'den almak daha iyi olur
    # veya burada sabit olarak tanımlanabilir.
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROTALAR ---

# ÖNEMLİ NOT: Eski app.py'de iki adet analiz submit rotası vardı: /submit ve /submit_analysis.
# /submit_analysis daha yeni ve daha detaylı validasyon içeriyor gibi duruyor.
# İkisini birleştirip tek bir ana analiz oluşturma rotası yapmak en iyisi.
# Şimdilik /submit_analysis rotasını alıyorum ve adını /create olarak değiştirebiliriz.
# Eski /submit rotasındaki Arsa sınıfı ve ArsaAnalizci kullanımı,
# yeni /create rotası içinde veya ArsaAnaliz modelinin metotları olarak entegre edilebilir.

@analysis_bp.route('/create', methods=['POST']) # Eski /submit_analysis
@login_required
def create_analysis(): # Fonksiyon adı değişti
    try:
        user_id = current_user.id
        form_data_dict = request.form.to_dict()
        altyapi_list = request.form.getlist("altyapi[]")

        # --- Sunucu Tarafı Validasyon (analysis_form.html'deki submit_analysis'ten alındı) ---
        errors = []
        required_fields = {
            "il": "İl", "ilce": "İlçe", "mahalle": "Mahalle",
            "ada": "Ada No", "parsel": "Parsel No",
            "metrekare": "Metrekare", "imar_durumu": "İmar Durumu",
            "maliyet": "Maliyet (Fiyat)", "guncel_deger": "Güncel Değer (Bölge Fiyatı)", "tarih": "Alım Tarihi" # İsimler eşleştirildi
        }
        for field, label in required_fields.items():
            if not form_data_dict.get(field, "").strip():
                if field != "tarih": # Tarih zorunlu olmayabilir, modele bağlı
                    errors.append(f"{label} alanı zorunludur.")

        numeric_fields_config = {
            "metrekare": {"label": "Metrekare", "min_val": 0.01, "max_val": 9999999.99},
            "taks": {"label": "TAKS", "min_val": 0, "max_val": 1, "default": 0.3},
            "kaks": {"label": "KAKS", "min_val": 0, "max_val": 10, "default": 1.5}, # max_val eklendi
            "maliyet": {"label": "Maliyet", "min_val": 0, "max_val": 9999999999999.99},
            "guncel_deger": {"label": "Güncel Değer", "min_val": 0, "max_val": 9999999999999.99},
            "deger_artis_orani": {"label": "Yıllık Değer Artış Oranı", "min_val": 0, "max_val": 100, "default": 15}
        }
        
        converted_data = {} # Dönüştürülmüş ve doğrulanmış sayısal veriler için

        for field, config in numeric_fields_config.items():
            value_str = form_data_dict.get(field, str(config.get("default", ""))).replace(",", "").strip()
            if value_str: # Sadece doluysa işlem yap
                try:
                    value_float = float(value_str)
                    if "min_val" in config and value_float < config["min_val"]:
                        errors.append(f"{config['label']} en az {config['min_val']} olmalıdır.")
                    if "max_val" in config and value_float > config["max_val"]:
                        errors.append(f"{config['label']} en fazla {config['max_val']} olmalıdır.")
                    converted_data[field] = value_float
                except ValueError:
                    errors.append(f"{config['label']} alanı geçerli bir sayı olmalıdır.")
            elif field in ["metrekare", "maliyet", "guncel_deger"]: # Bu alanlar zorunlu (default'ları yoksa)
                 if not config.get("default"): # Eğer default değeri yoksa ve boşsa hata ver
                    errors.append(f"{config['label']} alanı zorunludur ve sayısal olmalıdır.")
            else: # Opsiyonel sayısal alanlar için default değeri al
                converted_data[field] = config.get("default", 0.0)


        # Tarih validasyonu
        # tarih_str = form_data_dict.get("tarih", "")
        # if tarih_str: # Tarih zorunlu değilse bu kontrol opsiyonel
        #     try:
        #         datetime.strptime(tarih_str, "%Y-%m-%d")
        #     except ValueError:
        #         errors.append("Alım Tarihi geçerli bir formatta (YYYY-AA-GG) olmalıdır.")
        # else: # Eğer tarih zorunluysa
        #     errors.append("Alım Tarihi zorunludur.")
        
        swot_data_from_form = {}
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            swot_json_str = form_data_dict.get(key, "[]")
            try:
                swot_list = json.loads(swot_json_str)
                if not isinstance(swot_list, list):
                    errors.append(f"SWOT {key.capitalize()} verisi liste formatında olmalı.")
                    swot_data_from_form[key] = [] # Hata durumunda boş liste
                else:
                    swot_data_from_form[key] = swot_list
            except json.JSONDecodeError:
                errors.append(f"SWOT {key.capitalize()} verisi geçersiz JSON formatında.")
                swot_data_from_form[key] = []

        if errors:
            for error in errors:
                flash(error, "danger")
            session['analysis_form_data'] = form_data_dict
            session['analysis_form_data']['altyapi[]'] = altyapi_list # Checkbox'ları da ekle
            session['analysis_form_errors'] = errors
            return redirect(url_for("main.analysis_form")) # main blueprint'indeki forma yönlendir
        # --- Validasyon Sonu ---

        yeni_analiz = ArsaAnaliz(
            user_id=user_id,
            il=form_data_dict.get("il"),
            ilce=form_data_dict.get("ilce"),
            mahalle=form_data_dict.get("mahalle"),
            ada=form_data_dict.get("ada"),
            parsel=form_data_dict.get("parsel"),
            koordinatlar=form_data_dict.get("koordinatlar"),
            pafta=form_data_dict.get("pafta"),
            metrekare=Decimal(str(converted_data.get("metrekare", 0))),
            imar_durumu=form_data_dict.get("imar_durumu"),
            taks=Decimal(str(converted_data.get("taks", 0.3))),
            kaks=Decimal(str(converted_data.get("kaks", 1.5))),
            fiyat=Decimal(str(converted_data.get("maliyet", 0))), # Formda 'maliyet', modelde 'fiyat'
            bolge_fiyat=Decimal(str(converted_data.get("guncel_deger", 0))), # Formda 'guncel_deger', modelde 'bolge_fiyat'
            altyapi=json.dumps(altyapi_list),
            swot_analizi=json.dumps(swot_data_from_form),
            notlar=form_data_dict.get("notlar")
            # alim_tarihi=datetime.strptime(tarih_str, "%Y-%m-%d").date() if tarih_str else None,
            # deger_artis_orani=Decimal(str(converted_data.get("deger_artis_orani", 15))),
        )
        db.session.add(yeni_analiz)
        
        # Dashboard İstatistiklerini Güncelleme
        stats = DashboardStats.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = DashboardStats(user_id=user_id, en_dusuk_fiyat=float('inf')) # en_dusuk_fiyat için başlangıç
            db.session.add(stats)
        
        # İstatistikleri initialize et (None ise)
        stats.toplam_arsa_sayisi = (stats.toplam_arsa_sayisi or 0) + 1
        stats.toplam_deger = (stats.toplam_deger or Decimal(0)) + yeni_analiz.fiyat
        
        # Ortalama fiyat (Float olarak saklandığı varsayılıyor)
        current_fiyat_float = float(yeni_analiz.fiyat)
        if stats.toplam_arsa_sayisi == 1:
            stats.ortalama_fiyat = current_fiyat_float
            stats.en_yuksek_fiyat = current_fiyat_float
            stats.en_dusuk_fiyat = current_fiyat_float
        else:
            stats.ortalama_fiyat = (( (stats.ortalama_fiyat or 0.0) * (stats.toplam_arsa_sayisi - 1)) + current_fiyat_float) / stats.toplam_arsa_sayisi
            stats.en_yuksek_fiyat = max((stats.en_yuksek_fiyat or 0.0), current_fiyat_float)
            stats.en_dusuk_fiyat = min((stats.en_dusuk_fiyat or float('inf')), current_fiyat_float)
        
        stats.son_guncelleme = datetime.utcnow()

        # Bölge istatistiklerini güncelle
        bolge = BolgeDagilimi.query.filter_by(user_id=user_id, il=yeni_analiz.il).first()
        if not bolge:
            bolge = BolgeDagilimi(user_id=user_id, il=yeni_analiz.il, analiz_sayisi=0, toplam_deger=Decimal('0.00'))
            db.session.add(bolge)
        bolge.analiz_sayisi = (bolge.analiz_sayisi or 0) + 1
        bolge.toplam_deger = (bolge.toplam_deger or Decimal(0)) + yeni_analiz.fiyat
        bolge.son_guncelleme = datetime.utcnow()

        db.session.commit()
        flash("Arsa analizi başarıyla kaydedildi.", "success")
        return redirect(url_for('analysis.analiz_detay', analiz_id=yeni_analiz.id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analiz oluşturma hatası: {str(e)}", exc_info=True)
        # Hata durumunda form verilerini session'a kaydet ve formu tekrar göster
        session['analysis_form_data'] = request.form.to_dict() # Orijinal form verisi
        session['analysis_form_data']['altyapi[]'] = request.form.getlist("altyapi[]")
        session['analysis_form_errors'] = [f"Beklenmedik bir hata oluştu: {str(e)}"]
        flash(f"Arsa analizi kaydedilirken bir hata oluştu. Lütfen alanları kontrol edin.", "danger")
        return redirect(url_for("main.analysis_form"))


@analysis_bp.route('/<int:analiz_id>')
@login_required
def analiz_detay(analiz_id):
    try:
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        analiz_sahibi_user = User.query.get(analiz.user_id)

        if not analiz_sahibi_user:
            flash("Analize ait kullanıcı bulunamadı.", "danger")
            return redirect(url_for('analysis.analizler'))

        read_only_mode = (current_user.id != analiz.user_id)
        
        altyapi_parsed = []
        if analiz.altyapi:
            try:
                altyapi_data = json.loads(analiz.altyapi)
                if isinstance(altyapi_data, list):
                    altyapi_parsed = altyapi_data
                elif isinstance(altyapi_data, dict): # Eski format {yol:true, su:false} ise listeye çevir
                    altyapi_parsed = [key for key, value in altyapi_data.items() if value]
                else:
                    current_app.logger.warning(f"Analiz ID {analiz_id} altyapı verisi beklenmedik format: {analiz.altyapi}")
            except json.JSONDecodeError:
                current_app.logger.error(f"Analiz ID {analiz_id} altyapı JSON parse hatası.")
        
        swot_analizi_parsed = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        if analiz.swot_analizi:
            try:
                swot_data = json.loads(analiz.swot_analizi)
                if isinstance(swot_data, dict):
                    swot_analizi_parsed = {k: (v if isinstance(v, list) else [v] if v else []) for k, v in swot_data.items()}
                else: # Eğer direkt liste ise (eski bir format olabilir)
                    current_app.logger.warning(f"Analiz ID {analiz_id} SWOT verisi beklenmedik format: {analiz.swot_analizi}")
            except json.JSONDecodeError:
                current_app.logger.error(f"Analiz ID {analiz_id} SWOT JSON parse hatası.")

        # ArsaAnalizci ve FiyatTahminModeli kullanımı
        analizci = ArsaAnalizci() # Strateji default SwotAnalizi olacak
        # ArsaAnalizci'nin beklediği veri formatını kontrol et
        # Genellikle bir dict bekler: {'metrekare': ..., 'fiyat': ..., 'imar_durumu': ...}
        arsa_data_for_analizci = {
            "metrekare": float(analiz.metrekare or 0),
            "fiyat": float(analiz.fiyat or 0),
            "bolge_fiyat": float(analiz.bolge_fiyat or 0),
            "taks": float(analiz.taks or 0.3), # Varsayılan değerler
            "kaks": float(analiz.kaks or 1.5), # Varsayılan değerler
            "imar_durumu": analiz.imar_durumu or "",
            "altyapi": altyapi_parsed, # Parse edilmiş liste
            "konum": {"il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle}
        }
        analiz_sonuclari_data = analizci.analiz_et(arsa_data_for_analizci.copy()) # Kopyasını gönder
        ozet = analizci.ozetle(analiz_sonuclari_data.copy())

        tahmin_sonucu = None
        try:
            # db.engine'e create_app içinde erişim sağlanmalı veya FiyatTahminModeli'ne app context'i verilmeli.
            # Şimdilik db.engine'in erişilebilir olduğunu varsayıyorum.
            tahmin_modeli = FiyatTahminModeli(db.engine)
            prediction_input_data = {
                "il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle,
                "metrekare": float(analiz.metrekare or 0),
                "imar_durumu": analiz.imar_durumu or "",
                "taks": float(analiz.taks or 0.3),
                "kaks": float(analiz.kaks or 1.5),
                "bolge_fiyat": float(analiz.bolge_fiyat or 0)
            }
            tahmin_sonucu = tahmin_modeli.tahmin_yap(prediction_input_data)
        except Exception as e_tahmin:
            current_app.logger.error(f"Fiyat tahmini hatası (ID: {analiz_id}): {e_tahmin}", exc_info=False)

        medyalar = AnalizMedya.query.filter_by(analiz_id=analiz_id).order_by(AnalizMedya.uploaded_at.asc()).all()
        
        # Rapor için session verilerini ayarla (sadece sahibi ise)
        if not read_only_mode:
            session_arsa_data = {
                "id": analiz.id, "il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle,
                "ada": analiz.ada, "parsel": analiz.parsel, "koordinatlar": analiz.koordinatlar,
                "pafta": analiz.pafta, "metrekare": float(analiz.metrekare or 0), "imar_durumu": analiz.imar_durumu or "",
                "taks": float(analiz.taks or 0.3), "kaks": float(analiz.kaks or 1.5), 
                "fiyat": float(analiz.fiyat or 0), "bolge_fiyat": float(analiz.bolge_fiyat or 0),
                "altyapi[]": altyapi_parsed, # Bu anahtarın DocumentGenerator tarafından doğru okunması lazım
                "strengths": swot_analizi_parsed.get("strengths", []), 
                "weaknesses": swot_analizi_parsed.get("weaknesses", []),
                "opportunities": swot_analizi_parsed.get("opportunities", []), 
                "threats": swot_analizi_parsed.get("threats", []),
                # İnşaat hesaplama verisi DocumentGenerator'a gönderilecek arsa_data'ya eklenebilir
                "insaat_hesaplama": analiz_sonuclari_data.get("insaat_hesaplama", {}) # ArsaAnalizci'den gelen veri
            }
            session["arsa_data"] = session_arsa_data # DocumentGenerator için
            session["analiz_ozeti"] = ozet
        elif "arsa_data" in session: # Başkasının analizine bakarken kendi session'ımızı temizleyelim
            session.pop("arsa_data", None)
            session.pop("analiz_ozeti", None)

        return render_template(
            "analiz_detay.html", # templates/analiz_detay.html (veya templates/analysis/analiz_detay.html)
            analiz=analiz,
            altyapi=altyapi_parsed, # Şablona parse edilmiş altyapı listesini gönder
            swot=swot_analizi_parsed,
            sonuc=analiz_sonuclari_data, # ArsaAnalizci'den gelen tüm sonuçlar
            ozet=ozet,
            user=analiz_sahibi_user,
            medyalar=medyalar,
            file_id=str(analiz.id), # Rapor linkleri için
            tahmin=tahmin_sonucu,
            read_only_mode=read_only_mode
        )
    except Exception as e:
        current_app.logger.error(f"Analiz Detay Sayfası Hatası (ID: {analiz_id}): {str(e)}", exc_info=True)
        flash("Analiz görüntülenirken beklenmedik bir hata oluştu.", "danger")
        return redirect(url_for('analysis.analizler'))


@analysis_bp.route('/list') # Eski /analizler
@login_required
def analizler():
    user_id = current_user.id
    iller = (
        db.session.query(ArsaAnaliz.il)
        .filter_by(user_id=user_id)
        .distinct()
        .order_by(ArsaAnaliz.il)
        .all()
    )
    iller_list = [il[0] for il in iller] # Tuple listesinden string listesine

    all_analizler = (
        ArsaAnaliz.query.filter_by(user_id=user_id)
        .order_by(ArsaAnaliz.created_at.desc())
        .all()
    )

    grouped_analizler = {}
    ay_isimleri_tr = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
    for analiz_item in all_analizler:
        key = f"{ay_isimleri_tr[analiz_item.created_at.month]} {analiz_item.created_at.year}"
        if key not in grouped_analizler:
            grouped_analizler[key] = []
        grouped_analizler[key].append(analiz_item)

    return render_template(
        "analizler.html", # templates/analizler.html
        grouped_analizler=grouped_analizler,
        total_count=len(all_analizler),
        iller=iller_list
    )

@analysis_bp.route('/delete/<int:analiz_id>', methods=['POST']) # Eski /analiz/sil/...
@login_required
def analiz_sil(analiz_id):
    try:
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        if analiz.user_id != current_user.id:
            flash("Bu analizi silme yetkiniz yok.", "danger")
            return redirect(url_for('analysis.analizler'))

        # İstatistikleri güncelle
        stats = DashboardStats.query.filter_by(user_id=current_user.id).first()
        if stats:
            stats.toplam_arsa_sayisi = max(0, (stats.toplam_arsa_sayisi or 0) - 1)
            stats.toplam_deger = max(Decimal("0.00"), (stats.toplam_deger or Decimal(0)) - (analiz.fiyat or Decimal(0)))
            # Ortalama, min, max fiyatları yeniden hesaplamak gerekebilir veya en azından None kontrolü yapılmalı
            if stats.toplam_arsa_sayisi == 0:
                stats.ortalama_fiyat = 0.0
                stats.en_yuksek_fiyat = 0.0
                stats.en_dusuk_fiyat = 0.0
            # else: Daha karmaşık bir yeniden hesaplama gerekebilir tüm analizleri çekerek.
            # Şimdilik basit bir çıkarma yapıyoruz, bu ortalamayı bozabilir.
            # Doğru bir ortalama için tüm kalan analizlerin ortalaması alınmalı.

        bolge = BolgeDagilimi.query.filter_by(user_id=current_user.id, il=analiz.il).first()
        if bolge:
            bolge.analiz_sayisi = max(0, (bolge.analiz_sayisi or 0) - 1)
            bolge.toplam_deger = max(Decimal("0.00"), (bolge.toplam_deger or Decimal(0)) - (analiz.fiyat or Decimal(0)))
            if bolge.analiz_sayisi == 0:
                db.session.delete(bolge)
        
        # İlişkili medyaları ve dosyaları sil
        for medya in analiz.medyalar: # AnalizMedya modelinde cascade delete varsa bu gerekmeyebilir
            try:
                # medya.filename 'analiz_id/dosya_adi' formatında olmalı
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], medya.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                db.session.delete(medya) # Veritabanından da sil
            except Exception as e_media_delete:
                current_app.logger.error(f"Medya silinirken hata ({medya.filename}): {e_media_delete}")
        
        # Analize özel klasörü sil (içi boşsa)
        analiz_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(analiz_id))
        try:
            if os.path.exists(analiz_folder) and not os.listdir(analiz_folder):
                os.rmdir(analiz_folder)
        except Exception as e_folder_delete:
            current_app.logger.error(f"Analiz klasörü silinirken hata ({analiz_folder}): {e_folder_delete}")

        db.session.delete(analiz)
        db.session.commit()
        flash("Analiz ve ilişkili medyalar başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analiz silme hatası: {str(e)}", exc_info=True)
        flash("Analiz silinirken bir hata oluştu.", "danger")
    return redirect(url_for('analysis.analizler'))


@analysis_bp.route('/<int:analiz_id>/media_upload', methods=['POST']) # Eski /analiz/.../medya_yukle
@login_required
def medya_yukle(analiz_id):
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != current_user.id:
        flash("Bu analize medya yükleme yetkiniz yok.", "danger")
        return redirect(url_for('analysis.analizler'))

    if 'medya' not in request.files:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))
    
    file = request.files['medya']
    if file.filename == '':
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))

    if file and allowed_file(file.filename): # allowed_file bu BP içinde tanımlı
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        medya_type = 'image' if ext in {'jpg', 'jpeg', 'png', 'gif'} else 'video'
        
        # Analize özel klasör oluştur
        analiz_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(analiz_id))
        os.makedirs(analiz_upload_folder, exist_ok=True)
        
        # Benzersiz dosya adı oluşturma (aynı isimde dosya yüklenirse üzerine yazmasın diye)
        # unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}" 
        # Veya basitçe mevcut dosya adını kullanıp üzerine yazsın:
        unique_filename = filename
        filepath = os.path.join(analiz_upload_folder, unique_filename)
        
        try:
            file.save(filepath)
            # Veritabanına göreceli yolu kaydet (örn: "123/resim.jpg")
            db_filename = os.path.join(str(analiz_id), unique_filename).replace(os.sep, '/')
            medya_kaydi = AnalizMedya(analiz_id=analiz_id, filename=db_filename, type=medya_type)
            db.session.add(medya_kaydi)
            db.session.commit()
            flash('Medya başarıyla yüklendi.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Medya kaydetme hatası: {e}", exc_info=True)
            flash('Medya yüklenirken bir hata oluştu.', 'danger')
    else:
        flash('Geçersiz dosya türü.', 'danger')
    return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))


@analysis_bp.route('/<int:analiz_id>/media_delete/<int:medya_id>', methods=['POST']) # Eski /analiz/.../medya_sil/...
@login_required
def medya_sil(analiz_id, medya_id):
    medya = AnalizMedya.query.get_or_404(medya_id)
    analiz = ArsaAnaliz.query.get_or_404(analiz_id) # Medyanın analizini de alalım
    
    if analiz.user_id != current_user.id or medya.analiz_id != analiz_id:
        flash('Yetkisiz işlem.', 'danger')
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))

    try:
        # medya.filename 'analiz_id/dosyaadi' formatında
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], medya.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.session.delete(medya)
        db.session.commit()
        flash('Medya başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Medya silme hatası: {e}", exc_info=True)
        flash('Medya silinirken bir hata oluştu.', 'danger')
    return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))


# Rapor Oluşturma Rotası (Word, PDF)
# Eski /generate/<format>/<file_id>
@analysis_bp.route('/report/generate/<string:format_type>/<int:analiz_id_param>')
@login_required
def generate_report(format_type, analiz_id_param):
    try:
        # Session yerine veritabanından analiz verilerini al
        analiz = ArsaAnaliz.query.get_or_404(analiz_id_param)
        if analiz.user_id != current_user.id: # Sadece kendi analizleri için rapor
            flash("Bu analiz için rapor oluşturma yetkiniz yok.", "warning")
            return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id_param))

        user = User.query.get(analiz.user_id) # Zaten current_user

        # DocumentGenerator için arsa_data ve analiz_ozeti oluştur
        altyapi_parsed = []
        if analiz.altyapi:
            try: altyapi_parsed = json.loads(analiz.altyapi)
            except: pass
            if not isinstance(altyapi_parsed, list): altyapi_parsed = [k for k,v in (altyapi_parsed if isinstance(altyapi_parsed, dict) else {}).items() if v]


        swot_parsed = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        if analiz.swot_analizi:
            try: swot_parsed = json.loads(analiz.swot_analizi)
            except: pass
            if not isinstance(swot_parsed, dict): swot_parsed = {} # Hatalıysa boş dict

        # ArsaAnalizci'den hesaplamaları al
        analizci = ArsaAnalizci()
        arsa_data_for_analizci = {
            "metrekare": float(analiz.metrekare or 0), "fiyat": float(analiz.fiyat or 0),
            "bolge_fiyat": float(analiz.bolge_fiyat or 0), "taks": float(analiz.taks or 0.3),
            "kaks": float(analiz.kaks or 1.5), "imar_durumu": analiz.imar_durumu or "",
            "altyapi": altyapi_parsed,
            "konum": {"il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle}
        }
        analiz_sonuclari = analizci.analiz_et(arsa_data_for_analizci.copy())
        analiz_ozeti_calculated = analizci.ozetle(analiz_sonuclari.copy())

        # DocumentGenerator'a gönderilecek arsa_data
        doc_arsa_data = {
            "id": analiz.id, "il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle,
            "ada": analiz.ada, "parsel": analiz.parsel, "koordinatlar": analiz.koordinatlar,
            "pafta": analiz.pafta, "metrekare": float(analiz.metrekare or 0),
            "imar_durumu": analiz.imar_durumu or "", "taks": float(analiz.taks or 0.3),
            "kaks": float(analiz.kaks or 1.5), "fiyat": float(analiz.fiyat or 0),
            "bolge_fiyat": float(analiz.bolge_fiyat or 0),
            "altyapi[]": altyapi_parsed, # DocumentGenerator bu anahtarı bekliyor olabilir, kontrol edin
            "strengths": swot_parsed.get("strengths", []), "weaknesses": swot_parsed.get("weaknesses", []),
            "opportunities": swot_parsed.get("opportunities", []), "threats": swot_parsed.get("threats", []),
            "insaat_hesaplama": analiz_sonuclari.get("insaat_hesaplama", {}) # İnşaat hesaplamalarını da ekle
        }

        profile_info = {
            "ad": current_user.ad, "soyad": current_user.soyad, "email": current_user.email,
            "telefon": current_user.telefon, "firma": current_user.firma, "unvan": current_user.unvan,
            "adres": current_user.adres, "profil_foto": current_user.profil_foto,
            "created_at": analiz.created_at # Analizin oluşturulma tarihi
        }

        # Rapor ayarları (URL'den veya varsayılan)
        theme = request.args.get("theme", "classic")
        color_scheme = request.args.get("color_scheme", "blue")
        sections_str = request.args.get("sections")
        sections_list = [s.strip() for s in sections_str.split(',') if s.strip()] if sections_str else None
        
        doc_gen_settings = {"theme": theme, "color_scheme": color_scheme}
        if sections_list is not None:
            doc_gen_settings["sections"] = sections_list

        # file_id olarak analiz_id'yi kullanalım, output_dir PRESENTATIONS_DIR olmalı
        doc_generator = DocumentGenerator(
            doc_arsa_data,
            analiz_ozeti_calculated,
            str(analiz.id), # file_id olarak analiz ID'si
            current_app.config["PRESENTATIONS_DIR"], # Ana app config'den al
            profile_info=profile_info,
            settings=doc_gen_settings
        )

        filepath = None
        download_name = None

        if format_type == "word":
            filepath = doc_generator.create_word()
            download_name = f"arsa_analiz_{analiz.id}.docx"
        elif format_type == "pdf":
            filepath = doc_generator.create_pdf()
            download_name = f"arsa_analiz_{analiz.id}.pdf"
        else:
            flash("Geçersiz rapor formatı.", "danger")
            return redirect(url_for('analysis.analiz_detay', analiz_id=analiz.id))

        if filepath and os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=download_name)
        else:
            current_app.logger.error(f"{format_type.upper()} rapor dosyası oluşturulamadı veya bulunamadı: {filepath}")
            flash(f"{format_type.upper()} raporu oluşturulamadı.", "danger")
            return redirect(url_for('analysis.analiz_detay', analiz_id=analiz.id))

    except Exception as e:
        current_app.logger.error(f"Rapor oluşturma hatası ({format_type}, ID: {analiz_id_param}): {str(e)}", exc_info=True)
        flash("Rapor oluşturulurken beklenmedik bir hata oluştu.", "danger")
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id_param))


# Sunum Oluşturma Rotası (PPTX)
# Eski /generate/pptx/<int:analiz_id>
@analysis_bp.route('/report/generate_pptx/<int:analiz_id>', methods=['POST']) # POST olmalı, formdan veri alacak
@login_required
def generate_pptx(analiz_id):
    try:
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        if analiz.user_id != current_user.id:
            return jsonify({"error": "Yetkisiz işlem"}), 403

        sections_json = request.form.get("sections", "[]") # Varsayılan boş JSON dizisi
        try:
            sections = json.loads(sections_json)
            if not isinstance(sections, list): sections = []
        except json.JSONDecodeError:
            sections = []
        
        color_scheme = request.form.get("color_scheme", "blue")

        # DocumentGenerator için veri hazırlama (generate_report'takine benzer)
        altyapi_parsed = []
        if analiz.altyapi:
            try: altyapi_parsed = json.loads(analiz.altyapi)
            except: pass
            if not isinstance(altyapi_parsed, list): altyapi_parsed = [k for k,v in (altyapi_parsed if isinstance(altyapi_parsed, dict) else {}).items() if v]

        swot_parsed = {}
        if analiz.swot_analizi:
            try: swot_parsed = json.loads(analiz.swot_analizi)
            except: pass
            if not isinstance(swot_parsed, dict): swot_parsed = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}


        # ArsaAnalizci'den hesaplamaları al
        analizci = ArsaAnalizci()
        arsa_data_for_analizci = {
            "metrekare": float(analiz.metrekare or 0), "fiyat": float(analiz.fiyat or 0),
            "bolge_fiyat": float(analiz.bolge_fiyat or 0), "taks": float(analiz.taks or 0.3),
            "kaks": float(analiz.kaks or 1.5), "imar_durumu": analiz.imar_durumu or "",
            "altyapi": altyapi_parsed,
            "konum": {"il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle}
        }
        analiz_sonuclari = analizci.analiz_et(arsa_data_for_analizci.copy())
        # PPTX için analiz_ozeti'ne şimdilik ihtiyaç yok gibi, DocumentGenerator ona göre ayarlanmalı
        
        doc_arsa_data = {
            "id": analiz.id, "il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle,
            "ada": analiz.ada, "parsel": analiz.parsel,
            "metrekare": float(analiz.metrekare or 0), "imar_durumu": analiz.imar_durumu or "",
            "taks": float(analiz.taks or 0.3), "kaks": float(analiz.kaks or 1.5),
            "fiyat": float(analiz.fiyat or 0), "bolge_fiyat": float(analiz.bolge_fiyat or 0),
            "altyapi[]": altyapi_parsed, # DocumentGenerator'ın altyapi için beklediği anahtar
            "swot": swot_parsed, # DocumentGenerator swot için bu anahtarı bekliyor olabilir
            "created_at": analiz.created_at.strftime("%d.%m.%Y %H:%M"), # DocumentGenerator için eklendi
            "insaat_hesaplama": analiz_sonuclari.get("insaat_hesaplama", {})
        }
        
        user_profile_info = {
            "ad": current_user.ad, "soyad": current_user.soyad, "email": current_user.email,
            "telefon": current_user.telefon, "firma": current_user.firma, "unvan": current_user.unvan,
            "adres": current_user.adres, "profil_foto": current_user.profil_foto
        }
        
        # file_id olarak benzersiz bir ID veya analiz ID'si kullanılabilir.
        # output_dir olarak PRESENTATIONS_DIR kullanılmalı.
        temp_file_id = str(uuid.uuid4()) # Her sunum için benzersiz klasör ve dosya adı
        
        doc_gen = DocumentGenerator(
            arsa_data=doc_arsa_data, # Tüm arsa verilerini gönder
            analiz_ozeti=None, # PPTX için özet gerekmiyorsa
            file_id=temp_file_id,
            output_dir=current_app.config["PRESENTATIONS_DIR"],
            profile_info=user_profile_info,
            settings={"sections": sections, "color_scheme": color_scheme}
        )

        pptx_path = doc_gen.create_pptx()

        if pptx_path and os.path.exists(pptx_path):
            return send_file(pptx_path, as_attachment=True, download_name=f"analiz_sunum_{analiz.id}_{temp_file_id[:8]}.pptx")
        else:
            current_app.logger.error(f"PPTX sunum dosyası oluşturulamadı: {pptx_path}")
            return jsonify({"error": "Sunum oluşturulamadı"}), 500

    except Exception as e:
        current_app.logger.error(f"PPTX oluşturma hatası (ID: {analiz_id}): {str(e)}", exc_info=True)
        return jsonify({"error": f"Sunum oluşturulurken bir hata oluştu: {str(e)}"}), 500