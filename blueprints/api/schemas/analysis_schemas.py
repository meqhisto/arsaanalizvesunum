# blueprints/api/schemas/analysis_schemas.py
from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats, AnalizMedya
from models import db
from ..utils.validators import (
    validate_coordinates, validate_positive_number, validate_percentage,
    validate_price_range, validate_area_range
)


class ArsaAnalizSchema(SQLAlchemyAutoSchema):
    """Arsa analizi şeması."""
    class Meta:
        model = ArsaAnaliz
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    total_value = fields.Method("get_total_value")
    price_per_sqm = fields.Method("get_price_per_sqm")
    roi_percentage = fields.Method("get_roi_percentage")
    
    def get_total_value(self, obj):
        if obj.metrekare and obj.tahmini_deger_m2:
            return float(obj.metrekare * obj.tahmini_deger_m2)
        return None
    
    def get_price_per_sqm(self, obj):
        return float(obj.tahmini_deger_m2) if obj.tahmini_deger_m2 else None
    
    def get_roi_percentage(self, obj):
        return float(obj.yatirim_getirisi) if obj.yatirim_getirisi else None


class ArsaAnalizCreateSchema(Schema):
    """Arsa analizi oluşturma şeması."""
    il = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    ilce = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    mahalle = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    ada = fields.Str(allow_none=True, validate=validate.Length(max=20))
    parsel = fields.Str(allow_none=True, validate=validate.Length(max=20))
    koordinatlar = fields.Str(allow_none=True, validate=validate_coordinates)
    pafta = fields.Str(allow_none=True, validate=validate.Length(max=50))
    metrekare = fields.Decimal(required=True, places=2, validate=validate_positive_number)
    imar_durumu = fields.Str(allow_none=True, validate=validate.Length(max=50))
    taks = fields.Decimal(allow_none=True, places=2, validate=validate_percentage)
    kaks = fields.Decimal(allow_none=True, places=2, validate=validate_positive_number)
    yaklasik_deger = fields.Decimal(allow_none=True, places=2, validate=validate_positive_number)
    tahmini_deger_m2 = fields.Decimal(allow_none=True, places=2, validate=validate_positive_number)
    yatirim_getirisi = fields.Decimal(allow_none=True, places=2)
    risk_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    notlar = fields.Str(allow_none=True)
    
    # Analiz parametreleri
    konum_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    ulasim_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    cevre_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    gelecek_potansiyeli = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))


class ArsaAnalizUpdateSchema(Schema):
    """Arsa analizi güncelleme şeması."""
    il = fields.Str(validate=validate.Length(min=1, max=50))
    ilce = fields.Str(validate=validate.Length(min=1, max=50))
    mahalle = fields.Str(validate=validate.Length(min=1, max=100))
    ada = fields.Str(allow_none=True, validate=validate.Length(max=20))
    parsel = fields.Str(allow_none=True, validate=validate.Length(max=20))
    koordinatlar = fields.Str(allow_none=True, validate=validate_coordinates)
    pafta = fields.Str(allow_none=True, validate=validate.Length(max=50))
    metrekare = fields.Decimal(places=2, validate=validate_positive_number)
    imar_durumu = fields.Str(allow_none=True, validate=validate.Length(max=50))
    taks = fields.Decimal(allow_none=True, places=2, validate=validate_percentage)
    kaks = fields.Decimal(allow_none=True, places=2, validate=validate_positive_number)
    yaklasik_deger = fields.Decimal(allow_none=True, places=2, validate=validate_positive_number)
    tahmini_deger_m2 = fields.Decimal(allow_none=True, places=2, validate=validate_positive_number)
    yatirim_getirisi = fields.Decimal(allow_none=True, places=2)
    risk_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    notlar = fields.Str(allow_none=True)
    
    # Analiz parametreleri
    konum_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    ulasim_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    cevre_skoru = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    gelecek_potansiyeli = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))


