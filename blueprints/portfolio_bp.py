# blueprints/portfolio_bp.py
"""Portföy yönetimi: kullanıcının analizlerini ve analizlerden oluşan portföy (koleksiyon) kayıtlarını yönetir."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user

from models import db
from models.user_models import Portfolio
from models.arsa_models import ArsaAnaliz

portfolio_bp = Blueprint('portfolio', __name__, template_folder='../templates')

VISIBILITY_CHOICES = {'public': 'Herkese açık', 'private': 'Özel'}


def _own_portfolio_or_404(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    if portfolio.user_id != current_user.id:
        abort(404)
    return portfolio


def _portfolio_totals(analyses):
    toplam_fiyat = sum(float(a.fiyat or 0) for a in analyses)
    toplam_m2 = sum(float(a.metrekare or 0) for a in analyses)
    return {
        'adet': len(analyses),
        'toplam_fiyat': toplam_fiyat,
        'toplam_m2': toplam_m2,
        'ort_m2_fiyat': (toplam_fiyat / toplam_m2) if toplam_m2 else 0,
    }


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
    user_analyses = ArsaAnaliz.query.filter_by(user_id=current_user.id).order_by(ArsaAnaliz.created_at.desc()).all()
    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        visibility = request.form.get('visibility', 'private')
        if not title:
            flash('Portföy adı zorunludur.', 'danger')
            return render_template('portfolio_create.html', form_data=request.form, analyses=user_analyses,
                                   visibility_choices=VISIBILITY_CHOICES), 400
        if visibility not in VISIBILITY_CHOICES:
            visibility = 'private'
        try:
            portfolio = Portfolio(user_id=current_user.id, title=title[:200],
                                  description=(request.form.get('description') or '').strip(), visibility=visibility)
            selected_ids = {int(i) for i in request.form.getlist('analiz_ids') if i.isdigit()}
            for analiz in user_analyses:
                if analiz.id in selected_ids:
                    portfolio.analizler.append(analiz)
            db.session.add(portfolio)
            db.session.commit()
            flash('Portföy başarıyla oluşturuldu.', 'success')
            return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Portfolio creation error: {e}", exc_info=True)
            flash('Portföy oluşturulurken bir hata oluştu.', 'danger')
            return render_template('portfolio_create.html', form_data=request.form, analyses=user_analyses,
                                   visibility_choices=VISIBILITY_CHOICES), 500

    preselected = request.args.get('analiz_id', type=int)
    return render_template('portfolio_create.html', form_data={}, analyses=user_analyses,
                           preselected=preselected, visibility_choices=VISIBILITY_CHOICES)


@portfolio_bp.route('/<int:portfolio_id>')
@login_required
def portfolio_detail(portfolio_id):
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    is_owner = portfolio.user_id == current_user.id
    if portfolio.visibility == 'private' and not is_owner and current_user.role != 'superadmin':
        abort(404)
    analyses = portfolio.analizler.order_by(ArsaAnaliz.created_at.desc()).all()
    available = []
    if is_owner:
        in_ids = {a.id for a in analyses}
        available = [a for a in ArsaAnaliz.query.filter_by(user_id=current_user.id)
                     .order_by(ArsaAnaliz.created_at.desc()).all() if a.id not in in_ids]
    return render_template('portfolio_detail.html', portfolio=portfolio, analyses=analyses, available=available,
                           totals=_portfolio_totals(analyses), is_owner=is_owner,
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
    db.session.delete(portfolio)  # Analizler silinmez, sadece portföy bağlantıları kalkar
    db.session.commit()
    flash('Portföy silindi. İçindeki analizler korunuyor.', 'success')
    return redirect(url_for('portfolio.portfolios_list'))


@portfolio_bp.route('/<int:portfolio_id>/add', methods=['POST'])
@login_required
def portfolio_add_analysis(portfolio_id):
    portfolio = _own_portfolio_or_404(portfolio_id)
    ids = {int(i) for i in request.form.getlist('analiz_ids') if i.isdigit()}
    existing = {a.id for a in portfolio.analizler}
    added = 0
    for analiz in ArsaAnaliz.query.filter(ArsaAnaliz.id.in_(ids), ArsaAnaliz.user_id == current_user.id).all():
        if analiz.id not in existing:
            portfolio.analizler.append(analiz)
            added += 1
    db.session.commit()
    flash(f'{added} analiz portföye eklendi.' if added else 'Eklenecek analiz seçilmedi.', 'success' if added else 'warning')
    return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))


@portfolio_bp.route('/<int:portfolio_id>/remove/<int:analiz_id>', methods=['POST'])
@login_required
def portfolio_remove_analysis(portfolio_id, analiz_id):
    portfolio = _own_portfolio_or_404(portfolio_id)
    analiz = portfolio.analizler.filter(ArsaAnaliz.id == analiz_id).first()
    if analiz:
        portfolio.analizler.remove(analiz)
        db.session.commit()
        flash('Analiz portföyden çıkarıldı.', 'success')
    else:
        flash('Analiz bu portföyde bulunamadı.', 'warning')
    return redirect(url_for('portfolio.portfolio_detail', portfolio_id=portfolio.id))
