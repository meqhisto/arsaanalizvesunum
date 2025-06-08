# blueprints/api/v1/portfolio.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc
from datetime import datetime

from models import db
from models.user_models import Portfolio, portfolio_arsalar
from models.arsa_models import ArsaAnaliz
from ..schemas.user_schemas import (
    PortfolioSchema, PortfolioCreateSchema, PortfolioUpdateSchema
)
from ..schemas.analysis_schemas import ArsaAnalizSchema
from ..utils.decorators import (
    validate_json, log_api_call, handle_db_errors,
    paginate_query, )
from ..utils.responses import (
    success_response, error_response, not_found_response,
    paginated_response
)

portfolio_v1 = Blueprint('portfolio_v1', __name__)


@portfolio_v1.route('', methods=['GET'])
@()
@log_api_call
@paginate_query()
def list_portfolios(page, per_page):
    """
    Portfolio listesi
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
      - in: query
        name: visibility
        type: string
        description: Filter by visibility (public/private)
    responses:
      200:
        description: Portfolios retrieved successfully
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Filtreleme parametreleri
    visibility = request.args.get('visibility', '').strip()
    
    # Base query
    query = Portfolio.query.filter_by(user_id=current_user.id)
    
    # Visibility filtresi
    if visibility:
        query = query.filter(Portfolio.visibility == visibility)
    
    # Sıralama
    query = query.order_by(desc(Portfolio.created_at))
    
    # Sayfalama
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Serialize
    portfolio_schema = PortfolioSchema(many=True)
    portfolios_data = portfolio_schema.dump(pagination.items)
    
    return paginated_response(
        data=portfolios_data,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message="Portfolios retrieved successfully"
    )


@portfolio_v1.route('', methods=['POST'])
@()
@log_api_call
@handle_db_errors
@validate_json(PortfolioCreateSchema)
def create_portfolio(data):
    """
    Yeni portfolio oluştur
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: body
        name: portfolio
        description: Portfolio data
        required: true
        schema:
          $ref: '#/definitions/PortfolioCreate'
    responses:
      201:
        description: Portfolio created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Portfolio oluştur
    portfolio = Portfolio(
        user_id=current_user.id,
        **data
    )
    
    db.session.add(portfolio)
    db.session.commit()
    
    portfolio_schema = PortfolioSchema()
    portfolio_data = portfolio_schema.dump(portfolio)
    
    current_app.logger.info(f"Portfolio created: {portfolio.title}")
    return success_response(
        data=portfolio_data,
        message="Portfolio created successfully",
        status_code=201
    )


@portfolio_v1.route('/<int:portfolio_id>', methods=['GET'])
@()
@log_api_call
def get_portfolio(portfolio_id):
    """
    Portfolio detayı
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
    responses:
      200:
        description: Portfolio retrieved successfully
      401:
        description: Unauthorized
      404:
        description: Portfolio not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    portfolio_schema = PortfolioSchema()
    portfolio_data = portfolio_schema.dump(portfolio)
    
    # Portfolio'daki analizleri de ekle
    analyses = portfolio.analizler.all()
    analysis_schema = ArsaAnalizSchema(many=True)
    portfolio_data['analyses'] = analysis_schema.dump(analyses)
    
    return success_response(
        data=portfolio_data,
        message="Portfolio retrieved successfully"
    )


@portfolio_v1.route('/<int:portfolio_id>', methods=['PUT'])
@()
@log_api_call
@handle_db_errors
@validate_json(PortfolioUpdateSchema)
def update_portfolio(portfolio_id, data):
    """
    Portfolio güncelle
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
      - in: body
        name: portfolio
        description: Updated portfolio data
        required: true
        schema:
          $ref: '#/definitions/PortfolioUpdate'
    responses:
      200:
        description: Portfolio updated successfully
      401:
        description: Unauthorized
      404:
        description: Portfolio not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    # Portfolio güncelle
    for field, value in data.items():
        if hasattr(portfolio, field):
            setattr(portfolio, field, value)
    
    portfolio.updated_at = datetime.utcnow()
    db.session.commit()
    
    portfolio_schema = PortfolioSchema()
    portfolio_data = portfolio_schema.dump(portfolio)
    
    current_app.logger.info(f"Portfolio updated: {portfolio.title}")
    return success_response(
        data=portfolio_data,
        message="Portfolio updated successfully"
    )


@portfolio_v1.route('/<int:portfolio_id>', methods=['DELETE'])
@()
@log_api_call
@handle_db_errors
def delete_portfolio(portfolio_id):
    """
    Portfolio sil
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
    responses:
      200:
        description: Portfolio deleted successfully
      401:
        description: Unauthorized
      404:
        description: Portfolio not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    db.session.delete(portfolio)
    db.session.commit()
    
    current_app.logger.info(f"Portfolio deleted: {portfolio.title}")
    return success_response(message="Portfolio deleted successfully")


@portfolio_v1.route('/<int:portfolio_id>/analyses', methods=['GET'])
@()
@log_api_call
@paginate_query()
def get_portfolio_analyses(portfolio_id, page, per_page):
    """
    Portfolio analizleri
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: Portfolio analyses retrieved successfully
      401:
        description: Unauthorized
      404:
        description: Portfolio not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    # Portfolio analizlerini sayfalama ile getir
    query = portfolio.analizler.order_by(desc(ArsaAnaliz.created_at))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Serialize
    analysis_schema = ArsaAnalizSchema(many=True)
    analyses_data = analysis_schema.dump(pagination.items)
    
    return paginated_response(
        data=analyses_data,
        page=page,
        per_page=per_page,
        total=pagination.total,
        message="Portfolio analyses retrieved successfully"
    )


