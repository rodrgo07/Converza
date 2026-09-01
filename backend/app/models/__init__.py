import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from app.db.session import Base

class UserRole(str, enum.Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    SALES = 'sales'
    SUPPORT = 'support'

class PipelineStageType(str, enum.Enum):
    NEW = 'new'
    INTERESTED = 'interested'
    QUOTE = 'quote'
    NEGOTIATION = 'negotiation'
    SALE = 'sale'
    POST_SALE = 'post_sale'
    LOST = 'lost'

class TaskStatus(str, enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class FollowUpStatus(str, enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    EXPIRED = 'expired'

class MessageDirection(str, enum.Enum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'

class MessageType(str, enum.Enum):
    TEXT = 'text'
    IMAGE = 'image'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    VIDEO = 'video'

class MessageStatus(str, enum.Enum):
    SENDING = 'sending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    READ = 'read'
    FAILED = 'failed'

def utcnow():
    return datetime.now(timezone.utc)

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    segment = Column(String(100), default='Geral')
    team_size = Column(String(50), default='1')
    whatsapp_usage = Column(String(100), default='Vendas')
    logo_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    users = relationship('User', back_populates='company', cascade='all, delete-orphan')
    customers = relationship('Customer', back_populates='company', cascade='all, delete-orphan')
    conversations = relationship('Conversation', back_populates='company', cascade='all, delete-orphan')
    tags = relationship('Tag', back_populates='company', cascade='all, delete-orphan')
    pipeline_stages = relationship('PipelineStage', back_populates='company', cascade='all, delete-orphan')
    opportunities = relationship('Opportunity', back_populates='company', cascade='all, delete-orphan')
    tasks = relationship('Task', back_populates='company', cascade='all, delete-orphan')
    follow_ups = relationship('FollowUp', back_populates='company', cascade='all, delete-orphan')
    quick_replies = relationship('QuickReply', back_populates='company', cascade='all, delete-orphan')
    whatsapp_accounts = relationship('WhatsAppAccount', back_populates='company', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='company', cascade='all, delete-orphan')
    subscription = relationship('Subscription', back_populates='company', uselist=False, cascade='all, delete-orphan')

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ADMIN, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    theme_preference = Column(String(20), default='system')  # light, dark, system
    is_online = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='users', foreign_keys=[company_id])
    assigned_customers = relationship('Customer', back_populates='assigned_user')
    assigned_conversations = relationship('Conversation', back_populates='assigned_user', foreign_keys='Conversation.assigned_user_id')
    assigned_opportunities = relationship('Opportunity', back_populates='assigned_user')
    assigned_tasks = relationship('Task', back_populates='assigned_user')
    assigned_follow_ups = relationship('FollowUp', back_populates='assigned_user')
    notifications = relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    conversation_events = relationship('ConversationEvent', back_populates='user')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(50), default='#10B981')
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='tags', foreign_keys=[company_id])
    customer_tags = relationship('CustomerTag', back_populates='tag', cascade='all, delete-orphan')

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), index=True, nullable=False)
    email = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    total_spent = Column(Float, default=0.0)
    orders_count = Column(Integer, default=0)
    last_interaction = Column(DateTime(timezone=True), default=utcnow)
    last_purchase_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='customers', foreign_keys=[company_id])
    assigned_user = relationship('User', back_populates='assigned_customers', foreign_keys=[assigned_user_id])
    customer_tags = relationship('CustomerTag', back_populates='customer', cascade='all, delete-orphan')
    conversations = relationship('Conversation', back_populates='customer', cascade='all, delete-orphan')
    opportunities = relationship('Opportunity', back_populates='customer', cascade='all, delete-orphan')
    tasks = relationship('Task', back_populates='customer', cascade='all, delete-orphan')
    follow_ups = relationship('FollowUp', back_populates='customer', cascade='all, delete-orphan')

class CustomerTag(Base):
    __tablename__ = 'customer_tags'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), nullable=False)

    customer = relationship('Customer', back_populates='customer_tags', foreign_keys=[customer_id])
    tag = relationship('Tag', back_populates='customer_tags', foreign_keys=[tag_id])

class PipelineStage(Base):
    __tablename__ = 'pipeline_stages'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    stage_type = Column(Enum(PipelineStageType), default=PipelineStageType.NEW)
    order = Column(Integer, default=0)
    color = Column(String(50), default='#10B981')

    company = relationship('Company', back_populates='pipeline_stages', foreign_keys=[company_id])
    opportunities = relationship('Opportunity', back_populates='stage', cascade='all, delete-orphan')

