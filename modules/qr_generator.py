import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

class QRGenerator:
    def __init__(self, base_url="https://invecoproje.com/analiz/"):
        self.base_url = base_url
        
    def generate_qr(self, analiz_id, box_size=10, border=4):
        """QR kod oluşturur ve BytesIO olarak döner"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        url = f"{self.base_url}{analiz_id}"
        qr.add_data(url)
        qr.make(fit=True)
        
        # QR kodu resim olarak oluştur
        img = qr.make_image(fill_color="black", back_color="white")
        
        # BytesIO ile bellekte tut
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer

    def generate_qr_with_logo(self, analiz_id, logo_path=None):
        """Logo eklenmiş QR kod oluşturur"""
        qr_buffer = self.generate_qr(analiz_id, box_size=15)
        qr_image = Image.open(qr_buffer)
        
        if logo_path and os.path.exists(logo_path):
            try:
                # Logo'yu yükle ve boyutlandır
                logo = Image.open(logo_path)
                logo_size = qr_image.size[0] // 4  # QR kodun 1/4'ü kadar
                logo = logo.resize((logo_size, logo_size))
                
                # Logo'yu QR kodun ortasına yerleştir
                pos = ((qr_image.size[0] - logo.size[0]) // 2,
                      (qr_image.size[1] - logo.size[1]) // 2)
                qr_image.paste(logo, pos)
            except Exception as e:
                print(f"Logo eklenirken hata: {e}")
        
        # Sonucu BytesIO'ya kaydet
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer

    def generate_qr_with_text(self, analiz_id, alt_text="Bu raporu çevrimiçi görüntülemek için QR kodu tarayın"):
        """Alt yazılı QR kod oluşturur"""
        qr_buffer = self.generate_qr(analiz_id)
        qr_image = Image.open(qr_buffer)
        
        # Alt yazı için ek alan ekle
        padding = 40
        new_img = Image.new('RGB', 
                          (qr_image.size[0], qr_image.size[1] + padding),
                          'white')
        new_img.paste(qr_image, (0, 0))
        
        # Alt yazıyı ekle
        try:
            draw = ImageDraw.Draw(new_img)
            # Varsayılan font kullan (özel font gerekirse değiştirilebilir)
            font_size = 12
            draw.text((new_img.size[0]/2, qr_image.size[1] + padding/2),
                     alt_text,
                     fill='black',
                     anchor="mm")  # Ortalı yerleştir
        except Exception as e:
            print(f"Alt yazı eklenirken hata: {e}")
        
        # Sonucu BytesIO'ya kaydet
        buffer = BytesIO()
        new_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
