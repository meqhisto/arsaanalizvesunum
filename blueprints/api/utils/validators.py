# blueprints/api/utils/validators.py
import re
from marshmallow import ValidationError


def validate_email(email):
    """E-posta adresini doğrular."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")


def validate_phone(phone):
    """Telefon numarasını doğrular."""
    if phone:
        # Türkiye telefon numarası formatı
        pattern = r'^(\+90|0)?[5][0-9]{9}$'
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(pattern, cleaned_phone):
            raise ValidationError("Invalid phone number format")


def validate_password_strength(password):
    """Parola gücünü doğrular."""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit")


def validate_coordinates(coordinates):
    """Koordinatları doğrular."""
    if coordinates:
        # Latitude,Longitude formatı
        pattern = r'^-?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*-?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$'
        if not re.match(pattern, coordinates):
            raise ValidationError("Invalid coordinates format. Use 'latitude,longitude'")


def validate_positive_number(value):
    """Pozitif sayı doğrular."""
    if value is not None and value <= 0:
        raise ValidationError("Value must be positive")


def validate_percentage(value):
    """Yüzde değerini doğrular (0-100 arası)."""
    if value is not None and (value < 0 or value > 100):
        raise ValidationError("Percentage must be between 0 and 100")


def validate_file_extension(filename, allowed_extensions):
    """Dosya uzantısını doğrular."""
    if filename:
        extension = filename.rsplit('.', 1)[-1].lower()
        if extension not in allowed_extensions:
            raise ValidationError(f"File extension must be one of: {', '.join(allowed_extensions)}")


def validate_turkish_id(tc_no):
    """TC Kimlik numarasını doğrular."""
    if tc_no:
        if not tc_no.isdigit() or len(tc_no) != 11:
            raise ValidationError("TC ID must be 11 digits")
        
        # TC Kimlik numarası algoritması
        digits = [int(d) for d in tc_no]
        
        # İlk 10 haneden 10. haneyi kontrol et
        odd_sum = sum(digits[i] for i in range(0, 9, 2))
        even_sum = sum(digits[i] for i in range(1, 8, 2))
        
        if (odd_sum * 7 - even_sum) % 10 != digits[9]:
            raise ValidationError("Invalid TC ID number")
        
        # Tüm hanelerin toplamından 11. haneyi kontrol et
        if sum(digits[:10]) % 10 != digits[10]:
            raise ValidationError("Invalid TC ID number")


def validate_iban(iban):
    """IBAN numarasını doğrular."""
    if iban:
        # Türkiye IBAN formatı: TR + 2 kontrol hanesi + 5 banka kodu + 1 rezerv + 16 hesap numarası
        pattern = r'^TR\d{24}$'
        if not re.match(pattern, iban.replace(' ', '')):
            raise ValidationError("Invalid IBAN format for Turkey")


def validate_date_range(start_date, end_date):
    """Tarih aralığını doğrular."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError("Start date cannot be after end date")


def validate_price_range(min_price, max_price):
    """Fiyat aralığını doğrular."""
    if min_price is not None and max_price is not None:
        if min_price < 0:
            raise ValidationError("Minimum price cannot be negative")
        if max_price < 0:
            raise ValidationError("Maximum price cannot be negative")
        if min_price > max_price:
            raise ValidationError("Minimum price cannot be greater than maximum price")


def validate_area_range(min_area, max_area):
    """Alan aralığını doğrular."""
    if min_area is not None and max_area is not None:
        if min_area <= 0:
            raise ValidationError("Minimum area must be positive")
        if max_area <= 0:
            raise ValidationError("Maximum area must be positive")
        if min_area > max_area:
            raise ValidationError("Minimum area cannot be greater than maximum area")
