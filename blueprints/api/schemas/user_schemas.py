# blueprints/api/schemas/user_schemas.py
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.user_models import User, Portfolio
from models import db
from ..utils.validators import (
    validate_email, validate_phone, validate_password_strength
)


class UserRegistrationSchema(Schema):
    """Kullanıcı kayıt şeması."""
    email = fields.Email(required=True, validate=validate_email)
    password = fields.Str(required=True, validate=validate_password_strength)
    ad = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    soyad = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    telefon = fields.Str(allow_none=True, validate=validate_phone)
    firma = fields.Str(allow_none=True, validate=validate.Length(max=100))
    unvan = fields.Str(allow_none=True, validate=validate.Length(max=100))
    adres = fields.Str(allow_none=True)
    
    @validates('email')
    def validate_email_unique(self, value):
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists')


class UserLoginSchema(Schema):
    """Kullanıcı giriş şeması."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(load_default=False)


class UserUpdateSchema(Schema):
    """Kullanıcı güncelleme şeması."""
    ad = fields.Str(validate=validate.Length(min=2, max=50))
    soyad = fields.Str(validate=validate.Length(min=2, max=50))
    telefon = fields.Str(allow_none=True, validate=validate_phone)
    firma = fields.Str(allow_none=True, validate=validate.Length(max=100))
    unvan = fields.Str(allow_none=True, validate=validate.Length(max=100))
    adres = fields.Str(allow_none=True)
    timezone = fields.Str(validate=validate.Length(max=50))


class PasswordChangeSchema(Schema):
    """Parola değiştirme şeması."""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate_password_strength)
    confirm_password = fields.Str(required=True)
    
    # Password validation will be handled in the endpoint


class PasswordResetRequestSchema(Schema):
    """Parola sıfırlama isteği şeması."""
    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    """Parola sıfırlama şeması."""
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate_password_strength)
    confirm_password = fields.Str(required=True)
    
    # Password validation will be handled in the endpoint


class UserSchema(SQLAlchemyAutoSchema):
    """Kullanıcı çıktı şeması."""
    class Meta:
        model = User
        sqla_session = db.session
        load_instance = True
        exclude = ('password_hash', 'reset_token', 'failed_attempts')
    
    # Hassas bilgileri gizle
    password_hash = fields.Str(dump_only=True)
    reset_token = fields.Str(dump_only=True)
    failed_attempts = fields.Int(dump_only=True)
    
    # Computed fields
    full_name = fields.Method("get_full_name")
    is_active = fields.Method("get_is_active")
    
    def get_full_name(self, obj):
        return f"{obj.ad or ''} {obj.soyad or ''}".strip()
    
    def get_is_active(self, obj):
        return obj.is_active


class UserListSchema(Schema):
    """Kullanıcı listesi şeması."""
    id = fields.Int()
    email = fields.Email()
    ad = fields.Str()
    soyad = fields.Str()
    firma = fields.Str()
    role = fields.Str()
    is_active = fields.Method("get_is_active")
    registered_on = fields.DateTime()
    son_giris = fields.DateTime()
    
    def get_is_active(self, obj):
        return obj.is_active


class PortfolioSchema(SQLAlchemyAutoSchema):
    """Portfolio şeması."""
    class Meta:
        model = Portfolio
        sqla_session = db.session
        load_instance = True
        include_fk = True
    
    # Computed fields
    arsa_count = fields.Method("get_arsa_count")
    
    def get_arsa_count(self, obj):
        return obj.analizler.count() if obj.analizler else 0


class PortfolioCreateSchema(Schema):
    """Portfolio oluşturma şeması."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    visibility = fields.Str(
        validate=validate.OneOf(['public', 'private']),
        load_default='public'
    )


class PortfolioUpdateSchema(Schema):
    """Portfolio güncelleme şeması."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    visibility = fields.Str(validate=validate.OneOf(['public', 'private']))


class TokenResponseSchema(Schema):
    """Token yanıt şeması."""
    access_token = fields.Str()
    refresh_token = fields.Str()
    expires_in = fields.Int()
    token_type = fields.Str(load_default="Bearer")
    user = fields.Nested(UserSchema)


class RefreshTokenSchema(Schema):
    """Token yenileme şeması."""
    refresh_token = fields.Str(required=True)
