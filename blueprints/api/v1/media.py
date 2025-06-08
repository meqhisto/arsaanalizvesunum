# blueprints/api/v1/media.py
from flask import Blueprint, request, current_app, send_file, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import uuid
from datetime import datetime
import mimetypes

from models import db
from models.arsa_models import AnalizMedya
from ..schemas.analysis_schemas import AnalizMedyaSchema
from ..utils.decorators import (
    log_api_call, handle_db_errors, )
from ..utils.responses import (
    success_response, error_response, not_found_response
)

media_v1 = Blueprint('media_v1', __name__)

# İzin verilen dosya uzantıları
ALLOWED_EXTENSIONS = {
    'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
    'documents': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'},
    'archives': {'zip', 'rar', '7z', 'tar', 'gz'},
    'cad': {'dwg', 'dxf', 'dwf'}
}

ALL_ALLOWED_EXTENSIONS = set()
for extensions in ALLOWED_EXTENSIONS.values():
    ALL_ALLOWED_EXTENSIONS.update(extensions)

# Maksimum dosya boyutları (bytes)
MAX_FILE_SIZES = {
    'images': 10 * 1024 * 1024,  # 10MB
    'documents': 50 * 1024 * 1024,  # 50MB
    'archives': 100 * 1024 * 1024,  # 100MB
    'cad': 50 * 1024 * 1024  # 50MB
}


