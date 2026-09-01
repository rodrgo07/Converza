"""add_missing_columns

Revision ID: b2c3d4e5f6a7
Revises: 1acec6f65b1c
Create Date: 2026-09-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '1acec6f65b1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Users: add is_online
    if not column_exists('users', 'is_online'):
        op.add_column('users', sa.Column('is_online', sa.Boolean(), nullable=True, server_default='true'))

    # WhatsApp Accounts: add name, quality_rating, webhook_status
    if not column_exists('whatsapp_accounts', 'name'):
        op.add_column('whatsapp_accounts', sa.Column('name', sa.String(length=100), nullable=True, server_default='Principal'))
    if not column_exists('whatsapp_accounts', 'quality_rating'):
        op.add_column('whatsapp_accounts', sa.Column('quality_rating', sa.String(length=50), nullable=True))
    if not column_exists('whatsapp_accounts', 'webhook_status'):
        op.add_column('whatsapp_accounts', sa.Column('webhook_status', sa.String(length=50), nullable=True, server_default='active'))
    if not column_exists('whatsapp_accounts', 'updated_at'):
        op.add_column('whatsapp_accounts', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Conversations: add queue, last_inbound_time, version
    if not column_exists('conversations', 'queue'):
        op.add_column('conversations', sa.Column('queue', sa.String(length=50), nullable=True, server_default='unassigned'))
    if not column_exists('conversations', 'last_inbound_time'):
        op.add_column('conversations', sa.Column('last_inbound_time', sa.DateTime(), nullable=True))
    if not column_exists('conversations', 'version'):
        op.add_column('conversations', sa.Column('version', sa.Integer(), nullable=True, server_default='1'))

    # Messages: add sender_type, whatsapp_account_id, error_message
    if not column_exists('messages', 'sender_type'):
        op.add_column('messages', sa.Column('sender_type', sa.String(length=20), nullable=True, server_default='agent'))
    if not column_exists('messages', 'whatsapp_account_id'):
        op.add_column('messages', sa.Column('whatsapp_account_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_messages_whatsapp_account', 'messages', 'whatsapp_accounts', ['whatsapp_account_id'], ['id'], ondelete='SET NULL')
    if not column_exists('messages', 'error_message'):
        op.add_column('messages', sa.Column('error_message', sa.Text(), nullable=True))

    # Add unique constraint on customers(company_id, phone) to prevent race conditions
    op.create_unique_constraint('uq_customer_company_phone', 'customers', ['company_id', 'phone'])


def downgrade() -> None:
    op.drop_constraint('uq_customer_company_phone', 'customers', type_='unique')
    if column_exists('messages', 'error_message'):
        op.drop_column('messages', 'error_message')
    if column_exists('messages', 'whatsapp_account_id'):
        op.drop_constraint('fk_messages_whatsapp_account', 'messages', type_='foreignkey')
        op.drop_column('messages', 'whatsapp_account_id')
    if column_exists('messages', 'sender_type'):
        op.drop_column('messages', 'sender_type')
    if column_exists('conversations', 'version'):
        op.drop_column('conversations', 'version')
    if column_exists('conversations', 'last_inbound_time'):
        op.drop_column('conversations', 'last_inbound_time')
    if column_exists('conversations', 'queue'):
        op.drop_column('conversations', 'queue')
    if column_exists('whatsapp_accounts', 'updated_at'):
        op.drop_column('whatsapp_accounts', 'updated_at')
    if column_exists('whatsapp_accounts', 'webhook_status'):
        op.drop_column('whatsapp_accounts', 'webhook_status')
    if column_exists('whatsapp_accounts', 'quality_rating'):
        op.drop_column('whatsapp_accounts', 'quality_rating')
    if column_exists('whatsapp_accounts', 'name'):
        op.drop_column('whatsapp_accounts', 'name')
    if column_exists('users', 'is_online'):
        op.drop_column('users', 'is_online')
