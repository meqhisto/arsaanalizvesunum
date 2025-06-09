# utils/avatar_utils.py
import hashlib
import os
import time
from urllib.parse import urlencode
from flask import url_for, current_app
from PIL import Image, ImageDraw, ImageFont
import io
import base64


def get_avatar_url(user, size=40):
    """
    Kullanıcı için avatar URL'i döndürür.
    Önce profil fotoğrafını kontrol eder, yoksa Gravatar veya default avatar kullanır.
    """
    # Profil fotoğrafı varsa onu kullan
    if user.profil_foto and os.path.exists(os.path.join(current_app.static_folder, 'uploads', 'avatars', user.profil_foto)):
        return url_for('static', filename=f'uploads/avatars/{user.profil_foto}')
    
    # Gravatar'ı dene
    if user.email:
        gravatar_url = get_gravatar_url(user.email, size)
        return gravatar_url
    
    # Default avatar
    return generate_default_avatar_url(user, size)


def get_gravatar_url(email, size=40, default='identicon'):
    """
    Email için Gravatar URL'i oluşturur.
    """
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    params = urlencode({
        's': str(size),
        'd': default,
        'r': 'g'  # rating: g, pg, r, x
    })
    return f"https://www.gravatar.com/avatar/{email_hash}?{params}"


def generate_default_avatar_url(user, size=40):
    """
    Kullanıcı için default avatar URL'i oluşturur.
    İlk harfleri kullanarak avatar oluşturur.
    """
    # İlk harfleri al
    initials = get_user_initials(user)
    
    # Color based on user ID
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ]
    color = colors[user.id % len(colors)]
    
    # Generate data URL for SVG avatar
    svg_avatar = generate_svg_avatar(initials, color, size)
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_avatar.encode()).decode()}"


def get_user_initials(user):
    """
    Kullanıcının baş harflerini döndürür.
    """
    initials = ""
    
    if user.ad:
        initials += user.ad[0].upper()
    
    if user.soyad:
        initials += user.soyad[0].upper()
    
    if not initials and user.email:
        initials = user.email[0].upper()
    
    return initials or "?"


def generate_svg_avatar(initials, color, size=40):
    """
    SVG avatar oluşturur.
    """
    font_size = size // 2.5
    
    svg = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="{size//2}" cy="{size//2}" r="{size//2}" fill="{color}"/>
        <text x="{size//2}" y="{size//2 + font_size//3}" 
              text-anchor="middle" 
              font-family="Arial, sans-serif" 
              font-size="{font_size}" 
              font-weight="bold" 
              fill="white">
            {initials}
        </text>
    </svg>
    """
    return svg.strip()


def get_contact_avatar_url(contact, size=40):
    """
    CRM Contact için avatar URL'i döndürür.
    """
    # Contact'ın email'i varsa Gravatar'ı dene
    if contact.email:
        return get_gravatar_url(contact.email, size, default='identicon')
    
    # Default contact avatar
    initials = ""
    if contact.first_name:
        initials += contact.first_name[0].upper()
    if contact.last_name:
        initials += contact.last_name[0].upper()
    
    if not initials:
        initials = "?"
    
    # Contact için farklı renk paleti
    colors = [
        '#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6',
        '#1ABC9C', '#E67E22', '#34495E', '#16A085', '#27AE60'
    ]
    color = colors[contact.id % len(colors)]
    
    svg_avatar = generate_svg_avatar(initials, color, size)
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_avatar.encode()).decode()}"


def save_uploaded_avatar(user, file):
    """
    Yüklenen avatar dosyasını kaydeder ve kullanıcının profil_foto field'ını günceller.
    """
    if not file or not file.filename:
        return False, "Dosya seçilmedi"
    
    # Dosya uzantısını kontrol et
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return False, "Desteklenen formatlar: PNG, JPG, JPEG, GIF"
    
    # Dosya boyutunu kontrol et (max 5MB)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        return False, "Dosya boyutu 5MB'dan küçük olmalıdır"
    
    try:
        # Upload klasörünü oluştur
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Dosya adını oluştur
        filename = f"user_{user.id}_{int(time.time())}.{file_ext}"
        filepath = os.path.join(upload_dir, filename)
        
        # Resmi yeniden boyutlandır ve kaydet
        image = Image.open(file)
        
        # RGBA'ya çevir (transparency için)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Kare yapmak için crop et
        width, height = image.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        image = image.crop((left, top, left + size, top + size))
        
        # 200x200'e yeniden boyutlandır
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        
        # PNG olarak kaydet
        image.save(filepath, 'PNG', optimize=True)
        
        # Eski avatar dosyasını sil
        if user.profil_foto:
            old_filepath = os.path.join(upload_dir, user.profil_foto)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        
        # Veritabanını güncelle
        user.profil_foto = filename
        
        return True, filename
        
    except Exception as e:
        return False, f"Dosya kaydedilirken hata oluştu: {str(e)}"


def delete_user_avatar(user):
    """
    Kullanıcının avatar dosyasını siler.
    """
    if not user.profil_foto:
        return True, "Silinecek avatar yok"
    
    try:
        filepath = os.path.join(current_app.static_folder, 'uploads', 'avatars', user.profil_foto)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        user.profil_foto = None
        return True, "Avatar başarıyla silindi"
        
    except Exception as e:
        return False, f"Avatar silinirken hata oluştu: {str(e)}"
