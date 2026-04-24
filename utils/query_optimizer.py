"""
Query optimization utilities for improved database performance
"""

from sqlalchemy.orm import joinedload, selectinload, subqueryload
from models import db
from models.user_models import User
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact, Deal, Task
from models.office_models import Office


class QueryOptimizer:
    """Optimized database queries to prevent N+1 problems"""
    
    @staticmethod
    def get_user_with_office(user_id):
        """Get user with office information in single query"""
        return User.query.options(
            joinedload(User.office)
        ).filter_by(id=user_id).first()
    
    @staticmethod
    def get_analyses_with_user_and_office(user_id=None, limit=None):
        """Get analyses with user and office information"""
        query = ArsaAnaliz.query.options(
            joinedload(ArsaAnaliz.user).joinedload(User.office),
            selectinload(ArsaAnaliz.medyalar)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        query = query.order_by(ArsaAnaliz.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_contacts_with_relationships(user_id=None, office_id=None, limit=None):
        """Get contacts with user, office, and related data"""
        query = Contact.query.options(
            joinedload(Contact.user).joinedload(User.office),
            selectinload(Contact.deals),
            selectinload(Contact.tasks)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif office_id:
            query = query.filter_by(office_id=office_id)
        
        query = query.order_by(Contact.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_deals_with_relationships(user_id=None, office_id=None, limit=None):
        """Get deals with contact, user, and office information"""
        query = Deal.query.options(
            joinedload(Deal.contact),
            joinedload(Deal.user).joinedload(User.office),
            selectinload(Deal.interactions)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif office_id:
            query = query.filter_by(office_id=office_id)
        
        query = query.order_by(Deal.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_tasks_with_relationships(user_id=None, office_id=None, status=None, limit=None):
        """Get tasks with contact, user, and office information"""
        query = Task.query.options(
            joinedload(Task.contact),
            joinedload(Task.user).joinedload(User.office)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif office_id:
            # Tasks for office users
            query = query.join(User).filter(User.office_id == office_id)
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(Task.due_date.asc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_office_users_with_stats(office_id):
        """Get office users with their statistics using efficient subqueries"""
        from sqlalchemy import func, select

        # Correlated scalar subqueries to prevent Cartesian product when joining multiple one-to-many relationships
        analysis_subq = select(func.count(ArsaAnaliz.id)).where(
            ArsaAnaliz.user_id == User.id
        ).correlate(User).scalar_subquery()

        contact_subq = select(func.count(Contact.id)).where(
            Contact.user_id == User.id
        ).correlate(User).scalar_subquery()
        
        # Get users with analysis and contact counts efficiently
        users_with_stats = db.session.query(
            User,
            analysis_subq.label('analysis_count'),
            contact_subq.label('contact_count')
        ).filter(
            User.office_id == office_id
        ).all()
        
        return users_with_stats
    
    @staticmethod
    def get_dashboard_stats(user_id, office_id=None):
        """Get optimized dashboard statistics using separate queries to avoid Cartesian products"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Date ranges
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = {}
        
        # User's own stats
        total_analyses = db.session.query(func.count(ArsaAnaliz.id)).filter(ArsaAnaliz.user_id == user_id).scalar() or 0
        total_contacts = db.session.query(func.count(Contact.id)).filter(Contact.user_id == user_id).scalar() or 0
        total_deals = db.session.query(func.count(Deal.id)).filter(Deal.user_id == user_id).scalar() or 0
        total_tasks = db.session.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar() or 0
        
        stats['user'] = {
            'total_analyses': total_analyses,
            'total_contacts': total_contacts,
            'total_deals': total_deals,
            'total_tasks': total_tasks
        }
        
        # Monthly stats
        monthly_analyses = db.session.query(func.count(ArsaAnaliz.id)).filter(
            ArsaAnaliz.user_id == user_id,
            ArsaAnaliz.created_at >= start_of_month
        ).scalar() or 0

        monthly_contacts = db.session.query(func.count(Contact.id)).filter(
            Contact.user_id == user_id,
            Contact.created_at >= start_of_month
        ).scalar() or 0
        
        stats['monthly'] = {
            'analyses': monthly_analyses,
            'contacts': monthly_contacts
        }
        
        # Office stats (if office_id provided)
        if office_id:
            # We need to count users in office, and total analyses/contacts across those users
            # Subqueries for users in this office are faster than joining directly
            office_users = db.session.query(func.count(User.id)).filter(User.office_id == office_id).scalar() or 0

            office_analyses = db.session.query(func.count(ArsaAnaliz.id)).join(
                User, User.id == ArsaAnaliz.user_id
            ).filter(User.office_id == office_id).scalar() or 0

            office_contacts = db.session.query(func.count(Contact.id)).join(
                User, User.id == Contact.user_id
            ).filter(User.office_id == office_id).scalar() or 0
            
            stats['office'] = {
                'users': office_users,
                'analyses': office_analyses,
                'contacts': office_contacts
            }
        
        return stats
    
    @staticmethod
    def get_recent_activities(user_id, office_id=None, limit=10):
        """Get recent activities with optimized queries"""
        activities = []
        
        # Recent analyses
        recent_analyses = ArsaAnaliz.query.options(
            joinedload(ArsaAnaliz.user)
        ).filter_by(user_id=user_id).order_by(
            ArsaAnaliz.created_at.desc()
        ).limit(limit // 2).all()
        
        for analysis in recent_analyses:
            activities.append({
                'type': 'analysis',
                'title': analysis.baslik,
                'user': analysis.user,
                'date': analysis.created_at,
                'url': f'/analysis/{analysis.id}'
            })
        
        # Recent contacts
        recent_contacts = Contact.query.options(
            joinedload(Contact.user)
        ).filter_by(user_id=user_id).order_by(
            Contact.created_at.desc()
        ).limit(limit // 2).all()
        
        for contact in recent_contacts:
            activities.append({
                'type': 'contact',
                'title': f"{contact.ad} {contact.soyad}",
                'user': contact.user,
                'date': contact.created_at,
                'url': f'/crm/contact/{contact.id}'
            })
        
        # Sort by date and limit
        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:limit]


class CacheManager:
    """Simple caching utilities for frequently accessed data"""
    
    _cache = {}
    _cache_timeout = 300  # 5 minutes
    
    @classmethod
    def get(cls, key):
        """Get cached value if not expired"""
        import time
        
        if key in cls._cache:
            value, timestamp = cls._cache[key]
            if time.time() - timestamp < cls._cache_timeout:
                return value
            else:
                del cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key, value):
        """Set cached value with timestamp"""
        import time
        cls._cache[key] = (value, time.time())
    
    @classmethod
    def clear(cls):
        """Clear all cached values"""
        cls._cache.clear()
    
    @classmethod
    def delete(cls, key):
        """Delete specific cached value"""
        if key in cls._cache:
            del cls._cache[key]


def optimize_query_for_pagination(query, page=1, per_page=20):
    """Optimize query for pagination"""
    offset = (page - 1) * per_page
    
    # Use offset and limit for efficient pagination
    items = query.offset(offset).limit(per_page).all()
    
    # Get total count efficiently
    total = query.order_by(None).count()
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def batch_process_records(query, batch_size=100, callback=None):
    """Process large datasets in batches to avoid memory issues"""
    offset = 0
    
    while True:
        batch = query.offset(offset).limit(batch_size).all()
        
        if not batch:
            break
        
        if callback:
            callback(batch)
        
        offset += batch_size
        
        # Clear session to free memory
        db.session.expunge_all()
    
    return True
