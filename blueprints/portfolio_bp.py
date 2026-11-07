# blueprints/portfolio_bp.py
"""Portföy yönetimi: portföyler ilan içerir (spec §3.6); portfolio_arsalar yalnız okunur."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user

from models import db
from models.user_models import Portfolio
from models.arsa_models import ArsaAnaliz
from models.ilan_models import Ilan
from modules import gayrimenkul_sabitleri as sabit
from modules.ilan_servis import gorunur_gayrimenkuller, gorunur_ilanlar, secilebilir_ilanlar

portfolio_bp = Blueprint('portfolio', __name__, template_folder='../templates')

VISIBILITY_CHOICES = {'public': 'Herkese açık', 'private': 'Özel'}


def _own_portfolio_or_404(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    if portfolio.user_id != current_user.id:
        abort(404)
    return portfolio


def _portfolio_totals(ilanlar):
    """Portföy özeti: satılık fiyatları ve kiralık aylık kiralar ayrı toplanır."""
    return {
        'adet': len(ilanlar),
        'toplam_fiyat': sum(float(i.fiyat or 0) for i in ilanlar if i.teklif_tipi == 'satilik'),
        'aylik_kira': sum(float(i.kira or 0) for i in ilanlar if i.teklif_tipi == 'kiralik'),
        'kat_karsiligi_adet': sum(1 for i in ilanlar if i.teklif_tipi == 'kat_karsiligi'),
    }


def _gayrimenkulun_ilani(analiz_id):
    """Eski analiz_id için: görünür gayrimenkulün aktif ilanı, yoksa son ilanı (görünür olmalı)."""
    g = gorunur_gayrimenkuller(current_user).filter(ArsaAnaliz.id == analiz_id).first()
    if g is None:
        return None
    adaylar = [g.aktif_ilan] if g.aktif_ilan is not None else []
    adaylar += sorted((b.ilan for b in g.ilan_baglari if b.ilan is not None),
                      key=lambda i: (i.created_at is not None, i.created_at, i.id), reverse=True)
    for aday in adaylar:
        if gorunur_ilanlar(current_user).filter(Ilan.id == aday.id).first() is not None:
            return aday
    return None


@portfolio_bp.route('/portfolios')
@login_required
def portfolios_list():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '').strip()
    il_filter = request.args.get('il', '').strip()

    base = ArsaAnaliz.query.filter(ArsaAnaliz.user_id == current_user.id)
    query = base
    if search_term:
        like = f"%{search_term}%"
        query = query.filter(db.or_(
            ArsaAnaliz.il.ilike(like), ArsaAnaliz.ilce.ilike(like), ArsaAnaliz.mahalle.ilike(like),
            ArsaAnaliz.ada.ilike(like), ArsaAnaliz.parsel.ilike(like), ArsaAnaliz.imar_durumu.ilike(like),
        ))
    if il_filter:
        query = query.filter(ArsaAnaliz.il == il_filter)

    pagination = query.order_by(ArsaAnaliz.created_at.desc()).paginate(page=page, per_page=12, error_out=False)

    # İstatistikler tüm analizler üzerinden (sayfadan bağımsız)
    stats_row = base.with_entities(
        db.func.count(ArsaAnaliz.id), db.func.coalesce(db.func.sum(ArsaAnaliz.fiyat), 0),
        db.func.coalesce(db.func.sum(ArsaAnaliz.metrekare), 0),
        db.func.count(db.distinct(db.func.concat(ArsaAnaliz.il, '/', ArsaAnaliz.ilce))),
    ).one()
    stats = {
        'toplam_analiz': stats_row[0],
        'toplam_deger': float(stats_row[1]),
        'toplam_m2': float(stats_row[2]),
        'lokasyon': stats_row[3],
    }
    unique_ils = [r[0] for r in base.with_entities(ArsaAnaliz.il).distinct().order_by(ArsaAnaliz.il).all() if r[0]]
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).order_by(Portfolio.created_at.desc()).all()

    return render_template(
        'new_portfolios.html',
        analyses=pagination.items, pagination=pagination, stats=stats, portfolios=portfolios,
        search_term=search_term, il_filter=il_filter, unique_ils=unique_ils, title='Portföy',
    )


@portfolio_bp.route('/create', methods=['GET', 'POST'])
@login_required
def portfolio_create():
    ilanlar = secilebilir_ilanlar(current_user)

    def sayfa(form_data, kod=200, preselected=None):
        from blueprints.ilan_bp import kart_ozeti
        return render_template('portfolio_create.html', form_data=form_data, ilanlar=ilanlar, kart_ozeti=kart_ozeti,
                               preselected=preselected, visibility_choices=VISIBILITY_CHOICES), kod

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        visibility = request.form.get('visibility', 'private')
        if not title:
            flash('Portföy adı zorunludur.', 'danger')
            return sayfa(request.form, 400)
        if visibility not in VISIBILITY_CHOICES:
            visibility = 'private'
        try:
            portfolio = Portfolio(user_id=current_user.id, title=title[:200],
                                  description=(request.form.get('description') or '').strip(), visibility=visibility)
            selected_ids = {int(i) for i in request.form.getlist('ilan_ids') if i.isdigit()}
            for i in ilanlar:
                if i.id in selected_ids:
                    portfolio.ilanlar.append(i)
            db.session.add(portfolio)
            db.session.commit()
            flash('Portföy başarıyla oluşturuldu.', 'success')
            return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Portfolio creation error: {e}", exc_info=True)
            flash('Portföy oluşturulurken bir hata oluştu.', 'danger')
            return sayfa(request.form, 500)

    preselected = request.args.get('ilan_id', type=int)
    analiz_id = request.args.get('analiz_id', type=int)
    if preselected is None and analiz_id is not None:
        bulunan = _gayrimenkulun_ilani(analiz_id)
        preselected = bulunan.id if bulunan else None
    return sayfa({}, preselected=preselected)


@portfolio_bp.route('/<int:portfolio_id>')
@login_required
def portfolio_detail(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    is_owner = portfolio.user_id == current_user.id
    if portfolio.visibility == 'private' and not is_owner and current_user.role != 'superadmin':
        abort(404)
    ilanlar = portfolio.ilanlar.order_by(Ilan.created_at.desc(), Ilan.id.desc()).all()
    ids = [i.id for i in ilanlar]
    gorunur = {iid for (iid,) in gorunur_ilanlar(current_user).filter(Ilan.id.in_(ids))
               .with_entities(Ilan.id)} if ids else set()
    available = [i for i in secilebilir_ilanlar(current_user) if i.id not in set(ids)] if is_owner else []
    from blueprints.ilan_bp import fiyat_metni, kart_ozeti  # app.py ilan_bp'yi geç yükler
    return render_template('portfolio_detail.html', portfolio=portfolio, ilanlar=ilanlar, available=available,
                           gorunur=gorunur, totals=_portfolio_totals(ilanlar), is_owner=is_owner,
                           fiyat_metni=fiyat_metni, kart_ozeti=kart_ozeti, sabit=sabit,
                           visibility_choices=VISIBILITY_CHOICES)


@portfolio_bp.route('/<int:portfolio_id>/edit', methods=['POST'])
@login_required
def portfolio_edit(portfolio_id):
    portfolio = _own_portfolio_or_404(portfolio_id)
    title = (request.form.get('title') or '').strip()
    if not title:
        flash('Portföy adı zorunludur.', 'danger')
    else:
        portfolio.title = title[:200]
        portfolio.description = (request.form.get('description') or '').strip()
        vis = request.form.get('visibility')
        if vis in VISIBILITY_CHOICES:
            portfolio.visibility = vis
        db.session.commit()
        flash('Portföy güncellendi.', 'success')
    return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))


@portfolio_bp.route('/<int:portfolio_id>/delete', methods=['POST'])
@login_required
def portfolio_delete(portfolio_id):
    portfolio = _own_portfolio_or_404(portfolio_id)
    db.session.delete(portfolio)  # İlanlar silinmez, sadece portföy bağlantıları kalkar
    db.session.commit()
    flash('Portföy silindi. İçindeki ilanlar korunuyor.', 'success')
    return redirect(url_for('portfolio.portfolios_list'))


def _ilan_ekle(portfolio):
    """Formdaki ilan_id(ler)i (ya da eski analiz_id'yi) portföye ekler; flash mesajı yazar."""
    f = request.form
    ids = {int(x) for x in f.getlist('ilan_id') + f.getlist('ilan_ids') if x.strip().isdigit()}
    bulunan = gorunur_ilanlar(current_user).filter(Ilan.id.in_(ids)).all() if ids else []
    eski = [x for x in f.getlist('analiz_id') + f.getlist('analiz_ids') if x.strip().isdigit()]
    for analiz_id in eski:
        i = _gayrimenkulun_ilani(int(analiz_id))
        if i is None:
            flash('Bu gayrimenkulün portföye eklenecek ilanı yok.', 'danger')
            return
        bulunan.append(i)
    atlanan = len(ids) - len({i.id for i in bulunan if i.id in ids})
    if atlanan and bulunan:
        flash(f'{atlanan} ilan bulunamadığı için atlandı.', 'warning')
    if not bulunan:
        flash('Seçilen ilan bulunamadı.' if ids else 'Eklenecek ilan seçilmedi.', 'warning')
        return
    mevcut = {i.id for i in portfolio.ilanlar}
    eklenen = 0
    for i in bulunan:
        if i.id not in mevcut:
            portfolio.ilanlar.append(i)
            mevcut.add(i.id)
            eklenen += 1
    db.session.commit()
    if eklenen:
        flash(f'{eklenen} ilan "{portfolio.title}" portföyüne eklendi.', 'success')
    else:
        flash('Seçilen ilanlar zaten portföyde.', 'info')


def _ekleme_sonrasi(portfolio):
    ilan_id = request.form.get('ilan_id', '')
    if request.form.get('geri') == 'ilan' and ilan_id.isdigit():
        return redirect(url_for('ilan.detay', ilan_id=int(ilan_id)))
    return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))


