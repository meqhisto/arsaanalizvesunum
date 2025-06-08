# blueprints/api/v1/analysis.py
from flask import Blueprint, request, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, func, desc
from datetime import datetime, date
import os
import tempfile

from models import db
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats, AnalizMedya
from models.user_models import Portfolio, portfolio_arsalar, User
from ..schemas.analysis_schemas import (
    ArsaAnalizSchema, ArsaAnalizCreateSchema, ArsaAnalizUpdateSchema,
    ArsaAnalizFilterSchema, BolgeDagilimiSchema, DashboardStatsSchema,
    AnalysisReportSchema, BulkAnalysisSchema, AnalysisComparisonSchema
)
from ..utils.decorators import (
    validate_json, log_api_call, handle_db_errors,
    paginate_query, )
from ..utils.responses import (
    success_response, error_response, not_found_response,
    paginated_response
)

analysis_v1 = Blueprint('analysis_v1', __name__)


@analysis_v1.route('', methods=['GET'])
@jwt_required()
@log_api_call
def list_analyses():
    """
    Arsa analizi listesi
    ---
    tags:
      - Analysis
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
        name: search
        type: string
        description: Search in il, ilce, mahalle
    responses:
      200:
        description: Analyses retrieved successfully
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
        search = request.args.get('search', '').strip()

        # Base query
        query = ArsaAnaliz.query.filter_by(user_id=current_user.id)

        # Arama filtresi
        if search:
            from sqlalchemy import or_
            search_filter = or_(
                ArsaAnaliz.il.ilike(f'%{search}%'),
                ArsaAnaliz.ilce.ilike(f'%{search}%'),
                ArsaAnaliz.mahalle.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        # Sıralama
        query = query.order_by(ArsaAnaliz.created_at.desc())

        # Sayfalama
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Response data hazırla
        analyses_data = []
        for analysis in pagination.items:
            analysis_data = {
                'id': analysis.id,
                'il': analysis.il,
                'ilce': analysis.ilce,
                'mahalle': analysis.mahalle,
                'ada': analysis.ada,
                'parsel': analysis.parsel,
                'metrekare': float(analysis.metrekare),
                'fiyat': float(analysis.fiyat),
                'imar_durumu': analysis.imar_durumu,
                'taks': float(analysis.taks) if analysis.taks else None,
                'kaks': float(analysis.kaks) if analysis.kaks else None,
                'notlar': analysis.notlar,
                'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
                'user_id': analysis.user_id
            }
            analyses_data.append(analysis_data)

        response_data = {
            'data': analyses_data,
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
            message="Analyses retrieved successfully"
        )

    except Exception as e:
        current_app.logger.error(f"List analyses error: {str(e)}")
        return error_response("Failed to retrieve analyses", 500)


@analysis_v1.route('', methods=['POST'])
@jwt_required()
@log_api_call
def create_analysis():
    """
    Yeni arsa analizi oluştur
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - in: body
        name: analysis
        description: Analysis data
        required: true
        schema:
          type: object
          required:
            - il
            - ilce
            - mahalle
            - metrekare
            - fiyat
          properties:
            il:
              type: string
              minLength: 1
              maxLength: 50
            ilce:
              type: string
              minLength: 1
              maxLength: 50
            mahalle:
              type: string
              minLength: 1
              maxLength: 100
            ada:
              type: string
              maxLength: 20
            parsel:
              type: string
              maxLength: 20
            metrekare:
              type: number
              minimum: 1
            fiyat:
              type: number
              minimum: 0
            imar_durumu:
              type: string
              maxLength: 50
            taks:
              type: number
              minimum: 0
              maximum: 1
            kaks:
              type: number
              minimum: 0
            notlar:
              type: string
    responses:
      201:
        description: Analysis created successfully
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
        required_fields = ['il', 'ilce', 'mahalle', 'metrekare', 'fiyat']
        for field in required_fields:
            if field not in data or not data[field]:
                return error_response(f"Missing required field: {field}", 400)

        # Sayısal alan kontrolü
        try:
            metrekare = float(data['metrekare'])
            fiyat = float(data['fiyat'])
            if metrekare <= 0:
                return error_response("Metrekare must be greater than 0", 400)
            if fiyat < 0:
                return error_response("Fiyat cannot be negative", 400)
        except (ValueError, TypeError):
            return error_response("Invalid numeric values for metrekare or fiyat", 400)

        # Analiz oluştur
        analysis = ArsaAnaliz(
            user_id=current_user.id,
            office_id=current_user.office_id,
            il=data['il'],
            ilce=data['ilce'],
            mahalle=data['mahalle'],
            ada=data.get('ada'),
            parsel=data.get('parsel'),
            koordinatlar=data.get('koordinatlar'),
            pafta=data.get('pafta'),
            metrekare=metrekare,
            imar_durumu=data.get('imar_durumu'),
            taks=data.get('taks'),
            kaks=data.get('kaks'),
            fiyat=fiyat,
            notlar=data.get('notlar')
        )

        db.session.add(analysis)
        db.session.commit()

        # Dashboard istatistiklerini güncelle
        try:
            update_dashboard_stats(current_user.id)
        except Exception as e:
            current_app.logger.warning(f"Dashboard stats update failed: {str(e)}")

        # Response data hazırla
        analysis_data = {
            'id': analysis.id,
            'il': analysis.il,
            'ilce': analysis.ilce,
            'mahalle': analysis.mahalle,
            'ada': analysis.ada,
            'parsel': analysis.parsel,
            'metrekare': float(analysis.metrekare),
            'fiyat': float(analysis.fiyat),
            'imar_durumu': analysis.imar_durumu,
            'taks': float(analysis.taks) if analysis.taks else None,
            'kaks': float(analysis.kaks) if analysis.kaks else None,
            'notlar': analysis.notlar,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'user_id': analysis.user_id
        }

        current_app.logger.info(f"Analysis created: {analysis.il}/{analysis.ilce} by user {current_user.id}")
        return success_response(
            data=analysis_data,
            message="Analysis created successfully",
            status_code=201
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analysis creation error: {str(e)}")
        return error_response("Analysis creation failed", 500)


@analysis_v1.route('/<int:analysis_id>', methods=['GET'])
@jwt_required()
@log_api_call
def get_analysis(analysis_id):
    """
    Arsa analizi detayı
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - in: path
        name: analysis_id
        type: integer
        required: true
    responses:
      200:
        description: Analysis retrieved successfully
      401:
        description: Unauthorized
      404:
        description: Analysis not found
    """
    try:
        # Kullanıcı bilgisini al
        user_id = get_jwt_identity()
        from models.user_models import User
        current_user = User.query.get(user_id)

        if not current_user:
            return not_found_response("User not found")

        analysis = ArsaAnaliz.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()

        if not analysis:
            return not_found_response("Analysis not found")

        # Response data hazırla
        analysis_data = {
            'id': analysis.id,
            'il': analysis.il,
            'ilce': analysis.ilce,
            'mahalle': analysis.mahalle,
            'ada': analysis.ada,
            'parsel': analysis.parsel,
            'metrekare': float(analysis.metrekare),
            'fiyat': float(analysis.fiyat),
            'imar_durumu': analysis.imar_durumu,
            'taks': float(analysis.taks) if analysis.taks else None,
            'kaks': float(analysis.kaks) if analysis.kaks else None,
            'notlar': analysis.notlar,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'user_id': analysis.user_id
        }

        return success_response(
            data=analysis_data,
            message="Analysis retrieved successfully"
        )

    except Exception as e:
        current_app.logger.error(f"Get analysis error: {str(e)}")
        return error_response("Failed to retrieve analysis", 500)


@analysis_v1.route('/<int:analysis_id>', methods=['PUT'])
@jwt_required()
@log_api_call
def update_analysis(analysis_id):
    """
    Arsa analizini güncelle
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - in: path
        name: analysis_id
        type: integer
        required: true
      - in: body
        name: analysis
        description: Updated analysis data
        required: true
        schema:
          $ref: '#/definitions/ArsaAnalizUpdate'
    responses:
      200:
        description: Analysis updated successfully
      401:
        description: Unauthorized
      404:
        description: Analysis not found
    """
    current_user = ()
    analysis = ArsaAnaliz.query.filter_by(
        id=analysis_id,
        user_id=current_user.id
    ).first()
    
    if not analysis:
        return not_found_response("Analysis not found")
    
    # Analizi güncelle
    for field, value in data.items():
        if hasattr(analysis, field):
            setattr(analysis, field, value)
    
    analysis.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Dashboard istatistiklerini güncelle
    update_dashboard_stats(current_user.id)
    
    analysis_schema = ArsaAnalizSchema()
    analysis_data = analysis_schema.dump(analysis)
    
    current_app.logger.info(f"Analysis updated: {analysis.il}/{analysis.ilce}")
    return success_response(
        data=analysis_data,
        message="Analysis updated successfully"
    )


@analysis_v1.route('/<int:analysis_id>', methods=['DELETE'])
@jwt_required()
@log_api_call
def delete_analysis(analysis_id):
    """
    Arsa analizini sil
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - in: path
        name: analysis_id
        type: integer
        required: true
    responses:
      200:
        description: Analysis deleted successfully
      401:
        description: Unauthorized
      404:
        description: Analysis not found
    """
    current_user = ()
    analysis = ArsaAnaliz.query.filter_by(
        id=analysis_id,
        user_id=current_user.id
    ).first()
    
    if not analysis:
        return not_found_response("Analysis not found")
    
    db.session.delete(analysis)
    db.session.commit()
    
    # Dashboard istatistiklerini güncelle
    update_dashboard_stats(current_user.id)
    
    current_app.logger.info(f"Analysis deleted: {analysis.il}/{analysis.ilce}")
    return success_response(message="Analysis deleted successfully")


@analysis_v1.route('/stats', methods=['GET'])
@jwt_required()
@log_api_call
def get_analysis_stats():
    """
    Analiz istatistikleri
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    responses:
      200:
        description: Analysis statistics retrieved successfully
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

        # Basit istatistikler hesapla
        total_analyses = ArsaAnaliz.query.filter_by(user_id=current_user.id).count()

        if total_analyses == 0:
            stats_data = {
                'total_analyses': 0,
                'total_value': 0,
                'average_price_per_m2': 0,
                'regions': [],
                'recent_analyses': []
            }
        else:
            # Toplam değer hesapla
            analyses = ArsaAnaliz.query.filter_by(user_id=current_user.id).all()
            total_value = sum(float(a.fiyat or 0) for a in analyses)

            # Ortalama m2 fiyatı hesapla
            prices_per_m2 = []
            for a in analyses:
                if a.fiyat and a.metrekare and float(a.metrekare) > 0:
                    price_per_m2 = float(a.fiyat) / float(a.metrekare)
                    prices_per_m2.append(price_per_m2)

            avg_price_per_m2 = sum(prices_per_m2) / len(prices_per_m2) if prices_per_m2 else 0

            # İl bazında dağılım
            from sqlalchemy import func
            region_stats = db.session.query(
                ArsaAnaliz.il,
                func.count(ArsaAnaliz.id).label('count'),
                func.sum(ArsaAnaliz.fiyat).label('total_value')
            ).filter_by(user_id=current_user.id).group_by(ArsaAnaliz.il).all()

            regions = []
            for il, count, total_val in region_stats:
                regions.append({
                    'il': il,
                    'count': count,
                    'total_value': float(total_val or 0)
                })

            # Son 5 analiz
            recent = ArsaAnaliz.query.filter_by(user_id=current_user.id)\
                .order_by(ArsaAnaliz.created_at.desc())\
                .limit(5)\
                .all()

            recent_analyses = []
            for analysis in recent:
                recent_analyses.append({
                    'id': analysis.id,
                    'il': analysis.il,
                    'ilce': analysis.ilce,
                    'mahalle': analysis.mahalle,
                    'metrekare': float(analysis.metrekare),
                    'fiyat': float(analysis.fiyat),
                    'created_at': analysis.created_at.isoformat() if analysis.created_at else None
                })

            stats_data = {
                'total_analyses': total_analyses,
                'total_value': total_value,
                'average_price_per_m2': avg_price_per_m2,
                'regions': regions,
                'recent_analyses': recent_analyses
            }

        return success_response(
            data=stats_data,
            message="Analysis statistics retrieved successfully"
        )

    except Exception as e:
        current_app.logger.error(f"Analysis stats error: {str(e)}")
        return error_response("Failed to retrieve analysis statistics", 500)


@analysis_v1.route('/bulk', methods=['POST'])
@jwt_required()
@log_api_call
def bulk_create_analyses():
    """
    Toplu analiz oluştur
    ---
    tags:
      - Analysis
    security:
      - Bearer: []
    parameters:
      - in: body
        name: bulk_data
        description: Bulk analysis data
        required: true
        schema:
          $ref: '#/definitions/BulkAnalysis'
    responses:
      201:
        description: Analyses created successfully
      400:
        description: Validation error
      401:
        description: Unauthorized
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    analyses_data = data['analyses']
    portfolio_id = data.get('portfolio_id')
    
    # Portfolio kontrolü
    portfolio = None
    if portfolio_id:
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=current_user.id
        ).first()
        if not portfolio:
            return error_response("Portfolio not found", 404)
    
    created_analyses = []
    
    try:
        for analysis_data in analyses_data:
            analysis = ArsaAnaliz(
                user_id=current_user.id,
                **analysis_data
            )
            db.session.add(analysis)
            created_analyses.append(analysis)
        
        db.session.flush()  # ID'leri al
        
        # Portfolio'ya ekle
        if portfolio:
            for analysis in created_analyses:
                portfolio.analizler.append(analysis)
        
        db.session.commit()
        
        # Dashboard istatistiklerini güncelle
        update_dashboard_stats(current_user.id)
        
        analysis_schema = ArsaAnalizSchema(many=True)
        analyses_response = analysis_schema.dump(created_analyses)
        
        current_app.logger.info(f"Bulk analysis created: {len(created_analyses)} analyses")
        return success_response(
            data=analyses_response,
            message=f"{len(created_analyses)} analyses created successfully",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Bulk analysis creation failed: {str(e)}")
        return error_response("Bulk analysis creation failed", 500)


def update_dashboard_stats(user_id):
    """Dashboard istatistiklerini günceller."""
    try:
        # Mevcut istatistikleri hesapla
        analyses = ArsaAnaliz.query.filter_by(user_id=user_id).all()
        
        if not analyses:
            return
        
        total_count = len(analyses)
        total_value = sum(float(a.yaklasik_deger or 0) for a in analyses)
        prices = [float(a.tahmini_deger_m2 or 0) for a in analyses if a.tahmini_deger_m2]
        
        avg_price = sum(prices) / len(prices) if prices else 0
        max_price = max(prices) if prices else 0
        min_price = min(prices) if prices else 0
        
        # Dashboard stats'ı güncelle veya oluştur
        dashboard_stats = DashboardStats.query.filter_by(user_id=user_id).first()
        if not dashboard_stats:
            dashboard_stats = DashboardStats(user_id=user_id)
            db.session.add(dashboard_stats)
        
        dashboard_stats.toplam_arsa_sayisi = total_count
        dashboard_stats.ortalama_fiyat = avg_price
        dashboard_stats.en_yuksek_fiyat = max_price
        dashboard_stats.en_dusuk_fiyat = min_price
        dashboard_stats.toplam_deger = total_value
        dashboard_stats.son_guncelleme = datetime.utcnow()
        
        # Bölge dağılımını güncelle
        update_region_distribution(user_id, analyses)
        
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"Dashboard stats update failed: {str(e)}")
        db.session.rollback()


