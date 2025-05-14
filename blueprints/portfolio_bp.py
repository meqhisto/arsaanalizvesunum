# blueprints/portfolio_bp.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from flask_login import login_required, current_user

# Modelleri ve db nesnesini models paketinden import et
from models import db
from models.user_models import User, Portfolio # Portfolio modelini de import et
from models.arsa_models import ArsaAnaliz # ArsaAnaliz de portfolyo sayfasında kullanılıyor

# Flask uygulamasının yapılandırmasına erişmek için current_app
from flask import current_app

portfolio_bp = Blueprint('portfolio', __name__, template_folder='../templates')
 
# Eğer portfolyo şablonları templates/portfolio/ altındaysa, template_folder='../templates/portfolio' yapın.

@portfolio_bp.route('/portfolios') # url_prefix ana app.py'de /portfolio olarak ayarlanacak
@login_required
def portfolios_list(): # Fonksiyon adını endpoint ile eşleşmesi için değiştirdim (eski portfolios)
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '').strip()
    per_page = 15

    # ArsaAnaliz objelerini çekip, user ilişkisi üzerinden kullanıcı bilgilerine erişmek.
    # Bu, add_columns() kullanmaktan daha standart bir ORM yaklaşımıdır.
    # Eski app.py'deki sorgu biraz karışıktı, burada daha temiz bir hale getirelim.
    # User ilişkisi ArsaAnaliz modelinde 'user' olarak tanımlı.
    
    query = ArsaAnaliz.query.join(ArsaAnaliz.user).filter(User.is_active == True)

    if search_term:
        search_like = f"%{search_term}%"
        query = query.filter(
            db.or_(
                ArsaAnaliz.il.ilike(search_like),
                ArsaAnaliz.ilce.ilike(search_like),
                ArsaAnaliz.mahalle.ilike(search_like),
                User.ad.ilike(search_like),
                User.soyad.ilike(search_like),
                ArsaAnaliz.imar_durumu.ilike(search_like)
            )
        )
    
    # `paginated_analyses` artık doğrudan ArsaAnaliz nesnelerinin bir listesini içeren bir Pagination objesi.
    # Şablonda `analiz.il`, `analiz.user.ad`, `analiz.user.profil_foto` gibi erişimler kullanılabilir.
    paginated_analyses = query.order_by(ArsaAnaliz.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Şablona gönderilecek veri, doğrudan paginated_analyses.items olabilir.
    # Eski kodda results_for_template diye bir dönüşüm vardı,
    # eğer şablonunuz (portfolios.html) analiz_data.ArsaAnaliz.il ve analiz_data.ad
    # gibi bir yapı bekliyorsa, o dönüşümü korumanız gerekir.
    # Ancak `ArsaAnaliz.user` ilişkisiyle bu daha temiz olur.
    # Şimdilik şablonun `analiz.ArsaAnaliz.il` ve `analiz.ad` beklediğini varsayarak
    # eski yapıya benzer bir veri hazırlayalım.
    # AMA TAVSİYEM: Şablonu `paginated_analyses.items` listesindeki ArsaAnaliz objelerini
    # ve `analiz.user` ilişkisini kullanacak şekilde güncellemek olur.

    # portfolios.html şablonu `analiz.ArsaAnaliz.il` ve `analiz.ad` şeklinde kullanıyor.
    # Bu, `ArsaAnaliz` ve `User` objelerini ayrı ayrı alıp bir sözlükte birleştirmeyi gerektirir.
    # Bu durum, sorguyu `db.session.query(ArsaAnaliz, User)` ile yapıp,
    # sonra şablonda `item.ArsaAnaliz` ve `item.User` olarak erişmekle benzer.
    # Şablonunuzu doğrudan ArsaAnaliz objeleriyle çalışacak şekilde güncellemek en iyisi.
    # Şimdilik eski `portfolios.html` şablonuna uyum sağlamak için sorguyu query(ArsaAnaliz, User) yapalım.

    final_query = db.session.query(ArsaAnaliz, User).join(User, ArsaAnaliz.user_id == User.id).filter(User.is_active == True)
    if search_term:
        search_like = f"%{search_term}%"
        final_query = final_query.filter(
            db.or_(
                ArsaAnaliz.il.ilike(search_like),
                ArsaAnaliz.ilce.ilike(search_like),
                ArsaAnaliz.mahalle.ilike(search_like),
                User.ad.ilike(search_like),
                User.soyad.ilike(search_like)
            )
        )
    
    paginated_results_tuples = final_query.order_by(ArsaAnaliz.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    results_for_template = []
    for arsa_analiz_obj, user_obj in paginated_results_tuples.items:
        results_for_template.append({
            "ArsaAnaliz": arsa_analiz_obj, # Şablonda analiz_data.ArsaAnaliz.il
            "ad": user_obj.ad,             # Şablonda analiz_data.ad
            "soyad": user_obj.soyad,         # Şablonda analiz_data.soyad
            "profil_foto": user_obj.profil_foto # Şablonda analiz_data.profil_foto
        })

    return render_template(
        "portfolios.html", # templates/portfolios.html
        analizler=results_for_template, # Şablona uygun hale getirilmiş veri
        pagination=paginated_results_tuples, # Sayfalama için Pagination objesi
        title="Tüm Kullanıcı Analizleri", # Başlık güncellendi
        search_term=search_term 
    )

@portfolio_bp.route('/create', methods=['GET', 'POST']) # url_prefix ile /portfolio/create olacak
@login_required
def portfolio_create():
    if request.method == 'POST':
        try:
            new_portfolio = Portfolio(
                user_id=current_user.id, # session['user_id'] yerine current_user.id
                title=request.form.get('title'),
                description=request.form.get('description'),
                visibility=request.form.get('visibility', 'public')
            )
            db.session.add(new_portfolio)
            db.session.commit()
            flash('Portföy başarıyla oluşturuldu.', 'success')
            # Nereye yönlendirileceğine karar verin:
            # Belki yeni oluşturulan portföyün detayına veya portföy listesine
            return redirect(url_for('portfolio.portfolios_list')) # Portföy listesine yönlendir
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Portfolio creation error: {str(e)}", exc_info=True)
            flash('Portföy oluşturulurken bir hata oluştu.', 'danger')
            # Hata durumunda formu tekrar göster, girilen verilerle
            return render_template('portfolio_create.html', form_data=request.form)

    return render_template('portfolio_create.html', form_data={}) # templates/portfolio_create.html

@portfolio_bp.route('/<int:portfolio_id>') # url_prefix ile /portfolio/<id> olacak
@login_required
def portfolio_detail(portfolio_id): # Fonksiyon adı id yerine portfolio_id aldı
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    # Portföy private ise ve kullanıcının kendi portföyü değilse erişimi engelle
    if portfolio.visibility == 'private' and portfolio.user_id != current_user.id:
        # Eğer başkalarının private portföylerini adminler görebilecekse burada ek kontrol
        # if not current_user.is_admin: # Varsayımsal bir is_admin özelliği
        flash('Bu portföye erişim yetkiniz yok.', 'danger')
        return redirect(url_for('portfolio.portfolios_list')) # Veya ana sayfaya

    # portfolio_detail.html şablonu, portfolio nesnesini ve içindeki analizleri (portfolio.analizler) kullanır.
    # portfolio.analizler, Portfolio modelindeki ilişki sayesinde ArsaAnaliz nesnelerini içerir.
    return render_template('portfolio_detail.html', portfolio=portfolio) # templates/portfolio_detail.html

# --- Portföye Analiz Ekleme/Çıkarma (Opsiyonel, eğer böyle bir işlevsellik varsa) ---
# Bu rotalar için ayrı formlar ve mantık gerekebilir.
# Örnek:
# @portfolio_bp.route('/<int:portfolio_id>/add_analysis', methods=['GET', 'POST'])
# @login_required
# def portfolio_add_analysis(portfolio_id):
#     portfolio = Portfolio.query.get_or_404(portfolio_id)
#     if portfolio.user_id != current_user.id:
#         flash("Yetkisiz işlem.", "danger")
#         return redirect(url_for('portfolio.portfolios_list'))
    
#     if request.method == 'POST':
#         analiz_id_to_add = request.form.get('analiz_id')
#         analiz = ArsaAnaliz.query.get(analiz_id_to_add)
#         if analiz and analiz.user_id == current_user.id: # Sadece kendi analizlerini ekleyebilsin
#             if analiz not in portfolio.analizler:
#                 portfolio.analizler.append(analiz)
#                 db.session.commit()
#                 flash(f"'{analiz.il} {analiz.ilce}' analizi portföye eklendi.", "success")
#             else:
#                 flash("Bu analiz zaten portföyde.", "info")
#         else:
#             flash("Geçersiz analiz seçimi.", "danger")
#         return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))

#     # Kullanıcının portföye ekleyebileceği analizleri listele
#     user_analyses = ArsaAnaliz.query.filter_by(user_id=current_user.id).order_by(ArsaAnaliz.created_at.desc()).all()
#     # Portföyde olmayanları filtrele
#     available_analyses = [a for a in user_analyses if a not in portfolio.analizler]
#     return render_template('portfolio_add_analysis.html', portfolio=portfolio, analyses=available_analyses)

# @portfolio_bp.route('/<int:portfolio_id>/remove_analysis/<int:analiz_id>', methods=['POST'])
# @login_required
# def portfolio_remove_analysis(portfolio_id, analiz_id):
#     portfolio = Portfolio.query.get_or_404(portfolio_id)
#     if portfolio.user_id != current_user.id:
#         flash("Yetkisiz işlem.", "danger")
#         return redirect(url_for('portfolio.portfolios_list'))

#     analiz_to_remove = ArsaAnaliz.query.get(analiz_id)
#     if analiz_to_remove and analiz_to_remove in portfolio.analizler:
#         portfolio.analizler.remove(analiz_to_remove)
#         db.session.commit()
#         flash("Analiz portföyden çıkarıldı.", "success")
#     else:
#         flash("Analiz portföyde bulunamadı.", "danger")
#     return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))