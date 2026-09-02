from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
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

@tags_router.get("", response_model=List[TagOut])
def get_tags(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Tag).filter(Tag.company_id == current_user.company_id).all()

@tags_router.post("", response_model=TagOut)
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
        raise HTTPException(status_code=404, detail='Tag não encontrada.')
    db.delete(tag)
    db.commit()
    return {'message': 'Tag removida.'}

# QUICK REPLIES ROUTER
qr_router = APIRouter()

@qr_router.get("", response_model=List[QuickReplyOut])
def get_quick_replies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(QuickReply).filter(QuickReply.company_id == current_user.company_id).all()

@qr_router.post("", response_model=QuickReplyOut)
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
        raise HTTPException(status_code=404, detail='Resposta rápida não encontrada.')
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
        raise HTTPException(status_code=404, detail='Resposta rápida não encontrada.')
    db.delete(qr)
    db.commit()
    return {'message': 'Resposta rápida removida.'}

# WHATSAPP ROUTER
wa_router = APIRouter()

@wa_router.get('/accounts', response_model=List[WhatsAppAccountOut])
def get_whatsapp_accounts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Lista todos os números / contas oficiais de WhatsApp conectadas para a empresa.
    """
    accounts = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).all()
    if not accounts:
        # Se nenhuma conta existir, cria a conta padrão
        default_acc = WhatsAppAccount(
            company_id=current_user.company_id,
            name="Principal",
            is_connected=False,
            status="disconnected",
            display_phone_number="",
            verified_name="",
            webhook_verify_token=f"converza_token_{current_user.company_id}"
        )
        db.add(default_acc)
        db.commit()
        db.refresh(default_acc)
        accounts = [default_acc]
    return accounts

@wa_router.get('/status', response_model=WhatsAppAccountOut)
def get_whatsapp_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retorna a conta padrão / primária da empresa. O access_token NUNCA é retornado no schema.
    """
    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if not account:
        account = WhatsAppAccount(
            company_id=current_user.company_id,
            name="Principal",
            is_connected=False,
            status="disconnected",
            display_phone_number="",
            verified_name="",
            webhook_verify_token=f"converza_token_{current_user.company_id}"
        )
        db.add(account)
        db.commit()
        db.refresh(account)
    return account

