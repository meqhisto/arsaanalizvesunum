# blueprints/api/v1/portfolio_minimal.py
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.user_models import Portfolio
from models.arsa_models import ArsaAnaliz
from ..utils.decorators import log_api_call
from ..utils.responses import success_response, error_response, not_found_response

# Portfolio Blueprint
portfolio_v1 = Blueprint('portfolio_v1', __name__)


@portfolio_v1.route('', methods=['POST'])
@jwt_required()
@log_api_call
def create_portfolio():
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
          type: object
          required:
            - title
          properties:
            title:
              type: string
              minLength: 1
              maxLength: 200
            description:
              type: string
            visibility:
              type: string
              enum: ['public', 'private']
              default: 'public'
    responses:
      201:
        description: Portfolio created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)
        
        if not current_user:
            return not_found_response("User not found")
        
        # JSON verilerini al
        data = request.get_json()
        if not data:
            return error_response("No JSON data provided", 400)
        
        # Temel validasyonlar
        required_fields = ['title']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f"Missing required field: {field}", 400)
        
        # Title uzunluk kontrolü
        title = data['title'].strip()
        if len(title) < 1 or len(title) > 200:
            return error_response("Title must be between 1 and 200 characters", 400)
        
        # Visibility kontrolü
        visibility = data.get('visibility', 'public')
        if visibility not in ['public', 'private']:
            return error_response("Visibility must be 'public' or 'private'", 400)
        
        # Portfolio oluştur
        portfolio = Portfolio(
            user_id=current_user.id,
            title=title,
            description=data.get('description', '').strip() or None,
            visibility=visibility
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        # Response data hazırla
        portfolio_data = {
            'id': portfolio.id,
            'title': portfolio.title,
            'description': portfolio.description,
            'visibility': portfolio.visibility,
            'arsa_count': 0,  # Yeni oluşturulan portfolio'da henüz arsa yok
            'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
            'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None,
            'user_id': portfolio.user_id
        }
        
        current_app.logger.info(f"Portfolio created: {portfolio.title} by user {current_user.id}")
        return success_response(
            data=portfolio_data,
            message="Portfolio created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Portfolio creation error: {str(e)}")
        return error_response("Portfolio creation failed", 500)


@portfolio_v1.route('', methods=['GET'])
@jwt_required()
@log_api_call
def list_portfolios():
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
      - in: query
        name: search
        type: string
        description: Search in title or description
    responses:
      200:
        description: Portfolios retrieved successfully
      401:
        description: Unauthorized
    """
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)
        
        if not current_user:
            return not_found_response("User not found")
        
        # Parametreler
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        visibility = request.args.get('visibility', '').strip()
        search = request.args.get('search', '').strip()
        
        # Base query
        query = Portfolio.query.filter_by(user_id=current_user.id)
        
        # Visibility filtresi
        if visibility and visibility in ['public', 'private']:
            query = query.filter(Portfolio.visibility == visibility)
        
        # Arama filtresi
        if search:
            from sqlalchemy import or_
            search_filter = or_(
                Portfolio.title.ilike(f'%{search}%'),
                Portfolio.description.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        # Sıralama
        query = query.order_by(Portfolio.created_at.desc())
        
        # Sayfalama
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Response data hazırla
        portfolios_data = []
        for portfolio in pagination.items:
            # Arsa sayısını hesapla
            arsa_count = portfolio.analizler.count() if portfolio.analizler else 0
            
            portfolio_data = {
                'id': portfolio.id,
                'title': portfolio.title,
                'description': portfolio.description,
                'visibility': portfolio.visibility,
                'arsa_count': arsa_count,
                'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
                'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None,
                'user_id': portfolio.user_id
            }
            portfolios_data.append(portfolio_data)
        
        response_data = {
            'data': portfolios_data,
            'meta': {
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'total_pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        }
        
        return success_response(
            data=response_data,
            message="Portfolios retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"List portfolios error: {str(e)}")
        return error_response("Failed to retrieve portfolios", 500)


@portfolio_v1.route('/<int:portfolio_id>', methods=['GET'])
@jwt_required()
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
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)
        
        if not current_user:
            return not_found_response("User not found")
        
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=current_user.id
        ).first()
        
        if not portfolio:
            return not_found_response("Portfolio not found")
        
        # Portfolio'daki analizleri al
        analyses = portfolio.analizler.all() if portfolio.analizler else []
        analyses_data = []
        
        for analysis in analyses:
            analysis_data = {
                'id': analysis.id,
                'il': analysis.il,
                'ilce': analysis.ilce,
                'mahalle': analysis.mahalle,
                'metrekare': float(analysis.metrekare),
                'fiyat': float(analysis.fiyat),
                'imar_durumu': analysis.imar_durumu,
                'created_at': analysis.created_at.isoformat() if analysis.created_at else None
            }
            analyses_data.append(analysis_data)
        
        # Response data hazırla
        portfolio_data = {
            'id': portfolio.id,
            'title': portfolio.title,
            'description': portfolio.description,
            'visibility': portfolio.visibility,
            'arsa_count': len(analyses_data),
            'analyses': analyses_data,
            'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
            'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None,
            'user_id': portfolio.user_id
        }
        
        return success_response(
            data=portfolio_data,
            message="Portfolio retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Get portfolio error: {str(e)}")
        return error_response("Failed to retrieve portfolio", 500)
