from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from app.models import UserRole, PipelineStageType, TaskStatus, FollowUpStatus, MessageDirection, MessageType, MessageStatus

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user: Any

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# User
class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: Optional[UserRole] = UserRole.ADMIN

class UserCreate(UserBase):
    password: str
    company_name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    theme_preference: Optional[str] = None
    avatar_url: Optional[str] = None
    onboarding_completed: Optional[bool] = None

class UserOut(UserBase):
    id: int
    company_id: int
    role: UserRole
    avatar_url: Optional[str] = None
    is_active: bool
    onboarding_completed: bool
    theme_preference: str
    created_at: datetime

    class Config:
        from_attributes = True

# Company
class CompanyBase(BaseModel):
    name: str
    segment: Optional[str] = 'Geral'
    team_size: Optional[str] = '1'
    whatsapp_usage: Optional[str] = 'Vendas'
    logo_url: Optional[str] = None
    phone: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    segment: Optional[str] = None
    team_size: Optional[str] = None
    whatsapp_usage: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None

class CompanyOut(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Onboarding
class OnboardingSetup(BaseModel):
    segment: str
    team_size: str
    whatsapp_usage: str

# Tag
class TagBase(BaseModel):
    name: str
    color: Optional[str] = '#10B981'

class TagCreate(TagBase):
    pass

class TagOut(TagBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Customer Tag
class CustomerTagOut(BaseModel):
    id: int
    tag: TagOut

    class Config:
        from_attributes = True

# Customer
class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    notes: Optional[str] = None
    assigned_user_id: Optional[int] = None

class CustomerCreate(CustomerBase):
    tag_ids: Optional[List[int]] = []

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    company_name: Optional[str] = None
    notes: Optional[str] = None
    assigned_user_id: Optional[int] = None
    total_spent: Optional[float] = None
    orders_count: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class CustomerOut(CustomerBase):
    id: int
    company_id: int
    total_spent: float
    orders_count: int
    last_interaction: Optional[datetime]
    last_purchase_date: Optional[datetime]
    created_at: datetime
    assigned_user: Optional[UserOut] = None
    customer_tags: Optional[List[CustomerTagOut]] = []

    class Config:
        from_attributes = True

# Pipeline Stage
class PipelineStageBase(BaseModel):
    name: str
    stage_type: PipelineStageType = PipelineStageType.NEW
    order: int = 0
    color: str = '#10B981'

class PipelineStageCreate(PipelineStageBase):
    pass

class PipelineStageOut(PipelineStageBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True

# Opportunity
class OpportunityBase(BaseModel):
    customer_id: int
    stage_id: int
    title: str
    value: float = 0.0
    probability: int = 50
    expected_close_date: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    notes: Optional[str] = None

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    customer_id: Optional[int] = None
    stage_id: Optional[int] = None
    title: Optional[str] = None
    value: Optional[float] = None
    probability: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    assigned_user_id: Optional[int] = None
    notes: Optional[str] = None

class OpportunityOut(OpportunityBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerOut] = None
    stage: Optional[PipelineStageOut] = None
    assigned_user: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Pipeline Kanban Board View Schema
class KanbanColumn(BaseModel):
    stage: PipelineStageOut
    opportunities: List[OpportunityOut]
    total_value: float
    count: int

class ConversationEventOut(BaseModel):
    id: int
    conversation_id: int
    company_id: int
    user_id: Optional[int] = None
    event_type: str
    description: str
    created_at: datetime
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Message
class MessageBase(BaseModel):
    content: str
    direction: MessageDirection = MessageDirection.OUTBOUND
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None

class MessageCreate(BaseModel):
    content: str
    message_type: Optional[MessageType] = MessageType.TEXT
    media_url: Optional[str] = None

class MessageOut(MessageBase):
    id: int
    conversation_id: int
    sender_id: Optional[int] = None
    sender_type: Optional[str] = 'agent'
    status: MessageStatus
    external_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    sender: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Conversation
class ConversationBase(BaseModel):
    customer_id: int
    assigned_user_id: Optional[int] = None
    whatsapp_account_id: Optional[int] = None
    status: str = 'open'
    queue: Optional[str] = 'unassigned'

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    assigned_user_id: Optional[int] = None
    status: Optional[str] = None
    queue: Optional[str] = None
    version: Optional[int] = None

class ConversationAssignRequest(BaseModel):
    assigned_user_id: Optional[int] = None
    expected_version: Optional[int] = None

class ConversationTransferRequest(BaseModel):
    target_user_id: int
    notes: Optional[str] = None
    expected_version: Optional[int] = None

class ConversationOut(ConversationBase):
    id: int
    company_id: int
    unread_count: int
    last_message_text: Optional[str] = None
    last_message_time: datetime
    last_inbound_time: Optional[datetime] = None
    version: int = 1
    created_at: datetime
    customer: Optional[CustomerOut] = None
    assigned_user: Optional[UserOut] = None

    class Config:
        from_attributes = True

class ConversationDetailOut(ConversationOut):
    messages: List[MessageOut] = []
    events: List[ConversationEventOut] = []

# FollowUp
class FollowUpBase(BaseModel):
    customer_id: int
    title: str
    due_date: datetime
    notes: Optional[str] = None
    assigned_user_id: Optional[int] = None

class FollowUpCreate(FollowUpBase):
    pass

class FollowUpUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[FollowUpStatus] = None
    assigned_user_id: Optional[int] = None

class FollowUpOut(FollowUpBase):
    id: int
    company_id: int
    status: FollowUpStatus
    created_at: datetime
    customer: Optional[CustomerOut] = None
    assigned_user: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Task
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    customer_id: Optional[int] = None
    assigned_user_id: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    customer_id: Optional[int] = None
    assigned_user_id: Optional[int] = None

class TaskOut(TaskBase):
    id: int
    company_id: int
    status: TaskStatus
    created_at: datetime
    customer: Optional[CustomerOut] = None
    assigned_user: Optional[UserOut] = None

    class Config:
        from_attributes = True

# Quick Reply
class QuickReplyBase(BaseModel):
    shortcut: str
    title: str
    content: str

class QuickReplyCreate(QuickReplyBase):
    pass

class QuickReplyUpdate(BaseModel):
    shortcut: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None

class QuickReplyOut(QuickReplyBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class WhatsAppConnectRequest(BaseModel):
    name: Optional[str] = "Principal"
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None
    display_phone_number: Optional[str] = None
    verified_name: Optional[str] = None
    access_token: Optional[str] = None

class WhatsAppAccountOut(BaseModel):
    id: int
    company_id: int
    name: Optional[str] = "Principal"
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None
    display_phone_number: Optional[str] = None
    verified_name: Optional[str] = None
    is_connected: bool
    status: str
    quality_rating: Optional[str] = None
    webhook_status: Optional[str] = "active"
    webhook_verify_token: str
    has_token_configured: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class WhatsAppTestConnectionOut(BaseModel):
    success: bool
    status: str
    message: str
    display_phone_number: Optional[str] = None
    verified_name: Optional[str] = None
    quality_rating: Optional[str] = None

class WhatsAppTemplateSendRequest(BaseModel):
    template_name: str
    language_code: Optional[str] = "pt_BR"
    components: Optional[List[dict]] = None

# Notification
class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Subscription
class SubscriptionOut(BaseModel):
    id: int
    company_id: int
    plan: str
    status: str
    max_users: int
    max_customers: int
    price_cents: int
    current_period_end: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    plan: str

# Dashboard Summary
class DashboardMetrics(BaseModel):
    open_conversations: int
    new_customers_count: int
    active_opportunities_count: int
    total_sales_value: float
    pending_followups_count: int
    funnel_stages: List[dict]
    sales_chart_data: List[dict]
    urgent_followups: List[FollowUpOut]
    urgent_conversations: List[ConversationOut]