def update_region_distribution(user_id, analyses):
    """Bölge dağılımını günceller."""
    try:
        # Mevcut bölge dağılımını temizle
        BolgeDagilimi.query.filter_by(user_id=user_id).delete()
        
        # İl bazında grupla
        region_data = {}
        for analysis in analyses:
            il = analysis.il
            if il not in region_data:
                region_data[il] = {
                    'count': 0,
                    'total_value': 0
                }
            
            region_data[il]['count'] += 1
            region_data[il]['total_value'] += float(analysis.yaklasik_deger or 0)
        
        # Yeni bölge dağılımını oluştur
        for il, data in region_data.items():
            bolge = BolgeDagilimi(
                user_id=user_id,
                il=il,
                analiz_sayisi=data['count'],
                toplam_deger=data['total_value']
            )
            db.session.add(bolge)
        
    except Exception as e:
        current_app.logger.error(f"Region distribution update failed: {str(e)}")


def get_recent_analyses(user_id, limit=5):
    """Son analizleri getirir."""
    recent = ArsaAnaliz.query.filter_by(user_id=user_id)\
        .order_by(desc(ArsaAnaliz.created_at))\
        .limit(limit)\
        .all()
    
    schema = ArsaAnalizSchema(many=True)
    return schema.dump(recent)
