from flask import Markup
from app import app

@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if not value:
        return ""
    
    # Önce HTML'den kaçış yapılmış bir değere dönüştür
    value = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Sonra yeni satırları <br> tag'lerine dönüştür
    return Markup(value.replace("\n", "<br>"))
