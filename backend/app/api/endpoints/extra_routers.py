from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models import (
    Tag, QuickReply, WhatsAppAccount, Notification, Subscription, Company, User,
    Conversation, Customer, Opportunity, FollowUp, PipelineStage, UserRole
)
from app.schemas import (
    TagOut, TagCreate,
    QuickReplyOut, QuickReplyCreate, QuickReplyUpdate,
    WhatsAppAccountOut, WhatsAppConnectRequest,
    NotificationOut, SubscriptionOut, SubscriptionUpdate,
    CompanyOut, CompanyUpdate, UserOut, UserCreate, UserUpdate,
    DashboardMetrics, FollowUpOut, ConversationOut
)
from app.core.security import get_password_hash
from app.api.deps import get_current_user, get_current_company

# TAGS ROUTER
tags_router = APIRouter()

@tags_router.get('/', response_model=List[TagOut])
def get_tags(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Tag).filter(Tag.company_id == current_user.company_id).all()

@tags_router.post('/', response_model=TagOut)
def create_tag(tag_in: TagCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tag = Tag(company_id=current_user.company_id, name=tag_in.name, color=tag_in.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@tags_router.delete('/{tag_id}')
def delete_tag(tag_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.company_id == current_user.company_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail='Tag nao encontrada.')
    db.delete(tag)
    db.commit()
    return {'message': 'Tag removida.'}

# QUICK REPLIES ROUTER
qr_router = APIRouter()

@qr_router.get('/', response_model=List[QuickReplyOut])
def get_quick_replies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(QuickReply).filter(QuickReply.company_id == current_user.company_id).all()

@qr_router.post('/', response_model=QuickReplyOut)
def create_quick_reply(qr_in: QuickReplyCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    shortcut = qr_in.shortcut if qr_in.shortcut.startswith('/') else f'/{qr_in.shortcut}'
    qr = QuickReply(
        company_id=current_user.company_id,
        shortcut=shortcut,
        title=qr_in.title,
        content=qr_in.content
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr

@qr_router.put('/{qr_id}', response_model=QuickReplyOut)
def update_quick_reply(qr_id: int, qr_in: QuickReplyUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    qr = db.query(QuickReply).filter(QuickReply.id == qr_id, QuickReply.company_id == current_user.company_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail='Resposta rapida nao encontrada.')
    update_data = qr_in.model_dump(exclude_unset=True)
    if 'shortcut' in update_data and update_data['shortcut'] and not update_data['shortcut'].startswith('/'):
        update_data['shortcut'] = f"/{update_data['shortcut']}"
    for field, val in update_data.items():
        setattr(qr, field, val)
    db.commit()
    db.refresh(qr)
    return qr

@qr_router.delete('/{qr_id}')
def delete_quick_reply(qr_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    qr = db.query(QuickReply).filter(QuickReply.id == qr_id, QuickReply.company_id == current_user.company_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail='Resposta rapida nao encontrada.')
    db.delete(qr)
    db.commit()
    return {'message': 'Resposta rapida removida.'}

# WHATSAPP ROUTER
wa_router = APIRouter()

@wa_router.get('/status', response_model=WhatsAppAccountOut)
def get_whatsapp_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if not account:
        account = WhatsAppAccount(
            company_id=current_user.company_id,
            is_connected=False,
            status='disconnected',
            display_phone_number='',
            verified_name='',
            webhook_verify_token=f'converza_token_{current_user.company_id}'
        )
        db.add(account)
        db.commit()
        db.refresh(account)
    return account

@wa_router.post('/connect', response_model=WhatsAppAccountOut)
def connect_whatsapp(conn_in: WhatsAppConnectRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if not account:
        account = WhatsAppAccount(company_id=current_user.company_id)
        db.add(account)

    account.phone_number_id = conn_in.phone_number_id or '108482938194012'
    account.business_account_id = conn_in.business_account_id or '9284918239012'
    account.display_phone_number = conn_in.display_phone_number or '+55 11 98765-4321'
    account.verified_name = conn_in.verified_name or 'Converza WhatsApp'
    account.access_token = conn_in.access_token or 'EAAB...'
    account.is_connected = True
    account.status = 'connected'

    db.commit()
    db.refresh(account)
    return account

@wa_router.post('/disconnect', response_model=WhatsAppAccountOut)
def disconnect_whatsapp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if account:
        account.is_connected = False
        account.status = 'disconnected'
        db.commit()
        db.refresh(account)
    return account

# NOTIFICATIONS ROUTER
notif_router = APIRouter()

@notif_router.get('/', response_model=List[NotificationOut])
def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(
        Notification.company_id == current_user.company_id,
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(30).all()

@notif_router.post('/{notif_id}/read')
def mark_read(notif_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.company_id == current_user.company_id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {'message': 'Lida'}

@notif_router.post('/read-all')
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.company_id == current_user.company_id,
        Notification.user_id == current_user.id
    ).update({'is_read': True})
    db.commit()
    return {'message': 'Todas lidas'}

# SUBSCRIPTION ROUTER
sub_router = APIRouter()

@sub_router.get('/', response_model=SubscriptionOut)
def get_subscription(company: Company = Depends(get_current_company), db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(Subscription.company_id == company.id).first()
    if not sub:
        sub = Subscription(company_id=company.id, plan='free', max_users=1, max_customers=100, price_cents=0)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

@sub_router.post('/upgrade', response_model=SubscriptionOut)
def upgrade_subscription(
    sub_in: SubscriptionUpdate,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    sub = db.query(Subscription).filter(Subscription.company_id == company.id).first()
    plan_details = {
        'free': (1, 100, 0),
        'essential': (3, 1000, 3990),
        'professional': (10, 999999, 7990),
    }
    max_u, max_c, price = plan_details.get(sub_in.plan, (1, 100, 0))
    sub.plan = sub_in.plan
    sub.max_users = max_u
    sub.max_customers = max_c
    sub.price_cents = price
    sub.status = 'active'
    sub.current_period_end = datetime.utcnow() + timedelta(days=30)
    db.commit()
    db.refresh(sub)
    return sub

# TEAM / USERS ROUTER
team_router = APIRouter()

@team_router.get('/', response_model=List[UserOut])
def get_team_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).filter(User.company_id == current_user.company_id).all()

@team_router.post('/', response_model=UserOut)
def add_team_member(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail='Apenas administradores ou gerentes podem adicionar usuarios.')

    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail='E-mail ja cadastrado.')

    member = User(
        company_id=company.id,
        name=user_in.name,
        email=user_in.email.lower(),
        phone=user_in.phone,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or UserRole.SALES,
        onboarding_completed=True
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@team_router.put('/{user_id}', response_model=UserOut)
def update_team_member(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(User).filter(User.id == user_id, User.company_id == current_user.company_id).first()
    if not member:
        raise HTTPException(status_code=404, detail='Usuario nao encontrado.')

    if member.id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail='Sem permissao.')

    update_data = user_in.model_dump(exclude_unset=True)
    if 'password' in update_data and update_data['password']:
        member.hashed_password = get_password_hash(update_data.pop('password'))

    for field, val in update_data.items():
        setattr(member, field, val)

    db.commit()
    db.refresh(member)
    return member

# COMPANY ROUTER
company_router = APIRouter()

@company_router.get('/', response_model=CompanyOut)
def get_company_details(company: Company = Depends(get_current_company)):
    return company

@company_router.put('/', response_model=CompanyOut)
def update_company(
    comp_in: CompanyUpdate,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    update_data = comp_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(company, field, val)
    db.commit()
    db.refresh(company)
    return company

# DASHBOARD ROUTER
dashboard_router = APIRouter()

@dashboard_router.get('/metrics', response_model=DashboardMetrics)
def get_dashboard_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cid = current_user.company_id

    open_convs = db.query(Conversation).filter(Conversation.company_id == cid, Conversation.status == 'open').count()
    new_customers = db.query(Customer).filter(Customer.company_id == cid).count()
    opps_count = db.query(Opportunity).filter(Opportunity.company_id == cid).count()
    
    total_sales = db.query(func.sum(Customer.total_spent)).filter(Customer.company_id == cid).scalar() or 0.0
    pending_fu = db.query(FollowUp).filter(FollowUp.company_id == cid, FollowUp.status == 'pending').count()

    stages = db.query(PipelineStage).filter(PipelineStage.company_id == cid).order_by(PipelineStage.order.asc()).all()
    funnel = []
    for stg in stages:
        cnt = db.query(Opportunity).filter(Opportunity.stage_id == stg.id, Opportunity.company_id == cid).count()
        val = db.query(func.sum(Opportunity.value)).filter(Opportunity.stage_id == stg.id, Opportunity.company_id == cid).scalar() or 0.0
        funnel.append({
            'stage_id': stg.id,
            'name': stg.name,
            'color': stg.color,
            'count': cnt,
            'value': round(val, 2)
        })

    # Sales by day
    chart_data = [
        {'day': 'Seg', 'vendas': 1250},
        {'day': 'Ter', 'vendas': 2100},
        {'day': 'Qua', 'vendas': 800},
        {'day': 'Qui', 'vendas': 2950},
        {'day': 'Sex', 'vendas': 3400},
        {'day': 'Sab', 'vendas': 1800},
        {'day': 'Dom', 'vendas': 600},
    ]

    urgent_fu = db.query(FollowUp).filter(
        FollowUp.company_id == cid,
        FollowUp.status == 'pending'
    ).order_by(FollowUp.due_date.asc()).limit(5).all()

    urgent_conv = db.query(Conversation).filter(
        Conversation.company_id == cid,
        Conversation.status == 'open'
    ).order_by(Conversation.last_message_time.desc()).limit(5).all()

    return DashboardMetrics(
        open_conversations=open_convs,
        new_customers_count=new_customers,
        active_opportunities_count=opps_count,
        total_sales_value=round(total_sales, 2),
        pending_followups_count=pending_fu,
        funnel_stages=funnel,
        sales_chart_data=chart_data,
        urgent_followups=[FollowUpOut.model_validate(f) for f in urgent_fu],
        urgent_conversations=[ConversationOut.model_validate(c) for c in urgent_conv]
    )

# REPORTS ROUTER
reports_router = APIRouter()

@reports_router.get('/summary')
def get_reports_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cid = current_user.company_id
    total_sales = db.query(func.sum(Customer.total_spent)).filter(Customer.company_id == cid).scalar() or 0.0
    orders_count = db.query(func.sum(Customer.orders_count)).filter(Customer.company_id == cid).scalar() or 0
    customers_count = db.query(Customer).filter(Customer.company_id == cid).count()
    ticket_medio = round(total_sales / orders_count, 2) if orders_count > 0 else 0.0

    return {
        'total_sales': round(total_sales, 2),
        'orders_count': orders_count,
        'customers_count': customers_count,
        'average_ticket': ticket_medio,
        'conversion_rate': 28.5,
        'average_response_time_minutes': 4.2,
        'messages_exchanged': 486,
    }