def allowed_file(filename):
    """Dosya uzantısının izin verilen uzantılar arasında olup olmadığını kontrol eder."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALL_ALLOWED_EXTENSIONS


def get_file_category(filename):
    """Dosya kategorisini belirler."""
    if not filename or '.' not in filename:
        return None
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if extension in extensions:
            return category
    
    return None


def get_max_file_size(category):
    """Kategori için maksimum dosya boyutunu döner."""
    return MAX_FILE_SIZES.get(category, 10 * 1024 * 1024)  # Varsayılan 10MB


@media_v1.route('/upload', methods=['POST'])
@()
@log_api_call
@handle_db_errors
def upload_file():
    """
    Dosya yükle
    ---
    tags:
      - Media
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: File to upload
      - in: formData
        name: analysis_id
        type: integer
        description: Analysis ID to associate with the file
      - in: formData
        name: description
        type: string
        description: File description
    responses:
      201:
        description: File uploaded successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/AnalizMedya'
      400:
        description: No file provided or invalid file
      401:
        description: Unauthorized
      413:
        description: File too large
    """
    current_user = ()
    if not current_user:
        return not_found_response("User not found")
    
    # Dosya kontrolü
    if 'file' not in request.files:
        return error_response("No file provided", 400)
    
    file = request.files['file']
    if file.filename == '':
        return error_response("No file selected", 400)
    
    if not allowed_file(file.filename):
        return error_response(
            f"File type not allowed. Allowed types: {', '.join(ALL_ALLOWED_EXTENSIONS)}", 
            400
        )
    
    # Dosya kategorisi ve boyut kontrolü
    category = get_file_category(file.filename)
    max_size = get_max_file_size(category)
    
    # Dosya boyutunu kontrol et (Content-Length header'dan)
    content_length = request.content_length
    if content_length and content_length > max_size:
        return error_response(f"File too large. Maximum size: {max_size // (1024*1024)}MB", 413)
    
    # Form verileri
    analysis_id = request.form.get('analysis_id', type=int)
    description = request.form.get('description', '').strip()
    
    # Analysis kontrolü (eğer belirtilmişse)
    if analysis_id:
        from models.arsa_models import ArsaAnaliz
        analysis = ArsaAnaliz.query.filter_by(
            id=analysis_id,
            user_id=current_user.id
        ).first()
        if not analysis:
            return error_response("Analysis not found", 404)
    
    try:
        # Güvenli dosya adı oluştur
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Upload klasörünü oluştur
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Dosyayı kaydet
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Dosya boyutunu al
        file_size = os.path.getsize(file_path)
        
        # MIME type'ı belirle
        mime_type, _ = mimetypes.guess_type(original_filename)
        
        # Veritabanına kaydet
        media = AnalizMedya(
            analiz_id=analysis_id,
            dosya_adi=original_filename,
            dosya_yolu=unique_filename,
            dosya_tipi=mime_type or 'application/octet-stream',
            dosya_boyutu=file_size,
            aciklama=description
        )
        
        db.session.add(media)
        db.session.commit()
        
        # Response oluştur
        media_schema = AnalizMedyaSchema()
        media_data = media_schema.dump(media)
        
        current_app.logger.info(f"File uploaded: {original_filename} by user {current_user.id}")
        return success_response(
            data=media_data,
            message="File uploaded successfully",
            status_code=201
        )
        
    except RequestEntityTooLarge:
        return error_response("File too large", 413)
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        # Hata durumunda dosyayı sil
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        return error_response("File upload failed", 500)


@media_v1.route('/<int:media_id>', methods=['GET'])
@()
@log_api_call
def download_file(media_id):
    """
    Dosya indir
    ---
    tags:
      - Media
    security:
      - Bearer: []
    parameters:
      - in: path
        name: media_id
        type: integer
        required: true
        description: Media ID
    responses:
      200:
        description: File downloaded successfully
      401:
        description: Unauthorized
      404:
        description: File not found
    """
    current_user = ()
    
    # Media kaydını bul
    media = AnalizMedya.query.get(media_id)
    if not media:
        return not_found_response("File not found")
    
    # Analiz sahibi kontrolü (eğer analiz ile ilişkiliyse)
    if media.analiz_id:
        from models.arsa_models import ArsaAnaliz
        analysis = ArsaAnaliz.query.filter_by(
            id=media.analiz_id,
            user_id=current_user.id
        ).first()
        if not analysis:
            return not_found_response("File not found")
    
    # Dosya yolu
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    file_path = os.path.join(upload_folder, media.dosya_yolu)
    
    if not os.path.exists(file_path):
        return not_found_response("File not found on disk")
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=media.dosya_adi,
            mimetype=media.dosya_tipi
        )
    except Exception as e:
        current_app.logger.error(f"File download error: {str(e)}")
        return error_response("File download failed", 500)


@media_v1.route('/<int:media_id>/info', methods=['GET'])
@()
@log_api_call
def get_file_info(media_id):
    """
    Dosya bilgileri
    ---
    tags:
      - Media
    security:
      - Bearer: []
    parameters:
      - in: path
        name: media_id
        type: integer
        required: true
        description: Media ID
    responses:
      200:
        description: File info retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              $ref: '#/definitions/AnalizMedya'
      401:
        description: Unauthorized
      404:
        description: File not found
    """
    current_user = ()
    
    # Media kaydını bul
    media = AnalizMedya.query.get(media_id)
    if not media:
        return not_found_response("File not found")
    
    # Analiz sahibi kontrolü (eğer analiz ile ilişkiliyse)
    if media.analiz_id:
        from models.arsa_models import ArsaAnaliz
        analysis = ArsaAnaliz.query.filter_by(
            id=media.analiz_id,
            user_id=current_user.id
        ).first()
        if not analysis:
            return not_found_response("File not found")
    
    media_schema = AnalizMedyaSchema()
    media_data = media_schema.dump(media)
    
    return success_response(
        data=media_data,
        message="File info retrieved successfully"
    )


@media_v1.route('/<int:media_id>', methods=['DELETE'])
@()
@log_api_call
@handle_db_errors
def delete_file(media_id):
    """
    Dosya sil
    ---
    tags:
      - Media
    security:
      - Bearer: []
    parameters:
      - in: path
        name: media_id
        type: integer
        required: true
        description: Media ID
    responses:
      200:
        description: File deleted successfully
      401:
        description: Unauthorized
      404:
        description: File not found
    """
    current_user = ()
    
    # Media kaydını bul
    media = AnalizMedya.query.get(media_id)
    if not media:
        return not_found_response("File not found")
    
    # Analiz sahibi kontrolü (eğer analiz ile ilişkiliyse)
    if media.analiz_id:
        from models.arsa_models import ArsaAnaliz
        analysis = ArsaAnaliz.query.filter_by(
            id=media.analiz_id,
            user_id=current_user.id
        ).first()
        if not analysis:
            return not_found_response("File not found")
    
    # Fiziksel dosyayı sil
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    file_path = os.path.join(upload_folder, media.dosya_yolu)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.warning(f"Could not delete physical file: {str(e)}")
    
    # Veritabanından sil
    db.session.delete(media)
    db.session.commit()
    
    current_app.logger.info(f"File deleted: {media.dosya_adi} by user {current_user.id}")
    return success_response(message="File deleted successfully")


@media_v1.route('/analysis/<int:analysis_id>', methods=['GET'])
@()
@log_api_call
def list_analysis_files(analysis_id):
    """
    Analiz dosyaları listesi
    ---
    tags:
      - Media
    security:
      - Bearer: []
    parameters:
      - in: path
        name: analysis_id
        type: integer
        required: true
        description: Analysis ID
    responses:
      200:
        description: Analysis files retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: array
              items:
                $ref: '#/definitions/AnalizMedya'
      401:
        description: Unauthorized
      404:
        description: Analysis not found
    """
    current_user = ()
    
    # Analiz kontrolü
    from models.arsa_models import ArsaAnaliz
    analysis = ArsaAnaliz.query.filter_by(
        id=analysis_id,
        user_id=current_user.id
    ).first()
    
    if not analysis:
        return not_found_response("Analysis not found")
    
    # Analiz dosyalarını getir
    media_files = AnalizMedya.query.filter_by(analiz_id=analysis_id).all()
    
    media_schema = AnalizMedyaSchema(many=True)
    media_data = media_schema.dump(media_files)
    
    return success_response(
        data=media_data,
        message="Analysis files retrieved successfully"
    )


@media_v1.route('/stats', methods=['GET'])
@()
@log_api_call
def get_media_stats():
    """
    Medya istatistikleri
    ---
    tags:
      - Media
    security:
      - Bearer: []
    responses:
      200:
        description: Media statistics retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: object
              properties:
                total_files:
                  type: integer
                total_size:
                  type: integer
                file_types:
                  type: object
      401:
        description: Unauthorized
    """
    current_user = ()
    
    # Kullanıcının analizlerine ait dosyaları bul
    from models.arsa_models import ArsaAnaliz
    user_analysis_ids = db.session.query(ArsaAnaliz.id).filter_by(user_id=current_user.id).subquery()
    
    media_files = AnalizMedya.query.filter(
        AnalizMedya.analiz_id.in_(user_analysis_ids)
    ).all()
    
    # İstatistikleri hesapla
    total_files = len(media_files)
    total_size = sum(media.dosya_boyutu or 0 for media in media_files)
    
    # Dosya türü dağılımı
    file_types = {}
    for media in media_files:
        file_type = media.dosya_tipi or 'unknown'
        file_types[file_type] = file_types.get(file_type, 0) + 1
    
    stats = {
        'total_files': total_files,
        'total_size': total_size,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'file_types': file_types,
        'allowed_extensions': list(ALL_ALLOWED_EXTENSIONS),
        'max_file_sizes': {k: f"{v // (1024*1024)}MB" for k, v in MAX_FILE_SIZES.items()}
    }
    
    return success_response(
        data=stats,
        message="Media statistics retrieved successfully"
    )