@portfolio_bp.route('/<int:portfolio_id>/add', methods=['POST'])
@login_required
def portfolio_add_analysis(portfolio_id):
    """Portföye ilan ekler (form: ilan_id/ilan_ids; eski analiz_id → gayrimenkulün aktif/son ilanı)."""
    portfolio = _own_portfolio_or_404(portfolio_id)
    _ilan_ekle(portfolio)
    return _ekleme_sonrasi(portfolio)


@portfolio_bp.route('/ilan-ekle', methods=['POST'])
@login_required
def portfolio_add_ilan_secili():
    """İlan detayındaki "Portföye ekle": portföy formdaki portfolio_id ile seçilir."""
    pid = request.form.get('portfolio_id', '')
    if not pid.isdigit():
        abort(404)
    portfolio = _own_portfolio_or_404(int(pid))
    _ilan_ekle(portfolio)
    return _ekleme_sonrasi(portfolio)


@portfolio_bp.route('/<int:portfolio_id>/remove/<int:ilan_id>', methods=['POST'])
@login_required
def portfolio_remove_analysis(portfolio_id, ilan_id):
    portfolio = _own_portfolio_or_404(portfolio_id)
    ilan = portfolio.ilanlar.filter(Ilan.id == ilan_id).first()
    if ilan:
        portfolio.ilanlar.remove(ilan)
        db.session.commit()
        flash(f'{ilan.kod} portföyden çıkarıldı.', 'success')
    else:
        flash('İlan bu portföyde bulunamadı.', 'warning')
    return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))
