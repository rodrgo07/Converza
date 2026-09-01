from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import (
    Customer, CustomerTag, Tag, User, Conversation, Message,
    MessageDirection, MessageType, MessageStatus, Company, Subscription
)
from app.schemas import CustomerCreate, CustomerUpdate, CustomerOut
from app.api.deps import get_current_user, get_current_company

router = APIRouter()

@router.get('/', response_model=List[CustomerOut])
def get_customers(
    search: Optional[str] = None,
    filter_stage: Optional[str] = None,
    tag_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Customer).filter(Customer.company_id == current_user.company_id)

    if search:
        s = f'%{search}%'
        query = query.filter((Customer.name.ilike(s)) | (Customer.phone.ilike(s)) | (Customer.company_name.ilike(s)))

    if tag_id:
        query = query.join(CustomerTag).filter(CustomerTag.tag_id == tag_id)

    customers = query.order_by(Customer.last_interaction.desc().nullslast(), Customer.created_at.desc()).offset(skip).limit(limit).all()
    return customers

@router.post('/', response_model=CustomerOut)
def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_user),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    # Rule: Plan max customers validation
    sub = db.query(Subscription).filter(Subscription.company_id == company.id).first()
    max_allowed = sub.max_customers if sub else 100
    current_count = db.query(Customer).filter(Customer.company_id == company.id).count()

    if current_count >= max_allowed:
        raise HTTPException(
            status_code=403,
            detail=f'Limite do plano atingido ({max_allowed} clientes). Faça upgrade da sua assinatura para cadastrar mais clientes.'
        )

    now = datetime.now(timezone.utc)
    customer = Customer(
        company_id=company.id,
        name=customer_in.name,
        phone=customer_in.phone,
        email=customer_in.email,
        company_name=customer_in.company_name,
        notes=customer_in.notes,
        assigned_user_id=customer_in.assigned_user_id or current_user.id,
        last_interaction=now,
        created_at=now
    )
    db.add(customer)
    db.flush()

    if customer_in.tag_ids:
        for tid in customer_in.tag_ids:
            ct = CustomerTag(customer_id=customer.id, tag_id=tid)
            db.add(ct)

    # Automatically create the real conversation thread in PostgreSQL
    conversation = Conversation(
        company_id=current_user.company_id,
        customer_id=customer.id,
        assigned_user_id=customer.assigned_user_id,
        status='open',
        unread_count=0,
        last_message_text=None,
        last_message_time=now,
        created_at=now
    )
    db.add(conversation)

    db.commit()
    db.refresh(customer)
    return customer

@router.get('/{customer_id}', response_model=CustomerOut)
def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')
    return customer

@router.put('/{customer_id}', response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')

    update_data = customer_in.model_dump(exclude_unset=True)
    if 'tag_ids' in update_data:
        tag_ids = update_data.pop('tag_ids')
        if tag_ids is not None:
            db.query(CustomerTag).filter(CustomerTag.customer_id == customer.id).delete()
            for tid in tag_ids:
                db.add(CustomerTag(customer_id=customer.id, tag_id=tid))

    for field, value in update_data.items():
        setattr(customer, field, value)

    customer.last_interaction = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)
    return customer

@router.delete('/{customer_id}')
def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')

    db.delete(customer)
    db.commit()
    return {'message': 'Cliente e registros associados removidos com sucesso.'}

@router.get('/{customer_id}/export')
def export_customer_data_lgpd(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direito do Titular (LGPD Art. 18 / Art. 19): Exportação completa e portabilidade dos dados do titular.
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')

    # Collect conversations and messages
    conversations_data = []
    for conv in customer.conversations:
        messages_list = [
            {
                "id": m.id,
                "direction": m.direction.value,
                "type": m.message_type.value,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in conv.messages
        ]
        conversations_data.append({
            "id": conv.id,
            "status": conv.status,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "messages": messages_list
        })

    opportunities_data = [
        {
            "id": opp.id,
            "title": opp.title,
            "value": opp.value,
            "stage": opp.stage.name if opp.stage else None,
            "created_at": opp.created_at.isoformat() if opp.created_at else None
        }
        for opp in customer.opportunities
    ]

    return {
        "export_metadata": {
            "requested_by_user_id": current_user.id,
            "company_id": current_user.company_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "legal_basis": "LGPD Art. 18 - Portabilidade / Acesso aos Dados"
        },
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "company_name": customer.company_name,
            "notes": customer.notes,
            "total_spent": customer.total_spent,
            "orders_count": customer.orders_count,
            "created_at": customer.created_at.isoformat() if customer.created_at else None
        },
        "conversations": conversations_data,
        "opportunities": opportunities_data
    }

@router.post('/{customer_id}/anonymize')
def anonymize_customer_data_lgpd(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direito de Eliminação / Anonimização (LGPD Art. 18, VI): Anonimiza dados pessoais do cliente mantendo integridade contábil.
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.company_id == current_user.company_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail='Cliente não encontrado.')

    # Anonymize PII
    customer.name = f"Cliente Anonimizado #{customer.id}"
    customer.phone = f"+55000000000{customer.id % 1000}"
    customer.email = None
    customer.company_name = None
    customer.notes = "[DADOS PESSOAIS ANONIMIZADOS CONFORME SOLICITAÇÃO LGPD]"

    # Anonymize conversation messages
    for conv in customer.conversations:
        for msg in conv.messages:
            msg.content = "[MENSAGEM ANONIMIZADA - LGPD]"
            msg.media_url = None

    db.commit()
    db.refresh(customer)
    return {"message": "Dados do cliente e histórico de atendimento foram anonimizados com sucesso conforme LGPD."}