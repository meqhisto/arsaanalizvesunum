"""Add performance indexes

Revision ID: c7d1ecdef1b8
Revises: bca257d8b960
Create Date: 2025-06-09 23:33:38.860285

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d1ecdef1b8'
down_revision = 'bca257d8b960'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for critical database operations"""

    # ArsaAnaliz performance indexes
    op.create_index('idx_arsa_user_created', 'arsa_analizleri', ['user_id', 'created_at'])
    op.create_index('idx_arsa_location', 'arsa_analizleri', ['il', 'ilce'])
    op.create_index('idx_arsa_office_user', 'arsa_analizleri', ['office_id', 'user_id'])
    op.create_index('idx_arsa_status', 'arsa_analizleri', ['durum'])
    op.create_index('idx_arsa_price_range', 'arsa_analizleri', ['fiyat', 'metrekare'])
    op.create_index('idx_arsa_imar', 'arsa_analizleri', ['imar_durumu'])

    # CRM Contacts performance indexes
    op.create_index('idx_crm_contacts_user_status', 'crm_contacts', ['user_id', 'status'])
    op.create_index('idx_crm_contacts_office', 'crm_contacts', ['office_id'])
    op.create_index('idx_crm_contacts_email', 'crm_contacts', ['email'])
    op.create_index('idx_crm_contacts_created', 'crm_contacts', ['created_at'])

    # CRM Deals performance indexes
    op.create_index('idx_crm_deals_user_stage', 'crm_deals', ['user_id', 'stage'])
    op.create_index('idx_crm_deals_status', 'crm_deals', ['status'])
    op.create_index('idx_crm_deals_value', 'crm_deals', ['value'])
    op.create_index('idx_crm_deals_close_date', 'crm_deals', ['expected_close_date'])

    # CRM Tasks performance indexes
    op.create_index('idx_crm_tasks_user_status', 'crm_tasks', ['user_id', 'status'])
    op.create_index('idx_crm_tasks_priority', 'crm_tasks', ['priority'])
    op.create_index('idx_crm_tasks_due_date', 'crm_tasks', ['due_date'])
    op.create_index('idx_crm_tasks_contact', 'crm_tasks', ['contact_id'])

    # Users performance indexes
    op.create_index('idx_users_office_role', 'users', ['office_id', 'role'])
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_last_login', 'users', ['son_giris'])

    # Permissions performance indexes
    op.create_index('idx_user_permissions_user_key', 'user_permissions', ['user_id', 'permission_key'])
    op.create_index('idx_user_permissions_active', 'user_permissions', ['is_active'])
    op.create_index('idx_office_permissions_office_role', 'office_permissions', ['office_id', 'role'])

    # Portfolio performance indexes
    op.create_index('idx_portfolios_user', 'portfolios', ['user_id'])
    op.create_index('idx_portfolios_created', 'portfolios', ['created_at'])

    # Media performance indexes
    op.create_index('idx_analiz_medya_analiz', 'analiz_medya', ['analiz_id'])
    op.create_index('idx_analiz_medya_type', 'analiz_medya', ['type'])


def downgrade():
    """Remove performance indexes"""

    # Remove ArsaAnaliz indexes
    op.drop_index('idx_arsa_user_created', 'arsa_analizleri')
    op.drop_index('idx_arsa_location', 'arsa_analizleri')
    op.drop_index('idx_arsa_office_user', 'arsa_analizleri')
    op.drop_index('idx_arsa_status', 'arsa_analizleri')
    op.drop_index('idx_arsa_price_range', 'arsa_analizleri')
    op.drop_index('idx_arsa_imar', 'arsa_analizleri')

    # Remove CRM Contacts indexes
    op.drop_index('idx_crm_contacts_user_status', 'crm_contacts')
    op.drop_index('idx_crm_contacts_office', 'crm_contacts')
    op.drop_index('idx_crm_contacts_email', 'crm_contacts')
    op.drop_index('idx_crm_contacts_created', 'crm_contacts')

    # Remove CRM Deals indexes
    op.drop_index('idx_crm_deals_user_stage', 'crm_deals')
    op.drop_index('idx_crm_deals_status', 'crm_deals')
    op.drop_index('idx_crm_deals_value', 'crm_deals')
    op.drop_index('idx_crm_deals_close_date', 'crm_deals')

    # Remove CRM Tasks indexes
    op.drop_index('idx_crm_tasks_user_status', 'crm_tasks')
    op.drop_index('idx_crm_tasks_priority', 'crm_tasks')
    op.drop_index('idx_crm_tasks_due_date', 'crm_tasks')
    op.drop_index('idx_crm_tasks_contact', 'crm_tasks')

    # Remove Users indexes
    op.drop_index('idx_users_office_role', 'users')
    op.drop_index('idx_users_active', 'users')
    op.drop_index('idx_users_last_login', 'users')

    # Remove Permissions indexes
    op.drop_index('idx_user_permissions_user_key', 'user_permissions')
    op.drop_index('idx_user_permissions_active', 'user_permissions')
    op.drop_index('idx_office_permissions_office_role', 'office_permissions')

    # Remove Portfolio indexes
    op.drop_index('idx_portfolios_user', 'portfolios')
    op.drop_index('idx_portfolios_created', 'portfolios')

    # Remove Media indexes
    op.drop_index('idx_analiz_medya_analiz', 'analiz_medya')
    op.drop_index('idx_analiz_medya_type', 'analiz_medya')
