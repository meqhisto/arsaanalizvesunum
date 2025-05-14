from flask import session, g
from app import app, User

# Tüm şablonlara otomatik olarak current_user değişkenini aktaran bir middleware
@app.before_request
def inject_current_user():
    """Her istek için current_user değişkenini g nesnesine ekler"""
    if 'user_id' in session:
        user_id = session['user_id']
        g.current_user = User.query.get(user_id)
    else:
        g.current_user = None

# Tüm şablonlara otomatik olarak current_user değişkenini aktaran context processor
@app.context_processor
def inject_global_template_variables():
    """Tüm şablonlara bazı global değişkenleri aktarır"""
    return {
        'current_user': getattr(g, 'current_user', None)
    }