class ArsaAnalizFilterSchema(Schema):
    """Arsa analizi filtreleme şeması."""
    il = fields.Str(allow_none=True)
    ilce = fields.Str(allow_none=True)
    mahalle = fields.Str(allow_none=True)
    imar_durumu = fields.Str(allow_none=True)
    
    # Fiyat aralığı
    min_price = fields.Decimal(allow_none=True, places=2)
    max_price = fields.Decimal(allow_none=True, places=2)
    
    # Alan aralığı
    min_area = fields.Decimal(allow_none=True, places=2)
    max_area = fields.Decimal(allow_none=True, places=2)
    
    # Risk skoru aralığı
    min_risk = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    max_risk = fields.Int(allow_none=True, validate=validate.Range(min=1, max=10))
    
    # Tarih aralığı
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    
    # Sıralama
    sort_by = fields.Str(
        allow_none=True,
        validate=validate.OneOf([
            'created_at', 'metrekare', 'tahmini_deger_m2', 
            'yaklasik_deger', 'yatirim_getirisi', 'risk_skoru'
        ])
    )
    sort_order = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['asc', 'desc']),
        load_default='desc'
    )
    
    # Validation will be handled in the endpoint


class BolgeDagilimiSchema(SQLAlchemyAutoSchema):
    """Bölge dağılımı şeması."""
    class Meta:
        model = BolgeDagilimi
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    average_value = fields.Method("get_average_value")
    
    def get_average_value(self, obj):
        if obj.analiz_sayisi and obj.analiz_sayisi > 0 and obj.toplam_deger:
            return float(obj.toplam_deger / obj.analiz_sayisi)
        return 0


class DashboardStatsSchema(SQLAlchemyAutoSchema):
    """Dashboard istatistikleri şeması."""
    class Meta:
        model = DashboardStats
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    average_price_formatted = fields.Method("get_average_price_formatted")
    total_value_formatted = fields.Method("get_total_value_formatted")
    
    def get_average_price_formatted(self, obj):
        if obj.ortalama_fiyat:
            return f"{obj.ortalama_fiyat:,.2f} ₺"
        return "0 ₺"
    
    def get_total_value_formatted(self, obj):
        if obj.toplam_deger:
            return f"{float(obj.toplam_deger):,.2f} ₺"
        return "0 ₺"


class AnalizMedyaSchema(SQLAlchemyAutoSchema):
    """Analiz medya şeması."""
    class Meta:
        model = AnalizMedya
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    file_url = fields.Method("get_file_url")
    file_size_formatted = fields.Method("get_file_size_formatted")
    
    def get_file_url(self, obj):
        if obj.dosya_yolu:
            return f"/static/uploads/{obj.dosya_yolu}"
        return None
    
    def get_file_size_formatted(self, obj):
        if obj.dosya_boyutu:
            # Bytes to MB conversion
            size_mb = obj.dosya_boyutu / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        return "Unknown"


class AnalysisReportSchema(Schema):
    """Analiz raporu şeması."""
    analysis_id = fields.Int(required=True)
    report_type = fields.Str(
        required=True,
        validate=validate.OneOf(['pdf', 'docx', 'pptx'])
    )
    include_charts = fields.Bool(load_default=True)
    include_maps = fields.Bool(load_default=True)
    include_comparisons = fields.Bool(load_default=True)
    template = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['standard', 'detailed', 'summary'])
    )


class BulkAnalysisSchema(Schema):
    """Toplu analiz şeması."""
    analyses = fields.List(fields.Nested(ArsaAnalizCreateSchema), required=True)
    portfolio_id = fields.Int(allow_none=True)
    
    @validates('analyses')
    def validate_analyses_count(self, value):
        if len(value) > 100:
            raise ValidationError("Maximum 100 analyses can be created at once")
        if len(value) == 0:
            raise ValidationError("At least one analysis is required")


class AnalysisComparisonSchema(Schema):
    """Analiz karşılaştırma şeması."""
    analysis_ids = fields.List(fields.Int(), required=True)
    comparison_type = fields.Str(
        required=True,
        validate=validate.OneOf(['price', 'roi', 'risk', 'location', 'all'])
    )
    
    @validates('analysis_ids')
    def validate_analysis_ids_count(self, value):
        if len(value) < 2:
            raise ValidationError("At least 2 analyses are required for comparison")
        if len(value) > 10:
            raise ValidationError("Maximum 10 analyses can be compared at once")