@wa_router.post('/connect', response_model=WhatsAppAccountOut)
async def connect_whatsapp(
    conn_in: WhatsAppConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Salva credenciais da WhatsApp Business Platform / Cloud API no backend
    e realiza teste de verificação real com os servidores da Meta antes de aprovar a conexão.
    """
    from app.services.whatsapp import WhatsAppProvider
    from app.core.audit import log_audit
    from app.core.permissions import check_permission

    check_permission(current_user, 'whatsapp.manage')

    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if not account:
        account = WhatsAppAccount(company_id=current_user.company_id)
        db.add(account)

    account.name = conn_in.name or "Principal"
    account.phone_number_id = conn_in.phone_number_id.strip() if conn_in.phone_number_id else None
    account.business_account_id = conn_in.business_account_id.strip() if conn_in.business_account_id else None
    account.display_phone_number = conn_in.display_phone_number.strip() if conn_in.display_phone_number else None
    account.verified_name = conn_in.verified_name.strip() if conn_in.verified_name else None
    if conn_in.access_token:
        account.access_token = conn_in.access_token.strip()

    # Validação REAL com a API da Meta
    if account.phone_number_id and account.access_token:
        provider = WhatsAppProvider(phone_number_id=account.phone_number_id, access_token=account.access_token)
        try:
            meta_data = await provider.verify_credentials()
            account.is_connected = True
            account.status = "connected"
            account.verified_name = meta_data.get("verified_name") or account.verified_name
            account.display_phone_number = meta_data.get("display_phone_number") or account.display_phone_number
            account.quality_rating = meta_data.get("quality_rating") or "GREEN"
        except Exception as exc:
            account.is_connected = False
            account.status = "error"
            db.commit()
            raise HTTPException(status_code=400, detail={"code": "META_VERIFICATION_FAILED", "message": str(exc)})
    else:
        account.is_connected = False
        account.status = "disconnected"

    log_audit(
        db=db,
        company_id=current_user.company_id,
        user_id=current_user.id,
        action="WHATSAPP_CONNECTED" if account.is_connected else "WHATSAPP_CONNECT_FAILED",
        resource="WhatsAppAccount",
        resource_id=str(account.id),
        details={"phone_number_id": account.phone_number_id, "display_phone": account.display_phone_number}
    )

    db.commit()
    db.refresh(account)
    return account

@wa_router.post('/test-connection')
async def test_whatsapp_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executa teste de conexão real e ao vivo com a Graph API da Meta.
    """
    from app.services.whatsapp import WhatsAppProvider
    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if not account or not account.phone_number_id or not account.access_token:
        return {
            "success": False,
            "status": "Configuração incompleta",
            "message": "Nenhuma credencial oficial do WhatsApp Cloud API configurada no backend."
        }

    provider = WhatsAppProvider(phone_number_id=account.phone_number_id, access_token=account.access_token)
    try:
        data = await provider.verify_credentials()
        return {
            "success": True,
            "status": "Conectado e Operante",
            "message": "WhatsApp Cloud API conectada e respondendo perfeitamente.",
            "display_phone_number": data.get("display_phone_number", account.display_phone_number),
            "verified_name": data.get("verified_name", account.verified_name),
            "quality_rating": data.get("quality_rating", "GREEN")
        }
    except Exception as exc:
        return {
            "success": False,
            "status": "WhatsApp conectado, mas a API não respondeu corretamente",
            "message": str(exc)
        }

@wa_router.post('/disconnect', response_model=WhatsAppAccountOut)
def disconnect_whatsapp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Desconecta o número oficial da empresa.
    """
    from app.core.audit import log_audit
    from app.core.permissions import check_permission
    check_permission(current_user, 'whatsapp.disconnect')

    account = db.query(WhatsAppAccount).filter(WhatsAppAccount.company_id == current_user.company_id).first()
    if account:
        account.is_connected = False
        account.status = 'disconnected'
        account.access_token = None
        log_audit(
            db=db,
            company_id=current_user.company_id,
            user_id=current_user.id,
            action="WHATSAPP_DISCONNECTED",
            resource="WhatsAppAccount",
            resource_id=str(account.id)
        )
        db.commit()
        db.refresh(account)
    return account


# NOTIFICATIONS ROUTER
notif_router = APIRouter()

@notif_router.get("", response_model=List[NotificationOut])
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

@sub_router.get("", response_model=SubscriptionOut)
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
    sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
    db.commit()
    db.refresh(sub)
    return sub

# TEAM / USERS ROUTER
team_router = APIRouter()

@team_router.get("", response_model=List[UserOut])
def get_team_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(User).filter(User.company_id == current_user.company_id).all()

@team_router.post("", response_model=UserOut)
def add_team_member(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail='Apenas administradores ou gerentes podem adicionar usuários.')

    # Rule: Plan max users validation
    sub = db.query(Subscription).filter(Subscription.company_id == company.id).first()
    max_users_allowed = sub.max_users if sub else 1
    current_users_count = db.query(User).filter(User.company_id == company.id).count()

    if current_users_count >= max_users_allowed:
        raise HTTPException(
            status_code=403,
            detail=f'Limite do plano atingido ({max_users_allowed} usuários). Faça upgrade da assinatura para adicionar mais membros.'
        )

    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail='E-mail já cadastrado.')

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
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')

    if member.id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail='Sem permissão.')

    update_data = user_in.model_dump(exclude_unset=True)
    if 'password' in update_data and update_data['password']:
        member.hashed_password = get_password_hash(update_data.pop('password'))

    for field, val in update_data.items():
        setattr(member, field, val)

    db.commit()
    db.refresh(member)
    return member

@team_router.delete('/{user_id}')
def delete_team_member(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail='Apenas administradores podem remover membros da equipe.')

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail='Você não pode remover seu próprio usuário administrador.')

    member = db.query(User).filter(User.id == user_id, User.company_id == current_user.company_id).first()
    if not member:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')

    db.delete(member)
    db.commit()
    return {'message': 'Membro removido da equipe com sucesso.'}

# COMPANY ROUTER
company_router = APIRouter()

@company_router.get("", response_model=CompanyOut)
def get_company_details(company: Company = Depends(get_current_company)):
    return company

@company_router.put("", response_model=CompanyOut)
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

    # Sales by day - calculated dynamically from real customer purchases/interactions in the last 7 days
    days_map = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    now = datetime.now(timezone.utc)
    chart_data = []
    for i in range(6, -1, -1):
        target_date = (now - timedelta(days=i)).date()
        day_label = days_map[target_date.weekday()]
        
        # Real sum of purchases on that day
        day_sales = db.query(func.sum(Customer.total_spent)).filter(
            Customer.company_id == cid,
            func.date(Customer.last_purchase_date) == target_date
        ).scalar() or 0.0
        
        chart_data.append({'day': day_label, 'vendas': round(float(day_sales), 2)})

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

    # Total real messages in company conversations
    total_msgs = db.query(func.count(Conversation.id)).filter(Conversation.company_id == cid).scalar() or 0
    total_opps = db.query(func.count(Opportunity.id)).filter(Opportunity.company_id == cid).scalar() or 0
    closed_sales_count = db.query(func.count(Opportunity.id)).join(PipelineStage).filter(
        Opportunity.company_id == cid,
        PipelineStage.stage_type == 'sale'
    ).scalar() or 0

    conversion_rate = round((closed_sales_count / total_opps * 100), 1) if total_opps > 0 else 0.0

    return {
        'total_sales': round(total_sales, 2),
        'orders_count': orders_count,
        'customers_count': customers_count,
        'average_ticket': ticket_medio,
        'conversion_rate': conversion_rate,
        'average_response_time_minutes': 0.0,
        'messages_exchanged': total_msgs,
    }

@reports_router.post('/process-automations')
def run_automations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.automations import process_due_followups_and_tasks
    result = process_due_followups_and_tasks(db)
    return {
        "success": True,
        "result": result
    }