@portfolio_v1.route('/<int:portfolio_id>/analyses', methods=['POST'])
@()
@log_api_call
@handle_db_errors
def add_analysis_to_portfolio(portfolio_id):
    """
    Portfolio'ya analiz ekle
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
      - in: body
        name: analysis_ids
        description: Analysis IDs to add
        required: true
        schema:
          type: object
          required:
            - analysis_ids
          properties:
            analysis_ids:
              type: array
              items:
                type: integer
    responses:
      200:
        description: Analyses added to portfolio successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
      404:
        description: Portfolio or analysis not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    data = request.get_json()
    if not data or 'analysis_ids' not in data:
        return error_response("analysis_ids is required", 400)
    
    analysis_ids = data['analysis_ids']
    if not isinstance(analysis_ids, list):
        return error_response("analysis_ids must be a list", 400)
    
    # Analizleri kontrol et ve ekle
    added_count = 0
    for analysis_id in analysis_ids:
        analysis = ArsaAnaliz.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if analysis and analysis not in portfolio.analizler:
            portfolio.analizler.append(analysis)
            added_count += 1
    
    if added_count > 0:
        portfolio.updated_at = datetime.utcnow()
        db.session.commit()
    
    current_app.logger.info(f"Added {added_count} analyses to portfolio: {portfolio.title}")
    return success_response(
        message=f"{added_count} analyses added to portfolio successfully"
    )


@portfolio_v1.route('/<int:portfolio_id>/analyses/<int:analysis_id>', methods=['DELETE'])
@()
@log_api_call
@handle_db_errors
def remove_analysis_from_portfolio(portfolio_id, analysis_id):
    """
    Portfolio'dan analiz çıkar
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
      - in: path
        name: analysis_id
        type: integer
        required: true
    responses:
      200:
        description: Analysis removed from portfolio successfully
      401:
        description: Unauthorized
      404:
        description: Portfolio or analysis not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    analysis = ArsaAnaliz.query.filter_by(
        id=analysis_id,
        user_id=current_user.id
    ).first()
    
    if not analysis:
        return not_found_response("Analysis not found")
    
    if analysis in portfolio.analizler:
        portfolio.analizler.remove(analysis)
        portfolio.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Analysis removed from portfolio: {portfolio.title}")
        return success_response(message="Analysis removed from portfolio successfully")
    else:
        return error_response("Analysis is not in this portfolio", 400)


@portfolio_v1.route('/<int:portfolio_id>/stats', methods=['GET'])
@()
@log_api_call
def get_portfolio_stats(portfolio_id):
    """
    Portfolio istatistikleri
    ---
    tags:
      - Portfolio
    security:
      - Bearer: []
    parameters:
      - in: path
        name: portfolio_id
        type: integer
        required: true
    responses:
      200:
        description: Portfolio statistics retrieved successfully
      401:
        description: Unauthorized
      404:
        description: Portfolio not found
    """
    current_user = ()
    portfolio = Portfolio.query.filter_by(
        id=portfolio_id,
        user_id=current_user.id
    ).first()
    
    if not portfolio:
        return not_found_response("Portfolio not found")
    
    # Portfolio analizlerini al
    analyses = portfolio.analizler.all()
    
    if not analyses:
        stats = {
            'total_analyses': 0,
            'total_area': 0,
            'total_value': 0,
            'average_price_per_sqm': 0,
            'average_roi': 0,
            'risk_distribution': {},
            'region_distribution': {}
        }
    else:
        # İstatistikleri hesapla
        total_area = sum(float(a.metrekare or 0) for a in analyses)
        total_value = sum(float(a.yaklasik_deger or 0) for a in analyses)
        prices_per_sqm = [float(a.tahmini_deger_m2 or 0) for a in analyses if a.tahmini_deger_m2]
        rois = [float(a.yatirim_getirisi or 0) for a in analyses if a.yatirim_getirisi]
        
        # Risk dağılımı
        risk_distribution = {}
        for analysis in analyses:
            risk = analysis.risk_skoru or 0
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # Bölge dağılımı
        region_distribution = {}
        for analysis in analyses:
            region = f"{analysis.il}/{analysis.ilce}"
            region_distribution[region] = region_distribution.get(region, 0) + 1
        
        stats = {
            'total_analyses': len(analyses),
            'total_area': total_area,
            'total_value': total_value,
            'average_price_per_sqm': sum(prices_per_sqm) / len(prices_per_sqm) if prices_per_sqm else 0,
            'average_roi': sum(rois) / len(rois) if rois else 0,
            'risk_distribution': risk_distribution,
            'region_distribution': region_distribution
        }
    
    return success_response(
        data=stats,
        message="Portfolio statistics retrieved successfully"
    )