class Opportunity(Base):
    __tablename__ = 'opportunities'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    stage_id = Column(Integer, ForeignKey('pipeline_stages.id', ondelete='CASCADE'), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(255), nullable=False)
    value = Column(Float, default=0.0)
    probability = Column(Integer, default=50)
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company = relationship('Company', back_populates='opportunities')
    customer = relationship('Customer', back_populates='opportunities', foreign_keys=[customer_id])
    stage = relationship('PipelineStage', back_populates='opportunities', foreign_keys=[stage_id])
    assigned_user = relationship('User', back_populates='assigned_opportunities', foreign_keys=[assigned_user_id])

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    whatsapp_account_id = Column(Integer, ForeignKey('whatsapp_accounts.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(50), default='open') # open, closed, snoozed, resolved, pending
    queue = Column(String(50), default='unassigned') # unassigned, mine, all, waiting, resolved
    unread_count = Column(Integer, default=0)
    last_message_text = Column(Text, nullable=True)
    last_message_time = Column(DateTime(timezone=True), default=utcnow)
    last_inbound_time = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='conversations', foreign_keys=[company_id])
    customer = relationship('Customer', back_populates='conversations', foreign_keys=[customer_id])
    assigned_user = relationship('User', foreign_keys=[assigned_user_id], back_populates='assigned_conversations')
    whatsapp_account = relationship('WhatsAppAccount', back_populates='conversations', foreign_keys=[whatsapp_account_id])
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan', order_by='Message.id')
    events = relationship('ConversationEvent', back_populates='conversation', cascade='all, delete-orphan', order_by='ConversationEvent.id')

class ConversationEvent(Base):
    __tablename__ = 'conversation_events'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    event_type = Column(String(50), nullable=False) # ASSIGNED, TRANSFERRED, RESOLVED, REOPENED
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    conversation = relationship('Conversation', back_populates='events')
    user = relationship('User', back_populates='conversation_events', foreign_keys=[user_id])
    company = relationship('Company', foreign_keys=[company_id])

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True) # None if from customer
    sender_type = Column(String(20), default='agent') # agent, customer, system
    whatsapp_account_id = Column(Integer, ForeignKey('whatsapp_accounts.id', ondelete='SET NULL'), nullable=True)
    direction = Column(Enum(MessageDirection), default=MessageDirection.INBOUND)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    content = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    external_id = Column(String(255), unique=True, index=True, nullable=True) # WhatsApp Message ID (Idempotence)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    conversation = relationship('Conversation', back_populates='messages')
    sender = relationship('User', foreign_keys=[sender_id])
    whatsapp_account = relationship('WhatsAppAccount', foreign_keys=[whatsapp_account_id])

class FollowUp(Base):
    __tablename__ = 'follow_ups'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    assigned_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(FollowUpStatus), default=FollowUpStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='follow_ups')
    customer = relationship('Customer', back_populates='follow_ups', foreign_keys=[customer_id])
    assigned_user = relationship('User', back_populates='assigned_follow_ups', foreign_keys=[assigned_user_id])

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='SET NULL'), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='tasks')
    customer = relationship('Customer', back_populates='tasks', foreign_keys=[customer_id])
    assigned_user = relationship('User', back_populates='assigned_tasks', foreign_keys=[assigned_user_id])

class QuickReply(Base):
    __tablename__ = 'quick_replies'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    shortcut = Column(String(50), nullable=False) # e.g. /ola, /orcamento, /pix
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='quick_replies')

class WhatsAppAccount(Base):
    __tablename__ = 'whatsapp_accounts'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), default='Principal') # Comercial, Suporte, Vendas
    phone_number_id = Column(String(100), index=True, nullable=True)
    business_account_id = Column(String(100), nullable=True)
    display_phone_number = Column(String(50), nullable=True)
    verified_name = Column(String(255), nullable=True)
    access_token = Column(String(500), nullable=True)
    webhook_verify_token = Column(String(255), default='converza_verify_token_2026')
    is_connected = Column(Boolean, default=False)
    status = Column(String(50), default='disconnected') # connected, disconnected, pending, error
    quality_rating = Column(String(50), nullable=True)
    webhook_status = Column(String(50), default='active')
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @property
    def has_token_configured(self) -> bool:
        return bool(self.access_token)

    company = relationship('Company', back_populates='whatsapp_accounts', foreign_keys=[company_id])
    conversations = relationship('Conversation', back_populates='whatsapp_account')

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default='general')
    is_read = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='notifications', foreign_keys=[company_id])
    user = relationship('User', back_populates='notifications', foreign_keys=[user_id])

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), unique=True, nullable=False)
    plan = Column(String(50), default='free') # free, essential, professional
    status = Column(String(50), default='active')
    max_users = Column(Integer, default=1)
    max_customers = Column(Integer, default=100)
    price_cents = Column(Integer, default=0)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', back_populates='subscription', foreign_keys=[company_id])

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    company = relationship('Company', foreign_keys=[company_id])
    user = relationship('User', foreign_keys=[user_id])
